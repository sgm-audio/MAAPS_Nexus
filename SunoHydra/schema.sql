-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS suno_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id TEXT UNIQUE NOT NULL,
    title TEXT,
    play_count INT,
    upvote_count INT,
    raw_tags JSONB, -- Array of strings from Suno
    human_prompt TEXT, -- The LLM generated description
    virality_score INT, -- Calculated score
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by track_id (upsert performance)
CREATE INDEX IF NOT EXISTS idx_suno_tracks_track_id ON suno_tracks(track_id);

-- Index for querying high-status tracks
CREATE INDEX IF NOT EXISTS idx_suno_tracks_play_count ON suno_tracks(play_count DESC);
