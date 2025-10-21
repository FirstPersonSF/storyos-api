"""
Apply Migration 003: Add voice rules and story model strategies

Uses Supabase Python client to run SQL via REST API
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("=" * 80)
print("MIGRATION 003: Add Phase 2 Columns")
print("=" * 80)

# Read migration SQL
with open('migrations/003_add_voice_rules.sql', 'r') as f:
    sql = f.read()

print("\nSQL to execute:")
print(sql)

try:
    # Execute SQL via Supabase RPC
    print("\nExecuting migration...")

    # Note: Supabase Python client doesn't have direct SQL execution
    # We'll use the Supabase SQL editor manually or direct psycopg connection
    print("⚠️  This migration requires manual execution via Supabase SQL Editor")
    print("\n📋 Steps:")
    print("1. Go to: https://supabase.com/dashboard/project/eobjopjhnajmnkprbsuw/sql")
    print("2. Paste the SQL from migrations/003_add_voice_rules.sql")
    print("3. Click 'Run'")
    print("\nOR run this SQL directly:")
    print("-" * 80)
    print(sql)
    print("-" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
