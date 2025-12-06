import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure repository root is on sys.path so tests can import package modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import backend.src.adapters.google_places_adapter as gpa
from contracts.models import Category, Source

        mock_client.places_nearby.return_value = mock_api_response_with_results
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def adapter(mock_api_key, mock_googlemaps_client):
    """Fixture: GooglePlacesAdapter instance with mocked client."""
    adapter = GooglePlacesAdapter(api_key=mock_api_key)
    return adapter


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture: Temporary directory for raw data storage."""
    data_dir = tmp_path / "data" / "raw" / "google_places"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch DATA_DIR in adapter module
    with patch(
        "backend.src.adapters.google_places_adapter.DATA_DIR",
        data_dir,
    ):
        yield data_dir


# ============================================================================
# TESTS: Successful API Calls
# ============================================================================


class TestFetchBusinessesSuccess:
    """Test successful business fetching scenarios."""

    def test_fetch_businesses_success(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        mock_place_response_2,
    ):
        """Test successful fetch of businesses from Google Places API."""
        # Arrange
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1, mock_place_response_2],
            "status": "OK",
        }

        # Act
        businesses = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        assert len(businesses) == 2
        assert all(isinstance(b, Business) for b in businesses)

        # Verify first business
        assert businesses[0].business_id == "ChIJ1234567890abcdef"
        assert businesses[0].name == "Gold Gym"
        assert businesses[0].lat == 24.8510
        assert businesses[0].lon == 67.0110
        assert businesses[0].rating == 4.5
        assert businesses[0].review_count == 250
        assert businesses[0].category == Category.Gym
        assert businesses[0].source == Source.google_places

        # Verify second business
        assert businesses[1].business_id == "ChIJ9876543210fedcba"
        assert businesses[1].name == "Elite Fitness"
        assert businesses[1].rating == 4.2
        assert businesses[1].review_count == 180

        # Verify API was called correctly
        mock_googlemaps_client.places_nearby.assert_called_once()
        call_kwargs = mock_googlemaps_client.places_nearby.call_args[1]
        assert call_kwargs["type"] == "gym"

    def test_fetch_businesses_empty_results(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
    ):
        """Test fetch_businesses when API returns empty results."""
        # Arrange
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [],
            "status": "OK",
        }

        # Act
        businesses = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        assert businesses == []

    def test_fetch_businesses_cafe_category(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
    ):
        """Test fetch_businesses with Cafe category."""
        # Arrange
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        # Act
        businesses = adapter.fetch_businesses(
            category="Cafe",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        assert len(businesses) == 1
        assert businesses[0].category == Category.Cafe
        mock_googlemaps_client.places_nearby.assert_called_once()
        call_kwargs = mock_googlemaps_client.places_nearby.call_args[1]
        assert call_kwargs["type"] == "cafe"


# ============================================================================
# TESTS: Pagination
# ============================================================================


class TestFetchBusinessesPagination:
    """Test pagination handling."""

    def test_fetch_businesses_pagination_two_pages(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        mock_place_response_2,
    ):
        """Test fetch_businesses handles pagination correctly."""
        # Arrange
        page_1_response = {
            "results": [mock_place_response_1],
            "status": "OK",
            "next_page_token": "CqQCEAAAA...",
        }
        page_2_response = {
            "results": [mock_place_response_2],
            "status": "OK",
        }

        mock_googlemaps_client.places_nearby.side_effect = [
            page_1_response,
            page_2_response,
        ]

        # Act
        businesses = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        assert len(businesses) == 2
        assert businesses[0].name == "Gold Gym"
        assert businesses[1].name == "Elite Fitness"

        # Verify API was called twice (for pagination)
        assert mock_googlemaps_client.places_nearby.call_count == 2

    def test_fetch_businesses_pagination_max_pages(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        mock_place_response_2,
    ):
        """Test fetch_businesses respects MAX_PAGINATION_REQUESTS limit."""
        # Arrange: Create response with next_page_token on all pages
        response_with_token = {
            "results": [mock_place_response_1],
            "status": "OK",
            "next_page_token": "CqQCEAAAA...",
        }

        # Mock to always return a response with token
        mock_googlemaps_client.places_nearby.return_value = response_with_token

        # Act
        businesses = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert: Should stop at MAX_PAGINATION_REQUESTS (3 pages)
        from backend.src.adapters.google_places_adapter import MAX_PAGINATION_REQUESTS

        assert mock_googlemaps_client.places_nearby.call_count == MAX_PAGINATION_REQUESTS
        # Each page has 1 result, so 3 total
        assert len(businesses) == MAX_PAGINATION_REQUESTS


# ============================================================================
# TESTS: Error Handling
# ============================================================================


class TestFetchBusinessesErrorHandling:
    """Test error handling in fetch_businesses."""

    def test_fetch_businesses_invalid_api_key(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
    ):
        """Test fetch_businesses raises error on invalid API key (401)."""
        # Arrange
        import googlemaps

        error = googlemaps.exceptions.HTTPError(401, "Unauthorized")
        mock_googlemaps_client.places_nearby.side_effect = error

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid Google Places API key"):
            adapter.fetch_businesses(
                category="Gym",
                bounds=test_bounds,
                grid_id=test_grid_id,
            )

    def test_fetch_businesses_rate_limit_retry(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
    ):
        """Test fetch_businesses retries on rate limit (429) error."""
        # Arrange
        import googlemaps

        rate_limit_error = googlemaps.exceptions.HTTPError(429, "Rate limited")
        success_response = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        # First call fails with rate limit, second succeeds
        mock_googlemaps_client.places_nearby.side_effect = [
            rate_limit_error,
            success_response,
        ]

        # Act
        with patch("time.sleep"):  # Mock sleep to speed up test
            businesses = adapter.fetch_businesses(
                category="Gym",
                bounds=test_bounds,
                grid_id=test_grid_id,
            )

        # Assert
        assert len(businesses) == 1
        assert mock_googlemaps_client.places_nearby.call_count == 2

    def test_fetch_businesses_rate_limit_exhausted(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
    ):
        """Test fetch_businesses raises error after max retries on rate limit."""
        # Arrange
        import googlemaps

        rate_limit_error = googlemaps.exceptions.HTTPError(429, "Rate limited")
        mock_googlemaps_client.places_nearby.side_effect = rate_limit_error

        # Act & Assert
        with patch("time.sleep"):  # Mock sleep to speed up test
            with pytest.raises(googlemaps.exceptions.APIError):
                adapter.fetch_businesses(
                    category="Gym",
                    bounds=test_bounds,
                    grid_id=test_grid_id,
                )

    def test_fetch_businesses_invalid_bounds(
        self,
        adapter,
    ):
        """Test fetch_businesses raises error on invalid bounds."""
        # Act & Assert
        invalid_bounds = {
            "min_lat": 100,  # Invalid latitude
            "max_lat": 24.8520,
            "min_lon": 67.0100,
            "max_lon": 67.0120,
        }

        with pytest.raises(ValueError):
            adapter.fetch_businesses(
                category="Gym",
                bounds=invalid_bounds,
            )

    def test_fetch_businesses_missing_bounds_keys(
        self,
        adapter,
    ):
        """Test fetch_businesses raises error on missing bounds keys."""
        # Arrange
        invalid_bounds = {
            "min_lat": 24.8500,
            "max_lat": 24.8520,
            # Missing min_lon and max_lon
        }

        # Act & Assert
        with pytest.raises(ValueError):
            adapter.fetch_businesses(
                category="Gym",
                bounds=invalid_bounds,
            )


# ============================================================================
# TESTS: Category Mapping
# ============================================================================


class TestCategoryMapping:
    """Test category to Google Places type mapping."""

    def test_category_mapping_gym(self, adapter):
        """Test Gym category maps to 'gym'."""
        assert CATEGORY_TO_GOOGLE_TYPE["Gym"] == "gym"

    def test_category_mapping_cafe(self, adapter):
        """Test Cafe category maps to 'cafe'."""
        assert CATEGORY_TO_GOOGLE_TYPE["Cafe"] == "cafe"

    def test_category_mapping_all_entries(self):
        """Test all expected categories are mapped."""
        expected = {"Gym": "gym", "Cafe": "cafe"}
        assert CATEGORY_TO_GOOGLE_TYPE == expected


# ============================================================================
# TESTS: Raw Data Storage
# ============================================================================


class TestRawDataStorage:
    """Test raw response storage functionality."""

    def test_save_raw_response_creates_file(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        temp_data_dir,
    ):
        """Test _save_raw_response creates JSON file."""
        # Arrange
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        # Act
        businesses = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert: Check that cache file was created
        cache_files = list(temp_data_dir.glob("*.json"))
        assert len(cache_files) > 0

        # Verify file contents
        with open(cache_files[0], "r") as f:
            data = json.load(f)

        assert data["grid_id"] == test_grid_id
        assert data["category"] == "Gym"
        assert data["bounds"] == test_bounds
        assert data["result_count"] == 1
        assert len(data["businesses"]) == 1
        assert data["businesses"][0]["business_id"] == "ChIJ1234567890abcdef"

    def test_raw_response_contains_metadata(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        temp_data_dir,
    ):
        """Test raw response file contains correct metadata."""
        # Arrange
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        # Act
        adapter.fetch_businesses(
            category="Cafe",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        cache_files = list(temp_data_dir.glob("*.json"))
        assert len(cache_files) > 0

        with open(cache_files[0], "r") as f:
            data = json.load(f)

        # Check metadata fields
        assert "timestamp" in data
        assert "request_count" in data
        assert "duration_ms" in data
        assert "result_count" in data
        assert data["category"] == "Cafe"


# ============================================================================
# TESTS: Bounds Validation
# ============================================================================


class TestBoundsValidation:
    """Test geographic bounds validation."""

    def test_validate_bounds_valid(self, adapter, test_bounds):
        """Test _validate_bounds accepts valid bounds."""
        # Should not raise
        adapter._validate_bounds(test_bounds)

    def test_validate_bounds_invalid_latitude(self, adapter):
        """Test _validate_bounds rejects invalid latitude."""
        # Arrange
        invalid_bounds = {
            "min_lat": 100,
            "max_lat": 24.8520,
            "min_lon": 67.0100,
            "max_lon": 67.0120,
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            adapter._validate_bounds(invalid_bounds)

    def test_validate_bounds_invalid_longitude(self, adapter):
        """Test _validate_bounds rejects invalid longitude."""
        # Arrange
        invalid_bounds = {
            "min_lat": 24.8500,
            "max_lat": 24.8520,
            "min_lon": 200,
            "max_lon": 67.0120,
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            adapter._validate_bounds(invalid_bounds)

    def test_validate_bounds_min_greater_than_max_lat(self, adapter):
        """Test _validate_bounds rejects when min_lat > max_lat."""
        # Arrange
        invalid_bounds = {
            "min_lat": 24.8520,
            "max_lat": 24.8500,  # min > max
            "min_lon": 67.0100,
            "max_lon": 67.0120,
        }

        # Act & Assert
        with pytest.raises(ValueError, match="min_lat.*must be less than max_lat"):
            adapter._validate_bounds(invalid_bounds)

    def test_validate_bounds_missing_keys(self, adapter):
        """Test _validate_bounds rejects missing keys."""
        # Arrange
        invalid_bounds = {
            "min_lat": 24.8500,
            "max_lat": 24.8520,
            # Missing min_lon and max_lon
        }

        # Act & Assert
        with pytest.raises(ValueError, match="bounds must contain keys"):
            adapter._validate_bounds(invalid_bounds)


# ============================================================================
# TESTS: Throttling
# ============================================================================


class TestThrottling:
    """Test request throttling."""

    def test_throttle_sleeps_when_needed(self, adapter):
        """Test _apply_throttle sleeps when requests too frequent."""
        # Arrange
        from backend.src.adapters.google_places_adapter import MIN_SECONDS_BETWEEN_REQUESTS

        adapter.last_request_time = time.time()

        # Act
        with patch("time.sleep") as mock_sleep:
            adapter._apply_throttle()

            # Assert: sleep should have been called
            # (since last_request_time is too recent)
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            assert 0 < sleep_time <= MIN_SECONDS_BETWEEN_REQUESTS

    def test_throttle_no_sleep_when_enough_time_passed(self, adapter):
        """Test _apply_throttle doesn't sleep when enough time passed."""
        # Arrange
        from backend.src.adapters.google_places_adapter import MIN_SECONDS_BETWEEN_REQUESTS

        adapter.last_request_time = time.time() - MIN_SECONDS_BETWEEN_REQUESTS - 1

        # Act
        with patch("time.sleep") as mock_sleep:
            adapter._apply_throttle()

            # Assert: sleep should not be called
            mock_sleep.assert_not_called()


# ============================================================================
# TESTS: Place to Business Mapping
# ============================================================================


class TestPlaceToBusinessMapping:
    """Test mapping Google Place responses to Business models."""

    def test_map_place_to_business_success(
        self,
        adapter,
        mock_place_response_1,
    ):
        """Test _map_place_to_business creates correct Business model."""
        # Act
        business = adapter._map_place_to_business(mock_place_response_1, "Gym")

        # Assert
        assert business.business_id == "ChIJ1234567890abcdef"
        assert business.name == "Gold Gym"
        assert business.lat == 24.8510
        assert business.lon == 67.0110
        assert business.rating == 4.5
        assert business.review_count == 250
        assert business.category == Category.Gym
        assert business.source == Source.google_places

    def test_map_place_to_business_missing_optional_fields(self, adapter):
        """Test _map_place_to_business handles missing optional fields."""
        # Arrange
        place = {
            "place_id": "ChIJtest",
            "name": "Test Gym",
            "geometry": {
                "location": {"lat": 24.85, "lng": 67.01}
            },
            # Missing: rating, user_ratings_total
        }

        # Act
        business = adapter._map_place_to_business(place, "Gym")

        # Assert
        assert business.business_id == "ChIJtest"
        assert business.name == "Test Gym"
        assert business.rating is None
        assert business.review_count == 0  # Default value

    def test_map_place_to_business_cafe_category(
        self,
        adapter,
        mock_place_response_1,
    ):
        """Test _map_place_to_business with Cafe category."""
        # Act
        business = adapter._map_place_to_business(mock_place_response_1, "Cafe")

        # Assert
        assert business.category == Category.Cafe


# ============================================================================
# TESTS: Caching
# ============================================================================


class TestCaching:
    """Test caching functionality."""

    def test_cache_hit_returns_cached_data(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        temp_data_dir,
    ):
        """Test fetch_businesses uses cached data when available."""
        # Arrange: First fetch to populate cache
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        first_fetch = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Clear the mock to verify cache is used
        mock_googlemaps_client.reset_mock()

        # Act: Second fetch should use cache
        second_fetch = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Assert
        assert len(second_fetch) == len(first_fetch)
        # API should not be called again (cache hit)
        mock_googlemaps_client.places_nearby.assert_not_called()

    def test_force_refresh_bypasses_cache(
        self,
        adapter,
        test_bounds,
        test_grid_id,
        mock_googlemaps_client,
        mock_place_response_1,
        mock_place_response_2,
        temp_data_dir,
    ):
        """Test fetch_businesses with force_refresh=True bypasses cache."""
        # Arrange: First fetch to populate cache
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_1],
            "status": "OK",
        }

        adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
        )

        # Setup second response with different data
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [mock_place_response_2],
            "status": "OK",
        }

        # Act: Force refresh should bypass cache
        result = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            grid_id=test_grid_id,
            force_refresh=True,
        )

        # Assert
        assert len(result) == 1
        assert result[0].name == "Elite Fitness"  # New data
        # API should be called again
        assert mock_googlemaps_client.places_nearby.call_count == 2


# ============================================================================
# TESTS: Haversine Distance Calculation
# ============================================================================


class TestHaversineDistance:
    """Test Haversine distance calculation."""

    def test_haversine_distance_karachi_bounds(self, adapter):
        """Test haversine distance calculation for test bounds."""
        # The distance from (24.85, 67.01) to (24.8520, 67.0120)
        distance = adapter._haversine_distance(
            24.8500, 67.0100,
            24.8520, 67.0120,
        )

        # Should be approximately 1.9 km
        assert 1000 < distance < 3000  # Roughly 1-3 km

    def test_haversine_distance_zero(self, adapter):
        """Test haversine distance is zero for same coordinates."""
        distance = adapter._haversine_distance(24.85, 67.01, 24.85, 67.01)

        assert distance == 0


# ============================================================================
# TESTS: Source Name
# ============================================================================


class TestGetSourceName:
    """Test get_source_name method."""

    def test_get_source_name_returns_google_places(self, adapter):
        """Test get_source_name returns 'google_places'."""
        assert adapter.get_source_name() == "google_places"


# ============================================================================
# TESTS: Fetch Social Posts Not Implemented
# ============================================================================


class TestFetchSocialPosts:
    """Test fetch_social_posts (not implemented)."""

    def test_fetch_social_posts_raises_not_implemented(self, adapter, test_bounds):
        """Test fetch_social_posts raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            adapter.fetch_social_posts(
                category="Gym",
                bounds=test_bounds,
            )


# ============================================================================
# TESTS: Bounds to Center and Radius
# ============================================================================


class TestBoundsToCenter:
    """Test bounds to center point and radius conversion."""

    def test_bounds_to_center_radius(self, adapter, test_bounds):
        """Test _bounds_to_center_radius calculates center correctly."""
        # Act
        center, radius = adapter._bounds_to_center_radius(test_bounds)

        # Assert: Center should be at the midpoint
        expected_lat = (test_bounds["min_lat"] + test_bounds["max_lat"]) / 2
        expected_lon = (test_bounds["min_lon"] + test_bounds["max_lon"]) / 2

        assert abs(center[0] - expected_lat) < 0.0001
        assert abs(center[1] - expected_lon) < 0.0001

        # Radius should be positive
        assert radius > 0

    def test_bounds_to_center_radius_returns_tuple(self, adapter, test_bounds):
        """Test _bounds_to_center_radius returns (center, radius) tuple."""
        # Act
        result = adapter._bounds_to_center_radius(test_bounds)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        center, radius = result
        assert isinstance(center, tuple)
        assert len(center) == 2
        assert isinstance(radius, float)
