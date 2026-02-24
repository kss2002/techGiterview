import React from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, FileText, Home, Zap } from 'lucide-react'

interface AppShellSidebarProps {
  isActive: (path: string) => boolean
}

export const AppShellSidebar: React.FC<AppShellSidebarProps> = ({ isActive }) => {
  const navItems = [
    { name: 'Home', path: '/', icon: Home },
    { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
    { name: 'Reports', path: '/reports', icon: FileText }
  ]

  return (
    <aside className="app-shell-sidebar">
      <div className="app-shell-sidebar-brand">
        <Zap size={18} />
        <span>TechGiterview</span>
      </div>
      <nav className="app-shell-sidebar-nav">
        {navItems.map(item => {
          const Icon = item.icon
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`app-shell-nav-item ${isActive(item.path) ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
