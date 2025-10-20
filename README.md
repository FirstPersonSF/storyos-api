# StoryOS API

Content management system for enterprise storytelling.

## Features

- **UNF (Unified Narrative Framework)** - Manage reusable narrative content (Layers & Elements)
- **Brand Voices** - Define and apply tonal filters
- **Story Models** - Structural templates (PAS, Inverted Pyramid, etc.)
- **Deliverable Templates** - Assemble content using story models
- **Deliverables** - Final outputs with version tracking and impact alerts

## Key Concepts

- **Elements**: Reusable content blocks (e.g., "Vision Statement", "Problem")
- **Version Tracking**: Elements link via `prev_element_id` to track changes
- **Impact Alerts**: Deliverables detect when source Elements are updated
- **Brand Voice**: Applied at render time (non-destructive)

## Tech Stack

- **FastAPI** - Web framework
- **Supabase** - PostgreSQL database (REST API)
- **Pydantic** - Data validation
- **Python 3.13**

## Local Development

```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Run the server
uvicorn main:app --reload

# API docs available at:
# http://localhost:8000/docs
```

## Loading Data

```bash
# Clear all data
python3 scripts/clear_all_data.py

# Load dummy data
python3 scripts/load_dummy_data.py

# Check data
python3 scripts/check_data.py

# Test workflow
python3 scripts/test_workflow.py
```

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### UNF
- `GET /unf/layers` - List layers
- `GET /unf/elements` - List elements
- `POST /unf/elements` - Create element
- `PUT /unf/elements/{id}` - Update element (creates new version)

### Brand Voices
- `GET /voices` - List voices
- `POST /voices` - Create voice
- `GET /voices/{id}` - Get voice

### Story Models
- `GET /story-models` - List story models
- `GET /story-models/{id}` - Get story model

### Templates
- `GET /templates` - List templates
- `GET /templates/{id}` - Get template with bindings
- `POST /templates/{id}/bindings` - Add section binding

### Deliverables
- `GET /deliverables` - List deliverables
- `POST /deliverables` - Create deliverable
- `GET /deliverables/{id}/with-alerts` - Get deliverable with impact alerts
- `POST /deliverables/{id}/validate` - Validate deliverable

## Deployment

Deployed on Railway. Environment variables required:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Database Schema

8 tables in PostgreSQL (Supabase):
- `unf_layers` - UNF layer definitions
- `unf_elements` - Content elements with versioning
- `brand_voices` - Brand voice configurations
- `story_models` - Story structure definitions
- `deliverable_templates` - Template definitions
- `template_section_bindings` - Template-element mappings
- `deliverables` - Generated outputs
- `element_dependencies` - Dependency tracking for alerts

## Architecture

```
FastAPI
  ↓
Services Layer (business logic)
  ↓
Storage Interface (abstract)
  ├── SupabaseStorage (REST API)
  └── PostgresStorage (direct psycopg - future)
```

## Future Enhancements

- Neo4j integration for relationship/impact tracking
- LLM integration for Brand Voice transformation
- Real-time WebSocket updates for alerts
- Frontend UI (React/Vue)
