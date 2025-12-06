#!/usr/bin/env python3
"""CLI script to populate the businesses table using Google Places API.

Fetches business data for specified categories from Google Places API,
assigns grid cells based on geographic coordinates, and stores results
in the businesses table.

Features:
- Bulk fetch from Google Places API with pagination
- Automatic grid assignment using GeospatialService
- Database upsert (insert or update if exists)
- Dry-run mode for previewing changes
- Progress tracking with tqdm
- Comprehensive error handling and statistics
- Supports multiple neighborhoods

Usage:
    # Fetch gyms in DHA Phase 2 (use cached data if available)
    python3 backend/scripts/fetch_google_places.py \\
        --category Gym \\
        --neighborhood "DHA Phase 2, Karachi"

    # Force refetch (ignore cache)
    python3 backend/scripts/fetch_google_places.py \\
        --category Cafe \\
        --neighborhood "DHA Phase 2, Karachi" \\
        --force

    # Dry-run (show what would be inserted without modifying database)
    python3 backend/scripts/fetch_google_places.py \\
        --category Gym \\
        --neighborhood "DHA Phase 2, Karachi" \\
        --dry-run

    # Use custom API key
    python3 backend/scripts/fetch_google_places.py \\
        --category Gym \\
        --neighborhood "DHA Phase 2, Karachi" \\
        --api-key "YOUR_API_KEY"

Dependencies:
- argparse (stdlib)
- tqdm: pip install tqdm
- GooglePlacesAdapter, GeospatialService, DatabaseConnection
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.adapters.google_places_adapter import GooglePlacesAdapter
from backend.src.database.connection import get_session
from backend.src.database.models import BusinessModel, GridCellModel
from backend.src.services.geospatial_service import GeospatialService
from backend.src.utils.logger import Logger
from contracts.models import Category

logger = Logger.get_logger(__name__)


class GooglePlacesFetcher:
    """CLI handler for fetching businesses from Google Places API.
    
    Orchestrates:
    1. Loading grid cells for neighborhood
    2. Fetching businesses from API for each grid
    3. Assigning grid IDs to businesses
    4. Inserting/updating database records
    5. Tracking statistics
    """

    def __init__(
        self,
        category: str,
        neighborhood: str,
        api_key: str,
        force_refresh: bool = False,
        dry_run: bool = False,
    ):
        """Initialize fetcher.
        
        Args:
            category: "Gym" or "Cafe"
            neighborhood: e.g., "DHA-Phase2"
            api_key: Google Places API key
            force_refresh: Force refetch even if data exists
            dry_run: Fetch from API but don't insert into database
        """
        self.category = category
        self.neighborhood = neighborhood
        self.api_key = api_key
        self.force_refresh = force_refresh
        self.dry_run = dry_run

        # Initialize services
        self.adapter = GooglePlacesAdapter(api_key=api_key)
        self.geospatial = GeospatialService()

        # Statistics
        self.stats = {
            "total_businesses": 0,
            "businesses_per_grid": [],
            "grids_with_zero": [],
            "grids_processed": 0,
            "api_calls": 0,
            "duration_seconds": 0,
            "inserted": 0,
            "updated": 0,
            "failed": 0,
        }

    def run(self) -> int:
        """Execute the fetch workflow.
        
        Returns:
            0 on success, 1 on error
        """
        start_time = time.time()

        try:
            logger.info(f"Starting fetch for {self.category} in {self.neighborhood}")

            # Load grid cells for neighborhood
            grids = self._load_grids_for_neighborhood()
            if not grids:
                logger.error(f"No grids found for neighborhood {self.neighborhood}")
                return 1

            logger.info(f"Found {len(grids)} grids for {self.neighborhood}")

            # Process each grid
            for grid_num, grid in enumerate(tqdm(grids, desc="Processing grids"), 1):
                grid_id = grid.grid_id
                bounds = {
                    "min_lat": float(grid.min_lat),
                    "max_lat": float(grid.max_lat),
                    "min_lon": float(grid.min_lon),
                    "max_lon": float(grid.max_lon),
                }

                try:
                    # Fetch businesses from API
                    businesses = self.adapter.fetch_businesses(
                        category=self.category,
                        bounds=bounds,
                        grid_id=grid_id,
                        force_refresh=self.force_refresh,
                    )

                    self.stats["businesses_per_grid"].append(len(businesses))
                    self.stats["grids_processed"] += 1

                    if not businesses:
                        self.stats["grids_with_zero"].append(grid_id)
                        tqdm.write(f"Grid {grid_num}/{len(grids)}: {grid_id} - 0 businesses")
                        continue

                    # Process businesses
                    for business in businesses:
                        # Assign grid_id if not already set
                        if not business.grid_id:
                            try:
                                assigned_grid = self.geospatial.assign_grid_id(
                                    business.lat, business.lon
                                )
                                if assigned_grid:
                                    business.grid_id = assigned_grid
                            except Exception as e:
                                logger.warning(
                                    f"Failed to assign grid for {business.name}: {e}"
                                )

                        self.stats["total_businesses"] += 1

                    # Insert/update in database
                    if not self.dry_run:
                        inserted, updated = self._save_businesses(businesses, grid_id)
                        self.stats["inserted"] += inserted
                        self.stats["updated"] += updated

                    tqdm.write(
                        f"Grid {grid_num}/{len(grids)}: {grid_id} - {len(businesses)} businesses"
                    )

                except Exception as e:
                    logger.error(f"Failed to process grid {grid_id}: {e}", exc_info=True)
                    self.stats["failed"] += 1
                    tqdm.write(f"Grid {grid_num}/{len(grids)}: {grid_id} - FAILED ({e})")

            # Calculate statistics
            self.stats["duration_seconds"] = time.time() - start_time

            # Display summary
            self._display_summary()

            return 0

        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            return 1

    def _load_grids_for_neighborhood(self) -> List[GridCellModel]:
        """Load all grid cells for the specified neighborhood.
        
        Returns:
            List of GridCellModel objects
        """
        try:
            with get_session() as session:
                grids = (
                    session.query(GridCellModel)
                    .filter_by(neighborhood=self.neighborhood)
                    .all()
                )
                return grids
        except Exception as e:
            logger.error(f"Failed to load grids for {self.neighborhood}: {e}", exc_info=True)
            raise

    def _save_businesses(self, businesses: List, grid_id: str) -> Tuple[int, int]:
        """Save businesses to database (insert or update).
        
        Args:
            businesses: List of Business Pydantic models from adapter
            grid_id: Grid cell ID for batch operations
        
        Returns:
            Tuple of (inserted_count, updated_count)
        """
        inserted = 0
        updated = 0

        try:
            with get_session() as session:
                for business in businesses:
                    try:
                        # Check if business exists
                        existing = (
                            session.query(BusinessModel)
                            .filter_by(business_id=business.business_id)
                            .first()
                        )

                        if existing:
                            # Update existing record
                            existing.name = business.name
                            existing.lat = business.lat
                            existing.lon = business.lon
                            existing.category = business.category.value if business.category else None
                            existing.rating = business.rating
                            existing.review_count = business.review_count or 0
                            existing.source = business.source.value if business.source else None
                            existing.grid_id = business.grid_id or grid_id
                            existing.fetched_at = datetime.utcnow()
                            updated += 1
                        else:
                            # Create new record
                            new_business = BusinessModel(
                                business_id=business.business_id,
                                name=business.name,
                                lat=business.lat,
                                lon=business.lon,
                                category=business.category.value if business.category else None,
                                rating=business.rating,
                                review_count=business.review_count or 0,
                                source=business.source.value if business.source else None,
                                grid_id=business.grid_id or grid_id,
                                fetched_at=datetime.utcnow(),
                            )
                            session.add(new_business)
                            inserted += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to save business {business.business_id}: {e}"
                        )
                        continue

                # Commit all changes for this batch
                session.commit()

        except Exception as e:
            logger.error(f"Failed to save businesses for grid {grid_id}: {e}", exc_info=True)

        return inserted, updated

    def _display_summary(self) -> None:
        """Display comprehensive statistics."""
        total = self.stats["total_businesses"]
        processed = self.stats["grids_processed"]
        duration = self.stats["duration_seconds"]
        avg_per_grid = total / processed if processed > 0 else 0
        zeros = len(self.stats["grids_with_zero"])
        inserted = self.stats["inserted"]
        updated = self.stats["updated"]
        failed = self.stats["failed"]

        mode_text = "[DRY-RUN] " if self.dry_run else ""

        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print(
            "║ " + f"{mode_text}Google Places Fetch Summary".ljust(77) + "║"
        )
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")

        print(f"\n📊 STATISTICS:")
        print(f"  Category:              {self.category}")
        print(f"  Neighborhood:          {self.neighborhood}")
        print(f"  Total Businesses:      {total}")
        print(f"  Grids Processed:       {processed}")
        print(f"  Average per Grid:      {avg_per_grid:.1f}")
        print(f"  Grids with 0 results:  {zeros}")
        if zeros > 0:
            print(f"    → {', '.join(self.stats['grids_with_zero'][:3])}" +
                  ("..." if zeros > 3 else ""))
        print(f"  Failed Grids:          {failed}")

        if not self.dry_run:
            print(f"\n💾 DATABASE CHANGES:")
            print(f"  Inserted:              {inserted}")
            print(f"  Updated:               {updated}")
            print(f"  Total Modified:        {inserted + updated}")

        print(f"\n⏱️  PERFORMANCE:")
        print(f"  Duration:              {duration:.1f}s")
        if processed > 0 and duration > 0:
            print(f"  Grids/second:          {processed / duration:.2f}")
        print(f"  Timestamp:             {datetime.now().isoformat()}")

        if self.dry_run:
            print(f"\n⚠️  DRY-RUN MODE - No changes made to database")

        print("\n" + "═" * 80 + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch businesses from Google Places API and populate database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch gyms in DHA Phase 2
  python3 backend/scripts/fetch_google_places.py \\
    --category Gym \\
    --neighborhood "DHA Phase 2, Karachi"

  # Force refetch (ignore cache)
  python3 backend/scripts/fetch_google_places.py \\
    --category Cafe \\
    --neighborhood "DHA Phase 2, Karachi" \\
    --force

  # Dry-run mode (preview changes without inserting)
  python3 backend/scripts/fetch_google_places.py \\
    --category Gym \\
    --neighborhood "DHA Phase 2, Karachi" \\
    --dry-run

  # Custom API key
  python3 backend/scripts/fetch_google_places.py \\
    --category Gym \\
    --neighborhood "DHA Phase 2, Karachi" \\
    --api-key "YOUR_API_KEY"
        """,
    )

    parser.add_argument(
        "--category",
        required=True,
        choices=["Gym", "Cafe"],
        help="Business category to fetch (required)",
    )

    parser.add_argument(
        "--neighborhood",
        required=True,
        help='Neighborhood name (e.g., "DHA Phase 2, Karachi") (required)',
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="Google Places API key (default: GOOGLE_PLACES_API_KEY env var)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refetch even if data exists (ignore cache)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch from API but don't insert into database",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> Tuple[bool, Optional[str]]:
    """Validate command-line arguments.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check API key
    api_key = args.api_key or os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return False, (
            "API key not provided. Either pass --api-key or set "
            "GOOGLE_PLACES_API_KEY environment variable."
        )

    # Validate category
    if args.category not in ["Gym", "Cafe"]:
        return False, f"Invalid category: {args.category}. Must be 'Gym' or 'Cafe'."

    # Check if neighborhood exists in database
    try:
        with get_session() as session:
            exists = (
                session.query(GridCellModel)
                .filter_by(neighborhood=args.neighborhood)
                .first()
            )
            if not exists:
                # Get available neighborhoods
                neighborhoods = (
                    session.query(GridCellModel.neighborhood)
                    .distinct()
                    .all()
                )
                available = [n[0] for n in neighborhoods] if neighborhoods else []
                msg = f"Neighborhood not found: {args.neighborhood}."
                if available:
                    msg += f" Available: {', '.join(available)}"
                return False, msg
    except Exception as e:
        return False, f"Database error: {e}"

    return True, None


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(verbose=False)

    logger.info("Google Places Business Fetcher started")

    # Validate arguments
    is_valid, error_message = validate_args(args)
    if not is_valid:
        logger.error(f"Argument validation failed: {error_message}")
        print(f"❌ Error: {error_message}\n", file=sys.stderr)
        return 1

    # Get API key
    api_key = args.api_key or os.getenv("GOOGLE_PLACES_API_KEY")

    # Execute fetch
    try:
        fetcher = GooglePlacesFetcher(
            category=args.category,
            neighborhood=args.neighborhood,
            api_key=api_key,
            force_refresh=args.force,
            dry_run=args.dry_run,
        )

        return fetcher.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Fatal error: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
