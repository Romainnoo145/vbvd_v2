-- AI Curator Assistant Database Schema
-- PostgreSQL with pgvector extension for embeddings
--
-- This script sets up the complete database infrastructure for the 3-stage curator workflow

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text similarity matching

-- Set up database metadata
COMMENT ON DATABASE curator_db IS 'AI Curator Assistant - 3-Stage Agent System Database';

-- ============================================================================
-- CORE WORKFLOW TABLES
-- ============================================================================

-- Curator Sessions - Main workflow tracking
CREATE TABLE curator_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curator_name VARCHAR(255),
    institution_id VARCHAR(100) DEFAULT 'bommel_van_dam',

    -- Original curator input
    curator_brief JSONB NOT NULL,

    -- Processed data from each stage
    enriched_query JSONB,           -- Stage 1: Theme refinement output
    discovered_artists JSONB,       -- Stage 2: Artist discovery output
    discovered_artworks JSONB,      -- Stage 3: Artwork discovery output
    final_proposals JSONB,          -- Final exhibition proposals

    -- Workflow status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'stage1_processing', 'stage1_review',
        'stage2_processing', 'stage2_review',
        'stage3_processing', 'stage3_review',
        'complete', 'error', 'cancelled'
    )),
    current_stage INTEGER DEFAULT 1 CHECK (current_stage BETWEEN 1 AND 3),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),

    -- Human review data
    stage1_approved BOOLEAN DEFAULT NULL,
    stage1_feedback TEXT,
    stage2_approved BOOLEAN DEFAULT NULL,
    stage2_feedback TEXT,
    stage3_approved BOOLEAN DEFAULT NULL,
    stage3_feedback TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Indexes for curator_sessions
CREATE INDEX idx_curator_sessions_status ON curator_sessions(status);
CREATE INDEX idx_curator_sessions_stage ON curator_sessions(current_stage);
CREATE INDEX idx_curator_sessions_institution ON curator_sessions(institution_id);
CREATE INDEX idx_curator_sessions_created ON curator_sessions(created_at DESC);
CREATE INDEX idx_curator_sessions_curator ON curator_sessions(curator_name);

-- ============================================================================
-- KNOWLEDGE BASE TABLES
-- ============================================================================

-- Search patterns and concept mappings
CREATE TABLE search_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Concept information
    concept VARCHAR(255) NOT NULL,
    concept_type VARCHAR(50) CHECK (concept_type IN (
        'theme', 'technique', 'movement', 'style', 'period', 'subject'
    )),

    -- Authority mappings
    getty_aat_uri VARCHAR(500),
    getty_aat_id VARCHAR(50),
    wikidata_uri VARCHAR(500),
    wikidata_id VARCHAR(50),

    -- SPARQL queries for reuse
    sparql_pattern TEXT,
    sparql_endpoint VARCHAR(100),

    -- Semantic embeddings for similarity search
    embedding vector(1536),  -- OpenAI embedding dimension

    -- Performance metrics
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',

    -- Constraints
    UNIQUE(concept, concept_type)
);

-- Indexes for search_patterns
CREATE INDEX idx_patterns_concept ON search_patterns(concept);
CREATE INDEX idx_patterns_type ON search_patterns(concept_type);
CREATE INDEX idx_patterns_getty_id ON search_patterns(getty_aat_id);
CREATE INDEX idx_patterns_wikidata_id ON search_patterns(wikidata_id);
CREATE INDEX idx_patterns_embedding ON search_patterns USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_patterns_confidence ON search_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_usage ON search_patterns(usage_count DESC);

-- ============================================================================
-- ARTWORK AND ARTIST CACHE
-- ============================================================================

-- Artwork cache for discovered artworks
CREATE TABLE artwork_cache (
    uri VARCHAR(500) PRIMARY KEY,

    -- Basic information
    title VARCHAR(500) NOT NULL,
    artist_name VARCHAR(255),
    artist_uri VARCHAR(500),

    -- Temporal information
    date_created VARCHAR(100),  -- Flexible format for various date types
    period VARCHAR(100),

    -- Physical information
    medium VARCHAR(255),
    dimensions JSONB,  -- Flexible structure for various measurement types

    -- Location and availability
    current_location VARCHAR(255),
    institution_name VARCHAR(255),
    institution_uri VARCHAR(500),
    loan_available BOOLEAN,
    loan_conditions TEXT,

    -- Valuation
    insurance_value DECIMAL(15,2),
    insurance_currency VARCHAR(3) DEFAULT 'EUR',

    -- Rich data
    data JSONB NOT NULL,  -- Full Linked Art or source data
    embedding vector(1536),  -- For semantic similarity

    -- Source tracking
    source VARCHAR(100) NOT NULL CHECK (source IN (
        'yale_lux', 'rkd', 'getty', 'wikidata', 'europeana', 'other'
    )),
    source_url VARCHAR(1000),

    -- IIIF integration
    iiif_manifest VARCHAR(1000),
    thumbnail_url VARCHAR(1000),

    -- Quality metrics
    completeness_score FLOAT DEFAULT 0.0 CHECK (completeness_score BETWEEN 0 AND 1),
    verification_status VARCHAR(20) DEFAULT 'unverified' CHECK (verification_status IN (
        'unverified', 'verified', 'disputed', 'outdated'
    )),

    -- Cache management
    last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fetch_count INTEGER DEFAULT 1,
    cache_expires TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);

-- Indexes for artwork_cache
CREATE INDEX idx_artwork_title ON artwork_cache(title);
CREATE INDEX idx_artwork_artist ON artwork_cache(artist_name);
CREATE INDEX idx_artwork_institution ON artwork_cache(institution_name);
CREATE INDEX idx_artwork_source ON artwork_cache(source);
CREATE INDEX idx_artwork_embedding ON artwork_cache USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_artwork_loan ON artwork_cache(loan_available) WHERE loan_available = true;
CREATE INDEX idx_artwork_completeness ON artwork_cache(completeness_score DESC);
CREATE INDEX idx_artwork_expires ON artwork_cache(cache_expires);

-- Artist information cache
CREATE TABLE artist_cache (
    uri VARCHAR(500) PRIMARY KEY,

    -- Basic information
    name VARCHAR(255) NOT NULL,
    birth_year INTEGER,
    death_year INTEGER,
    nationality VARCHAR(100),

    -- Professional information
    movements JSONB,  -- Array of art movements
    techniques JSONB, -- Array of techniques/media
    themes JSONB,     -- Array of thematic focuses

    -- Authority records
    getty_ulan_uri VARCHAR(500),
    getty_ulan_id VARCHAR(50),
    wikidata_uri VARCHAR(500),
    wikidata_id VARCHAR(50),

    -- Rich biographical data
    biography_short TEXT,
    biography_long TEXT,
    data JSONB NOT NULL,  -- Full source data

    -- Connections
    influenced_by JSONB,  -- Array of artist URIs
    influenced JSONB,     -- Array of artist URIs
    associated_with JSONB, -- Contemporary artists

    -- Metrics
    importance_score FLOAT DEFAULT 0.0,
    artwork_count INTEGER DEFAULT 0,
    exhibition_count INTEGER DEFAULT 0,

    -- Source and cache info
    source VARCHAR(100) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cache_expires TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

-- Indexes for artist_cache
CREATE INDEX idx_artist_name ON artist_cache(name);
CREATE INDEX idx_artist_nationality ON artist_cache(nationality);
CREATE INDEX idx_artist_birth_year ON artist_cache(birth_year);
CREATE INDEX idx_artist_getty_id ON artist_cache(getty_ulan_id);
CREATE INDEX idx_artist_wikidata_id ON artist_cache(wikidata_id);
CREATE INDEX idx_artist_importance ON artist_cache(importance_score DESC);

-- ============================================================================
-- EXHIBITION PROPOSALS
-- ============================================================================

-- Final exhibition proposals
CREATE TABLE exhibition_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES curator_sessions(id) ON DELETE CASCADE,

    -- Exhibition details
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    narrative TEXT NOT NULL,
    curatorial_statement TEXT NOT NULL,

    -- Content structure
    artworks JSONB NOT NULL,  -- Array of selected artworks with metadata
    themes JSONB NOT NULL,    -- Array of thematic sections
    visitor_journey JSONB,   -- Structured visitor experience

    -- Practical considerations
    space_requirements JSONB,  -- Physical space needs
    budget_estimate DECIMAL(12,2),
    insurance_estimate DECIMAL(12,2),
    duration_weeks INTEGER,

    -- Feasibility analysis
    feasibility_score FLOAT CHECK (feasibility_score BETWEEN 0 AND 1),
    feasibility_notes TEXT,
    risk_assessment JSONB,

    -- Approval workflow
    curator_approved BOOLEAN DEFAULT NULL,
    director_approved BOOLEAN DEFAULT NULL,
    approval_notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    proposal_version INTEGER DEFAULT 1
);

-- Indexes for exhibition_proposals
CREATE INDEX idx_proposals_session ON exhibition_proposals(session_id);
CREATE INDEX idx_proposals_feasibility ON exhibition_proposals(feasibility_score DESC);
CREATE INDEX idx_proposals_created ON exhibition_proposals(created_at DESC);
CREATE INDEX idx_proposals_approved ON exhibition_proposals(curator_approved, director_approved);

-- ============================================================================
-- SYSTEM TABLES
-- ============================================================================

-- API usage tracking and rate limiting
CREATE TABLE api_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Request details
    api_service VARCHAR(50) NOT NULL CHECK (api_service IN (
        'wikipedia', 'wikidata', 'getty', 'yale_lux', 'brave_search'
    )),
    endpoint VARCHAR(255),
    request_method VARCHAR(10),

    -- Request/response info
    query_params JSONB,
    response_status INTEGER,
    response_size INTEGER,
    response_time_ms INTEGER,

    -- Rate limiting
    session_id UUID,
    user_ip INET,

    -- Error tracking
    error_message TEXT,
    retry_attempt INTEGER DEFAULT 0,

    -- Timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for api_usage_log
CREATE INDEX idx_api_usage_service ON api_usage_log(api_service);
CREATE INDEX idx_api_usage_timestamp ON api_usage_log(timestamp DESC);
CREATE INDEX idx_api_usage_session ON api_usage_log(session_id);
CREATE INDEX idx_api_usage_status ON api_usage_log(response_status);

-- System configuration
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Insert default configuration
INSERT INTO system_config (key, value, description) VALUES
('max_concurrent_sessions', '10', 'Maximum concurrent curator sessions'),
('session_timeout_minutes', '60', 'Session timeout in minutes'),
('cache_ttl_hours', '24', 'Default cache TTL in hours'),
('api_rate_limits', '{"wikipedia": 10, "wikidata": 5, "getty": 10, "yale_lux": 5, "brave_search": 1}', 'API rate limits per second'),
('embedding_model', '"text-embedding-ada-002"', 'OpenAI embedding model'),
('max_artworks_per_exhibition', '100', 'Maximum artworks per exhibition proposal');

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active sessions with progress
CREATE VIEW active_sessions AS
SELECT
    id,
    curator_name,
    status,
    current_stage,
    progress,
    created_at,
    updated_at,
    CASE
        WHEN status = 'complete' THEN completed_at
        WHEN status = 'error' THEN updated_at
        ELSE NULL
    END as finished_at
FROM curator_sessions
WHERE status NOT IN ('complete', 'cancelled', 'error')
ORDER BY created_at DESC;

-- Exhibition readiness summary
CREATE VIEW exhibition_readiness AS
SELECT
    cs.id as session_id,
    cs.curator_name,
    cs.status,
    ep.title as exhibition_title,
    ep.feasibility_score,
    COUNT(jsonb_array_elements(ep.artworks)) as artwork_count,
    ep.budget_estimate,
    ep.insurance_estimate,
    CASE
        WHEN ep.curator_approved = true AND ep.director_approved = true THEN 'approved'
        WHEN ep.curator_approved = false OR ep.director_approved = false THEN 'rejected'
        ELSE 'pending_approval'
    END as approval_status
FROM curator_sessions cs
LEFT JOIN exhibition_proposals ep ON cs.id = ep.session_id
WHERE cs.status = 'complete'
ORDER BY ep.feasibility_score DESC NULLS LAST;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers
CREATE TRIGGER update_curator_sessions_timestamp
    BEFORE UPDATE ON curator_sessions
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_exhibition_proposals_timestamp
    BEFORE UPDATE ON exhibition_proposals
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM artwork_cache WHERE cache_expires < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    DELETE FROM artist_cache WHERE cache_expires < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert sample Getty AAT concepts for testing
INSERT INTO search_patterns (concept, concept_type, getty_aat_uri, getty_aat_id, confidence_score) VALUES
('impressionism', 'movement', 'http://vocab.getty.edu/aat/300021503', '300021503', 0.95),
('chiaroscuro', 'technique', 'http://vocab.getty.edu/aat/300056168', '300056168', 0.90),
('portrait', 'subject', 'http://vocab.getty.edu/aat/300015637', '300015637', 0.85),
('landscape', 'subject', 'http://vocab.getty.edu/aat/300015636', '300015636', 0.85),
('oil painting', 'technique', 'http://vocab.getty.edu/aat/300178684', '300178684', 0.90);

-- Performance optimization
ANALYZE;

-- Final comment
COMMENT ON SCHEMA public IS 'AI Curator Assistant Database - 3-Stage Agent Workflow with Human-in-the-Loop Validation';

-- Show table sizes for monitoring
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY schemaname, tablename;