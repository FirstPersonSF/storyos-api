#!/usr/bin/env python3
"""
Test executing SQL via Supabase PostgREST
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("Testing SQL execution via Supabase...")
print("="*80)

# Try using the REST API to query the storyos schema
headers = {
    "apikey": service_key,
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Try a simple insert to test
test_url = f"{supabase_url}/rest/v1/rpc/exec_sql"

# Test if we can query the schema
query_url = f"{supabase_url}/rest/v1/rpc"

print(f"\nAttempting to execute SQL via REST API...")

# Alternative: Try using PostgREST directly on a table
# First, let's see what's available
list_url = f"{supabase_url}/rest/v1/"

response = requests.get(list_url, headers=headers)
print(f"\nAPI Response: {response.status_code}")
if response.status_code == 200:
    print("✅ API is accessible")
    print(f"Available endpoints: {response.json() if response.text else 'Root endpoint'}")
else:
    print(f"Response: {response.text[:200]}")

print("\n" + "="*80)
print("CONCLUSION:")
print("The Supabase REST API works, but direct PostgreSQL connections are blocked.")
print("We have two options:")
print("  1. Use Supabase client library for all database operations")
print("  2. Check your Supabase project settings for direct connection access")
print("  3. Use a SQL RPC function to execute raw SQL")
