"""
Relationship Service

Abstract interface for relationship/dependency tracking
Ready for Neo4j integration in Phase 2
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from storage.postgres_storage import PostgresStorage


class RelationshipService(ABC):
    """Abstract interface for relationship/dependency tracking"""

    @abstractmethod
    def track_element_usage(
        self,
        element_id: UUID,
        deliverable_id: UUID,
        template_id: Optional[UUID] = None
    ):
        """Record that a Deliverable uses an Element"""
        pass

    @abstractmethod
    def get_element_dependencies(
        self,
        element_id: UUID
    ) -> Dict[str, List[UUID]]:
        """
        Get all Templates and Deliverables using this Element

        Returns:
            {
                "templates": [template_ids],
                "deliverables": [deliverable_ids]
            }
        """
        pass

    @abstractmethod
    def get_impact_chain(
        self,
        element_id: UUID
    ) -> Dict[str, Any]:
        """
        Get full impact tree when Element changes

        Returns detailed impact information for UI display
        """
        pass


class PostgresRelationshipService(RelationshipService):
    """PostgreSQL implementation of Relationship Service"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    def track_element_usage(
        self,
        element_id: UUID,
        deliverable_id: UUID,
        template_id: Optional[UUID] = None
    ):
        """Record that a Deliverable uses an Element"""
        # Get template_id from deliverable if not provided
        if not template_id:
            deliverable = self.storage.get_one("deliverables", deliverable_id)
            if deliverable:
                template_id = UUID(deliverable['template_id'])

        if not template_id:
            return

        # Insert dependency record (Supabase upsert will handle duplicates)
        try:
            self.storage.insert_one(
                "element_dependencies",
                {
                    "element_id": element_id,
                    "template_id": template_id,
                    "deliverable_id": deliverable_id
                }
            )
        except Exception as e:
            # Ignore duplicate key errors (record already exists)
            if "duplicate" not in str(e).lower() and "23505" not in str(e):
                raise

    def get_element_dependencies(
        self,
        element_id: UUID
    ) -> Dict[str, List[UUID]]:
        """Get all Templates and Deliverables using this Element"""
        # Get all dependencies for this element
        rows = self.storage.get_many(
            "element_dependencies",
            filters={"element_id": str(element_id)}
        )

        template_ids = set()
        deliverable_ids = set()

        for row in rows:
            if row.get('template_id'):
                template_ids.add(UUID(row['template_id']))
            if row.get('deliverable_id'):
                deliverable_ids.add(UUID(row['deliverable_id']))

        return {
            "templates": list(template_ids),
            "deliverables": list(deliverable_ids)
        }

    def get_impact_chain(
        self,
        element_id: UUID
    ) -> Dict[str, Any]:
        """Get full impact tree when Element changes"""
        dependencies = self.get_element_dependencies(element_id)

        # Get element details
        element = self.storage.get_one("unf_elements", element_id)

        # Get template names
        template_details = []
        for template_id in dependencies['templates']:
            template = self.storage.get_one("deliverable_templates", template_id)
            if template:
                template_details.append({
                    "id": str(template_id),
                    "name": template['name'],
                    "version": template['version']
                })

        # Get deliverable names
        deliverable_details = []
        for deliverable_id in dependencies['deliverables']:
            deliverable = self.storage.get_one("deliverables", deliverable_id)
            if deliverable:
                deliverable_details.append({
                    "id": str(deliverable_id),
                    "name": deliverable.get('name', 'Unnamed Deliverable'),
                    "status": deliverable['status']
                })

        return {
            "element_id": str(element_id),
            "element_name": element['name'] if element else "Unknown",
            "element_version": element['version'] if element else "Unknown",
            "affected_templates": template_details,
            "affected_deliverables": deliverable_details,
            "total_impact": len(template_details) + len(deliverable_details)
        }

    def remove_deliverable_dependencies(self, deliverable_id: UUID):
        """Remove all dependency records for a Deliverable"""
        # TODO: Implement delete operation for Supabase storage
        # For now, this is not used in the core workflow
        pass
