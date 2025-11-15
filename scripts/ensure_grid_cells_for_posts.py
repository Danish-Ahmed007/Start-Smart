#!/usr/bin/env python3
"""Ensure grid_cells rows exist for grid_ids referenced in a posts JSON file.

This inserts minimal grid_cells records for any grid_id referenced by posts
that do not already exist in `grid_cells` to satisfy foreign key constraints
during bulk inserts of social posts.

Usage:
  export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startsmart_dev
  python3 scripts/ensure_grid_cells_for_posts.py --input data/synthetic/social_posts_v1.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Set

from dotenv import load_dotenv

try:
    import psycopg2
except Exception:
    psycopg2 = None


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    return p.parse_args()


def main():
    args = parse_args()
    load_dotenv()
    if psycopg2 is None:
        logging.error("psycopg2 not installed")
        raise SystemExit(1)

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logging.error("DATABASE_URL not set")
        raise SystemExit(1)

    p = Path(args.input)
    if not p.exists():
        logging.error("Input file not found: %s", p)
        raise SystemExit(1)

    posts = json.loads(p.read_text(encoding="utf-8"))
    grid_ids: Set[str] = set(pst.get("grid_id") for pst in posts if pst.get("grid_id"))

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT grid_id FROM grid_cells;")
            existing = set(r[0] for r in cur.fetchall())

            missing = sorted(grid_ids - existing)
            if not missing:
                print("No missing grid_cells to insert")
                return
            print(f"Inserting {len(missing)} missing grid_cells")
            for gid in missing:
                # Insert a tiny bounding box placeholder; these are synthetic helper rows.
                # Use a default small bbox near 0 if no coordinates available.
                sample = next((pst for pst in posts if pst.get("grid_id") == gid), None)
                if sample and sample.get("lat") is not None and sample.get("lon") is not None:
                    lat = float(sample.get("lat"))
                    lon = float(sample.get("lon"))
                    min_lat = lat - 0.0005
                    max_lat = lat + 0.0005
                    min_lon = lon - 0.0005
                    max_lon = lon + 0.0005
                else:
                    min_lat = 0.0
                    max_lat = 0.001
                    min_lon = 0.0
                    max_lon = 0.001

                centroid_lat = (min_lat + max_lat) / 2.0
                centroid_lon = (min_lon + max_lon) / 2.0
                # approximate area
                area_km2 = 0.0001
                cur.execute(
                    "INSERT INTO grid_cells (grid_id, neighborhood, min_lat, max_lat, min_lon, max_lon, area_km2, centroid_lat, centroid_lon) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (grid_id) DO NOTHING",
                    (gid, "synthetic-helper", min_lat, max_lat, min_lon, max_lon, area_km2, centroid_lat, centroid_lon),
                )
        conn.commit()
        print(f"Inserted {len(missing)} grid_cells")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
