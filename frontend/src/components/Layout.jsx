import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, BarChart3, Mail, Users, Settings as SettingsIcon, Zap } from 'lucide-react'

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/generate', label: 'Generate', icon: Mail },
    { path: '/segments', label: 'Segments', icon: Users },
    { path: '/analytics', label: 'Analytics', icon: Zap },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-ohm-dark text-white transition-all duration-300 flex flex-col`}>
        {/* Header */}
        <div className="p-6 border-b border-gray-700 flex items-center justify-between">
          {sidebarOpen && <h1 className="text-xl font-bold text-ohm-gold">OHM Agent</h1>}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-700 rounded"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive(path)
                  ? 'bg-ohm-gold text-black'
                  : 'text-gray-300 hover:bg-gray-700'
              }`}
              title={!sidebarOpen ? label : ''}
            >
              <Icon size={20} />
              {sidebarOpen && <span className="font-medium">{label}</span>}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 text-xs text-gray-400">
          {sidebarOpen && <p>Email Intelligence Agent v1.0</p>}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
