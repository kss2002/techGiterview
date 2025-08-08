import React from 'react'

export const DebugComponent: React.FC = () => {
  console.log('DebugComponent rendered successfully!')
  
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', margin: '20px' }}>
      <h1>Debug Component Working!</h1>
      <p>If you can see this, React is working correctly.</p>
      <p>Current URL: {window.location.href}</p>
      <p>Pathname: {window.location.pathname}</p>
    </div>
  )
}