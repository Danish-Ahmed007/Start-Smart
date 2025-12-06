"""Database layer for Phase 1 backend.

Provides SQLAlchemy 2.0 ORM setup, connection management, and repository pattern for CRUD operations.

Exports:
    - Base: Declarative base for ORM models
    - DatabaseConnection: Connection and session manager
    - get_db: Global database instance getter
    - get_session: Context manager for database sessions
    
    ORM Models:
    - GridCellModel, BusinessModel, SocialPostModel, GridMetricsModel, UserFeedbackModel
    
    Repositories:
    - GridRepository, BusinessRepository, SocialPostRepository, GridMetricsRepository, UserFeedbackRepository
"""

from .connection import Base, DatabaseConnection, get_db, get_session
from .models import (
    GridCellModel,
    BusinessModel,
    SocialPostModel,
    GridMetricsModel,
    UserFeedbackModel,
)
from .repository import (
    GridRepository,
    BusinessRepository,
    SocialPostRepository,
    GridMetricsRepository,
    UserFeedbackRepository,
)

__all__ = [
    # Connection
    "Base",
    "DatabaseConnection",
    "get_db",
    "get_session",
    # Models
    "GridCellModel",
    "BusinessModel",
    "SocialPostModel",
    "GridMetricsModel",
    "UserFeedbackModel",
    # Repositories
    "GridRepository",
    "BusinessRepository",
    "SocialPostRepository",
    "GridMetricsRepository",
    "UserFeedbackRepository",
]
