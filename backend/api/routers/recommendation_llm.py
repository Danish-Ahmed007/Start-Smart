"""
LLM Recommendations Router

Advanced recommendation endpoint using the full pipeline:
BEV → Rule Engine → LLM Evaluator → Score Combiner

Endpoints:
    GET /api/v1/recommendation_llm - Full LLM-powered recommendation
    GET /api/v1/recommendation_fast - Fast rule-based only
    GET /api/v1/recommendation_enhanced - Enhanced with income data and area analysis
"""

import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.services.recommendation_pipeline import (
    RecommendationPipeline,
    PipelineMode,
    PipelineResult
)
from src.services.bev_generator import BusinessEnvironmentVector
from src.services.income_service import get_income_service, IncomeDataService

logger = logging.getLogger("startsmart.api.recommendation_llm")

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class LocationInput(BaseModel):
    """Input location for recommendation."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    grid_id: Optional[str] = Field(None, description="Grid cell identifier")
    radius_meters: Optional[int] = Field(500, ge=100, le=2000, description="Search radius")


class CategoryRecommendation(BaseModel):
    """Recommendation for a single category."""
    score: float = Field(..., ge=0, le=1, description="Final score (0-1)")
    suitability: str = Field(..., description="Suitability level")
    reasoning: str = Field(..., description="LLM reasoning")
    positive_factors: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)


class RecommendationOutput(BaseModel):
    """Best recommendation output."""
    best_category: str = Field(..., description="Recommended category")
    score: float = Field(..., ge=0, le=1)
    suitability: str
    message: str = Field(..., description="Human-readable recommendation")


class AnalysisMeta(BaseModel):
    """Analysis metadata."""
    model_used: str = Field(..., description="LLM model used")
    total_businesses_nearby: int = Field(0, description="Total businesses analyzed")
    key_factors: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(0, description="Total processing time")


class LLMRecommendationResponse(BaseModel):
    """Full response from LLM recommendation endpoint."""
    grid_id: str
    recommendation: RecommendationOutput
    gym: CategoryRecommendation
    cafe: CategoryRecommendation
    analysis: AnalysisMeta

    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "Clifton-Block2-007-008",
                "recommendation": {
                    "best_category": "gym",
                    "score": 0.78,
                    "suitability": "good",
                    "message": "This location is GOOD for a GYM. Recommended with minor considerations."
                },
                "gym": {
                    "score": 0.78,
                    "suitability": "good",
                    "reasoning": "Strong office presence and limited gym competition make this ideal.",
                    "positive_factors": ["Nearby offices boost", "Good foot traffic"],
                    "concerns": ["Some competition in area"]
                },
                "cafe": {
                    "score": 0.62,
                    "suitability": "moderate",
                    "reasoning": "Moderate potential due to existing cafe density.",
                    "positive_factors": ["Restaurant area synergy"],
                    "concerns": ["Cafe saturation"]
                },
                "analysis": {
                    "model_used": "llama-3.3-70b-versatile",
                    "total_businesses_nearby": 45,
                    "key_factors": ["office workers", "limited competition"],
                    "processing_time_ms": 2340.5
                }
            }
        }


class BEVResponse(BaseModel):
    """BEV summary for debugging/transparency."""
    restaurant_count: int
    cafe_count: int
    gym_count: int
    office_count: int
    school_count: int
    avg_rating: float
    avg_reviews: float
    income_proxy: str
    mall_within_1km: bool
    university_within_2km: bool


class FullPipelineResponse(BaseModel):
    """Detailed response including BEV and all scores."""
    grid_id: str
    location: Dict[str, float]
    bev: BEVResponse
    rule_scores: Dict[str, float]
    llm_scores: Dict[str, float]
    final_scores: Dict[str, float]
    recommendation: RecommendationOutput
    timing: Dict[str, float]
    mode: str


# ============================================================================
# Enhanced Response Models (with income data and area analysis)
# ============================================================================

class CategoryCountModel(BaseModel):
    """Business category with count."""
    category: str
    count: int
    percentage: float
    business_names: List[str] = Field(default_factory=list)


class BackingFactorModel(BaseModel):
    """A data-backed insight from area analysis."""
    factor: str
    evidence: str
    implication: str
    strength: str  # strong, moderate, weak


class AreaAnalysisModel(BaseModel):
    """Comprehensive area analysis."""
    total_businesses: int
    top_5_categories: List[CategoryCountModel]
    area_character: str = ""
    backing_factors: List[BackingFactorModel] = Field(default_factory=list)
    

class IncomeDataModel(BaseModel):
    """Income data for the area."""
    avg_household_income: int
    median_income: int
    income_bracket: str
    spending_power: str
    affordability_score: float
    key_demographics: List[str]
    consumer_behavior: Dict[str, Any]


class SupportingFactorModel(BaseModel):
    """A supporting factor with count."""
    factor: str
    count: int
    impact: str  # positive, negative, neutral
    reason: str


class EnhancedRecommendationOutput(BaseModel):
    """Best recommendation with key numbers."""
    best_category: str
    confidence_score: float
    suitability: str
    summary: str
    key_numbers: Dict[str, Any]


class EnhancedRecommendationResponse(BaseModel):
    """Full enhanced response with income data and area analysis."""
    grid_id: str
    location: Dict[str, float]
    
    # Area analysis with top 5 business categories
    area_analysis: AreaAnalysisModel
    
    # Income data for the area
    income_data: IncomeDataModel
    
    # Standard recommendation
    recommendation: EnhancedRecommendationOutput
    
    # Supporting factors for/against each category
    supporting_factors: Dict[str, List[SupportingFactorModel]]
    
    # Detailed scores
    gym: CategoryRecommendation
    cafe: CategoryRecommendation
    
    # Metadata
    analysis: AnalysisMeta
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "Clifton-Block2-custom",
                "location": {"lat": 24.815, "lon": 67.028, "radius": 200},
                "area_analysis": {
                    "total_businesses": 47,
                    "top_5_categories": [
                        {"category": "restaurants", "count": 12, "percentage": 25.5},
                        {"category": "clothing_fashion", "count": 8, "percentage": 17.0},
                        {"category": "cafes", "count": 6, "percentage": 12.8}
                    ]
                },
                "income_data": {
                    "avg_household_income": 450000,
                    "median_income": 380000,
                    "income_bracket": "upper-middle",
                    "spending_power": "high",
                    "affordability_score": 0.85,
                    "key_demographics": ["Professionals", "Business Owners"],
                    "consumer_behavior": {"avg_coffee_spending": 800}
                },
                "recommendation": {
                    "best_category": "cafe",
                    "confidence_score": 0.78,
                    "suitability": "good",
                    "summary": "Based on 12 restaurants and 3 offices nearby...",
                    "key_numbers": {"restaurants_nearby": 12, "competing_cafes": 6}
                }
            }
        }


# ============================================================================
# Dependencies
# ============================================================================

_pipeline_instance: Optional[RecommendationPipeline] = None

def get_pipeline() -> RecommendationPipeline:
    """Get or create the recommendation pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RecommendationPipeline()
    return _pipeline_instance


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/recommendation_llm",
    response_model=LLMRecommendationResponse,
    summary="Get LLM-powered recommendation",
    description="""
    Get a full recommendation using the BEV → Rule Engine → LLM pipeline.
    
    This endpoint:
    1. Generates a Business Environment Vector (BEV) from Google Places
    2. Applies deterministic rule-based scoring
    3. Evaluates with Groq LLM for contextual reasoning
    4. Combines scores with weighted ensemble
    
    **Parameters:**
    - `lat`: Latitude of the location
    - `lon`: Longitude of the location
    - `grid_id`: Optional grid cell identifier
    - `radius`: Search radius in meters (default: 500)
    
    **Returns:**
    - Best category recommendation (gym or cafe)
    - Scores and reasoning for both categories
    - Key factors and concerns
    """
)
async def get_llm_recommendation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    grid_id: Optional[str] = Query(None, description="Grid cell identifier"),
    radius: int = Query(500, ge=100, le=2000, description="Search radius in meters"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> LLMRecommendationResponse:
    """Get LLM-powered recommendation for a location."""
    try:
        logger.info(f"LLM recommendation request: lat={lat}, lon={lon}")
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=PipelineMode.FULL
        )
        
        api_response = result.to_api_response()
        
        # Build response
        return LLMRecommendationResponse(
            grid_id=api_response["grid_id"],
            recommendation=RecommendationOutput(**api_response["recommendation"]),
            gym=CategoryRecommendation(**api_response["gym"]),
            cafe=CategoryRecommendation(**api_response["cafe"]),
            analysis=AnalysisMeta(
                **api_response["analysis"],
                processing_time_ms=result.total_time_ms
            )
        )
        
    except Exception as e:
        logger.error(f"LLM recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendation_fast",
    response_model=LLMRecommendationResponse,
    summary="Get fast rule-based recommendation",
    description="""
    Get a fast recommendation using only BEV and Rule Engine (no LLM).
    
    Much faster than /recommendation_llm but without LLM reasoning.
    Good for bulk processing or when LLM quota is limited.
    """
)
async def get_fast_recommendation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    grid_id: Optional[str] = Query(None, description="Grid cell identifier"),
    radius: int = Query(500, ge=100, le=2000, description="Search radius in meters"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> LLMRecommendationResponse:
    """Get fast rule-based recommendation for a location."""
    try:
        logger.info(f"Fast recommendation request: lat={lat}, lon={lon}")
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=PipelineMode.FAST
        )
        
        api_response = result.to_api_response()
        
        return LLMRecommendationResponse(
            grid_id=api_response["grid_id"],
            recommendation=RecommendationOutput(**api_response["recommendation"]),
            gym=CategoryRecommendation(**api_response["gym"]),
            cafe=CategoryRecommendation(**api_response["cafe"]),
            analysis=AnalysisMeta(
                **api_response["analysis"],
                processing_time_ms=result.total_time_ms
            )
        )
        
    except Exception as e:
        logger.error(f"Fast recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendation_debug",
    response_model=FullPipelineResponse,
    summary="Get detailed pipeline output",
    description="Full debugging output including BEV, all scores, and timing."
)
async def get_debug_recommendation(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    grid_id: Optional[str] = Query(None),
    radius: int = Query(500, ge=100, le=2000),
    mode: str = Query("full", regex="^(full|fast)$"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> FullPipelineResponse:
    """Get detailed pipeline output for debugging."""
    try:
        pipeline_mode = PipelineMode.FULL if mode == "full" else PipelineMode.FAST
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=pipeline_mode
        )
        
        bev = result.bev
        
        return FullPipelineResponse(
            grid_id=result.grid_id,
            location={"lat": result.lat, "lon": result.lon, "radius": result.radius_meters},
            bev=BEVResponse(
                restaurant_count=bev.density.restaurants,
                cafe_count=bev.density.cafes,
                gym_count=bev.density.gyms,
                office_count=bev.density.offices,
                school_count=bev.density.schools,
                avg_rating=round(bev.economic.avg_business_rating, 2),
                avg_reviews=round(bev.economic.avg_review_count, 1),
                income_proxy=bev.economic.income_proxy,
                mall_within_1km=bev.distance.distance_to_mall > 0 and bev.distance.distance_to_mall <= 1000,
                university_within_2km=bev.distance.distance_to_university > 0 and bev.distance.distance_to_university <= 2000
            ),
            rule_scores={
                "gym": round(result.rule_result.gym_score, 4),
                "cafe": round(result.rule_result.cafe_score, 4)
            },
            llm_scores={
                "gym": round(result.llm_result.gym_probability, 4) if result.llm_result else 0,
                "cafe": round(result.llm_result.cafe_probability, 4) if result.llm_result else 0
            },
            final_scores={
                "gym": round(result.combined.gym.final_score, 4),
                "cafe": round(result.combined.cafe.final_score, 4)
            },
            recommendation=RecommendationOutput(
                best_category=result.combined.best_category,
                score=round(result.combined.best_score, 2),
                suitability=result.combined.best_suitability,
                message=result.combined._generate_message()
            ),
            timing={
                "bev_ms": round(result.bev_time_ms, 1),
                "rule_ms": round(result.rule_time_ms, 1),
                "llm_ms": round(result.llm_time_ms, 1),
                "combine_ms": round(result.combine_time_ms, 1),
                "total_ms": round(result.total_time_ms, 1)
            },
            mode=result.mode
        )
        
    except Exception as e:
        logger.error(f"Debug recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recommendation_batch",
    summary="Batch recommendations",
    description="Get recommendations for multiple locations at once."
)
async def get_batch_recommendations(
    locations: List[LocationInput],
    mode: str = Query("fast", regex="^(full|fast)$"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> List[Dict[str, Any]]:
    """Get recommendations for multiple locations."""
    try:
        logger.info(f"Batch recommendation request: {len(locations)} locations")
        
        pipeline_mode = PipelineMode.FULL if mode == "full" else PipelineMode.FAST
        
        results = []
        for loc in locations:
            result = pipeline.recommend(
                lat=loc.lat,
                lon=loc.lon,
                grid_id=loc.grid_id,
                radius_meters=loc.radius_meters or 500,
                mode=pipeline_mode
            )
            results.append(result.to_api_response())
        
        return results
        
    except Exception as e:
        logger.error(f"Batch recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendation_enhanced",
    response_model=EnhancedRecommendationResponse,
    summary="Get enhanced recommendation with income data and area analysis",
    description="""
    Get a comprehensive recommendation with:
    - Top 5 business categories in the area with counts
    - Income and demographic data for the location
    - Supporting factors backed by specific numbers
    - Detailed recommendation summary
    
    This endpoint provides the most data-backed analysis.
    """
)
async def get_enhanced_recommendation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    grid_id: Optional[str] = Query(None, description="Grid cell identifier"),
    radius: int = Query(200, ge=100, le=500, description="Search radius in meters (100-500)"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> EnhancedRecommendationResponse:
    """Get enhanced recommendation with income data and area analysis."""
    try:
        logger.info(f"Enhanced recommendation request: lat={lat}, lon={lon}, radius={radius}")
        
        # Get recommendation from pipeline
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=PipelineMode.FULL
        )
        
        # Get income data
        income_service = get_income_service()
        income = income_service.get_income_data(lat, lon)
        sector = income_service.get_sector_for_location(lat, lon)
        
        # Extract area analysis from BEV
        bev = result.bev
        area_analysis = bev.area_analysis
        
        # Build top 5 categories with business names
        top_5_cats = [
            CategoryCountModel(
                category=cat.category,
                count=cat.count,
                percentage=cat.percentage,
                business_names=cat.business_names[:5]  # Include sample names
            )
            for cat in area_analysis.top_5_categories
        ]
        
        # Build backing factors from BEV area analysis
        backing_factors_list = [
            BackingFactorModel(
                factor=bf.factor,
                evidence=bf.evidence,
                implication=bf.implication,
                strength=bf.strength
            )
            for bf in area_analysis.backing_factors
        ]
        
        # Build supporting factors based on actual data
        gym_factors = _build_gym_factors(bev)
        cafe_factors = _build_cafe_factors(bev)
        
        # Build key numbers for summary
        key_numbers = {
            "restaurants_nearby": bev.density.restaurants,
            "cafes_nearby": bev.density.cafes,
            "gyms_nearby": bev.density.gyms,
            "offices_nearby": bev.density.offices,
            "schools_nearby": bev.density.schools,
            "total_businesses": area_analysis.total_businesses,
            "avg_household_income": income.avg_household_income_pkr
        }
        
        # Generate data-backed summary
        summary = _generate_data_backed_summary(
            result.combined.best_category,
            result.combined.best_score,
            bev,
            income,
            sector
        )
        
        return EnhancedRecommendationResponse(
            grid_id=result.grid_id,
            location={"lat": lat, "lon": lon, "radius": radius},
            area_analysis=AreaAnalysisModel(
                total_businesses=area_analysis.total_businesses,
                top_5_categories=top_5_cats,
                area_character=area_analysis.area_character,
                backing_factors=backing_factors_list
            ),
            income_data=IncomeDataModel(
                avg_household_income=income.avg_household_income_pkr,
                median_income=income.median_income_pkr,
                income_bracket=income.income_bracket,
                spending_power=income.spending_power,
                affordability_score=income.affordability_score,
                key_demographics=income.key_demographics,
                consumer_behavior={
                    "avg_meal_spending": income.avg_meal_spending,
                    "avg_coffee_spending": income.avg_coffee_spending,
                    "gym_budget_monthly": income.gym_budget_monthly,
                    "price_sensitivity": income.price_sensitivity
                }
            ),
            recommendation=EnhancedRecommendationOutput(
                best_category=result.combined.best_category,
                confidence_score=round(result.combined.best_score, 2),
                suitability=result.combined.best_suitability,
                summary=summary,
                key_numbers=key_numbers
            ),
            supporting_factors={
                "for_gym": gym_factors["positive"],
                "against_gym": gym_factors["negative"],
                "for_cafe": cafe_factors["positive"],
                "against_cafe": cafe_factors["negative"]
            },
            gym=CategoryRecommendation(
                score=round(result.combined.gym.final_score, 2),
                suitability=result.combined.gym.suitability,
                reasoning=result.llm_result.reasoning if result.llm_result else "Rule-based analysis",
                positive_factors=[f.factor for f in gym_factors["positive"]],
                concerns=[f.factor for f in gym_factors["negative"]]
            ),
            cafe=CategoryRecommendation(
                score=round(result.combined.cafe.final_score, 2),
                suitability=result.combined.cafe.suitability,
                reasoning=result.llm_result.reasoning if result.llm_result else "Rule-based analysis",
                positive_factors=[f.factor for f in cafe_factors["positive"]],
                concerns=[f.factor for f in cafe_factors["negative"]]
            ),
            analysis=AnalysisMeta(
                model_used=result.llm_result.model if result.llm_result else "rule-based",
                total_businesses_nearby=area_analysis.total_businesses,
                key_factors=result.llm_result.key_factors if result.llm_result else [],
                processing_time_ms=result.total_time_ms
            )
        )
        
    except Exception as e:
        logger.error(f"Enhanced recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_gym_factors(bev: BusinessEnvironmentVector) -> Dict[str, List[SupportingFactorModel]]:
    """Build supporting factors for gym recommendation."""
    positive = []
    negative = []
    
    # Office workers are potential gym customers
    if bev.density.offices > 0:
        positive.append(SupportingFactorModel(
            factor=f"{bev.density.offices} offices nearby",
            count=bev.density.offices,
            impact="positive",
            reason="Office workers often seek fitness facilities for after-work exercise"
        ))
    
    # Residential presence
    if bev.density.residential > 0:
        positive.append(SupportingFactorModel(
            factor=f"{bev.density.residential} residential areas",
            count=bev.density.residential,
            impact="positive",
            reason="Residents need convenient gym access in their neighborhood"
        ))
    
    # University/school nearby (young fitness-conscious demographic)
    if bev.density.universities > 0 or bev.density.schools > 0:
        count = bev.density.universities + bev.density.schools
        positive.append(SupportingFactorModel(
            factor=f"{count} educational institutions nearby",
            count=count,
            impact="positive",
            reason="Students and faculty are a key gym demographic"
        ))
    
    # High income area
    if bev.economic.income_proxy == "high":
        positive.append(SupportingFactorModel(
            factor="High income area",
            count=1,
            impact="positive",
            reason="Higher disposable income for gym memberships"
        ))
    
    # Competition (existing gyms)
    if bev.density.gyms > 2:
        negative.append(SupportingFactorModel(
            factor=f"{bev.density.gyms} existing gyms",
            count=bev.density.gyms,
            impact="negative",
            reason="High competition may split the customer base"
        ))
    elif bev.density.gyms > 0:
        negative.append(SupportingFactorModel(
            factor=f"{bev.density.gyms} existing gym(s)",
            count=bev.density.gyms,
            impact="negative",
            reason="Some competition exists but market may have room"
        ))
    
    return {"positive": positive, "negative": negative}


def _build_cafe_factors(bev: BusinessEnvironmentVector) -> Dict[str, List[SupportingFactorModel]]:
    """Build supporting factors for cafe recommendation."""
    positive = []
    negative = []
    
    # Restaurant density indicates food-friendly area
    if bev.density.restaurants > 3:
        positive.append(SupportingFactorModel(
            factor=f"{bev.density.restaurants} restaurants nearby",
            count=bev.density.restaurants,
            impact="positive",
            reason="High restaurant density indicates strong food/beverage foot traffic"
        ))
    
    # Office workers need coffee
    if bev.density.offices > 0:
        positive.append(SupportingFactorModel(
            factor=f"{bev.density.offices} offices nearby",
            count=bev.density.offices,
            impact="positive",
            reason="Office workers are regular coffee consumers"
        ))
    
    # Schools/universities - students need coffee
    if bev.density.universities > 0:
        positive.append(SupportingFactorModel(
            factor=f"{bev.density.universities} university nearby",
            count=bev.density.universities,
            impact="positive",
            reason="Students are frequent cafe visitors for studying"
        ))
    
    # Malls and stores indicate commercial activity
    if bev.density.malls > 0 or bev.density.stores > 3:
        count = bev.density.malls + bev.density.stores
        positive.append(SupportingFactorModel(
            factor=f"{count} retail locations nearby",
            count=count,
            impact="positive",
            reason="Shoppers often take coffee breaks"
        ))
    
    # Existing cafe competition
    if bev.density.cafes > 3:
        negative.append(SupportingFactorModel(
            factor=f"{bev.density.cafes} existing cafes",
            count=bev.density.cafes,
            impact="negative",
            reason="Market may be saturated with coffee options"
        ))
    elif bev.density.cafes > 0:
        negative.append(SupportingFactorModel(
            factor=f"{bev.density.cafes} existing cafe(s)",
            count=bev.density.cafes,
            impact="negative",
            reason="Some competition but differentiation possible"
        ))
    
    return {"positive": positive, "negative": negative}


def _generate_data_backed_summary(
    best_category: str,
    score: float,
    bev: BusinessEnvironmentVector,
    income,
    sector: str
) -> str:
    """Generate a data-backed summary with specific numbers."""
    
    suitability = "excellent" if score >= 0.8 else "good" if score >= 0.65 else "moderate" if score >= 0.5 else "poor"
    
    if best_category == "gym":
        summary = f"Based on analysis of {bev.area_analysis.total_businesses} businesses within the area, "
        summary += f"a GYM shows {suitability} potential. "
        
        if bev.density.offices > 0:
            summary += f"The presence of {bev.density.offices} office(s) provides a strong customer base of working professionals. "
        
        if bev.density.gyms == 0:
            summary += "With no existing gyms, you would face minimal competition. "
        elif bev.density.gyms <= 2:
            summary += f"With only {bev.density.gyms} existing gym(s), competition is manageable. "
        
        summary += f"The {income.income_bracket} income bracket (avg PKR {income.avg_household_income_pkr:,}/month) "
        summary += f"supports gym membership budgets of around PKR {income.gym_budget_monthly:,}/month."
        
    else:  # cafe
        summary = f"Based on analysis of {bev.area_analysis.total_businesses} businesses within the area, "
        summary += f"a CAFE shows {suitability} potential. "
        
        if bev.density.restaurants > 0:
            summary += f"The area has {bev.density.restaurants} restaurant(s), indicating established food traffic. "
        
        if bev.density.offices > 0:
            summary += f"With {bev.density.offices} office(s) nearby, there's consistent demand for coffee. "
        
        if bev.density.cafes == 0:
            summary += "With no existing cafes, you would be the first in this micro-area. "
        elif bev.density.cafes <= 3:
            summary += f"With {bev.density.cafes} existing cafe(s), there's room for differentiation. "
        
        summary += f"Average coffee spending in this {income.income_bracket} area is PKR {income.avg_coffee_spending}."
    
    return summary

