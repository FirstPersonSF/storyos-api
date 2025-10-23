"""
Apply migration 004: Add deliverable versioning
"""
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("MIGRATION 004: Add Deliverable Versioning")
print("=" * 80)

# Read migration SQL
with open('migrations/004_add_deliverable_versioning.sql', 'r') as f:
    sql = f.read()

print("\nSQL to execute:")
print(sql)

print("\nApplying migration to Railway database...")
try:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        exit(1)

    # Run migration using psql
    result = subprocess.run(
        ['psql', database_url, '-f', 'migrations/004_add_deliverable_versioning.sql'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Migration 004 applied successfully!")
        print("\nOutput:")
        print(result.stdout)
    else:
        print("❌ Error applying migration:")
        print(result.stderr)
        exit(1)

except FileNotFoundError:
    print("❌ psql not found. Install PostgreSQL client tools or run migration manually")
    print("\nManual steps:")
    print("1. Go to Railway database dashboard")
    print("2. Open SQL Query editor")
    print("3. Paste the SQL from migrations/004_add_deliverable_versioning.sql")
    print("4. Click 'Run'")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
