"""
Business Environment Vector (BEV) Generator

Computes structured, numerical features for each grid/sector based on
Google Places data. The BEV captures the business environment characteristics
that inform location suitability for different business types.

Features:
- Density features (counts of various POI types)
- Distance features (to key amenities)
- Economic proxy features (ratings, review counts, price levels)

Usage:
    from src.services.bev_generator import BEVGenerator
    
    generator = BEVGenerator(api_key="YOUR_API_KEY")
    bev = generator.generate_bev(
        center_lat=24.8150,
        center_lon=67.0280,
        radius_meters=500
    )
"""

import os
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# POI types to count for density features
DENSITY_POI_TYPES = {
    # Food & Beverage
    "restaurants": ["restaurant", "food"],
    "cafes": ["cafe", "coffee_shop"],
    "bakeries": ["bakery"],
    "bars": ["bar", "night_club"],
    "fast_food": ["meal_takeaway", "meal_delivery"],
    
    # Fitness & Health
    "gyms": ["gym", "health"],
    "spas": ["spa", "beauty_salon"],
    "healthcare": ["hospital", "doctor", "dentist", "pharmacy", "physiotherapist"],
    
    # Education
    "schools": ["school", "primary_school", "secondary_school"],
    "universities": ["university"],
    "training_centers": ["training_center"],
    
    # Commerce
    "offices": ["office", "corporate_office"],
    "malls": ["shopping_mall"],
    "stores": ["store", "supermarket", "convenience_store"],
    "banks": ["bank", "atm"],
    "clothing": ["clothing_store", "shoe_store"],
    "electronics": ["electronics_store"],
    
    # Services
    "real_estate": ["real_estate_agency"],
    "car_services": ["car_dealer", "car_repair", "car_wash"],
    "laundry": ["laundry"],
    
    # Entertainment
    "cinemas": ["movie_theater"],
    "parks": ["park", "amusement_park"],
    
    # Transport
    "transit_stations": ["transit_station", "bus_station", "subway_station"],
    "gas_stations": ["gas_station"],
    
    # Residential indicators
    "residential": ["apartment", "residential"],
}

# Comprehensive 20+ business categories for detailed analysis
BUSINESS_CATEGORIES = {
    # Food & Beverage (6 categories)
    "restaurants": ["restaurant", "food"],
    "cafes": ["cafe", "coffee_shop", "coffee"],
    "bakeries": ["bakery"],
    "fast_food": ["meal_takeaway", "meal_delivery", "fast_food"],
    "fine_dining": ["fine_dining"],
    "bars_nightlife": ["bar", "night_club", "pub"],
    
    # Health & Fitness (4 categories)
    "gyms_fitness": ["gym", "fitness", "health_club"],
    "spas_salons": ["spa", "beauty_salon", "hair_care"],
    "clinics_hospitals": ["doctor", "dentist", "clinic", "hospital", "medical"],
    "pharmacies": ["pharmacy", "drugstore"],
    
    # Education (3 categories)
    "schools": ["school", "primary_school", "secondary_school"],
    "universities_colleges": ["university", "college"],
    "tutoring_training": ["tutoring", "coaching", "training_center"],
    
    # Retail (5 categories)
    "clothing_fashion": ["clothing_store", "shoe_store", "boutique"],
    "electronics": ["electronics_store", "mobile_phone_store"],
    "grocery_supermarket": ["supermarket", "grocery_or_supermarket", "convenience_store"],
    "home_garden": ["home_goods_store", "furniture_store", "hardware_store"],
    "general_retail": ["store", "shopping_mall", "department_store"],
    
    # Services (4 categories)
    "banks_finance": ["bank", "atm", "accounting", "finance"],
    "offices_corporate": ["office", "corporate_office", "coworking"],
    "real_estate": ["real_estate_agency", "property"],
    "car_services": ["car_dealer", "car_repair", "car_wash", "gas_station"],
    
    # Entertainment (2 categories)
    "entertainment": ["movie_theater", "cinema", "amusement_park", "bowling_alley"],
    "parks_recreation": ["park", "zoo", "stadium", "sports_complex"],
}

# Key amenities for distance features
DISTANCE_AMENITIES = [
    "shopping_mall",
    "movie_theater", 
    "university",
    "hospital",
    "transit_station",
    "park",
]

# Income proxy thresholds
INCOME_THRESHOLDS = {
    "high": {"avg_rating": 4.3, "premium_ratio": 0.4},
    "mid": {"avg_rating": 3.8, "premium_ratio": 0.2},
    "low": {"avg_rating": 0, "premium_ratio": 0},
}

# Search radius configurations
DEFAULT_RADIUS = 500  # meters
EXTENDED_RADIUS = 1000  # for distance calculations


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DensityFeatures:
    """Counts of various POI types in the area."""
    restaurants: int = 0
    cafes: int = 0
    bakeries: int = 0
    bars: int = 0
    gyms: int = 0
    spas: int = 0
    healthcare: int = 0
    schools: int = 0
    universities: int = 0
    training_centers: int = 0
    offices: int = 0
    malls: int = 0
    stores: int = 0
    banks: int = 0
    cinemas: int = 0
    parks: int = 0
    transit_stations: int = 0
    gas_stations: int = 0
    residential: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class DistanceFeatures:
    """Distances to key amenities in meters."""
    distance_to_mall: float = -1  # -1 means not found
    distance_to_cinema: float = -1
    distance_to_university: float = -1
    distance_to_hospital: float = -1
    distance_to_transit: float = -1
    distance_to_park: float = -1
    distance_to_main_road: float = -1  # Estimated based on transit
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class EconomicFeatures:
    """Economic proxy features derived from business data."""
    avg_business_rating: float = 0.0
    avg_review_count: float = 0.0
    total_businesses: int = 0
    premium_business_count: int = 0  # Price level 3-4
    economy_business_count: int = 0  # Price level 1-2
    premium_to_economy_ratio: float = 0.0
    income_proxy: str = "unknown"  # low/mid/high
    competition_density: float = 0.0  # businesses per 100m²
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CategoryCount:
    """Single category with count and percentage."""
    category: str
    count: int
    percentage: float
    business_names: List[str] = field(default_factory=list)  # Sample business names
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "count": self.count,
            "percentage": self.percentage,
            "business_names": self.business_names[:5]  # Top 5 names only
        }


@dataclass
class BusinessInfo:
    """Basic info about a business."""
    name: str
    category: str
    types: List[str]
    rating: Optional[float]
    reviews: Optional[int]
    price_level: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BackingFactor:
    """A data-backed insight for recommendations."""
    factor: str  # e.g., "High foot traffic potential"
    evidence: str  # e.g., "12 restaurants and 5 cafes in the area"
    implication: str  # e.g., "Good for food-related businesses"
    strength: str  # "strong", "moderate", "weak"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AreaAnalysis:
    """Comprehensive area analysis with categorized businesses."""
    total_businesses: int = 0
    top_5_categories: List[CategoryCount] = field(default_factory=list)
    all_categories: Dict[str, int] = field(default_factory=dict)
    business_list: List[BusinessInfo] = field(default_factory=list)
    backing_factors: List[BackingFactor] = field(default_factory=list)
    area_character: str = ""  # e.g., "Commercial hub", "Residential with retail"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_businesses": self.total_businesses,
            "top_5_categories": [c.to_dict() for c in self.top_5_categories],
            "all_categories": self.all_categories,
            "business_list": [b.to_dict() for b in self.business_list[:20]],  # Limit for response size
            "backing_factors": [f.to_dict() for f in self.backing_factors],
            "area_character": self.area_character
        }


@dataclass
class BusinessEnvironmentVector:
    """
    Complete Business Environment Vector for a location.
    
    Combines density, distance, and economic features into a single
    structured representation of the business environment.
    """
    # Location info
    grid_id: Optional[str] = None
    center_lat: float = 0.0
    center_lon: float = 0.0
    radius_meters: int = DEFAULT_RADIUS
    
    # Feature groups
    density: DensityFeatures = field(default_factory=DensityFeatures)
    distance: DistanceFeatures = field(default_factory=DistanceFeatures)
    economic: EconomicFeatures = field(default_factory=EconomicFeatures)
    
    # Enhanced area analysis with categories
    area_analysis: AreaAnalysis = field(default_factory=AreaAnalysis)
    
    # Metadata
    generated_at: str = ""
    api_calls_used: int = 0
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for API response."""
        result = {
            "grid_id": self.grid_id,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "radius_meters": self.radius_meters,
            "generated_at": self.generated_at,
            "api_calls_used": self.api_calls_used,
        }
        result.update(self.density.to_dict())
        result.update(self.distance.to_dict())
        result.update(self.economic.to_dict())
        result["area_analysis"] = self.area_analysis.to_dict()
        return result
    
    def to_prompt_format(self) -> str:
        """Format BEV for LLM prompt."""
        lines = [
            "[Business Environment Vector]",
            f"Location: ({self.center_lat:.6f}, {self.center_lon:.6f})",
            f"Analysis radius: {self.radius_meters}m",
            "",
            "=== Area Analysis ===",
            f"Total businesses in area: {self.area_analysis.total_businesses}",
            f"Area Character: {self.area_analysis.area_character}",
            "",
            "Top 5 Business Categories (from actual data):",
        ]
        
        for i, cat in enumerate(self.area_analysis.top_5_categories[:5], 1):
            names_str = ", ".join(cat.business_names[:3]) if cat.business_names else ""
            lines.append(f"  {i}. {cat.category}: {cat.count} businesses ({cat.percentage:.1f}%)")
            if names_str:
                lines.append(f"     Examples: {names_str}")
        
        # Add backing factors
        lines.extend([
            "",
            "=== Data-Backed Insights ===",
        ])
        for factor in self.area_analysis.backing_factors:
            lines.append(f"• [{factor.strength.upper()}] {factor.factor}")
            lines.append(f"  Evidence: {factor.evidence}")
            lines.append(f"  Implication: {factor.implication}")
            lines.append("")
        
        lines.extend([
            "=== Density Features ===",
            f"Restaurants: {self.density.restaurants}",
            f"Cafes: {self.density.cafes}",
            f"Gyms: {self.density.gyms}",
            f"Schools: {self.density.schools}",
            f"Universities: {self.density.universities}",
            f"Offices: {self.density.offices}",
            f"Malls: {self.density.malls}",
            f"Stores: {self.density.stores}",
            f"Parks: {self.density.parks}",
            f"Transit Stations: {self.density.transit_stations}",
            f"Healthcare: {self.density.healthcare}",
            f"Bars/Nightlife: {self.density.bars}",
            "",
            "=== Distance Features ===",
            f"Distance to nearest mall: {self._format_distance(self.distance.distance_to_mall)}",
            f"Distance to nearest cinema: {self._format_distance(self.distance.distance_to_cinema)}",
            f"Distance to nearest university: {self._format_distance(self.distance.distance_to_university)}",
            f"Distance to transit station: {self._format_distance(self.distance.distance_to_transit)}",
            f"Distance to park: {self._format_distance(self.distance.distance_to_park)}",
            "",
            "=== Economic Indicators ===",
            f"Average business rating: {self.economic.avg_business_rating:.2f}/5.0",
            f"Average review count: {self.economic.avg_review_count:.0f}",
            f"Total businesses in area: {self.economic.total_businesses}",
            f"Premium to economy ratio: {self.economic.premium_to_economy_ratio:.2f}",
            f"Income proxy: {self.economic.income_proxy}",
            f"Competition density: {self.economic.competition_density:.2f} businesses per 100m²",
        ]
        return "\n".join(lines)
    
    def _format_distance(self, distance: float) -> str:
        if distance < 0:
            return "Not found within search radius"
        elif distance < 100:
            return f"{distance:.0f}m (very close)"
        elif distance < 300:
            return f"{distance:.0f}m (close)"
        elif distance < 500:
            return f"{distance:.0f}m (moderate)"
        else:
            return f"{distance:.0f}m (far)"


# ============================================================================
# BEV Generator Class
# ============================================================================

class BEVGenerator:
    """
    Generates Business Environment Vectors from Google Places data.
    
    Uses Google Places API to gather POI data and compute structured
    features for location analysis.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize BEV generator.
        
        Args:
            api_key: Google Places API key. If None, reads from environment.
        """
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("Google Places API key is required")
        
        self.client = googlemaps.Client(key=self.api_key)
        self.logger = get_logger(__name__)
        self._api_calls = 0
        
        self.logger.info("BEVGenerator initialized")
    
    def generate_bev(
        self,
        center_lat: float,
        center_lon: float,
        radius_meters: int = DEFAULT_RADIUS,
        grid_id: str = None
    ) -> BusinessEnvironmentVector:
        """
        Generate complete BEV for a location.
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_meters: Search radius in meters
            grid_id: Optional grid identifier
            
        Returns:
            BusinessEnvironmentVector with all computed features
        """
        self._api_calls = 0
        
        self.logger.info(
            f"Generating BEV for ({center_lat:.6f}, {center_lon:.6f})",
            extra={"extra_fields": {"radius": radius_meters, "grid_id": grid_id}}
        )
        
        # Fetch all nearby places
        all_places = self._fetch_all_nearby_places(center_lat, center_lon, radius_meters)
        
        # Compute density features
        density = self._compute_density_features(all_places)
        
        # Compute distance features
        distance = self._compute_distance_features(
            center_lat, center_lon, all_places, radius_meters
        )
        
        # Compute economic features
        economic = self._compute_economic_features(all_places, radius_meters)
        
        # Compute area analysis with business categorization
        area_analysis = self._compute_area_analysis(all_places)
        
        bev = BusinessEnvironmentVector(
            grid_id=grid_id,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_meters=radius_meters,
            density=density,
            distance=distance,
            economic=economic,
            area_analysis=area_analysis,
            api_calls_used=self._api_calls
        )
        
        self.logger.info(
            f"BEV generated successfully",
            extra={"extra_fields": {
                "total_businesses": economic.total_businesses,
                "api_calls": self._api_calls
            }}
        )
        
        return bev
    
    def generate_bev_for_grid(
        self,
        grid_bounds: Dict[str, float],
        grid_id: str = None
    ) -> BusinessEnvironmentVector:
        """
        Generate BEV for a grid cell using its bounds.
        
        Args:
            grid_bounds: Dict with lat_north, lat_south, lon_east, lon_west
            grid_id: Grid identifier
            
        Returns:
            BusinessEnvironmentVector
        """
        # Calculate center
        center_lat = (grid_bounds["lat_north"] + grid_bounds["lat_south"]) / 2
        center_lon = (grid_bounds["lon_east"] + grid_bounds["lon_west"]) / 2
        
        # Calculate approximate radius
        lat_span = grid_bounds["lat_north"] - grid_bounds["lat_south"]
        lon_span = grid_bounds["lon_east"] - grid_bounds["lon_west"]
        radius = max(
            lat_span * 111000 / 2,  # Convert lat degrees to meters
            lon_span * 100000 / 2   # Approximate lon degrees to meters
        )
        radius = int(min(radius * 1.5, 1000))  # Extend slightly, cap at 1km
        
        return self.generate_bev(center_lat, center_lon, radius, grid_id)
    
    def _fetch_all_nearby_places(
        self,
        lat: float,
        lon: float,
        radius: int
    ) -> List[Dict]:
        """
        Fetch ALL nearby businesses comprehensively.
        
        Uses multiple approaches to ensure we capture all businesses:
        1. Broad "establishment" search (catches most businesses)
        2. Specific type searches for categories Google doesn't always include
        3. Text search for additional coverage
        """
        all_places = []
        seen_ids = set()
        
        # --- APPROACH 1: Broad establishment search (gets most businesses) ---
        broad_types = [
            "establishment",  # Catches most commercial places
            "point_of_interest",  # Generic POIs
            "store",  # All retail stores
            "food",  # All food establishments
        ]
        
        for broad_type in broad_types:
            try:
                results = self._nearby_search(lat, lon, radius, broad_type)
                for place in results:
                    place_id = place.get("place_id")
                    if place_id and place_id not in seen_ids:
                        seen_ids.add(place_id)
                        all_places.append(place)
            except Exception as e:
                self.logger.warning(f"Error fetching broad type {broad_type}: {e}")
        
        # --- APPROACH 2: Specific types to ensure coverage ---
        # These ensure we don't miss important categories
        specific_types = [
            # Food & Beverage
            "restaurant", "cafe", "bakery", "bar", "meal_takeaway",
            # Health & Fitness
            "gym", "spa", "doctor", "dentist", "hospital", "pharmacy",
            # Education
            "school", "university", "library",
            # Retail
            "shopping_mall", "supermarket", "clothing_store", "electronics_store",
            # Services
            "bank", "atm", "beauty_salon", "hair_care", "laundry",
            # Entertainment
            "movie_theater", "park", "bowling_alley", "night_club",
            # Transport
            "transit_station", "bus_station", "gas_station",
            # Professional
            "real_estate_agency", "insurance_agency", "lawyer",
        ]
        
        for place_type in specific_types:
            try:
                results = self._nearby_search(lat, lon, radius, place_type)
                for place in results:
                    place_id = place.get("place_id")
                    if place_id and place_id not in seen_ids:
                        seen_ids.add(place_id)
                        all_places.append(place)
            except Exception as e:
                self.logger.warning(f"Error fetching {place_type}: {e}")
                continue
        
        self.logger.info(f"Fetched {len(all_places)} unique businesses in {radius}m radius")
        return all_places
    
    def _nearby_search(
        self,
        lat: float,
        lon: float,
        radius: int,
        place_type: str
    ) -> List[Dict]:
        """Perform a single nearby search with pagination."""
        results = []
        
        try:
            response = self.client.places_nearby(
                location=(lat, lon),
                radius=radius,
                type=place_type
            )
            self._api_calls += 1
            
            results.extend(response.get("results", []))
            
            # Handle pagination (up to 2 more pages)
            page_count = 0
            while "next_page_token" in response and page_count < 2:
                import time
                time.sleep(2)  # Required delay for page token
                
                response = self.client.places_nearby(
                    page_token=response["next_page_token"]
                )
                self._api_calls += 1
                results.extend(response.get("results", []))
                page_count += 1
                
        except (ApiError, Timeout, TransportError) as e:
            self.logger.warning(f"API error in nearby search: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in nearby search: {e}")
        
        return results
    
    def _compute_density_features(self, places: List[Dict]) -> DensityFeatures:
        """Count POIs by category."""
        density = DensityFeatures()
        
        for place in places:
            place_types = set(place.get("types", []))
            
            # Check each density category
            for category, type_list in DENSITY_POI_TYPES.items():
                if any(t in place_types for t in type_list):
                    current = getattr(density, category, 0)
                    setattr(density, category, current + 1)
        
        return density
    
    def _compute_distance_features(
        self,
        center_lat: float,
        center_lon: float,
        places: List[Dict],
        radius: int
    ) -> DistanceFeatures:
        """Calculate distances to nearest key amenities."""
        distance = DistanceFeatures()
        
        # Type to attribute mapping
        type_mapping = {
            "shopping_mall": "distance_to_mall",
            "movie_theater": "distance_to_cinema",
            "university": "distance_to_university",
            "hospital": "distance_to_hospital",
            "transit_station": "distance_to_transit",
            "bus_station": "distance_to_transit",
            "subway_station": "distance_to_transit",
            "park": "distance_to_park",
        }
        
        # Find nearest of each type
        for place in places:
            place_types = set(place.get("types", []))
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            
            if not location:
                continue
            
            place_lat = location.get("lat", 0)
            place_lon = location.get("lng", 0)
            dist = self._haversine_distance(
                center_lat, center_lon, place_lat, place_lon
            )
            
            for poi_type, attr in type_mapping.items():
                if poi_type in place_types:
                    current = getattr(distance, attr)
                    if current < 0 or dist < current:
                        setattr(distance, attr, round(dist, 1))
        
        # Estimate main road distance from transit
        if distance.distance_to_transit >= 0:
            distance.distance_to_main_road = max(50, distance.distance_to_transit - 50)
        
        return distance
    
    def _compute_economic_features(
        self,
        places: List[Dict],
        radius: int
    ) -> EconomicFeatures:
        """Compute economic proxy features."""
        economic = EconomicFeatures()
        
        ratings = []
        review_counts = []
        premium_count = 0
        economy_count = 0
        
        for place in places:
            rating = place.get("rating")
            reviews = place.get("user_ratings_total", 0)
            price_level = place.get("price_level")
            
            if rating:
                ratings.append(rating)
            if reviews:
                review_counts.append(reviews)
            
            if price_level is not None:
                if price_level >= 3:
                    premium_count += 1
                elif price_level <= 2:
                    economy_count += 1
        
        economic.total_businesses = len(places)
        
        if ratings:
            economic.avg_business_rating = round(sum(ratings) / len(ratings), 2)
        
        if review_counts:
            economic.avg_review_count = round(sum(review_counts) / len(review_counts), 1)
        
        economic.premium_business_count = premium_count
        economic.economy_business_count = economy_count
        
        if economy_count > 0:
            economic.premium_to_economy_ratio = round(premium_count / economy_count, 2)
        elif premium_count > 0:
            economic.premium_to_economy_ratio = 2.0  # All premium
        
        # Determine income proxy
        if (economic.avg_business_rating >= INCOME_THRESHOLDS["high"]["avg_rating"] and
            economic.premium_to_economy_ratio >= INCOME_THRESHOLDS["high"]["premium_ratio"]):
            economic.income_proxy = "high"
        elif (economic.avg_business_rating >= INCOME_THRESHOLDS["mid"]["avg_rating"] and
              economic.premium_to_economy_ratio >= INCOME_THRESHOLDS["mid"]["premium_ratio"]):
            economic.income_proxy = "mid"
        else:
            economic.income_proxy = "low"
        
        # Competition density (per 100m²)
        area_100m2 = (math.pi * radius * radius) / 100
        if area_100m2 > 0:
            economic.competition_density = round(len(places) / area_100m2, 4)
        
        return economic
    
    def _compute_area_analysis(self, places: List[Dict]) -> AreaAnalysis:
        """
        Compute comprehensive area analysis with business categorization.
        
        Categorizes ALL businesses into 20+ categories and returns
        top 5 with counts and percentages, plus data-backed insights.
        """
        area = AreaAnalysis()
        category_counts: Dict[str, int] = {cat: 0 for cat in BUSINESS_CATEGORIES.keys()}
        category_businesses: Dict[str, List[str]] = {cat: [] for cat in BUSINESS_CATEGORIES.keys()}
        business_list: List[BusinessInfo] = []
        
        for place in places:
            place_types = set(place.get("types", []))
            place_name = place.get("name", "Unknown")
            
            # Determine primary category for this business
            assigned_category = "other"
            for category, type_list in BUSINESS_CATEGORIES.items():
                if any(t in place_types for t in type_list):
                    assigned_category = category
                    category_counts[category] += 1
                    category_businesses[category].append(place_name)
                    break
            
            # If no category matched, count as other
            if assigned_category == "other":
                if "other" not in category_counts:
                    category_counts["other"] = 0
                    category_businesses["other"] = []
                category_counts["other"] += 1
                category_businesses["other"].append(place_name)
            
            # Create business info
            business_info = BusinessInfo(
                name=place_name,
                category=assigned_category,
                types=list(place_types)[:5],  # Limit types stored
                rating=place.get("rating"),
                reviews=place.get("user_ratings_total"),
                price_level=place.get("price_level")
            )
            business_list.append(business_info)
        
        area.total_businesses = len(places)
        area.all_categories = category_counts
        area.business_list = business_list
        
        # Sort and get top 5 categories
        sorted_categories = sorted(
            [(cat, count) for cat, count in category_counts.items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        total = area.total_businesses if area.total_businesses > 0 else 1
        area.top_5_categories = [
            CategoryCount(
                category=cat,
                count=count,
                percentage=round((count / total) * 100, 1),
                business_names=category_businesses.get(cat, [])[:5]
            )
            for cat, count in sorted_categories[:5]
        ]
        
        # Generate backing factors from the data
        area.backing_factors = self._generate_backing_factors(
            category_counts, sorted_categories, total, places
        )
        
        # Determine area character
        area.area_character = self._determine_area_character(sorted_categories, total)
        
        return area
    
    def _generate_backing_factors(
        self,
        category_counts: Dict[str, int],
        sorted_categories: List[tuple],
        total: int,
        places: List[Dict]
    ) -> List[BackingFactor]:
        """Generate data-backed factors for recommendations."""
        factors = []
        
        # Count grouped categories
        food_count = (category_counts.get("restaurants", 0) + 
                      category_counts.get("cafes_coffee", 0) + 
                      category_counts.get("bakery_desserts", 0))
        fitness_count = (category_counts.get("gyms_fitness", 0) + 
                         category_counts.get("spa_wellness", 0))
        office_count = (category_counts.get("offices_corporate", 0) + 
                        category_counts.get("banks_finance", 0))
        education_count = (category_counts.get("schools", 0) + 
                           category_counts.get("universities_colleges", 0) +
                           category_counts.get("tutoring_training", 0))
        retail_count = (category_counts.get("clothing_fashion", 0) +
                        category_counts.get("electronics", 0) +
                        category_counts.get("grocery_supermarket", 0) +
                        category_counts.get("general_retail", 0))
        entertainment_count = (category_counts.get("entertainment", 0) +
                               category_counts.get("bars_nightlife", 0))
        
        # 1. Food density factor
        if food_count >= 8:
            factors.append(BackingFactor(
                factor="High food establishment density",
                evidence=f"{food_count} food businesses nearby ({category_counts.get('restaurants', 0)} restaurants, {category_counts.get('cafes_coffee', 0)} cafes)",
                implication="Indicates high foot traffic and food-seeking customers. May mean saturation for new food businesses, but proves demand exists.",
                strength="strong"
            ))
        elif food_count >= 4:
            factors.append(BackingFactor(
                factor="Moderate food scene",
                evidence=f"{food_count} food businesses in the area",
                implication="Room for differentiated food concepts. Customers already visit for dining.",
                strength="moderate"
            ))
        elif food_count < 2:
            factors.append(BackingFactor(
                factor="Food gap opportunity",
                evidence=f"Only {food_count} food businesses nearby",
                implication="Potential unserved demand for food options. Could be first-mover advantage.",
                strength="moderate"
            ))
        
        # 2. Fitness factor (helps determine gym viability)
        if fitness_count >= 3:
            factors.append(BackingFactor(
                factor="Competitive fitness market",
                evidence=f"{fitness_count} fitness/wellness businesses ({category_counts.get('gyms_fitness', 0)} gyms, {category_counts.get('spa_wellness', 0)} spas)",
                implication="High gym competition. New gym needs strong differentiation (specialty, price, equipment).",
                strength="strong"
            ))
        elif fitness_count == 0:
            factors.append(BackingFactor(
                factor="Fitness gap",
                evidence="No gyms or fitness centers in the area",
                implication="Potential opportunity for fitness business if population supports it.",
                strength="moderate"
            ))
        
        # 3. Office/Professional presence
        if office_count >= 5:
            factors.append(BackingFactor(
                factor="Strong professional presence",
                evidence=f"{office_count} offices/banks in area",
                implication="Daytime working population needs lunch spots, cafes, quick services. B2B opportunity.",
                strength="strong"
            ))
        elif office_count >= 2:
            factors.append(BackingFactor(
                factor="Some professional activity",
                evidence=f"{office_count} professional establishments nearby",
                implication="Mix of residential and professional. Good for services catering to both.",
                strength="moderate"
            ))
        
        # 4. Education factor
        if education_count >= 3:
            factors.append(BackingFactor(
                factor="Education hub",
                evidence=f"{education_count} educational institutions ({category_counts.get('schools', 0)} schools, {category_counts.get('universities_colleges', 0)} universities)",
                implication="Student population creates demand for affordable food, stationery, tutoring, entertainment.",
                strength="strong"
            ))
        
        # 5. Retail density
        if retail_count >= 6:
            factors.append(BackingFactor(
                factor="Commercial retail hub",
                evidence=f"{retail_count} retail stores in the area",
                implication="High shopping traffic. Service businesses can benefit from footfall.",
                strength="moderate"
            ))
        
        # 6. Calculate average ratings and reviews
        ratings = [p.get("rating") for p in places if p.get("rating")]
        reviews = [p.get("user_ratings_total", 0) for p in places if p.get("user_ratings_total")]
        
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            if avg_rating >= 4.2:
                factors.append(BackingFactor(
                    factor="High quality area",
                    evidence=f"Average business rating: {avg_rating:.1f}/5.0",
                    implication="Customers expect quality. Premium positioning may work better than budget.",
                    strength="moderate"
                ))
        
        if reviews:
            avg_reviews = sum(reviews) / len(reviews)
            if avg_reviews >= 100:
                factors.append(BackingFactor(
                    factor="Highly engaged customers",
                    evidence=f"Average {avg_reviews:.0f} reviews per business",
                    implication="Active customer base that reviews. Good word-of-mouth potential.",
                    strength="moderate"
                ))
        
        # 7. Overall density factor
        if total >= 30:
            factors.append(BackingFactor(
                factor="High business density zone",
                evidence=f"{total} total businesses in search radius",
                implication="Established commercial area with proven foot traffic.",
                strength="strong"
            ))
        elif total <= 10:
            factors.append(BackingFactor(
                factor="Low business density",
                evidence=f"Only {total} businesses in the area",
                implication="May be emerging area or residential. Lower competition but unproven demand.",
                strength="weak"
            ))
        
        return factors
    
    def _determine_area_character(
        self,
        sorted_categories: List[tuple],
        total: int
    ) -> str:
        """Determine the overall character of the area."""
        if total == 0:
            return "Undeveloped area"
        
        top_category = sorted_categories[0][0] if sorted_categories else "unknown"
        top_pct = (sorted_categories[0][1] / total * 100) if sorted_categories else 0
        
        # Character mapping based on dominant category
        character_map = {
            "restaurants": "Food & dining hub",
            "cafes_coffee": "Cafe culture area",
            "general_retail": "Retail/shopping zone",
            "grocery_supermarket": "Residential with daily needs",
            "offices_corporate": "Business district",
            "banks_finance": "Financial services hub",
            "schools": "Education-focused neighborhood",
            "universities_colleges": "University area",
            "gyms_fitness": "Health-conscious community",
            "healthcare_medical": "Healthcare corridor",
            "bars_nightlife": "Entertainment district",
        }
        
        character = character_map.get(top_category, "Mixed-use area")
        
        if top_pct >= 40:
            return f"{character} (strongly dominant)"
        elif top_pct >= 25:
            return f"{character} with diverse offerings"
        else:
            return "Diverse mixed-use area"
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_bev(
    lat: float,
    lon: float,
    radius: int = DEFAULT_RADIUS,
    grid_id: str = None
) -> BusinessEnvironmentVector:
    """Convenience function to generate BEV."""
    generator = BEVGenerator()
    return generator.generate_bev(lat, lon, radius, grid_id)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test with Clifton Block 2 center
    generator = BEVGenerator()
    bev = generator.generate_bev(
        center_lat=24.8160,
        center_lon=67.0280,
        radius_meters=500,
        grid_id="Clifton-Block2-007-008"
    )
    
    print("\n" + "="*60)
    print("BEV GENERATION TEST")
    print("="*60)
    print(bev.to_prompt_format())
    print("\n" + "="*60)
    print(f"API calls used: {bev.api_calls_used}")
