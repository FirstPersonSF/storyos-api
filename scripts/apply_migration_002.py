#!/usr/bin/env python3
"""
Apply Migration 002: Move to Public Schema

Uses Supabase client library since direct PostgreSQL connections are blocked
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

migration_file = Path(__file__).parent.parent / "migrations" / "002_public_schema.sql"

print("=" * 80)
print("APPLYING MIGRATION 002: PUBLIC SCHEMA")
print("=" * 80)

# Read migration SQL
print(f"\n📖 Reading migration from: {migration_file}")
with open(migration_file, 'r') as f:
    sql = f.read()

print(f"✅ Read {len(sql)} characters of SQL")

# Connect to Supabase
supabase_url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"\n🔗 Connecting to Supabase...")
print(f"URL: {supabase_url}")

try:
    supabase = create_client(supabase_url, service_key)
    print("✅ Connected to Supabase")

    # Execute SQL using Supabase RPC
    # Note: We need to split the SQL into individual statements
    # because PostgREST may not handle multi-statement batches well

    print("\n⚠️  IMPORTANT: Direct SQL execution via Supabase client may be limited.")
    print("Please apply this migration manually in the Supabase SQL Editor:")
    print(f"\n1. Go to: {supabase_url.replace('https://', 'https://supabase.com/dashboard/project/')}/editor")
    print("2. Open SQL Editor")
    print(f"3. Copy and paste the contents of: {migration_file}")
    print("4. Click 'Run'")
    print("\nAlternatively, if you have psql installed:")
    print(f"psql $DATABASE_URL < {migration_file}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
