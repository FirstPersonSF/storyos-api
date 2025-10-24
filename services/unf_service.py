"""
Unified Narrative Framework (UNF) Service

Manages Layers and Elements with versioning
"""
from typing import List, Optional
from uuid import UUID
import ujson as json

from models.unf import (
    Layer, LayerCreate,
    Element, ElementCreate, ElementUpdate, ElementStatus
)
from storage.postgres_storage import PostgresStorage


class UNFService:
    """Service for UNF Layers and Elements"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    # ========================================================================
    # LAYERS
    # ========================================================================

    def create_layer(self, layer_data: LayerCreate) -> Layer:
        """Create a new Layer"""
        data = layer_data.model_dump(exclude_unset=True)

        layer_id = self.storage.insert_one(
            "unf_layers",
            data,
            returning="id"
        )

        return self.get_layer(layer_id)

    def get_layer(self, layer_id: UUID) -> Optional[Layer]:
        """Get a Layer by ID"""
        row = self.storage.get_one("unf_layers", layer_id)
        return Layer(**row) if row else None

    def list_layers(self) -> List[Layer]:
        """List all Layers"""
        rows = self.storage.get_many(
            "unf_layers",
            order_by="order_index ASC, name ASC"
        )
        return [Layer(**row) for row in rows]

    # ========================================================================
    # ELEMENTS
    # ========================================================================

    def create_element(self, element_data: ElementCreate) -> Element:
        """Create a new Element"""
        data = element_data.model_dump(exclude_unset=True)

        # Convert metadata dict to JSON if needed
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = json.dumps(data['metadata'])

        element_id = self.storage.insert_one(
            "unf_elements",
            data,
            returning="id"
        )

        return self.get_element(element_id)

    def get_element(self, element_id: UUID) -> Optional[Element]:
        """Get an Element by ID"""
        row = self.storage.get_one("unf_elements", element_id)
        if not row:
            return None

        # Parse metadata if it's a JSON string
        if 'metadata' in row and isinstance(row['metadata'], str):
            row['metadata'] = json.loads(row['metadata'])

        return Element(**row)

    def update_element(
        self,
        element_id: UUID,
        update_data: ElementUpdate
    ) -> Element:
        """
        Update an Element

        Behavior depends on current status:
        - DRAFT: Edits in-place (allows multiple edits before approval)
        - APPROVED: Creates new draft version (versioning workflow)
        - SUPERSEDED: Not allowed
        """
        # Get current element
        current = self.get_element(element_id)
        if not current:
            raise ValueError(f"Element {element_id} not found")

        # DRAFT: Edit in-place
        if current.status == ElementStatus.DRAFT:
            update_fields = {}
            if update_data.content is not None:
                update_fields['content'] = update_data.content
            if update_data.metadata is not None:
                update_fields['metadata'] = json.dumps(update_data.metadata)

            if update_fields:
                self.storage.update_one("unf_elements", element_id, update_fields)

            return self.get_element(element_id)

        # APPROVED: Create new draft version
        elif current.status == ElementStatus.APPROVED:
            # Parse version number and increment
            version_parts = current.version.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            new_version = f"{major}.{minor + 1}"

            # Prepare new draft element
            new_data = {
                "layer_id": current.layer_id,
                "name": current.name,
                "content": update_data.content if update_data.content is not None else current.content,
                "version": new_version,
                "status": ElementStatus.DRAFT.value,  # New version starts as draft
                "prev_element_id": element_id,  # Link to old version
                "metadata": json.dumps(
                    update_data.metadata if update_data.metadata is not None else current.metadata
                )
            }

            # Create new draft version (old version stays approved)
            new_element_id = self.storage.insert_one(
                "unf_elements",
                new_data,
                returning="id"
            )

            return self.get_element(new_element_id)

        # SUPERSEDED: Not allowed
        else:
            raise ValueError(
                f"Cannot update {current.status.value} element. "
                f"Only draft and approved elements can be updated."
            )

    def delete_element(self, element_id: UUID) -> None:
        """
        Delete a draft element

        Only draft elements can be deleted. Attempting to delete
        approved or superseded elements raises an error.
        """
        element = self.get_element(element_id)
        if not element:
            raise ValueError(f"Element {element_id} not found")

        if element.status != ElementStatus.DRAFT:
            raise ValueError(
                f"Cannot delete {element.status.value} element. "
                f"Only draft elements can be deleted."
            )

        self.storage.delete_one("unf_elements", element_id)

    def approve_element(self, element_id: UUID) -> Element:
        """
        Approve a draft element

        If another approved version with the same name exists,
        it will be superseded.
        """
        element = self.get_element(element_id)
        if not element:
            raise ValueError(f"Element {element_id} not found")

        if element.status != ElementStatus.DRAFT:
            raise ValueError(f"Element is already {element.status.value}")

        # Find existing approved version with same name
        all_elements = self.list_elements()
        existing_approved = None

        for elem in all_elements:
            if (elem.name == element.name and
                elem.status == ElementStatus.APPROVED and
                elem.id != element_id):
                existing_approved = elem
                break

        # If approved version exists, supersede it
        if existing_approved:
            self.storage.update_one(
                "unf_elements",
                existing_approved.id,
                {"status": ElementStatus.SUPERSEDED.value}
            )

        # Approve the draft
        self.storage.update_one(
            "unf_elements",
            element_id,
            {"status": ElementStatus.APPROVED.value}
        )

        return self.get_element(element_id)

    def list_elements(
        self,
        layer_id: Optional[UUID] = None,
        status: Optional[ElementStatus] = None
    ) -> List[Element]:
        """
        List Elements with optional filters

        Args:
            layer_id: Filter by Layer
            status: Filter by status
        """
        filters = {}
        if layer_id:
            filters['layer_id'] = layer_id
        if status:
            filters['status'] = status.value

        rows = self.storage.get_many(
            "unf_elements",
            filters=filters if filters else None,
            order_by="created_at DESC"
        )

        # Parse JSON fields
        elements = []
        for row in rows:
            if 'metadata' in row and isinstance(row['metadata'], str):
                row['metadata'] = json.loads(row['metadata'])
            elements.append(Element(**row))

        return elements

    def get_latest_approved_elements(self, layer_id: Optional[UUID] = None) -> List[Element]:
        """
        Get the latest approved version of each Element

        Args:
            layer_id: Optional filter by Layer
        """
        query = """
            SELECT DISTINCT ON (layer_id, name) *
            FROM unf_elements
            WHERE status = 'approved'
        """

        if layer_id:
            query += f" AND layer_id = '{layer_id}'"

        query += " ORDER BY layer_id, name, created_at DESC"

        rows = self.storage.execute_query(query, fetch="all")
        return [Element(**row) for row in rows]

    def get_element_version_chain(self, element_id: UUID) -> List[Element]:
        """
        Get the full version history for an Element

        Returns list from newest to oldest
        """
        versions = []
        current_id = element_id

        while current_id:
            element = self.get_element(current_id)
            if not element:
                break

            versions.append(element)
            current_id = element.prev_element_id

        return versions
