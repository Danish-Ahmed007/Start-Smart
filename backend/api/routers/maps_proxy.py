"""
Google Maps API Proxy Router

Proxies Google Maps API requests to hide the API key from the frontend.
This prevents exposing the API key in client-side code.
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter()


@router.get("/maps/geocode")
async def geocode_proxy(
    address: Optional[str] = Query(None, description="Address to geocode"),
    latlng: Optional[str] = Query(None, description="Latitude,longitude to reverse geocode"),
):
    """
    Proxy for Google Maps Geocoding API.
    Either address or latlng must be provided.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    if not address and not latlng:
        raise HTTPException(status_code=400, detail="Either address or latlng must be provided")
    
    params = {"key": api_key}
    if address:
        params["address"] = address
    if latlng:
        params["latlng"] = latlng
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=10.0
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Geocoding request failed: {str(e)}")


@router.get("/maps/places/nearbysearch")
async def places_nearby_proxy(
    location: str = Query(..., description="Latitude,longitude"),
    radius: int = Query(..., description="Radius in meters"),
    type: Optional[str] = Query(None, description="Place type to search for"),
    keyword: Optional[str] = Query(None, description="Keyword to search for"),
):
    """
    Proxy for Google Places API Nearby Search.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    params = {
        "key": api_key,
        "location": location,
        "radius": radius,
    }
    if type:
        params["type"] = type
    if keyword:
        params["keyword"] = keyword
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params=params,
                timeout=10.0
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Places search failed: {str(e)}")


@router.get("/maps/places/details")
async def places_details_proxy(
    place_id: str = Query(..., description="Google Place ID"),
):
    """
    Proxy for Google Places API Place Details.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    params = {
        "key": api_key,
        "place_id": place_id,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params=params,
                timeout=10.0
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Place details request failed: {str(e)}")
