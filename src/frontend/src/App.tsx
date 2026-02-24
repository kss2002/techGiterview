import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from '@pages/HomePage'
import { DashboardPageV2 } from '@pages/DashboardPageV2'
import { InterviewPage } from '@pages/InterviewPage'
import { ReportsPage } from '@pages/ReportsPage'
import { Layout } from '@components/Layout/Layout'
import { FloatingLinks } from '@components/FloatingLinks'
import { ErrorBoundary } from '@components/ErrorBoundary'
import { TestComponent } from './TestComponent'
import { CSSDebugComponent } from './CSSDebugComponent'
import './App.css'

// React Query 클라이언트 생성
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5분
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
      <Router 
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <Layout>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/design-test" element={<TestComponent />} />
              <Route path="/css-debug" element={<CSSDebugComponent />} />
              <Route path="/dashboard" element={<ErrorBoundary><DashboardPageV2 /></ErrorBoundary>} />
              <Route path="/dashboard/:analysisId" element={<ErrorBoundary><DashboardPageV2 /></ErrorBoundary>} />
              <Route path="/interview/:interviewId" element={<ErrorBoundary><InterviewPage /></ErrorBoundary>} />
              <Route path="/dashboard/:analysisId/interview/:interviewId" element={<ErrorBoundary><InterviewPage /></ErrorBoundary>} />
              <Route path="/reports" element={<ErrorBoundary><ReportsPage /></ErrorBoundary>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </Layout>
        <FloatingLinks />
      </Router>
    </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
