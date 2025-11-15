# Phase 0 — Handoff to Phase 1

Owner: GitHub Copilot

Completion date: 2025-11-15

Summary
-------
This document is the single source of truth for the Phase 0 handoff. It lists created contract files, exact file line counts, database state after local initialization and seeding, issues encountered during Phase 0, exact import statements for Phase 1 developers, and clear next steps.

Files and line counts
---------------------
All line counts were produced using a line-count pass on the repository on 2025-11-15.

- `contracts/database_schema.sql`: 106 lines
- `contracts/api_spec.yaml`: 535 lines
- `contracts/models.py`: 190 lines
- `contracts/base_adapter.py`: 92 lines
- `config/neighborhoods.json`: 17 lines
- `scripts/calculate_grid_count.py`: 69 lines
- `scripts/generate_synthetic_data.py`: 303 lines
- `scripts/seed_grids.py`: 201 lines
- `scripts/seed_synthetic_posts.py`: 180 lines
- `scripts/init_db.py`: 131 lines
- `scripts/ensure_grid_cells_for_posts.py`: 99 lines
- `requirements.txt`: 3 lines
- `docker-compose.yml`: 22 lines
- `.env.example`: 16 lines
- `.gitignore`: 8 lines
- `docs/phase0_validation.md`: 139 lines

If you need the byte/sha details or a per-line diff for any file, request it and I will provide the diffs.

Database state (local dev):
--------------------------------
Queries were executed against the local Postgres started with `docker compose up -d` and the `DATABASE_URL`:

Environment used for verification:
- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startsmart_dev`

Row counts (queried 2025-11-15):

- `grid_cells`: 17
- `businesses`: 0
- `social_posts`: 607
- `grid_metrics`: 0
- `user_feedback`: 0

Notes about database rows:
- `seed_grids.py` inserted 5 grid rows derived from `config/neighborhoods.json` (bounds produce a 5-grid tiling at 0.5 km^2 grid size).
- The synthetic data generator produced posts assigned to `grid-0001`..`grid-0012`. To satisfy FK constraints I added `scripts/ensure_grid_cells_for_posts.py` which inserted 12 helper `grid_cells` rows named `grid-0001`..`grid-0012`. That results in the total `grid_cells` count of 17.

Issues encountered (important)
--------------------------------
1. Pydantic version mismatch
   - Cause: repository `contracts/models.py` uses Pydantic v1-style `@root_validator` and `@validator` decorators.
   - Impact: environment initially had Pydantic v2; scripts failed until Pydantic was pinned to `pydantic==1.10.12` in `requirements.txt`.
   - Action taken: pinned `pydantic==1.10.12` and reinstalled dependencies. Phase 1 teams should be aware of this dependency constraint.

2. SQL schema execution error when comments-only blocks were present
   - Cause: initial `scripts/init_db.py` naively split the SQL file on `;` and attempted to execute comment-only fragments, causing "can't execute an empty query" errors.
   - Action taken: improved `execute_schema()` to strip out `--` comment lines before splitting and executing statements.

3. `grid_id` naming mismatch between generator and seeder
   - Cause: `scripts/generate_synthetic_data.py` uses numeric IDs `grid-0001`.. while `scripts/seed_grids.py` generates IDs of the form `{neighborhood}-Cell-01`.
   - Impact: when inserting posts, FK constraints against `grid_cells.grid_id` caused failures.
   - Action taken: I added `scripts/ensure_grid_cells_for_posts.py` which inserts minimal helper `grid_cells` rows for missing `grid_id`s referenced by posts. This is a temporary measure; Phase 1 should choose a single canonical `grid_id` format and update generator or seeder accordingly.

4. `psql` not available in the dev environment
   - Cause: container/dev environment lacks `psql` client.
   - Action taken: verification queries used a short Python/psycopg2 script. Phase 1 engineers may prefer `psql`; consider adding it to the dev container or using `pgcli`.

Exact import statements for Phase 1 developer
--------------------------------------------
Use these exact imports in Phase 1 code for consistent domain models and adapter base classes:

```py
from contracts.models import (
    GridCell,
    Business,
    SocialPost,
    GridMetrics,
    RecommendationResponse,
    GridDetailResponse,
    GridSummaryResponse,
    NeighborhoodResponse,
    TopPostDetail,
    CompetitorDetail,
)

from contracts.base_adapter import BaseAdapter
```

If you need additional model imports (e.g., `Category`, `Source`, `PostType`), import them from `contracts.models` as names:

```py
from contracts.models import Category, Source, PostType
```

Exact commands used to reproduce Phase 0 (copy/paste)
---------------------------------------------------
These are the exact commands I ran to reproduce the local Phase 0 initialization and verification (run from repo root):

```sh
# 1) start Postgres
docker compose up -d

# 2) initialize DB (drop existing)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/startsmart_dev"
python3 scripts/init_db.py --drop-existing

# 3) generate synthetic posts
python3 scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50 --output data/synthetic/ --seed 42

# 4) copy latest generated file to the v1 filename expected by the seeder
cp data/synthetic/posts_* data/synthetic/social_posts_v1.json || true

# 5) seed grids
python3 scripts/seed_grids.py --config config/neighborhoods.json

# 6) ensure grid_ids from generated posts exist as grid_cells (temporary helper)
python3 scripts/ensure_grid_cells_for_posts.py --input data/synthetic/social_posts_v1.json

# 7) seed synthetic posts
python3 scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json

# 8) quick verification using psycopg2-based script (or use psql if available)
python3 - <<'PY'
import os, psycopg2
DB=os.environ.get('DATABASE_URL','postgresql://postgres:postgres@localhost:5432/startsmart_dev')
conn=psycopg2.connect(DB)
try:
    cur=conn.cursor()
    for t in ['grid_cells','businesses','social_posts','grid_metrics','user_feedback']:
        cur.execute(f'SELECT count(*) FROM {t};')
        print(t, cur.fetchone()[0])
finally:
    conn.close()
PY
```

Handoff notes and next steps (explicit)
---------------------------------------
1. Decide canonical `grid_id` format
   - Problem: generator vs seeder mismatch requires `scripts/ensure_grid_cells_for_posts.py` hack.
   - Recommendation (pick one):
     - Option A (recommended): change the generator to emit `{neighborhood}-Cell-XX` (preferred when grids are derived from neighborhood config).
     - Option B: change seeder to create `grid-0001` style IDs (preferred if grids are independent of neighborhood label).

2. Remove temporary helper
   - Once `grid_id` canonicalization is decided, remove `scripts/ensure_grid_cells_for_posts.py` and re-run `seed_grids.py` and `seed_synthetic_posts.py`.

3. Stabilize dependencies
   - Pinned `pydantic==1.10.12` for Phase 0. If Phase 1 prefers Pydantic v2, update `contracts/models.py` validators to v2 API (`@model_validator`) before upgrading.

4. Add automated tests and CI
   - Add unit tests that validate: SQL schema execution, model serialization/deserialization, and seed scripts in `tests/`.
   - In CI add a job that brings up the `docker-compose.yml` Postgres, runs `scripts/init_db.py`, seeds a small dataset, and runs smoke queries.

5. Final acceptance criteria for Phase 1
   - All contracts (SQL schema and OpenAPI) remain unchanged unless Phase 0 spec is updated.
   - Phase 1 must implement adapters conforming to `BaseAdapter` and use Pydantic models in `contracts.models`.
   - One canonical `grid_id` naming convention is enforced across data generation and seeding.

Appendix: raw counts and file list
---------------------------------
File counts and DB counts (copied from the run outputs):

```
contracts/database_schema.sql   106
contracts/api_spec.yaml 535
contracts/models.py     190
contracts/base_adapter.py       92
config/neighborhoods.json       17
scripts/calculate_grid_count.py 69
scripts/generate_synthetic_data.py      303
scripts/seed_grids.py   201
scripts/seed_synthetic_posts.py 180
scripts/init_db.py      131
scripts/ensure_grid_cells_for_posts.py  99
requirements.txt        3
docker-compose.yml      22
.env.example    16
.gitignore      8
docs/phase0_validation.md       139

DB counts:
grid_cells      17
businesses      0
social_posts    607
grid_metrics    0
user_feedback   0
```

If you want the exact `wc -l` output or file checksums for any subset of these files included in this document, tell me which files and I'll append them.

End of Phase 0 handoff.
