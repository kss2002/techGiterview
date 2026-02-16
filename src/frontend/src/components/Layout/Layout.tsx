import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Zap, 
  Home, 
  BarChart3, 
  FileText, 
  Plus,
  Mail,
  Github,
  MessageCircle,
  Book
} from 'lucide-react'
import { AppShellSidebar } from './AppShellSidebar'
import { AppShellHeader } from './AppShellHeader'
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
    { name: '홈', path: '/', icon: () => <Home className="w-5 h-5" /> },
    { name: '대시보드', path: '/dashboard', icon: () => <BarChart3 className="w-5 h-5" /> },
    { name: '리포트', path: '/reports', icon: () => <FileText className="w-5 h-5" /> }
  ]

  const isHome = location.pathname === '/'
  const isDashboardPage = location.pathname.startsWith('/dashboard')
  const isAppShellPage =
    location.pathname.startsWith('/reports') ||
    location.pathname.startsWith('/interview')
  const showNavigation = !isHome && !isAppShellPage && !isDashboardPage

  return (
    <div className="layout">
      {isDashboardPage ? (
        <main className="main-content full-width">{children}</main>
      ) : isAppShellPage ? (
        <div className="app-shell">
          <AppShellSidebar isActive={isActive} />
          <div className="app-shell-main">
            <AppShellHeader />
            <main className="app-shell-content">{children}</main>
          </div>
        </div>
      ) : (
        <>
      {showNavigation && (
        <nav className="navigation">
          <div className="nav-container">
            <div className="nav-brand">
              <Link to="/" className="brand-link">
                <Zap className="brand-icon w-8 h-8" />
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
                <Plus className="btn-icon w-4 h-4" />
                <span className="btn-text">새 분석</span>
              </button>
            </div>
          </div>
        </nav>
      )}
      
      <main className={`main-content ${showNavigation ? 'with-nav' : 'full-width'}`}>
        {children}
      </main>
      
      {showNavigation && (
        <footer className="footer">
          <div className="footer-container">
            <div className="footer-content">
              <div className="footer-section">
                <h3><Zap className="w-5 h-5 inline mr-2" />TechGiterview</h3>
                <p>GitHub 기반 AI 기술면접 준비 플랫폼</p>
              </div>
              
              <div className="footer-section">
                <h4>기능</h4>
                <ul>
                  <li>저장소 자동 분석</li>
                  <li>맞춤형 질문 생성</li>
                  <li>실시간 모의면접</li>
                  <li>상세 피드백 리포트</li>
                </ul>
              </div>
              
              <div className="footer-section">
                <h4>지원 기술</h4>
                <ul>
                  <li>Python, JavaScript, TypeScript</li>
                  <li>React, Vue, Angular</li>
                  <li>Node.js, Django, FastAPI</li>
                  <li>그 외 다양한 언어와 프레임워크</li>
                </ul>
              </div>
              
              <div className="footer-section">
                <h4>연락처</h4>
                <ul>
                  <li><Mail className="w-4 h-4 inline mr-2" />support@techgiterview.com</li>
                  <li><Github className="w-4 h-4 inline mr-2" />GitHub Issues</li>
                  <li><MessageCircle className="w-4 h-4 inline mr-2" />Discord Community</li>
                  <li><Book className="w-4 h-4 inline mr-2" />Documentation</li>
                </ul>
              </div>
            </div>
            
            <div className="footer-bottom">
              <p>&copy; 2025 TechGiterview. All rights reserved.</p>

            </div>
          </div>
        </footer>
      )}
        </>
      )}
    </div>
  )
}
