#!/usr/bin/env python3
"""Seed synthetic social posts into Postgres `social_posts` table.

Reads a JSON file of posts, validates each against the Pydantic `SocialPost`
model located in `contracts.models`, and bulk-inserts into the database.

Usage:
  export DATABASE_URL=postgres://user:pass@host:5432/dbname
  python3 scripts/seed_synthetic_posts.py --input data/synthetic/posts_...json --dry-run

Dependencies: psycopg2-binary, python-dotenv
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2.extras import execute_values
except Exception:
    psycopg2 = None

# Ensure project root is on path to import contracts
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.models import SocialPost


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed synthetic social posts into DB")
    p.add_argument("--input", type=str, required=True, help="Path to JSON file with posts")
    p.add_argument("--dry-run", action="store_true", help="Validate and preview but do not insert")
    p.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk inserts")
    return p.parse_args()


def validate_posts(raw_posts: List[Dict]) -> (List[Dict], List[Dict]):
    valid = []
    invalid = []
    for p in raw_posts:
        try:
            sp = SocialPost(**p)
            # normalize to dict with proper types
            # ensure timestamp and created_at are strings in ISO format for DB
            d = sp.dict()
            valid.append(d)
        except Exception as e:
            invalid.append({"post": p, "error": str(e)})
    return valid, invalid


def insert_posts(conn, posts: List[Dict]) -> int:
    columns = [
        "post_id",
        "source",
        "text",
        "timestamp",
        "lat",
        "lon",
        "grid_id",
        "post_type",
        "engagement_score",
        "is_simulated",
        "created_at",
    ]
    values = [
        (
            p.get("post_id"),
            p.get("source"),
            p.get("text"),
            p.get("timestamp"),
            p.get("lat"),
            p.get("lon"),
            p.get("grid_id"),
            p.get("post_type"),
            p.get("engagement_score"),
            p.get("is_simulated", True),
            p.get("created_at"),
        )
        for p in posts
    ]

    sql = (
        "INSERT INTO social_posts (post_id, source, text, timestamp, lat, lon, grid_id, post_type, engagement_score, is_simulated, created_at)"
        " VALUES %s"
        " ON CONFLICT (post_id) DO NOTHING"
    )
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    return len(values)


def print_summary(valid_posts: List[Dict], invalid: List[Dict]):
    print("Summary:")
    print(f"  total_input: {len(valid_posts) + len(invalid)}")
    print(f"  valid: {len(valid_posts)}")
    print(f"  invalid: {len(invalid)}")

    counter_grid = Counter(p.get("grid_id") for p in valid_posts)
    counter_type = Counter(p.get("post_type") for p in valid_posts)

    print("  posts_per_grid (sample up to 10):")
    for g, c in list(counter_grid.items())[:10]:
        print(f"    {g}: {c}")

    print("  distribution_by_type:")
    for t, c in counter_type.items():
        print(f"    {t}: {c}")


def main() -> None:
    args = parse_args()
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if psycopg2 is None:
        logging.error("psycopg2 is required but not installed. Install psycopg2-binary.")
        raise SystemExit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        logging.error("Input file not found: %s", input_path)
        raise SystemExit(1)

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        logging.error("Input JSON must be an array of posts")
        raise SystemExit(1)

    logging.info("Validating %d posts...", len(raw))
    valid, invalid = validate_posts(raw)
    logging.info("Validation complete: %d valid, %d invalid", len(valid), len(invalid))

    print_summary(valid, invalid)

    if args.dry_run:
        logging.info("Dry-run mode: not inserting into DB")
        return

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logging.error("DATABASE_URL is not set; export it before running this script.")
        raise SystemExit(1)

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False

        total_inserted = 0
        batch_size = int(args.batch_size)
        for i in range(0, len(valid), batch_size):
            batch = valid[i : i + batch_size]
            logging.info("Inserting batch %d - %d", i + 1, i + len(batch))
            inserted = insert_posts(conn, batch)
            total_inserted += inserted
        conn.commit()
        logging.info("Inserted %d posts", total_inserted)
    except Exception:
        logging.exception("Failed inserting posts; rolling back")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
