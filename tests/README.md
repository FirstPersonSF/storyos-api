# StoryOS Test Suite

Automated integration tests for the 6 core workflow sequences.

## Quick Start

```bash
# Install pytest (if not already installed)
pip install pytest requests

# Run all tests with REAL LLM (costs ~$0.10, takes ~3-5 minutes)
pytest tests/integration/test_workflow_sequences.py -v

# Run all tests with MOCKED LLM (free, instant)
pytest tests/integration/test_workflow_sequences.py --mock-llm -v

# Run specific test sequence
pytest tests/integration/test_workflow_sequences.py::TestSequence01 -v
```

## Prerequisites

1. **Backend server must be running:**
   ```bash
   source .venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Dummy data must be loaded** (voices, templates, elements, story models)

3. **API key for Claude** (if using real LLM):
   - Ensure `ANTHROPIC_API_KEY` is set in `.env`
   - Or set environment variable: `export ANTHROPIC_API_KEY=your-key-here`

## Test Modes

### Real LLM Mode (Default)

Uses actual Claude API for voice transformation:

```bash
pytest tests/integration/test_workflow_sequences.py
```

**Pros:**
- Tests actual behavior
- Validates LLM prompts work correctly
- Catches real voice transformation issues

**Cons:**
- Costs ~$0.10 per full test run (with Haiku)
- Takes 3-5 minutes
- Requires API key

### Mocked LLM Mode

Uses deterministic regex-based mock for voice transformation:

```bash
pytest tests/integration/test_workflow_sequences.py --mock-llm
```

**Pros:**
- Free
- Instant (30-60 seconds)
- No API key required
- Deterministic results

**Cons:**
- Doesn't test actual LLM behavior
- Mock may not match real transformation

### Recommendation

- **Development**: Use `--mock-llm` for fast feedback
- **Pre-commit**: Run with real LLM to validate everything
- **CI/CD**: Use real LLM on main branch, mock on feature branches

## Test Sequences

### Test 01: Generate Deliverables with Corporate Voice
**File:** `test_workflow_sequences.py::TestSequence01`

Creates three deliverables (Press Release, Blog Post, Manifesto) using Corporate Voice v1.0.

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence01 -v
```

### Test 02: Switch Press Release to Product Voice
**File:** `test_workflow_sequences.py::TestSequence02`

Tests voice switching by creating a deliverable with Corporate Voice, then updating to Product Voice.

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence02 -v
```

### Test 03: Update Boilerplate and Test Refresh
**File:** `test_workflow_sequences.py::TestSequence03`

Tests update detection and refresh:
1. Create deliverable with boilerplate v1.0
2. Update boilerplate to v1.1 (approved)
3. Verify "update_available" alert
4. Refresh deliverable

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence03 -v
```

### Test 04: Draft Element Alerts and Blocking
**File:** `test_workflow_sequences.py::TestSequence04`

Tests draft element blocking:
1. Create deliverable
2. Update element to draft v1.1
3. Verify "update_pending" alert
4. Verify refresh is BLOCKED
5. Approve element
6. Verify refresh now succeeds

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence04 -v
```

### Test 05: Story Model Switching
**File:** `test_workflow_sequences.py::TestSequence05`

Tests Story Model switching:
1. Create Manifesto with PAS Story Model
2. Switch to Inverted Pyramid Story Model
3. Verify section reflow

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence05 -v
```

### Test 06: Provenance Tracking
**File:** `test_workflow_sequences.py::TestSequence06`

Validates complete provenance tracking:
1. Create deliverable
2. Verify all provenance fields
3. Update to create v2
4. Get version history
5. Verify version chain

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence06 -v
```

## Running Tests

### All Tests

```bash
# With real LLM
pytest tests/integration/test_workflow_sequences.py -v

# With mocked LLM
pytest tests/integration/test_workflow_sequences.py --mock-llm -v
```

### Specific Test Class

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence03 -v
```

### Specific Test Method

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence03::test_03_update_and_refresh -v
```

### With Detailed Output

```bash
# Show print statements
pytest tests/integration/test_workflow_sequences.py -v -s

# Show captured output even for passing tests
pytest tests/integration/test_workflow_sequences.py -v -s --capture=no
```

### Stop on First Failure

```bash
pytest tests/integration/test_workflow_sequences.py -x
```

### Run Only Failed Tests

```bash
pytest tests/integration/test_workflow_sequences.py --lf
```

## Test Output

Tests include detailed console output showing each step:

```
================================================================================
TEST 03: Update Boilerplate and Test Refresh
================================================================================

📝 Step 1: Create Press Release with Boilerplate v1.0...
✅ Deliverable created with boilerplate v1.0

📝 Step 2: Update Boilerplate element to v1.1 (approved)...
✅ Boilerplate updated to v1.1
   Old ID: abc-123
   New ID: def-456

📝 Step 3: Check for update alerts...
✅ Update alert detected:
   Element: Company Boilerplate
   Old version: 1.0
   New version: 1.1
   Status: update_available

📝 Step 4: Refresh deliverable with latest boilerplate...
✅ Deliverable refreshed successfully
   Content updated: True
```

## Cost Tracking

### Per Test Run (Real LLM with Haiku)

| Test | LLM Calls | Estimated Cost |
|------|-----------|----------------|
| Test 01 | ~15 | $0.03 |
| Test 02 | ~10 | $0.02 |
| Test 03 | ~10 | $0.02 |
| Test 04 | ~10 | $0.02 |
| Test 05 | ~12 | $0.02 |
| Test 06 | ~10 | $0.02 |
| **Total** | **~67** | **~$0.13** |

### Cost Scenarios

- **Single test run**: ~$0.13
- **10 test runs**: ~$1.30
- **100 test runs**: ~$13
- **Development team (5 devs × 5 runs/day × 250 days)**: ~$813/year

## Troubleshooting

### Tests Fail with "Connection Refused"

**Problem:** Backend server is not running

**Solution:**
```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Tests Fail with "Template not found"

**Problem:** Dummy data not loaded

**Solution:** Load dummy data into database (check dummy data loading script)

### Tests Fail with "Anthropic API Error"

**Problem:** Missing or invalid API key

**Solution:**
```bash
# Set API key in .env
echo "ANTHROPIC_API_KEY=your-key-here" >> .env

# Or export as environment variable
export ANTHROPIC_API_KEY=your-key-here
```

**Alternative:** Run with `--mock-llm` to bypass API

### Tests Pass but Content Doesn't Look Right

**Problem:** Mock LLM is being used instead of real LLM

**Solution:** Remove `--mock-llm` flag to use real LLM

### "No module named 'pytest'"

**Problem:** pytest not installed

**Solution:**
```bash
pip install pytest requests
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Workflow Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest requests

      - name: Start backend
        run: |
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Run tests (mocked for PR)
        if: github.event_name == 'pull_request'
        run: pytest tests/integration/test_workflow_sequences.py --mock-llm -v

      - name: Run tests (real LLM for main)
        if: github.ref == 'refs/heads/main'
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: pytest tests/integration/test_workflow_sequences.py -v
```

## Writing New Tests

To add new workflow tests:

1. Create new test class in `test_workflow_sequences.py`:
   ```python
   @pytest.mark.integration
   @pytest.mark.workflow
   class TestSequence07:
       """Description of test"""

       def test_07_my_new_test(self, api_client, test_data, cleanup_deliverables):
           # Your test code here
           pass
   ```

2. Use fixtures from `conftest.py`:
   - `api_client`: HTTP client for API calls
   - `test_data`: Pre-loaded test data (voices, templates, etc.)
   - `cleanup_deliverables`: Tracks created deliverables
   - `cleanup_elements`: Tracks created elements

3. Use helper functions:
   - `assert_deliverable_structure(deliverable)`: Validate deliverable structure
   - `assert_alert_structure(alert)`: Validate alert structure

## Debugging

### Run with Python Debugger

```bash
pytest tests/integration/test_workflow_sequences.py::TestSequence03 --pdb
```

### Print Variables

Tests already include print statements for debugging. Run with `-s` to see them:

```bash
pytest tests/integration/test_workflow_sequences.py -v -s
```

### Check API Responses

All API responses are available in test code. Add print statements:

```python
response = api_client.post("/deliverables", json={...})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## Best Practices

1. **Always run with `--mock-llm` first** for fast feedback
2. **Run with real LLM before committing** to validate everything
3. **Check test output** - tests print detailed step-by-step information
4. **Run specific tests** during development to save time
5. **Run full suite** before merging to ensure nothing breaks

## Support

For issues or questions:
- Check test output for detailed error messages
- Review `Documentation/Implementation_Summary_Workflow_Tests.md`
- Review `Documentation/Workflow_Test_Execution_Guide.md`
