# Draft Approval Workflow - Technical Specification

**Version:** 1.0
**Date:** 2025-10-24
**Status:** Planning

---

## Overview

This document defines the implementation plan for adding a draft/approval workflow to UNF Elements. The workflow ensures that all content changes go through review before being published to deliverables.

## Business Requirements

### Core Workflow

```
NEW ELEMENT:     draft → approved
UPDATE ELEMENT:  approved → (old: superseded, new: draft) → approved
DELETE:          Only draft elements can be deleted
EDIT:            Only draft elements can be edited
```

### Key Rules

1. **All new elements start as draft** and require approval
2. **Draft-only elements cannot be bound to deliverables**
3. **Drafts are editable** - can be modified multiple times before approval
4. **Approved elements are immutable** - can only be superseded by creating new version
5. **Drafts can be deleted/abandoned**
6. **Only approved elements** show in deliverable creation/refresh flows
7. **Draft updates block deliverable refresh** until approved
8. **Users can preview deliverables** with draft content before approving

### Alert Types

| Alert Type | Condition | UI Display | Action Available |
|------------|-----------|------------|------------------|
| `update_pending` | Draft version exists | Yellow badge: "Draft v{X} pending approval" | Refresh disabled, Preview enabled |
| `update_available` | Approved version exists | Blue badge: "Update available" | Refresh enabled |

---

## Implementation Phases

### Phase 1: Backend Element Management (Session 1)
**Estimated Context:** ~30K tokens
**Goal:** Enable draft creation, editing, deletion, and approval

#### 1.1 Update Element Model
**File:** `models/unf.py`

**Changes:**
- Change default `status` from `"approved"` to `"draft"`
- No schema changes needed (status already supports draft/approved/superseded)

**Code Location:** Line ~15-20 (ElementCreate model)

**Testing:**
- Create new element via API → verify status="draft"
- Verify existing approved elements still work

---

#### 1.2 Add Element Deletion
**File:** `api/routes/unf.py`

**New Endpoint:**
```python
@router.delete("/elements/{element_id}", status_code=204)
def delete_element(
    element_id: UUID,
    service: UNFService = Depends(get_unf_service)
):
    """
    Delete a draft element

    Only draft elements can be deleted. Attempting to delete
    approved or superseded elements returns 400 error.
    """
```

**Service Method:**
**File:** `services/unf_service.py`

```python
def delete_element(self, element_id: UUID) -> None:
    """Delete draft element"""
    element = self.get_element(element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found")

    if element.status != "draft":
        raise ValueError(
            f"Cannot delete {element.status} element. "
            f"Only draft elements can be deleted."
        )

    self.storage.delete_one("unf_elements", element_id)
```

**Testing:**
- Create draft element → delete it → verify 204 response
- Try to delete approved element → verify 400 error
- Try to delete non-existent element → verify 404 error

---

#### 1.3 Add Element Editing
**File:** `api/routes/unf.py`

**New Endpoint:**
```python
@router.put("/elements/{element_id}")
def update_element(
    element_id: UUID,
    update_data: ElementUpdate,
    service: UNFService = Depends(get_unf_service)
):
    """
    Update a draft element

    Only draft elements can be edited. Attempting to edit
    approved or superseded elements returns 400 error.
    """
```

**Model:**
**File:** `models/unf.py`

```python
class ElementUpdate(BaseModel):
    """Update model for draft elements"""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

**Service Method:**
**File:** `services/unf_service.py`

```python
def update_element(self, element_id: UUID, update_data: ElementUpdate) -> Element:
    """Update draft element"""
    element = self.get_element(element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found")

    if element.status != "draft":
        raise ValueError(
            f"Cannot edit {element.status} element. "
            f"Only draft elements can be edited."
        )

    # Update fields
    data = {}
    if update_data.content is not None:
        data['content'] = update_data.content
    if update_data.metadata is not None:
        data['metadata'] = json.dumps(update_data.metadata)

    self.storage.update_one("unf_elements", element_id, data)
    return self.get_element(element_id)
```

**Testing:**
- Create draft → edit content → verify changes saved
- Try to edit approved element → verify 400 error
- Edit draft multiple times → verify each change persists

---

#### 1.4 Enhance Approval Workflow
**File:** `services/unf_service.py`

**Update Method:** `approve_element()`

**Current Logic:**
```python
# Just sets status to approved
```

**New Logic:**
```python
def approve_element(self, element_id: UUID) -> Element:
    """
    Approve a draft element

    If another approved version with the same name exists,
    it will be superseded.
    """
    element = self.get_element(element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found")

    if element.status != "draft":
        raise ValueError(f"Element is already {element.status}")

    # Find existing approved version with same name
    all_elements = self.list_elements()
    existing_approved = None

    for elem in all_elements:
        if (elem.name == element.name and
            elem.status == "approved" and
            elem.id != element_id):
            existing_approved = elem
            break

    # If approved version exists, supersede it
    if existing_approved:
        self.storage.update_one(
            "unf_elements",
            existing_approved.id,
            {"status": "superseded"}
        )

    # Approve the draft
    self.storage.update_one(
        "unf_elements",
        element_id,
        {"status": "approved"}
    )

    return self.get_element(element_id)
```

**Testing:**
- Create draft → approve → verify status="approved"
- Create draft with same name as existing approved → approve → verify old becomes superseded
- Try to approve already approved element → verify error

---

### Phase 1 Testing Checklist

Before moving to Phase 2, verify:

- [ ] New elements default to draft status
- [ ] Draft elements can be edited multiple times
- [ ] Draft elements can be deleted
- [ ] Approved elements cannot be edited
- [ ] Approved elements cannot be deleted
- [ ] Approving draft with existing approved name supersedes old version
- [ ] All existing deliverables still work with approved elements

---

## Phase 2: Alert System Enhancement (Session 2)
**Estimated Context:** ~25K tokens
**Goal:** Detect draft vs approved updates and return appropriate alerts

#### 2.1 Update Alert Detection Logic
**File:** `services/deliverable_service.py`

**Method:** `_check_for_updates()`

**Current Logic:**
```python
# Checks if latest approved version > used version
# Returns generic alert
```

**New Logic:**
```python
def _check_for_updates(self, deliverable: Deliverable) -> List[ImpactAlert]:
    """
    Check for element updates (both draft and approved)

    Returns:
        List of ImpactAlert with status:
        - "update_pending": Draft exists, blocks refresh
        - "update_available": Approved update exists, allows refresh
    """
    alerts = []

    for elem_id_str, used_version in deliverable.element_versions.items():
        elem_id = UUID(elem_id_str)
        current_element = self.unf_service.get_element(elem_id)

        if not current_element:
            continue

        # Find all versions by name
        all_elements = self.unf_service.list_elements()
        same_name_elements = [
            e for e in all_elements
            if e.name == current_element.name
        ]

        # Find latest draft and latest approved
        latest_draft = None
        latest_approved = None
        highest_draft_version = "0.0"
        highest_approved_version = "0.0"

        for elem in same_name_elements:
            if elem.status == "draft" and elem.version > highest_draft_version:
                highest_draft_version = elem.version
                latest_draft = elem
            elif elem.status == "approved" and elem.version > highest_approved_version:
                highest_approved_version = elem.version
                latest_approved = elem

        # Priority: Draft alerts block approved alerts
        if latest_draft and latest_draft.version > used_version:
            alerts.append(ImpactAlert(
                element_id=str(latest_draft.id),
                element_name=latest_draft.name,
                old_version=used_version,
                new_version=latest_draft.version,
                status="update_pending",
                message=f"Draft v{latest_draft.version} pending approval"
            ))
        elif latest_approved and latest_approved.version > used_version:
            alerts.append(ImpactAlert(
                element_id=str(latest_approved.id),
                element_name=latest_approved.name,
                old_version=used_version,
                new_version=latest_approved.version,
                status="update_available",
                message=f"Update available to v{latest_approved.version}"
            ))

    return alerts
```

**Testing:**
- Deliverable uses Element v1.0 (approved)
- Create Element v1.1 (draft) → verify alert shows "update_pending"
- Approve Element v1.1 → verify alert changes to "update_available"
- Refresh deliverable → verify alert disappears

---

#### 2.2 Update Refresh Blocking Logic
**File:** `services/deliverable_service.py`

**Method:** `refresh_deliverable()`

**Current Logic:**
```python
# Blocks if ANY draft updates exist
if draft_alerts:
    raise ValueError(...)
```

**Keep Current Logic:** Already correctly blocks on draft updates

**Testing:**
- Try to refresh with update_pending alert → verify blocked with clear error message
- Approve draft → try to refresh → verify succeeds

---

### Phase 2 Testing Checklist

- [ ] Alert shows "update_pending" when draft exists
- [ ] Alert shows "update_available" when approved update exists
- [ ] Draft alerts take priority over approved alerts
- [ ] Refresh is blocked when update_pending alerts exist
- [ ] Refresh succeeds when only update_available alerts exist
- [ ] Alert message includes version numbers

---

## Phase 3: Preview Feature (Session 3)
**Estimated Context:** ~20K tokens
**Goal:** Allow users to preview deliverables with draft content

#### 3.1 Add Preview Endpoint
**File:** `api/routes/deliverables.py`

**New Endpoint:**
```python
@router.post("/{deliverable_id}/preview")
def preview_deliverable_with_drafts(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Preview deliverable with draft element versions

    Temporarily renders the deliverable using draft versions of elements
    where drafts exist. Does not save changes to database.

    Returns the same structure as a regular deliverable, but with
    rendered_content showing what it would look like with drafts applied.
    """
```

**Service Method:**
**File:** `services/deliverable_service.py`

```python
def preview_deliverable_with_drafts(self, deliverable_id: UUID) -> Dict[str, Any]:
    """
    Preview deliverable with draft content

    Returns rendered content using draft versions where available,
    without modifying the actual deliverable.
    """
    deliverable = self.get_deliverable(deliverable_id)
    if not deliverable:
        raise ValueError(f"Deliverable {deliverable_id} not found")

    # Get template and voice
    template = self.template_service.get_template_with_bindings(deliverable.template_id)
    voice = self.voice_service.get_voice(deliverable.voice_id)
    story_model = self.story_model_service.get_story_model(deliverable.story_model_id)

    # For each element used, find draft version if it exists
    preview_rendered_content = {}

    for binding in template.section_bindings:
        preview_element_ids = []

        for elem_id in binding.element_ids:
            current_element = self.unf_service.get_element(elem_id)
            if not current_element:
                continue

            # Find latest draft with same name
            all_elements = self.unf_service.list_elements()
            latest_draft = None
            highest_version = "0.0"

            for elem in all_elements:
                if (elem.name == current_element.name and
                    elem.status == "draft" and
                    elem.version > highest_version):
                    highest_version = elem.version
                    latest_draft = elem

            # Use draft if exists, otherwise use current
            if latest_draft:
                preview_element_ids.append(latest_draft.id)
            else:
                preview_element_ids.append(elem_id)

        # Create temporary binding with preview element IDs
        from copy import copy
        preview_binding = copy(binding)
        preview_binding.element_ids = preview_element_ids

        # Render section with preview elements
        section_content, _ = self._assemble_section_content(
            preview_binding,
            deliverable.instance_data,
            story_model,
            voice,
            template
        )

        preview_rendered_content[binding.section_name] = section_content

    return {
        "deliverable_id": str(deliverable_id),
        "preview_rendered_content": preview_rendered_content,
        "original_rendered_content": deliverable.rendered_content,
        "preview_note": "This is a preview with draft content. Changes are not saved."
    }
```

**Testing:**
- Deliverable uses Element v1.0
- Create Element v1.1 (draft) with different content
- Preview deliverable → verify shows v1.1 content
- Check actual deliverable → verify still uses v1.0
- Approve v1.1 → refresh → verify matches preview

---

### Phase 3 Testing Checklist

- [ ] Preview shows draft content where drafts exist
- [ ] Preview shows original content where no drafts exist
- [ ] Preview does not modify actual deliverable
- [ ] Preview handles multiple draft updates correctly
- [ ] Preview response includes both preview and original content

---

## Phase 4: Template Binding Validation (Session 4)
**Estimated Context:** ~15K tokens
**Goal:** Prevent binding draft-only elements to templates

#### 4.1 Add Binding Validation
**File:** `services/template_service.py`

**Method:** `create_section_binding()`

**Add Validation:**
```python
def create_section_binding(self, template_id: UUID, binding_data: SectionBindingCreate):
    """
    Create section binding

    Validates that all elements have approved versions before binding.
    """
    # Validate element_ids
    for elem_id in binding_data.element_ids:
        element = self.unf_service.get_element(elem_id)
        if not element:
            raise ValueError(f"Element {elem_id} not found")

        # Check if this element has an approved version
        all_elements = self.unf_service.list_elements()
        has_approved = any(
            e.name == element.name and e.status == "approved"
            for e in all_elements
        )

        if not has_approved:
            raise ValueError(
                f"Cannot bind element '{element.name}': "
                f"No approved version exists. "
                f"Please approve the element before binding."
            )

    # ... rest of binding creation
```

**Testing:**
- Create draft element → try to bind to template → verify error
- Approve element → try to bind → verify succeeds
- Bind approved element → create draft update → verify binding still valid

---

### Phase 4 Testing Checklist

- [ ] Cannot bind draft-only elements
- [ ] Can bind approved elements
- [ ] Can bind elements that have draft updates (as long as approved version exists)
- [ ] Clear error message when trying to bind draft-only element

---

## Phase 5: Frontend - Element Management (Session 5)
**Estimated Context:** ~35K tokens
**Goal:** UI for creating, editing, approving, and deleting draft elements

#### 5.1 Update Element List
**File:** `app/unf/page.tsx` (or equivalent)

**Add Status Badge:**
```tsx
{element.status === 'draft' && (
  <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded">
    Draft
  </span>
)}
{element.status === 'approved' && (
  <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
    Approved
  </span>
)}
{element.status === 'superseded' && (
  <span className="px-2 py-1 bg-gray-400 text-white text-xs rounded">
    Superseded
  </span>
)}
```

**Add Status Filter:**
```tsx
<select onChange={(e) => setStatusFilter(e.target.value)}>
  <option value="active">Active (Draft + Approved)</option>
  <option value="draft">Draft Only</option>
  <option value="approved">Approved Only</option>
  <option value="all">All Including Superseded</option>
</select>
```

---

#### 5.2 Add Action Buttons Based on Status
**Component:** Element card/row

**Draft Element Actions:**
```tsx
{element.status === 'draft' && (
  <>
    <button onClick={() => handleEdit(element.id)}>Edit</button>
    <button onClick={() => handleApprove(element.id)}>Approve</button>
    <button onClick={() => handleDelete(element.id)}>Delete</button>
  </>
)}
```

**Approved Element Actions:**
```tsx
{element.status === 'approved' && (
  <button onClick={() => handleCreateNewVersion(element)}>
    Create New Version
  </button>
)}
```

**Superseded Element Actions:**
```tsx
{element.status === 'superseded' && (
  <button onClick={() => handleView(element.id)}>
    View Only
  </button>
)}
```

---

#### 5.3 Add Edit Modal
**New Component:** `ElementEditModal.tsx`

```tsx
interface ElementEditModalProps {
  elementId: string;
  onClose: () => void;
  onSave: () => void;
}

export default function ElementEditModal({ elementId, onClose, onSave }: ElementEditModalProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load element content
    fetchElement(elementId).then(el => setContent(el.content));
  }, [elementId]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await unfAPI.updateElement(elementId, { content });
      onSave();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal>
      <h2>Edit Draft Element</h2>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={10}
      />
      <button onClick={handleSave} disabled={loading}>
        Save Changes
      </button>
      <button onClick={onClose}>Cancel</button>
    </Modal>
  );
}
```

---

#### 5.4 Add API Client Methods
**File:** `lib/api/client.ts`

```typescript
export const unfAPI = {
  // ... existing methods

  updateElement: (id: string, data: { content?: string; metadata?: any }) =>
    apiClient.put(`/unf/elements/${id}`, data),

  deleteElement: (id: string) =>
    apiClient.delete(`/unf/elements/${id}`),
};
```

---

### Phase 5 Testing Checklist

- [ ] Element list shows status badges
- [ ] Status filter works correctly
- [ ] Draft elements show Edit/Approve/Delete buttons
- [ ] Approved elements show "Create New Version" button
- [ ] Edit modal loads draft content
- [ ] Edit modal saves changes successfully
- [ ] Approve button changes status to approved
- [ ] Delete button removes draft elements

---

## Phase 6: Frontend - Deliverable Alerts (Session 6)
**Estimated Context:** ~30K tokens
**Goal:** Display different alerts and handle refresh/preview

#### 6.1 Update Alert Display
**File:** `app/components/DeliverableCard.tsx`

**Current Alert UI:**
```tsx
{deliverable.alerts && deliverable.alerts.map(alert => (
  <div className="alert">
    {alert.message}
  </div>
))}
```

**New Alert UI:**
```tsx
{deliverable.alerts && deliverable.alerts.map(alert => (
  <div className={`alert ${
    alert.status === 'update_pending' ? 'bg-yellow-100 border-yellow-500' :
    'bg-blue-100 border-blue-500'
  }`}>
    {alert.status === 'update_pending' && (
      <>
        <span className="text-yellow-700">⚠️ Draft Update Pending</span>
        <p className="text-sm">{alert.element_name}: {alert.message}</p>
      </>
    )}
    {alert.status === 'update_available' && (
      <>
        <span className="text-blue-700">ℹ️ Update Available</span>
        <p className="text-sm">{alert.element_name}: {alert.message}</p>
      </>
    )}
  </div>
))}
```

---

#### 6.2 Update Refresh Button
**File:** `app/components/DeliverableCard.tsx`

**Add Logic:**
```tsx
// Check if any alerts are pending
const hasPendingUpdates = deliverable.alerts?.some(
  a => a.status === 'update_pending'
) ?? false;

const hasAvailableUpdates = deliverable.alerts?.some(
  a => a.status === 'update_available'
) ?? false;

// Get list of pending element names for tooltip
const pendingElements = deliverable.alerts
  ?.filter(a => a.status === 'update_pending')
  .map(a => a.element_name)
  .join(', ') ?? '';
```

**Update Button:**
```tsx
<button
  onClick={handleRefresh}
  disabled={hasPendingUpdates}
  title={hasPendingUpdates
    ? `Approve draft updates first: ${pendingElements}`
    : 'Refresh with latest approved versions'
  }
  className={hasPendingUpdates
    ? 'opacity-50 cursor-not-allowed'
    : 'hover:bg-blue-700'
  }
>
  Refresh
</button>
```

---

#### 6.3 Add Preview Button
**File:** `app/components/DeliverableCard.tsx`

**Add Preview State:**
```tsx
const [showPreview, setShowPreview] = useState(false);
const [previewContent, setPreviewContent] = useState(null);
const [isLoadingPreview, setIsLoadingPreview] = useState(false);
```

**Add Preview Button:**
```tsx
{hasPendingUpdates && (
  <button
    onClick={handlePreview}
    className="bg-purple-600 hover:bg-purple-700"
  >
    Preview with Drafts
  </button>
)}
```

**Handle Preview:**
```tsx
const handlePreview = async () => {
  setIsLoadingPreview(true);
  try {
    const response = await deliverablesAPI.previewDeliverable(deliverable.id);
    setPreviewContent(response.data);
    setShowPreview(true);
  } finally {
    setIsLoadingPreview(false);
  }
};
```

---

#### 6.4 Add Preview Modal
**New Component:** `DeliverablePreviewModal.tsx`

```tsx
interface PreviewModalProps {
  previewData: {
    preview_rendered_content: Record<string, string>;
    original_rendered_content: Record<string, string>;
  };
  onClose: () => void;
}

export default function DeliverablePreviewModal({ previewData, onClose }: PreviewModalProps) {
  const [viewMode, setViewMode] = useState<'preview' | 'comparison'>('preview');

  return (
    <Modal size="xl">
      <div className="flex justify-between items-center mb-4">
        <h2>Preview with Draft Content</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('preview')}
            className={viewMode === 'preview' ? 'active' : ''}
          >
            Preview Only
          </button>
          <button
            onClick={() => setViewMode('comparison')}
            className={viewMode === 'comparison' ? 'active' : ''}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {viewMode === 'preview' && (
        <div className="preview-content">
          {Object.entries(previewData.preview_rendered_content).map(([section, content]) => (
            <div key={section} className="section">
              <h3>{section}</h3>
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          ))}
        </div>
      )}

      {viewMode === 'comparison' && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-center font-bold mb-2">Current</h3>
            {Object.entries(previewData.original_rendered_content).map(([section, content]) => (
              <div key={section} className="section">
                <h4>{section}</h4>
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            ))}
          </div>
          <div>
            <h3 className="text-center font-bold mb-2">With Drafts</h3>
            {Object.entries(previewData.preview_rendered_content).map(([section, content]) => (
              <div key={section} className="section">
                <h4>{section}</h4>
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
```

---

#### 6.5 Add API Client Method
**File:** `lib/api/client.ts`

```typescript
export const deliverablesAPI = {
  // ... existing methods

  previewDeliverable: (id: string) =>
    apiClient.post(`/deliverables/${id}/preview`),
};
```

---

### Phase 6 Testing Checklist

- [ ] Yellow alert appears for update_pending
- [ ] Blue alert appears for update_available
- [ ] Refresh button disabled when update_pending exists
- [ ] Tooltip shows which elements need approval
- [ ] Preview button appears when update_pending exists
- [ ] Preview modal shows draft content
- [ ] Side-by-side comparison works
- [ ] Preview doesn't modify actual deliverable

---

## End-to-End Test Sequence

### Test Sequence 1: Create and Approve New Element

1. Create new element "Vision Statement" via API
   - ✓ Verify status="draft"
2. Try to bind to template
   - ✓ Verify error: no approved version
3. Approve element
   - ✓ Verify status="approved"
4. Bind to template
   - ✓ Verify binding succeeds
5. Create deliverable using template
   - ✓ Verify deliverable uses element content

---

### Test Sequence 2: Edit Draft Before Approval

1. Create draft element "Mission Statement"
   - ✓ Verify status="draft"
2. Edit content 3 times
   - ✓ Verify each edit saves
3. Approve element
   - ✓ Verify final content matches last edit
4. Try to edit approved element
   - ✓ Verify error: cannot edit approved element

---

### Test Sequence 3: Update Approved Element

1. Create and approve "Value Proposition" v1.0
2. Create deliverable using Value Proposition
3. Create new draft version v1.1 with updated content
   - ✓ Verify v1.0 still status="approved"
   - ✓ Verify v1.1 status="draft"
4. View deliverable
   - ✓ Verify alert shows "update_pending"
   - ✓ Verify refresh button disabled
5. Preview deliverable
   - ✓ Verify shows v1.1 content
6. Approve v1.1
   - ✓ Verify v1.0 becomes "superseded"
   - ✓ Verify v1.1 becomes "approved"
7. View deliverable
   - ✓ Verify alert shows "update_available"
   - ✓ Verify refresh button enabled
8. Refresh deliverable
   - ✓ Verify uses v1.1 content
   - ✓ Verify alert disappears

---

### Test Sequence 4: Multiple Draft Updates (from requirements)

**Initial State:**
- Vision Statement v1.0 (approved) - used by Brand Manifesto & Press Release

**Steps:**

1. Edit Vision Statement to v1.1 (Draft)
   - ✓ Create Vision Statement v1.1 with status="draft"
   - ✓ Vision v1.0 remains status="approved"

2. View both Deliverables
   - ✓ Both show "Update Pending" notification (yellow)
   - ✓ Refresh button disabled with tooltip
   - ✓ Preview button visible

3. Try to Refresh (Should Block)
   - ✓ Refresh button disabled
   - ✓ Tooltip: "Approve draft updates first: Vision Statement"

4. Preview Deliverables
   - ✓ Preview shows Vision v1.1 content
   - ✓ Side-by-side comparison available
   - ✓ Original deliverable unchanged

5. Approve Vision Statement v1.1
   - ✓ Vision v1.0 → status="superseded"
   - ✓ Vision v1.1 → status="approved"

6. View Deliverables Again
   - ✓ Alert changes to "Update Available" (blue)
   - ✓ Refresh button enabled

7. Refresh Both Deliverables
   - ✓ Both pull Vision v1.1 content
   - ✓ Validation passes
   - ✓ Alerts disappear

---

### Test Sequence 5: Delete Abandoned Draft

1. Create draft element "Tagline" v1.0
2. Decide not to use it
3. Delete draft
   - ✓ Verify element deleted from database
4. Try to delete approved element
   - ✓ Verify error: cannot delete approved element

---

## Database Migration Considerations

**Current Schema:** Already supports draft/approved/superseded status values

**No migration needed** - just changing application defaults and logic

**Data Cleanup (Optional):**
If you want to mark existing approved elements explicitly:
```sql
UPDATE unf_elements
SET status = 'approved'
WHERE status IS NULL OR status = '';
```

---

## API Endpoints Summary

### New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| PUT | `/unf/elements/{id}` | Edit draft element |
| DELETE | `/unf/elements/{id}` | Delete draft element |
| POST | `/deliverables/{id}/preview` | Preview with draft content |

### Modified Endpoints

| Endpoint | Change |
|----------|--------|
| `POST /unf/elements` | Default status="draft" |
| `POST /unf/elements/{id}/approve` | Enhanced superseding logic |
| `GET /deliverables/{id}/with-alerts` | Returns update_pending vs update_available |

---

## Frontend Components Summary

### New Components

1. `ElementEditModal.tsx` - Edit draft element content
2. `DeliverablePreviewModal.tsx` - Preview deliverable with drafts

### Modified Components

1. Element list - Add status badges and filters
2. Element card/row - Add action buttons based on status
3. DeliverableCard - Update alerts and add preview button

---

## Session Breakdown

| Session | Phase | Estimated Time | Context Usage |
|---------|-------|----------------|---------------|
| 1 | Backend Element Management | 1-2 hours | ~30K tokens |
| 2 | Alert System Enhancement | 1 hour | ~25K tokens |
| 3 | Preview Feature | 1 hour | ~20K tokens |
| 4 | Template Binding Validation | 30 min | ~15K tokens |
| 5 | Frontend Element Management | 2 hours | ~35K tokens |
| 6 | Frontend Deliverable Alerts | 1-2 hours | ~30K tokens |

**Total:** 6-8 hours across 6 sessions

---

## Next Steps

When ready to begin implementation:

1. Review this spec document
2. Start with Phase 1 (Backend Element Management)
3. Test thoroughly after each phase
4. Reference this document in each session
5. Update test results in this document as you go

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-24 | 1.0 | Initial specification |
