# Templates, Section Bindings, and Validation

**Document Status**: Reference Documentation
**Created**: 2025-10-23
**Last Updated**: 2025-10-23

---

## Table of Contents

1. [Overview](#overview)
2. [Deliverable Templates Storage](#deliverable-templates-storage)
3. [Section Bindings Storage](#section-bindings-storage)
4. [Validation Rules Storage](#validation-rules-storage)
5. [How Validation Works](#how-validation-works)
6. [Complete Examples](#complete-examples)
7. [Testing Strategy](#testing-strategy)

---

## Overview

StoryOS uses a **three-tier architecture** for creating deliverables:

```
┌────────────────────────────────────────────────────────┐
│  Story Model (defines structure)                       │
│  - Sections (Headline, Lede, Body, etc.)              │
│  - Constraints (max_words, required_elements)          │
└────────────────────────────────────────────────────────┘
                         ↓ referenced by
┌────────────────────────────────────────────────────────┐
│  Deliverable Template (maps structure to content)      │
│  - Section Bindings (which Elements go where)         │
│  - Instance Fields (who, what, when, where, why)      │
│  - Validation Rules (template-level checks)            │
└────────────────────────────────────────────────────────┘
                         ↓ instantiated as
┌────────────────────────────────────────────────────────┐
│  Deliverable (final output)                            │
│  - Rendered Content (assembled text by section)       │
│  - Instance Data (filled-in fields)                   │
│  - Validation Log (results of rule checks)            │
└────────────────────────────────────────────────────────┘
```

---

## Deliverable Templates Storage

### Database Schema

**Table**: `deliverable_templates`

```sql
CREATE TABLE public.deliverable_templates (
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
```

### Pydantic Models

**File**: `models/templates.py`

```python
class InstanceField(BaseModel):
    """Metadata field required by specific Deliverables"""
    name: str                              # e.g., 'who', 'what', 'when'
    field_type: InstanceFieldType          # TEXT, DATE, NUMBER, EMAIL, URL
    required: bool = True
    description: Optional[str] = None      # Help text
    default_value: Optional[str] = None


class ValidationRule(BaseModel):
    """Template-level validation rule"""
    rule_type: str                         # e.g., 'require_boilerplate', 'max_sections'
    params: Dict[str, Any] = {}
    error_message: Optional[str] = None


class DeliverableTemplate(BaseModel):
    """Template database model"""
    id: UUID4
    name: str
    version: str = "1.0"
    story_model_id: UUID4                  # References Story Model
    default_voice_id: UUID4                # References Brand Voice
    validation_rules: List[ValidationRule] = []
    instance_fields: List[InstanceField] = []
    status: TemplateStatus                 # draft, approved, archived
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
```

### Storage Format

Templates are stored with **JSONB** fields for flexibility:

#### validation_rules (JSONB Array)

```json
[
  {
    "rule_type": "max_word_count",
    "params": {
      "section": "Headline",
      "max_words": 10
    },
    "error_message": "Headline must be 10 words or fewer"
  },
  {
    "rule_type": "require_element",
    "params": {
      "section": "Boilerplate",
      "element_name": "Messaging.Boilerplate"
    },
    "error_message": "Boilerplate section must use latest approved Messaging.Boilerplate element"
  },
  {
    "rule_type": "require_five_ws",
    "params": {
      "section": "Lede"
    },
    "error_message": "Lede must contain who, what, when, where, and why"
  }
]
```

#### instance_fields (JSONB Array)

```json
[
  {
    "name": "who",
    "field_type": "text",
    "required": true,
    "description": "Company or organization name",
    "default_value": null
  },
  {
    "name": "what",
    "field_type": "text",
    "required": true,
    "description": "What is being announced",
    "default_value": null
  },
  {
    "name": "when",
    "field_type": "date",
    "required": true,
    "description": "Announcement date",
    "default_value": null
  },
  {
    "name": "quote1_speaker",
    "field_type": "text",
    "required": true,
    "description": "Executive name for Quote 1",
    "default_value": null
  },
  {
    "name": "quote1_title",
    "field_type": "text",
    "required": true,
    "description": "Executive title for Quote 1",
    "default_value": null
  },
  {
    "name": "quote1_content",
    "field_type": "text",
    "required": true,
    "description": "Quote text from executive",
    "default_value": null
  }
]
```

---

## Section Bindings Storage

### Database Schema

**Table**: `template_section_bindings`

```sql
CREATE TABLE public.template_section_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES public.deliverable_templates(id) ON DELETE CASCADE,
    section_name VARCHAR(100) NOT NULL,
    section_order INTEGER,
    element_ids UUID[] DEFAULT '{}',        -- PostgreSQL array of UUIDs
    binding_rules JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields:**
- `section_name`: Name of section in Story Model (e.g., "Headline", "Lede", "Quote 1")
- `section_order`: Display order (1, 2, 3, etc.)
- `element_ids`: Array of UNF Element UUIDs to bind to this section
- `binding_rules`: Optional rules for how to use the elements (JSONB)

### Pydantic Models

**File**: `models/templates.py`

```python
class BindingRule(BaseModel):
    """Rules for how to use Element content in a section"""
    quantity: Optional[int] = None           # Number of Elements to use
    transformation: Optional[str] = None     # e.g., 'excerpt', 'summary', 'full'
    max_length: Optional[int] = None         # Max characters/words
    format: Optional[str] = None             # e.g., 'bullet', 'paragraph', 'quote'


class SectionBinding(BaseModel):
    """Section Binding database model"""
    id: UUID4
    template_id: UUID4
    section_name: str
    section_order: int
    element_ids: List[UUID4] = []
    binding_rules: Optional[BindingRule] = None
    created_at: datetime
```

### Storage Format

Bindings connect **Story Model sections** to **UNF Elements**:

#### Example: Press Release Template Bindings

```python
# Binding 1: Headline
{
    "id": "binding-uuid-1",
    "template_id": "template-press-release-v1-0",
    "section_name": "Headline",
    "section_order": 1,
    "element_ids": ["messaging-key-messages"],  # Array of UUIDs
    "binding_rules": {
        "quantity": 1,
        "transformation": "excerpt",
        "max_length": null,
        "format": "headline"
    }
}

# Binding 2: Lede
{
    "id": "binding-uuid-2",
    "template_id": "template-press-release-v1-0",
    "section_name": "Lede",
    "section_order": 2,
    "element_ids": ["vision-statement"],
    "binding_rules": {
        "quantity": 1,
        "transformation": "full",
        "max_length": null,
        "format": "paragraph"
    }
}

# Binding 3: Key Facts
{
    "id": "binding-uuid-3",
    "template_id": "template-press-release-v1-0",
    "section_name": "Key Facts",
    "section_order": 3,
    "element_ids": ["messaging-key-messages"],
    "binding_rules": {
        "quantity": 3,
        "transformation": "excerpt",
        "max_length": null,
        "format": "bullet"
    }
}

# Binding 4: Quote 1
{
    "id": "binding-uuid-4",
    "template_id": "template-press-release-v1-0",
    "section_name": "Quote 1",
    "section_order": 4,
    "element_ids": ["vision-principles"],
    "binding_rules": {
        "quantity": 1,
        "transformation": "phrase_derived",
        "max_length": null,
        "format": "quote"
    }
}

# Binding 5: Boilerplate
{
    "id": "binding-uuid-5",
    "template_id": "template-press-release-v1-0",
    "section_name": "Boilerplate",
    "section_order": 6,
    "element_ids": ["messaging-boilerplate"],
    "binding_rules": {
        "quantity": 1,
        "transformation": "full",
        "max_length": null,
        "format": "paragraph"
    }
}
```

### How Bindings Work

When rendering a deliverable:

1. **Fetch Template with Bindings**:
   ```python
   template = template_service.get_template_with_bindings(template_id)
   # Returns: TemplateWithBindings (template + section_bindings list)
   ```

2. **For Each Binding, Assemble Content**:
   ```python
   for binding in template.section_bindings:
       # Get bound elements
       bound_elements = []
       for elem_id in binding.element_ids:
           element = unf_service.get_element(elem_id)
           if element.status == "approved":
               bound_elements.append(element)

       # Assemble section content
       section_content = story_model_composer.compose_section(
           section_name=binding.section_name,
           section_strategy=section_strategy,
           bound_elements=bound_elements,
           instance_data=instance_data
       )

       # Apply voice transformation
       section_content = voice_transformer.apply_voice_with_profile(
           content=section_content,
           section_name=binding.section_name,
           voice_config=voice_config
       )

       rendered_content[binding.section_name] = section_content
   ```

---

## Validation Rules Storage

### Validation Rule Types

Based on the specification in `StoryOS - Prototype DummyData.md`, validation rules check:

#### 1. **Content Constraints**
- Max word/character count
- Required elements present
- Section not empty

#### 2. **Structure Requirements**
- Required fields (who, what, when, where, why)
- Specific content patterns (e.g., action verb in headline)
- Element version requirements (e.g., "use latest approved")

#### 3. **Binding Validation**
- Correct number of elements bound
- Elements from required layers
- Element status checks (must be "approved")

### Storage in Story Models

**Table**: `story_models`

```sql
CREATE TABLE public.story_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sections JSONB DEFAULT '[]',
    constraints JSONB DEFAULT '{}',           -- Story Model constraints
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### constraints (JSONB)

Story Models define **structural constraints** that apply to all templates using that model:

```json
{
  "Headline": {
    "max_words": 10,
    "requires_action_verb": true,
    "required": true
  },
  "Lede": {
    "requires_five_ws": true,
    "max_words": 50,
    "required": true
  },
  "Quote 1": {
    "requires_speaker": true,
    "requires_title": true,
    "required": true
  },
  "Quote 2": {
    "requires_speaker": true,
    "requires_title": true,
    "required": false
  },
  "Boilerplate": {
    "requires_element": "Messaging.Boilerplate",
    "requires_latest_version": true,
    "required": true
  }
}
```

### Storage in Templates

Templates define **template-specific validation rules**:

```python
class ValidationRule(BaseModel):
    rule_type: str                    # Type of validation
    params: Dict[str, Any] = {}       # Rule parameters
    error_message: Optional[str]      # User-facing error
```

#### Common Rule Types

```python
# 1. MAX_WORD_COUNT
{
    "rule_type": "max_word_count",
    "params": {
        "section": "Headline",
        "max_words": 10
    },
    "error_message": "Headline must be 10 words or fewer"
}

# 2. REQUIRE_ELEMENT
{
    "rule_type": "require_element",
    "params": {
        "section": "Boilerplate",
        "element_name": "Messaging.Boilerplate",
        "status": "approved"
    },
    "error_message": "Boilerplate must use approved Messaging.Boilerplate element"
}

# 3. REQUIRE_FIELDS (Five W's)
{
    "rule_type": "require_fields",
    "params": {
        "section": "Lede",
        "fields": ["who", "what", "when", "where", "why"]
    },
    "error_message": "Lede must contain who, what, when, where, and why"
}

# 4. REQUIRE_ATTRIBUTION
{
    "rule_type": "require_attribution",
    "params": {
        "section": "Quote 1",
        "requires": ["speaker", "title"]
    },
    "error_message": "Quote 1 must have speaker name and title"
}

# 5. MIN_ITEMS
{
    "rule_type": "min_items",
    "params": {
        "section": "Key Facts",
        "min_count": 3
    },
    "error_message": "Key Facts must include at least 3 items"
}

# 6. REQUIRE_PATTERN (e.g., action verb)
{
    "rule_type": "require_pattern",
    "params": {
        "section": "Headline",
        "pattern": "contains_action_verb"
    },
    "error_message": "Headline must include at least one action verb"
}

# 7. NON_EMPTY
{
    "rule_type": "non_empty",
    "params": {
        "section": "Body"
    },
    "error_message": "Body section cannot be empty"
}
```

---

## How Validation Works

### Validation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User Creates Deliverable                                │
│     - Provides instance data (who, what, when, quotes)      │
│     - System renders sections                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Content Assembly                                         │
│     - Bind UNF Elements to sections                         │
│     - Apply extraction strategies                           │
│     - Inject instance data                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Validation (NOT YET IMPLEMENTED)                        │
│     - Run Story Model constraints                           │
│     - Run Template validation rules                         │
│     - Log results to validation_log                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Voice Transformation (if validation passes)             │
│     - Apply transformation profiles by section              │
│     - Apply brand voice                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Final Output                                             │
│     - Rendered content stored in deliverable                │
│     - Validation log shows pass/fail for each rule          │
└─────────────────────────────────────────────────────────────┘
```

### Validation Log Storage

**Table**: `deliverables`

```sql
CREATE TABLE public.deliverables (
    -- ... other fields ...
    validation_log JSONB DEFAULT '[]',
    -- ... other fields ...
);
```

**Pydantic Model**:

```python
class ValidationLogEntry(BaseModel):
    """Single validation check result"""
    timestamp: datetime
    rule: str                        # Validation rule that was checked
    passed: bool                     # Did it pass?
    message: Optional[str] = None    # Details or error message
```

**Storage Format** (JSONB Array):

```json
[
  {
    "timestamp": "2025-10-23T10:30:00Z",
    "rule": "max_word_count:Headline",
    "passed": true,
    "message": "Headline has 8 words (max: 10)"
  },
  {
    "timestamp": "2025-10-23T10:30:00Z",
    "rule": "require_five_ws:Lede",
    "passed": true,
    "message": "Lede contains all five W's: who, what, when, where, why"
  },
  {
    "timestamp": "2025-10-23T10:30:00Z",
    "rule": "require_attribution:Quote_1",
    "passed": false,
    "message": "Quote 1 missing speaker title"
  },
  {
    "timestamp": "2025-10-23T10:30:00Z",
    "rule": "require_element:Boilerplate",
    "passed": true,
    "message": "Boilerplate uses approved Messaging.Boilerplate v1.0"
  }
]
```

### Validation Service (To Be Implemented)

**File**: `services/validation_service.py` (NOT YET EXISTS)

```python
class ValidationService:
    """Validates deliverables against Story Model and Template rules"""

    def validate_deliverable(
        self,
        deliverable: Deliverable,
        template: TemplateWithBindings,
        story_model: StoryModel
    ) -> Tuple[bool, List[ValidationLogEntry]]:
        """
        Run all validation rules and return results.

        Returns:
            (all_passed, validation_log)
        """
        log_entries = []

        # 1. Run Story Model constraints
        for section_name, constraints in story_model.constraints.items():
            section_content = deliverable.rendered_content.get(section_name, "")

            # Check max_words
            if "max_words" in constraints:
                passed, message = self._check_max_words(
                    content=section_content,
                    max_words=constraints["max_words"]
                )
                log_entries.append(ValidationLogEntry(
                    timestamp=datetime.now(),
                    rule=f"max_words:{section_name}",
                    passed=passed,
                    message=message
                ))

            # Check requires_five_ws
            if constraints.get("requires_five_ws"):
                passed, message = self._check_five_ws(
                    content=section_content,
                    instance_data=deliverable.instance_data
                )
                log_entries.append(ValidationLogEntry(
                    timestamp=datetime.now(),
                    rule=f"five_ws:{section_name}",
                    passed=passed,
                    message=message
                ))

        # 2. Run Template validation rules
        for rule in template.validation_rules:
            passed, message = self._run_validation_rule(rule, deliverable)
            log_entries.append(ValidationLogEntry(
                timestamp=datetime.now(),
                rule=rule.rule_type,
                passed=passed,
                message=message
            ))

        all_passed = all(entry.passed for entry in log_entries)
        return all_passed, log_entries

    def _check_max_words(self, content: str, max_words: int) -> Tuple[bool, str]:
        """Check if content exceeds max word count"""
        word_count = len(content.split())
        passed = word_count <= max_words
        message = f"Word count: {word_count} (max: {max_words})"
        return passed, message

    def _check_five_ws(
        self,
        content: str,
        instance_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if content contains five W's"""
        required_fields = ["who", "what", "when", "where", "why"]
        missing = [
            field for field in required_fields
            if field not in instance_data or not instance_data[field]
        ]

        passed = len(missing) == 0
        if passed:
            message = f"Contains all five W's: {', '.join(required_fields)}"
        else:
            message = f"Missing: {', '.join(missing)}"

        return passed, message

    def _run_validation_rule(
        self,
        rule: ValidationRule,
        deliverable: Deliverable
    ) -> Tuple[bool, str]:
        """Run a specific validation rule"""
        if rule.rule_type == "require_element":
            return self._check_require_element(rule, deliverable)
        elif rule.rule_type == "require_attribution":
            return self._check_require_attribution(rule, deliverable)
        elif rule.rule_type == "min_items":
            return self._check_min_items(rule, deliverable)
        # ... etc

        return False, f"Unknown rule type: {rule.rule_type}"
```

---

## Complete Examples

### Example 1: Press Release Template

**Dummy Data Specification** (lines 356-393):

```markdown
#### Deliverable Template ID: template-press-release-v1-0

**Title:** Press Release Template
**Version:** 1.0
**Status:** Approved
**Story Model Used:** Inverted Pyramid Story Model v1.0
**Default Brand Voice:** Corporate Voice v1.0

**Sections and Bindings:**

1. Headline → Messaging.Key Messages (Element ID: messaging-key-messages, headline field)
2. Lede → Vision.Vision Statement (Element ID: vision-statement)
   + Inject "who, what, when, where, why" from PR metadata.
3. Key Facts → Messaging.Key Messages (Element ID: messaging-key-messages, proof fields, select 3).
4. Quote 1 → Vision.Principles (Element ID: vision-principles, phrase derived) + Executive attribution.
5. Quote 2 → Category.Problem (Element ID: category-problem, reframed) + Customer persona attribution.
6. Boilerplate → Messaging.Boilerplate (Element ID: messaging-boilerplate, use latest Approved version).

**Validation Rules:**

- Headline ≤10 words and must include one action verb.
- Lede must contain "who, what, when, where, and why."
- Key Facts section must include 3 Key Messages.
- Each Quote requires text and attribution fields.
- Boilerplate section required.
- Voice validation required before publishing.
```

**Database Storage**:

```python
# 1. Template Record
{
    "id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "name": "Press Release Template",
    "version": "1.0",
    "story_model_id": "61369622-3222-43c3-9bd6-e95ad7838d72",  # Inverted Pyramid
    "default_voice_id": "voice-corporate-v1-0",
    "status": "approved",
    "validation_rules": [
        {
            "rule_type": "max_word_count",
            "params": {"section": "Headline", "max_words": 10},
            "error_message": "Headline must be 10 words or fewer"
        },
        {
            "rule_type": "require_pattern",
            "params": {"section": "Headline", "pattern": "contains_action_verb"},
            "error_message": "Headline must include at least one action verb"
        },
        {
            "rule_type": "require_fields",
            "params": {"section": "Lede", "fields": ["who", "what", "when", "where", "why"]},
            "error_message": "Lede must contain who, what, when, where, and why"
        },
        {
            "rule_type": "min_items",
            "params": {"section": "Key Facts", "min_count": 3},
            "error_message": "Key Facts must include at least 3 Key Messages"
        },
        {
            "rule_type": "require_attribution",
            "params": {"section": "Quote 1", "requires": ["speaker", "title"]},
            "error_message": "Quote 1 must have speaker name and title"
        },
        {
            "rule_type": "require_attribution",
            "params": {"section": "Quote 2", "requires": ["speaker", "title"]},
            "error_message": "Quote 2 must have speaker name and title"
        },
        {
            "rule_type": "require_element",
            "params": {"section": "Boilerplate", "element_name": "Messaging.Boilerplate"},
            "error_message": "Boilerplate section required"
        }
    ],
    "instance_fields": [
        {"name": "who", "field_type": "text", "required": true, "description": "Company or organization name"},
        {"name": "what", "field_type": "text", "required": true, "description": "What is being announced"},
        {"name": "when", "field_type": "date", "required": true, "description": "Announcement date"},
        {"name": "where", "field_type": "text", "required": false, "description": "Location of announcement"},
        {"name": "why", "field_type": "text", "required": false, "description": "Purpose or reason"},
        {"name": "quote1_speaker", "field_type": "text", "required": true, "description": "Executive name"},
        {"name": "quote1_title", "field_type": "text", "required": true, "description": "Executive title"},
        {"name": "quote1_content", "field_type": "text", "required": true, "description": "Quote text from executive"},
        {"name": "quote2_speaker", "field_type": "text", "required": false, "description": "Customer name"},
        {"name": "quote2_title", "field_type": "text", "required": false, "description": "Customer title"},
        {"name": "quote2_content", "field_type": "text", "required": false, "description": "Quote text from customer"}
    ]
}

# 2. Section Bindings (6 records in template_section_bindings table)

# Binding 1: Headline
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Headline",
    "section_order": 1,
    "element_ids": ["messaging-key-messages"],
    "binding_rules": {"transformation": "excerpt", "format": "headline"}
}

# Binding 2: Lede
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Lede",
    "section_order": 2,
    "element_ids": ["vision-statement"],
    "binding_rules": {"transformation": "full", "inject_metadata": true}
}

# Binding 3: Key Facts
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Key Facts",
    "section_order": 3,
    "element_ids": ["messaging-key-messages"],
    "binding_rules": {"quantity": 3, "transformation": "excerpt", "format": "bullet"}
}

# Binding 4: Quote 1
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Quote 1",
    "section_order": 4,
    "element_ids": ["vision-principles"],
    "binding_rules": {"transformation": "phrase_derived", "format": "quote"}
}

# Binding 5: Quote 2
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Quote 2",
    "section_order": 5,
    "element_ids": ["category-problem"],
    "binding_rules": {"transformation": "reframed", "format": "quote"}
}

# Binding 6: Boilerplate
{
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "section_name": "Boilerplate",
    "section_order": 6,
    "element_ids": ["messaging-boilerplate"],
    "binding_rules": {"transformation": "full", "format": "paragraph"}
}
```

---

## Testing Strategy

### Current State

**Validation is NOT YET IMPLEMENTED.** The architecture is in place:
- Models exist (`ValidationRule`, `ValidationLogEntry`)
- Storage exists (JSONB fields in database)
- Validation log tracked in deliverables

**But**: No validation service exists to run the checks.

### Testing Approach

#### Unit Tests

**File**: `tests/test_validation_service.py` (TO BE CREATED)

```python
import pytest
from services.validation_service import ValidationService
from models.templates import ValidationRule
from models.deliverables import Deliverable

@pytest.fixture
def validation_service():
    return ValidationService()

def test_max_word_count_validation_passes():
    """Test that content under max words passes"""
    service = ValidationService()

    passed, message = service._check_max_words(
        content="This headline has exactly eight words here",
        max_words=10
    )

    assert passed is True
    assert "8" in message
    assert "10" in message

def test_max_word_count_validation_fails():
    """Test that content over max words fails"""
    service = ValidationService()

    passed, message = service._check_max_words(
        content="This headline has way too many words and exceeds the limit significantly",
        max_words=10
    )

    assert passed is False
    assert "12" in message  # Actual count
    assert "10" in message  # Max allowed

def test_five_ws_validation_all_present():
    """Test that five W's validation passes when all fields present"""
    service = ValidationService()

    instance_data = {
        "who": "Hexagon AB",
        "what": "announces HxGN Precision One",
        "when": "2025-10-17",
        "where": "Stockholm, Sweden",
        "why": "To help manufacturers increase precision"
    }

    passed, message = service._check_five_ws(
        content="Some content",
        instance_data=instance_data
    )

    assert passed is True
    assert "who, what, when, where, why" in message.lower()

def test_five_ws_validation_missing_fields():
    """Test that five W's validation fails when fields missing"""
    service = ValidationService()

    instance_data = {
        "who": "Hexagon AB",
        "what": "announces HxGN Precision One"
        # Missing: when, where, why
    }

    passed, message = service._check_five_ws(
        content="Some content",
        instance_data=instance_data
    )

    assert passed is False
    assert "missing" in message.lower()
    assert "when" in message.lower()

def test_require_element_validation():
    """Test that element presence is validated"""
    service = ValidationService()

    rule = ValidationRule(
        rule_type="require_element",
        params={
            "section": "Boilerplate",
            "element_name": "Messaging.Boilerplate"
        }
    )

    # Mock deliverable with boilerplate
    deliverable = create_test_deliverable(
        rendered_content={
            "Boilerplate": "Hexagon is a global leader..."
        },
        element_versions={
            "messaging-boilerplate": "1.0"
        }
    )

    passed, message = service._run_validation_rule(rule, deliverable)

    assert passed is True
```

#### Integration Tests

**File**: `tests/test_deliverable_validation.py` (TO BE CREATED)

```python
def test_press_release_validation_full_flow():
    """Test complete validation flow for press release"""

    # 1. Create press release deliverable
    deliverable_data = DeliverableCreate(
        name="Test Press Release",
        template_id=PRESS_RELEASE_TEMPLATE_ID,
        instance_data={
            "who": "Hexagon AB",
            "what": "announces HxGN Precision One",
            "when": "2025-10-17",
            "where": "Stockholm, Sweden",
            "why": "To help manufacturers increase precision",
            "quote1_speaker": "Burkhardt Boekem",
            "quote1_title": "Chief Technology Officer",
            "quote1_content": "This platform represents our vision for autonomous manufacturing",
            "quote2_speaker": "Jane Smith",
            "quote2_title": "Manufacturing Director, ACME Corp",
            "quote2_content": "We've seen a 40% improvement in precision"
        }
    )

    deliverable = deliverable_service.create_deliverable(deliverable_data)

    # 2. Validate
    passed, validation_log = validation_service.validate_deliverable(
        deliverable=deliverable,
        template=template,
        story_model=story_model
    )

    # 3. Assert all checks passed
    assert passed is True
    assert len(validation_log) > 0

    # Check specific validations
    headline_check = next(
        entry for entry in validation_log
        if entry.rule == "max_word_count:Headline"
    )
    assert headline_check.passed is True

    five_ws_check = next(
        entry for entry in validation_log
        if entry.rule == "five_ws:Lede"
    )
    assert five_ws_check.passed is True
```

#### Manual Testing Checklist

```markdown
## Press Release Validation Testing

### Headline Validation
- [ ] Create PR with 8-word headline → Should PASS
- [ ] Create PR with 12-word headline → Should FAIL (max: 10)
- [ ] Create PR with headline lacking action verb → Should FAIL
- [ ] Create PR with headline including action verb → Should PASS

### Lede Validation
- [ ] Create PR with all five W's → Should PASS
- [ ] Create PR missing "where" → Should FAIL
- [ ] Create PR missing "why" → Should FAIL

### Quote Validation
- [ ] Create PR with both speaker and title for Quote 1 → Should PASS
- [ ] Create PR missing speaker for Quote 1 → Should FAIL
- [ ] Create PR missing title for Quote 1 → Should FAIL

### Key Facts Validation
- [ ] Create PR with 3 key messages → Should PASS
- [ ] Create PR with 2 key messages → Should FAIL (min: 3)

### Boilerplate Validation
- [ ] Create PR using approved Messaging.Boilerplate → Should PASS
- [ ] Create PR using draft Messaging.Boilerplate → Should FAIL
- [ ] Create PR missing boilerplate → Should FAIL
```

---

## Summary

### Key Takeaways

1. **Templates Define Structure**: Templates map Story Model sections to UNF Elements through bindings

2. **Bindings Are Flexible**: Section bindings support:
   - Multiple elements per section
   - Binding rules (quantity, transformation, format)
   - Easy reuse across templates

3. **Validation Has Two Layers**:
   - **Story Model constraints**: Structural rules (max_words, required fields)
   - **Template rules**: Template-specific checks (attribution, element presence)

4. **Storage Is JSONB-Heavy**: Validation rules, instance fields, and binding rules use PostgreSQL JSONB for flexibility

5. **Validation Log Tracks Everything**: Every check is logged with timestamp, rule, pass/fail, and message

6. **Testing Is Critical**: Validation must be thoroughly tested at unit, integration, and manual levels

### What's Missing

**Validation Service** (`services/validation_service.py`) needs to be implemented to:
- Read Story Model constraints
- Read Template validation rules
- Run checks on deliverables
- Generate validation log entries
- Return pass/fail results

---

## References

- **Database Schema**: `/migrations/002_public_schema.sql`
- **Template Models**: `/models/templates.py`
- **Deliverable Models**: `/models/deliverables.py`
- **Dummy Data Spec**: `/Documentation/StoryOS - Prototype DummyData.md`
- **Story Model Composer**: `/services/story_model_composer.py`

---

**End of Document**
