"""
Workflow Sequence Tests - End-to-End Integration Tests

These tests validate the 6 core workflow sequences defined in the
dummy data specification. Each test builds on the previous functionality
to ensure the complete system works as expected.

Run with real LLM (default, costs ~$0.10):
    pytest tests/integration/test_workflow_sequences.py

Run with mocked LLM (free, instant):
    pytest tests/integration/test_workflow_sequences.py --mock-llm

Run specific test:
    pytest tests/integration/test_workflow_sequences.py::TestSequence01
"""
import pytest
from tests.conftest import assert_deliverable_structure, assert_alert_structure


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence01:
    """
    Test Sequence 01: Generate Deliverables with Corporate Voice v1.0

    Creates three deliverables (Press Release, Blog Post, Manifesto)
    using Corporate Voice v1.0 and validates structure and content.
    """

    def test_01_create_press_release(self, api_client, test_data, cleanup_deliverables):
        """Create Press Release with Corporate Voice v1.0"""
        print("\n" + "="*80)
        print("TEST 01A: Create Press Release with Corporate Voice v1.0")
        print("="*80)

        response = api_client.post("/deliverables", json={
            "name": "Sequence Test 01 - Press Release",
            "template_id": test_data['press_release_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "who": "Hexagon AB",
                "what": "announces breakthrough in manufacturing intelligence platform",
                "when": "January 15, 2024",
                "where": "Stockholm, Sweden",
                "why": "to help manufacturers increase precision and reduce waste",
                "quote1_speaker": "Paolo Guglielmini",
                "quote1_title": "President, Hexagon Manufacturing Intelligence",
                "quote1_content": "This breakthrough represents a fundamental shift in how manufacturers approach precision and efficiency."
            }
        })

        assert response.status_code == 201, f"Failed to create deliverable: {response.text}"
        deliverable = response.json()

        # Track for cleanup
        cleanup_deliverables.track(deliverable['id'])

        # Validate structure
        assert_deliverable_structure(deliverable)

        # Validate specific fields
        assert deliverable['name'] == "Sequence Test 01 - Press Release"
        assert deliverable['voice_id'] == test_data['corporate_voice']['id']
        assert deliverable['status'] == 'draft'
        assert deliverable['version'] == 1
        assert deliverable['prev_deliverable_id'] is None

        # Validate rendered content exists
        assert 'rendered_content' in deliverable
        assert isinstance(deliverable['rendered_content'], dict)
        assert len(deliverable['rendered_content']) > 0

        # Validate element versions tracked
        assert 'element_versions' in deliverable
        assert isinstance(deliverable['element_versions'], dict)
        assert len(deliverable['element_versions']) > 0

        print("✅ Press Release created successfully")
        print(f"   ID: {deliverable['id']}")
        print(f"   Sections rendered: {list(deliverable['rendered_content'].keys())}")
        print(f"   Elements used: {len(deliverable['element_versions'])}")

    def test_01_create_blog_post(self, api_client, test_data, cleanup_deliverables):
        """Create Blog Post with Corporate Voice v1.0 (if template exists)"""
        print("\n" + "="*80)
        print("TEST 01B: Create Blog Post with Corporate Voice v1.0")
        print("="*80)

        if not test_data['blog_post_template']:
            pytest.skip("Blog Post template not found - skipping test")

        response = api_client.post("/deliverables", json={
            "name": "Sequence Test 01 - Blog Post",
            "template_id": test_data['blog_post_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "title": "The Future of Digital Manufacturing",
                "author": "Hexagon Engineering Team",
                "date": "2024-01-15"
            }
        })

        assert response.status_code == 201, f"Failed to create blog post: {response.text}"
        deliverable = response.json()

        cleanup_deliverables.track(deliverable['id'])
        assert_deliverable_structure(deliverable)

        assert deliverable['name'] == "Sequence Test 01 - Blog Post"
        print("✅ Blog Post created successfully")

    def test_01_create_manifesto(self, api_client, test_data, cleanup_deliverables):
        """Create Manifesto with Corporate Voice v1.0 (if template exists)"""
        print("\n" + "="*80)
        print("TEST 01C: Create Manifesto with Corporate Voice v1.0")
        print("="*80)

        if not test_data['manifesto_pas_template']:
            pytest.skip("Manifesto (PAS) template not found - skipping test")

        response = api_client.post("/deliverables", json={
            "name": "Sequence Test 01 - Manifesto (PAS)",
            "template_id": test_data['manifesto_pas_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "company_name": "Hexagon AB",
                "year": "2024"
            }
        })

        assert response.status_code == 201, f"Failed to create manifesto: {response.text}"
        deliverable = response.json()

        cleanup_deliverables.track(deliverable['id'])
        assert_deliverable_structure(deliverable)

        assert deliverable['name'] == "Sequence Test 01 - Manifesto (PAS)"
        print("✅ Manifesto created successfully")


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence02:
    """
    Test Sequence 02: Switch Press Release to Product Voice v1.0

    Tests voice switching functionality by creating a deliverable with
    Corporate Voice, then updating it to use Product Voice.
    """

    def test_02_voice_switching(self, api_client, test_data, cleanup_deliverables):
        """Test switching voice on existing deliverable"""
        print("\n" + "="*80)
        print("TEST 02: Switch Press Release from Corporate to Product Voice")
        print("="*80)

        # Step 1: Create deliverable with Corporate Voice
        print("\n📝 Step 1: Create Press Release with Corporate Voice...")
        create_response = api_client.post("/deliverables", json={
            "name": "Sequence Test 02 - Press Release (Voice Switch)",
            "template_id": test_data['press_release_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "who": "Hexagon AB",
                "what": "launches new innovation platform for smart factories",
                "when": "January 16, 2024",
                "where": "Stockholm, Sweden",
                "why": "to enable digital transformation in manufacturing",
                "quote1_speaker": "Ola Rollén",
                "quote1_title": "CEO, Hexagon AB",
                "quote1_content": "This platform will redefine how manufacturers operate in the digital age."
            }
        })

        assert create_response.status_code == 201
        original = create_response.json()
        cleanup_deliverables.track(original['id'])

        print(f"✅ Created deliverable with Corporate Voice")
        print(f"   ID: {original['id']}")
        print(f"   Version: {original['version']}")
        print(f"   Voice: {test_data['corporate_voice']['name']}")

        # Step 2: Get with alerts (should be none yet)
        print("\n📝 Step 2: Check for alerts (should be none)...")
        alerts_response = api_client.get(f"/deliverables/{original['id']}/with-alerts")
        assert alerts_response.status_code == 200
        with_alerts = alerts_response.json()

        assert with_alerts['has_updates'] == False
        assert len(with_alerts['alerts']) == 0
        print("✅ No alerts as expected")

        # Step 3: Switch to Product Voice
        print(f"\n📝 Step 3: Switch to Product Voice...")
        update_response = api_client.put(f"/deliverables/{original['id']}", json={
            "voice_id": test_data['product_voice']['id']
        })

        assert update_response.status_code == 200, f"Failed to update voice: {update_response.text}"
        updated = update_response.json()

        print("✅ Voice switch completed")

        # Step 4: Validate changes
        print("\n📝 Step 4: Validate voice switch...")

        # Verify voice changed
        assert updated['voice_id'] == test_data['product_voice']['id']

        # Verify new version created
        assert updated['version'] == original['version'] + 1
        assert updated['version'] == 2

        # Verify version chain
        assert updated['prev_deliverable_id'] == original['id']

        # Verify content was re-rendered
        # (content should differ because voice transformation changes it)
        assert updated['rendered_content'] != original['rendered_content']

        print(f"✅ Voice switched successfully")
        print(f"   Old voice: {test_data['corporate_voice']['name']}")
        print(f"   New voice: {test_data['product_voice']['name']}")
        print(f"   Old version: {original['version']}")
        print(f"   New version: {updated['version']}")
        print(f"   Linked via prev_deliverable_id: {updated['prev_deliverable_id'] == original['id']}")


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence03:
    """
    Test Sequence 03: Update Boilerplate to v1.1 and Test Refresh

    Tests update detection and refresh flow:
    1. Create deliverable with boilerplate v1.0
    2. Update boilerplate element to v1.1 (approved)
    3. Check for "update_available" alert
    4. Refresh deliverable with new boilerplate
    """

    def test_03_update_and_refresh(self, api_client, test_data, cleanup_deliverables, cleanup_elements):
        """Test update detection and refresh workflow"""
        print("\n" + "="*80)
        print("TEST 03: Update Boilerplate and Test Refresh")
        print("="*80)

        # Step 1: Create deliverable
        print("\n📝 Step 1: Create Press Release with Boilerplate v1.0...")
        create_response = api_client.post("/deliverables", json={
            "name": "Sequence Test 03 - Press Release (Update & Refresh)",
            "template_id": test_data['press_release_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "who": "Hexagon AB",
                "what": "announces update detection capabilities",
                "when": "January 17, 2024",
                "where": "Stockholm, Sweden",
                "why": "to ensure content stays current with latest information",
                "quote1_speaker": "Product Manager",
                "quote1_title": "VP of Product",
                "quote1_content": "Our update detection system ensures deliverables always reflect the most current information."
            }
        })

        assert create_response.status_code == 201
        deliverable = create_response.json()
        cleanup_deliverables.track(deliverable['id'])

        original_content = deliverable['rendered_content']
        print(f"✅ Deliverable created with boilerplate v{test_data['boilerplate']['version']}")

        # Step 2: Update boilerplate to v1.1 (APPROVED)
        print("\n📝 Step 2: Update Boilerplate element to v1.1 (approved)...")
        boilerplate_update_response = api_client.put(
            f"/unf/elements/{test_data['boilerplate']['id']}",
            json={
                "content": f"{test_data['boilerplate']['content']}\n\nUPDATED CONTENT v1.1 - New information added.",
                "status": "approved"
            }
        )

        assert boilerplate_update_response.status_code == 200
        updated_boilerplate = boilerplate_update_response.json()
        cleanup_elements.track(updated_boilerplate['id'])

        print(f"✅ Boilerplate updated to v{updated_boilerplate['version']}")
        print(f"   Old ID: {test_data['boilerplate']['id']}")
        print(f"   New ID: {updated_boilerplate['id']}")

        # Step 3: Check deliverable for alerts
        print("\n📝 Step 3: Check for update alerts...")
        alerts_response = api_client.get(f"/deliverables/{deliverable['id']}/with-alerts")
        assert alerts_response.status_code == 200
        with_alerts = alerts_response.json()

        assert with_alerts['has_updates'] == True, "Should have updates"
        assert len(with_alerts['alerts']) > 0, "Should have at least one alert"

        # Find boilerplate alert
        boilerplate_alerts = [
            a for a in with_alerts['alerts']
            if 'Boilerplate' in a.get('element_name', '')
        ]

        assert len(boilerplate_alerts) > 0, "Should have boilerplate alert"
        boilerplate_alert = boilerplate_alerts[0]

        assert_alert_structure(boilerplate_alert)
        assert boilerplate_alert['status'] == 'update_available', \
            f"Expected 'update_available', got '{boilerplate_alert['status']}'"

        print(f"✅ Update alert detected:")
        print(f"   Element: {boilerplate_alert['element_name']}")
        print(f"   Old version: {boilerplate_alert['old_version']}")
        print(f"   New version: {boilerplate_alert['new_version']}")
        print(f"   Status: {boilerplate_alert['status']}")

        # Step 4: Refresh deliverable
        print("\n📝 Step 4: Refresh deliverable with latest boilerplate...")
        refresh_response = api_client.post(f"/deliverables/{deliverable['id']}/refresh")

        assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.text}"
        refreshed = refresh_response.json()

        # Verify content updated (NOTE: refresh updates in-place, doesn't create new version)
        assert refreshed['rendered_content'] != original_content, \
            "Content should have changed after refresh"

        print("✅ Deliverable refreshed successfully")
        print(f"   Content updated: {refreshed['rendered_content'] != original_content}")


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence04:
    """
    Test Sequence 04: Edit Vision Statement to v1.1 (Draft) and Test Alerts

    Tests draft element blocking:
    1. Create deliverable with vision v1.0
    2. Update vision to v1.1 (DRAFT, not approved)
    3. Check for "update_pending" alert
    4. Verify refresh is BLOCKED
    5. Approve vision v1.1
    6. Verify refresh now SUCCEEDS
    """

    def test_04_draft_element_blocking(self, api_client, test_data, cleanup_deliverables, cleanup_elements):
        """Test draft element alerts and refresh blocking"""
        print("\n" + "="*80)
        print("TEST 04: Draft Element Alerts and Blocking")
        print("="*80)

        # Step 1: Create deliverable
        print("\n📝 Step 1: Create deliverable with Vision Statement v1.0...")
        create_response = api_client.post("/deliverables", json={
            "name": "Sequence Test 04 - Deliverable (Draft Blocking)",
            "template_id": test_data['press_release_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "who": "Hexagon AB",
                "what": "demonstrates draft blocking functionality",
                "when": "January 18, 2024",
                "where": "Stockholm, Sweden",
                "why": "to prevent publishing with unapproved content changes",
                "quote1_speaker": "Quality Manager",
                "quote1_title": "VP of Quality",
                "quote1_content": "Draft blocking ensures only approved content reaches our deliverables."
            }
        })

        assert create_response.status_code == 201
        deliverable = create_response.json()
        cleanup_deliverables.track(deliverable['id'])

        print(f"✅ Deliverable created")

        # Step 2: Update Vision Statement to v1.1 (DRAFT)
        print("\n📝 Step 2: Update Vision Statement to v1.1 (DRAFT - not approved)...")
        vision_update_response = api_client.put(
            f"/unf/elements/{test_data['vision_statement']['id']}",
            json={
                "content": f"{test_data['vision_statement']['content']}\n\nDRAFT UPDATE v1.1 - Under review.",
                "status": "draft"  # DRAFT, not approved!
            }
        )

        assert vision_update_response.status_code == 200
        updated_vision_draft = vision_update_response.json()
        cleanup_elements.track(updated_vision_draft['id'])

        print(f"✅ Vision Statement updated to v{updated_vision_draft['version']} (DRAFT)")

        # Step 3: Check for draft alerts
        print("\n📝 Step 3: Check for 'update_pending' alert...")
        alerts_response = api_client.get(f"/deliverables/{deliverable['id']}/with-alerts")
        assert alerts_response.status_code == 200
        with_alerts = alerts_response.json()

        assert with_alerts['has_updates'] == True
        assert len(with_alerts['alerts']) > 0

        # Find vision draft alert
        draft_alerts = [
            a for a in with_alerts['alerts']
            if a['status'] == 'update_pending'
        ]

        assert len(draft_alerts) > 0, "Should have at least one 'update_pending' alert"

        print(f"✅ Draft alert detected:")
        for alert in draft_alerts:
            print(f"   Element: {alert['element_name']}")
            print(f"   Status: {alert['status']}")
            print(f"   New version: {alert['new_version']}")

        # Step 4: Try to refresh (should FAIL)
        print("\n📝 Step 4: Try to refresh (should be BLOCKED by draft)...")
        refresh_response = api_client.post(f"/deliverables/{deliverable['id']}/refresh")

        assert refresh_response.status_code == 400, \
            f"Refresh should fail with 400, got {refresh_response.status_code}"

        error = refresh_response.json()
        assert 'detail' in error
        assert 'draft' in error['detail'].lower() or 'pending' in error['detail'].lower()

        print("✅ Refresh correctly BLOCKED by draft element")
        print(f"   Error message: {error['detail']}")

        # Step 5: Approve vision v1.1
        print("\n📝 Step 5: Approve Vision Statement v1.1...")
        approve_response = api_client.put(
            f"/unf/elements/{updated_vision_draft['id']}",
            json={"status": "approved"}
        )

        assert approve_response.status_code == 200
        approved_vision = approve_response.json()

        print(f"✅ Vision Statement v{approved_vision['version']} approved")

        # Step 6: Refresh should now succeed
        print("\n📝 Step 6: Refresh deliverable (should now work)...")
        refresh_response_2 = api_client.post(f"/deliverables/{deliverable['id']}/refresh")

        assert refresh_response_2.status_code == 200, \
            f"Refresh should succeed after approval: {refresh_response_2.text}"

        print("✅ Refresh succeeded after approval")


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence05:
    """
    Test Sequence 05: Swap Story Model in Manifesto (PAS → Inverted Pyramid)

    Tests Story Model switching:
    1. Create Manifesto with PAS Story Model
    2. Switch to Inverted Pyramid Story Model (requires template change)
    3. Verify section reflow occurs
    """

    def test_05_story_model_switching(self, api_client, test_data, cleanup_deliverables):
        """Test Story Model switching with template change"""
        print("\n" + "="*80)
        print("TEST 05: Story Model Switching (PAS → Inverted Pyramid)")
        print("="*80)

        if not test_data['manifesto_pas_template']:
            pytest.skip("Manifesto (PAS) template not found")
        if not test_data['manifesto_inverted_template']:
            pytest.skip("Manifesto (Inverted Pyramid) template not found")

        # Step 1: Create Manifesto with PAS
        print("\n📝 Step 1: Create Manifesto with PAS Story Model...")
        create_response = api_client.post("/deliverables", json={
            "name": "Sequence Test 05 - Manifesto (Story Model Switch)",
            "template_id": test_data['manifesto_pas_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "company_name": "Hexagon AB",
                "year": "2024"
            }
        })

        assert create_response.status_code == 201
        original = create_response.json()
        cleanup_deliverables.track(original['id'])

        print(f"✅ Manifesto created with PAS Story Model")
        print(f"   Template: {test_data['manifesto_pas_template']['name']}")
        print(f"   Story Model: {test_data['pas_model']['name'] if test_data['pas_model'] else 'PAS'}")
        print(f"   Sections: {list(original['rendered_content'].keys())}")

        # Step 2: Switch to Inverted Pyramid
        print("\n📝 Step 2: Switch to Inverted Pyramid Story Model...")
        update_response = api_client.put(f"/deliverables/{original['id']}", json={
            "template_id": test_data['manifesto_inverted_template']['id']
        })

        assert update_response.status_code == 200, f"Template switch failed: {update_response.text}"
        updated = update_response.json()

        print("✅ Story Model switched successfully")

        # Step 3: Validate changes
        print("\n📝 Step 3: Validate Story Model switch...")

        # Verify template changed
        assert updated['template_id'] == test_data['manifesto_inverted_template']['id']

        # Verify story model changed
        assert updated['story_model_id'] != original['story_model_id'], \
            "Story Model ID should have changed"

        # Verify version incremented
        assert updated['version'] == original['version'] + 1

        # Verify content re-rendered
        assert updated['rendered_content'] != original['rendered_content'], \
            "Content should have been re-rendered with new structure"

        # Verify sections may have changed (different Story Model = different sections)
        print(f"✅ Story Model switching validated")
        print(f"   Old template: {test_data['manifesto_pas_template']['name']}")
        print(f"   New template: {test_data['manifesto_inverted_template']['name']}")
        print(f"   Old sections: {list(original['rendered_content'].keys())}")
        print(f"   New sections: {list(updated['rendered_content'].keys())}")


@pytest.mark.integration
@pytest.mark.workflow
class TestSequence06:
    """
    Test Sequence 06: End-to-End Provenance Check

    Validates complete provenance tracking:
    1. Create deliverable
    2. Verify all provenance fields exist
    3. Update deliverable to create v2
    4. Get version history
    5. Verify version chain integrity
    """

    def test_06_provenance_tracking(self, api_client, test_data, cleanup_deliverables):
        """Test complete provenance and version tracking"""
        print("\n" + "="*80)
        print("TEST 06: End-to-End Provenance Check")
        print("="*80)

        # Step 1: Create deliverable
        print("\n📝 Step 1: Create deliverable...")
        create_response = api_client.post("/deliverables", json={
            "name": "Sequence Test 06 - Provenance Check",
            "template_id": test_data['press_release_template']['id'],
            "voice_id": test_data['corporate_voice']['id'],
            "instance_data": {
                "who": "Hexagon AB",
                "what": "validates complete provenance tracking",
                "when": "January 19, 2024",
                "where": "Stockholm, Sweden",
                "why": "to ensure full traceability of content lineage",
                "quote1_speaker": "Compliance Officer",
                "quote1_title": "Chief Compliance Officer",
                "quote1_content": "Complete provenance tracking is essential for content governance and audit trails."
            }
        })

        assert create_response.status_code == 201
        v1 = create_response.json()
        cleanup_deliverables.track(v1['id'])

        print(f"✅ Deliverable v1 created")

        # Step 2: Verify provenance fields
        print("\n📝 Step 2: Verify all provenance fields exist...")
        required_provenance_fields = [
            'element_versions',
            'template_id',
            'template_version',
            'voice_id',
            'voice_version',
            'story_model_id',
            'version',
            'prev_deliverable_id'
        ]

        for field in required_provenance_fields:
            assert field in v1, f"Missing provenance field: {field}"

        # Validate types
        assert isinstance(v1['element_versions'], dict)
        assert len(v1['element_versions']) > 0, "Should have element versions tracked"

        assert v1['version'] == 1
        assert v1['prev_deliverable_id'] is None

        print(f"✅ All provenance fields present")
        print(f"   Element versions tracked: {len(v1['element_versions'])}")
        print(f"   Template: {v1['template_id']} (v{v1['template_version']})")
        print(f"   Voice: {v1['voice_id']} (v{v1['voice_version']})")
        print(f"   Story Model: {v1['story_model_id']}")

        # Step 3: Update to create v2
        print("\n📝 Step 3: Update deliverable to create v2...")
        update_response = api_client.put(f"/deliverables/{v1['id']}", json={
            "voice_id": test_data['product_voice']['id']
        })

        assert update_response.status_code == 200
        v2 = update_response.json()

        print(f"✅ Deliverable v2 created")

        # Step 4: Get version history
        print("\n📝 Step 4: Get version history...")
        versions_response = api_client.get(f"/deliverables/{v2['id']}/versions")
        assert versions_response.status_code == 200
        versions = versions_response.json()

        assert isinstance(versions, list)
        assert len(versions) == 2, f"Should have 2 versions, got {len(versions)}"

        print(f"✅ Version history retrieved: {len(versions)} versions")

        # Step 5: Verify version chain
        print("\n📝 Step 5: Verify version chain integrity...")

        # Versions should be sorted newest first
        assert versions[0]['version'] == 2
        assert versions[1]['version'] == 1

        # Verify linkage
        assert versions[0]['prev_deliverable_id'] == versions[1]['id'], \
            "Version chain broken: v2 should link to v1"

        assert versions[1]['prev_deliverable_id'] is None, \
            "v1 should have no predecessor"

        # Verify v2 has different voice
        assert versions[0]['voice_id'] == test_data['product_voice']['id']
        assert versions[1]['voice_id'] == test_data['corporate_voice']['id']

        print(f"✅ Version chain validated")
        print(f"   v2 ID: {versions[0]['id']}")
        print(f"   v1 ID: {versions[1]['id']}")
        print(f"   v2 → v1 link: {versions[0]['prev_deliverable_id'] == versions[1]['id']}")
        print(f"   Voice changed: {versions[0]['voice_id'] != versions[1]['voice_id']}")

        print("\n" + "="*80)
        print("🎉 ALL PROVENANCE TRACKING VALIDATED")
        print("="*80)
