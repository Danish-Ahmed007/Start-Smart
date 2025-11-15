from __future__ import annotations

from enum import Enum
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, root_validator, validator


class Category(str, Enum):
    Gym = "Gym"
    Cafe = "Cafe"


class Source(str, Enum):
    google_places = "google_places"
    instagram = "instagram"
    reddit = "reddit"
    simulated = "simulated"


class PostType(str, Enum):
    demand = "demand"
    complaint = "complaint"
    mention = "mention"


class GridCell(BaseModel):
    grid_id: str
    neighborhood: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    area_km2: Optional[float] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    created_at: Optional[datetime] = None

    @root_validator
    def check_bounds(cls, values):
        min_lat = values.get("min_lat")
        max_lat = values.get("max_lat")
        min_lon = values.get("min_lon")
        max_lon = values.get("max_lon")
        if min_lat is None or max_lat is None or min_lon is None or max_lon is None:
            return values
        if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
            raise ValueError("Longitude must be between -180 and 180")
        if not (min_lat < max_lat and min_lon < max_lon):
            raise ValueError("min_lat < max_lat and min_lon < max_lon must hold")
        return values


class Business(BaseModel):
    business_id: str
    name: str
    lat: float
    lon: float
    category: Optional[Category] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    review_count: Optional[int] = Field(0, ge=0)
    source: Optional[Source] = None
    grid_id: Optional[str] = None
    fetched_at: Optional[datetime] = None

    @validator("lat")
    def lat_range(cls, v):
        if v is None:
            return v
        if not -90.0 <= v <= 90.0:
            raise ValueError("lat must be between -90 and 90")
        return v

    @validator("lon")
    def lon_range(cls, v):
        if v is None:
            return v
        if not -180.0 <= v <= 180.0:
            raise ValueError("lon must be between -180 and 180")
        return v


class SocialPost(BaseModel):
    post_id: str
    source: Source
    text: Optional[str] = None
    timestamp: datetime
    lat: Optional[float] = None
    lon: Optional[float] = None
    grid_id: Optional[str] = None
    post_type: Optional[PostType] = None
    engagement_score: Optional[float] = None
    is_simulated: bool = False
    created_at: Optional[datetime] = None

    @validator("lat")
    def lat_range(cls, v):
        if v is None:
            return v
        if not -90.0 <= v <= 90.0:
            raise ValueError("lat must be between -90 and 90")
        return v

    @validator("lon")
    def lon_range(cls, v):
        if v is None:
            return v
        if not -180.0 <= v <= 180.0:
            raise ValueError("lon must be between -180 and 180")
        return v


class CompetitorDetail(BaseModel):
    business_id: str
    name: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)


class GridMetrics(BaseModel):
    id: Optional[int] = None
    grid_id: str
    category: Optional[Category] = None
    business_count: int = Field(0, ge=0)
    instagram_volume: int = Field(0, ge=0)
    reddit_mentions: int = Field(0, ge=0)
    gos: Optional[float] = None
    confidence: Optional[float] = None
    top_posts_json: Optional[List[SocialPost]] = None
    competitors_json: Optional[List[CompetitorDetail]] = None
    last_updated: Optional[datetime] = None


class TopPostDetail(BaseModel):
    post_id: str
    source: Source
    text: Optional[str]
    timestamp: datetime
    engagement_score: Optional[float]
    post_type: Optional[PostType]
    is_simulated: bool = False


class RecommendationItem(BaseModel):
    category: str
    score: float
    business: Business


class RecommendationResponse(BaseModel):
    grid_id: Optional[str] = None
    recommendations: List[RecommendationItem]


class GridSummaryResponse(BaseModel):
    grids: List[GridCell]


class GridDetailResponse(BaseModel):
    grid: GridCell
    businesses: List[Business]
    metrics: List[GridMetrics]
    top_posts: Optional[List[TopPostDetail]] = None


class NeighborhoodResponse(BaseModel):
    id: str
    name: str
    grid_count: int
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None


__all__ = [
    "Category",
    "Source",
    "PostType",
    "GridCell",
    "Business",
    "SocialPost",
    "GridMetrics",
    "TopPostDetail",
    "CompetitorDetail",
    "RecommendationResponse",
    "GridSummaryResponse",
    "GridDetailResponse",
    "NeighborhoodResponse",
]
