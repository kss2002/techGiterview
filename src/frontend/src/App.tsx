import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { HomePage } from '@pages/HomePage'
import { DashboardPage } from '@pages/DashboardPage'
import { InterviewPage } from '@pages/InterviewPage'
import { ReportsPage } from '@pages/ReportsPage'
import { Layout } from '@components/Layout/Layout'
import { FloatingLinks } from '@components/FloatingLinks'
import { ErrorBoundary } from '@components/ErrorBoundary'
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Layout>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/dashboard" element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
              <Route path="/dashboard/:analysisId" element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
              <Route path="/interview/:interviewId" element={<ErrorBoundary><InterviewPage /></ErrorBoundary>} />
              <Route path="/reports" element={<ErrorBoundary><ReportsPage /></ErrorBoundary>} />
            </Routes>
          </ErrorBoundary>
        </Layout>
        <FloatingLinks />
      </Router>
    </ErrorBoundary>
  )
}

export default App
