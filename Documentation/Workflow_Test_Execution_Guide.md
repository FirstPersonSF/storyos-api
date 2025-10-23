# Workflow Test Execution Guide

**Document Status**: Test Plan
**Created**: 2025-10-23
**Test Environment**: Production (Railway + Vercel)

---

## Overview

This document provides step-by-step instructions for executing the six Workflow Test Sequences defined in the StoryOS Prototype specification. Each test validates a different aspect of the system's core functionality.

**Test Execution Method**: These tests should be run through the **web application** at your Vercel URL, not via API calls.

---

## Prerequisites

Before starting tests, verify:

- [ ] Backend API is running on Railway
- [ ] Frontend is deployed on Vercel
- [ ] Database has dummy data loaded (UNF Elements, Templates, Voices)
- [ ] You can access the web application

**Quick Status Check**:
1. Open web application in browser
2. Navigate to "Deliverables" page
3. Click "Create New Deliverable"
4. Verify you can see templates and voices in dropdowns

---

## Test Sequence 01: Generate Deliverables with Corporate Voice v1.0

### Objective
Confirm that both Deliverable Templates can generate correctly using the default Brand Voice.

### Test Status
✅ **READY TO TEST** - All features implemented

### Steps

#### Part A: Create Brand Manifesto Deliverable

1. **Navigate** to Deliverables page
2. **Click** "Create New Deliverable"
3. **Fill Form**:
   - Name: `Sequence Test 01 - Brand Manifesto`
   - Template: Select "Brand Manifesto Template"
   - Voice: Select "Corporate Voice v1.0" (should be default)
   - Story Model: Should auto-select "PAS Story Model v1.0"

4. **Fill Instance Fields** (Brand Manifesto typically has minimal instance fields):
   - Fill any required fields shown

5. **Click** "Create Deliverable"
6. **Wait** for rendering to complete
7. **Review** the deliverable sections

#### Part B: Create Press Release Deliverable

1. **Navigate** back to Deliverables page
2. **Click** "Create New Deliverable"
3. **Fill Form**:
   - Name: `Sequence Test 01 - Press Release`
   - Template: Select "Press Release Template"
   - Voice: Select "Corporate Voice v1.0"
   - Story Model: Should auto-select "Inverted Pyramid Story Model v1.0"

4. **Fill Instance Fields** (Required for Press Release):
   - **who**: Hexagon AB
   - **what**: announces the launch of its next-generation measurement platform, HxGN Precision One
   - **when**: 2025-10-17
   - **where**: Stockholm, Sweden
   - **why**: To help manufacturers increase precision, reduce waste, and move closer to fully autonomous production
   - **quote1_speaker**: Burkhardt Boekem
   - **quote1_title**: Chief Technology Officer, Hexagon AB
   - **quote1_content**: "This platform represents a significant leap forward in our vision for autonomous manufacturing, combining cutting-edge sensor technology with intelligent analytics."
   - **quote2_speaker**: Alex Grant
   - **quote2_title**: Plant Director, Orion Manufacturing
   - **quote2_content**: "We've seen a 40% improvement in precision and a measurable reduction in material waste since implementing this technology."

5. **Click** "Create Deliverable"
6. **Wait** for rendering to complete
7. **Review** the deliverable sections

### Expected Results

✅ **Brand Manifesto**:
- [ ] Deliverable generates successfully
- [ ] All 3 PAS sections render (Problem, Agitate, Solve)
- [ ] Content pulls from correct UNF Elements
- [ ] Corporate Voice applied (check tone and terminology)
- [ ] No errors in console or UI

✅ **Press Release**:
- [ ] Deliverable generates successfully
- [ ] All 6 Inverted Pyramid sections render (Headline, Lede, Key Facts, Quote 1, Quote 2, Boilerplate)
- [ ] Headline is 10 words or fewer
- [ ] Lede includes five W's (who, what, when, where, why)
- [ ] Quote 1 shows speaker name and title
- [ ] Quote 2 shows speaker name and title
- [ ] Quotes are preserved verbatim (not transformed)
- [ ] Corporate Voice applied to other sections
- [ ] No errors in console or UI

### Validation Steps

1. **Check Headline Word Count**:
   ```
   Count words in headline - should be ≤ 10 words
   ```

2. **Check Lede Contains Five W's**:
   ```
   Verify lede paragraph mentions:
   - Who: Hexagon AB
   - What: announces HxGN Precision One
   - When: 2025-10-17
   - Where: Stockholm, Sweden
   - Why: to help manufacturers...
   ```

3. **Check Quotes Are Verbatim**:
   ```
   Compare quote text to instance data entered
   Should match exactly (not transformed)
   ```

4. **Check Corporate Voice Applied**:
   ```
   Look for Corporate Voice traits in non-quote sections:
   - Professional tone
   - Industry terminology
   - No contractions
   ```

### Notes
- If validation errors occur, note which rules failed
- Save deliverable IDs for use in subsequent tests
- Take screenshots of rendered output

---

## Test Sequence 02: Switch Press Release to Product Voice v1.0

### Objective
Verify that multiple Brand Voices can be selected and applied correctly.

### Test Status
⚠️ **PARTIALLY READY** - Voice switching requires update/refresh feature

### Dependencies
- Requires Test Sequence 01 completed
- Requires "Sequence Test 01 - Press Release" deliverable created

### Steps

1. **Navigate** to Deliverables page
2. **Find** "Sequence Test 01 - Press Release" deliverable
3. **Click** to open/view deliverable
4. **Click** "Edit" or "Settings" (if available)
5. **Change Voice**:
   - Find Voice dropdown/selector
   - Switch from "Corporate Voice v1.0" to "Product Voice v1.0"
6. **Click** "Re-render" or "Apply Changes"
7. **Wait** for re-rendering to complete
8. **Compare** old vs. new output

### Expected Results

✅ **Voice Change**:
- [ ] Product Voice applies successfully
- [ ] Tone changes (e.g., more technical, less formal)
- [ ] Terminology changes (e.g., product-specific terms)
- [ ] Quotes remain unchanged (still verbatim)
- [ ] Version tracking shows Voice ID and version used

⚠️ **Known Limitations**:
- Update/refresh mechanism may not be fully implemented
- May require creating new deliverable instead of updating existing

### Alternative Approach (If Update Not Available)

If you cannot update the existing deliverable:

1. **Create** new Press Release: `Sequence Test 02 - Press Release (Product Voice)`
2. **Use same** instance data as Test 01
3. **Select** "Product Voice v1.0" instead of Corporate Voice
4. **Compare** output to Test 01 deliverable
5. **Verify** differences in tone and terminology

### Validation Steps

1. **Compare Tone**:
   ```
   Corporate Voice: Professional, formal
   Product Voice: Technical, product-focused
   ```

2. **Check Terminology Changes**:
   ```
   Look for product-specific terms
   More technical language
   Feature/benefit focus
   ```

3. **Verify Quotes Unchanged**:
   ```
   Quotes should still match instance data exactly
   ```

---

## Test Sequence 03: Update Boilerplate to v1.1 and Test Refresh

### Objective
Validate "Update Available" alerts and refresh behavior.

### Test Status
❌ **NOT YET IMPLEMENTED** - Requires update alert system

### Dependencies
- Requires Test Sequence 01 completed
- Requires UNF Element versioning system
- Requires update detection mechanism

### What Needs to Be Implemented

Before this test can run:
1. **Update Alert System** - detect when Element versions change
2. **Refresh Mechanism** - allow re-rendering with new Element versions
3. **Version Comparison** - track old vs. new Element versions

### Steps (When Implemented)

1. **Navigate** to UNF Elements page
2. **Find** "Messaging.Boilerplate" element
3. **Edit** element:
   - Change content slightly
   - Increment version to "1.1"
   - Set status to "Approved"
4. **Save** updated element

5. **Navigate** to Deliverables page
6. **Open** "Sequence Test 01 - Press Release"
7. **Look for** "Update Available" alert/badge
8. **Click** "Refresh" or "Update"
9. **Verify** new Boilerplate v1.1 is used

10. **Alternative**: Click "Defer" instead
11. **Verify** old Boilerplate v1.0 still used
12. **Verify** deliverable marked as "using older data"

### Expected Results (When Implemented)

✅ **Update Detection**:
- [ ] System detects Boilerplate v1.1 is available
- [ ] "Update Available" alert shown on deliverable
- [ ] Alert indicates which Elements have updates

✅ **Refresh Behavior**:
- [ ] Clicking "Refresh" pulls new Boilerplate v1.1
- [ ] Re-renders deliverable with new content
- [ ] Validation passes
- [ ] Version tracking updated to show v1.1

✅ **Defer Behavior**:
- [ ] Clicking "Defer" keeps old Boilerplate v1.0
- [ ] Deliverable marked with "outdated" indicator
- [ ] Can refresh later when ready

### Current Workaround

Until update alerts are implemented:
1. Manually note which Elements are used by deliverable
2. Update Element versions in UNF
3. Create new deliverable to test new Element content
4. Compare old vs. new deliverables

---

## Test Sequence 04: Edit Vision Statement to v1.1 (Draft) and Test Alerts

### Objective
Test alert behavior for dependent Deliverables when a linked Element is edited but not approved.

### Test Status
❌ **NOT YET IMPLEMENTED** - Requires draft Element alerts

### Dependencies
- Requires Test Sequence 01 completed
- Requires update alert system
- Requires draft vs. approved Element distinction in alerts

### What Needs to Be Implemented

Before this test can run:
1. **Draft Element Detection** - identify when Element is Draft
2. **Update Pending Alerts** - show different alert for Draft vs. Approved
3. **Refresh Blocking** - prevent refresh until Element is Approved
4. **Approval Workflow** - allow approving Draft Elements

### Steps (When Implemented)

1. **Navigate** to UNF Elements page
2. **Find** "Vision.Vision Statement" element
3. **Edit** element:
   - Change content slightly
   - Increment version to "1.1"
   - **Set status to "Draft"** (not Approved)
4. **Save** updated element

5. **Navigate** to Deliverables page
6. **Check** both "Brand Manifesto" and "Press Release"
7. **Look for** "Update Pending" notification
8. **Try** to click "Refresh"
9. **Verify** refresh is blocked with message: "Element is Draft, cannot refresh"

10. **Navigate** back to UNF Elements
11. **Find** Vision Statement v1.1
12. **Change status** to "Approved"
13. **Save** element

14. **Navigate** back to Deliverables
15. **Verify** "Update Pending" changes to "Update Available"
16. **Click** "Refresh"
17. **Verify** both deliverables update successfully

### Expected Results (When Implemented)

✅ **Draft Element Behavior**:
- [ ] Both Brand Manifesto and Press Release show "Update Pending"
- [ ] Alert indicates Element is Draft
- [ ] Refresh is blocked until Element is Approved
- [ ] Clear message explains why refresh is unavailable

✅ **After Approval**:
- [ ] Alert changes to "Update Available"
- [ ] Refresh button becomes enabled
- [ ] Both deliverables can be refreshed
- [ ] New Vision Statement v1.1 used in both
- [ ] Validation passes for both

### Current Workaround

Until alerts are implemented:
1. Edit Vision Statement as Draft
2. Note that deliverables don't automatically detect change
3. Approve Vision Statement
4. Create new deliverables to see new content

---

## Test Sequence 05: Swap Story Model in Manifesto (PAS → Inverted Pyramid)

### Objective
Verify reflow logic and revalidation when Story Model changes.

### Test Status
❌ **NOT YET IMPLEMENTED** - Requires Story Model switching

### Dependencies
- Requires Test Sequence 01 completed
- Requires ability to change Story Model on existing deliverable
- Requires section reflow logic
- Requires validation re-check

### What Needs to Be Implemented

Before this test can run:
1. **Story Model Switching** - UI to change Story Model
2. **Section Reflow** - remap sections to new Story Model structure
3. **Missing Content Detection** - identify which sections need content
4. **Validation Re-check** - re-run validation with new constraints

### Steps (When Implemented)

1. **Navigate** to Deliverables page
2. **Open** "Sequence Test 01 - Brand Manifesto"
3. **Click** "Edit" or "Settings"
4. **Change Story Model**:
   - From: "PAS Story Model v1.0"
   - To: "Inverted Pyramid Story Model v1.0"
5. **Click** "Apply" or "Save"

6. **Observe** section reflow:
   - Old sections: Problem, Agitate, Solve (3 sections)
   - New sections: Headline, Lede, Key Facts, Quote 1, Quote 2, Boilerplate (6 sections)

7. **Check** validation status
8. **Note** which sections are missing content
9. **Fill in** missing sections:
   - Add Headline content
   - Add Quote 1 with attribution
   - Add Quote 2 with attribution
   - Add Boilerplate

10. **Click** "Re-render"
11. **Verify** deliverable renders successfully with new structure

### Expected Results (When Implemented)

✅ **Reflow Behavior**:
- [ ] Sections reflow to match Inverted Pyramid structure
- [ ] Existing content retained where applicable
- [ ] New sections flagged as "missing content"

✅ **Validation**:
- [ ] Deliverable fails validation initially (missing sections)
- [ ] Specific validation errors shown:
  - "Headline section required"
  - "Quote 1 requires text and attribution"
  - "Quote 2 requires text and attribution"
  - "Boilerplate section required"

✅ **After Filling Sections**:
- [ ] All sections have content
- [ ] Validation passes
- [ ] Deliverable renders successfully
- [ ] Provenance logs record new Story Model ID

### Current Workaround

Story Model switching not available:
1. Create new Brand Manifesto with PAS model (Test 01)
2. Create separate Press Release with Inverted Pyramid model (Test 01)
3. Compare structures and validation rules
4. Note that switching would require content migration

---

## Test Sequence 06: End-to-End Provenance Check

### Objective
Confirm that provenance tracking works across all changes.

### Test Status
✅ **PARTIALLY READY** - Basic provenance exists, full history may be limited

### Dependencies
- Requires at least one deliverable created (Test Sequence 01)

### Steps

1. **Navigate** to Deliverables page
2. **Open** any deliverable from previous tests
3. **Look for** "Provenance" or "Details" section
4. **Review** provenance record

### What to Check

✅ **Element Versions Used**:
- [ ] Lists all UNF Element IDs used
- [ ] Shows version of each Element
- [ ] Indicates which sections use which Elements

✅ **Template Information**:
- [ ] Shows Deliverable Template ID
- [ ] Shows Template version used

✅ **Story Model Information**:
- [ ] Shows Story Model ID
- [ ] Shows Story Model version/name

✅ **Brand Voice Information**:
- [ ] Shows Brand Voice ID
- [ ] Shows Voice version used

✅ **Instance Data**:
- [ ] Shows all instance fields entered
- [ ] Values for who, what, when, where, why
- [ ] Quote attributions

✅ **Version History** (if implemented):
- [ ] Shows prior versions of this deliverable
- [ ] Timestamps for each render
- [ ] Changes made in each version

### Expected Results

✅ **Complete Provenance Record**:
- [ ] All Element IDs and versions listed
- [ ] Template version recorded
- [ ] Story Model ID recorded
- [ ] Brand Voice ID and version recorded
- [ ] Instance fields captured
- [ ] Creation timestamp present

⚠️ **Partial Results Acceptable**:
- Version history may not be fully implemented
- Some provenance fields may be incomplete
- Core tracking (Elements, Template, Voice) should be present

### Validation Steps

1. **Check Element Versions**:
   ```json
   {
     "element_versions": {
       "vision-statement": "1.0",
       "messaging-boilerplate": "1.0",
       ...
     }
   }
   ```

2. **Check Template Info**:
   ```json
   {
     "template_id": "06c9b4bd-c188-475f-b972-dc1e92998cfb",
     "template_version": "1.0"
   }
   ```

3. **Check Voice Info**:
   ```json
   {
     "voice_id": "voice-corporate-v1-0",
     "voice_version": "1.0"
   }
   ```

### Current State

The following provenance data is currently tracked in deliverables:
- `template_id`, `template_version`
- `story_model_id`
- `voice_id`, `voice_version`
- `element_versions` (JSONB object mapping Element IDs to versions)
- `instance_data` (JSONB object with who/what/when/etc.)
- `rendered_content` (final output by section)
- `created_at`, `updated_at` timestamps

**May not be implemented**:
- Full version history chain (prev_deliverable_id tracking exists but may not have UI)
- Detailed change logs between versions
- Render history with timestamps

---

## Test Summary Matrix

| Test | Status | Can Test Now? | Requirements | Workaround Available? |
|------|--------|---------------|--------------|----------------------|
| **01: Generate with Corporate Voice** | ✅ Ready | ✅ Yes | Basic deliverable creation | N/A |
| **02: Switch to Product Voice** | ⚠️ Partial | ⚠️ Maybe | Voice update/refresh | Create new deliverable |
| **03: Update Boilerplate & Refresh** | ❌ Not Ready | ❌ No | Update alert system | Manual comparison |
| **04: Draft Element Alerts** | ❌ Not Ready | ❌ No | Draft vs. Approved alerts | N/A |
| **05: Swap Story Model** | ❌ Not Ready | ❌ No | Story Model switching | Create separate deliverables |
| **06: Provenance Check** | ✅ Ready | ✅ Yes | Provenance display in UI | Check via API/DB |

---

## Recommended Test Order

### Phase 1: What You Can Test Now

1. ✅ **Test Sequence 01** - Create both deliverables
2. ✅ **Test Sequence 06** - Check provenance tracking
3. ⚠️ **Test Sequence 02** - Try voice switching or create new deliverable with different voice

### Phase 2: What Needs Implementation

4. ❌ **Test Sequence 03** - Implement update alert system first
5. ❌ **Test Sequence 04** - Implement draft Element alerts
6. ❌ **Test Sequence 05** - Implement Story Model switching

---

## Feature Implementation Checklist

To enable all tests, implement these features:

### High Priority (Enables Test 02)
- [ ] Deliverable update/edit UI
- [ ] Voice switching without creating new deliverable
- [ ] Re-render triggered by voice change

### Medium Priority (Enables Tests 03-04)
- [ ] Update detection system (compare Element versions)
- [ ] "Update Available" alerts in UI
- [ ] "Update Pending" alerts for Draft Elements
- [ ] Refresh/update button in deliverable view
- [ ] Element approval workflow in UI

### Lower Priority (Enables Test 05)
- [ ] Story Model switching in deliverable edit
- [ ] Section reflow logic
- [ ] Content migration between Story Models
- [ ] Validation re-check on Story Model change

### Nice to Have (Enhances Test 06)
- [ ] Full version history display
- [ ] Render history with timestamps
- [ ] Change log between versions
- [ ] Visual diff of changes

---

## Test Execution Log Template

Use this template to record test results:

```markdown
## Test Execution: [Date/Time]

### Test Sequence 01
**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL
**Brand Manifesto Created**: Yes/No
**Press Release Created**: Yes/No
**Issues Found**: [List any issues]
**Notes**: [Additional observations]

### Test Sequence 02
**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL / ⏭️ SKIPPED
**Voice Switched**: Yes/No
**Tone Changed**: Yes/No
**Issues Found**: [List any issues]
**Notes**: [Additional observations]

[... repeat for all 6 tests ...]
```

---

## Troubleshooting

### Issue: Deliverable won't create
- **Check**: All required instance fields filled?
- **Check**: Template and Voice selected?
- **Check**: Browser console for errors?
- **Fix**: Review instance field requirements for template

### Issue: Sections not rendering
- **Check**: UNF Elements exist and are "Approved"?
- **Check**: Section bindings configured in template?
- **Check**: Backend logs for errors?
- **Fix**: Verify template has bindings for all sections

### Issue: Quotes being transformed
- **Check**: Using transformation profiles?
- **Check**: Quote sections mapped to "preserve" profile?
- **Fix**: Verify transformation_profiles.py maps Quote sections correctly

### Issue: Voice not applying
- **Check**: Voice ID exists in database?
- **Check**: Voice has traits, tone_rules, lexicon configured?
- **Check**: LLM voice transformer working?
- **Fix**: Check backend logs for transformation errors

---

## Success Criteria

### Minimum Viable Test (Test 01 only)
- ✅ Can create Brand Manifesto deliverable
- ✅ Can create Press Release deliverable
- ✅ Both deliverables render without errors
- ✅ Sections contain expected content
- ✅ Quotes are preserved verbatim

### Full Test Suite
- ✅ All 6 test sequences pass
- ✅ Update alerts work correctly
- ✅ Voice switching works correctly
- ✅ Story Model switching works correctly
- ✅ Provenance tracking is complete
- ✅ No validation errors
- ✅ No system errors

---

**End of Test Guide**
