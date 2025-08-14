import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from '@pages/HomePage'
import { DashboardPage } from '@pages/DashboardPage'
import { InterviewPage } from '@pages/InterviewPage'
import { ReportsPage } from '@pages/ReportsPage'
import { Layout } from '@components/Layout/Layout'
import { FloatingLinks } from '@components/FloatingLinks'
import { ErrorBoundary } from '@components/ErrorBoundary'
import { DebugComponent } from '@components/DebugComponent'
import { ErrorTestComponent } from '@components/ErrorTestComponent'
import { TestComponent } from './TestComponent'
import { CSSDebugComponent } from './CSSDebugComponent'
import { HomePageSimple } from './pages/HomePageSimple'
import { IconTestPage } from './pages/IconTestPage'
import { InterviewTestPage } from './pages/InterviewTestPage'
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
              <Route path="/debug" element={<DebugComponent />} />
              <Route path="/design-test" element={<TestComponent />} />
              <Route path="/css-debug" element={<CSSDebugComponent />} />
              <Route path="/simple-test" element={<HomePageSimple />} />
              <Route path="/icon-test" element={<IconTestPage />} />
              <Route path="/interview-test" element={<InterviewTestPage />} />
              <Route path="/error-test" element={<ErrorBoundary><ErrorTestComponent /></ErrorBoundary>} />
              <Route path="/dashboard" element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
              <Route path="/dashboard/:analysisId" element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
              <Route path="/interview/:interviewId" element={<ErrorBoundary><InterviewPage /></ErrorBoundary>} />
              <Route path="/dashboard/:analysisId/interview/:interviewId" element={<ErrorBoundary><InterviewPage /></ErrorBoundary>} />
              <Route path="/reports" element={<ErrorBoundary><ReportsPage /></ErrorBoundary>} />
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
