"""SQLAlchemy ORM models for StartSmart Phase 0 database.

Defines declarative ORM models matching the database schema in contracts/database_schema.sql.
All column names, types, and constraints match EXACTLY.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .connection import Base


class GridCellModel(Base):
    """ORM model for grid_cells table.
    
    Represents geographic grid cells for the DHA Phase 2 neighborhood.
    Each cell is a bounded box with location metadata.
    """

    __tablename__ = "grid_cells"

    # Primary Key
    grid_id = Column(String, primary_key=True, nullable=False)

    # Location metadata
    neighborhood = Column(String, nullable=False)
    min_lat = Column(
        Numeric(precision=10, scale=8),
        nullable=False,
        comment="Minimum latitude (bounds check: -90 to 90)",
    )
    max_lat = Column(
        Numeric(precision=10, scale=8),
        nullable=False,
        comment="Maximum latitude (bounds check: -90 to 90)",
    )
    min_lon = Column(
        Numeric(precision=11, scale=8),
        nullable=False,
        comment="Minimum longitude (bounds check: -180 to 180)",
    )
    max_lon = Column(
        Numeric(precision=11, scale=8),
        nullable=False,
        comment="Maximum longitude (bounds check: -180 to 180)",
    )

    # Computed fields
    area_km2 = Column(Numeric(precision=10, scale=4), nullable=True)
    centroid_lat = Column(
        Numeric(precision=10, scale=8), nullable=True, comment="Computed center latitude"
    )
    centroid_lon = Column(
        Numeric(precision=11, scale=8), nullable=True, comment="Computed center longitude"
    )

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Constraints (matching SQL schema)
    __table_args__ = (
        CheckConstraint("min_lat >= -90 AND min_lat <= 90", name="check_min_lat_range"),
        CheckConstraint("max_lat >= -90 AND max_lat <= 90", name="check_max_lat_range"),
        CheckConstraint("min_lon >= -180 AND min_lon <= 180", name="check_min_lon_range"),
        CheckConstraint("max_lon >= -180 AND max_lon <= 180", name="check_max_lon_range"),
        CheckConstraint("min_lat < max_lat", name="check_min_max_lat"),
        CheckConstraint("min_lon < max_lon", name="check_min_max_lon"),
    )

    # Relationships
    businesses = relationship(
        "BusinessModel",
        back_populates="grid",
        cascade="all, delete-orphan",
        foreign_keys="BusinessModel.grid_id",
    )
    social_posts = relationship(
        "SocialPostModel",
        back_populates="grid",
        cascade="all, delete-orphan",
        foreign_keys="SocialPostModel.grid_id",
    )
    grid_metrics = relationship(
        "GridMetricsModel",
        back_populates="grid",
        cascade="all, delete-orphan",
        foreign_keys="GridMetricsModel.grid_id",
    )
    user_feedback = relationship(
        "UserFeedbackModel",
        back_populates="grid",
        cascade="all, delete-orphan",
        foreign_keys="UserFeedbackModel.grid_id",
    )

    def __repr__(self) -> str:
        return (
            f"<GridCellModel(grid_id={self.grid_id!r}, "
            f"neighborhood={self.neighborhood!r}, "
            f"area_km2={self.area_km2})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary for JSON serialization."""
        return {
            "grid_id": self.grid_id,
            "neighborhood": self.neighborhood,
            "min_lat": float(self.min_lat) if self.min_lat else None,
            "max_lat": float(self.max_lat) if self.max_lat else None,
            "min_lon": float(self.min_lon) if self.min_lon else None,
            "max_lon": float(self.max_lon) if self.max_lon else None,
            "area_km2": float(self.area_km2) if self.area_km2 else None,
            "centroid_lat": float(self.centroid_lat) if self.centroid_lat else None,
            "centroid_lon": float(self.centroid_lon) if self.centroid_lon else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model: Any) -> GridCellModel:
        """Create ORM instance from Pydantic model (contracts.models.GridCell)."""
        return cls(
            grid_id=pydantic_model.grid_id,
            neighborhood=pydantic_model.neighborhood,
            min_lat=pydantic_model.min_lat,
            max_lat=pydantic_model.max_lat,
            min_lon=pydantic_model.min_lon,
            max_lon=pydantic_model.max_lon,
            area_km2=pydantic_model.area_km2,
            centroid_lat=pydantic_model.centroid_lat,
            centroid_lon=pydantic_model.centroid_lon,
            created_at=pydantic_model.created_at or datetime.utcnow(),
        )


class BusinessModel(Base):
    """ORM model for businesses table.
    
    Represents businesses (gym, cafe, etc.) with location and rating data.
    Each business is mapped to a grid cell.
    """

    __tablename__ = "businesses"

    # Primary Key
    business_id = Column(String, primary_key=True, nullable=False)

    # Business metadata
    name = Column(String, nullable=False)
    lat = Column(
        Numeric(precision=10, scale=8),
        nullable=True,
        comment="Business latitude (bounds check: -90 to 90)",
    )
    lon = Column(
        Numeric(precision=11, scale=8),
        nullable=True,
        comment="Business longitude (bounds check: -180 to 180)",
    )
    category = Column(String, nullable=True)
    rating = Column(
        Numeric(precision=3, scale=2),
        nullable=True,
        comment="Rating 0-5 (bounds check)",
    )
    review_count = Column(Integer, nullable=False, default=0)
    source = Column(String, nullable=True)

    # Foreign Key
    grid_id = Column(
        String,
        ForeignKey("grid_cells.grid_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamp
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Constraints (matching SQL schema)
    __table_args__ = (
        CheckConstraint("lat >= -90 AND lat <= 90", name="check_business_lat_range"),
        CheckConstraint("lon >= -180 AND lon <= 180", name="check_business_lon_range"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="check_rating_range"),
        CheckConstraint("review_count >= 0", name="check_review_count_non_negative"),
    )

    # Relationships
    grid = relationship(
        "GridCellModel",
        back_populates="businesses",
        foreign_keys=[grid_id],
    )

    def __repr__(self) -> str:
        return (
            f"<BusinessModel(business_id={self.business_id!r}, "
            f"name={self.name!r}, "
            f"category={self.category!r}, "
            f"rating={self.rating})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary for JSON serialization."""
        return {
            "business_id": self.business_id,
            "name": self.name,
            "lat": float(self.lat) if self.lat else None,
            "lon": float(self.lon) if self.lon else None,
            "category": self.category,
            "rating": float(self.rating) if self.rating else None,
            "review_count": self.review_count,
            "source": self.source,
            "grid_id": self.grid_id,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model: Any) -> BusinessModel:
        """Create ORM instance from Pydantic model (contracts.models.Business)."""
        return cls(
            business_id=pydantic_model.business_id,
            name=pydantic_model.name,
            lat=pydantic_model.lat,
            lon=pydantic_model.lon,
            category=pydantic_model.category.value if pydantic_model.category else None,
            rating=pydantic_model.rating,
            review_count=pydantic_model.review_count or 0,
            source=pydantic_model.source.value if pydantic_model.source else None,
            grid_id=pydantic_model.grid_id,
            fetched_at=pydantic_model.fetched_at or datetime.utcnow(),
        )


class SocialPostModel(Base):
    """ORM model for social_posts table.
    
    Represents social media posts (Instagram, Reddit, Twitter) with engagement metrics.
    Supports both real posts and simulated posts for testing.
    """

    __tablename__ = "social_posts"

    # Primary Key
    post_id = Column(String, primary_key=True, nullable=False)

    # Post metadata
    source = Column(String, nullable=False, comment="Source: instagram, reddit, twitter, etc.")
    text = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="Post timestamp")
    lat = Column(
        Numeric(precision=10, scale=8),
        nullable=True,
        comment="Post latitude (bounds check: -90 to 90)",
    )
    lon = Column(
        Numeric(precision=11, scale=8),
        nullable=True,
        comment="Post longitude (bounds check: -180 to 180)",
    )

    # Foreign Key
    grid_id = Column(
        String,
        ForeignKey("grid_cells.grid_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Analysis fields
    post_type = Column(String, nullable=True, comment="demand, complaint, mention, etc.")
    engagement_score = Column(Numeric(precision=10, scale=2), nullable=True)
    is_simulated = Column(Boolean, nullable=False, default=False)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp (when post entered system)",
    )

    # Constraints (matching SQL schema)
    __table_args__ = (
        CheckConstraint("lat >= -90 AND lat <= 90", name="check_social_posts_lat_range"),
        CheckConstraint("lon >= -180 AND lon <= 180", name="check_social_posts_lon_range"),
    )

    # Relationships
    grid = relationship(
        "GridCellModel",
        back_populates="social_posts",
        foreign_keys=[grid_id],
    )

    def __repr__(self) -> str:
        return (
            f"<SocialPostModel(post_id={self.post_id!r}, "
            f"source={self.source!r}, "
            f"post_type={self.post_type!r}, "
            f"engagement_score={self.engagement_score})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary for JSON serialization."""
        return {
            "post_id": self.post_id,
            "source": self.source,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "lat": float(self.lat) if self.lat else None,
            "lon": float(self.lon) if self.lon else None,
            "grid_id": self.grid_id,
            "post_type": self.post_type,
            "engagement_score": float(self.engagement_score) if self.engagement_score else None,
            "is_simulated": self.is_simulated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model: Any) -> SocialPostModel:
        """Create ORM instance from Pydantic model (contracts.models.SocialPost)."""
        return cls(
            post_id=pydantic_model.post_id,
            source=pydantic_model.source.value,
            text=pydantic_model.text,
            timestamp=pydantic_model.timestamp,
            lat=pydantic_model.lat,
            lon=pydantic_model.lon,
            grid_id=pydantic_model.grid_id,
            post_type=pydantic_model.post_type.value if pydantic_model.post_type else None,
            engagement_score=pydantic_model.engagement_score,
            is_simulated=pydantic_model.is_simulated,
            created_at=pydantic_model.created_at or datetime.utcnow(),
        )


class GridMetricsModel(Base):
    """ORM model for grid_metrics table.
    
    Stores aggregated metrics and analysis results for each grid cell and category.
    Includes JSON columns for top posts and competitor details.
    """

    __tablename__ = "grid_metrics"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    grid_id = Column(
        String,
        ForeignKey("grid_cells.grid_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Metrics
    category = Column(String, nullable=True)
    business_count = Column(Integer, nullable=False, default=0)
    instagram_volume = Column(Integer, nullable=False, default=0)
    reddit_mentions = Column(Integer, nullable=False, default=0)

    # Analysis fields
    gos = Column(Numeric(precision=10, scale=4), nullable=True, comment="Growth Opportunity Score")
    confidence = Column(Numeric(precision=5, scale=4), nullable=True, comment="Confidence score 0-1")

    # JSON data columns
    top_posts_json = Column(
        JSON,
        nullable=True,
        comment="Array of top posts (SocialPost objects)",
    )
    competitors_json = Column(
        JSON,
        nullable=True,
        comment="Array of competitor details (CompetitorDetail objects)",
    )

    # Timestamp
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Constraints (matching SQL schema)
    __table_args__ = (
        CheckConstraint("business_count >= 0", name="check_business_count_non_negative"),
        CheckConstraint(
            "instagram_volume >= 0", name="check_instagram_volume_non_negative"
        ),
        CheckConstraint("reddit_mentions >= 0", name="check_reddit_mentions_non_negative"),
        UniqueConstraint("grid_id", "category", name="uq_grid_category"),
    )

    # Relationships
    grid = relationship(
        "GridCellModel",
        back_populates="grid_metrics",
        foreign_keys=[grid_id],
    )

    def __repr__(self) -> str:
        return (
            f"<GridMetricsModel(id={self.id}, "
            f"grid_id={self.grid_id!r}, "
            f"category={self.category!r}, "
            f"gos={self.gos})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "grid_id": self.grid_id,
            "category": self.category,
            "business_count": self.business_count,
            "instagram_volume": self.instagram_volume,
            "reddit_mentions": self.reddit_mentions,
            "gos": float(self.gos) if self.gos else None,
            "confidence": float(self.confidence) if self.confidence else None,
            "top_posts_json": self.top_posts_json,
            "competitors_json": self.competitors_json,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model: Any) -> GridMetricsModel:
        """Create ORM instance from Pydantic model (contracts.models.GridMetrics)."""
        return cls(
            grid_id=pydantic_model.grid_id,
            category=pydantic_model.category.value if pydantic_model.category else None,
            business_count=pydantic_model.business_count,
            instagram_volume=pydantic_model.instagram_volume,
            reddit_mentions=pydantic_model.reddit_mentions,
            gos=pydantic_model.gos,
            confidence=pydantic_model.confidence,
            top_posts_json=pydantic_model.top_posts_json,
            competitors_json=pydantic_model.competitors_json,
            last_updated=pydantic_model.last_updated or datetime.utcnow(),
        )


class UserFeedbackModel(Base):
    """ORM model for user_feedback table.
    
    Stores user feedback ratings and comments for grid cells.
    Rating: -1 (negative), 1 (positive).
    """

    __tablename__ = "user_feedback"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    grid_id = Column(
        String,
        ForeignKey("grid_cells.grid_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Feedback data
    category = Column(String, nullable=True)
    rating = Column(Integer, nullable=False, comment="Rating: -1 (negative) or 1 (positive)")
    comment = Column(Text, nullable=True)
    user_email = Column(String, nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Constraints (matching SQL schema)
    __table_args__ = (CheckConstraint("rating IN (-1, 1)", name="check_rating_values"),)

    # Relationships
    grid = relationship(
        "GridCellModel",
        back_populates="user_feedback",
        foreign_keys=[grid_id],
    )

    def __repr__(self) -> str:
        return (
            f"<UserFeedbackModel(id={self.id}, "
            f"grid_id={self.grid_id!r}, "
            f"rating={self.rating}, "
            f"user_email={self.user_email!r})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "grid_id": self.grid_id,
            "category": self.category,
            "rating": self.rating,
            "comment": self.comment,
            "user_email": self.user_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model: Any) -> UserFeedbackModel:
        """Create ORM instance from Pydantic model.
        
        Note: Contracts don't have a UserFeedback Pydantic model yet.
        This method is provided for consistency and future use.
        """
        return cls(
            grid_id=pydantic_model.grid_id,
            category=getattr(pydantic_model, "category", None),
            rating=pydantic_model.rating,
            comment=getattr(pydantic_model, "comment", None),
            user_email=getattr(pydantic_model, "user_email", None),
            created_at=getattr(pydantic_model, "created_at", None) or datetime.utcnow(),
        )


__all__ = [
    "GridCellModel",
    "BusinessModel",
    "SocialPostModel",
    "GridMetricsModel",
    "UserFeedbackModel",
]
