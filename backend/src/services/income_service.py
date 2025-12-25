"""
Income Data Service

Provides income and demographic data for Clifton sectors.
Uses data from config/income_data.json for MVP.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from src.utils.logger import get_logger


@dataclass
class IncomeData:
    """Income data for a sector."""
    avg_household_income_pkr: int
    median_income_pkr: int
    income_bracket: str  # low, middle, upper-middle, high
    spending_power: str  # low, moderate, moderate-high, high
    affordability_score: float  # 0-1 scale
    key_demographics: list
    avg_meal_spending: int
    avg_coffee_spending: int
    gym_budget_monthly: int
    price_sensitivity: str  # low, moderate, high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_household_income": self.avg_household_income_pkr,
            "median_income": self.median_income_pkr,
            "income_bracket": self.income_bracket,
            "spending_power": self.spending_power,
            "affordability_score": self.affordability_score,
            "key_demographics": self.key_demographics,
            "consumer_behavior": {
                "avg_meal_spending": self.avg_meal_spending,
                "avg_coffee_spending": self.avg_coffee_spending,
                "gym_budget_monthly": self.gym_budget_monthly,
                "price_sensitivity": self.price_sensitivity
            }
        }


class IncomeDataService:
    """Service for retrieving income data for locations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._data = self._load_income_data()
        
    def _load_income_data(self) -> Dict[str, Any]:
        """Load income data from config file."""
        # Try multiple paths
        paths = [
            Path(__file__).parent.parent.parent.parent / "config" / "income_data.json",
            Path("config/income_data.json"),
            Path("../config/income_data.json"),
        ]
        
        for path in paths:
            if path.exists():
                with open(path, 'r') as f:
                    self.logger.info(f"Loaded income data from {path}")
                    return json.load(f)
        
        self.logger.warning("Income data file not found, using defaults")
        return self._default_data()
    
    def _default_data(self) -> Dict[str, Any]:
        """Return default income data if file not found."""
        return {
            "clifton_income_data": {
                "Block2": {
                    "avg_household_income_pkr": 450000,
                    "median_income_pkr": 380000,
                    "income_bracket": "upper-middle",
                    "spending_power": "high",
                    "affordability_score": 0.85,
                    "key_demographics": ["Professionals", "Business Owners", "Established Families"],
                    "consumer_behavior": {
                        "avg_meal_spending": 2500,
                        "avg_coffee_spending": 800,
                        "gym_budget_monthly": 12000,
                        "price_sensitivity": "low"
                    }
                },
                "Block5": {
                    "avg_household_income_pkr": 380000,
                    "median_income_pkr": 320000,
                    "income_bracket": "middle",
                    "spending_power": "moderate-high",
                    "affordability_score": 0.72,
                    "key_demographics": ["Young Professionals", "Students", "Small Business Owners"],
                    "consumer_behavior": {
                        "avg_meal_spending": 1800,
                        "avg_coffee_spending": 600,
                        "gym_budget_monthly": 8000,
                        "price_sensitivity": "moderate"
                    }
                }
            },
            "sector_boundaries": {
                "Block2": {
                    "bounds": {"north": 24.8220, "south": 24.8100, "east": 67.0360, "west": 67.0200}
                },
                "Block5": {
                    "bounds": {"north": 24.8130, "south": 24.8010, "east": 67.0440, "west": 67.0320}
                }
            }
        }
    
    def get_sector_for_location(self, lat: float, lon: float) -> Optional[str]:
        """Determine which sector a location falls into."""
        boundaries = self._data.get("sector_boundaries", {})
        
        for sector, info in boundaries.items():
            bounds = info.get("bounds", {})
            if (bounds.get("south", 0) <= lat <= bounds.get("north", 0) and
                bounds.get("west", 0) <= lon <= bounds.get("east", 0)):
                return sector
        
        # Default fallback - estimate based on position
        # Block 2 is more north-west, Block 5 is more south-east
        center_lat = 24.8115
        if lat >= center_lat:
            return "Block2"
        return "Block5"
    
    def get_income_data(self, lat: float, lon: float) -> IncomeData:
        """Get income data for a location."""
        sector = self.get_sector_for_location(lat, lon)
        sector_data = self._data.get("clifton_income_data", {}).get(sector, {})
        
        consumer = sector_data.get("consumer_behavior", {})
        
        return IncomeData(
            avg_household_income_pkr=sector_data.get("avg_household_income_pkr", 400000),
            median_income_pkr=sector_data.get("median_income_pkr", 350000),
            income_bracket=sector_data.get("income_bracket", "middle"),
            spending_power=sector_data.get("spending_power", "moderate"),
            affordability_score=sector_data.get("affordability_score", 0.75),
            key_demographics=sector_data.get("key_demographics", ["General population"]),
            avg_meal_spending=consumer.get("avg_meal_spending", 2000),
            avg_coffee_spending=consumer.get("avg_coffee_spending", 700),
            gym_budget_monthly=consumer.get("gym_budget_monthly", 10000),
            price_sensitivity=consumer.get("price_sensitivity", "moderate")
        )
    
    def get_income_for_prompt(self, lat: float, lon: float) -> str:
        """Get formatted income data for LLM prompt."""
        income = self.get_income_data(lat, lon)
        sector = self.get_sector_for_location(lat, lon)
        
        return f"""
=== Income & Demographics for {sector} ===
Average Household Income: PKR {income.avg_household_income_pkr:,}/month
Income Bracket: {income.income_bracket}
Spending Power: {income.spending_power}
Key Demographics: {', '.join(income.key_demographics)}

Consumer Behavior:
- Average meal spending: PKR {income.avg_meal_spending}
- Average coffee spending: PKR {income.avg_coffee_spending}
- Typical gym budget: PKR {income.gym_budget_monthly}/month
- Price sensitivity: {income.price_sensitivity}
"""


# Singleton instance
_income_service: Optional[IncomeDataService] = None

def get_income_service() -> IncomeDataService:
    """Get the income data service instance."""
    global _income_service
    if _income_service is None:
        _income_service = IncomeDataService()
    return _income_service
