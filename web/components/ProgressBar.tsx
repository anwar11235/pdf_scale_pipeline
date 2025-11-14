'use client'

interface ProgressBarProps {
  progress: number
}

export default function ProgressBar({ progress }: ProgressBarProps) {
  return (
    <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
      <div
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        className="h-full bg-primary rounded-full transition-all duration-300"
      />
    </div>
  )
}

