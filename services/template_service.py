"""
Deliverable Template Service

Manages templates and section bindings
"""
from typing import List, Optional
from uuid import UUID
import ujson as json

from models.templates import (
    DeliverableTemplate, TemplateCreate, TemplateUpdate,
    SectionBinding, SectionBindingCreate,
    TemplateWithBindings, TemplateStatus
)
from storage.postgres_storage import PostgresStorage


class TemplateService:
    """Service for Deliverable Template management"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(self, template_data: TemplateCreate) -> DeliverableTemplate:
        """Create a new Deliverable Template"""
        data = template_data.model_dump(exclude_unset=True)

        # Convert complex fields to JSON
        for field in ['validation_rules', 'instance_fields', 'metadata']:
            if field in data and data[field] is not None:
                if isinstance(data[field], list):
                    data[field] = json.dumps([
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in data[field]
                    ])
                elif isinstance(data[field], dict):
                    data[field] = json.dumps(data[field])

        # Handle status enum
        if 'status' in data and isinstance(data['status'], TemplateStatus):
            data['status'] = data['status'].value

        template_id = self.storage.insert_one(
            "deliverable_templates",
            data,
            returning="id"
        )

        return self.get_template(template_id)

    def get_template(self, template_id: UUID) -> Optional[DeliverableTemplate]:
        """Get a Template by ID"""
        row = self.storage.get_one("deliverable_templates", template_id)
        if not row:
            return None

        # Parse JSON fields
        for field in ['validation_rules', 'instance_fields', 'metadata']:
            if field in row and isinstance(row[field], str):
                row[field] = json.loads(row[field])

        return DeliverableTemplate(**row)

    def get_template_with_bindings(self, template_id: UUID) -> Optional[TemplateWithBindings]:
        """Get a Template with all its section bindings"""
        template = self.get_template(template_id)
        if not template:
            return None

        bindings = self.list_section_bindings(template_id)

        template_dict = template.model_dump()
        template_dict['section_bindings'] = bindings

        return TemplateWithBindings(**template_dict)

    def update_template(
        self,
        template_id: UUID,
        update_data: TemplateUpdate
    ) -> DeliverableTemplate:
        """Update a Template"""
        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Convert complex fields to JSON
        for field in ['validation_rules', 'instance_fields', 'metadata']:
            if field in data and data[field] is not None:
                if isinstance(data[field], list):
                    data[field] = json.dumps([
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in data[field]
                    ])
                elif isinstance(data[field], dict):
                    data[field] = json.dumps(data[field])

        # Handle status enum
        if 'status' in data and isinstance(data['status'], TemplateStatus):
            data['status'] = data['status'].value

        self.storage.update_one("deliverable_templates", template_id, data)
        return self.get_template(template_id)

    def list_templates(self, status: Optional[TemplateStatus] = None) -> List[DeliverableTemplate]:
        """List all Templates with optional status filter"""
        filters = {}
        if status:
            filters['status'] = status.value

        rows = self.storage.get_many(
            "deliverable_templates",
            filters=filters if filters else None,
            order_by="created_at DESC"
        )

        templates = []
        for row in rows:
            for field in ['validation_rules', 'instance_fields', 'metadata']:
                if field in row and isinstance(row[field], str):
                    row[field] = json.loads(row[field])
            templates.append(DeliverableTemplate(**row))

        return templates

    # ========================================================================
    # SECTION BINDINGS
    # ========================================================================

    def create_section_binding(
        self,
        binding_data: SectionBindingCreate
    ) -> SectionBinding:
        """Create a section binding"""
        data = binding_data.model_dump(exclude_unset=True)

        # Convert binding_rules to JSON
        if 'binding_rules' in data and data['binding_rules'] is not None:
            if not isinstance(data['binding_rules'], str):
                data['binding_rules'] = json.dumps(
                    data['binding_rules'].model_dump() if hasattr(data['binding_rules'], 'model_dump') else data['binding_rules']
                )

        binding_id = self.storage.insert_one(
            "template_section_bindings",
            data,
            returning="id"
        )

        return self.get_section_binding(binding_id)

    def get_section_binding(self, binding_id: UUID) -> Optional[SectionBinding]:
        """Get a section binding by ID"""
        row = self.storage.get_one("template_section_bindings", binding_id)
        if not row:
            return None

        if 'binding_rules' in row and isinstance(row['binding_rules'], str):
            row['binding_rules'] = json.loads(row['binding_rules'])

        return SectionBinding(**row)

    def list_section_bindings(self, template_id: UUID) -> List[SectionBinding]:
        """List all section bindings for a template"""
        rows = self.storage.get_many(
            "template_section_bindings",
            filters={"template_id": template_id},
            order_by="section_order ASC"
        )

        bindings = []
        for row in rows:
            if 'binding_rules' in row and isinstance(row['binding_rules'], str):
                row['binding_rules'] = json.loads(row['binding_rules'])
            bindings.append(SectionBinding(**row))

        return bindings
