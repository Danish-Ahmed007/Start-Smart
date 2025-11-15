from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from .models import Business, SocialPost


class BaseAdapter(ABC):
    """
    Abstract base adapter that defines the contract any data-source adapter
    must implement for Phase 0 Part 2 of StartSmart.

    Implementations are responsible for fetching data from a specific
    upstream (e.g. Google Places, Instagram, Reddit, or simulation engine)
    and returning lists of domain models declared in `contracts.models`.

    Expectations / Contracts for implementations:
    - Methods should return an empty list when no results are available.
    - Methods should not raise exceptions for ordinary "not found" cases
      (network or upstream failures may raise exceptions; callers should
      handle/translate them as appropriate).
    - Implementations must not perform side-effects outside their scope
      (no database writes). They must only fetch/transform remote records
      into the Pydantic domain models.
    - All returned model fields should be populated when upstream provides
      them; otherwise use `None` for optional fields.
    """

    @abstractmethod
    def fetch_businesses(self, category: str, bounds: Dict[str, float]) -> List[Business]:
        """
        Fetch businesses for the requested category within the given bounding box.

        Parameters
        - category: The category string to query (caller may pass values from
          `contracts.models.Category` or free-form categories like "coffee").
        - bounds: A dictionary describing the bounding box with keys:
            - min_lat: float
            - max_lat: float
            - min_lon: float
            - max_lon: float

        Returns
        - A list of `Business` Pydantic models. Return an empty list if there
          are no matching businesses.

        Notes
        - Implementations are free to apply additional ranking/filters but must
          not mutate the input `bounds` parameter.
        - Network errors may raise exceptions; callers should handle retries
          or fallback behavior.
        """
        raise NotImplementedError()

    @abstractmethod
    def fetch_social_posts(self, category: str, bounds: Dict[str, float], days: int = 7) -> List[SocialPost]:
        """
        Fetch social posts for the requested category inside the bounding box
        from the last `days` days.

        Parameters
        - category: Category string used to filter posts (may be a hashtag,
          category name or other filter depending on the adapter).
        - bounds: Bounding box dict same format as `fetch_businesses`.
        - days: Number of days in the past to include posts from. Defaults to 7.

        Returns
        - A list of `SocialPost` models. Return an empty list when no posts
          match the criteria.

        Notes
        - Implementations may need to page through upstream APIs. They should
          aggregate results and return a consolidated list.
        - Timestamps must be returned as timezone-aware datetimes if available.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return a stable, machine-readable name for this adapter's upstream
        source. This string is used in the `source` fields of domain models
        (e.g. "google_places", "instagram", "reddit", "simulated").

        Returns
        - A short string identifying the upstream source.
        """
        raise NotImplementedError()


__all__ = ["BaseAdapter"]
