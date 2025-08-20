import React from 'react'
import './HomePage.css' // Import the CSS file to test class-based styles

export const HomePageSimple: React.FC = () => {
  return (
    <div 
      style={{
        minHeight: '100vh',
        background: 'var(--primary-900, red)',
        color: 'var(--gray-50, green)',
        padding: 'var(--spacing-20, 20px)',
        textAlign: 'center'
      }}
    >
      <h1 
        style={{
          fontSize: 'var(--text-6xl, 24px)',
          fontWeight: 'var(--font-bold, bold)',
          marginBottom: '20px'
        }}
      >
        Direct Inline CSS Variables Test
      </h1>
      <p>If this appears with blue background and large text, CSS variables work in React</p>
      <p>If this appears red background, CSS variables are not working</p>
      
      {/* CSS 클래스 사용 버전 */}
      <div className="home-page" style={{ marginTop: '40px', padding: '20px' }}>
        <h2 className="hero-title">CSS Class Version</h2>
        <p>This uses CSS classes from HomePage.css</p>
      </div>
      
      {/* 하드코딩된 버전 */}
      <div 
        style={{
          background: '#1e3a8a',
          color: '#f9fafb',
          fontSize: '60px',
          fontWeight: 700,
          padding: '40px',
          marginTop: '40px'
        }}
      >
        Hardcoded Version (Should Always Work)
      </div>
    </div>
  )
}