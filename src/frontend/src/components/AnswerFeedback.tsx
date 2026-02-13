import React from 'react'
import './AnswerFeedback.css'

interface AnswerFeedbackProps {
  feedback: {
    overall_score?: number
    score?: number
    feedback?: string
    message?: string
    feedback_type?: 'strength' | 'improvement' | 'suggestion' | 'keyword_missing'
    details?: string
    suggestions?: string[]
  }
  isVisible: boolean
}

export const AnswerFeedback: React.FC<AnswerFeedbackProps> = ({ feedback, isVisible }) => {
  if (!isVisible || !feedback) return null
  const effectiveScore = feedback.overall_score ?? feedback.score ?? 0
  const effectiveMessage = feedback.feedback || feedback.message || ''
  const effectiveType = feedback.feedback_type || 'suggestion'
  const effectiveDetails = feedback.details || ''
  const effectiveSuggestions = feedback.suggestions || []

  const getScoreClass = (score: number) => {
    if (score >= 8) return 'score-excellent' // 우수
    if (score >= 6) return 'score-good' // 보통
    return 'score-poor' // 개선 필요
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return '우수'
    if (score >= 6) return '양호'
    if (score >= 4) return '보통'
    return '개선필요'
  }

  const getFeedbackIcon = (type: string) => {
    switch (type) {
      case 'strength': return '[GOOD]'
      case 'improvement': return '[TIPS]'
      case 'suggestion': return '[IDEA]'
      case 'keyword_missing': return '[HELP]'
      default: return '[INFO]'
    }
  }

  return (
    <div className={`answer-feedback ${isVisible ? 'fade-in' : ''}`}>
      {/* 점수 표시 */}
      <div className="feedback-header">
        <div className="score-container">
          <div 
            className={`score-circle ${getScoreClass(effectiveScore)}`}
          >
            <span className={`score-value ${getScoreClass(effectiveScore)}`}>
              {effectiveScore}
            </span>
            <span className="score-max">/10</span>
          </div>
          <div className={`score-label ${getScoreClass(effectiveScore)}`}>
            {getScoreLabel(effectiveScore)}
          </div>
        </div>
        
        <div className="feedback-type">
          <span className="feedback-icon">{getFeedbackIcon(effectiveType)}</span>
        </div>
      </div>

      {/* 메인 피드백 메시지 */}
      <div className="feedback-message">
        <p>{effectiveMessage}</p>
      </div>

      {/* 상세 정보 */}
      <div className="feedback-details">
        <div className="detail-row">
          <span className="detail-label">[분석]</span>
          <span className="detail-value">{effectiveDetails}</span>
        </div>
      </div>


      {/* 개선 제안 */}
      {effectiveSuggestions.length > 0 && (
        <div className="suggestions-section">
          <h4 className="suggestions-title">[개선 제안]</h4>
          <ul className="suggestions-list">
            {effectiveSuggestions.map((suggestion, index) => (
              <li key={index} className="suggestion-item">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
