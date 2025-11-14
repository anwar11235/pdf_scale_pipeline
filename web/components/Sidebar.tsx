'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FileText, Flag, Settings, User } from 'lucide-react'

export default function Sidebar() {
  const pathname = usePathname()
  
  const navItems = [
    { href: '/', label: 'Dashboard', icon: FileText },
    { href: '/review/flagged', label: 'Flagged', icon: Flag },
    { href: '/settings', label: 'Settings', icon: Settings },
  ]
  
  return (
    <div className="w-60 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-primary">PDF Pipeline</h2>
      </div>
      
      <nav className="flex-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 p-3 rounded-lg mb-2 transition-colors ${
                isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 p-3">
          <User size={20} className="text-gray-500" />
          <span className="text-sm text-gray-700">User Profile</span>
        </div>
      </div>
    </div>
  )
}

