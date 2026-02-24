import React from 'react'
import './LoadingState.css'

interface LoadingStateProps {
  title?: string
  steps?: string[]
  hint?: string
  onCancel?: () => void
}

export function LoadingState({
  title = '분석 결과 로딩 중',
  steps = ['저장소 정보 조회', '파일 구조 분석', 'AI 질문 생성'],
  hint = '큰 저장소일수록 더 오래 걸릴 수 있습니다',
  onCancel,
}: LoadingStateProps) {
  const [activeStep, setActiveStep] = React.useState(0)
  React.useEffect(() => {
    const t = setInterval(() => setActiveStep(p => (p + 1) % steps.length), 2000)
    return () => clearInterval(t)
  }, [steps.length])

  return (
    <div className="v2-root v2-loading-state">
      <div className="v2-loading-content">
        <div className="v2-spinner" />
        <h3 className="v2-loading-title">📊 {title}</h3>
        <div className="v2-loading-steps">
          {steps.map((s, i) => (
            <div key={i} className={`v2-loading-step ${i === activeStep ? 'v2-loading-step--active' : ''} ${i < activeStep ? 'v2-loading-step--done' : ''}`}>
              <div className="v2-loading-step-dot" />
              <span>{s}</span>
            </div>
          ))}
        </div>
        <p className="v2-loading-hint">⏱️ {hint}</p>
        {onCancel && (
          <button className="v2-btn v2-btn-outline v2-btn-sm" onClick={onCancel}>
            취소하고 홈으로
          </button>
        )}
      </div>
    </div>
  )
}
