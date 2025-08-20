import React, { useState } from 'react'

export const TestComponent: React.FC = () => {
  const [isVisible, setIsVisible] = useState(true)
  const [count, setCount] = useState(0)

  return (
    <div className="center-container">
      {/* 디자인 시스템 성공 메시지 */}
      <div className="debug-container animate-fade-in-up">
        <h1 className="debug-title">
          SUCCESS 디자인 시스템 성공적으로 적용!
        </h1>
        <p className="debug-text">
          TechGiterview의 통합 디자인 시스템이 정상적으로 작동하고 있습니다.
        </p>
        <p className="debug-text">
          모든 CSS 변수, 유틸리티 클래스, 컴포넌트 스타일이 로드되었습니다.
        </p>
      </div>

      {/* 카운터 테스트 */}
      <div className="debug-container">
        <h2 className="debug-title">인터랙션 테스트</h2>
        <p className="debug-text">카운터: {count}</p>
        <div className="error-actions">
          <button 
            className="error-action-btn primary hover-lift"
            onClick={() => setCount(c => c + 1)}
          >
            카운트 증가
          </button>
          <button 
            className="error-action-btn secondary hover-lift"
            onClick={() => setCount(0)}
          >
            리셋
          </button>
        </div>
      </div>

      {/* 진행률 바 테스트 */}
      <div className="debug-container">
        <h2 className="debug-title">진행률 바 컴포넌트</h2>
        <p className="debug-text">동적 진행률 바 예시:</p>
        
        <div style={{ marginBottom: '16px' }}>
          <div className="flex-between" style={{ marginBottom: '8px' }}>
            <span className="debug-text">중요도</span>
            <span className="debug-text">85%</span>
          </div>
          <div className="bar-container">
            <div 
              className="bar-fill importance" 
              style={{ width: '85%' }}
            >
              <span className="metric-value">85</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div className="flex-between" style={{ marginBottom: '8px' }}>
            <span className="debug-text">복잡도</span>
            <span className="debug-text">60%</span>
          </div>
          <div className="bar-container">
            <div 
              className="bar-fill complexity" 
              style={{ width: '60%' }}
            >
              <span className="metric-value">60</span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div className="flex-between" style={{ marginBottom: '8px' }}>
            <span className="debug-text">핫스팟</span>
            <span className="debug-text">40%</span>
          </div>
          <div className="bar-container">
            <div 
              className="bar-fill hotspot" 
              style={{ width: '40%' }}
            >
              <span className="metric-value">40</span>
            </div>
          </div>
        </div>
      </div>

      {/* 가시성 토글 테스트 */}
      <div className="debug-container">
        <h2 className="debug-title">애니메이션 테스트</h2>
        <button 
          className="error-action-btn primary"
          onClick={() => setIsVisible(!isVisible)}
        >
          컴포넌트 토글
        </button>
        
        {isVisible && (
          <div className="debug-container animate-fade-in" style={{ marginTop: '16px' }}>
            <p className="debug-text">
              이 컴포넌트는 fade-in 애니메이션과 함께 나타납니다!
            </p>
            <div className="language-color lang-color-typescript"></div>
          </div>
        )}
      </div>

      {/* 네비게이션 링크 */}
      <div className="debug-container">
        <h2 className="debug-title">라우팅 테스트</h2>
        <div className="error-actions">
          <a href="/debug" className="error-action-btn secondary">
            Debug 페이지
          </a>
          <a href="/error-test" className="error-action-btn secondary">
            Error Test 페이지
          </a>
        </div>
      </div>
    </div>
  )
}