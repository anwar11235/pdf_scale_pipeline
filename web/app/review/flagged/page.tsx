'use client'

import { useState, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import ReviewCard from '@/components/ReviewCard'

interface FlaggedDocument {
  doc_id: string
  filename: string
  applicant_id: string | null
  reason: string
  confidence: number
  created_at: string
}

export default function FlaggedPage() {
  const [documents, setDocuments] = useState<FlaggedDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)

  useEffect(() => {
    const fetchFlagged = async () => {
      try {
        const response = await fetch('/api/flagged')
        if (!response.ok) {
          throw new Error('Failed to fetch flagged documents')
        }
        const data = await response.json()
        setDocuments(data)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching flagged documents:', err)
        setLoading(false)
      }
    }

    fetchFlagged()
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-gray-600">Loading flagged documents...</p>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Flagged Documents for Review</h1>

            {documents.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-6 text-center">
                <p className="text-gray-600">No documents flagged for review</p>
              </div>
            ) : (
              <div className="space-y-4">
                {documents.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className="bg-white rounded-xl shadow-sm p-6 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => setSelectedDoc(doc.doc_id)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-lg mb-2">{doc.filename}</h3>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Reason:</strong> {doc.reason}
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Confidence:</strong> {(doc.confidence * 100).toFixed(1)}%
                        </p>
                        {doc.applicant_id && (
                          <p className="text-sm text-gray-600">
                            <strong>Applicant ID:</strong> {doc.applicant_id}
                          </p>
                        )}
                      </div>
                      <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                        Flagged
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedDoc && (
              <ReviewCard
                docId={selectedDoc}
                onClose={() => setSelectedDoc(null)}
                onReviewSubmitted={() => {
                  setSelectedDoc(null)
                  // Refresh list
                  window.location.reload()
                }}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

