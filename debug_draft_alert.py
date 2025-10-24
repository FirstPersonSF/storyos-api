"""
Debug script to understand why draft alerts aren't being generated
"""
import requests
import json

print("=" * 80)
print("DEBUG: Draft Alert Detection")
print("=" * 80)

# Step 1: Create a deliverable with Vision Statement v1.0
print("\nStep 1: Get Vision Statement element...")
elements_response = requests.get("http://localhost:8000/unf/elements")
elements = elements_response.json()

vision_elements = [e for e in elements if e['name'] == 'Vision Statement']
if not vision_elements:
    print("✗ No Vision Statement element found!")
    exit(1)

vision_v1 = vision_elements[0]
print(f"✓ Found Vision Statement: {vision_v1['id']} v{vision_v1['version']} ({vision_v1['status']})")

# Step 2: Create deliverable using Vision Statement
print("\nStep 2: Create deliverable with Vision Statement...")
templates_response = requests.get("http://localhost:8000/deliverable-templates")
templates = templates_response.json()
manifesto_template = next(t for t in templates if t['name'] == 'Manifesto')

deliverable_response = requests.post("http://localhost:8000/deliverables", json={
    "name": "Debug Test - Draft Alert",
    "template_id": manifesto_template['id'],
    "instance_data": {"test": "data"}
})

if deliverable_response.status_code != 201:
    print(f"✗ Failed to create deliverable: {deliverable_response.text}")
    exit(1)

deliverable = deliverable_response.json()
print(f"✓ Deliverable created: {deliverable['id']}")
print(f"  Element versions: {json.dumps(deliverable['element_versions'], indent=2)}")

# Step 3: Update Vision Statement to draft v1.1
print("\nStep 3: Update Vision Statement to v1.1 (draft)...")
update_response = requests.put(
    f"http://localhost:8000/unf/elements/{vision_v1['id']}",
    json={
        "content": f"{vision_v1['content']}\n\nDRAFT UPDATE v1.1 - Under review.",
        "status": "draft"
    }
)

if update_response.status_code != 200:
    print(f"✗ Failed to update element: {update_response.text}")
    exit(1)

updated_vision = update_response.json()
print(f"✓ Vision Statement updated: {updated_vision['id']} v{updated_vision['version']} ({updated_vision['status']})")

# Step 4: Check all Vision Statement elements
print("\nStep 4: Check all Vision Statement elements in database...")
elements_response = requests.get("http://localhost:8000/unf/elements")
all_elements = elements_response.json()
all_vision = [e for e in all_elements if e['name'] == 'Vision Statement']

print(f"Found {len(all_vision)} Vision Statement elements:")
for e in all_vision:
    print(f"  - ID: {e['id']}, v{e['version']}, status: {e['status']}")

# Step 5: Check for alerts
print("\nStep 5: Check for draft alerts...")
alerts_response = requests.get(f"http://localhost:8000/deliverables/{deliverable['id']}/with-alerts")

if alerts_response.status_code != 200:
    print(f"✗ Failed to get alerts: {alerts_response.text}")
    exit(1)

with_alerts = alerts_response.json()
print(f"has_updates: {with_alerts['has_updates']}")
print(f"alerts count: {len(with_alerts['alerts'])}")

if with_alerts['alerts']:
    for alert in with_alerts['alerts']:
        print(f"\n  Alert:")
        print(f"    element_name: {alert['element_name']}")
        print(f"    status: {alert['status']}")
        print(f"    old_version: {alert['old_version']}")
        print(f"    new_version: {alert['new_version']}")
else:
    print("  ✗ NO ALERTS FOUND!")

    # Debug: manually check what the service sees
    print("\n  Debugging deliverable.element_versions:")
    for elem_id, version in deliverable['element_versions'].items():
        print(f"    {elem_id}: {version}")

        # Get this element
        elem_response = requests.get(f"http://localhost:8000/unf/elements/{elem_id}")
        if elem_response.status_code == 200:
            elem = elem_response.json()
            print(f"      -> name: {elem['name']}, status: {elem['status']}")

            # Check for newer versions with same name
            matching = [e for e in all_elements if e['name'] == elem['name'] and e['id'] != elem_id]
            print(f"      -> found {len(matching)} other elements with same name:")
            for m in matching:
                print(f"         - {m['id']} v{m['version']} ({m['status']})")

print("\n" + "=" * 80)
