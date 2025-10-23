# LLM-Based Voice Transformation - Implementation Guide

## Overview

We've implemented a context-aware, LLM-based voice transformation system that uses Claude AI to apply brand voice guidelines intelligently. This replaces the fragile regex-based approach with a robust, context-aware solution.

## What Was Built

### 1. LLM Client Service (`services/llm_client.py`)
- Handles communication with Anthropic Claude API
- Uses Claude 3.5 Haiku for fast, cost-effective transformations
- Singleton pattern for connection reuse
- Error handling with fallbacks

### 2. LLM Voice Transformer (`services/voice_transformer_llm.py`)
- Converts brand voice guidelines into natural language instructions
- Builds comprehensive prompts from ALL voice configuration data:
  - **Traits** (personality: Confident, Precise, etc.)
  - **Tone Rules** (formality, POV, sentence length, voice, contractions, tense)
  - **Style Guardrails** (do's, don'ts, punctuation preferences)
  - **Lexicon** (required/banned/preferred terms)
  - **Transformation Rules** (word replacements, terminology preferences)

### 3. Integration (`services/deliverable_service.py`)
- Updated to use LLM transformer by default
- Falls back to regex transformer if LLM fails
- Passes complete voice configuration to LLM

## How It Works

### Input: Brand Voice Configuration

The system reads from the `brand_voices` table:

```python
{
    "traits": ["Confident", "Precise", "Grounded", "Optimistic", "Professional"],
    "tone_rules": {
        "formality": "medium-high",
        "point_of_view": "third-person",
        "sentence_length": "15-25 words average",
        "voice": "active voice required",
        "contractions": "allowed in informal materials",
        "tense": "present tense preferred"
    },
    "style_guardrails": {
        "do": ["Use clear, declarative sentences", "Lead with evidence"],
        "dont": ["Overpromise", "Use jargon"],
        "punctuation": "Avoid exclamation marks"
    },
    "lexicon": {
        "required": ["When it has to be right"],
        "banned": ["Reality Technology"],
        "preferred": [...]
    },
    "rules": {
        "lexicon": {
            "company_reference": {
                "generic": ["the company", "we", "our"],
                "branded": "Hexagon AB"
            }
        },
        "terminology": {
            "preferred_terms": {
                "digital transformation": "digital reality solutions",
                "automation": "autonomous technologies"
            }
        }
    }
}
```

### Prompt Construction

The transformer builds a comprehensive prompt like:

```
You are a professional copyeditor transforming content to match a specific brand voice.

## BRAND PERSONALITY
Confident, Precise, Grounded, Optimistic, Professional

## TONE GUIDELINES
- Formality: medium-high (expand contractions, use formal language)
- Point of view: third-person
- Sentence length: 15-25 words average
- Voice: active voice required
- Contractions: allowed in informal materials
- Tense: present tense preferred

## STYLE GUARDRAILS
DO:
  - Use clear, declarative sentences
  - Lead with evidence and measurable impact

DON'T:
  - Overpromise or use emotionally charged language
  - Use jargon that obscures meaning

Punctuation: Avoid exclamation marks and rhetorical questions

## TERMINOLOGY
REQUIRED phrases to include when appropriate:
  - "When it has to be right"

BANNED phrases to avoid:
  - "Reality Technology"

## WORD REPLACEMENTS
- Replace "the company", "we", "our" with "Hexagon AB" (only when referring to the company, not when part of other words)

Preferred terminology:
  - Use "digital reality solutions" instead of "digital transformation"
  - Use "autonomous technologies" instead of "automation"

## IMPORTANT RULES
- Only replace pronouns when they clearly refer to the company (not when part of other words)
- Preserve all markdown formatting
- Maintain natural flow and readability
- Return ONLY the transformed content

## CONTENT TO TRANSFORM

[Original content here]

## TRANSFORMED CONTENT
```

### Output

Claude returns the transformed content with:
- ✅ Context-aware word replacements ("we" in "We announce" → "Hexagon AB")
- ✅ Preservation of words like "Empowering", "Sweden", "between"
- ✅ Tone adjustments (formality, sentence structure)
- ✅ Style compliance (active voice, declarative sentences)
- ✅ Terminology preferences applied
- ✅ Markdown formatting preserved

## Setup Instructions

### 1. Get Anthropic API Key

1. Go to https://console.anthropic.com
2. Create an account or sign in
3. Navigate to API Keys
4. Generate a new API key
5. Copy the key (starts with `sk-ant-...`)

### 2. Add to Environment

Add to `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 3. Add to Railway (Production)

```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Or via Railway dashboard:
1. Go to your project
2. Click "Variables"
3. Add `ANTHROPIC_API_KEY` with your key
4. Redeploy

### 4. Restart Backend

```bash
# Kill current server
killall -9 python3

# Clear cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# Restart
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

### Test Script

```python
from services.voice_transformer_llm import get_voice_transformer
from storage.supabase_storage import SupabaseStorage
import os
from dotenv import load_dotenv

load_dotenv()

# Get Corporate Brand Voice
storage = SupabaseStorage(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
result = storage.client.table('brand_voices').select('*').eq('name', 'Corporate Brand Voice').execute()
voice = result.data[0]

# Test content
test_content = """
We're excited to announce our new platform for digital transformation.
The automation capabilities will help companies worldwide.
We believe in empowering organizations to succeed.
"""

# Build voice config
voice_config = {
    'traits': voice['traits'],
    'tone_rules': voice['tone_rules'],
    'style_guardrails': voice['style_guardrails'],
    'lexicon': voice['lexicon'],
    'rules': voice['rules']
}

# Transform
transformer = get_voice_transformer()
transformed = transformer.apply_voice(test_content, voice_config)

print("ORIGINAL:")
print(test_content)
print("\nTRANSFORMED:")
print(transformed)
```

### Expected Output

```
ORIGINAL:
We're excited to announce our new platform for digital transformation.
The automation capabilities will help companies worldwide.
We believe in empowering organizations to succeed.

TRANSFORMED:
Hexagon AB is pleased to announce its new platform for digital reality solutions.
The autonomous technologies capabilities will help companies worldwide.
Hexagon AB believes in empowering organizations to succeed.
```

Note how:
- "We're" → "Hexagon AB is" (formality + perspective)
- "we" → "Hexagon AB" (pronoun replacement)
- "digital transformation" → "digital reality solutions" (terminology)
- "automation" → "autonomous technologies" (terminology)
- "empowering" → stays "empowering" (not "empoHexagon ABring"!)

## Cost Analysis

**Per Deliverable:**
- Average deliverable: ~1,000 tokens input, ~1,000 tokens output
- Claude 3.5 Haiku: $0.25/$1.25 per M tokens (input/output)
- Cost: ~$0.0025 per deliverable (quarter of a penny)

**Monthly estimates:**
- 100 deliverables/month: **$0.25**
- 1,000 deliverables/month: **$2.50**
- 10,000 deliverables/month: **$25.00**

**Performance:**
- Latency: ~500-1500ms
- Quality: Much better than regex
- Reliability: Fallback to regex on errors

## Benefits Over Regex

### Before (Regex)
❌ "Empowering" → "EmpoHexagon ABring"
❌ "Sweden" → "SHexagon ABden"
❌ "between" → "betHexagon ABen"
❌ Cannot adjust tone or style
❌ Cannot understand context
❌ Complex patterns break easily

### After (LLM)
✅ "Empowering" → "Empowering"
✅ "Sweden" → "Sweden"
✅ "between" → "between"
✅ Adjusts formality, sentence structure, voice
✅ Understands when "we" refers to company vs. part of word
✅ Maintains natural flow
✅ Style guidelines enforced
✅ Easy to maintain (rules in database)

## Files Modified

1. **requirements.txt** - Added `anthropic==0.71.0`
2. **services/llm_client.py** - New: LLM client wrapper
3. **services/voice_transformer_llm.py** - New: LLM-based transformer
4. **services/deliverable_service.py** - Updated: Use LLM transformer with fallback
5. **.env** - Need to add: `ANTHROPIC_API_KEY`

## Next Steps

1. **Add API Key** - Get from https://console.anthropic.com
2. **Test Locally** - Create deliverable, verify transformation
3. **Deploy to Railway** - Add API key to Railway variables
4. **Monitor Costs** - Track API usage in Anthropic dashboard
5. **Optimize** (optional):
   - Cache transformations for identical content
   - Use cheaper model (Haiku) for simple transformations
   - Batch multiple sections in one API call

## Troubleshooting

### "Anthropic API key required" Error

**Problem:** ANTHROPIC_API_KEY not set

**Solution:**
```bash
# Add to .env
echo 'ANTHROPIC_API_KEY=sk-ant-api03-your-key-here' >> .env

# Restart server
```

### Transformation Not Happening

**Problem:** API error, falling back to regex

**Solution:**
- Check server logs for error details
- Verify API key is valid
- Check Anthropic API status
- Ensure account has credits

### Transformation Too Slow

**Problem:** 1-2 second delay per deliverable

**Solution:**
- This is normal for LLM transformations
- Caching can help for repeated content
- Consider showing "Transforming..." indicator in UI

### Cost Too High

**Problem:** API costs exceeding budget

**Solution:**
- Check which deliverables are being transformed repeatedly
- Add caching layer
- Use cheaper model (Haiku instead of Sonnet)
- Set monthly spending limits in Anthropic dashboard

## Rollback Plan

If LLM transformation causes issues:

1. **Disable LLM** (immediate):
```python
# In deliverable_service.py, change:
assembled_content = self.llm_voice_transformer.apply_voice(
    assembled_content,
    voice_config
)

# To:
assembled_content = self.voice_transformer.apply_voice(
    assembled_content,
    voice.rules
)
```

2. **Or set fallback-only mode**:
Remove ANTHROPIC_API_KEY from environment - transformer will automatically fallback to regex.

## Future Enhancements

1. **Caching** - Cache transformations for identical content+voice pairs
2. **Batch Processing** - Transform multiple sections in one API call
3. **A/B Testing** - Compare LLM vs regex quality
4. **Custom Prompts** - Allow brands to customize transformation prompts
5. **Multi-Model** - Use Haiku for speed, Sonnet for quality
6. **Analytics** - Track transformation quality metrics
