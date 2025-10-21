-- Migration 003: Add voice rules and story model strategies for Phase 2

-- Add rules column to brand_voices
ALTER TABLE brand_voices
ADD COLUMN IF NOT EXISTS rules JSONB;

COMMENT ON COLUMN brand_voices.rules IS 'Voice transformation rules (lexicon, terminology, tone)';

-- Add section_strategies column to story_models
ALTER TABLE story_models
ADD COLUMN IF NOT EXISTS section_strategies JSONB;

COMMENT ON COLUMN story_models.section_strategies IS 'Section extraction strategies for content composition';
