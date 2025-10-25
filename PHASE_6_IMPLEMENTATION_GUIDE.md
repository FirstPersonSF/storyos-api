# Phase 6: Frontend Deliverable Alerts - Implementation Guide

## Status: READY TO IMPLEMENT

**Previous Phases Completed:**
- ✅ Phase 1: Draft Approval Workflow (Backend)
- ✅ Phase 2: Alert System Enhancement (Backend)
- ✅ Phase 3: Preview Feature (Backend)
- ✅ Phase 4: Template Binding Validation (Backend)
- ✅ Phase 5: Frontend Element Management

**Current Phase:** Phase 6 - Frontend Deliverable Alerts

---

## Overview

Phase 6 adds the final piece of the draft approval workflow: displaying impact alerts on deliverables and providing refresh/preview functionality.

### Key Features to Implement:

1. **Status-Based Alert Display** - Differentiate `update_pending` (yellow) vs `update_available` (blue)
2. **Smart Refresh Button** - Disable when draft updates exist, show helpful tooltips
3. **Preview Button** - Allow previewing deliverables with draft content
4. **Preview Modal** - Side-by-side comparison view

---

## Files to Modify

### 1. API Client
**File:** `/Users/drewf/Desktop/Python/storyos-frontend-vercel/storyos-frontend-vercel/lib/api/client.ts`

**Add to `deliverablesAPI` object (after line 67):**
```typescript
previewDeliverable: (id: string) => apiClient.post(`/deliverables/${id}/preview`),
```

---

### 2. Deliverables Page
**File:** `/Users/drewf/Desktop/Python/storyos-frontend-vercel/storyos-frontend-vercel/app/deliverables/page.tsx`

#### Current Alert Display (lines 269-298)
Currently treats all alerts the same (yellow warning). Needs to differentiate by `alert.status`.

#### Changes Needed:

**A. Add State Variables (after line 22):**
```typescript
const [showPreviewModal, setShowPreviewModal] = useState(false);
const [previewData, setPreviewData] = useState<any>(null);
const [isLoadingPreview, setIsLoadingPreview] = useState(false);
```

**B. Add Refresh Handler (after loadDeliverableWithAlerts function):**
```typescript
const handleRefresh = async (deliverableId: string) => {
  try {
    await deliverablesAPI.refreshDeliverable(deliverableId);
    loadDeliverables();
    loadDeliverableWithAlerts(deliverableId);
  } catch (err: any) {
    alert('Error refreshing deliverable: ' + err.message);
  }
};
```

**C. Add Preview Handler:**
```typescript
const handlePreview = async (deliverableId: string) => {
  setIsLoadingPreview(true);
  try {
    const response = await deliverablesAPI.previewDeliverable(deliverableId);
    setPreviewData(response.data);
    setShowPreviewModal(true);
  } catch (err: any) {
    alert('Error loading preview: ' + err.message);
  } finally {
    setIsLoadingPreview(false);
  }
};
```

**D. Replace Alert Display Section (lines 269-298):**
```typescript
{/* Update Alerts */}
{selectedDeliverable?.id === deliverable.id && (
  <div className="mb-6">
    {alerts && alerts.length > 0 ? (
      <div className="space-y-3">
        {/* Check for pending vs available updates */}
        {(() => {
          const pendingAlerts = alerts.filter((a: any) => a.status === 'update_pending');
          const availableAlerts = alerts.filter((a: any) => a.status === 'update_available');

          return (
            <>
              {/* Pending Updates (Draft) - Yellow Warning */}
              {pendingAlerts.length > 0 && (
                <div className="rounded-lg border-2 border-yellow-400 bg-yellow-50 p-6">
                  <div className="mb-4 flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    <h4 className="text-lg font-bold text-yellow-900">
                      ⚠️ {pendingAlerts.length} Draft Update{pendingAlerts.length !== 1 ? 's' : ''} Pending
                    </h4>
                  </div>
                  <div className="space-y-2 mb-4">
                    {pendingAlerts.map((alert: any, idx: number) => (
                      <div key={idx} className="text-sm text-yellow-800">
                        <strong>{alert.element_name}:</strong> {alert.message}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-yellow-700 mb-3">
                    Approve draft elements before refreshing this deliverable.
                  </p>
                  <Button
                    onClick={() => handlePreview(deliverable.id)}
                    disabled={isLoadingPreview}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-semibold"
                  >
                    {isLoadingPreview ? 'Loading...' : 'Preview with Drafts'}
                  </Button>
                </div>
              )}

              {/* Available Updates (Approved) - Blue Info */}
              {availableAlerts.length > 0 && (
                <div className="rounded-lg border-2 border-blue-400 bg-blue-50 p-6">
                  <div className="mb-4 flex items-center gap-3">
                    <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <h4 className="text-lg font-bold text-blue-900">
                      ℹ️ {availableAlerts.length} Update{availableAlerts.length !== 1 ? 's' : ''} Available
                    </h4>
                  </div>
                  <div className="space-y-2 mb-4">
                    {availableAlerts.map((alert: any, idx: number) => (
                      <div key={idx} className="text-sm text-blue-800">
                        <strong>{alert.element_name}:</strong> {alert.message}
                      </div>
                    ))}
                  </div>
                  <Button
                    onClick={() => handleRefresh(deliverable.id)}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh Deliverable
                  </Button>
                </div>
              )}
            </>
          );
        })()}
      </div>
    ) : (
      <div className="rounded-lg border-2 border-green-400 bg-green-50 p-6">
        <div className="flex items-center gap-3 text-green-700">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="font-bold">Up to date</span>
        </div>
      </div>
    )}
  </div>
)}
```

**E. Add Preview Modal (before closing div, around line 520):**
```typescript
{/* Preview Modal */}
{showPreviewModal && previewData && (
  <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-6">
    <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-foreground">Preview with Draft Content</h2>
          <Button
            onClick={() => setShowPreviewModal(false)}
            variant="outline"
            className="border-2"
          >
            Close
          </Button>
        </div>

        {previewData.draft_elements_used && previewData.draft_elements_used.length > 0 && (
          <div className="mb-6 p-4 bg-purple-50 border-2 border-purple-200 rounded-lg">
            <p className="text-sm font-bold text-purple-900 mb-2">
              Draft elements being previewed:
            </p>
            <div className="text-sm text-purple-800">
              {previewData.draft_elements_used.join(', ')}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Content */}
          <div className="border-2 border-gray-300 rounded-lg p-4">
            <h3 className="text-xl font-bold text-center mb-4 text-gray-700">Current</h3>
            <div className="space-y-4">
              {Object.entries(previewData.original_rendered_content || {}).map(([section, content]) => (
                <div key={section} className="border-b pb-4 last:border-b-0">
                  <h4 className="text-sm font-semibold text-[#003A70] mb-2">{section}</h4>
                  <ReactMarkdown className="text-sm text-gray-700 prose prose-sm max-w-none">
                    {content as string}
                  </ReactMarkdown>
                </div>
              ))}
            </div>
          </div>

          {/* Preview with Drafts */}
          <div className="border-2 border-purple-500 rounded-lg p-4 bg-purple-50">
            <h3 className="text-xl font-bold text-center mb-4 text-purple-700">With Drafts</h3>
            <div className="space-y-4">
              {Object.entries(previewData.preview_rendered_content || {}).map(([section, content]) => (
                <div key={section} className="border-b border-purple-200 pb-4 last:border-b-0">
                  <h4 className="text-sm font-semibold text-purple-700 mb-2">{section}</h4>
                  <ReactMarkdown className="text-sm text-gray-900 prose prose-sm max-w-none">
                    {content as string}
                  </ReactMarkdown>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 text-center text-sm text-gray-600">
          {previewData.preview_note}
        </div>
      </div>
    </div>
  </div>
)}
```

---

## Testing Checklist

After implementation, verify:

- [ ] Yellow alert appears for `update_pending` (draft exists)
- [ ] Blue alert appears for `update_available` (approved update)
- [ ] "Preview with Drafts" button appears when pending updates exist
- [ ] Preview modal shows side-by-side comparison
- [ ] "Refresh Deliverable" button appears when approved updates exist
- [ ] Refresh button updates deliverable with latest approved versions
- [ ] Preview doesn't modify actual deliverable
- [ ] Alerts clear after successful refresh

---

## Backend APIs Already Implemented

All backend endpoints are ready:
- ✅ `GET /deliverables/{id}/with-alerts` - Returns deliverable with alerts
- ✅ `POST /deliverables/{id}/refresh` - Refreshes with latest approved versions
- ✅ `POST /deliverables/{id}/preview` - Previews with draft content

---

## Summary

Phase 6 completes the Draft Approval Workflow by:
1. Adding visual distinction between draft (pending) and approved (available) updates
2. Providing preview functionality to see draft content before approval
3. Enabling smart refresh that only works with approved updates
4. Giving users clear guidance on what actions to take

This is the **FINAL PHASE** of the 6-phase Draft Approval Workflow implementation.
