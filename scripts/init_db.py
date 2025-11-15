#!/usr/bin/env python3
"""Initialize the Postgres database using `contracts/database_schema.sql`.

Usage:
  export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startsmart_dev
  python3 scripts/init_db.py --drop-existing

Dependencies: psycopg2-binary, python-dotenv
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

try:
    import psycopg2
except Exception:
    psycopg2 = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Initialize DB schema from SQL file")
    p.add_argument("--schema", type=str, default="contracts/database_schema.sql", help="Path to schema SQL file")
    p.add_argument("--drop-existing", action="store_true", help="Drop existing tables in public schema before creating")
    return p.parse_args()


def drop_all_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cur.fetchall()]
        if not tables:
            logging.info("No existing tables to drop")
            return
        logging.info("Dropping %d existing tables", len(tables))
        for t in tables:
            cur.execute(f"DROP TABLE IF EXISTS public.\"{t}\" CASCADE;")


def execute_schema(conn, sql_text: str) -> None:
    # Remove SQL single-line comments and split statements by semicolon.
    lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        # skip SQL comment lines
        if stripped.startswith("--") or not stripped:
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]

    with conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt + ";")
            except Exception:
                logging.exception("Failed to execute statement: %s", stmt[:120])
                raise


def summarize_tables(conn) -> List[str]:
    rows = []
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        tables = [r[0] for r in cur.fetchall()]
        for t in tables:
            try:
                cur.execute(f"SELECT count(*) FROM public.\"{t}\";")
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = None
            rows.append(f"{t}: {cnt}")
    return rows


def main() -> None:
    args = parse_args()
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if psycopg2 is None:
        logging.error("psycopg2 is required but not installed.")
        raise SystemExit(1)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        logging.error("Schema file not found: %s", schema_path)
        raise SystemExit(1)

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logging.error("DATABASE_URL is not set. Export it or provide in .env")
        raise SystemExit(1)

    sql_text = schema_path.read_text(encoding="utf-8")

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False

        if args.drop_existing:
            drop_all_tables(conn)

        logging.info("Executing schema from %s", schema_path)
        execute_schema(conn, sql_text)
        conn.commit()

        logging.info("Schema executed successfully. Verifying tables...")
        summary = summarize_tables(conn)
        logging.info("Tables summary:\n%s", "\n".join(summary))

    except Exception:
        logging.exception("Failed to initialize DB; rolling back")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
