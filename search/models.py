"""Data models for search results."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class SearchResult:
    """Represents one candidate result from a reverse image search."""
    platform: str
    url: str
    title: str = ""
    description: str = ""
    image_url: str = ""
    source: str = ""
    thumbnail_url: str = ""
    search_provider: str = ""
    discovery_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "source": self.source,
            "thumbnail_url": self.thumbnail_url,
            "search_provider": self.search_provider,
            "discovery_timestamp": self.discovery_timestamp,
        }
