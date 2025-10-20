"""
Base Storage Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID


class BaseStorage(ABC):
    """Abstract base class for storage operations"""

    @abstractmethod
    def get_connection_string(self) -> str:
        """Get database connection string"""
        pass

    @abstractmethod
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
            Query results as list of dicts
        """
        pass

    @abstractmethod
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
        pass
