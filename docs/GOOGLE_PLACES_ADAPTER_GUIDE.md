# Google Places Adapter - Production Features Guide

## Overview

The enhanced `GooglePlacesAdapter` includes production-ready features for handling real-world scenarios:
- **Raw Data Storage**: Audit trail of all API calls
- **Robust Error Handling**: API key validation, rate limiting, bounds validation
- **Request Throttling**: Respects Google's 10 req/sec limit
- **Cache-Aware Fetching**: 24-hour cache to reduce API quota usage
- **Comprehensive Logging**: All operations logged for debugging

## Quick Start

### Basic Usage with Caching

```python
from backend.src.adapters.google_places_adapter import GooglePlacesAdapter

adapter = GooglePlacesAdapter(api_key="YOUR_GOOGLE_PLACES_API_KEY")

# First call: Fetches from API, saves to cache
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={
        "min_lat": 24.85,
        "max_lat": 24.86,
        "min_lon": 67.01,
        "max_lon": 67.02,
    },
    grid_id="GRID_001"  # Required for caching
)

# Second call: Loads from cache (no API call)
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={...},
    grid_id="GRID_001"  # Same grid_id = cache hit
)

# Force fresh data from API (bypass cache)
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={...},
    grid_id="GRID_001",
    force_refresh=True  # Ignores cache
)
```

## Feature Details

### 1. Raw Data Storage

**Purpose**: Creates an audit trail of all API calls for debugging and analysis.

**Files Saved**: `data/raw/google_places/{grid_id}_{category}_{YYYYMMDD_HHMMSS}.json`

**File Structure**:
```json
{
  "grid_id": "GRID_001",
  "category": "Gym",
  "bounds": { "min_lat": 24.85, "max_lat": 24.86, "min_lon": 67.01, "max_lon": 67.02 },
  "timestamp": "2025-11-15T17:05:30.123456",
  "request_count": 3,
  "duration_ms": 1245.3,
  "result_count": 42,
  "businesses": [...]
}
```

### 2. Robust Error Handling

#### API Key Validation (401)
```python
try:
    adapter = GooglePlacesAdapter(api_key="invalid_key")
    businesses = adapter.fetch_businesses("Gym", bounds)
except ValueError as e:
    print(e)  # "Invalid Google Places API key (401 Unauthorized)"
```

#### Bounds Validation
```python
try:
    businesses = adapter.fetch_businesses(
        "Gym",
        bounds={"min_lat": 100, "max_lat": 24.86, ...}  # Invalid
    )
except ValueError as e:
    print(e)  # "Latitude must be between -90 and 90"
```

#### Rate Limit Handling (429)
The adapter automatically retries with exponential backoff:
- Attempt 1: Wait 1 second
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds
- Max total wait: 7 seconds

#### Empty Results
Empty results are logged as a warning, not an error:
```python
businesses = adapter.fetch_businesses("Gym", bounds)  # Returns []
# Log: "No Gym businesses found in bounds (...)"
```

### 3. Request Throttling

Automatically limits requests to 10 per second (100ms between requests) to respect Google's rate limits.

**Transparent behavior**: You don't need to do anything - throttling is automatic.

```
Request 1: t=0.000s   ✓ Immediate
Request 2: t=0.100s   ✓ Immediate (100ms since last)
Request 3: t=0.200s   ✓ Immediate (100ms since last)
Request 4: t=0.250s   ⏱ Sleep 50ms → t=0.300s ✓
```

### 4. Cache-Aware Fetching

**How it works**:
1. If `grid_id` provided and `force_refresh=False` (default):
   - Checks `data/raw/google_places/` for today's cache file
   - If found and < 24 hours old: returns cached data (no API call)
   - If expired or missing: fetches from API and creates new cache

2. If `grid_id` not provided:
   - Always fetches from API (no caching)

3. If `force_refresh=True`:
   - Bypasses cache check, fetches fresh data from API

**Cache Key Format**: `{grid_id}_{category}_{YYYYMMDD}*.json`

**Example**:
```
GRID_001_gym_20251115_170530.json  # Today's gym cache for GRID_001
GRID_001_cafe_20251114_092015.json # Yesterday's cafe cache (expired)
GRID_001_hotel_20251110_150000.json # Old hotel cache (> 24h, expired)
```

### 5. Comprehensive Logging

**INFO Level** (default):
```
Initialized GooglePlacesAdapter with API key (first 10 chars: AIzaSyD...)
Fetching Gym businesses within 353m of center (24.8510, 67.0110)
Fetched 42 Gym businesses (3 API requests, 1245.3ms)
Loaded 42 Gym businesses from cache (grid=GRID_001)
```

**WARNING Level**:
```
Unknown category: PowerYoga
No Gym businesses found in bounds (24.8500, 24.8520, 67.0100, 67.0120)
Rate limited by Google Places API (429). Retrying in 2s (attempt 2/3)
Failed to map place ChIJZX...: Invalid coordinates
```

**ERROR Level**:
```
Invalid Google Places API key (401 Unauthorized)
HTTP error 500 from Google Places API: Server Error
Failed to fetch businesses for Gym: [error details]
```

**DEBUG Level** (set `LOG_LEVEL=DEBUG` to see):
```
Throttling: sleeping 0.050s
Mapped Gym → gym
Bounds (...) → center (...), radius 353m
Calling Google Places Nearby Search (location=(...), radius=353m, type=gym)
Saved raw response to GRID_001_gym_20251115_170530.json: 42 businesses
Cache hit for GRID_001_gym: 42 businesses (age: 0.5h)
```

## Configuration

### Environment Variables

```bash
# Logging level
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

# Environment type (for logging format)
export ENVIRONMENT=development  # development, production (default: development)
```

### Constants (in adapter code)

```python
MIN_SECONDS_BETWEEN_REQUESTS = 0.1  # 10 requests/second
CACHE_EXPIRY_HOURS = 24             # 24-hour cache window
DATA_DIR = Path(...) / "data" / "raw" / "google_places"
```

## Best Practices

### 1. Always Provide grid_id for Caching
```python
# ✓ Good - enables caching
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds=bounds,
    grid_id="GRID_001"  # Enables 24h cache
)

# ✗ Bad - no caching
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds=bounds
)
```

### 2. Use force_refresh=True Sparingly
```python
# ✓ Normal operation - uses cache
businesses = adapter.fetch_businesses(..., grid_id="GRID_001")

# ✓ Manual refresh when needed
businesses = adapter.fetch_businesses(..., grid_id="GRID_001", force_refresh=True)
```

### 3. Handle Errors Gracefully
```python
try:
    businesses = adapter.fetch_businesses(...)
except ValueError as e:
    # Invalid bounds or API key
    logger.error(f"Validation error: {e}")
    businesses = []
except Exception as e:
    # Network or other errors
    logger.error(f"API error: {e}")
    businesses = []
```

### 4. Monitor Cache Size
Raw data files accumulate in `data/raw/google_places/`. Consider:
- Archiving files older than 30 days
- Deleting files older than 90 days
- Compressing to gzip format

## Troubleshooting

### "Invalid Google Places API key (401 Unauthorized)"
- Check your API key is correct
- Verify it's not expired in Google Cloud Console
- Ensure Places API is enabled

### "Rate limited by Google Places API (429)"
- Normal behavior - adapter retries automatically
- If persistent, reduce concurrent requests or upgrade API quota

### "No businesses found in bounds"
- Normal result when category has no businesses in area
- Check bounds are correct
- Try adjacent grid or different category

### Cache not working
- Ensure `grid_id` is provided
- Check `data/raw/google_places/` directory exists (created automatically)
- Check file permissions on data directory

### Low API performance
- Check throttling is working (DEBUG logs show sleep times)
- Verify network connectivity to Google APIs
- Monitor API quota usage in Google Cloud Console

## API Reference

### fetch_businesses()
```python
def fetch_businesses(
    category: str,              # "Gym", "Cafe", "Restaurant", "Hotel", "Shopping"
    bounds: Dict[str, float],   # {min_lat, max_lat, min_lon, max_lon}
    grid_id: Optional[str] = None,  # For caching
    force_refresh: bool = False     # Bypass cache
) -> List[Business]:            # Business models or []
    """Fetch businesses from Google Places API or cache."""
```

### Error Handling
```python
raises ValueError:   # Invalid bounds or API key (401)
raises APIError:     # Network or API errors (after retries)
returns []:          # Empty results or other errors (logged as warning)
```

## Migration from Old Version

Old code:
```python
businesses = adapter.fetch_businesses(category="Gym", bounds=bounds)
```

New code (with caching):
```python
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds=bounds,
    grid_id="GRID_001"  # Add this for caching
)
```

The adapter is backward compatible - old code still works (just without caching).

## Performance

Typical performance for 100 grids:

| Scenario | Requests | Time | API Calls |
|----------|----------|------|-----------|
| First fetch | 100 | ~5-10 min | 100-300 |
| With cache | 100 | ~0.1 sec | 0 |
| Force refresh | 100 | ~5-10 min | 100-300 |

## Next Steps

1. **Implement CLI script** with `--force` flag for manual refresh
2. **Add data cleanup** script to delete cache files older than 30 days
3. **Set up monitoring** for API errors and quota usage
4. **Create unit tests** for caching and error handling scenarios

## Support

For issues or questions:
1. Check DEBUG logs: `LOG_LEVEL=DEBUG`
2. Review raw data files: `data/raw/google_places/`
3. Check Google Cloud Console for API quota and errors
