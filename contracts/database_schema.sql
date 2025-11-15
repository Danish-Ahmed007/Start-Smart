-- StartSmart Phase 0 - Part 1: PostgreSQL schema (contracts/phase0_part1_database_schema.sql)
-- Locked interface for Phase 0 Part 1: Do not change without updating Phase 0 spec

-- Table: grid_cells
CREATE TABLE IF NOT EXISTS grid_cells (
    grid_id TEXT PRIMARY KEY,
    neighborhood TEXT NOT NULL,
    min_lat DOUBLE PRECISION NOT NULL CHECK (min_lat >= -90 AND min_lat <= 90),
    max_lat DOUBLE PRECISION NOT NULL CHECK (max_lat >= -90 AND max_lat <= 90),
    min_lon DOUBLE PRECISION NOT NULL CHECK (min_lon >= -180 AND min_lon <= 180),
    max_lon DOUBLE PRECISION NOT NULL CHECK (max_lon >= -180 AND max_lon <= 180),
    area_km2 DOUBLE PRECISION,
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CHECK (min_lat < max_lat),
    CHECK (min_lon < max_lon)
);

-- Table: businesses
CREATE TABLE IF NOT EXISTS businesses (
    business_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lat DOUBLE PRECISION CHECK (lat >= -90 AND lat <= 90),
    lon DOUBLE PRECISION CHECK (lon >= -180 AND lon <= 180),
    category TEXT,
    rating NUMERIC(3,2) CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER DEFAULT 0 CHECK (review_count >= 0),
    source TEXT,
    grid_id TEXT REFERENCES grid_cells(grid_id) ON DELETE SET NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Table: social_posts
CREATE TABLE IF NOT EXISTS social_posts (
    post_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    text TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    lat DOUBLE PRECISION CHECK (lat >= -90 AND lat <= 90),
    lon DOUBLE PRECISION CHECK (lon >= -180 AND lon <= 180),
    grid_id TEXT REFERENCES grid_cells(grid_id) ON DELETE SET NULL,
    post_type TEXT,
    engagement_score NUMERIC,
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Table: grid_metrics
CREATE TABLE IF NOT EXISTS grid_metrics (
    id SERIAL PRIMARY KEY,
    grid_id TEXT NOT NULL REFERENCES grid_cells(grid_id) ON DELETE CASCADE,
    category TEXT,
    business_count INTEGER DEFAULT 0 CHECK (business_count >= 0),
    instagram_volume INTEGER DEFAULT 0 CHECK (instagram_volume >= 0),
    reddit_mentions INTEGER DEFAULT 0 CHECK (reddit_mentions >= 0),
    gos NUMERIC,
    confidence NUMERIC,
    top_posts_json JSONB,
    competitors_json JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (grid_id, category)
);

-- Table: user_feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    grid_id TEXT NOT NULL REFERENCES grid_cells(grid_id) ON DELETE CASCADE,
    category TEXT,
    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
    comment TEXT,
    user_email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
-- Businesses
CREATE INDEX IF NOT EXISTS idx_businesses_grid_id ON businesses (grid_id);
CREATE INDEX IF NOT EXISTS idx_businesses_lat_lon ON businesses (lat, lon);
CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses (category);
CREATE INDEX IF NOT EXISTS idx_businesses_rating ON businesses (rating);
CREATE INDEX IF NOT EXISTS idx_businesses_source ON businesses (source);

-- Social posts
CREATE INDEX IF NOT EXISTS idx_social_posts_grid_id ON social_posts (grid_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_timestamp ON social_posts (timestamp);
CREATE INDEX IF NOT EXISTS idx_social_posts_source ON social_posts (source);

-- Grid metrics
CREATE INDEX IF NOT EXISTS idx_grid_metrics_grid_category ON grid_metrics (grid_id, category);
CREATE INDEX IF NOT EXISTS idx_grid_metrics_last_updated ON grid_metrics (last_updated);
-- JSONB indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_grid_metrics_top_posts_json ON grid_metrics USING GIN (top_posts_json);
CREATE INDEX IF NOT EXISTS idx_grid_metrics_competitors_json ON grid_metrics USING GIN (competitors_json);

-- User feedback
CREATE INDEX IF NOT EXISTS idx_user_feedback_grid_id ON user_feedback (grid_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_user_email ON user_feedback (user_email);

-- Grid cells
CREATE INDEX IF NOT EXISTS idx_grid_cells_neighborhood ON grid_cells (neighborhood);
CREATE INDEX IF NOT EXISTS idx_grid_cells_centroid ON grid_cells (centroid_lat, centroid_lon);

-- Additional notes:
-- - For production spatial queries consider adding PostGIS geometry columns and GiST indexes.
-- - IDs are stored as TEXT to remain flexible; teams may migrate to UUID type later.
