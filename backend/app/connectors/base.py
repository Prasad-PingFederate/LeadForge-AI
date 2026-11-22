from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseConnector(ABC):
    """Abstract base class for all lead & intelligence connectors."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Execute search and return a list of structured records.
        Every record MUST have a verifiable external source URL (Zero Hallucination Rule).
        """
        pass
