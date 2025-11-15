#!/usr/bin/env python3
"""Synthetic social post generator for StartSmart Phase 0 Part 4.

Generates simulated social posts per-grid with configurable distributions and
outputs a JSON array of posts to the chosen output directory. Uses only
standard library modules for reproducibility in the dev container.

Usage:
  python3 scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50 --output data/synthetic/ --seed 42

Outputs: <output>/posts_<timestamp>_<seed>.json
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Default neighborhood bounds (DHA Phase 2, Karachi) — used if no config provided
DEFAULT_BOUNDS = {
    "lat_north": 24.8345,
    "lat_south": 24.8210,
    "lon_east": 67.0670,
    "lon_west": 67.0520,
}
DEFAULT_CATEGORIES = ["Gym", "Cafe"]

# Distribution constants
BASE_DISTRIBUTION = {"mention": 0.60, "demand": 0.25, "complaint": 0.15}
HIGH_OPP_BONUS = {"mention": -0.15, "demand": 0.10, "complaint": 0.05}
LOW_OPP_ADJUST = {"mention": 0.10, "demand": -0.05, "complaint": -0.05}


def subdivide_bounds(bounds: Dict[str, float], grids: int) -> List[Dict[str, float]]:
    """Subdivide a bounding box into approximately `grids` grid cells.

    Returns a list of dicts with grid_id, min_lat, max_lat, min_lon, max_lon.
    """
    lat_n = bounds["lat_north"]
    lat_s = bounds["lat_south"]
    lon_e = bounds["lon_east"]
    lon_w = bounds["lon_west"]

    # Compute grid layout rows x cols ~ grids
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
                    "grid_id": f"grid-{idx:04d}",
                    "min_lat": min_lat,
                    "max_lat": max_lat,
                    "min_lon": min_lon,
                    "max_lon": max_lon,
                }
            )
    return result


def random_point_in_bounds(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Tuple[float, float]:
    lat = random.uniform(min_lat, max_lat)
    lon = random.uniform(min_lon, max_lon)
    return lat, lon


def random_timestamp_within_days(days: int = 90) -> str:
    now = datetime.utcnow()
    delta = timedelta(days=random.uniform(0, days))
    ts = now - delta
    return ts.replace(microsecond=0).isoformat() + "Z"


def weighted_post_type(base: Dict[str, float], modifier: Dict[str, float]) -> str:
    # Apply modifier and normalize
    weights = {k: max(0.0, base.get(k, 0.0) + modifier.get(k, 0.0)) for k in base}
    total = sum(weights.values())
    if total <= 0:
        return "mention"
    choices = list(weights.keys())
    probs = [weights[k] / total for k in choices]
    return random.choices(choices, probs, k=1)[0]


TEMPLATES = {
    "Gym": {
        "mention": [
            "Anyone tried a good gym in Phase 2?",
            "Looking for workout recommendations near me.",
            "Saw some fitness places around Phase 2 — thoughts?",
        ],
        "demand": [
            "Looking for a good gym in Phase 2, any suggestions?",
            "Need a 24/7 gym close to DHA Phase 2.",
            "Where can I find personal trainers near Phase 2?",
        ],
        "complaint": [
            "There are barely any decent gyms in this area.",
            "Disappointed with the lack of affordable gyms nearby.",
        ],
    },
    "Cafe": {
        "mention": [
            "Any nice cafes in Phase 2?",
            "Where's a good spot for coffee around here?",
            "Looking for a quiet cafe to work from.",
        ],
        "demand": [
            "Anyone recommend a bakery/cafe in Phase 2?",
            "Need a cafe with good Wi-Fi close to DHA Phase 2.",
            "Looking for a cafe with outdoor seating nearby.",
        ],
        "complaint": [
            "Not many decent cafes in the area, sadly.",
            "Wish there were better coffee options here.",
        ],
    },
}


def generate_text(category: str, post_type: str) -> str:
    cat_templates = TEMPLATES.get(category, {})
    templates = cat_templates.get(post_type) or cat_templates.get("mention") or [f"Looking for {category} in Phase 2"]
    return random.choice(templates)


def generate_posts_for_grid(
    grid: Dict[str, float],
    avg_posts: int,
    category_choices: List[str],
    opportunity: str,
    seed: int | None = None,
) -> List[Dict]:
    posts: List[Dict] = []

    # Adjust posts count by opportunity
    if opportunity == "high":
        count = max(1, int(random.gauss(avg_posts * 1.8, avg_posts * 0.2)))
    elif opportunity == "low":
        count = max(0, int(random.gauss(avg_posts * 0.4, avg_posts * 0.15)))
    else:
        count = max(0, int(random.gauss(avg_posts * 1.0, avg_posts * 0.2)))

    # Post type distribution modifier
    if opportunity == "high":
        modifier = HIGH_OPP_BONUS
    elif opportunity == "low":
        modifier = LOW_OPP_ADJUST
    else:
        modifier = {k: 0.0 for k in BASE_DISTRIBUTION}

    for _ in range(count):
        category = random.choice(category_choices)
        post_type = weighted_post_type(BASE_DISTRIBUTION, modifier)

        # Engagement score weighting per opportunity
        if opportunity == "high":
            engagement = int(min(100, max(0, random.gauss(60, 20))))
        elif opportunity == "low":
            engagement = int(min(100, max(0, random.gauss(20, 15))))
        else:
            engagement = int(min(100, max(0, random.gauss(40, 20))))

        lat, lon = random_point_in_bounds(grid["min_lat"], grid["max_lat"], grid["min_lon"], grid["max_lon"])

        post = {
            "post_id": str(uuid.uuid4()),
            "source": "simulated",
            "text": generate_text(category, post_type),
            "timestamp": random_timestamp_within_days(90),
            "lat": lat,
            "lon": lon,
            "grid_id": grid["grid_id"],
            "post_type": post_type,
            "engagement_score": engagement,
            "is_simulated": True,
        }
        posts.append(post)

    return posts


def assign_opportunities(num_grids: int) -> List[str]:
    # 25% high, 50% medium, 25% low — distribute across grid indices
    indices = list(range(num_grids))
    random.shuffle(indices)
    high_n = max(1, int(round(num_grids * 0.25)))
    low_n = max(1, int(round(num_grids * 0.25)))
    medium_n = num_grids - high_n - low_n

    opportunities = [None] * num_grids
    for i in indices[:high_n]:
        opportunities[i] = "high"
    for i in indices[high_n: high_n + medium_n]:
        opportunities[i] = "medium"
    for i in indices[high_n + medium_n: high_n + medium_n + low_n]:
        opportunities[i] = "low"

    # Fallback fill
    for i in range(num_grids):
        if opportunities[i] is None:
            opportunities[i] = "medium"
    return opportunities


def write_output(posts: List[Dict], output_dir: Path, seed: int | None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    seed_part = f"_seed{seed}" if seed is not None else ""
    outfile = output_dir / f"posts_{ts}{seed_part}.json"
    with outfile.open("w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    return outfile


def load_config_bounds() -> Tuple[Dict[str, float], List[str]]:
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "neighborhoods.json"
    if cfg_path.exists():
        try:
            with cfg_path.open() as f:
                data = json.load(f)
            neighborhoods = data.get("neighborhoods", [])
            if neighborhoods:
                nb = neighborhoods[0]
                bounds = nb.get("bounds", DEFAULT_BOUNDS)
                categories = data.get("categories", DEFAULT_CATEGORIES)
                return bounds, categories
        except Exception:
            logging.exception("Failed to read config/neighborhoods.json; using defaults")
    return DEFAULT_BOUNDS, DEFAULT_CATEGORIES


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate synthetic social posts for grids")
    p.add_argument("--grids", type=int, default=12, help="Number of grid cells to generate (default 12)")
    p.add_argument(
        "--posts-per-grid",
        type=int,
        default=50,
        help="Average posts per grid (used as mean for per-grid counts, default 50)",
    )
    p.add_argument("--output", type=str, default="data/synthetic/", help="Output directory (default data/synthetic/)")
    p.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Starting synthetic data generation")

    if args.seed is not None:
        random.seed(args.seed)
        logging.info(f"Using seed: {args.seed}")

    bounds, categories = load_config_bounds()
    logging.info(f"Using bounds: {bounds}")
    logging.info(f"Categories: {categories}")

    grids = args.grids
    grid_cells = subdivide_bounds(bounds, grids)
    logging.info(f"Created {len(grid_cells)} grid cells")

    opportunities = assign_opportunities(len(grid_cells))

    all_posts: List[Dict] = []

    for i, grid in enumerate(grid_cells):
        opp = opportunities[i]
        logging.info(f"Generating posts for {grid['grid_id']} (opportunity={opp})")
        posts = generate_posts_for_grid(grid, args.posts_per_grid, categories, opp, args.seed)
        logging.info(f"  -> Generated {len(posts)} posts")
        all_posts.extend(posts)

    outpath = write_output(all_posts, Path(args.output), args.seed)
    logging.info(f"Wrote {len(all_posts)} posts to {outpath}")


if __name__ == "__main__":
    main()
