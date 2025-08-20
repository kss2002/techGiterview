import React, { useEffect, useState } from 'react'

export const CSSDebugComponent: React.FC = () => {
  const [cssValues, setCssValues] = useState<Record<string, string>>({})
  const [computedValues, setComputedValues] = useState<Record<string, string>>({})

  useEffect(() => {
    // CSS 변수 값 확인
    const root = document.documentElement
    const computed = getComputedStyle(root)
    
    const variables = [
      '--primary-900',
      '--text-6xl',
      '--spacing-20',
      '--gray-50',
      '--font-bold',
      '--secondary-300'
    ]
    
    const cssVars: Record<string, string> = {}
    variables.forEach(varName => {
      const value = computed.getPropertyValue(varName)
      cssVars[varName] = value?.trim() || 'UNDEFINED'
    })
    setCssValues(cssVars)
    
    // 실제 요소의 computed style 확인
    const testElement = document.querySelector('.css-debug-test')
    if (testElement) {
      const testComputed = getComputedStyle(testElement)
      setComputedValues({
        backgroundColor: testComputed.backgroundColor,
        color: testComputed.color,
        fontSize: testComputed.fontSize,
        padding: testComputed.padding
      })
    }
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1 style={{ fontSize: '24px', marginBottom: '20px' }}>React CSS Debug Component</h1>
      
      {/* CSS 변수 테스트 요소 */}
      <div 
        className="css-debug-test"
        style={{
          background: 'var(--primary-900, red)',
          color: 'var(--gray-50, green)', 
          padding: 'var(--spacing-20, 20px)',
          fontSize: 'var(--text-6xl, 24px)',
          marginBottom: '20px',
          border: '2px solid var(--secondary-300, blue)'
        }}
      >
        React CSS Variables Test
        <br />
        <small>Should be blue background, white text, large font</small>
      </div>

      {/* 하드코딩된 스타일 테스트 */}
      <div style={{
        background: '#1e3a8a',
        color: '#f9fafb',
        padding: '80px',
        fontSize: '60px',
        marginBottom: '20px'
      }}>
        Hardcoded Styles Test
      </div>

      {/* CSS 변수 값 출력 */}
      <div style={{ background: '#f0f0f0', padding: '15px', marginBottom: '20px' }}>
        <h3>CSS Variables from :root:</h3>
        {Object.entries(cssValues).map(([key, value]) => (
          <div key={key} style={{ marginBottom: '5px' }}>
            <strong>{key}:</strong> "{value}" {value === 'UNDEFINED' && <span style={{color: 'red'}}>(NOT FOUND)</span>}
          </div>
        ))}
      </div>

      {/* Computed styles 출력 */}
      <div style={{ background: '#e0e0e0', padding: '15px' }}>
        <h3>Computed Styles of Test Element:</h3>
        {Object.entries(computedValues).map(([key, value]) => (
          <div key={key} style={{ marginBottom: '5px' }}>
            <strong>{key}:</strong> {value}
          </div>
        ))}
      </div>
      
      {/* 환경 정보 */}
      <div style={{ background: '#d0d0d0', padding: '15px', marginTop: '20px' }}>
        <h3>Environment Info:</h3>
        <div>User Agent: {navigator.userAgent}</div>
        <div>CSS Custom Properties Support: {CSS.supports('color', 'var(--test)') ? 'YES' : 'NO'}</div>
        <div>Current URL: {window.location.href}</div>
      </div>
    </div>
  )
}