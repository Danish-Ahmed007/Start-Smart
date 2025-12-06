# Database Setup - SQLAlchemy 2.0 ORM

## Overview

Phase 1 backend uses SQLAlchemy 2.0 with a modern async-ready architecture. The database layer provides:

- **Connection Management**: Singleton pattern with connection pooling
- **ORM Models**: Declarative models for all 5 Phase 0 tables
- **Repository Pattern**: CRUD operations for each entity
- **Context Manager Pattern**: Automatic session management with commit/rollback
- **Multi-Database Support**: PostgreSQL (production) and SQLite (testing)

## Architecture

### 1. Connection Management (`connection.py`)

```
DatabaseConnection (Singleton)
├── SQLAlchemy Engine (with pooling)
├── Session Factory
└── Methods:
    ├── get_session() - Raw session (not recommended)
    ├── get_session_context() - Context manager (recommended)
    ├── create_all_tables() - Initialize schema
    ├── drop_all_tables() - Clean database
    └── dispose_pool() - Cleanup
```

**Key Features:**
- **PostgreSQL**: QueuePool with pool_size=5, max_overflow=10
- **SQLite**: NullPool (no pooling, better for testing)
- **Pooling Options**:
  - `pool_pre_ping=True` - Verify connections before use
  - `pool_recycle=3600` - Recycle stale connections
  - Connection timeout handling

### 2. ORM Models (`models.py`)

Five SQLAlchemy models mapping to Phase 0 schema:

#### GridCellModel
```python
grid_id (PK, String)
centroid_lat, centroid_lon (Float)
lat_north, lat_south, lon_west, lon_east (Float)
area_km2 (Float)
created_at (DateTime)

Relationships:
- businesses (1:N)
- social_posts (1:N)
- grid_metrics (1:N)
- user_feedback (1:N)
```

#### BusinessModel
```python
business_id (PK, String)
name, category, source (String)
lat, lon (Float)
rating, review_count (Float/Int, nullable)
grid_id (FK to GridCellModel)
fetched_at (DateTime)
```

#### SocialPostModel
```python
post_id (PK, String)
content (String)
post_type (String) - "mention", "demand", "complaint"
engagement_score (Float)
timestamp (DateTime)
source, is_simulated (String, Boolean)
grid_id (FK to GridCellModel)
created_at (DateTime)
```

#### GridMetricsModel
```python
metric_id (PK, Integer, auto-increment)
grid_id (FK to GridCellModel)
category (String)
top_posts, competitors (JSON - lists)
created_at (DateTime)
```

#### UserFeedbackModel
```python
feedback_id (PK, String)
grid_id (FK to GridCellModel)
rating (Integer) - -1, 0, or 1
comments (String, nullable)
created_at (DateTime)
```

### 3. Repository Pattern (`repository.py`)

Five repository classes for CRUD operations:

```
GridRepository
├── get_by_id(grid_id)
├── list_all(limit, offset)
├── create(grid)
├── update(grid_id, **kwargs)
└── delete(grid_id)

BusinessRepository
├── get_by_id(business_id)
├── get_by_grid(grid_id, limit)
├── create(business)
├── create_many(businesses)
└── delete_by_grid(grid_id)

SocialPostRepository
├── get_by_id(post_id)
├── get_by_grid(grid_id, limit, offset)
├── get_by_type(grid_id, post_type, limit)
├── create(post)
├── create_many(posts)
└── delete_by_grid(grid_id)

GridMetricsRepository
├── get_by_grid_and_category(grid_id, category)
├── get_by_grid(grid_id)
├── create(metrics)
└── update(metric_id, **kwargs)

UserFeedbackRepository
├── get_by_id(feedback_id)
├── get_by_grid(grid_id, limit)
├── create(feedback)
└── get_average_rating(grid_id)
```

## Usage

### 1. Basic Setup

```python
from backend.src.database import get_db, Base

# Initialize database (happens on first call)
db = get_db()

# Create all tables
db.create_all_tables()

# Get list of existing tables
tables = db.get_table_names()
print(tables)  # ['grid_cells', 'businesses', 'social_posts', ...]
```

### 2. Session Management (Context Manager Pattern)

```python
from backend.src.database import get_session
from backend.src.database import GridRepository

# Recommended way - automatic commit/rollback
with get_session() as session:
    grids = session.query(GridCellModel).all()
    # Automatic commit on success, rollback on error
```

### 3. Using Repositories

```python
from backend.src.database import GridRepository, BusinessRepository

# Get a single grid
grid = GridRepository.get_by_id("grid-0001")
print(f"Grid: {grid.grid_id}, Area: {grid.area_km2} km²")

# List all grids
grids = GridRepository.list_all(limit=10, offset=0)

# Get businesses in a grid
businesses = BusinessRepository.get_by_grid("grid-0001", limit=50)
for biz in businesses:
    print(f"{biz.name} - Rating: {biz.rating}")

# Create a new business
from backend.src.database import BusinessModel
from datetime import datetime

new_biz = BusinessModel(
    business_id="biz-123",
    name="Coffee Shop",
    lat=24.8305,
    lon=67.0595,
    category="Cafe",
    rating=4.5,
    review_count=100,
    source="google_places",
    grid_id="grid-0001",
    fetched_at=datetime.utcnow()
)
BusinessRepository.create(new_biz)

# Bulk create
posts = [SocialPostModel(...), SocialPostModel(...)]
SocialPostRepository.create_many(posts)
```

### 4. Advanced Queries

```python
from backend.src.database import SocialPostRepository

# Get high-engagement posts
posts = SocialPostRepository.get_by_type("grid-0001", "demand", limit=100)

# Get average user rating
avg_rating = UserFeedbackRepository.get_average_rating("grid-0001")
print(f"Average rating: {avg_rating}")

# Get metrics for grid
metrics = GridMetricsRepository.get_by_grid("grid-0001")
for metric in metrics:
    print(f"{metric.category}: {metric.top_posts}")
```

### 5. Direct Session Usage

```python
from backend.src.database import get_db
from backend.src.database import GridCellModel, BusinessModel

db = get_db()

# Get a raw session (use with caution)
session = db.get_session()
try:
    # Do something with session
    grids = session.query(GridCellModel).all()
finally:
    session.close()

# Better: Use context manager through get_session()
with db.get_session_context() as session:
    grids = session.query(GridCellModel).all()
    # Auto-commit and close
```

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@localhost:5432/startsmart_dev

# Optional
SQL_ECHO=false  # Set to 'true' to log SQL statements
```

### For Testing (SQLite)

```bash
DATABASE_URL=sqlite:///test.db
```

## Connection Pool Settings

### PostgreSQL (Production)

```python
pool_size = 5          # Minimum connections to keep open
max_overflow = 10      # Additional connections when needed
pool_pre_ping = True   # Verify connections are alive
pool_recycle = 3600    # Recycle connections after 1 hour
```

This means:
- 5 connections always available
- Can grow to 15 max (5 + 10 overflow)
- Each connection recycled after 1 hour
- Before using a connection, verify it's still alive

### SQLite (Testing)

```python
poolclass = NullPool   # Don't pool connections
timeout = 15           # Connection timeout
check_same_thread = False
```

## Error Handling

All repository methods handle errors gracefully:

```python
try:
    grid = GridRepository.get_by_id("nonexistent")
except Exception as e:
    logger.error(f"Error: {e}")
    # Handle gracefully
```

Sessions automatically rollback on error:

```python
try:
    with get_session() as session:
        # Do something
        session.query(...).delete()  # If error occurs here
        # Automatically rolls back
except Exception:
    # Transaction rolled back
    pass
```

## Initialization

### First Time Setup

```python
from backend.src.database import get_db

db = get_db()
db.create_all_tables()  # Creates all tables from ORM models
```

### Production Initialization

For production, use Alembic migrations instead:

```bash
# Install Alembic
pip install alembic

# Initialize migration folder
alembic init alembic

# Create migration script
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

## Testing

For unit tests, use SQLite:

```python
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.src.database import get_db

db = get_db()
db.create_all_tables()  # Create in-memory database
# Run tests
db.drop_all_tables()  # Clean up
```

## Performance Tips

1. **Use batch operations** when possible:
   ```python
   BusinessRepository.create_many(businesses)  # Faster than individual creates
   ```

2. **Use pagination** for large queries:
   ```python
   GridRepository.list_all(limit=100, offset=0)
   ```

3. **Filter at database level**:
   ```python
   SocialPostRepository.get_by_type("grid-0001", "demand")  # Filtered in DB
   ```

4. **Close sessions properly**:
   ```python
   with get_session() as session:  # Always use context manager
       ...
   ```

5. **Use connection pooling** - automatic with PostgreSQL

## Troubleshooting

### "No such table" error
- Run `db.create_all_tables()`

### "Connection refused" error
- Check DATABASE_URL is correct
- Check PostgreSQL is running
- Check credentials

### "Too many connections" error
- Increase `max_overflow` in connection pool
- Use context managers to ensure sessions close
- Don't hold onto sessions unnecessarily

### "Check same thread" error (SQLite)
- Already handled: `check_same_thread=False` in connection config

## Next Steps

1. **API Integration**: Use repositories in FastAPI endpoints
2. **Caching**: Add Redis caching layer for frequently accessed data
3. **Migrations**: Implement Alembic for schema versioning
4. **Testing**: Create test fixtures using SQLite database
