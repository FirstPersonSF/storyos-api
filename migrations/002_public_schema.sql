-- StoryOS Prototype - Public Schema Migration
-- Migration 002: Move tables to public schema for REST API access

-- Drop storyos schema tables if they exist
DROP SCHEMA IF EXISTS storyos CASCADE;

-- Set search path to public
SET search_path TO public;

-- ============================================================================
-- 1. UNIFIED NARRATIVE FRAMEWORK (UNF)
-- ============================================================================

-- UNF Layers (Category, Vision, Messaging, etc.)
CREATE TABLE IF NOT EXISTS public.unf_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- UNF Elements (Problem, Vision Statement, Key Messages, etc.)
CREATE TABLE IF NOT EXISTS public.unf_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES public.unf_layers(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    content TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'superseded', 'archived')),
    prev_element_id UUID REFERENCES public.unf_elements(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_unf_elements_layer ON public.unf_elements(layer_id);
CREATE INDEX IF NOT EXISTS idx_unf_elements_status ON public.unf_elements(status);
CREATE INDEX IF NOT EXISTS idx_unf_elements_prev ON public.unf_elements(prev_element_id);

-- ============================================================================
-- 2. BRAND VOICE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.brand_voices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    traits JSONB DEFAULT '[]',
    tone_rules JSONB DEFAULT '{}',
    style_guardrails JSONB DEFAULT '{}',
    lexicon JSONB DEFAULT '{}',
    readability_range VARCHAR(50),
    parent_voice_id UUID REFERENCES public.brand_voices(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'archived')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brand_voices_parent ON public.brand_voices(parent_voice_id);
CREATE INDEX IF NOT EXISTS idx_brand_voices_status ON public.brand_voices(status);

-- ============================================================================
-- 3. STORY MODELS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.story_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sections JSONB DEFAULT '[]',
    constraints JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 4. DELIVERABLE TEMPLATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.deliverable_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    story_model_id UUID REFERENCES public.story_models(id) ON DELETE RESTRICT,
    default_voice_id UUID REFERENCES public.brand_voices(id) ON DELETE RESTRICT,
    validation_rules JSONB DEFAULT '[]',
    instance_fields JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'archived')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_templates_model ON public.deliverable_templates(story_model_id);
CREATE INDEX IF NOT EXISTS idx_templates_voice ON public.deliverable_templates(default_voice_id);
CREATE INDEX IF NOT EXISTS idx_templates_status ON public.deliverable_templates(status);

-- Template Section Bindings
CREATE TABLE IF NOT EXISTS public.template_section_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES public.deliverable_templates(id) ON DELETE CASCADE,
    section_name VARCHAR(100) NOT NULL,
    section_order INTEGER,
    element_ids UUID[] DEFAULT '{}',
    binding_rules JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bindings_template ON public.template_section_bindings(template_id);

-- ============================================================================
-- 5. DELIVERABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200),
    template_id UUID REFERENCES public.deliverable_templates(id) ON DELETE RESTRICT,
    template_version VARCHAR(20),
    story_model_id UUID REFERENCES public.story_models(id) ON DELETE RESTRICT,
    voice_id UUID REFERENCES public.brand_voices(id) ON DELETE RESTRICT,
    voice_version VARCHAR(20),
    instance_data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'published')),
    element_versions JSONB DEFAULT '{}',
    rendered_content JSONB DEFAULT '{}',
    validation_log JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deliverables_template ON public.deliverables(template_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_voice ON public.deliverables(voice_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON public.deliverables(status);

-- ============================================================================
-- 6. ELEMENT DEPENDENCIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.element_dependencies (
    element_id UUID REFERENCES public.unf_elements(id) ON DELETE CASCADE,
    template_id UUID REFERENCES public.deliverable_templates(id) ON DELETE CASCADE,
    deliverable_id UUID REFERENCES public.deliverables(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (element_id, template_id, deliverable_id)
);

CREATE INDEX IF NOT EXISTS idx_deps_element ON public.element_dependencies(element_id);
CREATE INDEX IF NOT EXISTS idx_deps_template ON public.element_dependencies(template_id);
CREATE INDEX IF NOT EXISTS idx_deps_deliverable ON public.element_dependencies(deliverable_id);

-- ============================================================================
-- 7. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS update_unf_layers_updated_at ON public.unf_layers;
CREATE TRIGGER update_unf_layers_updated_at
    BEFORE UPDATE ON public.unf_layers
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_unf_elements_updated_at ON public.unf_elements;
CREATE TRIGGER update_unf_elements_updated_at
    BEFORE UPDATE ON public.unf_elements
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_brand_voices_updated_at ON public.brand_voices;
CREATE TRIGGER update_brand_voices_updated_at
    BEFORE UPDATE ON public.brand_voices
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_story_models_updated_at ON public.story_models;
CREATE TRIGGER update_story_models_updated_at
    BEFORE UPDATE ON public.story_models
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_deliverable_templates_updated_at ON public.deliverable_templates;
CREATE TRIGGER update_deliverable_templates_updated_at
    BEFORE UPDATE ON public.deliverable_templates
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_deliverables_updated_at ON public.deliverables;
CREATE TRIGGER update_deliverables_updated_at
    BEFORE UPDATE ON public.deliverables
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- COMPLETE
-- ============================================================================

COMMENT ON TABLE public.unf_layers IS 'StoryOS - UNF Layers';
COMMENT ON TABLE public.unf_elements IS 'StoryOS - UNF Elements with versioning';
COMMENT ON TABLE public.brand_voices IS 'StoryOS - Brand Voice configurations';
COMMENT ON TABLE public.story_models IS 'StoryOS - Story Model definitions';
COMMENT ON TABLE public.deliverable_templates IS 'StoryOS - Deliverable Templates';
COMMENT ON TABLE public.template_section_bindings IS 'StoryOS - Section bindings';
COMMENT ON TABLE public.deliverables IS 'StoryOS - Generated deliverables';
COMMENT ON TABLE public.element_dependencies IS 'StoryOS - Dependency tracking';
