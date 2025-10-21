# Phase 2: Voice Transformation & Story Model Restructuring

## Overview

Phase 2 transforms StoryOS from a **content assembly system** into a **content generation system** by:

1. **Voice Transformation**: Apply brand voice rules to transform content tone, style, and structure
2. **Story Model Restructuring**: Use story model logic to extract, restructure, and compose content

---

## 1. Voice Transformation System

### 1.1 Design Philosophy

**Goal**: Transform generic UNF content into brand-specific voice while preserving semantic meaning.

**Approach**: Rule-based transformation engine that applies sequential transformations to content.

### 1.2 Voice Rules Schema

```python
# Stored in brand_voices.rules (JSONB)
{
  "tone_rules": [
    {
      "type": "formality",
      "level": "formal",  # formal | casual | conversational
      "examples": {
        "casual": "We're excited to announce",
        "formal": "Hexagon AB is pleased to announce"
      }
    },
    {
      "type": "perspective",
      "value": "third_person",  # first_person | third_person
      "examples": {
        "first_person": "We develop solutions",
        "third_person": "Hexagon develops solutions"
      }
    }
  ],
  "lexicon": {
    # Word/phrase replacements
    "company_reference": {
      "generic": ["the company", "the organization"],
      "branded": "Hexagon"
    },
    "product_reference": {
      "generic": ["the product", "the solution"],
      "branded": "HxGN Precision One"
    }
  },
  "style_rules": [
    {
      "type": "sentence_length",
      "preference": "short",  # short | medium | long
      "max_words": 25
    },
    {
      "type": "active_voice",
      "enforce": true
    }
  ],
  "terminology": {
    # Industry-specific terms
    "preferred_terms": {
      "digital transformation": "digital reality solutions",
      "automation": "autonomous technologies",
      "data analytics": "sensor and software technologies"
    }
  }
}
```

### 1.3 Transformation Pipeline

**Order of Operations**:
1. **Lexicon replacement**: Replace generic terms with brand terms
2. **Terminology alignment**: Replace industry terms with brand-specific terms
3. **Tone transformation**: Adjust formality and perspective
4. **Style enforcement**: Enforce sentence structure rules

**Implementation**:
```python
class VoiceTransformer:
    def apply_voice(self, content: str, voice: BrandVoice) -> str:
        """Apply voice transformation pipeline"""

        # Step 1: Lexicon replacement
        content = self._apply_lexicon(content, voice.rules.get('lexicon', {}))

        # Step 2: Terminology alignment
        content = self._apply_terminology(content, voice.rules.get('terminology', {}))

        # Step 3: Tone transformation
        content = self._apply_tone(content, voice.rules.get('tone_rules', []))

        # Step 4: Style enforcement (future: LLM-based)
        # content = self._apply_style(content, voice.rules.get('style_rules', []))

        return content
```

### 1.4 Example Transformation

**Input** (generic UNF element):
```
The company announces the launch of its next-generation measurement platform.
This solution enables manufacturers to increase precision and reduce waste.
```

**Corporate Voice** (formal, third-person):
```
Hexagon AB announces the launch of HxGN Precision One, its next-generation
measurement platform. This digital reality solution enables manufacturers to
increase precision and reduce waste through autonomous technologies.
```

**Product Voice** (conversational, first-person):
```
We're excited to announce HxGN Precision One, our next-generation measurement
platform. Our solution helps manufacturers increase precision and reduce waste
with smart automation.
```

---

## 2. Story Model Restructuring System

### 2.1 Design Philosophy

**Goal**: Extract semantic content from UNF elements and compose it according to story model structure.

**Approach**: Intent-based content extraction + template-driven composition.

### 2.2 Story Model Structure

Story models define:
- **Sections**: Ordered list of content sections
- **Intent**: What each section should accomplish
- **Constraints**: Validation rules (word count, required elements, required fields)

**Example - Inverted Pyramid**:
```python
{
  "sections": [
    {
      "name": "Headline",
      "intent": "Capture the essence in 10 words or less",
      "order": 1,
      "required": true,
      "extraction_strategy": "key_message"
    },
    {
      "name": "Lede",
      "intent": "Answer who, what, when, where, why",
      "order": 2,
      "required": true,
      "extraction_strategy": "five_ws"
    },
    {
      "name": "Body",
      "intent": "Supporting details in descending order of importance",
      "order": 3,
      "required": true,
      "extraction_strategy": "full_content"
    }
  ]
}
```

### 2.3 Content Extraction Strategies

**1. Key Message Extraction** (for Headlines):
```python
def extract_key_message(element_content: str) -> str:
    """Extract main message, limit to 10 words"""
    # Strategy: First sentence, truncated to headline length
    sentences = element_content.split('.')
    headline = sentences[0].strip()
    words = headline.split()
    if len(words) > 10:
        headline = ' '.join(words[:10]) + '...'
    return headline
```

**2. Five W's Extraction** (for Lede):
```python
def extract_five_ws(element_content: str, instance_data: dict) -> str:
    """Compose lede using who/what/when/where/why"""
    template = "{where}, {when} — {who} {what}. {why}"
    return template.format(**instance_data)
```

**3. Full Content** (for Body):
```python
def extract_full_content(element_content: str) -> str:
    """Use complete element content"""
    return element_content
```

### 2.4 Section Composition Logic

**Current** (Phase 1):
```python
# Simple concatenation
section_content = "\n\n".join([elem.content for elem in elements])
```

**Phase 2**:
```python
def compose_section(
    section_definition: dict,
    bound_elements: list,
    instance_data: dict,
    voice: BrandVoice
) -> str:
    """Compose section using story model intent"""

    strategy = section_definition['extraction_strategy']

    # Extract content based on strategy
    if strategy == 'key_message':
        content = extract_key_message(bound_elements[0].content)
    elif strategy == 'five_ws':
        content = extract_five_ws(bound_elements[0].content, instance_data)
    elif strategy == 'full_content':
        content = "\n\n".join([elem.content for elem in bound_elements])
    else:
        content = "\n\n".join([elem.content for elem in bound_elements])

    # Apply voice transformation
    content = voice_transformer.apply_voice(content, voice)

    return content
```

### 2.5 Example Restructuring

**Input Elements**:
- Vision Statement: "Stockholm, Sweden — Hexagon is transforming manufacturing through digital reality solutions..."
- Key Messages: "Hexagon announces HxGN Precision One. Increases precision by 40%. Reduces waste by 30%."

**PAS Story Model**:
```
Problem: "Manufacturers struggle with precision and waste."
Agitate: "This costs $X billion annually and delays production."
Solve: "HxGN Precision One increases precision by 40% and reduces waste by 30%."
```

**Inverted Pyramid Story Model**:
```
Headline: "Hexagon Launches HxGN Precision One"
Lede: "Stockholm, Sweden, 2025-10-20 — Hexagon AB announces HxGN Precision One.
       The platform increases manufacturing precision by 40%."
Body: [Full content from elements]
```

---

## 3. Implementation Plan

### 3.1 Database Schema Updates

**Add to story_models table**:
```sql
ALTER TABLE story_models
ADD COLUMN section_strategies JSONB;

-- Example data:
{
  "Headline": {
    "extraction_strategy": "key_message",
    "max_words": 10,
    "source_element_types": ["Key Messages", "Vision Statement"]
  },
  "Lede": {
    "extraction_strategy": "five_ws",
    "required_fields": ["who", "what", "when", "where", "why"]
  }
}
```

**Add voice rules to brand_voices table**:
```sql
UPDATE brand_voices
SET rules = '{"tone_rules": [...], "lexicon": {...}}'::jsonb
WHERE name = 'Corporate Brand Voice';
```

### 3.2 New Services

**services/voice_transformer.py**:
- `VoiceTransformer` class
- Methods: `apply_voice()`, `_apply_lexicon()`, `_apply_terminology()`, `_apply_tone()`

**services/story_model_composer.py**:
- `StoryModelComposer` class
- Methods: `compose_section()`, `extract_key_message()`, `extract_five_ws()`

### 3.3 Integration Points

**Update `services/deliverable_service.py`**:
```python
def _assemble_section_content(
    self,
    binding,
    instance_data: Dict[str, Any],
    story_model: StoryModel,
    voice: BrandVoice
) -> str:
    # Get section strategy from story model
    section_strategy = story_model.section_strategies.get(binding.section_name, {})

    # Compose content using story model logic
    content = self.story_model_composer.compose_section(
        section_definition=section_strategy,
        bound_elements=[self.unf_service.get_element(eid) for eid in binding.element_ids],
        instance_data=instance_data
    )

    # Apply voice transformation
    content = self.voice_transformer.apply_voice(content, voice)

    return content
```

---

## 4. Testing Strategy

### 4.1 Voice Transformation Tests

**Test Case 4**: Transform content using Corporate Voice
- Input: Generic content
- Expected: Formal, third-person, brand terminology

**Test Case 5**: Transform content using Product Voice
- Input: Same generic content
- Expected: Conversational, first-person, simplified terms

**Verification**: Same source content produces different output based on voice

### 4.2 Story Model Tests

**Test Case 6**: Generate Press Release with Inverted Pyramid
- Verify Headline extracted from Key Messages
- Verify Lede composed using five W's
- Verify Body uses full content

**Test Case 7**: Generate Brand Manifesto with PAS
- Verify Problem section identifies challenge
- Verify Solve section references Vision Statement
- Verify content flows Problem → Agitate → Solve

---

## 5. Phase 2 vs Phase 1 Comparison

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Content Assembly** | Concatenation | Story model-aware composition |
| **Voice Application** | Metadata tracking only | Rule-based transformation |
| **Section Structure** | Template bindings | Intent-driven extraction |
| **Content Transformation** | None | Tone, lexicon, terminology |
| **Story Model Usage** | Validation only | Structural composition |

---

## 6. Future Enhancements (Phase 3+)

- **LLM Integration**: Use GPT-4 for sophisticated style transformations
- **Multi-language Support**: Voice rules per language
- **A/B Testing**: Compare voice variations
- **Automated Optimization**: Learn from user edits to improve rules
- **Visual Style Transfer**: Apply brand design rules to layouts

---

## 7. Success Metrics

**Phase 2 Complete When**:
- ✅ Same content + different voices = different output
- ✅ Same elements + different story models = different structure
- ✅ Voice rules applied to all content sections
- ✅ Story model intents drive content extraction
- ✅ Test Cases 4-7 passing
- ✅ Content quality improved (human review)

---

## Implementation Timeline

1. **Design** (current): Voice & Story Model schemas
2. **Voice Transformation**: Implement VoiceTransformer service
3. **Story Model Composition**: Implement StoryModelComposer service
4. **Integration**: Update DeliverableService to use both
5. **Sample Data**: Create voice rules for Corporate/Product voices
6. **Testing**: Test Cases 4-7
7. **Documentation**: Update README and TESTING_GUIDE

**Estimated Complexity**: Medium-High (requires careful design of extraction strategies)
