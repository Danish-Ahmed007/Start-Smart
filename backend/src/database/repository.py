"""Database repository layer for CRUD operations and queries.

Provides a high-level interface for database operations using SQLAlchemy ORM.
All methods use the context manager pattern for automatic session management.
"""
from __future__ import annotations

from typing import Optional, List

from sqlalchemy.orm import Session

from ..utils.logger import Logger
from .connection import get_db, get_session
from .models import GridCellModel, BusinessModel, SocialPostModel, GridMetricsModel, UserFeedbackModel

logger = Logger.get_logger(__name__)


class GridRepository:
    """Repository for grid_cells operations."""

    @staticmethod
    def get_by_id(grid_id: str) -> Optional[GridCellModel]:
        """Get a grid cell by ID."""
        try:
            with get_session() as session:
                return session.query(GridCellModel).filter_by(grid_id=grid_id).first()
        except Exception as e:
            logger.error(f"Error fetching grid {grid_id}: {e}")
            raise

    @staticmethod
    def list_all(limit: int = 100, offset: int = 0) -> List[GridCellModel]:
        """List all grid cells with pagination."""
        try:
            with get_session() as session:
                return session.query(GridCellModel).limit(limit).offset(offset).all()
        except Exception as e:
            logger.error(f"Error listing grids: {e}")
            raise

    @staticmethod
    def create(grid: GridCellModel) -> GridCellModel:
        """Create a new grid cell."""
        try:
            with get_session() as session:
                session.add(grid)
                session.flush()
                logger.info(f"Created grid {grid.grid_id}")
                return grid
        except Exception as e:
            logger.error(f"Error creating grid: {e}")
            raise

    @staticmethod
    def update(grid_id: str, **kwargs) -> Optional[GridCellModel]:
        """Update a grid cell."""
        try:
            with get_session() as session:
                grid = session.query(GridCellModel).filter_by(grid_id=grid_id).first()
                if grid:
                    for key, value in kwargs.items():
                        if hasattr(grid, key):
                            setattr(grid, key, value)
                    session.flush()
                    logger.info(f"Updated grid {grid_id}")
                return grid
        except Exception as e:
            logger.error(f"Error updating grid {grid_id}: {e}")
            raise

    @staticmethod
    def delete(grid_id: str) -> bool:
        """Delete a grid cell."""
        try:
            with get_session() as session:
                result = session.query(GridCellModel).filter_by(grid_id=grid_id).delete()
                logger.info(f"Deleted grid {grid_id}")
                return result > 0
        except Exception as e:
            logger.error(f"Error deleting grid {grid_id}: {e}")
            raise


class BusinessRepository:
    """Repository for businesses operations."""

    @staticmethod
    def get_by_id(business_id: str) -> Optional[BusinessModel]:
        """Get a business by ID."""
        try:
            with get_session() as session:
                return session.query(BusinessModel).filter_by(business_id=business_id).first()
        except Exception as e:
            logger.error(f"Error fetching business {business_id}: {e}")
            raise

    @staticmethod
    def get_by_grid(grid_id: str, limit: int = 100) -> List[BusinessModel]:
        """Get all businesses in a grid."""
        try:
            with get_session() as session:
                return (
                    session.query(BusinessModel)
                    .filter_by(grid_id=grid_id)
                    .order_by(BusinessModel.name)
                    .limit(limit)
                    .all()
                )
        except Exception as e:
            logger.error(f"Error fetching businesses for grid {grid_id}: {e}")
            raise

    @staticmethod
    def create(business: BusinessModel) -> BusinessModel:
        """Create a new business."""
        try:
            with get_session() as session:
                session.add(business)
                session.flush()
                logger.info(f"Created business {business.business_id}")
                return business
        except Exception as e:
            logger.error(f"Error creating business: {e}")
            raise

    @staticmethod
    def create_many(businesses: List[BusinessModel]) -> int:
        """Bulk create businesses."""
        try:
            with get_session() as session:
                session.add_all(businesses)
                session.flush()
                logger.info(f"Created {len(businesses)} businesses")
                return len(businesses)
        except Exception as e:
            logger.error(f"Error bulk creating businesses: {e}")
            raise

    @staticmethod
    def delete_by_grid(grid_id: str) -> int:
        """Delete all businesses in a grid."""
        try:
            with get_session() as session:
                count = session.query(BusinessModel).filter_by(grid_id=grid_id).delete()
                logger.info(f"Deleted {count} businesses from grid {grid_id}")
                return count
        except Exception as e:
            logger.error(f"Error deleting businesses for grid {grid_id}: {e}")
            raise


class SocialPostRepository:
    """Repository for social_posts operations."""

    @staticmethod
    def get_by_id(post_id: str) -> Optional[SocialPostModel]:
        """Get a social post by ID."""
        try:
            with get_session() as session:
                return session.query(SocialPostModel).filter_by(post_id=post_id).first()
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            raise

    @staticmethod
    def get_by_grid(grid_id: str, limit: int = 100, offset: int = 0) -> List[SocialPostModel]:
        """Get posts in a grid with pagination."""
        try:
            with get_session() as session:
                return (
                    session.query(SocialPostModel)
                    .filter_by(grid_id=grid_id)
                    .order_by(SocialPostModel.timestamp.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )
        except Exception as e:
            logger.error(f"Error fetching posts for grid {grid_id}: {e}")
            raise

    @staticmethod
    def get_by_type(grid_id: str, post_type: str, limit: int = 100) -> List[SocialPostModel]:
        """Get posts of a specific type in a grid."""
        try:
            with get_session() as session:
                return (
                    session.query(SocialPostModel)
                    .filter_by(grid_id=grid_id, post_type=post_type)
                    .order_by(SocialPostModel.engagement_score.desc())
                    .limit(limit)
                    .all()
                )
        except Exception as e:
            logger.error(f"Error fetching {post_type} posts for grid {grid_id}: {e}")
            raise

    @staticmethod
    def create(post: SocialPostModel) -> SocialPostModel:
        """Create a new social post."""
        try:
            with get_session() as session:
                session.add(post)
                session.flush()
                logger.info(f"Created post {post.post_id}")
                return post
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise

    @staticmethod
    def create_many(posts: List[SocialPostModel]) -> int:
        """Bulk create social posts."""
        try:
            with get_session() as session:
                session.add_all(posts)
                session.flush()
                logger.info(f"Created {len(posts)} posts")
                return len(posts)
        except Exception as e:
            logger.error(f"Error bulk creating posts: {e}")
            raise

    @staticmethod
    def delete_by_grid(grid_id: str) -> int:
        """Delete all posts in a grid."""
        try:
            with get_session() as session:
                count = session.query(SocialPostModel).filter_by(grid_id=grid_id).delete()
                logger.info(f"Deleted {count} posts from grid {grid_id}")
                return count
        except Exception as e:
            logger.error(f"Error deleting posts for grid {grid_id}: {e}")
            raise


class GridMetricsRepository:
    """Repository for grid_metrics operations."""

    @staticmethod
    def get_by_grid_and_category(grid_id: str, category: str) -> Optional[GridMetricsModel]:
        """Get metrics for a grid and category."""
        try:
            with get_session() as session:
                return (
                    session.query(GridMetricsModel)
                    .filter_by(grid_id=grid_id, category=category)
                    .first()
                )
        except Exception as e:
            logger.error(f"Error fetching metrics for grid {grid_id}/{category}: {e}")
            raise

    @staticmethod
    def get_by_grid(grid_id: str) -> List[GridMetricsModel]:
        """Get all metrics for a grid."""
        try:
            with get_session() as session:
                return session.query(GridMetricsModel).filter_by(grid_id=grid_id).all()
        except Exception as e:
            logger.error(f"Error fetching metrics for grid {grid_id}: {e}")
            raise

    @staticmethod
    def create(metrics: GridMetricsModel) -> GridMetricsModel:
        """Create new metrics."""
        try:
            with get_session() as session:
                session.add(metrics)
                session.flush()
                logger.info(f"Created metrics for grid {metrics.grid_id}")
                return metrics
        except Exception as e:
            logger.error(f"Error creating metrics: {e}")
            raise

    @staticmethod
    def update(metric_id: int, **kwargs) -> Optional[GridMetricsModel]:
        """Update metrics."""
        try:
            with get_session() as session:
                metrics = session.query(GridMetricsModel).filter_by(metric_id=metric_id).first()
                if metrics:
                    for key, value in kwargs.items():
                        if hasattr(metrics, key):
                            setattr(metrics, key, value)
                    session.flush()
                    logger.info(f"Updated metrics {metric_id}")
                return metrics
        except Exception as e:
            logger.error(f"Error updating metrics {metric_id}: {e}")
            raise


class UserFeedbackRepository:
    """Repository for user_feedback operations."""

    @staticmethod
    def get_by_id(feedback_id: str) -> Optional[UserFeedbackModel]:
        """Get feedback by ID."""
        try:
            with get_session() as session:
                return session.query(UserFeedbackModel).filter_by(feedback_id=feedback_id).first()
        except Exception as e:
            logger.error(f"Error fetching feedback {feedback_id}: {e}")
            raise

    @staticmethod
    def get_by_grid(grid_id: str, limit: int = 100) -> List[UserFeedbackModel]:
        """Get feedback for a grid."""
        try:
            with get_session() as session:
                return (
                    session.query(UserFeedbackModel)
                    .filter_by(grid_id=grid_id)
                    .order_by(UserFeedbackModel.created_at.desc())
                    .limit(limit)
                    .all()
                )
        except Exception as e:
            logger.error(f"Error fetching feedback for grid {grid_id}: {e}")
            raise

    @staticmethod
    def create(feedback: UserFeedbackModel) -> UserFeedbackModel:
        """Create new feedback."""
        try:
            with get_session() as session:
                session.add(feedback)
                session.flush()
                logger.info(f"Created feedback {feedback.feedback_id}")
                return feedback
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            raise

    @staticmethod
    def get_average_rating(grid_id: str) -> Optional[float]:
        """Get average rating for a grid."""
        try:
            with get_session() as session:
                from sqlalchemy import func
                avg_rating = (
                    session.query(func.avg(UserFeedbackModel.rating))
                    .filter_by(grid_id=grid_id)
                    .scalar()
                )
                return avg_rating
        except Exception as e:
            logger.error(f"Error calculating average rating for grid {grid_id}: {e}")
            raise
