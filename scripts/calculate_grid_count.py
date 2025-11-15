#!/usr/bin/env python3
"""Calculate grid counts for neighborhoods in `config/neighborhoods.json`.

This uses a simple equirectangular approximation suitable for small bounding boxes:
  - 1 degree latitude ~= 111.32 km
  - 1 degree longitude ~= 111.32 * cos(mean_lat)
Area (km^2) = (lat_diff * 111.32) * (lon_diff * 111.32 * cos(mean_lat))

Grid count = ceil(area / grid_size_km2)

Run:
  python3 scripts/calculate_grid_count.py
"""
from __future__ import annotations

import json
import math
from math import cos, radians
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "neighborhoods.json"


def calc_grid_info(bounds: dict, grid_size_km2: float) -> dict:
    lat_north = float(bounds["lat_north"]) 
    lat_south = float(bounds["lat_south"]) 
    lon_east = float(bounds["lon_east"]) 
    lon_west = float(bounds["lon_west"]) 

    lat_diff = abs(lat_north - lat_south)
    lon_diff = abs(lon_east - lon_west)
    mean_lat = (lat_north + lat_south) / 2.0

    ns_km = lat_diff * 111.32
    ew_km = lon_diff * 111.32 * cos(radians(mean_lat))
    area_km2 = ns_km * ew_km

    grid_count = math.ceil(area_km2 / grid_size_km2) if grid_size_km2 > 0 else 0

    return {
        "ns_km": ns_km,
        "ew_km": ew_km,
        "area_km2": area_km2,
        "grid_count": grid_count,
    }


def main() -> None:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config file not found: {CONFIG_PATH}")

    data = json.loads(CONFIG_PATH.read_text())
    for nh in data.get("neighborhoods", []):
        bounds = nh.get("bounds", {})
        grid_size = float(nh.get("grid_size_km2", 0.5))
        info = calc_grid_info(bounds, grid_size)

        print(f"Neighborhood: {nh.get('name')} (id: {nh.get('id')})")
        print(f"  Bounds: {bounds}")
        print(f"  NS distance (km): {info['ns_km']:.4f}")
        print(f"  EW distance (km): {info['ew_km']:.4f}")
        print(f"  Area (km^2): {info['area_km2']:.4f}")
        print(f"  Grid size (km^2): {grid_size}")
        print(f"  Calculated grid_count: {info['grid_count']}")
        print()


if __name__ == "__main__":
    main()
