-- LingoVision Database Schema v2 (LingoCard format)
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor > New Query)
--
-- If upgrading from v1, run the drop commands first:
-- DROP POLICY IF EXISTS "Public read cards" ON cards;
-- DROP POLICY IF EXISTS "Public read units" ON units;
-- DROP TABLE IF EXISTS cards;
-- DROP TABLE IF EXISTS units;

-- Units table
CREATE TABLE units (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  language TEXT NOT NULL DEFAULT 'Spanish',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Cards table (matches frontend LingoCard type)
CREATE TABLE cards (
  id TEXT NOT NULL,
  unit_id UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('immersive', 'drill', 'concept')),
  visual_url TEXT NOT NULL,
  audio_url TEXT NOT NULL DEFAULT '',
  target_text TEXT NOT NULL,
  english_bridge TEXT,
  grammar_note TEXT,
  sentence TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (unit_id, id),
  UNIQUE (unit_id, position)
);

CREATE INDEX idx_cards_unit_id ON cards(unit_id);

-- Allow public read access (no auth needed per PRD)
ALTER TABLE units ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read units" ON units FOR SELECT USING (true);
CREATE POLICY "Public read cards" ON cards FOR SELECT USING (true);
