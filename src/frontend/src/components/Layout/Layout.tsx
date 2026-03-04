import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Zap, 
  Home, 
  BarChart3, 
  FileText, 
  Plus
} from 'lucide-react'
import { SiteFooter } from '../common/SiteFooter'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()
  
  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true
    if (path !== '/' && location.pathname.startsWith(path)) return true
    return false
  }

  const navigation = [
    { name: '홈', path: '/', icon: () => <Home className="layout-icon layout-icon--nav" /> },
    { name: '대시보드', path: '/dashboard', icon: () => <BarChart3 className="layout-icon layout-icon--nav" /> },
    { name: '리포트', path: '/reports', icon: () => <FileText className="layout-icon layout-icon--nav" /> }
  ]

  const isHome = location.pathname === '/'
  const isDashboardPage = location.pathname.startsWith('/dashboard')
  const showNavigation = !isHome && !isDashboardPage

  return (
    <div className="layout">
      {isDashboardPage ? (
        <main className="main-content full-width">{children}</main>
      ) : (
        <>
          {showNavigation && (
            <nav className="navigation">
              <div className="nav-container">
                <div className="nav-brand">
                  <Link to="/" className="brand-link">
                    <Zap className="brand-icon layout-icon layout-icon--brand" />
                    <span className="brand-text">TechGiterview</span>
                  </Link>
                </div>
                
                <div className="nav-links">
                  {navigation.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                    >
                      <span className="nav-icon">{item.icon()}</span>
                      <span className="nav-text">{item.name}</span>
                    </Link>
                  ))}
                </div>
                
                <div className="nav-actions">
                  <button 
                    className="new-analysis-btn"
                    onClick={() => window.location.href = '/'}
                  >
                    <Plus className="btn-icon layout-icon layout-icon--button" />
                    <span className="btn-text">새 분석</span>
                  </button>
                </div>
              </div>
            </nav>
          )}
          
          <main className={`main-content ${showNavigation ? 'with-nav' : 'full-width'}`}>
            {children}
          </main>
          
          {showNavigation && <SiteFooter />}
        </>
      )}
    </div>
  )
}
