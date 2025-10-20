"""
PostgreSQL Storage Implementation

Direct psycopg connections to Supabase
"""
import os
from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row
from .base import BaseStorage


class PostgresStorage(BaseStorage):
    """PostgreSQL storage using psycopg"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize storage

        Args:
            connection_string: PostgreSQL connection string
                             If not provided, will build from SUPABASE_URL
        """
        self._connection_string = connection_string or self._build_connection_string()

    def _build_connection_string(self) -> str:
        """Build connection string from environment variables"""
        # Check for explicit DATABASE_URL first
        db_url = os.getenv('DATABASE_URL')
        if db_url and '[YOUR-PASSWORD]' not in db_url:
            # Valid DATABASE_URL found
            return db_url

        # Fall back to building from components
        supabase_url = os.getenv('SUPABASE_URL')
        if not supabase_url:
            raise ValueError("SUPABASE_URL not set in environment")

        # Extract project reference from URL
        # Format: https://PROJECT_REF.supabase.co
        project_ref = supabase_url.split('//')[1].split('.')[0]

        # Build connection string for Supabase
        db_password = os.getenv('DATABASE_PASSWORD')
        if not db_password:
            raise ValueError(
                "DATABASE_PASSWORD not set. Get it from Supabase Settings → Database"
            )

        return (
            f"postgresql://postgres.{project_ref}:{db_password}"
            f"@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )

    def get_connection_string(self) -> str:
        """Get database connection string"""
        return self._connection_string

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: str = "all"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Query parameters
            fetch: 'all', 'one', or 'none'

        Returns:
            Query results as list of dicts (or single dict if fetch='one')
        """
        with psycopg.connect(self._connection_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())

                if fetch == "all":
                    return cur.fetchall()
                elif fetch == "one":
                    result = cur.fetchone()
                    return [result] if result else None
                else:  # fetch == "none"
                    conn.commit()
                    return None

    def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """
        Execute a query multiple times with different parameters

        Returns:
            Number of rows affected
        """
        with psycopg.connect(self._connection_string) as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                conn.commit()
                return cur.rowcount

    def insert_one(
        self,
        table: str,
        data: Dict[str, Any],
        returning: str = "id"
    ) -> Any:
        """
        Insert a single row

        Args:
            table: Table name (with schema if needed)
            data: Column: value mapping
            returning: Column to return (usually 'id')

        Returns:
            Value of the returned column
        """
        columns = list(data.keys())
        placeholders = [f"%s" for _ in columns]

        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING {returning}
        """

        result = self.execute_query(query, tuple(data.values()), fetch="one")
        return result[0][returning] if result else None

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
            table: Table name (with schema if needed)
            id_value: ID value
            data: Column: value mapping
            id_column: ID column name (default: 'id')

        Returns:
            True if row was updated
        """
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {id_column} = %s
        """

        params = tuple(list(data.values()) + [id_value])
        self.execute_query(query, params, fetch="none")
        return True

    def get_one(
        self,
        table: str,
        id_value: Any,
        id_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single row by ID

        Args:
            table: Table name (with schema if needed)
            id_value: ID value
            id_column: ID column name (default: 'id')

        Returns:
            Row as dict or None
        """
        query = f"SELECT * FROM {table} WHERE {id_column} = %s"
        result = self.execute_query(query, (id_value,), fetch="one")
        return result[0] if result else None

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
            table: Table name (with schema if needed)
            filters: Column: value filters (AND condition)
            limit: Max rows to return
            offset: Number of rows to skip
            order_by: ORDER BY clause (e.g., 'created_at DESC')

        Returns:
            List of rows as dicts
        """
        query = f"SELECT * FROM {table}"
        params = []

        if filters:
            where_clauses = []
            for col, val in filters.items():
                where_clauses.append(f"{col} = %s")
                params.append(val)
            query += " WHERE " + " AND ".join(where_clauses)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        if offset:
            query += f" OFFSET {offset}"

        return self.execute_query(query, tuple(params) if params else None, fetch="all")
