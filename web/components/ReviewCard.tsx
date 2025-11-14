'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'

interface ReviewCardProps {
  docId: string
  onClose: () => void
  onReviewSubmitted: () => void
}

interface Field {
  field_name: string
  field_value: string | null
  confidence: number | null
  page_no: number | null
}

interface ResultData {
  doc_id: string
  filename: string
  fields: Field[]
}

export default function ReviewCard({ docId, onClose, onReviewSubmitted }: ReviewCardProps) {
  const [resultData, setResultData] = useState<ResultData | null>(null)
  const [loading, setLoading] = useState(true)
  const [corrections, setCorrections] = useState<Record<string, string>>({})
  const [comments, setComments] = useState('')
  const [decision, setDecision] = useState('')
  const [conditions, setConditions] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const response = await fetch(`/api/result/${docId}`)
        if (!response.ok) {
          throw new Error('Failed to fetch document result')
        }
        const data = await response.json()
        setResultData(data)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching result:', err)
        setLoading(false)
      }
    }

    fetchResult()
  }, [docId])

  const handleSubmit = async () => {
    if (!decision) {
      alert('Please select a decision')
      return
    }

    setSubmitting(true)
    try {
      const response = await fetch(`/api/human_review/${docId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          decision,
          comments,
          corrections: Object.keys(corrections).length > 0 ? corrections : undefined,
          conditions: decision === 'approve_with_conditions' ? conditions : undefined,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit review')
      }

      onReviewSubmitted()
    } catch (err) {
      console.error('Error submitting review:', err)
      alert('Failed to submit review. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        </div>
      </div>
    )
  }

  if (!resultData) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold">Review Document</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Document: {resultData.filename}</h3>
            <p className="text-sm text-gray-600">Document ID: {resultData.doc_id}</p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Extracted Fields</h3>
            <div className="space-y-3">
              {resultData.fields.map((field, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <label className="font-medium text-sm text-gray-700">
                      {field.field_name}
                    </label>
                    <span className="text-xs text-gray-500">
                      Confidence: {field.confidence ? (field.confidence * 100).toFixed(1) : 'N/A'}%
                    </span>
                  </div>
                  <input
                    type="text"
                    defaultValue={field.field_value || ''}
                    onChange={(e) =>
                      setCorrections((prev) => ({
                        ...prev,
                        [field.field_name]: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block font-medium text-sm text-gray-700 mb-2">
              Comments
            </label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              rows={4}
            />
          </div>

          {decision === 'approve_with_conditions' && (
            <div>
              <label className="block font-medium text-sm text-gray-700 mb-2">
                Conditions
              </label>
              <textarea
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                rows={3}
              />
            </div>
          )}

          <div>
            <label className="block font-medium text-sm text-gray-700 mb-2">
              Decision
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setDecision('approve')}
                className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                  decision === 'approve'
                    ? 'border-green-500 bg-green-50 text-green-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                Approve
              </button>
              <button
                onClick={() => setDecision('approve_with_conditions')}
                className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                  decision === 'approve_with_conditions'
                    ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                Approve with Conditions
              </button>
              <button
                onClick={() => setDecision('reject')}
                className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                  decision === 'reject'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                Reject
              </button>
              <button
                onClick={() => setDecision('request_more_docs')}
                className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                  decision === 'request_more_docs'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                Request More Docs
              </button>
            </div>
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!decision || submitting}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {submitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

