# StoryOS Testing & Validation Guide

This guide shows you how to test and validate the StoryOS prototype.

---

## Prerequisites

Make sure both servers are running:

```bash
# Terminal 1: Backend API
cd /Users/drewf/Desktop/Python/storyos_protoype
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (optional)
cd /Users/drewf/Desktop/Python/storyos-frontend
npm run dev
```

---

## Method 1: Automated Test Script (Recommended)

The easiest way to validate the entire system is to run Test Case 1:

```bash
cd /Users/drewf/Desktop/Python/storyos_protoype
source .venv/bin/activate
python3 test_case_1.py
```

### What This Tests:

✅ **Template Application**
- Brand Manifesto uses PAS Story Model
- Press Release uses Inverted Pyramid Story Model

✅ **Voice Tracking**
- Corporate Brand Voice v1.0 tracked on both deliverables

✅ **Instance Field Management**
- Collection: All 9 instance fields captured
- Validation: 7/7 required fields validated
- Injection: Instance fields injected into content (e.g., {who}, {what}, {when})

✅ **Story Model Validation**
- Word count constraints (Problem ≤120 words, Headline ≤10 words)
- Required element constraints (Solve requires Vision Statement)
- Required field constraints (Lede requires who/what/when/where/why)

✅ **Version Tracking**
- Element versions tracked
- Impact alerts when elements update

### Expected Results:

**Brand Manifesto:**
- 2 Story Model validation checks passed
  - Problem word count ≤120
  - Solve includes Vision Statement

**Press Release:**
- 7 instance field validation checks passed
- 1 Story Model check failed (Headline too long) - **this is correct behavior**
- 1 Story Model check passed (Lede has required fields)

---

## Method 2: API Testing with curl

Test individual API endpoints:

### 1. Check API is Running

```bash
curl -s http://localhost:8000/
```

Should return:
```json
{
  "name": "StoryOS API",
  "version": "1.0.0",
  "description": "Content management system for enterprise storytelling"
}
```

### 2. Get All Deliverables

```bash
curl -s http://localhost:8000/deliverables | python3 -m json.tool
```

### 3. Get Deliverable with Impact Alerts

```bash
# Replace <ID> with actual deliverable ID
curl -s 'http://localhost:8000/deliverables/<ID>/alerts' | python3 -m json.tool
```

### 4. Get UNF Elements

```bash
curl -s http://localhost:8000/unf/elements | python3 -m json.tool
```

### 5. Get Templates

```bash
curl -s http://localhost:8000/templates | python3 -m json.tool
```

### 6. Get Brand Voices

```bash
curl -s http://localhost:8000/voices | python3 -m json.tool
```

### 7. Get Story Models

```bash
curl -s http://localhost:8000/story-models | python3 -m json.tool
```

---

## Method 3: Interactive API Documentation

Open your browser to:

**http://localhost:8000/docs**

This provides:
- Interactive API playground
- Try all endpoints with sample data
- See request/response schemas
- Test authentication (if implemented)

Alternative documentation format:
**http://localhost:8000/redoc**

---

## Method 4: React Frontend Testing

### Local Development:
**http://localhost:5173/**

### Production (Vercel):
**https://storyos-frontend.vercel.app/**

### What You Can Test:

#### A. Elements Page
1. **View all UNF elements**
   - See element versions
   - Check approval status
   - View content

2. **Create new elements**
   - Click "+ Create Element"
   - Fill in layer, name, content
   - Submit as draft

3. **Edit existing elements**
   - Click "Edit" on any element
   - Modify content
   - Creates new version, marks old as superseded

4. **Approve draft elements**
   - Click "Approve" on draft elements
   - Status changes from draft → approved

#### B. Deliverables Page
1. **View all deliverables**
   - See template and voice used
   - Check status (draft/approved/published)
   - View instance data fields

2. **Create new deliverable**
   - Click "+ Create Deliverable"
   - Select template (Brand Manifesto or Press Release)
   - Select brand voice (Corporate or Product)
   - Select UNF elements to include
   - Submit

3. **View rendered content**
   - Click "View Content" on any deliverable
   - See all sections with instance fields injected
   - View template/voice/status metadata

4. **Check for updates (Impact Alerts)**
   - Click "Check for Updates" on any deliverable
   - See if any bound elements have newer versions
   - Shows "Update Available" alerts with version changes

---

## Method 5: Database Inspection

Query the database directly using Python:

```python
from storage.supabase_storage import SupabaseStorage
import os
from dotenv import load_dotenv

load_dotenv()
storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get all deliverables
deliverables = storage.get_many('deliverables')
print(f"Total deliverables: {len(deliverables)}")

# Get latest deliverable
latest = deliverables[0] if deliverables else None
if latest:
    print(f"Latest: {latest['name']}")
    print(f"Status: {latest['status']}")
    print(f"Voice: {latest['voice_version']}")
```

---

## Common Test Scenarios

### Scenario 1: Verify Instance Field Injection

1. Run Test Case 1
2. Check Press Release Lede section
3. Should show: "Stockholm, Sweden, 2025-10-20 — Hexagon AB Announces..."
4. Confirms {where}, {when}, {who}, {what} injected

### Scenario 2: Verify Story Model Validation

1. Run Test Case 1
2. Check validation output
3. Should show Problem word count check (Brand Manifesto)
4. Should show Headline word count failure (Press Release) - **this is correct**
5. Should show Lede required fields check (Press Release)

### Scenario 3: Verify Version Tracking

1. Update an element (e.g., Vision Statement)
2. Old version should be marked "superseded"
3. New version should be "approved"
4. Deliverables using old version should show update alert

### Scenario 4: Verify Impact Alerts

1. Create a deliverable
2. Update an element used in that deliverable
3. Click "Check for Updates" on the deliverable
4. Should show alert: "Vision Statement: v1.1 → v1.2"

---

## Validation Checklist

Use this checklist to validate Phase 1 features:

- [ ] **Deliverable Generation**
  - [ ] Can create Brand Manifesto
  - [ ] Can create Press Release
  - [ ] Content renders correctly

- [ ] **Voice Tracking**
  - [ ] Corporate Voice tracked
  - [ ] Product Voice tracked
  - [ ] Version recorded in deliverable

- [ ] **Instance Fields**
  - [ ] Fields collected via form
  - [ ] Fields validated (required check)
  - [ ] Fields injected into content

- [ ] **Story Model Validation**
  - [ ] Word count constraints work
  - [ ] Required element constraints work
  - [ ] Required field constraints work

- [ ] **Version Tracking**
  - [ ] Element versions tracked
  - [ ] Old versions marked superseded
  - [ ] Version history maintained

- [ ] **Impact Alerts**
  - [ ] Alerts show when elements update
  - [ ] Shows old vs new version
  - [ ] Identifies affected deliverables

---

## Troubleshooting

### Backend Not Running

```bash
cd /Users/drewf/Desktop/Python/storyos_protoype
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Not Running

```bash
cd /Users/drewf/Desktop/Python/storyos-frontend
npm run dev
```

### Database Connection Issues

Check `.env` file has correct Supabase credentials:

```bash
cat .env
# Should show:
# SUPABASE_URL=https://...
# SUPABASE_SERVICE_ROLE_KEY=...
```

### Test Script Fails

Make sure dependencies are installed:

```bash
source .venv/bin/activate
pip install -q psycopg[binary] python-dotenv ujson pydantic supabase
```

---

## Next Steps

Once Phase 1 validation is complete, you can:

1. **Test Case 2**: Switch Press Release to Product Voice v1.0
2. **Test Case 3**: Update Boilerplate element and verify alerts
3. **Test Case 4**: Edit Vision Statement and check impact on deliverables
4. **Custom Tests**: Create your own deliverables with different combinations

---

## Support

For issues or questions:
- Check the API docs: http://localhost:8000/docs
- Review the code in `/services/deliverable_service.py`
- Check validation logic in `validate_deliverable()`
- Review test case in `test_case_1.py`
