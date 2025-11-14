const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function uploadFileToBackend(filename: string) {
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename }),
  })
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.statusText}`)
  }
  return res.json() // {doc_id, presigned_url}
}

export async function getStatus(docId: string) {
  const res = await fetch(`${API_BASE}/status/${docId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch status: ${res.statusText}`)
  }
  return res.json()
}

export async function getResult(docId: string) {
  const res = await fetch(`${API_BASE}/result/${docId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch result: ${res.statusText}`)
  }
  return res.json()
}

export async function getFlaggedDocuments() {
  const res = await fetch(`${API_BASE}/flagged`)
  if (!res.ok) {
    throw new Error(`Failed to fetch flagged documents: ${res.statusText}`)
  }
  return res.json()
}

export async function submitReview(docId: string, review: any) {
  const res = await fetch(`${API_BASE}/human_review/${docId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(review),
  })
  if (!res.ok) {
    throw new Error(`Failed to submit review: ${res.statusText}`)
  }
  return res.json()
}

