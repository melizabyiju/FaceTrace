"""SerpAPI Google Lens reverse image search provider."""
import os
from typing import List

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None

from .base import SearchProvider
from .models import SearchResult
from .image_upload import upload_image_for_url


SOCIAL_PLATFORMS = [
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "linkedin.com", "tiktok.com", "pinterest.com", "reddit.com",
    "youtube.com", "tumblr.com", "flickr.com", "vk.com",
]


def _detect_platform(url: str) -> str:
    """Guess the social platform from a URL."""
    lower = url.lower()
    for domain in SOCIAL_PLATFORMS:
        if domain in lower:
            return domain.split(".")[0].capitalize()
    return "Web"


class SerpAPIProvider(SearchProvider):
    """Performs genuine reverse image search using Google Lens via SerpAPI."""

    def __init__(self, api_key: str):
        if GoogleSearch is None:
            raise ImportError(
                "serpapi package not installed. Run: pip install google-search-results"
            )
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "SerpAPI Google Lens"

    def search(self, image_path: str) -> List[SearchResult]:
        """
        Upload the local image, send it to Google Lens via SerpAPI,
        and return parsed SearchResult objects.
        """
        # 1. Upload image to obtain a public URL
        print("[Search] Uploading image for reverse search...")
        image_url = upload_image_for_url(image_path)
        if not image_url:
            raise RuntimeError("Failed to upload image for reverse search.")
        print(f"[Search] Image URL: {image_url}")

        # 2. Call SerpAPI Google Lens
        print("[Search] Querying Google Lens via SerpAPI...")
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.api_key,
        }
        raw = GoogleSearch(params).get_dict()

        results: List[SearchResult] = []

        # 3a. Visual matches
        for match in raw.get("visual_matches", []):
            link = match.get("link", "")
            if not link:
                continue
            results.append(
                SearchResult(
                    platform=_detect_platform(link),
                    url=link,
                    title=match.get("title", ""),
                    description=match.get("snippet", ""),
                    image_url=match.get("thumbnail", ""),
                    source=match.get("source", ""),
                    thumbnail_url=match.get("thumbnail", ""),
                    search_provider=self.provider_name,
                )
            )

        # 3b. Knowledge graph entries
        kg = raw.get("knowledge_graph", [])
        if isinstance(kg, list):
            for item in kg:
                link = item.get("link", "")
                if not link:
                    continue
                results.append(
                    SearchResult(
                        platform=_detect_platform(link),
                        url=link,
                        title=item.get("title", ""),
                        description=item.get("subtitle", ""),
                        source="Knowledge Graph",
                        search_provider=self.provider_name,
                    )
                )

        print(f"[Search] Found {len(results)} candidate(s).")
        return results
