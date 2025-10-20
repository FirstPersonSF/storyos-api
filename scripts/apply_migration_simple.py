#!/usr/bin/env python3
"""
Apply database migration using Supabase REST API

This is simpler than direct psycopg connection for initial setup
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv()

def apply_migration(migration_file: Path):
    """Apply SQL migration via Supabase"""
    print(f"📄 Reading migration: {migration_file.name}")

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    sql = migration_file.read_text()

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_role_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)

    print(f"🔗 Connecting to Supabase at {supabase_url}...")

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, service_role_key)
        print(f"✅ Connected successfully")

        # Note: We'll need to execute raw SQL via RPC or direct connection
        # For now, let's provide instructions for manual execution

        print("\n" + "="*80)
        print("📋 MIGRATION SQL READY")
        print("="*80)
        print("\nTo apply this migration, please:")
        print(f"1. Go to: {supabase_url}/project/default/sql")
        print(f"2. Copy and paste the SQL from: {migration_file}")
        print("3. Click 'Run'")
        print("\nOr, you can copy the SQL below:\n")
        print("="*80)
        print(sql[:500])  # Show first 500 chars
        print("\n... (see full SQL in migration file)")
        print("="*80)

        # Ask if they want the full SQL printed
        response = input("\nPrint full SQL to console? (y/n): ").strip().lower()
        if response == 'y':
            print("\n" + "="*80)
            print("FULL MIGRATION SQL")
            print("="*80)
            print(sql)
            print("="*80)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/apply_migration_simple.py migrations/001_initial_schema.sql")
        sys.exit(1)

    migration_file = Path(sys.argv[1])
    apply_migration(migration_file)

if __name__ == "__main__":
    main()
