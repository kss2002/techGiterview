import React from 'react'

export const DebugComponent: React.FC = () => {
  console.log('DebugComponent rendered successfully!')
  
  return (
    <div className="debug-container">
      <h1 className="debug-title">Debug Component Working!</h1>
      <p className="debug-text">If you can see this, React is working correctly.</p>
      <p className="debug-text">Current URL: {window.location.href}</p>
      <p className="debug-text">Pathname: {window.location.pathname}</p>
    </div>
  )
}