"""
Test all sections to verify meta-commentary is removed and Headline renders
"""
import requests
import json

# Create a test deliverable
deliverable_data = {
    "template_id": "f8c2bb37-a26a-42d3-8c69-d568aeefba45",  # Press Release template from dummy data
    "name": "Test All Sections - Verify Fixes",
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
print("TESTING ALL SECTIONS - VERIFY FIXES")
print("=" * 80)

response = requests.post("http://localhost:8000/deliverables", json=deliverable_data)

if response.status_code == 201:
    deliverable = response.json()

    print(f"\n✓ Deliverable created successfully: {deliverable['id']}")

    # Get rendered content - could be dict or string
    rendered_raw = deliverable.get('rendered_content', {})

    # Convert to string for checking
    if isinstance(rendered_raw, dict):
        rendered = json.dumps(rendered_raw, indent=2)
    else:
        rendered = str(rendered_raw)

    # Check for meta-commentary issues
    meta_issues = []
    if "Here's the transformed content" in rendered:
        meta_issues.append("'Here's the transformed content' found")
    if "Transformed Content" in rendered:
        meta_issues.append("'Transformed Content' header found")
    if "Key Transformation Notes" in rendered:
        meta_issues.append("'Key Transformation Notes' found")
    if " v1.1" in rendered or " v1.2" in rendered:
        meta_issues.append("Version numbers found")
    if "UPDATED VERSION" in rendered:
        meta_issues.append("'UPDATED VERSION' found")
    if "UPDATED CONTENT" in rendered:
        meta_issues.append("'UPDATED CONTENT' found")
    if "STRATEGIC RELEASE" in rendered:
        meta_issues.append("'STRATEGIC RELEASE' found")
    if "I apologize" in rendered:
        meta_issues.append("LLM apology/error found")
    if "incomplete or truncated" in rendered:
        meta_issues.append("'incomplete or truncated' error found")

    # Print results
    print("\n" + "=" * 80)
    print("META-COMMENTARY CHECK")
    print("=" * 80)

    if meta_issues:
        print("\n✗ FOUND META-COMMENTARY ISSUES:")
        for issue in meta_issues:
            print(f"  - {issue}")
    else:
        print("\n✓ NO META-COMMENTARY FOUND!")

    # Show first 2000 chars of rendered content
    print("\n" + "=" * 80)
    print("RENDERED CONTENT (first 2000 chars)")
    print("=" * 80)
    print(rendered[:2000])

    if len(rendered) > 2000:
        print(f"\n... (showing 2000 of {len(rendered)} total chars)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if not meta_issues and len(rendered) > 500:
        print("✓ SUCCESS: Content renders without meta-commentary!")
    elif meta_issues:
        print("✗ PARTIAL SUCCESS: Meta-commentary still present")
    else:
        print("✗ FAILURE: Content too short or missing")

else:
    print(f"\n✗ Failed to create deliverable: {response.status_code}")
    print(response.text)
