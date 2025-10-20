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
        Update an Element (creates new version)

        This follows the version chain pattern:
        1. Create new Element with updated content
        2. Link to previous version via prev_element_id
        3. Mark old version as 'superseded'
        """
        # Get current element
        current = self.get_element(element_id)
        if not current:
            raise ValueError(f"Element {element_id} not found")

        # Parse version number and increment
        version_parts = current.version.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        new_version = f"{major}.{minor + 1}"

        # Prepare new element data
        new_data = {
            "layer_id": current.layer_id,
            "name": current.name,
            "content": update_data.content if update_data.content is not None else current.content,
            "version": new_version,
            "status": update_data.status.value if update_data.status else current.status.value,
            "prev_element_id": element_id,  # Link to old version
            "metadata": json.dumps(
                update_data.metadata if update_data.metadata is not None else current.metadata
            )
        }

        # Create new version
        new_element_id = self.storage.insert_one(
            "unf_elements",
            new_data,
            returning="id"
        )

        # Mark old version as superseded
        self.storage.update_one(
            "unf_elements",
            element_id,
            {"status": ElementStatus.SUPERSEDED.value}
        )

        return self.get_element(new_element_id)

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
