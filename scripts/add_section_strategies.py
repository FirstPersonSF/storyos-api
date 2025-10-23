#!/usr/bin/env python3
"""
Migration: Add section_strategies to Inverted Pyramid Story Model

This migration adds the missing section_strategies to the Inverted Pyramid story model
so that press releases render correctly with proper extraction strategies.
"""
import os
import sys
import ujson as json
from dotenv import load_dotenv

# Add parent directory to path to import storage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.supabase_storage import SupabaseStorage

# Load environment variables
load_dotenv()

INVERTED_PYRAMID_ID = "61369622-3222-43c3-9bd6-e95ad7838d72"

# Define proper section strategies for press release
SECTION_STRATEGIES = {
    "Headline": {
        "extraction_strategy": "key_message",
        "max_words": 10
    },
    "Lede": {
        "extraction_strategy": "five_ws"
    },
    "Key Facts": {
        "extraction_strategy": "structured_list",
        "format": "paragraph"
    },
    "Quote 1": {
        "extraction_strategy": "quote",
        "quote_number": 1
    },
    "Quote 2": {
        "extraction_strategy": "quote",
        "quote_number": 2
    },
    "Boilerplate": {
        "extraction_strategy": "full_content"
    }
}

def apply_migration():
    """Apply migration to add section_strategies"""
    print("=" * 80)
    print("Migration: Add section_strategies to Inverted Pyramid Story Model")
    print("=" * 80)
    print()

    # Initialize storage
    storage = SupabaseStorage()

    # Get current story model
    print(f"Fetching Inverted Pyramid story model (ID: {INVERTED_PYRAMID_ID})...")
    story_model = storage.get_one("story_models", INVERTED_PYRAMID_ID)

    if not story_model:
        print(f"❌ ERROR: Story model not found!")
        return False

    print(f"✅ Found story model: {story_model.get('name')}")

    # Check if section_strategies already exists
    current_strategies = story_model.get('section_strategies')
    if current_strategies:
        print(f"\n⚠️  Story model already has section_strategies:")
        print(json.dumps(current_strategies, indent=2))
        print("\nDo you want to overwrite? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("Migration aborted.")
            return False

    # Update with section_strategies
    print(f"\nAdding section_strategies...")
    success = storage.update_one(
        "story_models",
        INVERTED_PYRAMID_ID,
        {"section_strategies": SECTION_STRATEGIES}
    )

    if success:
        print("\n✅ Migration completed successfully!")
        print("\nSection Strategies added:")
        for section, strategy in SECTION_STRATEGIES.items():
            print(f"  • {section}: {strategy['extraction_strategy']}")

        print("\n" + "=" * 80)
        print("Next Steps:")
        print("  1. Refresh existing deliverables to see the changes")
        print("  2. Create new press release deliverables to test")
        print("=" * 80)
        return True
    else:
        print("\n❌ Migration failed!")
        return False


if __name__ == "__main__":
    try:
        success = apply_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
