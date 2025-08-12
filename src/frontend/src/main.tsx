import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { errorHandler, ErrorHandler } from './utils/errorHandler'

// 전역 오류 처리기 - 브라우저 확장 프로그램 충돌 처리
window.addEventListener('error', (event) => {
  errorHandler.logError(event.error, 'Global Error Handler')
  
  if (ErrorHandler.isExtensionError(event.error)) {
    event.preventDefault() // 기본 오류 처리 방지
    return false
  }
})

// Promise rejection 처리
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
  errorHandler.logError(error, 'Unhandled Promise Rejection')
  
  if (ErrorHandler.isExtensionError(error)) {
    event.preventDefault() // 기본 오류 처리 방지
    return false
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
