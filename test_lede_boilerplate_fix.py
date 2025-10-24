"""
Test script to verify Lede and Boilerplate sections now render correctly
"""
import requests
import json

# Create a test deliverable
deliverable_data = {
    "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
    "name": "Test Deliverable - Verify Lede/Boilerplate Fix",
    "instance_data": {
        "who": "Hexagon AB",
        "what": "announces breakthrough in manufacturing intelligence platform",
        "when": "January 15, 2024",
        "where": "Stockholm, Sweden",
        "why": "to help manufacturers increase precision and reduce waste",
        "quote1_speaker": "Paolo Guglielmini",
        "quote1_title": "President, Hexagon Manufacturing Intelligence",
        "quote1_content": "This breakthrough represents a fundamental shift."
    }
}

print("=" * 80)
print("TESTING LEDE/BOILERPLATE FIX")
print("=" * 80)

response = requests.post("http://localhost:8000/deliverables", json=deliverable_data)

if response.status_code == 201:
    deliverable = response.json()

    print(f"\n✓ Deliverable created successfully: {deliverable['id']}")
    print(f"\nName: {deliverable['name']}")
    print(f"\nResponse keys: {list(deliverable.keys())}")

    # Check Lede section
    print("\n" + "=" * 80)
    print("LEDE SECTION")
    print("=" * 80)
    lede = deliverable['rendered_sections'].get('Lede', '')
    print(f"Length: {len(lede)} chars")
    if lede:
        print(f"Content:\n{lede}")
        print("\n✓ Lede section is NOT empty!")
    else:
        print("✗ Lede section is STILL empty!")

    # Check Boilerplate section
    print("\n" + "=" * 80)
    print("BOILERPLATE SECTION")
    print("=" * 80)
    boilerplate = deliverable['rendered_sections'].get('Boilerplate', '')
    print(f"Length: {len(boilerplate)} chars")
    if boilerplate:
        print(f"Content:\n{boilerplate}")
        print("\n✓ Boilerplate section is NOT empty!")
    else:
        print("✗ Boilerplate section is STILL empty!")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if lede and boilerplate:
        print("✓ SUCCESS: Both Lede and Boilerplate sections are now rendering correctly!")
    else:
        print("✗ FAILURE: One or both sections are still empty")

else:
    print(f"\n✗ Failed to create deliverable: {response.status_code}")
    print(response.text)
