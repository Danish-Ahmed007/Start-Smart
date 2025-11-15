# Phase 0 — Manual Validation Template

This document is a template for recording manual validation results for Phase 0 (interface contracts) of StartSmart.

## 1. Validation methodology

- Objective: verify that grid generation, social post ingestion, and GOS calculations align with expectations for small sample neighborhoods.
- Scope: use the DHA Phase 2, Karachi neighborhood from `config/neighborhoods.json`.
- Tools used:
  - `scripts/init_db.py` to create DB schema
  - `scripts/generate_synthetic_data.py` to create synthetic social posts
  - `scripts/seed_grids.py` to insert grid cells
  - `scripts/seed_synthetic_posts.py` to insert posts
  - `psql` for ad-hoc queries
- Sampling strategy: validate 3 representative grids (one high-opportunity, one medium, one low) selected from the seeded opportunity assignments.

## 2. Environment

- Docker Compose: `docker-compose.yml` (Postgres 14)
- Database: `startsmart_dev`
- Date of validation: <!-- fill date -->
- Operator: <!-- name -->

## 3. Scripts run and results

Describe the exact commands run and paste console output where relevant.

Example:

```sh
docker compose up -d
python3 scripts/init_db.py --drop-existing
python3 scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50 --seed 42
python3 scripts/seed_grids.py --config config/neighborhoods.json
python3 scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json
psql startsmart_dev -c "SELECT COUNT(*) FROM grid_cells;"
```

Console output and results:

```
<!-- paste output here -->
```

## 4. Sample grids and manual business counts

For each sample grid, record:
- Grid ID
- Neighborhood
- Area (km^2)
- Manual business count (by manual lookup or verified dataset)
- Notes about what counts as a business for the category

### Grid A (high-opportunity)

- Grid ID: <!-- -->
- Area: <!-- -->
- Manual business count: <!-- -->
- Notes: <!-- -->

### Grid B (medium-opportunity)

- Grid ID: <!-- -->
- Area: <!-- -->
- Manual business count: <!-- -->
- Notes: <!-- -->

### Grid C (low-opportunity)

- Grid ID: <!-- -->
- Area: <!-- -->
- Manual business count: <!-- -->
- Notes: <!-- -->

## 5. Hand-calculated GOS for each grid

Provide the GOS formula used (documented in Phase 0) and manual calculations for each sample grid.

Example:

GOS = f(business_count, instagram_volume, reddit_mentions, engagement_score,...)

Show step-by-step numeric calculation for Grid A/B/C.

## 6. Feedback template for local entrepreneurs

Use this section to paste interview notes or survey answers from local entrepreneurs.

- Interviewee: <!-- name -->
- Role: <!-- -->
- Date: <!-- -->
- Notes: <!-- -->

## 7. Conclusions about GOS formula accuracy

- Summary of differences between hand-calculated GOS and system GOS
- Recommendations to adjust weights, data sources, or validation approach

## 8. Instructions for future validators

- How to pick grids (use opportunity label and centroid)
- How to find businesses (Google Maps, local directories)
- How to record evidence and attach screenshots

## 9. Run results (automation performed)

The following commands were executed to initialize the local dev DB, generate synthetic data, seed grids and posts, and verify counts. Commands were run on 2025-11-15 in the development environment.

Commands run:

```sh
docker compose up -d
python3 scripts/init_db.py --drop-existing
python3 scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50 --seed 42 --output data/synthetic/
python3 scripts/seed_grids.py --config config/neighborhoods.json
python3 scripts/ensure_grid_cells_for_posts.py --input data/synthetic/social_posts_v1.json
python3 scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json
```

Key console outputs (abridged):

- init_db.py: created tables: `businesses`, `grid_cells`, `grid_metrics`, `social_posts`, `user_feedback` (all empty initially)
- generate_synthetic_data.py: generated 607 posts across 12 grid cells (distribution: mention=327, demand=199, complaint=81)
- seed_grids.py: inserted 5 grid cells derived from `config/neighborhoods.json`
- ensure_grid_cells_for_posts.py: inserted 12 additional helper `grid_cells` rows to match generated `grid-0001...grid-0012` ids
- seed_synthetic_posts.py: validated 607 posts (0 invalid), inserted 607 posts

Final verification (via psycopg2 query):

```
grid_cells count: 17
social_posts count: 607
```

Notes:

- `psql` was not available in the environment, so verification used a small Python script with `psycopg2` to query counts.
- The grid count in `config/neighborhoods.json` currently equals 5 (derived from the provided bounds). If you prefer 12 grids, update the bounds or `grid_size_km2` in the config and re-run `scripts/seed_grids.py`.

