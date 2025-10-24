# Press Release Architecture Refactor

## Problem
PR-specific elements (PR Headline, PR Lede, PR Key Facts, PR Quote - Executive, PR Quote - Customer) were incorrectly created as UNF elements. According to System Details, these should be composed from instance_data and existing UNF elements, NOT stored as separate UNF elements.

## Solution Overview

### Correct Architecture

**From UNF Elements:**
- **Headline**: Extracted from Key Messages element's 'headline' field
- **Key Facts**: Extracted from Key Messages element's 'proof' fields (select 3)
- **Boilerplate**: Full Boilerplate element content
- **Vision Statement**: Used in Lede composition

**From Instance Data:**
- **who, what, when, where, why**: For Lede composition
- **quote1_text**: Full quote from executive
- **quote1_speaker**: Executive name
- **quote1_title**: Executive title
- **quote2_text**: Full quote from customer (optional)
- **quote2_speaker**: Customer name (optional)
- **quote2_title**: Customer title (optional)

**LLM-Composed:**
- **Lede**: Composed from instance_data (5 W's) + Vision Statement element

## Changes Made

### 1. Updated `scripts/load_dummy_data.py`

**Instance Fields** (lines 366-378):
- ✅ Added `quote1_text` and `quote2_text` fields
- ✅ Kept `quote1_speaker`, `quote1_title`, `quote2_speaker`, `quote2_title`
- ✅ Kept `who`, `what`, `when`, `where`, `why` fields

**Section Bindings** (lines 406-418):
- ✅ Quote 1 and Quote 2 now have empty `element_ids` arrays (quotes from instance_data)
- ✅ Other sections still bind to correct UNF elements

**Section Strategies** (lines 288-319):
- ✅ `Headline`: Uses `field_extraction` strategy with `field_path: 'headline'`
- ✅ `Lede`: Uses `composed` strategy with composition_sources including instance_data and Vision Statement
- ✅ `Key Facts`: Uses `field_extraction` strategy with `field_path: 'proof'` and `selection_count: 3`
- ✅ `Quote 1` and `Quote 2`: Use `instance_data` strategy with specific instance_fields
- ✅ `Boilerplate`: Uses `full_content` strategy

### 2. PR-Specific Elements to Remove

These 5 elements should be deleted from UNF:
- PR Headline (ID: 9a2c8e55-18e7-49a3-8aa6-ec321d571c11)
- PR Lede (ID: 627b35e4-331a-4e0e-931e-c01a80fbe39a)
- PR Key Facts (ID: ab04f91f-3e9c-4a0d-8bc0-1a8ead4f2508)
- PR Quote - Executive (ID: 58c72b8d-1cdf-4033-a052-d3c0c09a6652)
- PR Quote - Customer (ID: d71deba5-2cda-4c3e-9e2a-2798e60803a1)

**Note**: DELETE endpoint not available via API. Will be removed when database is reloaded with updated script.

## Implementation Requirements

### Story Model Composer Updates Needed

The `services/story_model_composer.py` needs to handle these new extraction strategies:

#### 1. Field Extraction Strategy
```python
def _extract_field_from_element(element_content: str, field_path: str, selection_count: int = None) -> str:
    """
    Extract specific fields from structured element content.

    Example - Key Messages element:
    Content format (plain text):
        Key Message 1
        Headline: Transform data into real-world outcomes
        Proof: Our Reality Technology connects...
        Benefit: Enables industries to act faster...

        Key Message 2
        Headline: Capture, create, and shape reality
        Proof: We unify sensors, software, and AI...
        Benefit: Turns data into decisions...

    field_path='headline' → Extract first headline
    field_path='proof', selection_count=3 → Extract first 3 proof statements

    Parsing logic:
    - Split content into "Key Message N" blocks
    - For each block, extract lines starting with "{field_path}:"
    - Return first match (or first N matches if selection_count specified)
    """
    pass
```

#### 2. Instance Data Strategy
```python
def _compose_from_instance_data(instance_data: dict, instance_fields: list) -> str:
    """
    Compose section content from instance_data fields.

    Example - Quote 1:
    instance_fields = ['quote1_text', 'quote1_speaker', 'quote1_title']

    Output format:
    "{quote1_text}"

    — {quote1_speaker}, {quote1_title}
    """
    pass
```

#### 3. Composed Strategy
```python
def _compose_with_llm(composition_sources: list, instance_data: dict, elements: dict) -> str:
    """
    LLM composes content from multiple sources.

    Example - Lede:
    composition_sources = [
        'instance_data.who',
        'instance_data.what',
        'instance_data.when',
        'instance_data.where',
        'instance_data.why',
        'element.Vision Statement'
    ]

    Prompt:
    "Compose a press release lede paragraph using the following:
    - Who: {who}
    - What: {what}
    - When: {when}
    - Where: {where}
    - Why: {why}
    - Vision: {vision_statement_content}

    Format: [Location], [Date] — [Who] announces [what] [why].
    Include the vision statement naturally."
    """
    pass
```

### Updated Composer Flow

```python
def compose_section(
    section_name: str,
    section_strategy: dict,
    bound_elements: list,
    instance_data: dict
) -> str:
    strategy = section_strategy.get('extraction_strategy')

    if strategy == 'full_content':
        # Existing behavior - return full element content
        return bound_elements[0].content

    elif strategy == 'field_extraction':
        # NEW: Extract specific fields from element
        field_path = section_strategy['field_path']
        selection_count = section_strategy.get('selection_count')
        return self._extract_field_from_element(
            bound_elements[0].content,
            field_path,
            selection_count
        )

    elif strategy == 'instance_data':
        # NEW: Compose from instance_data fields
        instance_fields = section_strategy['instance_fields']
        return self._compose_from_instance_data(instance_data, instance_fields)

    elif strategy == 'composed':
        # NEW: LLM composes from multiple sources
        composition_sources = section_strategy['composition_sources']
        return self._compose_with_llm(
            composition_sources,
            instance_data,
            {elem.name: elem for elem in bound_elements}
        )
```

## Testing Plan

### Test Case: Press Release Creation

**Instance Data:**
```json
{
  "who": "Hexagon AB",
  "what": "Announces HxGN Precision One measurement platform",
  "when": "2025-10-17",
  "where": "Stockholm, Sweden",
  "why": "To help manufacturers increase precision and reduce waste",
  "quote1_text": "Our integrated approach creates enormous value for our customers...",
  "quote1_speaker": "Maria Olsson",
  "quote1_title": "Chief Technology Officer, Hexagon AB",
  "quote2_text": "We have reduced costs by 16% while improving quality...",
  "quote2_speaker": "Alex Grant",
  "quote2_title": "Plant Director, Orion Manufacturing"
}
```

**Expected Output:**

**Headline**: "Transform data into real-world outcomes"
(Extracted from Key Messages.headline)

**Lede**: "Stockholm, Sweden, October 17, 2025 — Hexagon AB announces HxGN Precision One measurement platform to help manufacturers increase precision and reduce waste. Vision: A world where business, humanity, and the planet thrive together."
(Composed by LLM from instance_data + Vision Statement)

**Key Facts**:
- Our Reality Technology connects physical and digital realities...
- We unify sensors, software, and AI to bridge the gap...
- Advanced measurement and calibration systems ensure...
(Extracted 3 proof statements from Key Messages)

**Quote 1**:
"Our integrated approach creates enormous value for our customers..."

— Maria Olsson, Chief Technology Officer, Hexagon AB
(From instance_data)

**Quote 2**:
"We have reduced costs by 16% while improving quality..."

— Alex Grant, Plant Director, Orion Manufacturing
(From instance_data)

**Boilerplate**: [Full boilerplate text]
(From Boilerplate element)

## Next Steps

1. ✅ Update `load_dummy_data.py` script
2. ✅ Implement new extraction strategies in Story Model Composer
3. ✅ Clear database and reload with updated script
4. ✅ Test press release generation end-to-end
5. ✅ Remove `scripts/add_press_release_elements.py` and `scripts/add_press_release_strategies.py`
6. ✅ Update documentation

## Files Modified

- `scripts/load_dummy_data.py` - Updated instance_fields, section_bindings, and section_strategies
- `services/story_model_composer.py` - Implemented 3 new extraction strategies:
  - `field_extraction`: Extract specific fields from Key Messages (headline, proof)
  - `instance_data`: Compose quotes from instance_data fields
  - `composed`: Template-based Lede composition from 5 W's + Vision Statement

## Files Removed

- ✅ `scripts/add_press_release_elements.py` - Created PR-specific UNF elements (incorrect architecture)
- ✅ `scripts/add_press_release_strategies.py` - Added strategies (now in load_dummy_data.py)

## Implementation Complete

All architectural corrections have been implemented:
- ✅ 5 PR-specific elements removed from UNF
- ✅ Press Release template updated with correct instance_fields
- ✅ Section strategies updated to use correct extraction methods
- ✅ Story Model Composer implements all 3 new extraction strategies
- ✅ Database cleared and reloaded with correct architecture
- ✅ Obsolete scripts removed
