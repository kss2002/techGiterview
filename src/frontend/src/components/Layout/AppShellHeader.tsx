import React from 'react'
import { Bell, Play } from 'lucide-react'
import { useLocation } from 'react-router-dom'

export const AppShellHeader: React.FC = () => {
  const location = useLocation()

  const pageLabel =
    location.pathname.startsWith('/dashboard') ? 'Dashboard' :
      location.pathname.startsWith('/reports') ? 'Reports' :
        location.pathname.startsWith('/interview') ? 'Interview' : 'Workspace'

  return (
    <header className="app-shell-header">
      <div className="app-shell-header-title">
        <div className="app-shell-header-main">{pageLabel}</div>
        <div className="app-shell-breadcrumb">TechGiterview / {pageLabel}</div>
      </div>
      <div className="app-shell-header-actions">
        <button className="app-shell-primary-action" type="button">
          <Play size={14} />
          <span>면접 시작하기</span>
        </button>
        <button className="app-shell-icon-button" type="button" aria-label="Notifications">
          <Bell size={16} />
        </button>
      </div>
    </header>
  )
}
