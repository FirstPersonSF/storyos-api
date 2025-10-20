#!/usr/bin/env python3
"""
Apply database migrations to Supabase PostgreSQL

Usage:
    python scripts/apply_migration.py migrations/001_initial_schema.sql
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

def get_database_url() -> str:
    """Get PostgreSQL connection URL from Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url:
        raise ValueError("SUPABASE_URL not set in .env")

    # Extract project ID from URL
    # Format: https://PROJECT_ID.supabase.co
    project_id = supabase_url.split('//')[1].split('.')[0]

    # Try to get DATABASE_URL from env, or construct it
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("⚠️  DATABASE_URL not set in .env")
        print("Please get your database password from Supabase dashboard:")
        print(f"  1. Go to {supabase_url}")
        print("  2. Settings → Database → Connection string")
        print("  3. Copy the password")
        password = input("Enter database password: ").strip()
        db_url = f"postgresql://postgres.{project_id}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    return db_url

def apply_migration(migration_file: Path):
    """Apply a SQL migration file"""
    print(f"📄 Reading migration: {migration_file.name}")

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    sql = migration_file.read_text()

    print(f"🔗 Connecting to Supabase...")
    db_url = get_database_url()

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                print(f"✅ Connected successfully")
                print(f"🔨 Applying migration...")

                # Execute the migration
                cur.execute(sql)
                conn.commit()

                print(f"✅ Migration applied successfully!")

                # Verify schema
                print(f"\n📊 Verifying schema...")
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'storyos'
                    ORDER BY table_name
                """)
                tables = cur.fetchall()

                print(f"\n✅ Created {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table[0]}")

    except psycopg.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/apply_migration.py migrations/001_initial_schema.sql")
        sys.exit(1)

    migration_file = Path(sys.argv[1])
    apply_migration(migration_file)

if __name__ == "__main__":
    main()
