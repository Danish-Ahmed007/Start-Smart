"""Simulated social adapter for synthetic data.

Adapter for fetching simulated social media data from the database.
Unlike GooglePlacesAdapter which uses external APIs, this adapter queries
the social_posts table where is_simulated=TRUE to provide test/demo data.

This adapter is useful for:
- Testing without external API calls
- Demo environments with reproducible data
- Development without rate limit concerns
- Performance testing with controlled datasets

Features:
- Database-backed queries (no external API calls)
- Geographic bounds filtering (lat/lon)
- Date range filtering (last N days)
- Category-based filtering
- Comprehensive logging and error handling
- Production-ready bounds validation

Usage:
    >>> adapter = SimulatedSocialAdapter()
    >>> posts = adapter.fetch_social_posts(
    ...     category="gym",
    ...     bounds={
    ...         "min_lat": 24.8500, "max_lat": 24.8520,
    ...         "min_lon": 67.0100, "max_lon": 67.0120,
    ...     },
    ...     days=7
    ... )
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from contracts.models import Business, SocialPost
from contracts.base_adapter import BaseAdapter
from ..database.connection import get_session
from ..database.models import SocialPostModel
from ..utils.logger import Logger


logger = Logger.get_logger(__name__)


class SimulatedSocialAdapter(BaseAdapter):
    """
    Adapter for simulated social data from database.
    
    Provides synthetic social posts by querying the social_posts table
    for records marked with is_simulated=TRUE. This adapter applies
    geographic and temporal filtering without making external API calls.
    
    Attributes:
        source_name: "simulated"
        logger: Logger instance for operational logging
    """

    def __init__(self) -> None:
        """Initialize simulated social adapter with database connection and logger."""
        self.source_name = "simulated"
        self.logger = Logger.get_logger(__name__)
        self.logger.info(f"Initialized {self.__class__.__name__}")

    def get_source_name(self) -> str:
        """
        Get the source name for this adapter.
        
        Returns:
            "simulated"
        """
        return self.source_name

    def fetch_businesses(
        self,
        category: str,
        bounds: Dict[str, float]
    ) -> List[Business]:
        """
        Fetch businesses from simulated data.
        
        Note:
            Simulated adapter does not provide business data.
            Use GooglePlacesAdapter or other sources.
        
        Args:
            category: Category string (ignored for simulated).
            bounds: Bounding box dict with min_lat, max_lat, min_lon, max_lon.
        
        Returns:
            Empty list (simulated adapter has no business data).
        """
        self.logger.debug(
            "Simulated adapter does not provide business data. "
            "Use GooglePlacesAdapter or other sources."
        )
        return []

    def fetch_social_posts(
        self,
        category: str,
        bounds: Dict[str, float],
        days: int = 7
    ) -> List[SocialPost]:
        """
        Fetch simulated social posts from database.
        
        Queries the social_posts table for records where is_simulated=TRUE,
        applies filters for date range and geographic bounds, and returns
        Pydantic SocialPost models.
        
        Filters applied:
        - is_simulated = TRUE (only simulated posts)
        - timestamp within last `days` days
        - latitude/longitude within geographic bounds
        - source matching category (if category provided)
        
        Args:
            category: Category string to filter posts (optional).
            bounds: Bounding box dict with keys:
                - min_lat: Minimum latitude (-90 to 90)
                - max_lat: Maximum latitude (-90 to 90)
                - min_lon: Minimum longitude (-180 to 180)
                - max_lon: Maximum longitude (-180 to 180)
            days: Number of days in the past to include (default 7).
        
        Returns:
            List of SocialPost Pydantic models matching criteria.
            Returns empty list on error or when no results found.
        
        Raises:
            No exceptions raised; errors are logged and empty list returned.
        """
        try:
            # Validate bounds before querying
            if not self._validate_bounds(bounds):
                self.logger.warning(f"Invalid bounds provided: {bounds}")
                return []
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            self.logger.debug(
                f"Querying simulated posts: category={category}, "
                f"bounds={bounds}, date_range={start_date} to {end_date}"
            )
            
            # Query database for simulated posts
            with get_session() as session:
                query = session.query(SocialPostModel).filter(
                    SocialPostModel.is_simulated == True,
                    SocialPostModel.timestamp >= start_date,
                    SocialPostModel.timestamp <= end_date,
                    SocialPostModel.lat >= bounds["min_lat"],
                    SocialPostModel.lat <= bounds["max_lat"],
                    SocialPostModel.lon >= bounds["min_lon"],
                    SocialPostModel.lon <= bounds["max_lon"],
                )
                
                # Optional category filter if category is provided
                if category:
                    query = query.filter(SocialPostModel.source == category)
                
                orm_results = query.all()
            
            # Convert ORM models to Pydantic models
            social_posts = []
            for orm_post in orm_results:
                try:
                    post_dict = orm_post.to_dict()
                    social_post = SocialPost(**post_dict)
                    social_posts.append(social_post)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert ORM post to Pydantic model: {e}"
                    )
                    continue
            
            # Log query results with row count and performance info
            self.logger.info(
                f"Fetched {len(social_posts)} simulated posts for "
                f"category={category}, days={days}, bounds_area="
                f"[{bounds['min_lat']:.4f},{bounds['max_lat']:.4f}]x"
                f"[{bounds['min_lon']:.4f},{bounds['max_lon']:.4f}]"
            )
            
            return social_posts
            
        except Exception as e:
            self.logger.error(
                f"Error fetching simulated social posts: {e}",
                exc_info=True
            )
            return []

    def _validate_bounds(self, bounds: Dict[str, float]) -> bool:
        """
        Validate geographic bounds.
        
        Checks that required keys exist and values are within valid ranges:
        - Latitude: -90 to 90
        - Longitude: -180 to 180
        - min <= max for both dimensions
        
        Args:
            bounds: Dictionary with min_lat, max_lat, min_lon, max_lon keys.
        
        Returns:
            True if bounds are valid, False otherwise.
        """
        required_keys = {"min_lat", "max_lat", "min_lon", "max_lon"}
        if not all(key in bounds for key in required_keys):
            self.logger.warning(f"Missing required bounds keys: {required_keys}")
            return False
        
        min_lat = bounds["min_lat"]
        max_lat = bounds["max_lat"]
        min_lon = bounds["min_lon"]
        max_lon = bounds["max_lon"]
        
        # Validate latitude range
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            self.logger.warning(f"Latitude out of range: min={min_lat}, max={max_lat}")
            return False
        
        # Validate longitude range
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            self.logger.warning(f"Longitude out of range: min={min_lon}, max={max_lon}")
            return False
        
        # Validate min <= max
        if min_lat > max_lat:
            self.logger.warning(f"Invalid latitude bounds: min={min_lat} > max={max_lat}")
            return False
        
        if min_lon > max_lon:
            self.logger.warning(f"Invalid longitude bounds: min={min_lon} > max={max_lon}")
            return False
        
        return True
