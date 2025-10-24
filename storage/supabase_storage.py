"""
Supabase Storage Implementation

Uses Supabase PostgREST API instead of direct psycopg connections
"""
import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import create_client, Client
from .base import BaseStorage


class SupabaseStorage(BaseStorage):
    """Supabase storage using PostgREST API"""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize storage

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not set in environment")
        if not self.supabase_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set in environment")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def get_connection_string(self) -> str:
        """Get Supabase URL (not a traditional connection string)"""
        return self.supabase_url

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: str = "all"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query using Supabase RPC

        Note: This is limited - PostgREST prefers table operations
        For now, we'll raise NotImplementedError and use table methods
        """
        raise NotImplementedError(
            "Raw SQL queries not supported in Supabase storage. "
            "Use insert_one, update_one, get_one, get_many instead."
        )

    def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """Execute a query multiple times"""
        raise NotImplementedError("Use insert_one in a loop instead")

    def insert_one(
        self,
        table: str,
        data: Dict[str, Any],
        returning: str = "id"
    ) -> Any:
        """
        Insert a single row using PostgREST

        Args:
            table: Table name
            data: Column: value mapping
            returning: Column to return (usually 'id')

        Returns:
            Value of the returned column
        """
        # Convert UUIDs to strings for JSON serialization
        serialized_data = self._serialize_data(data)

        result = self.client.table(table).insert(serialized_data).execute()

        if result.data and len(result.data) > 0:
            return result.data[0].get(returning)

        return None

    def update_one(
        self,
        table: str,
        id_value: Any,
        data: Dict[str, Any],
        id_column: str = "id"
    ) -> bool:
        """
        Update a single row

        Args:
            table: Table name
            id_value: ID value
            data: Column: value mapping
            id_column: ID column name (default: 'id')

        Returns:
            True if row was updated
        """
        # Convert UUIDs to strings for JSON serialization
        serialized_data = self._serialize_data(data)

        result = self.client.table(table).update(serialized_data).eq(id_column, str(id_value)).execute()
        return len(result.data) > 0 if result.data else False

    def get_one(
        self,
        table: str,
        id_value: Any,
        id_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single row by ID

        Args:
            table: Table name
            id_value: ID value
            id_column: ID column name (default: 'id')

        Returns:
            Row as dict or None
        """
        result = self.client.table(table).select("*").eq(id_column, str(id_value)).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]

        return None

    def get_many(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get multiple rows with optional filtering

        Args:
            table: Table name
            filters: Column: value filters (AND condition)
            limit: Max rows to return
            offset: Number of rows to skip
            order_by: ORDER BY clause (e.g., 'created_at DESC')

        Returns:
            List of rows as dicts
        """
        query = self.client.table(table).select("*")

        # Apply filters
        if filters:
            for col, val in filters.items():
                query = query.eq(col, str(val) if val is not None else None)

        # Apply ordering
        if order_by:
            # Parse "column_name ASC/DESC" format
            parts = order_by.split()
            if len(parts) >= 1:
                column = parts[0].replace(',', '')  # Remove commas
                ascending = True if len(parts) == 1 or parts[1].upper() == 'ASC' else False
                query = query.order(column, desc=not ascending)

        # Apply limit
        if limit:
            query = query.limit(limit)

        # Apply offset
        if offset:
            query = query.range(offset, offset + (limit or 1000) - 1)

        result = query.execute()
        return result.data if result.data else []

    def delete_one(
        self,
        table: str,
        id_value: Any,
        id_column: str = "id"
    ) -> bool:
        """
        Delete a single row by ID

        Args:
            table: Table name
            id_value: ID value
            id_column: ID column name (default: 'id')

        Returns:
            True if row was deleted
        """
        result = self.client.table(table).delete().eq(id_column, str(id_value)).execute()
        return len(result.data) > 0 if result.data else False

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert UUIDs and other non-JSON-serializable types to strings

        Args:
            data: Data dictionary

        Returns:
            Serialized data dictionary
        """
        serialized = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                serialized[key] = str(value)
            elif isinstance(value, list):
                # Handle lists of UUIDs
                serialized[key] = [str(v) if isinstance(v, UUID) else v for v in value]
            else:
                serialized[key] = value
        return serialized
