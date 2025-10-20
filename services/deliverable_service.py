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
            section_content = self._assemble_section_content(binding)
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

    def _assemble_section_content(self, binding) -> str:
        """Assemble content for a section from bound Elements"""
        content_parts = []

        for elem_id in binding.element_ids:
            element = self.unf_service.get_element(elem_id)
            if element and element.status == "approved":
                content_parts.append(element.content or "")

        return "\n\n".join(content_parts)

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
        """Update a Deliverable"""
        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Convert complex fields to JSON
        for field in ['instance_data', 'rendered_content', 'metadata']:
            if field in data and isinstance(data[field], dict):
                data[field] = json.dumps(data[field])

        # Handle status enum
        if 'status' in data and isinstance(data['status'], DeliverableStatus):
            data['status'] = data['status'].value

        self.storage.update_one("deliverables", deliverable_id, data)
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

        # Save validation log
        self.storage.update_one(
            "deliverables",
            deliverable_id,
            {"validation_log": json.dumps([v.model_dump() for v in validation_log])}
        )

        return validation_log
