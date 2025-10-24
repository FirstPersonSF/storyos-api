"""
Deliverable Service

Orchestrates creation and rendering of Deliverables
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import ujson as json

from models.deliverables import (
    Deliverable, DeliverableCreate, DeliverableUpdate,
    DeliverableStatus, DeliverableWithAlerts, ImpactAlert,
    ValidationLogEntry
)
from storage.postgres_storage import PostgresStorage
from services.voice_transformer import VoiceTransformer
from services.voice_transformer_llm import get_voice_transformer
from services.story_model_composer import StoryModelComposer


class DeliverableService:
    """Service for Deliverable management and rendering"""

    def __init__(
        self,
        storage: PostgresStorage,
        unf_service,  # Avoid circular import
        voice_service,
        template_service,
        story_model_service,
        relationship_service
    ):
        self.storage = storage
        self.unf_service = unf_service
        self.voice_service = voice_service
        self.template_service = template_service
        self.story_model_service = story_model_service
        self.relationship_service = relationship_service

        # Phase 2: Initialize transformers
        self.voice_transformer = VoiceTransformer()  # Legacy regex-based (backup)
        self.llm_voice_transformer = get_voice_transformer()  # LLM-based (primary)
        self.story_model_composer = StoryModelComposer()

        # Validation rules for Press Release sections (to be included in LLM prompts)
        self.press_release_validation_rules = {
            'Headline': [
                "Must be ≤10 words",
                "MUST include a strong, present-tense action verb that clearly communicates what is being announced (examples: announces, launches, introduces, reveals, unveils, releases, optimizes, transforms, enables, empowers, drives, accelerates, etc.)"
            ],
            'Lede': [
                "Must contain WHO (who is making the announcement)",
                "Must contain WHAT (what is being announced)",
                "Must contain WHEN (when is this happening)",
                "Must contain WHERE (where is this relevant)",
                "Must contain WHY (why does this matter)"
            ],
            'Key Facts': [
                "Must include at least 3 bullet points/key messages"
            ]
        }

    def _validate_headline_with_llm(self, headline: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Use LLM to validate if headline contains an appropriate action verb for press releases.

        Args:
            headline: The headline text to validate

        Returns:
            tuple: (passed, verb_found, explanation)
                - passed: True if validation passed
                - verb_found: The action verb found (if any)
                - explanation: Brief explanation of the validation result
        """
        from services.llm_client import get_llm_client

        validation_prompt = f"""Analyze this press release headline for action verb requirements.

Press release headlines should contain a strong, present-tense action verb that clearly communicates what is being announced (e.g., announces, launches, introduces, reveals, unveils, releases, optimizes, transforms, enables, etc.).

Headline to analyze: "{headline}"

Evaluate:
1. Does it contain an appropriate action verb for a press release?
2. If yes, what is the verb?
3. Is the verb strong and announcement-oriented?

Respond with ONLY valid JSON in this exact format:
{{
  "has_action_verb": true or false,
  "verb_found": "the verb if present, or null",
  "explanation": "brief explanation (1-2 sentences)"
}}"""

        try:
            llm_client = get_llm_client()
            response = llm_client.transform_content(
                prompt=validation_prompt,
                model="claude-3-5-haiku-20241022",
                max_tokens=256,
                temperature=0.0
            )

            # Parse JSON response
            result = json.loads(response)

            return (
                result.get('has_action_verb', False),
                result.get('verb_found'),
                result.get('explanation', 'No explanation provided')
            )

        except Exception as e:
            # Fallback: if LLM validation fails, log error and pass the validation
            # to avoid blocking on transient API errors
            print(f"LLM validation error: {e}")
            return (True, None, f"LLM validation unavailable (error: {str(e)}). Allowing headline to pass.")

    def create_deliverable(self, deliverable_data: DeliverableCreate) -> Deliverable:
        """
        Create a new Deliverable from a Template

        This assembles content from UNF Elements,
       applies Brand Voice, and tracks dependencies
        """
        # Get template
        template = self.template_service.get_template_with_bindings(
            deliverable_data.template_id
        )
        if not template:
            raise ValueError(f"Template {deliverable_data.template_id} not found")

        # Get Story Model
        story_model = self.story_model_service.get_story_model(template.story_model_id)

        # Use provided voice or template default
        voice_id = deliverable_data.voice_id or template.default_voice_id
        voice = self.voice_service.get_voice(voice_id)

        # Assemble content from Elements
        element_versions = {}
        rendered_content = {}
        transformation_notes = {}

        for i, binding in enumerate(template.section_bindings):
            section_content, section_notes = self._assemble_section_content(
                binding,
                deliverable_data.instance_data,
                story_model,
                voice
            )
            rendered_content[binding.section_name] = section_content

            # Store transformation notes if present
            if section_notes:
                transformation_notes[binding.section_name] = section_notes

            # Track element versions used
            for elem_id in binding.element_ids:
                element = self.unf_service.get_element(elem_id)
                if element:
                    element_versions[str(elem_id)] = element.version

        # Merge transformation_notes into metadata
        metadata = deliverable_data.metadata.copy() if deliverable_data.metadata else {}
        if transformation_notes:
            metadata['transformation_notes'] = transformation_notes

        # Add transformation metadata to indicate LLM method
        metadata['transformation_metadata'] = {
            'method': 'llm',
            'transformer': 'voice_transformer_llm'
        }

        # Prepare deliverable data
        data = {
            "name": deliverable_data.name,
            "template_id": template.id,
            "template_version": template.version,
            "story_model_id": template.story_model_id,
            "voice_id": voice_id,
            "voice_version": voice.version,
            "instance_data": json.dumps(deliverable_data.instance_data),
            "status": deliverable_data.status.value,
            "element_versions": json.dumps(element_versions),
            "rendered_content": json.dumps(rendered_content),
            "validation_log": json.dumps([]),
            "metadata": json.dumps(metadata)
        }

        # Create deliverable
        deliverable_id = self.storage.insert_one(
            "deliverables",
            data,
            returning="id"
        )

        # Track dependencies
        for elem_id in element_versions.keys():
            self.relationship_service.track_element_usage(
                UUID(elem_id),
                deliverable_id
            )

        # Automatically run validation after creation
        self.validate_deliverable(deliverable_id)

        return self.get_deliverable(deliverable_id)

    def _assemble_section_content(
        self,
        binding,
        instance_data: Dict[str, Any],
        story_model,
        voice
    ) -> tuple[str, str]:
        """
        Assemble content for a section from bound Elements

        Phase 2: Uses story model strategies and voice transformation

        Returns:
            tuple: (section_content, transformation_notes)
        """
        # Get bound elements
        bound_elements = []
        for elem_id in binding.element_ids:
            element = self.unf_service.get_element(elem_id)
            if element and element.status == "approved":
                bound_elements.append(element)

        # Get section strategy from story model (if available)
        section_strategy = {}
        if story_model and hasattr(story_model, 'section_strategies') and story_model.section_strategies:
            section_strategy = story_model.section_strategies.get(binding.section_name, {})

        # If no strategy defined, use default (full_content)
        if not section_strategy:
            section_strategy = {'extraction_strategy': 'full_content'}

        # Phase 2: Use story model composer
        assembled_content = self.story_model_composer.compose_section(
            section_name=binding.section_name,
            section_strategy=section_strategy,
            bound_elements=bound_elements,
            instance_data=instance_data
        )

        # Track transformation notes
        transformation_notes = ""

        # Phase 2: Apply voice transformation (LLM-based)
        # Skip transformation if assembled_content is empty
        if voice and assembled_content:
            # Build complete voice configuration for LLM (convert Pydantic models to dicts)
            def to_dict(obj):
                """Convert Pydantic model or dict to dict"""
                if obj is None:
                    return {}
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                if isinstance(obj, dict):
                    return obj
                return {}

            voice_config = {
                'traits': voice.traits if hasattr(voice, 'traits') else [],
                'tone_rules': to_dict(voice.tone_rules) if hasattr(voice, 'tone_rules') else {},
                'style_guardrails': to_dict(voice.style_guardrails) if hasattr(voice, 'style_guardrails') else {},
                'lexicon': to_dict(voice.lexicon) if hasattr(voice, 'lexicon') else {},
                'rules': voice.rules if hasattr(voice, 'rules') else {}
            }

            # Use LLM transformer with profile-aware transformation (fallback to regex if LLM fails)
            try:
                # Inject validation rules for Press Release sections
                constraints_with_validation = section_strategy.copy() if section_strategy else {}
                if template.name == "Press Release" and binding.section_name in self.press_release_validation_rules:
                    constraints_with_validation['validation_rules'] = self.press_release_validation_rules[binding.section_name]

                # Pass section name and constraints for profile-aware transformation
                assembled_content, transformation_notes = self.llm_voice_transformer.apply_voice_with_profile(
                    content=assembled_content,
                    voice_config=voice_config,
                    section_name=binding.section_name,
                    constraints=constraints_with_validation  # Section strategy includes max_words, format, validation_rules, etc.
                )
                # DEBUG: Log transformation results
                print(f"[TRANSFORM] Section: {binding.section_name}")
                print(f"[TRANSFORM]   Content length: {len(assembled_content)}")
                print(f"[TRANSFORM]   Notes length: {len(transformation_notes) if transformation_notes else 0}")
                print(f"[TRANSFORM]   Notes preview: {transformation_notes[:100] if transformation_notes else '(empty)'}")
            except Exception as e:
                print(f"LLM transformation failed, using regex fallback: {e}")
                # Fallback to regex transformer with just rules
                if voice.rules:
                    assembled_content = self.voice_transformer.apply_voice(
                        assembled_content,
                        voice.rules
                    )
                transformation_notes = f"LLM transformation failed: {e}"

        return assembled_content, transformation_notes

    def get_deliverable(self, deliverable_id: UUID) -> Optional[Deliverable]:
        """Get a Deliverable by ID"""
        row = self.storage.get_one("deliverables", deliverable_id)
        if not row:
            return None

        # Parse JSON fields
        for field in ['instance_data', 'element_versions', 'rendered_content', 'validation_log', 'metadata']:
            if field in row and isinstance(row[field], str):
                row[field] = json.loads(row[field])

        return Deliverable(**row)

    def get_deliverable_with_alerts(self, deliverable_id: UUID) -> Optional[DeliverableWithAlerts]:
        """Get a Deliverable with impact alerts"""
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            return None

        # Check for element updates
        alerts = self._check_for_updates(deliverable)

        deliverable_dict = deliverable.model_dump()
        deliverable_dict['alerts'] = alerts
        deliverable_dict['has_updates'] = len(alerts) > 0

        return DeliverableWithAlerts(**deliverable_dict)

    def get_deliverable_versions(self, deliverable_id: UUID) -> List[Deliverable]:
        """
        Get all versions of a deliverable by tracing back through prev_deliverable_id chain

        Returns list of deliverables sorted by version (newest first)
        Similar to UNF Element version history
        """
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            return []

        # Find the latest version in the chain by following next versions forward
        all_deliverables = self.list_deliverables()

        # Build a map of prev_id -> deliverable for forward traversal
        next_versions = {}
        for d in all_deliverables:
            if d.prev_deliverable_id:
                next_versions[str(d.prev_deliverable_id)] = d

        # Find the latest version (one with no next version)
        current = deliverable
        while str(current.id) in next_versions:
            current = next_versions[str(current.id)]

        # Now trace back from latest version to get all versions
        versions = []
        while current:
            versions.append(current)
            if current.prev_deliverable_id:
                current = self.get_deliverable(current.prev_deliverable_id)
            else:
                current = None

        return versions

    def _check_for_updates(self, deliverable: Deliverable) -> List[ImpactAlert]:
        """
        Check if any Elements used by this Deliverable have been updated

        Returns alerts with two status types:
        - 'update_available': Element has newer APPROVED version (safe to refresh)
        - 'update_pending': Element has newer DRAFT version (should NOT refresh until approved)
        """
        alerts = []

        for elem_id_str, used_version in deliverable.element_versions.items():
            elem_id = UUID(elem_id_str)
            used_element = self.unf_service.get_element(elem_id)

            if not used_element:
                continue

            # Find all newer versions of this element (by name)
            all_elements = self.unf_service.list_elements()

            # Build version chain from used element forward
            newer_approved = []
            newer_draft = []

            for e in all_elements:
                if e.name == used_element.name and e.id != used_element.id:
                    # Check if this is a newer version (compare version strings)
                    if self._is_newer_version(e.version, used_version):
                        if e.status == "approved":
                            newer_approved.append(e)
                        elif e.status == "draft":
                            newer_draft.append(e)

            # Create alerts for approved updates (safe to refresh)
            for newer in newer_approved:
                alerts.append(ImpactAlert(
                    element_id=elem_id,
                    element_name=used_element.name,
                    old_version=used_version,
                    new_version=newer.version,
                    status="update_available"
                ))

            # Create alerts for draft updates (NOT safe to refresh)
            for newer in newer_draft:
                alerts.append(ImpactAlert(
                    element_id=elem_id,
                    element_name=used_element.name,
                    old_version=used_version,
                    new_version=newer.version,
                    status="update_pending"
                ))

        return alerts

    def _is_newer_version(self, version_a: str, version_b: str) -> bool:
        """
        Compare version strings (e.g., "1.1" > "1.0")

        Returns True if version_a is newer than version_b
        """
        try:
            # Split version strings into parts and compare
            parts_a = [int(x) for x in version_a.split('.')]
            parts_b = [int(x) for x in version_b.split('.')]

            # Pad shorter version with zeros
            max_len = max(len(parts_a), len(parts_b))
            parts_a.extend([0] * (max_len - len(parts_a)))
            parts_b.extend([0] * (max_len - len(parts_b)))

            return parts_a > parts_b
        except (ValueError, AttributeError):
            # If version comparison fails, treat as not newer
            return False

    def update_deliverable(
        self,
        deliverable_id: UUID,
        update_data: DeliverableUpdate
    ) -> Deliverable:
        """
        Update a Deliverable by creating a new version

        Creates a new deliverable record with incremented version number,
        marks the old version as 'superseded', and links them via prev_deliverable_id.
        This provides non-destructive version history similar to UNF Elements.

        Re-renders content if template_id, voice_id, instance_data, or story_model_id changes

        Story Model Switching (Test 05):
        - If story_model_id changes, template_id MUST also be provided
        - The new template must use the new Story Model
        - Section reflow happens automatically via the new template's bindings
        """
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable {deliverable_id} not found")

        # Validate that deliverable has a name (data integrity check)
        if not deliverable.name:
            raise ValueError(
                f"Deliverable {deliverable_id} has NULL name - this is a data integrity issue. "
                f"Please delete this deliverable or fix the name in the database."
            )

        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Validate Story Model and Template compatibility
        if 'story_model_id' in data and 'template_id' not in data:
            raise ValueError(
                "When changing story_model_id, you must also provide a template_id "
                "that uses the new Story Model. Templates and Story Models are tightly coupled."
            )

        if 'template_id' in data:
            new_template = self.template_service.get_template_with_bindings(data['template_id'])
            if not new_template:
                raise ValueError(f"Template {data['template_id']} not found")

            # If story_model_id is explicitly provided, validate it matches the template
            if 'story_model_id' in data:
                if new_template.story_model_id != data['story_model_id']:
                    raise ValueError(
                        f"Template {new_template.id} uses Story Model {new_template.story_model_id}, "
                        f"but you requested Story Model {data['story_model_id']}. "
                        f"Template and Story Model must match."
                    )
            # If story_model_id not provided, inherit from new template
            else:
                data['story_model_id'] = new_template.story_model_id

        # Check if we need to re-render
        needs_rerender = (
            'template_id' in data or
            'voice_id' in data or
            'instance_data' in data or
            'story_model_id' in data
        )

        # Prepare new deliverable data (start with existing values)
        new_deliverable_data = {
            "name": data.get('name', deliverable.name),
            "template_id": data.get('template_id', deliverable.template_id),
            "template_version": deliverable.template_version,  # Will be updated if template changes
            "story_model_id": data.get('story_model_id', deliverable.story_model_id),
            "voice_id": data.get('voice_id', deliverable.voice_id),
            "voice_version": deliverable.voice_version,
            "instance_data": data.get('instance_data', deliverable.instance_data),
            "status": data.get('status', deliverable.status),
            "element_versions": deliverable.element_versions,
            "rendered_content": deliverable.rendered_content,
            "validation_log": deliverable.validation_log,
            "metadata": data.get('metadata', deliverable.metadata),
            "version": deliverable.version + 1,
            "prev_deliverable_id": deliverable.id
        }

        if needs_rerender:
            # Get template (use new template if provided, otherwise existing)
            template = self.template_service.get_template_with_bindings(
                new_deliverable_data['template_id']
            )

            # Update template version
            new_deliverable_data['template_version'] = template.version

            # Use new voice or keep existing
            voice_id = new_deliverable_data['voice_id']
            voice = self.voice_service.get_voice(voice_id)
            if not voice:
                raise ValueError(f"Brand Voice {voice_id} not found")

            # Use new story model or keep existing
            story_model_id = new_deliverable_data['story_model_id']
            story_model = self.story_model_service.get_story_model(story_model_id)
            if not story_model:
                raise ValueError(f"Story Model {story_model_id} not found")

            # Use new instance data or keep existing
            instance_data = new_deliverable_data['instance_data']

            # Re-render content with current element versions (Phase 2: with transformers)
            rendered_content = {}
            element_versions = {}

            for binding in template.section_bindings:
                section_content = self._assemble_section_content(
                    binding,
                    instance_data,
                    story_model,
                    voice
                )
                rendered_content[binding.section_name] = section_content

                # Track element versions used
                for elem_id in binding.element_ids:
                    element = self.unf_service.get_element(elem_id)
                    if element:
                        element_versions[str(elem_id)] = element.version

            # Update data with re-rendered content, new voice version, and element versions
            new_deliverable_data['rendered_content'] = rendered_content
            new_deliverable_data['voice_version'] = voice.version
            new_deliverable_data['element_versions'] = element_versions

        # Convert complex fields to JSON
        for field in ['instance_data', 'rendered_content', 'metadata', 'element_versions', 'validation_log']:
            if field in new_deliverable_data and isinstance(new_deliverable_data[field], (dict, list)):
                new_deliverable_data[field] = json.dumps(new_deliverable_data[field])

        # Handle status enum
        if isinstance(new_deliverable_data['status'], DeliverableStatus):
            new_deliverable_data['status'] = new_deliverable_data['status'].value

        # Create new deliverable version
        new_deliverable_id = self.storage.insert_one(
            "deliverables",
            new_deliverable_data,
            returning="id"
        )

        # Mark old deliverable as superseded
        self.storage.update_one(
            "deliverables",
            deliverable_id,
            {"status": DeliverableStatus.SUPERSEDED.value}
        )

        # Track element dependencies for new version
        if needs_rerender:
            for elem_id in element_versions.keys():
                self.relationship_service.track_element_usage(
                    UUID(elem_id),
                    new_deliverable_id
                )

        return self.get_deliverable(new_deliverable_id)

    def refresh_deliverable(self, deliverable_id: UUID, force: bool = False) -> Deliverable:
        """
        Refresh a Deliverable with latest element versions

        Re-renders content using the most recent approved versions
        of all elements used in the deliverable

        Args:
            deliverable_id: ID of deliverable to refresh
            force: If False (default), blocks refresh if any draft element updates exist.
                   If True, refreshes anyway (use with caution).

        Raises:
            ValueError: If deliverable not found or if draft elements exist (and force=False)
        """
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable {deliverable_id} not found")

        # Check for draft element updates (blocking condition)
        if not force:
            alerts = self._check_for_updates(deliverable)
            draft_alerts = [a for a in alerts if a.status == "update_pending"]

            if draft_alerts:
                # Build error message with details
                element_names = ', '.join([a.element_name for a in draft_alerts])
                raise ValueError(
                    f"Cannot refresh deliverable: {len(draft_alerts)} element(s) have draft updates "
                    f"that must be approved first: {element_names}. "
                    f"Use force=True to override (not recommended)."
                )

        # Get template
        template = self.template_service.get_template_with_bindings(deliverable.template_id)

        # Get current voice
        voice = self.voice_service.get_voice(deliverable.voice_id)

        # Get story model
        story_model = self.story_model_service.get_story_model(deliverable.story_model_id)

        # Find latest versions of elements and re-render
        element_versions = {}
        rendered_content = {}

        for binding in template.section_bindings:
            # Find latest approved versions of elements bound to this section
            latest_elements = []

            for elem_id in binding.element_ids:
                # Get current element
                old_element = self.unf_service.get_element(elem_id)
                if not old_element:
                    continue

                # Find latest approved version by name
                all_elements = self.unf_service.list_elements()
                latest_approved = None
                latest_version = "0.0"

                for elem in all_elements:
                    if elem.name == old_element.name and elem.status == "approved":
                        if elem.version > latest_version:
                            latest_version = elem.version
                            latest_approved = elem

                if latest_approved:
                    latest_elements.append(latest_approved)
                    element_versions[str(latest_approved.id)] = latest_approved.version

            # Phase 2: Use story model composer and voice transformer
            if latest_elements:
                # Get section strategy
                section_strategy = {}
                if story_model and hasattr(story_model, 'section_strategies') and story_model.section_strategies:
                    section_strategy = story_model.section_strategies.get(binding.section_name, {})

                if not section_strategy:
                    section_strategy = {'extraction_strategy': 'full_content'}

                # Compose section
                section_content = self.story_model_composer.compose_section(
                    section_name=binding.section_name,
                    section_strategy=section_strategy,
                    bound_elements=latest_elements,
                    instance_data=deliverable.instance_data
                )

                # Apply voice transformation
                if voice and hasattr(voice, 'rules') and voice.rules:
                    section_content = self.voice_transformer.apply_voice(
                        section_content,
                        voice.rules
                    )

                rendered_content[binding.section_name] = section_content
            else:
                rendered_content[binding.section_name] = ""

        # Update deliverable with new versions and content
        data = {
            "element_versions": json.dumps(element_versions),
            "rendered_content": json.dumps(rendered_content),
            "voice_version": voice.version
        }

        self.storage.update_one("deliverables", deliverable_id, data)

        # Update relationship tracking
        for elem_id in element_versions.keys():
            self.relationship_service.track_element_usage(
                UUID(elem_id),
                deliverable_id
            )

        return self.get_deliverable(deliverable_id)

    def list_deliverables(self, status: Optional[DeliverableStatus] = None) -> List[Deliverable]:
        """List all Deliverables with optional status filter"""
        filters = {}
        if status:
            filters['status'] = status.value

        rows = self.storage.get_many(
            "deliverables",
            filters=filters if filters else None,
            order_by="created_at DESC"
        )

        deliverables = []
        for row in rows:
            # Skip deliverables with NULL names (data integrity issue)
            if row.get('name') is None:
                print(f"Warning: Skipping deliverable {row.get('id')} with NULL name")
                continue

            for field in ['instance_data', 'element_versions', 'rendered_content', 'validation_log', 'metadata']:
                if field in row and isinstance(row[field], str):
                    row[field] = json.loads(row[field])
            deliverables.append(Deliverable(**row))

        return deliverables

    def validate_deliverable(self, deliverable_id: UUID) -> List[ValidationLogEntry]:
        """Run validation checks on a Deliverable"""
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable {deliverable_id} not found")

        template = self.template_service.get_template(deliverable.template_id)
        story_model = self.story_model_service.get_story_model(deliverable.story_model_id)
        validation_log = []

        # Check instance fields
        for field in template.instance_fields:
            if field.required:
                if field.name not in deliverable.instance_data:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"required_field_{field.name}",
                        passed=False,
                        message=f"Required field '{field.name}' is missing"
                    ))
                else:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"required_field_{field.name}",
                        passed=True,
                        message=None
                    ))

        # Check Story Model constraints
        if story_model and story_model.constraints:
            for constraint in story_model.constraints:
                section_name = constraint.section_name
                constraint_type = constraint.constraint_type
                params = constraint.params

                # Get section content
                section_content = deliverable.rendered_content.get(section_name, '')

                # Word count validation
                if constraint_type == 'max_words':
                    word_count = len(section_content.split())
                    max_words = params.get('max_words', 0)

                    if word_count > max_words:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_max_words",
                            passed=False,
                            message=f"{section_name} has {word_count} words, exceeds max {max_words}"
                        ))
                    else:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_max_words",
                            passed=True,
                            message=None
                        ))

                # Required element validation
                elif constraint_type == 'requires_element':
                    element_name = params.get('element_name')

                    # Check if any used elements match the required name
                    has_element = False
                    for elem_id in deliverable.element_versions.keys():
                        elem = self.unf_service.get_element(UUID(elem_id))
                        if elem and elem.name == element_name:
                            has_element = True
                            break

                    if not has_element:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_requires_{element_name.replace(' ', '_')}",
                            passed=False,
                            message=f"{section_name} requires element '{element_name}'"
                        ))
                    else:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_requires_{element_name.replace(' ', '_')}",
                            passed=True,
                            message=None
                        ))

                # Required fields validation (for instance data)
                elif constraint_type == 'requires_fields':
                    required_fields = params.get('fields', [])
                    missing_fields = [f for f in required_fields if f not in deliverable.instance_data]

                    if missing_fields:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_requires_fields",
                            passed=False,
                            message=f"{section_name} missing fields: {', '.join(missing_fields)}"
                        ))
                    else:
                        validation_log.append(ValidationLogEntry(
                            timestamp=datetime.now(),
                            rule=f"story_model_{section_name}_requires_fields",
                            passed=True,
                            message=None
                        ))

        # Press Release Specific Validation Rules
        if template.name == "Press Release":
            self._validate_press_release(deliverable, validation_log)

        # Save validation log (convert datetime to ISO string for JSON serialization)
        validation_log_serializable = []
        for v in validation_log:
            entry = v.model_dump()
            if 'timestamp' in entry and entry['timestamp']:
                entry['timestamp'] = entry['timestamp'].isoformat()
            validation_log_serializable.append(entry)

        self.storage.update_one(
            "deliverables",
            deliverable_id,
            {"validation_log": json.dumps(validation_log_serializable)}
        )

        return validation_log

    def _validate_press_release(self, deliverable: Deliverable, validation_log: List[ValidationLogEntry]):
        """
        Press Release specific validation rules:
        1. Headline ≤10 words and must include one action verb
        2. Lede must contain "who, what, when, where, and why"
        3. Key Facts section must include 3 Key Messages
        4. Each Quote requires text and attribution fields
        5. Boilerplate section required
        6. Voice validation required before publishing
        """
        import re

        # Rule 1: Headline ≤10 words and must include one action verb
        headline = deliverable.rendered_content.get('Headline', '')
        word_count = len(headline.split())

        # Check word count
        if word_count > 10:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_headline_max_10_words",
                passed=False,
                message=f"Headline has {word_count} words, must be ≤10 words"
            ))
        else:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_headline_max_10_words",
                passed=True,
                message=None
            ))

        # Check for action verb using LLM-based validation
        has_action_verb, verb_found, explanation = self._validate_headline_with_llm(headline)

        if not has_action_verb:
            message = f"Headline should include a strong action verb. {explanation}"
            if verb_found:
                message = f"Found '{verb_found}' but {explanation}"

            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_headline_action_verb",
                passed=False,
                message=message
            ))
        else:
            message = None
            if verb_found:
                message = f"Action verb '{verb_found}' found. {explanation}" if explanation else f"Action verb '{verb_found}' found."

            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_headline_action_verb",
                passed=True,
                message=message
            ))

        # Rule 2: Lede must contain who, what, when, where, and why
        lede = deliverable.rendered_content.get('Lede', '').lower()
        five_ws = {
            'who': deliverable.instance_data.get('who', ''),
            'what': deliverable.instance_data.get('what', ''),
            'when': deliverable.instance_data.get('when', ''),
            'where': deliverable.instance_data.get('where', ''),
            'why': deliverable.instance_data.get('why', '')
        }

        missing_ws = [w for w, value in five_ws.items() if not value]

        if missing_ws:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_lede_five_ws",
                passed=False,
                message=f"Lede missing: {', '.join(missing_ws)}"
            ))
        else:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_lede_five_ws",
                passed=True,
                message=None
            ))

        # Rule 3: Key Facts must include 3 items
        key_facts = deliverable.rendered_content.get('Key Facts', '')
        # Count bullet points (lines starting with -)
        bullet_count = len([line for line in key_facts.split('\n') if line.strip().startswith('-')])

        if bullet_count < 3:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_key_facts_min_3",
                passed=False,
                message=f"Key Facts has {bullet_count} items, requires 3 Key Messages"
            ))
        else:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_key_facts_min_3",
                passed=True,
                message=None
            ))

        # Rule 4: Each Quote requires text and attribution
        for quote_num in [1, 2]:
            quote_text = deliverable.instance_data.get(f'quote{quote_num}_text', '')
            quote_speaker = deliverable.instance_data.get(f'quote{quote_num}_speaker', '')
            quote_title = deliverable.instance_data.get(f'quote{quote_num}_title', '')

            # Quote 1 is required, Quote 2 is optional
            if quote_num == 1:
                if not quote_text:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_text_required",
                        passed=False,
                        message=f"Quote {quote_num} text is required"
                    ))
                else:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_text_required",
                        passed=True,
                        message=None
                    ))

                if not quote_speaker or not quote_title:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_attribution_required",
                        passed=False,
                        message=f"Quote {quote_num} requires both speaker and title"
                    ))
                else:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_attribution_required",
                        passed=True,
                        message=None
                    ))
            else:
                # Quote 2 is optional, but if provided, must have attribution
                if quote_text and (not quote_speaker or not quote_title):
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_attribution_required",
                        passed=False,
                        message=f"Quote {quote_num} has text but missing speaker or title"
                    ))
                elif quote_text:
                    validation_log.append(ValidationLogEntry(
                        timestamp=datetime.now(),
                        rule=f"press_release_quote{quote_num}_attribution_required",
                        passed=True,
                        message=None
                    ))

        # Rule 5: Boilerplate section required
        boilerplate = deliverable.rendered_content.get('Boilerplate', '')

        if not boilerplate or len(boilerplate.strip()) == 0:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_boilerplate_required",
                passed=False,
                message="Boilerplate section is required"
            ))
        else:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_boilerplate_required",
                passed=True,
                message=None
            ))

        # Rule 6: Voice validation (check if transformation notes exist as indicator of voice application)
        has_transformation_notes = bool(deliverable.metadata.get('transformation_notes'))

        if not has_transformation_notes:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_voice_validation",
                passed=False,
                message="Voice transformation required before publishing"
            ))
        else:
            validation_log.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule="press_release_voice_validation",
                passed=True,
                message=None
            ))
