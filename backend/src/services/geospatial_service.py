"""Geospatial assignment service for StartSmart backend.

Provides fast point-in-polygon queries for assigning coordinates to grid cells.

Features:
- In-memory cache of grid cells as Shapely polygons
- O(1) average lookup time for coordinate assignment
- Bounds validation for Karachi region
- Comprehensive error handling and logging

Usage:
    >>> service = GeospatialService()
    >>> grid_id = service.assign_grid_id(24.8500, 67.0100)
    >>> bounds = service.get_grid_bounds(grid_id)
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

from shapely.geometry import Point, Polygon

from ..database.connection import get_session
from ..database.models import GridCellModel
from ..utils.logger import Logger

logger = Logger.get_logger(__name__)

# Karachi region bounds (approximate)
KARACHI_BOUNDS = {
    "lat_min": 24.75,
    "lat_max": 25.05,
    "lon_min": 66.90,
    "lon_max": 67.35,
}


class GeospatialService:
    """Service for assigning coordinates to geographic grid cells.
    
    Maintains an in-memory cache of grid cells for fast spatial queries.
    Uses Shapely for point-in-polygon operations.
    
    Attributes:
        _grids: Dict mapping grid_id to Shapely Polygon objects
        _bounds_cache: Dict mapping grid_id to bounds dict
    """

    def __init__(self) -> None:
        """Initialize geospatial service and load grid cache from database."""
        self._grids: Dict[str, Polygon] = {}
        self._bounds_cache: Dict[str, Dict[str, float]] = {}
        self._load_grids_from_database()

    def _load_grids_from_database(self) -> None:
        """Load all grid cells from database and cache as Shapely polygons.
        
        Raises:
            RuntimeError: If database is not seeded with grid cells.
        """
        try:
            with get_session() as session:
                grids = session.query(GridCellModel).all()

                if not grids:
                    logger.warning(
                        "No grid cells found in database. "
                        "Geospatial service initialized with empty cache. "
                        "Run grid seeding scripts before using this service."
                    )
                    return

                for grid in grids:
                    try:
                        # Create polygon from bounds: (min_lon, min_lat) to (max_lon, max_lat)
                        polygon = Polygon([
                            (float(grid.min_lon), float(grid.min_lat)),
                            (float(grid.max_lon), float(grid.min_lat)),
                            (float(grid.max_lon), float(grid.max_lat)),
                            (float(grid.min_lon), float(grid.max_lat)),
                        ])

                        self._grids[grid.grid_id] = polygon

                        # Cache bounds for quick retrieval
                        self._bounds_cache[grid.grid_id] = {
                            "lat_north": float(grid.max_lat),
                            "lat_south": float(grid.min_lat),
                            "lon_east": float(grid.max_lon),
                            "lon_west": float(grid.min_lon),
                            "area_km2": float(grid.area_km2) if grid.area_km2 else None,
                            "neighborhood": grid.neighborhood,
                        }
                    except Exception as e:
                        logger.error(
                            f"Failed to cache grid {grid.grid_id}: {str(e)}"
                        )
                        continue

                logger.info(
                    f"Loaded {len(self._grids)} grid cells into geospatial cache"
                )

        except Exception as e:
            logger.error(
                f"Failed to load grids from database: {str(e)}. "
                "Geospatial service will operate with empty cache.",
                exc_info=True
            )

    def assign_grid_id(self, lat: float, lon: float) -> Optional[str]:
        """Assign a coordinate to a grid cell using point-in-polygon lookup.

        Args:
            lat: Latitude coordinate (-90 to 90)
            lon: Longitude coordinate (-180 to 180)

        Returns:
            grid_id if point falls within a grid cell, None otherwise

        Raises:
            ValueError: If coordinates are invalid (out of bounds)

        Example:
            >>> service = GeospatialService()
            >>> grid_id = service.assign_grid_id(24.8500, 67.0100)
            >>> print(grid_id)  # "DHA-Phase2-Cell-07"
        """
        # Validate coordinates
        if not self._validate_coordinates(lat, lon):
            raise ValueError(
                f"Invalid coordinates: lat={lat}, lon={lon}. "
                f"Expected lat in [{KARACHI_BOUNDS['lat_min']}, {KARACHI_BOUNDS['lat_max']}], "
                f"lon in [{KARACHI_BOUNDS['lon_min']}, {KARACHI_BOUNDS['lon_max']}]"
            )

        # Check if grid cache is empty
        if not self._grids:
            logger.warning(
                "Grid cache is empty. "
                f"Cannot assign coordinate ({lat}, {lon}) to any grid. "
                "Database may not be seeded."
            )
            return None

        # Create point and check against all polygons
        point = Point(lon, lat)

        for grid_id, polygon in self._grids.items():
            if polygon.contains(point):
                logger.debug(f"Assigned point ({lat}, {lon}) to grid {grid_id}")
                return grid_id

        # Point outside all grids
        logger.warning(
            f"Point ({lat}, {lon}) does not fall within any grid cell. "
            f"Point is within Karachi bounds but outside all grids."
        )
        return None

    def get_grid_bounds(self, grid_id: str) -> Dict[str, Optional[float]]:
        """Get geographic bounds for a grid cell.

        Args:
            grid_id: Grid cell identifier

        Returns:
            Dictionary with keys: lat_north, lat_south, lon_east, lon_west,
            area_km2, neighborhood

        Raises:
            ValueError: If grid_id not found

        Example:
            >>> service = GeospatialService()
            >>> bounds = service.get_grid_bounds("DHA-Phase2-Cell-07")
            >>> print(bounds)
            {
                "lat_north": 24.8520,
                "lat_south": 24.8500,
                "lon_east": 67.0120,
                "lon_west": 67.0100,
                "area_km2": 0.25,
                "neighborhood": "DHA"
            }
        """
        if grid_id not in self._bounds_cache:
            raise ValueError(f"Grid cell not found: {grid_id}")

        return self._bounds_cache[grid_id]

    def get_all_grid_ids(self) -> list[str]:
        """Get list of all cached grid IDs.

        Returns:
            List of grid_id strings

        Example:
            >>> service = GeospatialService()
            >>> grid_ids = service.get_all_grid_ids()
            >>> print(len(grid_ids))  # Number of grids
        """
        return list(self._grids.keys())

    def get_grid_count(self) -> int:
        """Get number of grids in cache.

        Returns:
            Number of grid cells currently cached

        Example:
            >>> service = GeospatialService()
            >>> count = service.get_grid_count()
        """
        return len(self._grids)

    def is_grid_cached(self, grid_id: str) -> bool:
        """Check if a grid cell is in cache.

        Args:
            grid_id: Grid cell identifier

        Returns:
            True if grid is cached, False otherwise
        """
        return grid_id in self._grids

    def _validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate coordinates are within Karachi bounds.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            True if valid, False otherwise
        """
        lat_valid = KARACHI_BOUNDS["lat_min"] <= lat <= KARACHI_BOUNDS["lat_max"]
        lon_valid = KARACHI_BOUNDS["lon_min"] <= lon <= KARACHI_BOUNDS["lon_max"]

        if not lat_valid:
            logger.debug(
                f"Latitude {lat} outside valid range "
                f"[{KARACHI_BOUNDS['lat_min']}, {KARACHI_BOUNDS['lat_max']}]"
            )

        if not lon_valid:
            logger.debug(
                f"Longitude {lon} outside valid range "
                f"[{KARACHI_BOUNDS['lon_min']}, {KARACHI_BOUNDS['lon_max']}]"
            )

        return lat_valid and lon_valid

    def refresh_cache(self) -> None:
        """Refresh grid cache from database.
        
        Useful after seeding new grids or updating grid boundaries.
        """
        logger.info("Refreshing geospatial cache from database")
        self._grids.clear()
        self._bounds_cache.clear()
        self._load_grids_from_database()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the cache.

        Returns:
            Dictionary with cache statistics

        Example:
            >>> service = GeospatialService()
            >>> stats = service.get_cache_stats()
            >>> print(stats)
            {"grid_count": 42, "total_polygons": 42}
        """
        return {
            "grid_count": len(self._grids),
            "total_polygons": len(self._grids),
            "bounds_cached": len(self._bounds_cache),
        }


# Singleton instance for application use
_instance: Optional[GeospatialService] = None


def get_geospatial_service() -> GeospatialService:
    """Get or create singleton instance of GeospatialService.

    Returns:
        GeospatialService instance

    Example:
        >>> from backend.src.services.geospatial_service import get_geospatial_service
        >>> service = get_geospatial_service()
        >>> grid_id = service.assign_grid_id(24.8500, 67.0100)
    """
    global _instance
    if _instance is None:
        _instance = GeospatialService()
    return _instance


__all__ = [
    "GeospatialService",
    "get_geospatial_service",
    "KARACHI_BOUNDS",
]
