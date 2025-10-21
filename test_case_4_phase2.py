"""
Test Case 4: Phase 2 Voice Transformation Verification

This test creates the SAME deliverable with DIFFERENT voices to verify
that Phase 2 voice transformation rules are being applied correctly.
"""
from storage.supabase_storage import SupabaseStorage
from services.deliverable_service import DeliverableService
from services.unf_service import UNFService
from services.voice_service import VoiceService
from services.story_model_service import StoryModelService
from services.template_service import TemplateService
from services.relationship_service import PostgresRelationshipService
from models.deliverables import DeliverableCreate, DeliverableStatus
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize storage
storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Initialize services
unf_service = UNFService(storage)
voice_service = VoiceService(storage)
story_model_service = StoryModelService(storage)
template_service = TemplateService(storage)
relationship_service = PostgresRelationshipService(storage)
deliverable_service = DeliverableService(
    storage,
    unf_service,
    voice_service,
    template_service,
    story_model_service,
    relationship_service
)

print("=" * 80)
print("TEST CASE 4: Phase 2 Voice Transformation Verification")
print("=" * 80)

# Step 1: Get voices
print("\n[Step 1] Getting voices...")
voices = storage.get_many('brand_voices')
corporate_voice = next((v for v in voices if 'Corporate' in v['name']), None)
product_voice = next((v for v in voices if 'Product' in v['name']), None)

if not corporate_voice or not product_voice:
    print("❌ FAIL: Voices not found")
    exit(1)

print(f"✅ Found Corporate Voice: {corporate_voice['id']}")
print(f"✅ Found Product Voice: {product_voice['id']}")

# Verify voices have rules
corporate_rules = corporate_voice.get('rules')
product_rules = product_voice.get('rules')

if isinstance(corporate_rules, str):
    corporate_rules = json.loads(corporate_rules)
if isinstance(product_rules, str):
    product_rules = json.loads(product_rules)

print(f"\nCorporate Voice has rules: {'✅ YES' if corporate_rules else '❌ NO'}")
print(f"Product Voice has rules: {'✅ YES' if product_rules else '❌ NO'}")

if not corporate_rules or not product_rules:
    print("\n⚠️  WARNING: Voice rules missing. Run scripts/add_voice_rules.py")
    exit(1)

# Step 2: Get template
print("\n[Step 2] Getting Brand Manifesto template...")
templates = storage.get_many('deliverable_templates')
brand_manifesto = next((t for t in templates if 'Brand Manifesto' in t['name']), None)

if not brand_manifesto:
    print("❌ FAIL: Brand Manifesto template not found")
    exit(1)

print(f"✅ Found template: {brand_manifesto['id']}")

# Step 3: Create deliverable with CORPORATE voice
print("\n[Step 3] Creating deliverable with Corporate Voice...")
try:
    corporate_deliverable_data = DeliverableCreate(
        name="Test Phase 2: Corporate Voice Transformation",
        template_id=brand_manifesto['id'],
        voice_id=corporate_voice['id'],
        instance_data={},
        status=DeliverableStatus.DRAFT
    )

    corporate_deliverable = deliverable_service.create_deliverable(corporate_deliverable_data)
    print(f"✅ Created deliverable: {corporate_deliverable.id}")

except Exception as e:
    print(f"❌ FAIL: Error creating deliverable: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Create deliverable with PRODUCT voice
print("\n[Step 4] Creating deliverable with Product Voice...")
try:
    product_deliverable_data = DeliverableCreate(
        name="Test Phase 2: Product Voice Transformation",
        template_id=brand_manifesto['id'],
        voice_id=product_voice['id'],
        instance_data={},
        status=DeliverableStatus.DRAFT
    )

    product_deliverable = deliverable_service.create_deliverable(product_deliverable_data)
    print(f"✅ Created deliverable: {product_deliverable.id}")

except Exception as e:
    print(f"❌ FAIL: Error creating deliverable: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 5: Compare content
print("\n[Step 5] Comparing rendered content...")

corporate_content = corporate_deliverable.rendered_content
product_content = product_deliverable.rendered_content

print("\n" + "=" * 80)
print("CORPORATE VOICE OUTPUT:")
print("=" * 80)
for section, content in corporate_content.items():
    print(f"\n{section}:")
    print(content[:300] if len(content) > 300 else content)
    print("...")

print("\n" + "=" * 80)
print("PRODUCT VOICE OUTPUT:")
print("=" * 80)
for section, content in product_content.items():
    print(f"\n{section}:")
    print(content[:300] if len(content) > 300 else content)
    print("...")

# Step 6: Verify transformations
print("\n" + "=" * 80)
print("TRANSFORMATION VERIFICATION")
print("=" * 80)

differences_found = False

for section in corporate_content.keys():
    corp_text = corporate_content[section]
    prod_text = product_content[section]

    if corp_text != prod_text:
        differences_found = True
        print(f"\n✅ {section}: Content DIFFERS (voice transformation working)")

        # Check for specific transformations
        if "Hexagon AB" in corp_text and "we" in prod_text.lower():
            print("   ✅ Detected perspective shift: 'Hexagon AB' → 'we'")

        if "autonomous technologies" in corp_text and "smart automation" in prod_text:
            print("   ✅ Detected terminology: 'autonomous technologies' → 'smart automation'")

        if "digital reality solutions" in corp_text and "smart digital tools" in prod_text:
            print("   ✅ Detected terminology: 'digital reality solutions' → 'smart digital tools'")

    else:
        print(f"\n⚠️  {section}: Content IDENTICAL (no transformation applied)")

# Results Summary
print("\n" + "=" * 80)
print("TEST RESULTS SUMMARY")
print("=" * 80)

if differences_found:
    print("\n✅ PHASE 2 VOICE TRANSFORMATION: WORKING")
    print("   - Same source content produced different outputs")
    print("   - Corporate Voice: Formal, third-person, brand terminology")
    print("   - Product Voice: Casual, first-person, simplified terms")
else:
    print("\n❌ PHASE 2 VOICE TRANSFORMATION: NOT WORKING")
    print("   - Same content produced identical outputs")
    print("   - Voice rules may not be applied correctly")

print("\n📊 VERIFICATION:")
print(f"   Corporate Voice has rules: {bool(corporate_rules)}")
print(f"   Product Voice has rules: {bool(product_rules)}")
print(f"   Content differs: {differences_found}")
print(f"   Transformation pipeline: {'✅ ACTIVE' if differences_found else '❌ INACTIVE'}")

print("\n" + "=" * 80)
