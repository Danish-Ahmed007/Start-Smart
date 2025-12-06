"""Example usage of SQLAlchemy 2.0 database setup.

This file demonstrates how to use the DatabaseConnection, ORM models, and repositories.
Run this to verify the database setup is working correctly.

Usage:
    python backend/scripts/test_database.py --create-tables --populate-sample
"""
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.database import (
    get_db,
    get_session,
    Base,
    GridCellModel,
    BusinessModel,
    SocialPostModel,
    GridMetricsModel,
    UserFeedbackModel,
    GridRepository,
    BusinessRepository,
    SocialPostRepository,
    GridMetricsRepository,
    UserFeedbackRepository,
)
from backend.src.utils.logger import Logger

# Initialize logger
Logger()
logger = Logger.get_logger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    db = get_db()
    db.create_all_tables()
    logger.info("✓ Tables created successfully")


def list_tables():
    """List all tables in the database."""
    db = get_db()
    tables = db.get_table_names()
    logger.info(f"Tables in database: {tables}")
    return tables


def populate_sample_data():
    """Populate database with sample data."""
    logger.info("Populating sample data...")

    # Create sample grids
    grids = [
        GridCellModel(
            grid_id="grid-test-001",
            centroid_lat=24.8305,
            centroid_lon=67.0595,
            lat_north=24.8345,
            lat_south=24.8265,
            lon_west=67.0555,
            lon_east=67.0635,
            area_km2=0.5,
        ),
        GridCellModel(
            grid_id="grid-test-002",
            centroid_lat=24.8310,
            centroid_lon=67.0605,
            lat_north=24.8350,
            lat_south=24.8270,
            lon_west=67.0565,
            lon_east=67.0645,
            area_km2=0.5,
        ),
    ]

    for grid in grids:
        try:
            GridRepository.create(grid)
            logger.info(f"✓ Created grid {grid.grid_id}")
        except Exception as e:
            logger.warning(f"Grid {grid.grid_id} might already exist: {e}")

    # Create sample businesses
    businesses = [
        BusinessModel(
            business_id="biz-001",
            name="Fitness First Gym",
            lat=24.8305,
            lon=67.0595,
            category="Gym",
            rating=4.5,
            review_count=150,
            source="google_places",
            grid_id="grid-test-001",
            fetched_at=datetime.utcnow(),
        ),
        BusinessModel(
            business_id="biz-002",
            name="Coffee Corner",
            lat=24.8310,
            lon=67.0605,
            category="Cafe",
            rating=4.3,
            review_count=89,
            source="google_places",
            grid_id="grid-test-002",
            fetched_at=datetime.utcnow(),
        ),
    ]

    for biz in businesses:
        try:
            BusinessRepository.create(biz)
            logger.info(f"✓ Created business {biz.business_id} ({biz.name})")
        except Exception as e:
            logger.warning(f"Business {biz.business_id} might already exist: {e}")

    # Create sample social posts
    posts = [
        SocialPostModel(
            post_id="post-001",
            grid_id="grid-test-001",
            content="Looking for a good gym in this area!",
            post_type="demand",
            engagement_score=0.85,
            timestamp=datetime.utcnow() - timedelta(days=1),
            source="twitter",
            is_simulated=True,
        ),
        SocialPostModel(
            post_id="post-002",
            grid_id="grid-test-001",
            content="Just joined Fitness First! Amazing facilities!",
            post_type="mention",
            engagement_score=0.92,
            timestamp=datetime.utcnow(),
            source="twitter",
            is_simulated=True,
        ),
    ]

    for post in posts:
        try:
            SocialPostRepository.create(post)
            logger.info(f"✓ Created post {post.post_id} ({post.post_type})")
        except Exception as e:
            logger.warning(f"Post {post.post_id} might already exist: {e}")

    # Create sample metrics
    metrics = [
        GridMetricsModel(
            grid_id="grid-test-001",
            category="Gym",
            top_posts=["post-001", "post-002"],
            competitors=["biz-001"],
        ),
    ]

    for metric in metrics:
        try:
            GridMetricsRepository.create(metric)
            logger.info(f"✓ Created metrics for {metric.grid_id} ({metric.category})")
        except Exception as e:
            logger.warning(f"Metrics might already exist: {e}")

    # Create sample feedback
    feedback = [
        UserFeedbackModel(
            feedback_id="feedback-001",
            grid_id="grid-test-001",
            rating=1,
            comments="Great opportunities here!",
        ),
        UserFeedbackModel(
            feedback_id="feedback-002",
            grid_id="grid-test-001",
            rating=0,
            comments="Average area",
        ),
    ]

    for fb in feedback:
        try:
            UserFeedbackRepository.create(fb)
            logger.info(f"✓ Created feedback {fb.feedback_id} (rating: {fb.rating})")
        except Exception as e:
            logger.warning(f"Feedback {fb.feedback_id} might already exist: {e}")


def query_sample_data():
    """Query and display sample data."""
    logger.info("\n--- Querying Sample Data ---\n")

    # Query grids
    logger.info("Grids:")
    grids = GridRepository.list_all(limit=10)
    for grid in grids:
        logger.info(f"  {grid.grid_id}: ({grid.centroid_lat}, {grid.centroid_lon}) - {grid.area_km2} km²")

    # Query businesses
    logger.info("\nBusinesses in grid-test-001:")
    businesses = BusinessRepository.get_by_grid("grid-test-001", limit=10)
    for biz in businesses:
        logger.info(f"  {biz.name}: rating={biz.rating}, category={biz.category}")

    # Query posts
    logger.info("\nSocial posts in grid-test-001:")
    posts = SocialPostRepository.get_by_grid("grid-test-001", limit=10)
    for post in posts:
        logger.info(f"  {post.post_type}: {post.content[:50]}... (engagement: {post.engagement_score})")

    # Query metrics
    logger.info("\nMetrics for grid-test-001:")
    metrics = GridMetricsRepository.get_by_grid("grid-test-001")
    for metric in metrics:
        logger.info(f"  {metric.category}: top_posts={metric.top_posts}")

    # Query feedback
    logger.info("\nFeedback for grid-test-001:")
    feedback_items = UserFeedbackRepository.get_by_grid("grid-test-001", limit=10)
    for item in feedback_items:
        logger.info(f"  Rating: {item.rating}, Comment: {item.comments}")

    avg_rating = UserFeedbackRepository.get_average_rating("grid-test-001")
    logger.info(f"\nAverage rating: {avg_rating}")


def test_context_manager():
    """Test context manager pattern."""
    logger.info("\n--- Testing Context Manager Pattern ---\n")

    logger.info("Using context manager:")
    with get_session() as session:
        grids = session.query(GridCellModel).all()
        logger.info(f"Found {len(grids)} grids using context manager")


def drop_sample_data():
    """Drop all tables (for testing)."""
    logger.warning("Dropping all tables...")
    db = get_db()
    db.drop_all_tables()
    logger.info("✓ All tables dropped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test SQLAlchemy database setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create tables and populate sample data
  python backend/scripts/test_database.py --create-tables --populate-sample --query

  # Just create tables
  python backend/scripts/test_database.py --create-tables

  # Query existing data
  python backend/scripts/test_database.py --query

  # Clean up (drop all tables)
  python backend/scripts/test_database.py --drop
        """,
    )

    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create all tables from ORM models",
    )

    parser.add_argument(
        "--populate-sample",
        action="store_true",
        help="Populate database with sample data",
    )

    parser.add_argument(
        "--query",
        action="store_true",
        help="Query and display sample data",
    )

    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List all tables in database",
    )

    parser.add_argument(
        "--test-context-manager",
        action="store_true",
        help="Test context manager pattern",
    )

    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables (WARNING: destructive)",
    )

    args = parser.parse_args()

    try:
        if args.list_tables:
            list_tables()

        if args.create_tables:
            create_tables()

        if args.populate_sample:
            populate_sample_data()

        if args.query:
            query_sample_data()

        if args.test_context_manager:
            test_context_manager()

        if args.drop:
            confirm = input("Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == "yes":
                drop_sample_data()
            else:
                logger.info("Cancelled")

        if not any([args.create_tables, args.populate_sample, args.query,
                    args.list_tables, args.test_context_manager, args.drop]):
            parser.print_help()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
