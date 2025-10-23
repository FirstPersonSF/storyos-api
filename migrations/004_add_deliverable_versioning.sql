-- Migration 004: Add Deliverable Versioning
-- This migration adds version tracking to deliverables, similar to UNF Elements
-- Now when updating a deliverable (changing story model, voice, or content),
-- a new version is created instead of destructively updating the original

-- Add version and prev_deliverable_id columns
ALTER TABLE public.deliverables
ADD COLUMN version INTEGER DEFAULT 1,
ADD COLUMN prev_deliverable_id UUID REFERENCES public.deliverables(id) ON DELETE SET NULL;

-- Update status constraint to include 'superseded'
ALTER TABLE public.deliverables
DROP CONSTRAINT IF EXISTS deliverables_status_check;

ALTER TABLE public.deliverables
ADD CONSTRAINT deliverables_status_check
CHECK (status IN ('draft', 'review', 'approved', 'published', 'superseded'));

-- Create index for version lookups
CREATE INDEX idx_deliverables_prev_id ON public.deliverables(prev_deliverable_id);
CREATE INDEX idx_deliverables_name_version ON public.deliverables(name, version DESC);

-- Set all existing deliverables to version 1 (they are the initial versions)
UPDATE public.deliverables SET version = 1 WHERE version IS NULL;

-- Make version NOT NULL after setting defaults
ALTER TABLE public.deliverables ALTER COLUMN version SET NOT NULL;

-- Add comment explaining the versioning system
COMMENT ON COLUMN public.deliverables.version IS 'Version number for this deliverable. Increments with each update.';
COMMENT ON COLUMN public.deliverables.prev_deliverable_id IS 'References the previous version of this deliverable. NULL for initial version.';
COMMENT ON COLUMN public.deliverables.status IS 'Status of deliverable. Superseded means a newer version exists.';
