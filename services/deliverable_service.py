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

        for binding in template.section_bindings:
            section_content = self._assemble_section_content(
                binding,
                deliverable_data.instance_data,
                story_model,
                voice
            )
            rendered_content[binding.section_name] = section_content

            # Track element versions used
            for elem_id in binding.element_ids:
                element = self.unf_service.get_element(elem_id)
                if element:
                    element_versions[str(elem_id)] = element.version

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
            "metadata": json.dumps(deliverable_data.metadata)
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

        return self.get_deliverable(deliverable_id)

    def _assemble_section_content(
        self,
        binding,
        instance_data: Dict[str, Any],
        story_model,
        voice
    ) -> str:
        """
        Assemble content for a section from bound Elements

        Phase 2: Uses story model strategies and voice transformation
        """
        # Get bound elements
        bound_elements = []
        for elem_id in binding.element_ids:
            element = self.unf_service.get_element(elem_id)
            if element and element.status == "approved":
                bound_elements.append(element)

        if not bound_elements:
            return ""

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

        # Phase 2: Apply voice transformation (LLM-based)
        if voice:
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

            # Use LLM transformer (fallback to regex if LLM fails)
            try:
                assembled_content = self.llm_voice_transformer.apply_voice(
                    assembled_content,
                    voice_config
                )
            except Exception as e:
                print(f"LLM transformation failed, using regex fallback: {e}")
                # Fallback to regex transformer with just rules
                if voice.rules:
                    assembled_content = self.voice_transformer.apply_voice(
                        assembled_content,
                        voice.rules
                    )

        return assembled_content

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
        """Check if any Elements used by this Deliverable have been updated"""
        alerts = []

        for elem_id_str, used_version in deliverable.element_versions.items():
            elem_id = UUID(elem_id_str)
            used_element = self.unf_service.get_element(elem_id)

            if not used_element:
                continue

            # Check if this element has been superseded
            if used_element.status == "superseded":
                # Find the newer version(s) - look for elements with same name
                all_elements = self.unf_service.list_elements()
                newer_versions = [
                    e for e in all_elements
                    if e.name == used_element.name
                    and e.status == "approved"
                    and e.prev_element_id == elem_id
                ]

                for newer in newer_versions:
                    alerts.append(ImpactAlert(
                        element_id=elem_id,
                        element_name=used_element.name,
                        old_version=used_version,
                        new_version=newer.version,
                        status="update_available"
                    ))

        return alerts

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

        Re-renders content if voice_id, instance_data, or story_model_id changes
        """
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable {deliverable_id} not found")

        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Check if we need to re-render
        needs_rerender = 'voice_id' in data or 'instance_data' in data or 'story_model_id' in data

        # Prepare new deliverable data (start with existing values)
        new_deliverable_data = {
            "name": data.get('name', deliverable.name),
            "template_id": deliverable.template_id,
            "template_version": deliverable.template_version,
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
            # Get template and re-render with new voice/instance data/story model
            template = self.template_service.get_template_with_bindings(deliverable.template_id)

            # Use new voice or keep existing
            voice_id = new_deliverable_data['voice_id']
            voice = self.voice_service.get_voice(voice_id)

            # Use new story model or keep existing
            story_model_id = new_deliverable_data['story_model_id']
            story_model = self.story_model_service.get_story_model(story_model_id)

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

    def refresh_deliverable(self, deliverable_id: UUID) -> Deliverable:
        """
        Refresh a Deliverable with latest element versions

        Re-renders content using the most recent approved versions
        of all elements used in the deliverable
        """
        deliverable = self.get_deliverable(deliverable_id)
        if not deliverable:
            raise ValueError(f"Deliverable {deliverable_id} not found")

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
