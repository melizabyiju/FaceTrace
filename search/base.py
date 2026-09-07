"""Abstract base class for search providers."""
from abc import ABC, abstractmethod
from typing import List
from .models import SearchResult


class SearchProvider(ABC):
    """Base class for reverse image search providers."""

    @abstractmethod
    def search(self, image_path: str) -> List[SearchResult]:
        """
        Perform reverse image search using a local image file.

        Args:
            image_path: Absolute path to the query image.

        Returns:
            A list of SearchResult objects found online.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of this search provider."""
        pass
