import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { HomePage } from '@pages/HomePage'
import { DashboardPage } from '@pages/DashboardPage'
import { InterviewPage } from '@pages/InterviewPage'
import { ReportsPage } from '@pages/ReportsPage'
import { Layout } from '@components/Layout/Layout'
import { FloatingLinks } from '@components/FloatingLinks'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:analysisId" element={<DashboardPage />} />
          <Route path="/interview/:interviewId" element={<InterviewPage />} />
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </Layout>
      <FloatingLinks />
    </Router>
  )
}

export default App
