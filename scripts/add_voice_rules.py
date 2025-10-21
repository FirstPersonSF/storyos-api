"""
Add Phase 2 Voice Rules to Brand Voices

This script adds transformation rules to the existing Corporate and Product voices.
"""
from storage.supabase_storage import SupabaseStorage
import os
from dotenv import load_dotenv
import json

load_dotenv()

storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("ADDING VOICE TRANSFORMATION RULES")
print("=" * 80)

# Get existing voices
voices = storage.get_many('brand_voices')

corporate_voice = next((v for v in voices if 'Corporate' in v['name']), None)
product_voice = next((v for v in voices if 'Product' in v['name']), None)

if not corporate_voice or not product_voice:
    print("❌ Could not find Corporate or Product voices")
    exit(1)

print(f"\n✅ Found Corporate Voice: {corporate_voice['id']}")
print(f"✅ Found Product Voice: {product_voice['id']}")

# Corporate Voice Rules (formal, third-person, brand terminology)
corporate_rules = {
    "lexicon": {
        "company_reference": {
            "generic": ["the company", "the organization", "we"],
            "branded": "Hexagon AB"
        },
        "product_reference": {
            "generic": ["the product", "the solution", "our platform"],
            "branded": "HxGN Precision One"
        }
    },
    "terminology": {
        "preferred_terms": {
            "digital transformation": "digital reality solutions",
            "automation": "autonomous technologies",
            "data analytics": "sensor and software technologies",
            "AI": "autonomous technologies",
            "smart manufacturing": "precision manufacturing"
        }
    },
    "tone_rules": [
        {
            "type": "formality",
            "level": "formal",
            "patterns": {}
        },
        {
            "type": "perspective",
            "value": "third_person",
            "company_name": "Hexagon AB"
        }
    ]
}

# Product Voice Rules (casual, first-person, simplified terms)
product_rules = {
    "lexicon": {
        "company_reference": {
            "generic": ["the company", "the organization", "Hexagon AB"],
            "branded": "we"
        },
        "product_reference": {
            "generic": ["the product", "the solution"],
            "branded": "HxGN Precision One"
        }
    },
    "terminology": {
        "preferred_terms": {
            "digital transformation": "smart digital tools",
            "automation": "smart automation",
            "autonomous technologies": "smart automation",
            "data analytics": "data insights",
            "sensor and software technologies": "smart sensors and software"
        }
    },
    "tone_rules": [
        {
            "type": "formality",
            "level": "casual",
            "patterns": {}
        },
        {
            "type": "perspective",
            "value": "first_person"
        }
    ]
}

# Update Corporate Voice
print("\n[Step 1] Updating Corporate Brand Voice with rules...")
try:
    storage.update_one(
        'brand_voices',
        corporate_voice['id'],
        {'rules': json.dumps(corporate_rules)}
    )
    print("✅ Corporate Voice rules added")
    print(f"   - Lexicon: {len(corporate_rules['lexicon'])} categories")
    print(f"   - Terminology: {len(corporate_rules['terminology']['preferred_terms'])} terms")
    print(f"   - Tone: {len(corporate_rules['tone_rules'])} rules")
except Exception as e:
    print(f"❌ Error updating Corporate Voice: {e}")
    import traceback
    traceback.print_exc()

# Update Product Voice
print("\n[Step 2] Updating Product Division Voice with rules...")
try:
    storage.update_one(
        'brand_voices',
        product_voice['id'],
        {'rules': json.dumps(product_rules)}
    )
    print("✅ Product Voice rules added")
    print(f"   - Lexicon: {len(product_rules['lexicon'])} categories")
    print(f"   - Terminology: {len(product_rules['terminology']['preferred_terms'])} terms")
    print(f"   - Tone: {len(product_rules['tone_rules'])} rules")
except Exception as e:
    print(f"❌ Error updating Product Voice: {e}")
    import traceback
    traceback.print_exc()

# Verify
print("\n[Step 3] Verifying voice rules...")
voices_updated = storage.get_many('brand_voices')

for v in voices_updated:
    if 'Corporate' in v['name'] or 'Product' in v['name']:
        rules = v.get('rules')
        if rules:
            if isinstance(rules, str):
                rules = json.loads(rules)
            print(f"\n✅ {v['name']} rules verified:")
            print(f"   - Has lexicon: {'lexicon' in rules}")
            print(f"   - Has terminology: {'terminology' in rules}")
            print(f"   - Has tone_rules: {'tone_rules' in rules}")
        else:
            print(f"\n❌ {v['name']} has no rules")

print("\n" + "=" * 80)
print("VOICE RULES ADDED SUCCESSFULLY")
print("=" * 80)

print("\nPhase 2 voice transformation is now active!")
print("New deliverables will use these rules to transform content.")
