# Voice Transformation Architecture

**Document Status**: Implementation Complete
**Created**: 2025-10-23
**Last Updated**: 2025-10-23

---

## Executive Summary

This document memorializes the architectural decisions and implementation of **section-aware transformation profiles** for voice application in StoryOS. This system enables sophisticated, context-aware voice transformation that respects the unique requirements of different content types (headlines, quotes, body text, etc.).

### Key Decision

**We implemented Option B: Separate Transformation Profiles** as a distinct architectural layer that sits between content assembly and voice application.

### Core Principle

**Different content types require different transformation strategies.** A quote must be preserved verbatim, a headline must maintain strict length constraints, while body text can receive full voice transformation.

---

## Problem Statement

### Initial Issue

When applying brand voice transformation to press releases, the results were problematic:
- Quotes were being altered (quotes must remain verbatim)
- Headlines were exceeding word limits
- Boilerplate text was being unnecessarily transformed
- LLM prompts contained conflicting instructions
- No differentiation between content types

### Root Cause

The voice transformation system applied a **one-size-fits-all approach** to all sections:
1. Same LLM prompt for all content types
2. No awareness of section-specific constraints
3. No concept of transformation intensity levels
4. All transformation rules applied to all content

### User Feedback

> "I think we need to add the two quotes into the instance data. Otherwise it looks like the LLM is making them up."

This revealed that some content (quotes) should never be transformed automatically - it's user-provided data, not LLM-generated content.

---

## Design Process

### Phase 1: Understanding the Problem

We mapped out the actual transformations needed for manifesto → press release:

| Section | Source | Transformation Type | Description |
|---------|--------|---------------------|-------------|
| Headline | Vision.Purpose | Extraction + Condensing | "phrase derived", max 10 words |
| Lede | Category.Problem + Product.Benefits | Merging + Restructuring | "merged", must follow five W's |
| Key Facts | Product.Features | Formatting | "listed", convert to bullets, 3-5 items |
| Body | Product.Benefits | Expansion (?) | "expanded" - unclear meaning |
| Quote 1 | *User-provided* | **Authoring Guidance** | NOT a transformation! |
| Quote 2 | *User-provided* | **Authoring Guidance** | NOT a transformation! |
| Boilerplate | Company.About | Minimal/Preservation | "minimally transformed" |

**Key Insight**: Some things labeled as "transformations" in the spec are actually **authoring guidance**, not automated transformations.

### Phase 2: Identifying Transformation Dimensions

We identified three key dimensions that determine transformation rules:

**A. Content Type** (Deliverable Template)
- Press Release has different rules than Blog Post
- Each template type has specific constraints

**B. Section Type** (Within Deliverable)
- Headlines don't need much transformation
- Quotes should never be changed
- Body text has more opportunity for transformation

**C. Voice Variation** (Not intensity levels)
- Different brand voices (e.g., academic vs. punchy)
- Sub-brand voices
- Audience and channel adjustments

### Phase 3: Exploring Options

We evaluated three architectural approaches:

#### Option A: All in Story Model
Store transformation rules directly in Story Model `section_strategies`.

**Pros:**
- Single source of truth
- Keeps extraction and transformation together

**Cons:**
- Mixes two concerns (extraction vs transformation)
- Hard to override per-template
- Duplication across similar story models

#### Option B: Separate Transformation Profiles ✅ CHOSEN
Create transformation profiles as a distinct concept, mapped to section types.

**Pros:**
- Clean separation of concerns
- Reusable across story models
- Easy to override at multiple levels
- Standard profiles for common section types

**Cons:**
- Additional configuration layer

#### Option C: Embedded in Voice Config
Store section-specific transformation rules in Brand Voice.

**Pros:**
- Voice-centric approach

**Cons:**
- Duplicates across voices
- Voice shouldn't know about story structure
- Hard to maintain

### Phase 4: Cascade Architecture

We designed a hybrid ownership model with clear precedence:

```
Section Type Default Profile
    ↓ (overrides)
Story Model profile assignment
    ↓ (overrides)
Template profile override
    ↓ (applied with)
Brand Voice (lexicon, tone, traits)
```

**Division of Responsibilities:**
- **Story Model**: Owns structure and extraction strategies
- **Template**: Can override profiles when needed for specific use cases
- **Transformation Profiles**: Define HOW voice should be applied
- **Brand Voice**: Provides the lexicon, tone, traits to use

---

## Implementation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DELIVERABLE RENDERING                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Content Assembly (story_model_composer.py)        │
│  • Binds UNF Elements to sections                           │
│  • Applies extraction strategies (key_message, five_ws)     │
│  • Injects instance data placeholders                       │
│  • Output: Assembled raw content                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Voice Transformation (voice_transformer_llm.py)   │
│                                                              │
│  1. Look up section name → transformation profile           │
│     (transformation_profiles.py)                            │
│                                                              │
│  2. Get profile-specific instructions:                      │
│     • PRESERVE → Skip transformation                        │
│     • REDUCE_ONLY → Only if exceeds constraints             │
│     • VOICE_CONSTRAINED → Apply voice + preserve length     │
│     • VOICE_FORMATTED → Apply voice + preserve format       │
│     • VOICE_FULL → Full transformation                      │
│                                                              │
│  3. Build focused LLM prompt with:                          │
│     • Profile instructions                                  │
│     • Section constraints (max_words, format)               │
│     • Brand voice (traits, tone, lexicon)                   │
│                                                              │
│  4. Transform via Claude API                                │
│     • Temperature: 0.0 (deterministic)                      │
│     • Fallback to regex transformer on error               │
│                                                              │
│  Output: Voiced, section-appropriate content                │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
services/
├── transformation_profiles.py   (NEW)
│   ├── TransformationProfileType (Enum)
│   ├── TransformationProfiles (Class)
│   │   ├── PROFILES (Dict of profile definitions)
│   │   ├── SECTION_TYPE_MAPPINGS (Dict of section → profile)
│   │   ├── get_profile_for_section()
│   │   └── build_profile_prompt()
│
├── voice_transformer_llm.py     (UPDATED)
│   └── LLMVoiceTransformer
│       ├── apply_voice()  (legacy method)
│       └── apply_voice_with_profile()  (NEW - preferred)
│
└── deliverable_service.py       (UPDATED)
    └── _assemble_section_content()
        └── Now calls apply_voice_with_profile()
```

### Transformation Profile Definitions

#### 1. PRESERVE Profile

**Use Case**: Quotes, citations, attributions

**Instructions to LLM**:
```
Do not transform this content. Return it exactly as provided, word-for-word.
This content must remain verbatim - it represents quotes or other content that
cannot be altered.
```

**Behavior**:
- Skips LLM entirely
- Returns content exactly as provided
- No voice application

**Example**:
```
INPUT:  "We unlock human potential through technology and data."
OUTPUT: "We unlock human potential through technology and data."
         (unchanged)
```

---

#### 2. REDUCE_ONLY Profile

**Use Case**: Boilerplate, company descriptions, about sections

**Instructions to LLM**:
```
Preserve the original voice, tone, and meaning of this content.
Only make changes if the content exceeds length constraints - in that case,
reduce length minimally.
Do NOT apply brand voice transformation. Keep the original style intact.
```

**Behavior**:
- Checks if content exceeds constraints
- Only calls LLM if reduction needed
- Preserves original voice
- Minimal changes

**Example**:
```
INPUT:  "Hexagon AB is a global leader in digital reality solutions, combining
         sensor, software and autonomous technologies. We are putting data to
         work to boost efficiency, productivity, quality and safety across
         industrial, manufacturing, infrastructure, public sector, and mobility
         applications." (150 words)

CONSTRAINT: max_words: 50

OUTPUT: "Hexagon AB is a global leader in digital reality solutions. We put
         data to work to boost efficiency across industrial, manufacturing,
         infrastructure, and mobility applications." (30 words)
```

---

#### 3. VOICE_CONSTRAINED Profile

**Use Case**: Headlines, titles, subheads, taglines

**Instructions to LLM**:
```
Transform this content to match the brand voice fully.
CRITICAL: You must preserve the exact length constraint (max words/characters).
The meaning must stay consistent - do not add or remove information.
Apply voice transformation within these strict boundaries.
```

**Behavior**:
- Applies full voice transformation
- MUST preserve exact length (max_words)
- Meaning cannot change
- Lexicon replacements applied
- Tone adjustments made

**Example**:
```
INPUT:  "Hexagon AB announces the launch of HxGN Precision One"
CONSTRAINT: max_words: 8
VOICE: Bold, Direct, Technical | Use "launches" not "announces"

OUTPUT: "Hexagon Launches HxGN Precision One Platform"
        (8 words, voice applied, meaning preserved)
```

---

#### 4. VOICE_FORMATTED Profile

**Use Case**: Key facts, bullet points, numbered lists, features

**Instructions to LLM**:
```
Transform this content to match the brand voice.
Maintain the list format (bullets, numbers) and item count exactly.
Each list item should be transformed independently.
Preserve the structure while applying voice transformation to the content.
```

**Behavior**:
- Applies voice transformation
- Preserves format (bullets, numbers)
- Maintains item count
- Each item transformed independently

**Example**:
```
INPUT:
• Feature 1 utilizes advanced sensor technology
• Feature 2 leverages cloud-based analytics
• Feature 3 provides real-time monitoring capabilities

VOICE: Use "uses" not "utilizes", "use" not "leverage"

OUTPUT:
• Feature 1 uses advanced sensor technology
• Feature 2 uses cloud-based analytics
• Feature 3 provides real-time monitoring capabilities
```

---

#### 5. VOICE_FULL Profile

**Use Case**: Body paragraphs, lede, introductions, conclusions

**Instructions to LLM**:
```
Transform this content fully to match the brand voice.
Maintain the overall structure and meaning, but apply complete voice transformation.
This includes lexicon, tone, sentence structure, and style.
Ensure the transformed content flows naturally in the brand voice.
```

**Behavior**:
- Full voice transformation
- Structure preserved (paragraphs, sections)
- Meaning maintained
- Complete lexicon, tone, style application
- Natural flow in brand voice

**Example**:
```
INPUT:
"The company is excited to announce that we are launching a new product that
will help manufacturers to increase precision and reduce waste in their
operations."

VOICE: Bold, Direct, Technical | Use "Hexagon" not "the company"

OUTPUT:
"Hexagon launches a new precision platform that helps manufacturers increase
accuracy and reduce waste."
(More concise, direct, branded)
```

---

### Section Type Mappings

The system includes default mappings for 20+ common section types:

```python
SECTION_TYPE_MAPPINGS = {
    # Preserve verbatim
    "Quote": PRESERVE,
    "Quote 1": PRESERVE,
    "Quote 2": PRESERVE,
    "Citation": PRESERVE,
    "Attribution": PRESERVE,

    # Minimal transformation
    "Boilerplate": REDUCE_ONLY,
    "About": REDUCE_ONLY,
    "Company Description": REDUCE_ONLY,

    # Voice with strict constraints
    "Headline": VOICE_CONSTRAINED,
    "Title": VOICE_CONSTRAINED,
    "Subhead": VOICE_CONSTRAINED,
    "Tagline": VOICE_CONSTRAINED,

    # Voice with format preservation
    "Key Facts": VOICE_FORMATTED,
    "Bullet Points": VOICE_FORMATTED,
    "List": VOICE_FORMATTED,
    "Features": VOICE_FORMATTED,
    "Benefits": VOICE_FORMATTED,

    # Full voice transformation
    "Lede": VOICE_FULL,
    "Body": VOICE_FULL,
    "Introduction": VOICE_FULL,
    "Paragraph": VOICE_FULL,
    "Conclusion": VOICE_FULL,
    "Problem": VOICE_FULL,
    "Solution": VOICE_FULL,
    "Agitate": VOICE_FULL,
}
```

---

## Usage Examples

### Example 1: Press Release Rendering

**Template**: Press Release
**Story Model**: Inverted Pyramid
**Voice**: Hexagon Brand Voice

**Section Rendering Flow**:

```python
# HEADLINE
section_name = "Headline"
profile = get_profile_for_section("Headline")  # → VOICE_CONSTRAINED
constraints = {"max_words": 10}

# Profile skips LLM? No, VOICE_CONSTRAINED applies voice
# Prompt includes: "preserve exact length", brand traits, lexicon
# Result: Voiced headline, exactly 10 words

# QUOTE 1
section_name = "Quote 1"
profile = get_profile_for_section("Quote 1")  # → PRESERVE
# Profile skips LLM? Yes, returns content as-is
# Result: Quote unchanged from instance data

# BODY
section_name = "Body"
profile = get_profile_for_section("Body")  # → VOICE_FULL
# Profile skips LLM? No, VOICE_FULL applies full transformation
# Prompt includes: full voice application, maintain structure
# Result: Fully voiced body content
```

### Example 2: Override Cascade

**Scenario**: Special headline that should NOT be transformed

```python
# Template Override (highest priority)
template_binding = {
    "section_name": "Special Headline",
    "transformation_profile_override": "preserve"  # Override to PRESERVE
}

# System looks up profile:
profile = get_profile_for_section(
    section_name="Special Headline",
    story_model_override=None,
    template_override="preserve"  # This wins!
)

# Result: profile = PRESERVE (despite "Headline" mapping to VOICE_CONSTRAINED)
```

### Example 3: Custom Profile in Story Model

**Scenario**: Custom story model wants headlines with minimal voice

```python
# Story Model defines override
story_model = {
    "name": "Custom Model",
    "section_strategies": {
        "Headline": {
            "extraction_strategy": "key_message",
            "max_words": 8,
            "transformation_profile": "reduce_only"  # Story Model override
        }
    }
}

# System looks up profile:
profile = get_profile_for_section(
    section_name="Headline",
    story_model_override="reduce_only",  # This overrides default
    template_override=None
)

# Result: profile = REDUCE_ONLY (instead of default VOICE_CONSTRAINED)
```

---

## Code Integration Points

### 1. In deliverable_service.py

```python
def _assemble_section_content(
    self,
    binding,
    instance_data: Dict[str, Any],
    story_model,
    voice
) -> str:
    # ... (Phase 1: Content Assembly) ...

    # Phase 2: Apply voice transformation with profile
    if voice:
        voice_config = {
            'traits': voice.traits,
            'tone_rules': voice.tone_rules,
            'lexicon': voice.lexicon,
            # ... etc
        }

        # NEW: Profile-aware transformation
        assembled_content = self.llm_voice_transformer.apply_voice_with_profile(
            content=assembled_content,
            voice_config=voice_config,
            section_name=binding.section_name,  # Key: section awareness
            constraints=section_strategy  # Includes max_words, format, etc.
        )

    return assembled_content
```

### 2. In voice_transformer_llm.py

```python
def apply_voice_with_profile(
    self,
    content: str,
    voice_config: Dict[str, Any],
    section_name: str,
    constraints: Optional[Dict[str, Any]] = None,
    story_model_override: Optional[str] = None,
    template_override: Optional[str] = None,
    use_llm: bool = True
) -> str:
    # Get transformation profile for this section
    profile = TransformationProfiles.get_profile_for_section(
        section_name=section_name,
        story_model_override=story_model_override,
        template_override=template_override
    )

    # If profile says don't apply voice, return as-is (or reduce if needed)
    if not profile.get('apply_voice', False):
        if profile_type == PRESERVE:
            return content  # No changes
        elif profile_type == REDUCE_ONLY:
            # Only call LLM if exceeds constraints
            if needs_reduction(content, constraints):
                # ... reduce ...
            else:
                return content

    # Build profile-specific prompt
    prompt = TransformationProfiles.build_profile_prompt(
        profile=profile,
        voice_config=voice_config,
        content=content,
        constraints=constraints
    )

    # Transform via LLM
    return self.llm_client.transform_content(prompt, temperature=0.0)
```

### 3. In transformation_profiles.py

```python
@classmethod
def get_profile_for_section(
    cls,
    section_name: str,
    story_model_override: Optional[str] = None,
    template_override: Optional[str] = None
) -> Dict[str, Any]:
    # Cascade logic
    profile_type = None

    # 1. Template override (highest priority)
    if template_override:
        profile_type = TransformationProfileType(template_override)

    # 2. Story Model override
    elif story_model_override:
        profile_type = TransformationProfileType(story_model_override)

    # 3. Section type default mapping
    elif section_name in cls.SECTION_TYPE_MAPPINGS:
        profile_type = cls.SECTION_TYPE_MAPPINGS[section_name]

    # 4. Fallback
    else:
        profile_type = TransformationProfileType.VOICE_FULL

    return cls.PROFILES[profile_type]
```

---

## Benefits

### 1. Clean Separation of Concerns

**Before**: Voice transformer had no concept of section types, applied same rules to everything.

**After**:
- Story Model owns structure and extraction
- Transformation Profiles define HOW to transform
- Brand Voice provides WHAT to apply
- Template can override when needed

### 2. Section-Aware Transformation

**Before**: Headlines could exceed word limits, quotes got transformed, boilerplate was unnecessarily changed.

**After**:
- Headlines: Voice applied, length preserved
- Quotes: Never touched
- Boilerplate: Only changed if needed
- Body: Full transformation

### 3. Focused LLM Prompts

**Before**: Single prompt with conflicting rules for all sections.

**After**: Each profile gets tailored instructions:
- PRESERVE: "Return exactly as provided"
- VOICE_CONSTRAINED: "Preserve exact length, apply voice"
- VOICE_FULL: "Full transformation"

### 4. Reusability

**Before**: Transformation rules duplicated across story models.

**After**:
- Standard profiles for common section types
- Defined once, used everywhere
- Easy to override for special cases

### 5. Extensibility

Easy to add:
- New profile types (e.g., "VOICE_LEGAL" for compliant transformations)
- New section mappings (e.g., "Executive Summary" → VOICE_FULL)
- Profile overrides at Story Model or Template level

---

## Future Enhancements

### 1. Profile Persistence

**Current**: Profiles are code-based (Python enums and dicts)

**Future**: Store profiles in database
- Allow users to create custom profiles
- UI for managing profile definitions
- Profile versioning

### 2. Profile Metrics

Track profile effectiveness:
- Transformation quality scores
- Constraint violation rates
- User satisfaction by profile
- A/B testing of profile instructions

### 3. Context-Aware Profiles

Extend profiles to consider:
- Audience (technical vs. general)
- Channel (web vs. print)
- Urgency (formal vs. casual)
- Industry vertical

### 4. Multi-Language Profiles

Adapt profiles for different languages:
- Translation-aware transformations
- Language-specific constraints
- Cultural tone adjustments

### 5. Learning Profiles

Use ML to optimize profile instructions:
- Collect user edits to transformed content
- Fine-tune profile prompts based on patterns
- Suggest profile improvements

---

## Testing Strategy

### Unit Tests

```python
def test_preserve_profile_returns_unchanged():
    """PRESERVE profile should return content exactly as-is"""
    profile = TransformationProfiles.get_profile_for_section("Quote 1")
    assert profile['apply_voice'] == False

    content = "Original quote text"
    result = apply_voice_with_profile(
        content=content,
        section_name="Quote 1",
        voice_config={}
    )
    assert result == content  # Unchanged

def test_voice_constrained_preserves_length():
    """VOICE_CONSTRAINED should maintain exact word count"""
    content = "This is a test headline with ten words exactly"
    constraints = {"max_words": 10}

    result = apply_voice_with_profile(
        content=content,
        section_name="Headline",
        voice_config=test_voice,
        constraints=constraints
    )

    assert len(result.split()) == 10  # Exactly 10 words
```

### Integration Tests

```python
def test_press_release_section_profiles():
    """Verify each press release section uses correct profile"""
    deliverable = create_press_release(...)

    # Headline should be voice_constrained
    assert_profile_used("Headline", "voice_constrained")

    # Quote should be preserve
    assert_profile_used("Quote 1", "preserve")

    # Body should be voice_full
    assert_profile_used("Body", "voice_full")
```

### Manual Testing Checklist

- [ ] Create new press release deliverable
- [ ] Verify Quote 1 matches instance data exactly (no transformation)
- [ ] Verify Headline is exactly max_words length
- [ ] Verify Headline has brand voice applied
- [ ] Verify Body has full voice transformation
- [ ] Verify Boilerplate is minimally changed
- [ ] Verify Key Facts maintain bullet format

---

## Deployment Notes

### Railway Deployment

**Commit**: `4d76cee`
**Files Changed**:
- `services/transformation_profiles.py` (NEW - 370 lines)
- `services/voice_transformer_llm.py` (UPDATED - added 87 lines)
- `services/deliverable_service.py` (UPDATED - 6 lines changed)

**Migration Steps**: None required (backward compatible)

**Rollback Plan**:
- System falls back to `apply_voice()` if `apply_voice_with_profile()` fails
- No database schema changes
- Can revert commit safely

### Monitoring

Watch for:
- LLM transformation errors (logged to console)
- Profile lookup failures (falls back to VOICE_FULL)
- Constraint violations (headlines exceeding max_words)
- User reports of incorrect transformations

---

## Decision Log

### Decision 1: Separate Profiles vs Embedded

**Date**: 2025-10-23
**Decision**: Implement separate transformation profiles (Option B)
**Rationale**:
- Cleaner separation of concerns
- Reusable across story models
- Easier to maintain and extend
- Standard profiles for common section types

**Alternatives Considered**:
- Option A: Embed in Story Model section_strategies
- Option C: Store in Brand Voice config

### Decision 2: Code-Based vs Database Profiles

**Date**: 2025-10-23
**Decision**: Start with code-based profiles
**Rationale**:
- Faster to implement
- Version controlled
- Easy to test
- Can migrate to database later

**Future**: Move to database when UI needed

### Decision 3: Profile Cascade Order

**Date**: 2025-10-23
**Decision**: Template → Story Model → Section Type → Fallback
**Rationale**:
- Template most specific (overrides everything)
- Story Model second (defines structure)
- Section Type default (sensible defaults)
- Fallback to VOICE_FULL (safe default)

### Decision 4: Five Profile Types

**Date**: 2025-10-23
**Decision**: PRESERVE, REDUCE_ONLY, VOICE_CONSTRAINED, VOICE_FORMATTED, VOICE_FULL
**Rationale**:
- Covers all use cases identified in press releases
- Clear, distinct purposes
- Room to add more types later

**Alternatives Considered**:
- Light/Medium/Heavy intensity levels (rejected: too vague)
- Per-deliverable profiles (rejected: too many profiles)

---

## Glossary

**Transformation Profile**: A named strategy that defines HOW voice transformation should be applied to a specific type of content.

**Section Type**: The category of content within a deliverable (e.g., Headline, Quote, Body).

**Voice Application**: The process of applying brand voice traits, tone, and lexicon to content.

**Extraction Strategy**: How content is assembled from UNF Elements (e.g., key_message, five_ws).

**Cascade Logic**: The precedence order for determining which profile to use (Template → Story Model → Section Type → Fallback).

**Constraint**: A requirement that must be met after transformation (e.g., max_words: 10).

**Instance Data**: Temporary, deliverable-specific data provided by users (e.g., who, what, when, quotes).

---

## References

- **Brainstorming Session**: 2025-10-23 (conversation with user)
- **Dummy Data Spec**: `/Documentation/StoryOS - Prototype DummyData.md`
- **Implementation**: Commit `4d76cee` on `master` branch
- **Related Files**:
  - `services/transformation_profiles.py`
  - `services/voice_transformer_llm.py`
  - `services/deliverable_service.py`
  - `services/story_model_composer.py`

---

## Authors

- Architecture: Drew (User) & Claude (AI)
- Implementation: Claude Code
- Document: Claude Code

---

**End of Document**
