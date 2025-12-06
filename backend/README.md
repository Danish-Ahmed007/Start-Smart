# Start-Smart Backend (Phase 1)

Phase 1 backend structure for data integration and spatial analysis.

## Architecture

```
backend/
├── src/
│   ├── adapters/          # Data source integrations
│   │   ├── google_places_adapter.py      # Google Places API
│   │   └── simulated_social_adapter.py   # Synthetic data
│   ├── services/          # Business logic
│   │   └── geospatial_service.py         # Spatial analysis
│   ├── database/          # Data access layer
│   │   ├── connection.py  # Connection pooling
│   │   └── models.py      # ORM and queries
│   └── utils/             # Utilities
│       └── logger.py      # Logging configuration
├── tests/                 # Test suite
├── scripts/               # CLI utilities
│   └── fetch_google_places.py  # Business data ingestion
└── README.md              # This file
```

## Components

### Adapters
- **GooglePlacesAdapter**: Fetches real business data from Google Places API (Phase 2)
- **SimulatedSocialAdapter**: Provides synthetic social posts from Phase 0 seed data

### Services
- **GeospatialService**: Grid-based spatial queries, opportunity scoring, distance calculations

### Database
- **Database**: Connection pool manager using psycopg2
- **DatabaseModels**: ORM layer with CRUD operations for domain models

### Utils
- **Logger**: Centralized logging with console and file output

## Setup

1. Ensure Phase 0 is complete:
   ```bash
   cd /workspaces/Start-Smart
   python scripts/init_db.py  # Initialize schema
   python scripts/seed_grids.py  # Seed 12 grids
   python scripts/seed_synthetic_posts.py  # Seed 680 posts
   ```

2. Verify database state:
   ```bash
   python scripts/verify_db.py
   ```

3. Run Phase 1 tests:
   ```bash
   pytest backend/tests/ -v
   ```

## Usage

### Fetch and seed business data (Phase 2)

```bash
# Dry run without API key (stub mode)
python backend/scripts/fetch_google_places.py --dry-run

# With Google Places API key
python backend/scripts/fetch_google_places.py --api-key YOUR_KEY --category Gym
```

### Import modules in your code

```python
from backend.src.adapters import GooglePlacesAdapter, SimulatedSocialAdapter
from backend.src.services import GeospatialService
from backend.src.database import Database, DatabaseModels, get_database
from backend.src.utils import Logger

# Initialize logger
logger = Logger.get_logger(__name__)

# Get database
db = get_database()
conn = db.get_connection()
models = DatabaseModels(conn)

# Use adapters
adapter = SimulatedSocialAdapter(database=models)
source = adapter.get_source_name()

# Use services
geo = GeospatialService(database=models)
dist = GeospatialService.haversine_distance(24.8305, 67.0595, 24.8310, 67.0600)
```

## Dependencies

- Python 3.10+
- psycopg2-binary (PostgreSQL driver)
- pydantic==1.10.12 (data validation)
- python-dotenv (configuration)

All dependencies are in `requirements.txt`.

## Phase 1 Milestones

1. ✓ Directory structure and module scaffolding
2. ✓ Database connection pooling
3. ✓ Adapter interfaces (Google Places, Simulated Social)
4. ✓ Geospatial service (distance, opportunity scoring)
5. ⧗ Business logic API endpoints (Phase 2)
6. ⧗ Real Google Places integration (Phase 2)
7. ⧗ Test coverage (Phase 2)

## Testing

Tests are organized by component:

```bash
# Run all tests
pytest backend/tests/

# Run specific test suite
pytest backend/tests/adapters/
pytest backend/tests/services/
```

## Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/backend.log` (DEBUG level and above, rotating file handler)

Set log level:
```python
from backend.src.utils import Logger
import logging

Logger.set_level(logging.DEBUG)
```

## Notes

- Phase 1 is focused on architecture and data integration interfaces
- Google Places API integration is stubbed (Phase 2)
- Simulated adapter reads from Phase 0 seed data
- All modules follow Pydantic v1 contracts from Phase 0
- Connection pooling uses psycopg2 (not SQLAlchemy ORM in Phase 1)
