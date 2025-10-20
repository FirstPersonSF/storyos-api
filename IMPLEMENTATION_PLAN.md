# StoryOS Prototype - Implementation Plan

**Version:** 1.0
**Date:** 2025-10-19

---

## Executive Summary

This prototype validates the core StoryOS architecture: content (UNF Elements), structure (Story Models), style (Brand Voice), and assembly (Deliverable Templates → Deliverables). It builds on patterns from your 1p_knowledgebase project and aligns with the existing Neo4j v1 prototype.

**Core Flow:**
1. Create Brand Manifesto (using PAS Story Model)
2. Create Press Release (using Inverted Pyramid Model)
3. Update UNF Element
4. See impact alerts on affected Deliverables

---

## Architecture Alignment

### Tech Stack (matching 1p_knowledgebase)
```
- Python 3.10+
- FastAPI (API layer)
- PostgreSQL via Supabase (content storage)
- Pydantic (data models)
- Neo4j (later integration - relationships & impact tracking)
- Streamlit or HTML/JS (simple UI)
```

### Data Split Strategy

**PostgreSQL** (Source of Truth for Content):
- Element content, versions, metadata
- Brand Voice configurations
- Story Model definitions
- Template structure and bindings
- Deliverable outputs and instance fields
- Status, timestamps, provenance

**Neo4j** (Relationship & Impact Graph - Phase 2):
- Element → Template bindings
- Template → Deliverable instances
- Element version lineage chains
- Layer → Element hierarchy
- Impact propagation ("What uses this?")
- Dependency tracking

**Rationale:** PostgreSQL handles transactional content, Neo4j excels at graph queries.

---

## Terminology Reconciliation

**Documentation → Neo4j v1 → This Prototype**

| Documentation | Neo4j v1 | This Prototype |
|---------------|----------|----------------|
| UNF Layer | StoryLayer | `unf_layers` table |
| UNF Element | StoryFacet | `unf_elements` table |
| Story Model | StoryModel | `story_models` table |
| Deliverable Template | DeliverableTemplate | `deliverable_templates` table |
| Section Binding | REQUIRES_FACET relationship | `template_section_bindings` table |
| Brand Voice | (not in Neo4j v1) | `brand_voices` table |
| Deliverable | (not in Neo4j v1) | `deliverables` table |

---

## Database Schema (PostgreSQL)

### Core Tables

```sql
-- Unified Narrative Framework
CREATE TABLE unf_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE unf_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES unf_layers(id),
    name VARCHAR(200) NOT NULL,
    content TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft', -- draft, approved, superseded
    prev_element_id UUID REFERENCES unf_elements(id), -- version chain
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Brand Voice
CREATE TABLE brand_voices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    traits JSONB DEFAULT '[]', -- ["confident", "precise"]
    tone_rules JSONB DEFAULT '{}',
    lexicon JSONB DEFAULT '{}', -- {required: [], banned: []}
    parent_voice_id UUID REFERENCES brand_voices(id),
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Story Models
CREATE TABLE story_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sections JSONB DEFAULT '[]', -- [{name, intent, order}]
    constraints JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Deliverable Templates
CREATE TABLE deliverable_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    story_model_id UUID REFERENCES story_models(id),
    default_voice_id UUID REFERENCES brand_voices(id),
    validation_rules JSONB DEFAULT '[]',
    instance_fields JSONB DEFAULT '[]', -- [{name, type, required}]
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Template Section Bindings
CREATE TABLE template_section_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES deliverable_templates(id),
    section_name VARCHAR(100) NOT NULL,
    section_order INTEGER,
    element_ids UUID[] DEFAULT '{}', -- array of UNF element IDs
    binding_rules JSONB DEFAULT '{}', -- {quantity, transformation, etc.}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Deliverables
CREATE TABLE deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES deliverable_templates(id),
    template_version VARCHAR(20),
    voice_id UUID REFERENCES brand_voices(id),
    voice_version VARCHAR(20),
    instance_data JSONB DEFAULT '{}', -- who, what, when, where, why
    status VARCHAR(20) DEFAULT 'draft', -- draft, review, approved, published
    element_versions JSONB DEFAULT '{}', -- {element_id: version} snapshot
    rendered_content JSONB DEFAULT '{}', -- {section_name: rendered_text}
    validation_log JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Impact Tracking (for "Update Available" alerts)
CREATE TABLE element_dependencies (
    element_id UUID REFERENCES unf_elements(id),
    template_id UUID REFERENCES deliverable_templates(id),
    deliverable_id UUID REFERENCES deliverables(id),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (element_id, template_id, deliverable_id)
);
```

---

## Service Architecture

### Directory Structure
```
storyos_prototype/
├── models/              # Pydantic models
│   ├── unf.py          # Layer, Element
│   ├── voice.py        # BrandVoice
│   ├── story_models.py # StoryModel
│   ├── templates.py    # DeliverableTemplate, SectionBinding
│   └── deliverables.py # Deliverable, InstanceField
├── services/            # Business logic
│   ├── unf_service.py
│   ├── voice_service.py
│   ├── template_service.py
│   ├── deliverable_service.py
│   └── relationship_service.py  # Abstract interface
├── storage/             # Database operations
│   ├── postgres_storage.py
│   └── neo4j_storage.py (future)
├── api/                 # FastAPI routes
│   ├── app.py
│   ├── routes/
│   │   ├── unf.py
│   │   ├── templates.py
│   │   └── deliverables.py
│   └── dependencies.py
├── scripts/             # Utilities
│   ├── load_dummy_data.py
│   └── migrate_db.py
├── tests/
├── .env
├── requirements.txt
└── README.md
```

### Service Layer Design

**RelationshipService (Abstract Interface)**
```python
class RelationshipService(ABC):
    """Abstract interface for relationship/dependency tracking"""

    @abstractmethod
    def get_element_dependencies(self, element_id: str) -> List[str]:
        """Get all Templates/Deliverables using this Element"""
        pass

    @abstractmethod
    def get_impact_chain(self, element_id: str) -> Dict:
        """Get full impact tree when Element changes"""
        pass

    @abstractmethod
    def track_element_usage(self, element_id: str, deliverable_id: str):
        """Record that a Deliverable uses an Element"""
        pass
```

**PostgresRelationshipService (Prototype Implementation)**
- Uses joins on `element_dependencies` table
- Simple but functional for prototype

**Neo4jRelationshipService (Future)**
- Uses Cypher queries
- Swaps in seamlessly via dependency injection

---

## Core Workflow Implementation

### User Story 1: Create Brand Manifesto

**Request:**
```json
POST /api/deliverables
{
  "template_id": "<brand-manifesto-template-id>",
  "voice_id": "<corporate-voice-id>"
}
```

**Process:**
1. Fetch Template (PAS Story Model)
2. Fetch Section Bindings (Problem → category-problem, Solve → vision-statement, etc.)
3. Fetch latest approved Element versions
4. Validate: Problem section ≤120 words, Solve includes Vision Statement
5. Apply Brand Voice filter (check lexicon, banned terms)
6. Create Deliverable record with version locks
7. Track dependencies in `element_dependencies`
8. Return Deliverable with provenance

### User Story 2: Create Press Release

**Request:**
```json
POST /api/deliverables
{
  "template_id": "<press-release-template-id>",
  "voice_id": "<corporate-voice-id>",
  "instance_data": {
    "who": "Hexagon AB",
    "what": "Announces HxGN Precision One",
    "when": "2025-10-17",
    "where": "Stockholm, Sweden",
    "why": "To help manufacturers...",
    "quote1_speaker": "Maria Olsson",
    "quote1_title": "CTO, Hexagon AB",
    "quote2_speaker": "Alex Grant",
    "quote2_title": "Plant Director, Orion Manufacturing"
  }
}
```

**Process:**
1. Fetch Template (Inverted Pyramid Model)
2. Validate instance fields (who, what, when, where, why required)
3. Fetch section bindings + Elements
4. Validate: Headline ≤10 words, Lede has 5Ws, Boilerplate = latest approved
5. Apply Brand Voice
6. Create Deliverable
7. Return with full provenance

### User Story 3: Update Element & See Impact

**Request:**
```json
PATCH /api/unf/elements/<element-id>
{
  "content": "Updated vision statement text...",
  "status": "approved"
}
```

**Process:**
1. Create new Element version (prev_element_id → old version)
2. Mark old version as 'superseded'
3. Query `element_dependencies` for affected Deliverables
4. Return impact report:
```json
{
  "element_id": "...",
  "new_version": "1.1",
  "affected_deliverables": [
    {"id": "...", "name": "Brand Manifesto", "status": "update_available"},
    {"id": "...", "name": "Press Release #1", "status": "update_available"}
  ]
}
```

**User can then:**
- View Deliverable (shows "Update Available" banner)
- Click "Refresh" → recreates Deliverable with new Element version
- Click "Defer" → keeps old version, marks as "using older data"

---

## Dummy Data Loading

**Script:** `scripts/load_dummy_data.py`

**Loads:**
1. UNF Layers (Category, Vision, Messaging)
2. UNF Elements from `Documentation/StoryOS - Prototype DummyData.md`
3. Brand Voices (Corporate v1.0, Product v1.0)
4. Story Models (PAS, Inverted Pyramid)
5. Deliverable Templates (Brand Manifesto, Press Release)
6. Section Bindings

---

## MVP Feature Set

**Phase 1: Core Prototype**
- ✅ PostgreSQL schema + migrations
- ✅ Pydantic models
- ✅ Service layer (UNF, Voice, Templates, Deliverables)
- ✅ Basic relationship tracking (PostgreSQL)
- ✅ FastAPI routes (CRUD for all components)
- ✅ Load dummy data
- ✅ Test core workflow

**Out of Scope (for now):**
- ❌ Full Neo4j integration (design interface, implement later)
- ❌ Advanced Brand Voice rendering (LLM-based tone transformation)
- ❌ Complex validation engine (keep simple rule-based for prototype)
- ❌ Production-grade UI (use Streamlit or basic HTML forms)
- ❌ Authentication/permissions (add later)

**Phase 2: Neo4j Integration (after prototype validation)**
- Implement Neo4jRelationshipService
- Migrate relationship data to graph
- Advanced impact analysis queries
- Visualize dependency graphs

---

## Testing Strategy

**Test Sequences from Documentation:**

1. ✅ Generate Deliverables using Corporate Voice v1.0
2. ✅ Switch Press Release to Product Voice v1.0
3. ✅ Update Boilerplate to v1.1 → see "Update Available"
4. ✅ Edit Vision Statement to v1.1 (Draft) → see "Update Pending"
5. ✅ Swap Story Model in Manifesto → revalidate
6. ✅ End-to-end provenance check

---

## Implementation Timeline

**Phase 1: Foundation (Days 1-2)**
- Database schema + migrations
- Pydantic models
- Basic storage layer

**Phase 2: Services (Days 3-4)**
- UNF, Voice, Template, Deliverable services
- Relationship service (PostgreSQL implementation)
- Validation logic

**Phase 3: API & Data (Day 5)**
- FastAPI routes
- Load dummy data script
- Integration testing

**Phase 4: Testing & Polish (Day 6)**
- Run all test sequences
- Document findings
- Prepare demo

---

## Success Criteria

**The prototype succeeds if:**

1. ✅ Elements can be reused across Deliverables with version tracking
2. ✅ Brand Voice applies without modifying source Elements
3. ✅ Story Models and Templates structure narratives consistently
4. ✅ Deliverables record full provenance (Element versions, Template version, Voice version)
5. ✅ "Update Available" alerts trigger correctly when Elements change
6. ✅ System is ready for Neo4j integration (clean service interface)

---

## Next Steps

**Upon approval:**

1. Create `.env` with Supabase credentials
2. Set up PostgreSQL database
3. Generate schema migrations
4. Implement Pydantic models
5. Build service layer
6. Create FastAPI app
7. Load dummy data
8. Test core workflow

**Questions?** Ready to proceed?
