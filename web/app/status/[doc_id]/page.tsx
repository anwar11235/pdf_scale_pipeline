'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import ProgressBar from '@/components/ProgressBar'

interface StatusData {
  doc_id: string
  status: string
  current_step: string | null
  progress_percent: number
  steps: Array<{
    step: string
    status: string
    details: any
    created_at: string | null
    updated_at: string | null
  }>
  created_at: string
  updated_at: string
}

export default function StatusPage() {
  const params = useParams()
  const router = useRouter()
  const docId = params.doc_id as string
  const [statusData, setStatusData] = useState<StatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`/api/status/${docId}`)
        if (!response.ok) {
          throw new Error('Failed to fetch status')
        }
        const data = await response.json()
        setStatusData(data)
        setLoading(false)
        
        // If processing is complete, stop polling
        if (data.status === 'complete' || data.status === 'failed' || data.status === 'flagged') {
          return
        }
      } catch (err) {
        setError((err as Error).message)
        setLoading(false)
      }
    }

    // Initial fetch
    fetchStatus()

    // Poll every 3 seconds
    const interval = setInterval(fetchStatus, 3000)

    return () => clearInterval(interval)
  }, [docId])

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-gray-600">Loading status...</p>
            </div>
          </main>
        </div>
      </div>
    )
  }

  if (error || !statusData) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error || 'Status not found'}</p>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700"
              >
                Go Back
              </button>
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
          <div className="max-w-4xl mx-auto">
            <div className="mb-6">
              <button
                onClick={() => router.push('/')}
                className="text-primary hover:underline mb-4"
              >
                ← Back to Upload
              </button>
              <h1 className="text-3xl font-bold mb-2">Document Status</h1>
              <p className="text-gray-600">Document ID: {docId}</p>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Status</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    statusData.status === 'complete' ? 'bg-green-100 text-green-800' :
                    statusData.status === 'failed' ? 'bg-red-100 text-red-800' :
                    statusData.status === 'flagged' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {statusData.status.toUpperCase()}
                  </span>
                </div>
                <ProgressBar progress={statusData.progress_percent} />
              </div>

              {statusData.current_step && (
                <p className="text-sm text-gray-600">
                  Current step: <span className="font-medium">{statusData.current_step}</span>
                </p>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold mb-4">Processing Steps</h2>
              <div className="space-y-3">
                {statusData.steps.map((step, index) => (
                  <div
                    key={step.step}
                    className={`p-4 rounded-lg border ${
                      step.status === 'complete'
                        ? 'bg-green-50 border-green-200'
                        : step.status === 'running'
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            step.status === 'complete'
                              ? 'bg-green-500 text-white'
                              : step.status === 'running'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {step.status === 'complete' ? '✓' : index + 1}
                        </div>
                        <div>
                          <p className="font-medium capitalize">{step.step}</p>
                          {step.updated_at && (
                            <p className="text-xs text-gray-500">
                              {new Date(step.updated_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-sm font-medium capitalize">{step.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {statusData.status === 'complete' && (
              <div className="mt-6">
                <button
                  onClick={() => router.push(`/result/${docId}`)}
                  className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700"
                >
                  View Results
                </button>
              </div>
            )}

            {statusData.status === 'flagged' && (
              <div className="mt-6">
                <button
                  onClick={() => router.push(`/review/flagged`)}
                  className="px-6 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
                >
                  Open for Review
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

