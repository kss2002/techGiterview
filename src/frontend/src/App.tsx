import { lazy, Suspense, type ReactNode } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from '@components/Layout/Layout'
import { FloatingLinks } from '@components/FloatingLinks'
import { ErrorBoundary } from '@components/ErrorBoundary'
import './App.css'

const HomePage = lazy(() => import('@pages/HomePage').then((m) => ({ default: m.HomePage })))
const DashboardPageV2 = lazy(() => import('@pages/DashboardPageV2').then((m) => ({ default: m.DashboardPageV2 })))
const DashboardPage = lazy(() => import('@pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const InterviewPage = lazy(() => import('@pages/InterviewPage').then((m) => ({ default: m.InterviewPage })))
const ReportsPage = lazy(() => import('@pages/ReportsPage').then((m) => ({ default: m.ReportsPage })))

const DebugComponent = lazy(() => import('@components/DebugComponent').then((m) => ({ default: m.DebugComponent })))
const ErrorTestComponent = lazy(() => import('@components/ErrorTestComponent').then((m) => ({ default: m.ErrorTestComponent })))
const TestComponent = lazy(() => import('./TestComponent').then((m) => ({ default: m.TestComponent })))
const CSSDebugComponent = lazy(() => import('./CSSDebugComponent').then((m) => ({ default: m.CSSDebugComponent })))
const HomePageSimple = lazy(() => import('./pages/HomePageSimple').then((m) => ({ default: m.HomePageSimple })))
const IconTestPage = lazy(() => import('./pages/IconTestPage').then((m) => ({ default: m.IconTestPage })))
const InterviewTestPage = lazy(() => import('./pages/InterviewTestPage').then((m) => ({ default: m.InterviewTestPage })))

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

const routeFallback = (
  <div className="app-route-loading" role="status" aria-live="polite">
    페이지를 불러오는 중...
  </div>
)

const withSuspense = (element: ReactNode) => (
  <Suspense fallback={routeFallback}>{element}</Suspense>
)

function App() {
  const isDev = import.meta.env.DEV

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
              <Route path="/" element={withSuspense(<HomePage />)} />
              <Route path="/dashboard" element={withSuspense(<ErrorBoundary><DashboardPageV2 /></ErrorBoundary>)} />
              <Route path="/dashboard/:analysisId" element={withSuspense(<ErrorBoundary><DashboardPageV2 /></ErrorBoundary>)} />
              <Route path="/dashboard-legacy" element={withSuspense(<ErrorBoundary><DashboardPage /></ErrorBoundary>)} />
              <Route path="/dashboard-legacy/:analysisId" element={withSuspense(<ErrorBoundary><DashboardPage /></ErrorBoundary>)} />
              <Route path="/interview/:interviewId" element={withSuspense(<ErrorBoundary><InterviewPage /></ErrorBoundary>)} />
              <Route path="/dashboard/:analysisId/interview/:interviewId" element={withSuspense(<ErrorBoundary><InterviewPage /></ErrorBoundary>)} />
              <Route path="/reports" element={withSuspense(<ErrorBoundary><ReportsPage /></ErrorBoundary>)} />
              {isDev && (
                <>
                  <Route path="/debug" element={withSuspense(<DebugComponent />)} />
                  <Route path="/design-test" element={withSuspense(<TestComponent />)} />
                  <Route path="/css-debug" element={withSuspense(<CSSDebugComponent />)} />
                  <Route path="/simple-test" element={withSuspense(<HomePageSimple />)} />
                  <Route path="/icon-test" element={withSuspense(<IconTestPage />)} />
                  <Route path="/interview-test" element={withSuspense(<InterviewTestPage />)} />
                  <Route path="/error-test" element={withSuspense(<ErrorBoundary><ErrorTestComponent /></ErrorBoundary>)} />
                </>
              )}
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
