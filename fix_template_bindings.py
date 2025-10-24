"""Fix template bindings to use latest approved elements"""
import requests

# Template ID
template_id = "06c9b4bd-c188-475f-b972-dc1e92998cfb"

# Get current bindings
bindings = requests.get(f"http://localhost:8000/templates/{template_id}/bindings").json()

# New approved element IDs
new_vision_id = "5882a148-cdd6-4a39-a718-1ca36ccdfcfc"  # v1.5
new_boilerplate_id = "e19ab470-1f95-4759-abe4-df7fe95353f2"  # v1.5

print("Current bindings:")
for b in bindings:
    print(f"  {b['section_name']}: {b['element_ids']}")

# Update bindings for Lede and Boilerplate
for binding in bindings:
    if binding['section_name'] == 'Lede':
        print(f"\nUpdating Lede binding:")
        print(f"  Old: {binding['element_ids']}")
        binding['element_ids'] = [new_vision_id]
        print(f"  New: {binding['element_ids']}")

        # Update via API
        response = requests.put(
            f"http://localhost:8000/templates/{template_id}/bindings/{binding['id']}",
            json={"element_ids": [new_vision_id]}
        )
        print(f"  Status: {response.status_code}")

    elif binding['section_name'] == 'Boilerplate':
        print(f"\nUpdating Boilerplate binding:")
        print(f"  Old: {binding['element_ids']}")
        binding['element_ids'] = [new_boilerplate_id]
        print(f"  New: {binding['element_ids']}")

        # Update via API
        response = requests.put(
            f"http://localhost:8000/templates/{template_id}/bindings/{binding['id']}",
            json={"element_ids": [new_boilerplate_id]}
        )
        print(f"  Status: {response.status_code}")

print("\nDone!")
