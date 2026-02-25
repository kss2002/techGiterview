import React from 'react'
import type { DashboardLoadingProgress } from '../../types/dashboard'
import './LoadingState.css'

interface LoadingStateProps {
  title?: string
  progressModel?: DashboardLoadingProgress
  steps?: string[]
  hint?: string
  onCancel?: () => void
}

interface RenderStep {
  key: string
  label: string
  status: 'pending' | 'active' | 'done' | 'failed'
  detail?: string
}

export function LoadingState({
  title = '분석 결과 로딩 중',
  progressModel,
  steps = ['저장소 정보 조회', '파일 구조 분석', 'AI 질문 생성'],
  hint = '큰 저장소일수록 더 오래 걸릴 수 있습니다',
  onCancel,
}: LoadingStateProps) {
  const [now, setNow] = React.useState<number>(Date.now())

  React.useEffect(() => {
    if (!progressModel?.startedAt) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [progressModel?.startedAt])

  const effectiveTitle = progressModel?.title || title
  const effectiveSteps: RenderStep[] = progressModel
    ? progressModel.steps
    : steps.map((label, index) => ({
        key: `legacy_${index}`,
        label,
        status: index === 0 ? 'active' : 'pending',
      }))
  const effectivePercent = progressModel?.percent ?? 5
  const currentDetail = progressModel?.currentDetail || hint
  const startedAtMs = progressModel?.startedAt ? new Date(progressModel.startedAt).getTime() : 0
  const elapsedSeconds = startedAtMs > 0 ? Math.max(0, Math.floor((now - startedAtMs) / 1000)) : 0

  return (
    <div className="v2-root v2-loading-state">
      <div className="v2-loading-content">
        <div className="v2-spinner" />
        <h3 className="v2-loading-title">📊 {effectiveTitle}</h3>
        <div className="v2-loading-progress-summary">
          <div className="v2-loading-progress-meta">
            <span className="v2-loading-progress-label">진행률</span>
            <span className="v2-loading-progress-value" data-testid="loading-percent">
              {effectivePercent}%
            </span>
          </div>
          <div className="v2-loading-progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={effectivePercent}>
            <div
              className="v2-loading-progress-fill"
              style={{ width: `${effectivePercent}%` }}
            />
          </div>
        </div>
        <div className="v2-loading-steps">
          {effectiveSteps.map((step, index) => (
            <div
              key={step.key || index}
              className={`v2-loading-step v2-loading-step--${step.status}`}
            >
              <div className="v2-loading-step-dot" />
              <span>{step.label}</span>
              {step.detail && <small className="v2-loading-step-detail">{step.detail}</small>}
            </div>
          ))}
        </div>
        <p className="v2-loading-hint">{currentDetail}</p>
        <p className="v2-loading-time">
          ⏱️ 경과 시간: {elapsedSeconds}초
          {progressModel?.attempt ? ` · 재시도 ${progressModel.attempt.current}/${progressModel.attempt.total}` : ''}
        </p>
        {onCancel && (
          <button className="v2-btn v2-btn-outline v2-btn-sm" onClick={onCancel}>
            취소하고 홈으로
          </button>
        )}
      </div>
    </div>
  )
}
