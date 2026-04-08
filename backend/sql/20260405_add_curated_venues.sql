-- Create curated_venues table for admin-managed recommendation baseline.
CREATE TABLE IF NOT EXISTS curated_venues (
    id UUID PRIMARY KEY,
    city VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    snippet TEXT DEFAULT '',
    source_domain VARCHAR(255) DEFAULT '',
    curated_rank INTEGER DEFAULT 50,
    estimated_cost DOUBLE PRECISION NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    opening_date DATE NULL,
    event_date TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_curated_venues_city ON curated_venues(city);
CREATE INDEX IF NOT EXISTS ix_curated_venues_category ON curated_venues(category);
CREATE INDEX IF NOT EXISTS ix_curated_venues_is_active ON curated_venues(is_active);
