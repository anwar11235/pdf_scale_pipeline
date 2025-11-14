'use client'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Document Processing Pipeline</h1>
        <div className="text-sm text-gray-600">
          Welcome, User
        </div>
      </div>
    </header>
  )
}

