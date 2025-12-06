# Phase 2 Planning - Data Analysis & Recommendations

## Overview

Phase 2 will build the **Data Analysis and Recommendation Engine** layer on top of Phase 1's data integration foundation. This layer processes the businesses and social media data to generate insights and recommendations.

---

## Key Objectives

1. **Data Aggregation**: Compute grid-level metrics from raw data
2. **Recommendation Engine**: Generate location-based recommendations
3. **Social Insights**: Extract trends from social media data
4. **Performance Analytics**: Track metrics over time

---

## Proposed Architecture

```
Phase 1: Data Integration
  ↓
Phase 2: Data Analysis & Recommendations
  ├── Aggregation Service: Compute grid metrics
  ├── Recommendation Engine: Generate insights
  ├── Trend Service: Analyze social data
  └── Analytics Service: Performance tracking
  ↓
Phase 3: API Layer (REST/GraphQL)
  ↓
Phase 4: Frontend
```

---

## Core Components to Build

### 1. Aggregation Service

**Purpose**: Compute pre-aggregated metrics per grid/category

**Metrics to Calculate**:
- Total businesses per category
- Average rating by category
- Competitor density (businesses/km²)
- Top businesses (by rating)
- Business trend (new vs. established)

**Database Tables**:
- GridMetrics (already defined in Phase 0)
  - metric_id, grid_id (FK), category
  - business_count, avg_rating
  - top_posts_json, competitors_json
  - timestamp

**Implementation**:
```python
# backend/src/services/aggregation_service.py
class AggregationService:
    def compute_grid_metrics(self, grid_id: str, category: str) -> GridMetrics:
        """Compute metrics for a grid/category combination"""
        
    def compute_all_metrics(self) -> None:
        """Compute metrics for all grids"""
```

### 2. Recommendation Engine

**Purpose**: Generate personalized location recommendations

**Recommendation Types**:
- **Best Gyms**: Top rated gyms in neighborhood
- **Hidden Gems**: High-engagement posts with low business density
- **Trending**: Businesses gaining traction on social media
- **Value Picks**: High engagement, lower rating (up-and-coming)

**Implementation**:
```python
# backend/src/services/recommendation_service.py
class RecommendationService:
    def get_best_gyms(self, grid_id: str, limit: int = 5) -> List[Recommendation]:
        """Get top gyms by rating and reviews"""
        
    def get_trending(self, grid_id: str, days: int = 7) -> List[Recommendation]:
        """Get trending businesses by social engagement"""
        
    def get_hidden_gems(self, grid_id: str) -> List[Recommendation]:
        """Get high-potential businesses"""
```

### 3. Trend Service

**Purpose**: Analyze social media trends

**Trend Analysis**:
- Engagement trends by category
- Sentiment indicators (from post content)
- Growth metrics (new businesses/posts)
- Peak hours/days for activity

**Implementation**:
```python
# backend/src/services/trend_service.py
class TrendService:
    def get_category_trends(self, grid_id: str, days: int = 30) -> CategoryTrend:
        """Analyze trends in business categories"""
        
    def get_engagement_patterns(self, grid_id: str) -> EngagementPattern:
        """Identify when engagement peaks"""
```

### 4. Analytics Service

**Purpose**: Track system performance and data quality

**Metrics to Track**:
- API call success/failure rates
- Average response times
- Data freshness (last update per grid)
- Recommendation accuracy (if feedback data available)

**Implementation**:
```python
# backend/src/services/analytics_service.py
class AnalyticsService:
    def get_health_metrics(self) -> HealthMetrics:
        """Get system health status"""
        
    def get_data_freshness(self) -> DataFreshness:
        """Check how current the data is"""
```

---

## Implementation Sequence

### Phase 2A: Foundation (Week 1-2)
1. Create aggregation service
2. Build metrics computation
3. Add background job support
4. Implement caching for metrics

**Output**: GridMetrics table populated with computed data

### Phase 2B: Recommendations (Week 3-4)
1. Build recommendation engine
2. Implement ranking algorithms
3. Add filtering and personalization
4. Create recommendation caching

**Output**: Recommendation API endpoints ready for Phase 3

### Phase 2C: Analytics (Week 5)
1. Implement trend analysis
2. Build performance monitoring
3. Create analytics endpoints
4. Add data quality checks

**Output**: Analytics dashboard data ready

---

## Database Changes

### New Tables (from Phase 0 schema, needs population)
- `grid_metrics` - Already defined, needs aggregation logic
- Consider: `recommendation_log` (track which recommendations shown)
- Consider: `analytics_events` (track API usage)

### New Indexes Recommended
```sql
-- For fast metric lookups
CREATE INDEX idx_grid_metrics_grid_category 
ON grid_metrics(grid_id, category);

-- For recommendation queries
CREATE INDEX idx_businesses_grid_rating 
ON businesses(grid_id, rating DESC);

-- For engagement queries
CREATE INDEX idx_social_posts_grid_timestamp 
ON social_posts(grid_id, timestamp DESC);
```

---

## Recommended Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Scheduling | APScheduler | Lightweight job scheduler |
| Caching | Redis | Fast metric caching |
| Data Processing | Pandas | Efficient aggregations |
| Async | Celery | Background job queue |
| Metrics | Prometheus | System monitoring |
| Tests | pytest | Consistent with Phase 1 |

---

## API Preview (Phase 3)

These endpoints will be exposed in Phase 3:

```
GET /api/v1/grids/{grid_id}/metrics
  → Returns: GridMetrics for location

GET /api/v1/grids/{grid_id}/recommendations/{category}
  → Returns: List[Recommendation]

GET /api/v1/grids/{grid_id}/trends
  → Returns: Trends for location

GET /api/v1/analytics/health
  → Returns: System health metrics

POST /api/v1/recommendations/{rec_id}/feedback
  → Submit recommendation feedback
```

---

## Success Metrics for Phase 2

- ✓ All grid metrics computed and cached
- ✓ Recommendation engine returns relevant results
- ✓ Trend analysis identifies patterns in data
- ✓ Analytics tracks system performance
- ✓ All Phase 2 services fully tested
- ✓ <100ms latency for metric lookups
- ✓ Comprehensive documentation

---

## Dependencies on Phase 1

Phase 2 requires Phase 1 to be complete:

- ✓ `BusinessModel` table populated with real data
- ✓ `SocialPostModel` table populated with posts
- ✓ `GridCellModel` with geographic boundaries
- ✓ Logging infrastructure for debugging
- ✓ Database connection pool

**Status**: ✅ All Phase 1 requirements met

---

## Estimated Effort

| Component | Effort | Risk |
|-----------|--------|------|
| Aggregation Service | 20 hours | Low |
| Recommendation Engine | 25 hours | Medium |
| Trend Analysis | 15 hours | Medium |
| Analytics Service | 10 hours | Low |
| Testing & Integration | 20 hours | Low |
| **Total** | **~90 hours** | - |

---

## Next Steps

When ready to start Phase 2:

1. **Review this plan**: Adjust based on product requirements
2. **Set up APScheduler**: For background metric computation
3. **Create aggregation service**: Start with Aggregation Service (lowest risk)
4. **Build test data scenarios**: Use Phase 1 data for testing
5. **Implement incrementally**: Build, test, and verify each service

### To Start Phase 2 Implementation

```bash
# Create Phase 2 directory structure
mkdir -p backend/src/services/phase2
touch backend/src/services/phase2/__init__.py
touch backend/src/services/phase2/aggregation_service.py
touch backend/src/services/phase2/recommendation_service.py
touch backend/src/services/phase2/trend_service.py
touch backend/src/services/phase2/analytics_service.py

# Create test directory
mkdir -p backend/tests/services/phase2
touch backend/tests/services/phase2/__init__.py
touch backend/tests/services/phase2/test_aggregation.py
```

---

**Created**: December 6, 2024  
**Phase 1 Status**: ✅ COMPLETE  
**Phase 2 Status**: 📋 PLANNED (Ready to implement)
