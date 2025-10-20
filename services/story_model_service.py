"""
Story Model Service

Manages narrative structures and constraints
"""
from typing import List, Optional
from uuid import UUID
import ujson as json

from models.story_models import StoryModel, StoryModelCreate
from storage.postgres_storage import PostgresStorage


class StoryModelService:
    """Service for Story Model management"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    def create_story_model(self, model_data: StoryModelCreate) -> StoryModel:
        """Create a new Story Model"""
        data = model_data.model_dump(exclude_unset=True)

        # Convert sections and constraints to JSON
        if 'sections' in data:
            data['sections'] = json.dumps([s.model_dump() if hasattr(s, 'model_dump') else s for s in data['sections']])

        if 'constraints' in data:
            data['constraints'] = json.dumps([c.model_dump() if hasattr(c, 'model_dump') else c for c in data['constraints']])

        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = json.dumps(data['metadata'])

        model_id = self.storage.insert_one(
            "story_models",
            data,
            returning="id"
        )

        return self.get_story_model(model_id)

    def get_story_model(self, model_id: UUID) -> Optional[StoryModel]:
        """Get a Story Model by ID"""
        row = self.storage.get_one("story_models", model_id)
        if not row:
            return None

        # Parse JSON fields
        for field in ['sections', 'constraints', 'metadata']:
            if field in row and isinstance(row[field], str):
                row[field] = json.loads(row[field])

        return StoryModel(**row)

    def get_story_model_by_name(self, name: str) -> Optional[StoryModel]:
        """Get a Story Model by name"""
        rows = self.storage.get_many("story_models", filters={"name": name})
        if not rows:
            return None

        row = rows[0]
        for field in ['sections', 'constraints', 'metadata']:
            if field in row and isinstance(row[field], str):
                row[field] = json.loads(row[field])

        return StoryModel(**row)

    def list_story_models(self) -> List[StoryModel]:
        """List all Story Models"""
        rows = self.storage.get_many(
            "story_models",
            order_by="name ASC"
        )

        models = []
        for row in rows:
            for field in ['sections', 'constraints', 'metadata']:
                if field in row and isinstance(row[field], str):
                    row[field] = json.loads(row[field])
            models.append(StoryModel(**row))

        return models
