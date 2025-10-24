"""
Pytest configuration and fixtures for StoryOS tests
"""
import pytest
import requests
from typing import Dict, Any
from unittest.mock import patch
import re


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--mock-llm",
        action="store_true",
        default=False,
        help="Mock LLM calls instead of using real API (faster, free)"
    )
    parser.addoption(
        "--llm-model",
        action="store",
        default="haiku",
        help="LLM model to use: 'haiku' (cheap) or 'sonnet' (better quality)"
    )


@pytest.fixture(scope="session")
def use_mock_llm(request):
    """Determine if tests should mock the LLM"""
    return request.config.getoption("--mock-llm")


@pytest.fixture(scope="session")
def llm_model(request):
    """Get LLM model preference"""
    return request.config.getoption("--llm-model")


# ============================================================================
# LLM MOCKING
# ============================================================================

def mock_voice_transform(content: str, voice_config: Dict[str, Any], **kwargs) -> str:
    """
    Deterministic mock for voice transformation

    Applies simple regex transformations based on voice config
    to simulate voice transformation without calling LLM
    """
    transformed = content

    # Apply lexicon replacements from rules
    rules = voice_config.get('rules', {})
    lexicon = rules.get('lexicon', {})

    for category, mapping in lexicon.items():
        generic_terms = mapping.get('generic', [])
        branded_term = mapping.get('branded', '')

        if generic_terms and branded_term:
            for term in generic_terms:
                # Only replace when not part of other words (word boundaries)
                pattern = r'(?<![a-zA-Z])' + re.escape(term) + r'(?![a-zA-Z])'
                transformed = re.sub(
                    pattern,
                    branded_term,
                    transformed,
                    flags=re.IGNORECASE
                )

    # Apply contractions based on formality
    tone_rules = voice_config.get('tone_rules', {})
    formality = tone_rules.get('formality', '')

    if 'low' in formality.lower() or 'casual' in formality.lower():
        # Add contractions
        transformed = transformed.replace('do not', "don't")
        transformed = transformed.replace('will not', "won't")
        transformed = transformed.replace('cannot', "can't")
    elif 'high' in formality.lower():
        # Expand contractions
        transformed = transformed.replace("don't", 'do not')
        transformed = transformed.replace("won't", 'will not')
        transformed = transformed.replace("can't", 'cannot')

    return transformed


@pytest.fixture(autouse=True)
def setup_llm_mock(use_mock_llm, monkeypatch):
    """
    Automatically mock LLM if --mock-llm flag is set

    This fixture runs for every test and patches the LLM transformer
    """
    if use_mock_llm:
        # Patch the LLM voice transformer
        monkeypatch.setattr(
            'services.voice_transformer_llm.LLMVoiceTransformer.apply_voice_with_profile',
            mock_voice_transform
        )
        monkeypatch.setattr(
            'services.voice_transformer_llm.LLMVoiceTransformer.apply_voice',
            mock_voice_transform
        )
        print("\n🔧 Using MOCKED LLM (fast, free, deterministic)")
    else:
        print("\n🤖 Using REAL LLM (slow, costs ~$0.10 per test run)")


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def api_client():
    """Reusable API client for making requests"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def get(self, path, **kwargs):
            return requests.get(f"{self.base_url}{path}", **kwargs)

        def post(self, path, **kwargs):
            return requests.post(f"{self.base_url}{path}", **kwargs)

        def put(self, path, **kwargs):
            return requests.put(f"{self.base_url}{path}", **kwargs)

        def delete(self, path, **kwargs):
            return requests.delete(f"{self.base_url}{path}", **kwargs)

    return APIClient(BASE_URL)


@pytest.fixture(scope="session")
def test_data(api_client):
    """
    Fetch all test data from the API (voices, templates, elements, story models)

    This assumes dummy data has been loaded into the database
    """
    # Get voices
    voices_response = api_client.get("/voices")
    assert voices_response.status_code == 200, "Failed to fetch voices"
    voices = voices_response.json()

    # Find Corporate and Product voices
    corporate_voice = None
    product_voice = None
    for v in voices:
        if "Corporate" in v['name'] and "1.0" in v['version']:
            corporate_voice = v
        if "Product" in v['name'] and "1.0" in v['version']:
            product_voice = v

    assert corporate_voice, "Corporate Voice v1.0 not found"
    assert product_voice, "Product Voice v1.0 not found"

    # Get templates
    templates_response = api_client.get("/templates")
    assert templates_response.status_code == 200, "Failed to fetch templates"
    templates = templates_response.json()

    # Find specific templates
    press_release_template = None
    blog_post_template = None
    manifesto_pas_template = None
    manifesto_inverted_template = None

    for t in templates:
        if "Press Release" in t['name']:
            press_release_template = t
        elif "Blog Post" in t['name']:
            blog_post_template = t
        elif "Manifesto" in t['name']:
            # Need to check story model to distinguish PAS vs Inverted Pyramid
            if "PAS" in t.get('metadata', {}).get('story_model_name', ''):
                manifesto_pas_template = t
            elif "Inverted" in t.get('metadata', {}).get('story_model_name', ''):
                manifesto_inverted_template = t

    assert press_release_template, "Press Release template not found"
    # Blog post and manifesto templates may not exist yet

    # Get approved elements
    elements_response = api_client.get("/unf/elements?status=approved")
    assert elements_response.status_code == 200, "Failed to fetch elements"
    elements = elements_response.json()

    # Find specific elements
    boilerplate = None
    vision_statement = None

    for e in elements:
        if "Boilerplate" in e['name']:
            boilerplate = e
        if "Vision" in e['name']:
            vision_statement = e

    assert boilerplate, "Boilerplate element not found"
    assert vision_statement, "Vision Statement element not found"

    # Get story models
    story_models_response = api_client.get("/story-models")
    assert story_models_response.status_code == 200, "Failed to fetch story models"
    story_models = story_models_response.json()

    pas_model = None
    inverted_model = None

    for sm in story_models:
        if "PAS" in sm['name']:
            pas_model = sm
        if "Inverted" in sm['name']:
            inverted_model = sm

    return {
        # Voices
        'corporate_voice': corporate_voice,
        'product_voice': product_voice,

        # Templates
        'press_release_template': press_release_template,
        'blog_post_template': blog_post_template,
        'manifesto_pas_template': manifesto_pas_template,
        'manifesto_inverted_template': manifesto_inverted_template,

        # Elements
        'boilerplate': boilerplate,
        'vision_statement': vision_statement,

        # Story Models
        'pas_model': pas_model,
        'inverted_model': inverted_model,

        # All items (for exploration)
        'all_voices': voices,
        'all_templates': templates,
        'all_elements': elements,
        'all_story_models': story_models
    }


@pytest.fixture
def cleanup_deliverables(api_client):
    """
    Cleanup fixture that tracks created deliverables and deletes them after test

    Usage in tests:
        deliverable_id = cleanup_deliverables.track(created_deliverable['id'])
    """
    created_ids = []

    class CleanupHelper:
        def track(self, deliverable_id):
            created_ids.append(deliverable_id)
            return deliverable_id

    yield CleanupHelper()

    # Cleanup after test
    # Note: Currently there's no DELETE endpoint, so this is a placeholder
    # In production, you might want to mark as "test" and clean up periodically
    # for deliverable_id in created_ids:
    #     api_client.delete(f"/deliverables/{deliverable_id}")


@pytest.fixture
def cleanup_elements(api_client):
    """
    Cleanup fixture for elements created during tests
    """
    created_ids = []

    class CleanupHelper:
        def track(self, element_id):
            created_ids.append(element_id)
            return element_id

    yield CleanupHelper()

    # Cleanup after test (placeholder)
    # for element_id in created_ids:
    #     api_client.delete(f"/unf/elements/{element_id}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_deliverable_structure(deliverable: Dict[str, Any]):
    """Validate that a deliverable has the expected structure"""
    required_fields = [
        'id', 'name', 'template_id', 'template_version',
        'story_model_id', 'voice_id', 'voice_version',
        'status', 'version', 'element_versions',
        'rendered_content', 'created_at', 'updated_at'
    ]

    for field in required_fields:
        assert field in deliverable, f"Deliverable missing required field: {field}"

    # Validate types
    assert isinstance(deliverable['element_versions'], dict), "element_versions should be a dict"
    assert isinstance(deliverable['rendered_content'], dict), "rendered_content should be a dict"
    assert isinstance(deliverable['version'], int), "version should be an int"


def assert_alert_structure(alert: Dict[str, Any]):
    """Validate that an alert has the expected structure"""
    required_fields = ['element_id', 'element_name', 'old_version', 'new_version', 'status']

    for field in required_fields:
        assert field in alert, f"Alert missing required field: {field}"

    # Validate status values
    assert alert['status'] in ['update_available', 'update_pending'], \
        f"Invalid alert status: {alert['status']}"
