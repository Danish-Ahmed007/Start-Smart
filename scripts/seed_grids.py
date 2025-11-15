#!/usr/bin/env python3
"""Seed grid cells into Postgres from `config/neighborhoods.json`.

Generates grid cells for each neighborhood at approximately `grid_size_km2` each,
calculates lat/lon bounds for each grid cell, and inserts records into
`grid_cells` table.

Usage:
  export DATABASE_URL=postgres://user:pass@host:5432/dbname
  python3 scripts/seed_grids.py --config config/neighborhoods.json --dry-run

Dependencies: psycopg2-binary, python-dotenv
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2.extras import execute_values
except Exception:
    psycopg2 = None

# Ensure project root is on path so `contracts` can be imported when needed
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def subdivide_bounds(bounds: Dict[str, float], grids: int) -> List[Dict[str, float]]:
    # same logic as generator: choose rows/cols roughly square
    lat_n = bounds["lat_north"]
    lat_s = bounds["lat_south"]
    lon_e = bounds["lon_east"]
    lon_w = bounds["lon_west"]

    rows = int(math.floor(math.sqrt(grids)))
    if rows <= 0:
        rows = 1
    cols = int(math.ceil(grids / rows))

    lat_step = (lat_n - lat_s) / rows
    lon_step = (lon_e - lon_w) / cols

    result = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= grids:
                break
            min_lat = lat_s + r * lat_step
            max_lat = min_lat + lat_step
            min_lon = lon_w + c * lon_step
            max_lon = min_lon + lon_step
            idx += 1
            result.append(
                {
                    "min_lat": min_lat,
                    "max_lat": max_lat,
                    "min_lon": min_lon,
                    "max_lon": max_lon,
                }
            )
    return result


def calc_grid_count(bounds: Dict[str, float], grid_size_km2: float) -> int:
    # simple equirectangular approximation
    lat_n = bounds["lat_north"]
    lat_s = bounds["lat_south"]
    lon_e = bounds["lon_east"]
    lon_w = bounds["lon_west"]
    lat_diff = abs(lat_n - lat_s)
    lon_diff = abs(lon_e - lon_w)
    mean_lat = (lat_n + lat_s) / 2.0
    ns_km = lat_diff * 111.32
    ew_km = lon_diff * 111.32 * math.cos(math.radians(mean_lat))
    area_km2 = ns_km * ew_km
    return max(1, math.ceil(area_km2 / grid_size_km2))


def insert_grid_cells(conn, rows: List[Dict]) -> int:
    sql = (
        "INSERT INTO grid_cells (grid_id, neighborhood, min_lat, max_lat, min_lon, max_lon, area_km2, centroid_lat, centroid_lon)"
        " VALUES %s"
        " ON CONFLICT (grid_id) DO UPDATE SET neighborhood=EXCLUDED.neighborhood, min_lat=EXCLUDED.min_lat, max_lat=EXCLUDED.max_lat, min_lon=EXCLUDED.min_lon, max_lon=EXCLUDED.max_lon"
    )
    values = [
        (
            r["grid_id"],
            r["neighborhood"],
            r["min_lat"],
            r["max_lat"],
            r["min_lon"],
            r["max_lon"],
            r.get("area_km2"),
            r.get("centroid_lat"),
            r.get("centroid_lon"),
        )
        for r in rows
    ]
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    return len(values)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed grid cells from neighborhoods config")
    p.add_argument("--config", type=str, default="config/neighborhoods.json", help="Path to neighborhoods config")
    p.add_argument("--dry-run", action="store_true", help="Do not insert into DB; just print what would be done")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        logging.error("Config file not found: %s", cfg_path)
        raise SystemExit(1)

    data = json.loads(cfg_path.read_text())

    if psycopg2 is None:
        logging.error("psycopg2 is required but not installed. Install psycopg2-binary.")
        raise SystemExit(1)

    for nh in data.get("neighborhoods", []):
        nh_id = nh.get("id") or nh.get("name", "unknown").replace(" ", "_")
        bounds = nh.get("bounds")
        grid_size = float(nh.get("grid_size_km2", 0.5))
        grid_count = nh.get("grid_count") or calc_grid_count(bounds, grid_size)

        logging.info("Neighborhood %s -> grid_size=%s km^2, grid_count=%s", nh_id, grid_size, grid_count)

        cells = subdivide_bounds(bounds, int(grid_count))

        rows = []
        for idx, cell in enumerate(cells, start=1):
            # Use canonical numeric grid IDs to match generator output: grid-0001, grid-0002, ...
            grid_id = f"grid-{idx:04d}"
            centroid_lat = (cell["min_lat"] + cell["max_lat"]) / 2.0
            centroid_lon = (cell["min_lon"] + cell["max_lon"]) / 2.0
            # approximate area using equirectangular small-box method
            ns_km = abs(cell["max_lat"] - cell["min_lat"]) * 111.32
            ew_km = abs(cell["max_lon"] - cell["min_lon"]) * 111.32 * math.cos(math.radians(centroid_lat))
            area_km2 = ns_km * ew_km
            rows.append(
                {
                    "grid_id": grid_id,
                    "neighborhood": nh.get("name"),
                    "min_lat": cell["min_lat"],
                    "max_lat": cell["max_lat"],
                    "min_lon": cell["min_lon"],
                    "max_lon": cell["max_lon"],
                    "area_km2": area_km2,
                    "centroid_lat": centroid_lat,
                    "centroid_lon": centroid_lon,
                }
            )

        if args.dry_run:
            logging.info("Dry run mode - would insert %d grid cells for %s", len(rows), nh_id)
            for r in rows:
                logging.info("  %s: bounds=(%s,%s,%s,%s) area_km2=%.4f", r["grid_id"], r["min_lat"], r["max_lat"], r["min_lon"], r["max_lon"], r["area_km2"])
            continue

        if not DATABASE_URL:
            logging.error("DATABASE_URL is not set. Export it before running the script.")
            raise SystemExit(1)

        conn = None
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = False
            inserted = insert_grid_cells(conn, rows)
            conn.commit()
            logging.info("Inserted/updated %d grid_cells for %s", inserted, nh_id)
        except Exception:
            logging.exception("Failed to insert grid cells for %s; rolling back", nh_id)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    main()
