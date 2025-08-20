import React from 'react'
import { 
  MessageCircle,
  Clock,
  Sun,
  Moon,
  Settings,
  ChevronLeft,
  ChevronRight,
  Send,
  User,
  Bot,
  Zap
} from 'lucide-react'

export const InterviewTestPage: React.FC = () => {
  return (
    <div className="interview-page font-size-medium">
      {/* 헤더 */}
      <div className="interview-header">
        <div className="header-left">
          <h1><MessageCircle className="w-8 h-8 mr-3 inline-block" /> 모의면접 진행중</h1>
          <div className="interview-info">
            <span className="question-progress">질문 1 / 5</span>
          </div>
        </div>
        
        <div className="header-right">
          <div className="settings-controls">
            <button className="setting-btn">
              <Sun className="w-4 h-4" />
            </button>
          </div>
          <div className="timer">
            <Clock className="w-5 h-5" />
            <span className="timer-value">25:30</span>
          </div>
          <div className="connection-status connected">
            <span className="status-dot"></span>
            연결됨
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="interview-content">
        {/* 질문 영역 */}
        <div className="question-container">
          <div className="current-question">
            <div className="question-header">
              <div className="question-meta">
                <span className="question-number">Q1</span>
                <Zap className="w-4 h-4 text-blue-600" />
                <span className="category-name">Technical</span>
                <span className="difficulty-badge" style={{ backgroundColor: 'var(--primary-600)' }}>
                  Medium
                </span>
              </div>
              <div className="question-navigation">
                <button className="nav-btn prev">
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  이전
                </button>
                <button className="nav-btn next">
                  다음
                  <ChevronRight className="w-4 h-4 ml-1" />
                </button>
              </div>
            </div>
            <div className="question-content">
              <div className="question-text">
                <p>React에서 useState Hook의 작동 원리를 설명하고, 클래스 컴포넌트의 setState와 어떤 차이가 있는지 설명해주세요.</p>
              </div>
            </div>
          </div>
          
          {/* 답변 히스토리 */}
          <div className="answer-history">
            <div className="answer-item">
              <div className="answer-header">
                <span className="answer-label">
                  <User className="w-4 h-4 inline mr-2" />
                  내 답변
                </span>
                <span className="answer-time">10:42:15</span>
              </div>
              <div className="answer-content">
                이것은 테스트 답변입니다. Lucide React 아이콘이 올바르게 표시되는지 확인하고 있습니다.
              </div>
            </div>
            
            <div className="answer-item system-message">
              <div className="answer-header">
                <span className="answer-label">
                  <Bot className="w-4 h-4 inline mr-2" />
                  AI 피드백
                </span>
                <span className="answer-time">10:42:30</span>
              </div>
              <div className="answer-content">
                좋은 답변입니다! 아이콘들이 올바르게 표시되고 있습니다.
              </div>
            </div>
          </div>
        </div>
        
        {/* 답변 입력 영역 */}
        <div className="answer-input-area">
          <div className="input-header">
            <h3>답변 입력</h3>
          </div>
          
          <div className="input-container">
            <textarea
              placeholder="답변을 입력하세요..."
              className="form-input form-textarea"
              rows={6}
              defaultValue="테스트 답변 내용입니다."
            />
            <div className="input-actions">
              <div className="input-stats">
                <span className="char-count">25 / 1000</span>
                <span className="word-count">4 단어</span>
              </div>
              <div className="action-buttons">
                <button className="submit-answer-btn">
                  <Send className="w-4 h-4 mr-1" />
                  답변 제출
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ 
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        padding: '15px',
        backgroundColor: '#f0f7ff',
        border: '2px solid var(--primary-600)',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        maxWidth: '300px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', color: 'var(--primary-700)' }}>
          TARGET 아이콘 테스트 결과
        </h4>
        <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.4' }}>
          모든 아이콘이 표시되면 Lucide React 통합이 성공적으로 완료된 것입니다!
        </p>
      </div>
    </div>
  )
}