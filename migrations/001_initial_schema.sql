-- StoryOS Prototype - Initial Database Schema
-- Migration 001: Core tables for UNF, Brand Voice, Story Models, Templates, and Deliverables

-- Create schema
CREATE SCHEMA IF NOT EXISTS storyos;

-- Set search path
SET search_path TO storyos, public;

-- ============================================================================
-- 1. UNIFIED NARRATIVE FRAMEWORK (UNF)
-- ============================================================================

-- UNF Layers (Category, Vision, Messaging, etc.)
CREATE TABLE storyos.unf_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- UNF Elements (Problem, Vision Statement, Key Messages, etc.)
CREATE TABLE storyos.unf_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES storyos.unf_layers(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    content TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'superseded', 'archived')),
    prev_element_id UUID REFERENCES storyos.unf_elements(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_unf_elements_layer ON storyos.unf_elements(layer_id);
CREATE INDEX idx_unf_elements_status ON storyos.unf_elements(status);
CREATE INDEX idx_unf_elements_prev ON storyos.unf_elements(prev_element_id);

-- ============================================================================
-- 2. BRAND VOICE
-- ============================================================================

CREATE TABLE storyos.brand_voices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    traits JSONB DEFAULT '[]', -- ["confident", "precise", "grounded"]
    tone_rules JSONB DEFAULT '{}', -- {formality: "medium-high", pov: "third-person", ...}
    style_guardrails JSONB DEFAULT '{}', -- {do: [...], dont: [...]}
    lexicon JSONB DEFAULT '{}', -- {required: ["phrase1"], banned: ["term1"]}
    readability_range VARCHAR(50),
    parent_voice_id UUID REFERENCES storyos.brand_voices(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'archived')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_brand_voices_parent ON storyos.brand_voices(parent_voice_id);
CREATE INDEX idx_brand_voices_status ON storyos.brand_voices(status);

-- ============================================================================
-- 3. STORY MODELS
-- ============================================================================

CREATE TABLE storyos.story_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sections JSONB DEFAULT '[]', -- [{name, intent, order}]
    constraints JSONB DEFAULT '{}', -- {section_name: {max_words: 120, ...}}
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 4. DELIVERABLE TEMPLATES
-- ============================================================================

CREATE TABLE storyos.deliverable_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    story_model_id UUID REFERENCES storyos.story_models(id) ON DELETE RESTRICT,
    default_voice_id UUID REFERENCES storyos.brand_voices(id) ON DELETE RESTRICT,
    validation_rules JSONB DEFAULT '[]', -- [{rule_type, params}]
    instance_fields JSONB DEFAULT '[]', -- [{name, type, required, description}]
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'archived')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_templates_model ON storyos.deliverable_templates(story_model_id);
CREATE INDEX idx_templates_voice ON storyos.deliverable_templates(default_voice_id);
CREATE INDEX idx_templates_status ON storyos.deliverable_templates(status);

-- Template Section Bindings (maps Template sections to UNF Elements)
CREATE TABLE storyos.template_section_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES storyos.deliverable_templates(id) ON DELETE CASCADE,
    section_name VARCHAR(100) NOT NULL,
    section_order INTEGER,
    element_ids UUID[] DEFAULT '{}', -- array of UNF element IDs
    binding_rules JSONB DEFAULT '{}', -- {quantity: 2, transformation: "excerpt", ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bindings_template ON storyos.template_section_bindings(template_id);

-- ============================================================================
-- 5. DELIVERABLES
-- ============================================================================

CREATE TABLE storyos.deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200),
    template_id UUID REFERENCES storyos.deliverable_templates(id) ON DELETE RESTRICT,
    template_version VARCHAR(20),
    story_model_id UUID REFERENCES storyos.story_models(id) ON DELETE RESTRICT,
    voice_id UUID REFERENCES storyos.brand_voices(id) ON DELETE RESTRICT,
    voice_version VARCHAR(20),
    instance_data JSONB DEFAULT '{}', -- {who, what, when, where, why, ...}
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'published')),
    element_versions JSONB DEFAULT '{}', -- {element_id: version} snapshot for reproducibility
    rendered_content JSONB DEFAULT '{}', -- {section_name: rendered_text}
    validation_log JSONB DEFAULT '[]', -- [{timestamp, rule, passed, message}]
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deliverables_template ON storyos.deliverables(template_id);
CREATE INDEX idx_deliverables_voice ON storyos.deliverables(voice_id);
CREATE INDEX idx_deliverables_status ON storyos.deliverables(status);

-- ============================================================================
-- 6. ELEMENT DEPENDENCIES (Impact Tracking)
-- ============================================================================

-- Tracks which Templates and Deliverables use which Elements
-- Used for "Update Available" alerts
CREATE TABLE storyos.element_dependencies (
    element_id UUID REFERENCES storyos.unf_elements(id) ON DELETE CASCADE,
    template_id UUID REFERENCES storyos.deliverable_templates(id) ON DELETE CASCADE,
    deliverable_id UUID REFERENCES storyos.deliverables(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (element_id, template_id, deliverable_id)
);

CREATE INDEX idx_deps_element ON storyos.element_dependencies(element_id);
CREATE INDEX idx_deps_template ON storyos.element_dependencies(template_id);
CREATE INDEX idx_deps_deliverable ON storyos.element_dependencies(deliverable_id);

-- ============================================================================
-- 7. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION storyos.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_unf_layers_updated_at
    BEFORE UPDATE ON storyos.unf_layers
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

CREATE TRIGGER update_unf_elements_updated_at
    BEFORE UPDATE ON storyos.unf_elements
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

CREATE TRIGGER update_brand_voices_updated_at
    BEFORE UPDATE ON storyos.brand_voices
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

CREATE TRIGGER update_story_models_updated_at
    BEFORE UPDATE ON storyos.story_models
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

CREATE TRIGGER update_deliverable_templates_updated_at
    BEFORE UPDATE ON storyos.deliverable_templates
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

CREATE TRIGGER update_deliverables_updated_at
    BEFORE UPDATE ON storyos.deliverables
    FOR EACH ROW
    EXECUTE FUNCTION storyos.update_updated_at_column();

-- ============================================================================
-- 8. HELPER VIEWS
-- ============================================================================

-- View: Active (non-superseded) Elements
CREATE VIEW storyos.active_elements AS
SELECT * FROM storyos.unf_elements
WHERE status != 'superseded';

-- View: Latest Element Versions (per name+layer)
CREATE VIEW storyos.latest_elements AS
SELECT DISTINCT ON (layer_id, name) *
FROM storyos.unf_elements
WHERE status = 'approved'
ORDER BY layer_id, name, created_at DESC;

-- View: Deliverables with Update Alerts
CREATE VIEW storyos.deliverables_with_alerts AS
SELECT
    d.id,
    d.name,
    d.status,
    COUNT(DISTINCT ed.element_id) as elements_with_updates,
    ARRAY_AGG(DISTINCT e.name) as updated_element_names
FROM storyos.deliverables d
LEFT JOIN storyos.element_dependencies ed ON d.id = ed.deliverable_id
LEFT JOIN storyos.unf_elements e ON ed.element_id = e.prev_element_id
WHERE e.status = 'approved' -- newer version exists
GROUP BY d.id, d.name, d.status;

-- ============================================================================
-- COMPLETE
-- ============================================================================

COMMENT ON SCHEMA storyos IS 'StoryOS Prototype - Unified Narrative Framework and Deliverable Management';
