** Directory structure for Front End

web/
├── app/
│ ├── layout.tsx
│ ├── page.tsx # home / upload page
│ ├── upload/
│ │ └── page.tsx
│ ├── status/
│ │ └── [doc_id].tsx
│ ├── review/
│ │ └── flagged.tsx
│ └── auth/
│ ├── login.tsx
│ └── signup.tsx
├── components/
│ ├── Header.tsx
│ ├── Sidebar.tsx
│ ├── UploadForm.tsx
│ ├── ProgressBar.tsx
│ └── ReviewCard.tsx
├── styles/
└── utils/
└── api.ts


## Pages & components (requirements)
- All client-interactive components must include `'use client'`.
- Use Tailwind utility classes; responsive by default.
- Sidebar (left, 240px) with navigation items: Dashboard, Documents, Flagged (for reviewers), Settings. Bottom area for user profile.
- Top header with app title and user info.
- `UploadForm` component:
  - Allows file selection (single or batch)
  - Shows per-file upload progress (percentage)
  - Uses pre-signed upload flow:
    1. Call `POST /upload` (backend) to register doc; backend returns `doc_id` and `presigned_url` OR accepts the file if pre-signed not used
    2. Upload file via `PUT presigned_url` or form upload to API
    3. Show upload progress using `fetch` or `XMLHttpRequest` progress events
  - After upload, show link to status page `/status/{doc_id}`
- `Status` page (`/status/[doc_id]`):
  - Poll `GET /status/{doc_id}` every 3–5s (exponential backoff if queued long)
  - Show processing steps, per-step timestamps, and final extracted text when ready
  - Render bounding boxes overlay on page images (canvas overlay)
- `Flagged` page (review UI):
  - List of flagged docs with short summary (applicant, reason, confidence)
  - Clicking opens `ReviewCard`:
    - Shows extracted fields and confidence
    - Allow inline edit for a field and a comment box
    - Buttons: `Approve`, `Approve with Conditions` (open modal to specify conditions), `Reject`, `Request More Docs`
    - Submits to `POST /human_review/{doc_id}` and updates status in UI

## UI design constraints
- Colors:
  - Primary: `#0066FF`
  - Background: `#F5F5F7`
  - Text: `#1A1A1A`
- Sidebar width: `240px`
- Card corner radius: `rounded-xl` (~12px)
- Padding: consistent `p-6` (24px)
- Grid gaps: `gap-6` (24px)

## Minimal sample components (seed code)
### `components/UploadForm.tsx`
```tsx
'use client'
import React, {useState} from 'react'
import {UploadCloud} from 'lucide-react'
import {uploadFileToBackend} from '@/utils/api'

export default function UploadForm() {
  const [files, setFiles] = useState<FileList | null>(null)
  const [progress, setProgress] = useState<Record<string, number>>({})

  async function handleUpload() {
    if(!files) return
    for (const file of Array.from(files)) {
      const {doc_id, presigned_url} = await uploadFileToBackend(file.name)
      // upload with XHR to track progress
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('PUT', presigned_url)
        xhr.upload.onprogress = (e) => {
          const pct = Math.round((e.loaded / e.total) * 100)
          setProgress(p => ({...p, [doc_id]: pct}))
        }
        xhr.onload = () => resolve(true)
        xhr.onerror = () => reject()
        xhr.send(file)
      })
    }
  }

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm">
      <div className="flex items-center gap-4">
        <UploadCloud />
        <input type="file" multiple onChange={(e)=>setFiles(e.target.files)} />
      </div>
      <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded" onClick={handleUpload}>Upload</button>
      <div className="mt-4">
        {Object.keys(progress).map(id => (
          <div key={id} className="mb-2">
            <div>{id}</div>
            <div className="w-full bg-gray-200 h-2 rounded"><div style={{width: `${progress[id]}%`}} className="h-2 bg-blue-600 rounded" /></div>
          </div>
        ))}
      </div>
    </div>
  )
}

** utils/api.ts

export async function uploadFileToBackend(filename: string) {
  const res = await fetch('/api/remote-upload', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({filename})
  })
  return res.json() // {doc_id, presigned_url}
}


UX behavior & polling

After the upload finishes, redirect to /status/{doc_id} where the page polls GET /status/{doc_id} until status == done or flagged.

If flagged, show a prominent button "Open for review" which links to the reviewer UI (role-based).

Accessibility & validation

File input should accept .pdf only and show file size limits.

Friendly error messages on upload failure.

All forms should have labeled inputs for screen readers.

Tests (frontend)

Unit tests for UploadForm (simulate file selection + mock XHR upload)

Integration test for status page mocking backend polling responses

E2E smoke test: upload a small sample PDF and assert navigation to status page and eventual display of "Extracted Text"

Dev & Production

Dev: Next.js with next dev and proxied API to local FastAPI via next.config.js rewrites.

Prod: Build static Next app served by Node or a CDN. Provide Dockerfile.web and docker-compose entry.

Acceptance criteria (frontend)

Cursor builds a Next.js app with Supabase auth and the pages/components above.

Upload flow works end-to-end against the backend POST /upload and either:

Uses presigned URLs (preferred) OR

Posts file directly to API (acceptable for demo)

Status page displays step-by-step processing and shows final extracted text

Flagged review page accessible to reviewer users and can post review decisions

Deliverables

Source code in web/ with components, pages, Tailwind config, and tests

README for local dev steps, env vars, and how to link to backend

Minimal styling consistent with given palette and sizes