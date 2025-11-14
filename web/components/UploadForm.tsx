'use client'

import { useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { uploadFileToBackend } from '@/utils/api'

export default function UploadForm() {
  const [files, setFiles] = useState<FileList | null>(null)
  const [progress, setProgress] = useState<Record<string, number>>({})
  const [uploading, setUploading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const router = useRouter()

  async function handleUpload() {
    if (!files || files.length === 0) return
    
    setUploading(true)
    setErrors({})
    
    for (const file of Array.from(files)) {
      // Validate file type
      if (!file.name.endsWith('.pdf')) {
        setErrors(prev => ({ ...prev, [file.name]: 'Only PDF files are allowed' }))
        continue
      }
      
      // Validate file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, [file.name]: 'File size must be less than 50MB' }))
        continue
      }
      
      try {
        // Register document with backend
        const formData = new FormData()
        formData.append('file', file)
        formData.append('filename', file.name)
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        })
        
        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`)
        }
        
        const result = await response.json()
        const { doc_id, presigned_url } = result
        
        // Upload file with progress tracking
        if (presigned_url) {
          await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.open('PUT', presigned_url)
            xhr.setRequestHeader('Content-Type', 'application/pdf')
            
            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100)
                setProgress(p => ({ ...p, [doc_id]: pct }))
              }
            }
            
            xhr.onload = () => {
              if (xhr.status === 200) {
                setProgress(p => ({ ...p, [doc_id]: 100 }))
                resolve()
              } else {
                reject(new Error(`Upload failed: ${xhr.statusText}`))
              }
            }
            
            xhr.onerror = () => reject(new Error('Upload failed'))
            xhr.send(file)
          })
        } else {
          // Direct upload (if presigned URL not provided)
          setProgress(p => ({ ...p, [doc_id]: 100 }))
        }
        
        // Redirect to status page after a short delay
        setTimeout(() => {
          router.push(`/status/${doc_id}`)
        }, 1000)
        
      } catch (error) {
        setErrors(prev => ({ ...prev, [file.name]: (error as Error).message }))
      }
    }
    
    setUploading(false)
  }

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm">
      <div className="flex items-center gap-4 mb-4">
        <UploadCloud className="text-primary" size={24} />
        <div className="flex-1">
          <label htmlFor="file-input" className="block text-sm font-medium text-gray-700 mb-2">
            Select PDF files
          </label>
          <input
            id="file-input"
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) => setFiles(e.target.files)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-blue-700"
            disabled={uploading}
          />
          <p className="mt-1 text-xs text-gray-500">Maximum file size: 50MB</p>
        </div>
      </div>
      
      <button
        onClick={handleUpload}
        disabled={!files || uploading}
        className="mt-4 px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
      
      {Object.keys(progress).length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Upload Progress</h3>
          {Object.entries(progress).map(([docId, pct]) => (
            <div key={docId} className="space-y-1">
              <div className="flex justify-between text-xs text-gray-600">
                <span>Document {docId.substring(0, 8)}...</span>
                <span>{pct}%</span>
              </div>
              <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                <div
                  style={{ width: `${pct}%` }}
                  className="h-full bg-primary rounded-full transition-all duration-300"
                />
              </div>
            </div>
          ))}
        </div>
      )}
      
      {Object.keys(errors).length > 0 && (
        <div className="mt-4 space-y-2">
          {Object.entries(errors).map(([filename, error]) => (
            <div key={filename} className="text-sm text-red-600 bg-red-50 p-2 rounded">
              <strong>{filename}:</strong> {error}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

