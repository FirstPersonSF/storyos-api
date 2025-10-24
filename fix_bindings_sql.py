"""
Fix template bindings using direct SQL execution
"""
import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

# Load environment
load_dotenv()

# Get DATABASE_URL
db_url = os.getenv('DATABASE_URL')

print("=" * 80)
print("UPDATING TEMPLATE BINDINGS VIA SQL")
print("=" * 80)

# SQL to update bindings
update_sql = """
-- Update Lede binding to use Vision Statement v1.5
UPDATE public.template_section_bindings
SET element_ids = ARRAY['5882a148-cdd6-4a39-a718-1ca36ccdfcfc'::uuid]
WHERE template_id = '06c9b4bd-c188-475f-b972-dc1e92998cfb'::uuid
  AND section_name = 'Lede';

-- Update Boilerplate binding to use Boilerplate v1.5
UPDATE public.template_section_bindings
SET element_ids = ARRAY['e19ab470-1f95-4759-abe4-df7fe95353f2'::uuid]
WHERE template_id = '06c9b4bd-c188-475f-b972-dc1e92998cfb'::uuid
  AND section_name = 'Boilerplate';
"""

verify_sql = """
SELECT
    section_name,
    element_ids,
    (SELECT name || ' v' || version || ' (' || status || ')'
     FROM public.unf_elements
     WHERE id = element_ids[1]) as element_info
FROM public.template_section_bindings
WHERE template_id = '06c9b4bd-c188-475f-b972-dc1e92998cfb'::uuid
  AND section_name IN ('Lede', 'Boilerplate')
ORDER BY section_name;
"""

try:
    # Connect and execute
    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            print("\n[1] Executing UPDATE statements...")
            cur.execute(update_sql)
            conn.commit()
            print("✓ Updates committed")

            print("\n[2] Verifying updates...")
            cur.execute(verify_sql)
            results = cur.fetchall()

            print("\n" + "=" * 80)
            print("VERIFICATION RESULTS")
            print("=" * 80)

            for row in results:
                print(f"\n[{row['section_name']}]")
                print(f"  element_ids: {row['element_ids']}")
                print(f"  Element: {row['element_info']}")

                if '(approved)' in row['element_info']:
                    print("  ✓ Element is approved")
                else:
                    print(f"  ✗ WARNING: Element is not approved")

    print("\n" + "=" * 80)
    print("✓ Binding update complete!")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
