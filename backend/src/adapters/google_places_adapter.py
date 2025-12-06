"""Google Places API adapter for StartSmart backend.

Fetches business data from Google Places API and maps to Business domain models.

Features:
- Automatic category mapping (Gym -> gym, Cafe -> cafe)
- Pagination support (up to 60 results per grid cell)
- Retry logic with exponential backoff for rate limits
- Comprehensive error handling and logging
- Coordinate bounds to center point + radius conversion
- Raw API response storage for audit trail
- Request throttling (max 10 requests/second)
- Cache-aware fetching (checks today's cache before API call)
- Production-ready error handling

Usage:
    >>> adapter = GooglePlacesAdapter(api_key="YOUR_API_KEY")
    >>> businesses = adapter.fetch_businesses(
    ...     category="Gym",
    ...     bounds={
    ...         "min_lat": 24.8500, "max_lat": 24.8520,
    ...         "min_lon": 67.0100, "max_lon": 67.0120,
    ...     },
    ...     grid_id="GRID_001",
    ...     force_refresh=False  # Use cache if available
    ... )
"""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import googlemaps

from contracts.base_adapter import BaseAdapter
from contracts.models import Business, Category, Source, SocialPost
from ..utils.logger import Logger, log_api_call


logger = Logger.get_logger(__name__)

# Constants for production behavior
MAX_RESULTS_PER_REQUEST = 20
MAX_PAGINATION_REQUESTS = 3  # 3 pages = ~60 results
MIN_SECONDS_BETWEEN_REQUESTS = 0.1  # 10 requests/second max
CACHE_EXPIRY_HOURS = 24  # Cache raw responses for 24 hours
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "google_places"

# Category to Google Places type mapping
CATEGORY_TO_GOOGLE_TYPE = {
    "Gym": "gym",
    "Cafe": "cafe",
    "Restaurant": "restaurant",
    "Hotel": "hotel",
    "Shopping": "shopping_mall",
}


class GooglePlacesAdapter(BaseAdapter):
    """Adapter for fetching business data from Google Places API.
    
    Implements point-of-interest search within geographic bounds with
    automatic pagination, error handling, caching, and throttling.
    
    Production features:
    - Raw API response storage for audit trail
    - Request throttling (max 10 requests/second)
    - Cache-aware fetching (checks today's cache first)
    - Comprehensive error handling and logging
    - Exponential backoff retry for rate limits
    
    Attributes:
        client: googlemaps.Client instance
        api_key: Google Places API key
        source_name: "google_places"
        last_request_time: Timestamp of last API call (for throttling)
    """

    def __init__(self, api_key: str) -> None:
        """Initialize Google Places adapter with API key.

        Args:
            api_key: Google Places API key

        Raises:
            ValueError: If api_key is empty or invalid

        Example:
            >>> adapter = GooglePlacesAdapter(api_key="YOUR_KEY")
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("api_key must be a non-empty string")

        self.api_key = api_key
        self.client = googlemaps.Client(key=api_key)
        self.source_name = Source.google_places.value
        self.last_request_time: float = 0  # For throttling

        # Ensure raw data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized GooglePlacesAdapter with API key "
            f"(first 10 chars: {api_key[:10]}...)"
        )

    def fetch_businesses(
        self,
        category: str,
        bounds: Dict[str, float],
        grid_id: Optional[str] = None,
        force_refresh: bool = False,
    ) -> List[Business]:
        """Fetch businesses for a category within geographic bounds.

        Production-ready with caching and throttling.

        Args:
            category: Category name (e.g., "Gym", "Cafe")
            bounds: Bounding box with keys: min_lat, max_lat, min_lon, max_lon
            grid_id: Optional grid ID for cache key (required for caching)
            force_refresh: If True, bypass cache and refresh from API

        Returns:
            List of Business models, empty list if no results

        Raises:
            ValueError: If bounds are invalid

        Example:
            >>> businesses = adapter.fetch_businesses(
            ...     category="Gym",
            ...     bounds={
            ...         "min_lat": 24.8500, "max_lat": 24.8520,
            ...         "min_lon": 67.0100, "max_lon": 67.0120,
            ...     },
            ...     grid_id="GRID_001",
            ...     force_refresh=False
            ... )
            >>> print(f"Found {len(businesses)} gyms")
        """
        start_time = time.time()

        try:
            # Validate bounds before proceeding
            self._validate_bounds(bounds)

            # Map category to Google Places type
            google_type = self._map_category_to_type(category)
            if not google_type:
                logger.warning(
                    f"Unknown category: {category}. "
                    f"Available categories: {', '.join(CATEGORY_TO_GOOGLE_TYPE.keys())}"
                )
                return []

            # Check cache if grid_id provided and not forcing refresh
            if grid_id and not force_refresh:
                cached_businesses = self._load_cached_response(grid_id, category)
                if cached_businesses is not None:
                    logger.info(
                        f"Loaded {len(cached_businesses)} {category} businesses from cache "
                        f"(grid={grid_id})"
                    )
                    return cached_businesses

            # Calculate center point and search radius from bounds
            center, radius_m = self._bounds_to_center_radius(bounds)

            logger.info(
                f"Fetching {category} businesses within {radius_m:.0f}m "
                f"of center ({center[0]:.4f}, {center[1]:.4f})"
            )

            businesses = []
            page_token = None
            request_count = 0

            # Fetch with pagination
            for page_num in range(MAX_PAGINATION_REQUESTS):
                # Apply throttling: ensure min time between requests
                self._apply_throttle()
                request_count += 1

                # Call Google Places Nearby Search API
                places_result = self._places_nearby_with_retry(
                    location=center,
                    radius=int(radius_m),
                    type=google_type,
                    page_token=page_token,
                )

                # Extract businesses from response
                if "results" in places_result:
                    for place in places_result["results"]:
                        try:
                            business = self._map_place_to_business(place, category)
                            businesses.append(business)
                        except Exception as e:
                            logger.warning(
                                f"Failed to map place {place.get('place_id')}: {str(e)}"
                            )
                            continue

                # Check for next page
                page_token = places_result.get("next_page_token")
                if not page_token:
                    break

                # Google API requires a small delay between page requests
                logger.debug(f"Paginating to next results (page_token available)")
                time.sleep(0.2)

            duration_ms = (time.time() - start_time) * 1000

            # Save raw response for audit trail if grid_id provided
            if grid_id:
                self._save_raw_response(
                    grid_id=grid_id,
                    category=category,
                    bounds=bounds,
                    results=businesses,
                    request_count=request_count,
                    duration_ms=duration_ms,
                )

            log_api_call(
                logger,
                endpoint=f"/places/nearby?type={google_type}",
                method="GET",
                params={"category": category, "bounds": bounds},
                duration_ms=duration_ms,
                status_code=200,
            )

            if not businesses:
                logger.warning(
                    f"No {category} businesses found in bounds "
                    f"({bounds['min_lat']:.4f}, {bounds['max_lat']:.4f}, "
                    f"{bounds['min_lon']:.4f}, {bounds['max_lon']:.4f})"
                )
            else:
                logger.info(
                    f"Fetched {len(businesses)} {category} businesses "
                    f"({request_count} API requests, {duration_ms:.1f}ms)"
                )

            return businesses

        except ValueError as e:
            logger.error(f"Invalid bounds: {str(e)}")
            return []
        except Exception as e:
            logger.error(
                f"Failed to fetch businesses for {category}: {str(e)}",
                exc_info=True
            )
            return []

    def fetch_social_posts(
        self,
        category: str,
        bounds: Dict[str, float],
        days: int = 7,
    ) -> List[SocialPost]:
        """Not implemented for Google Places API (no social posts).

        Google Places does not provide social media data.
        This adapter only fetches businesses.

        Args:
            category: Ignored (not applicable to Google Places)
            bounds: Ignored (not applicable to Google Places)
            days: Ignored (not applicable to Google Places)

        Returns:
            Empty list (Google Places does not provide social posts)

        Raises:
            NotImplementedError: Always raises with informative message
        """
        raise NotImplementedError(
            "Google Places API does not provide social media posts. "
            "Use Instagram or Reddit adapters for social data."
        )

    def get_source_name(self) -> str:
        """Get the source identifier for this adapter.

        Returns:
            "google_places"

        Example:
            >>> adapter = GooglePlacesAdapter(api_key="KEY")
            >>> source = adapter.get_source_name()
            >>> assert source == "google_places"
        """
        return self.source_name

    def _validate_bounds(self, bounds: Dict[str, float]) -> None:
        """Validate geographic bounds are within acceptable ranges.

        Args:
            bounds: Dict with min_lat, max_lat, min_lon, max_lon

        Raises:
            ValueError: If bounds are invalid

        Example:
            >>> adapter._validate_bounds({
            ...     "min_lat": 24.8500, "max_lat": 24.8520,
            ...     "min_lon": 67.0100, "max_lon": 67.0120,
            ... })  # OK
            >>> adapter._validate_bounds({
            ...     "min_lat": 100,  # Invalid latitude
            ...     "max_lat": 24.8520,
            ...     "min_lon": 67.0100, "max_lon": 67.0120,
            ... })  # Raises ValueError
        """
        required_keys = {"min_lat", "max_lat", "min_lon", "max_lon"}
        if not all(k in bounds for k in required_keys):
            raise ValueError(f"bounds must contain keys: {required_keys}")

        min_lat = bounds["min_lat"]
        max_lat = bounds["max_lat"]
        min_lon = bounds["min_lon"]
        max_lon = bounds["max_lon"]

        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90: got {min_lat}, {max_lat}")
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180: got {min_lon}, {max_lon}")
        if min_lat >= max_lat:
            raise ValueError(f"min_lat ({min_lat}) must be less than max_lat ({max_lat})")
        if min_lon >= max_lon:
            raise ValueError(f"min_lon ({min_lon}) must be less than max_lon ({max_lon})")

    def _apply_throttle(self) -> None:
        """Apply request throttling to respect rate limits.

        Implements: max 10 requests/second = min 0.1s between requests
        """
        now = time.time()
        time_since_last_request = now - self.last_request_time

        if time_since_last_request < MIN_SECONDS_BETWEEN_REQUESTS:
            sleep_time = MIN_SECONDS_BETWEEN_REQUESTS - time_since_last_request
            logger.debug(f"Throttling: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cache_key(self, grid_id: str, category: str) -> str:
        """Generate cache key for grid+category.

        Args:
            grid_id: Grid identifier
            category: Category name

        Returns:
            Cache key string
        """
        return f"{grid_id}_{category.lower()}"

    def _get_cache_file_path(self, grid_id: str, category: str) -> Optional[Path]:
        """Get path to today's cached response file for grid+category.

        Args:
            grid_id: Grid identifier
            category: Category name

        Returns:
            Path to cache file if it exists and is fresh, None otherwise
        """
        try:
            # Look for cache files matching pattern: {grid_id}_{category}_{YYYYMMDD}.json
            today_str = datetime.now().strftime("%Y%m%d")
            pattern = f"{grid_id}_{category.lower()}_{today_str}*.json"

            cache_files = list(DATA_DIR.glob(pattern))
            if cache_files:
                return cache_files[0]  # Return first match (should be only one per day)
        except Exception as e:
            logger.debug(f"Error checking cache files: {str(e)}")

        return None

    def _load_cached_response(self, grid_id: str, category: str) -> Optional[List[Business]]:
        """Load cached businesses from file if available and fresh.

        Args:
            grid_id: Grid identifier
            category: Category name

        Returns:
            List of Business models if cache hit, None if cache miss
        """
        try:
            cache_file = self._get_cache_file_path(grid_id, category)
            if not cache_file or not cache_file.exists():
                logger.debug(f"No cache file for {grid_id}_{category}")
                return None

            # Check file age
            file_mtime = cache_file.stat().st_mtime
            file_age_hours = (time.time() - file_mtime) / 3600
            if file_age_hours > CACHE_EXPIRY_HOURS:
                logger.debug(f"Cache expired ({file_age_hours:.1f}h old): {cache_file.name}")
                return None

            # Load and parse cached response
            with open(cache_file, "r") as f:
                data = json.load(f)

            # Extract businesses from metadata
            businesses_data = data.get("businesses", [])
            businesses = [Business(**b) for b in businesses_data]

            logger.debug(
                f"Cache hit for {grid_id}_{category}: {len(businesses)} businesses "
                f"(age: {file_age_hours:.1f}h)"
            )
            return businesses

        except Exception as e:
            logger.warning(f"Error loading cache for {grid_id}_{category}: {str(e)}")
            return None

    def _save_raw_response(
        self,
        grid_id: str,
        category: str,
        bounds: Dict[str, float],
        results: List[Business],
        request_count: int,
        duration_ms: float,
    ) -> None:
        """Save raw API response with metadata to disk for audit trail.

        Args:
            grid_id: Grid identifier
            category: Category name
            bounds: Search bounds
            results: List of fetched businesses
            request_count: Number of API requests made
            duration_ms: Total duration in milliseconds
        """
        try:
            # Create filename: {grid_id}_{category}_{YYYYMMDD_HHMMSS}.json
            now = datetime.now()
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            filename = f"{grid_id}_{category.lower()}_{timestamp_str}.json"
            filepath = DATA_DIR / filename

            # Prepare metadata and response
            response_data = {
                "grid_id": grid_id,
                "category": category,
                "bounds": bounds,
                "timestamp": now.isoformat(),
                "request_count": request_count,
                "duration_ms": round(duration_ms, 1),
                "result_count": len(results),
                "businesses": [b.dict() for b in results],
            }

            # Write to file
            with open(filepath, "w") as f:
                json.dump(response_data, f, indent=2, default=str)

            logger.debug(
                f"Saved raw response to {filename}: {len(results)} businesses"
            )

        except Exception as e:
            logger.warning(
                f"Failed to save raw response for {grid_id}_{category}: {str(e)}"
            )

    def _map_category_to_type(self, category: str) -> Optional[str]:
        """Map our category names to Google Places types.

        Args:
            category: Category name (e.g., "Gym", "Cafe")

        Returns:
            Google Places type string, or None if not mapped
        """
        google_type = CATEGORY_TO_GOOGLE_TYPE.get(category)
        if google_type:
            logger.debug(f"Mapped {category} → {google_type}")
        return google_type

    def _bounds_to_center_radius(
        self,
        bounds: Dict[str, float],
    ) -> tuple[tuple[float, float], float]:
        """Convert geographic bounds to center point and search radius.

        Args:
            bounds: Dict with min_lat, max_lat, min_lon, max_lon

        Returns:
            Tuple of ((center_lat, center_lon), radius_in_meters)

        Example:
            >>> bounds = {
            ...     "min_lat": 24.8500, "max_lat": 24.8520,
            ...     "min_lon": 67.0100, "max_lon": 67.0120,
            ... }
            >>> center, radius = adapter._bounds_to_center_radius(bounds)
            >>> print(f"Center: {center}, Radius: {radius}m")
        """
        min_lat = bounds["min_lat"]
        max_lat = bounds["max_lat"]
        min_lon = bounds["min_lon"]
        max_lon = bounds["max_lon"]

        # Calculate center point
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        # Calculate radius as half the diagonal distance
        # Using Haversine formula for accurate geographic distance
        diagonal_m = self._haversine_distance(
            min_lat, min_lon,
            max_lat, max_lon,
        )
        radius_m = diagonal_m / 2

        logger.debug(
            f"Bounds ({min_lat:.4f}, {max_lat:.4f}, {min_lon:.4f}, {max_lon:.4f}) "
            f"→ center ({center_lat:.4f}, {center_lon:.4f}), radius {radius_m:.0f}m"
        )

        return (center_lat, center_lon), radius_m

    @staticmethod
    def _haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula.

        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate

        Returns:
            Distance in meters
        """
        R_KM = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R_KM * c * 1000  # Convert to meters

    def _places_nearby_with_retry(
        self,
        location: tuple[float, float],
        radius: int,
        type: str,
        page_token: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict:
        """Call Google Places Nearby Search with retry logic.

        Implements exponential backoff for rate limit (429) errors.
        Handles API key validation and network errors.

        Args:
            location: (lat, lon) tuple
            radius: Search radius in meters
            type: Place type (e.g., "gym", "cafe")
            page_token: Pagination token from previous request
            max_retries: Maximum number of retry attempts

        Returns:
            API response dictionary

        Raises:
            ValueError: If API key is invalid
            googlemaps.exceptions.APIError: If all retries exhausted or network error
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Calling Google Places Nearby Search "
                    f"(location={location}, radius={radius}m, type={type})"
                )

                response = self.client.places_nearby(
                    location=location,
                    radius=radius,
                    type=type,
                    page_token=page_token,
                )

                logger.debug(f"Google Places API response: {len(response.get('results', []))} results")
                return response

            except googlemaps.exceptions.HTTPError as e:
                # Handle different HTTP errors
                if e.status == 401:  # Unauthorized - invalid API key
                    error_msg = "Invalid Google Places API key (401 Unauthorized)"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                elif e.status == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Rate limited by Google Places API (429). "
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)

                else:  # Other HTTP errors
                    logger.error(
                        f"HTTP error {e.status} from Google Places API: {str(e)}",
                        exc_info=True
                    )
                    raise

            except Exception as e:
                logger.error(
                    f"Error calling Google Places API: {str(e)}",
                    exc_info=True
                )
                raise

        # All retries exhausted
        raise googlemaps.exceptions.APIError(
            f"Google Places API rate limited after {max_retries} retries"
        )

    def _map_place_to_business(
        self,
        place: Dict,
        category: str,
    ) -> Business:
        """Map Google Place response to Business domain model.

        Args:
            place: Google Place result object
            category: Category string (for validation)

        Returns:
            Business model instance

        Raises:
            ValueError: If place data is invalid

        Example:
            >>> place = {
            ...     "place_id": "ChIJZX...",
            ...     "name": "Gold Gym",
            ...     "geometry": {"location": {"lat": 24.85, "lng": 67.01}},
            ...     "rating": 4.5,
            ...     "user_ratings_total": 123,
            ... }
            >>> business = adapter._map_place_to_business(place, "Gym")
            >>> print(business.business_id)  # ChIJZX...
        """
        place_id = place.get("place_id")
        name = place.get("name", "Unknown")
        geometry = place.get("geometry", {})
        location = geometry.get("location", {})
        lat = location.get("lat")
        lon = location.get("lng")
        rating = place.get("rating")
        review_count = place.get("user_ratings_total", 0)

        logger.debug(
            f"Mapping place {place_id}: {name} "
            f"({lat:.4f}, {lon:.4f}), rating={rating}, reviews={review_count}"
        )

        return Business(
            business_id=place_id,
            name=name,
            lat=lat,
            lon=lon,
            category=Category[category],  # Map string to Enum
            rating=rating,
            review_count=review_count,
            source=Source.google_places,
            fetched_at=None,  # Will be set by adapter caller
        )
