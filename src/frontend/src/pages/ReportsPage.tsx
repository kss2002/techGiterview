import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  BookOpen, 
  TrendingUp,
  Star,
  Diamond,
  FileText,
  BarChart3,
  Target,
  Circle,
  Clock,
  Award,
  CheckCircle2,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import './ReportsPage.css'

interface InterviewReport {
  id: string
  repo_url: string
  repo_name: string
  completed_at: string
  total_questions: number
  answered_questions: number
  overall_score: number
  category_scores: Record<string, number>
  duration_minutes: number
  status: 'completed' | 'in_progress'
}

interface DetailedReport {
  interview_id: string
  repo_info: {
    name: string
    owner: string
    description: string
    language: string
  }
  overall_assessment: {
    score: number
    strengths: string[]
    weaknesses: string[]
    recommendations: string[]
  }
  question_analyses: Array<{
    question: string
    category: string
    difficulty: string
    answer: string
    score: number
    feedback: string
    improvement_suggestions: string[]
  }>
  performance_metrics: {
    response_time_avg: number
    completeness_score: number
    technical_accuracy: number
    communication_clarity: number
  }
}

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<InterviewReport[]>([])
  const [selectedReport, setSelectedReport] = useState<DetailedReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [filter, setFilter] = useState<'all' | 'completed' | 'in_progress'>('all')
  const navigate = useNavigate()

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      console.log('[REPORTS] API 요청 시작: /api/v1/reports/list')
      const response = await fetch('/api/v1/reports/list')
      
      console.log('[REPORTS] API 응답 상태:', response.status)
      
      if (!response.ok) {
        throw new Error(`서버 응답 오류: ${response.status} ${response.statusText}`)
      }

      const result = await response.json()
      console.log('[REPORTS] API 응답 데이터:', result)
      
      if (result.success) {
        setReports(result.data.reports)
        console.log('[REPORTS] 리포트 데이터 설정 완료:', result.data.reports.length, '개')
      } else {
        throw new Error(result.message || '리포트 데이터를 처리할 수 없습니다.')
      }
    } catch (error) {
      console.error('Error loading reports:', error)
      // 사용자에게 에러 상태 표시
      setReports([])
    } finally {
      setIsLoading(false)
    }
  }

  const loadDetailedReport = async (interviewId: string) => {
    setIsLoadingDetail(true)
    try {
      const response = await fetch(`/api/v1/reports/${interviewId}/detailed`)
      
      if (!response.ok) {
        throw new Error('상세 리포트를 불러올 수 없습니다.')
      }

      const result = await response.json()
      if (result.success) {
        setSelectedReport(result.data)
      }
    } catch (error) {
      console.error('Error loading detailed report:', error)
      alert('상세 리포트를 불러오는데 실패했습니다.')
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const filteredReports = reports.filter(report => {
    if (filter === 'all') return true
    return report.status === filter
  })

  const getScoreClass = (score: number) => {
    if (score >= 80) return 'score-excellent'
    if (score >= 60) return 'score-good'
    if (score >= 40) return 'score-fair'
    return 'score-poor'
  }

  const getScoreGrade = (score: number) => {
    if (score >= 90) return 'A+'
    if (score >= 80) return 'A'
    if (score >= 70) return 'B+'
    if (score >= 60) return 'B'
    if (score >= 50) return 'C+'
    if (score >= 40) return 'C'
    return 'D'
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}시간 ${mins}분`
    }
    return `${mins}분`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="reports-loading">
        <div className="spinner-large"></div>
        <p>리포트를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div className="reports-page">
      <div className="reports-header">
        <div className="header-content">
          <h1><FileText className="icon" /> 면접 리포트</h1>
          <p>당신의 면접 성과를 분석하고 개선점을 확인하세요</p>
        </div>
        
        <div className="header-actions">
          <div className="filter-buttons">
            <button 
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              전체 ({reports.length})
            </button>
            <button 
              className={filter === 'completed' ? 'active' : ''}
              onClick={() => setFilter('completed')}
            >
              완료 ({reports.filter(r => r.status === 'completed').length})
            </button>
            <button 
              className={filter === 'in_progress' ? 'active' : ''}
              onClick={() => setFilter('in_progress')}
            >
              진행중 ({reports.filter(r => r.status === 'in_progress').length})
            </button>
          </div>
          
          <button 
            className="new-interview-btn"
            onClick={() => navigate('/')}
          >
            새 면접 시작
          </button>
        </div>
      </div>

      <div className="reports-content">
        {filteredReports.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"><Circle className="icon" /></div>
            <h3>아직 면접 리포트가 없습니다</h3>
            <p>첫 번째 면접을 시작해서 리포트를 생성해보세요!</p>
            <button 
              className="start-first-interview-btn"
              onClick={() => navigate('/')}
            >
              첫 면접 시작하기
            </button>
          </div>
        ) : (
          <div className="reports-grid">
            {/* 리포트 목록 */}
            <div className="reports-list">
              <h2>면접 기록</h2>
              <div className="reports-cards">
                {filteredReports.map((report) => (
                  <div 
                    key={report.id} 
                    className={`report-card ${selectedReport?.interview_id === report.id ? 'selected' : ''}`}
                    onClick={() => loadDetailedReport(report.id)}
                  >
                    <div className="report-card-header">
                      <div className="report-title">
                        <h3>{report.repo_name}</h3>
                        <span className={`status-badge ${report.status}`}>
                          {report.status === 'completed' ? '완료' : '진행중'}
                        </span>
                      </div>
                      <div className="report-score">
                        <span 
                          className={`score-value ${getScoreClass(report.overall_score)}`}
                        >
                          {report.overall_score}
                        </span>
                        <span className="score-grade">
                          {getScoreGrade(report.overall_score)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="report-card-content">
                      <div className="report-meta">
                        <div className="meta-item">
                          <span className="meta-icon"><Star className="icon" /></span>
                          <span>{formatDate(report.completed_at)}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-icon"><BookOpen className="icon" /></span>
                          <span>{formatDuration(report.duration_minutes)}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-icon"><TrendingUp className="icon" /></span>
                          <span>{report.answered_questions}/{report.total_questions} 답변</span>
                        </div>
                      </div>
                      
                      <div className="category-scores">
                        {Object.entries(report.category_scores).map(([category, score]) => (
                          <div key={category} className="category-score">
                            <span className="category-name">{category}</span>
                            <div className="score-bar">
                              <div 
                                className={`score-fill ${getScoreClass(score)}`}
                                style={{ width: `${score}%` }}
                              ></div>
                            </div>
                            <span className="score-text">{score}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 상세 리포트 */}
            <div className="detailed-report">
              {isLoadingDetail ? (
                <div className="detail-loading">
                  <div className="spinner"></div>
                  <p>상세 리포트를 불러오는 중...</p>
                </div>
              ) : selectedReport ? (
                <div className="report-detail-content">
                  <div className="detail-header">
                    <h2><BarChart3 className="icon" /> 상세 분석</h2>
                    <div className="repo-info">
                      <h3>{selectedReport.repo_info.owner}/{selectedReport.repo_info.name}</h3>
                      <p>{selectedReport.repo_info.description}</p>
                      <span className="language-tag">{selectedReport.repo_info.language}</span>
                    </div>
                  </div>

                  {/* 전체 평가 */}
                  <div className="assessment-section">
                    <h3><ArrowUp className="icon" /> 전체 평가</h3>
                    <div className="assessment-score">
                      <div className="score-display">
                        <span 
                          className={`big-score ${getScoreClass(selectedReport.overall_assessment.score)}`}
                        >
                          {selectedReport.overall_assessment.score}
                        </span>
                        <span className="score-suffix">점</span>
                      </div>
                      <span className="score-grade-big">
                        {getScoreGrade(selectedReport.overall_assessment.score)}
                      </span>
                    </div>
                    
                    <div className="assessment-details">
                      <div className="strengths">
                        <h4><ArrowUp className="icon" /> 강점</h4>
                        <ul>
                          {selectedReport.overall_assessment.strengths.map((strength, index) => (
                            <li key={index}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="weaknesses">
                        <h4><ArrowDown className="icon" /> 개선점</h4>
                        <ul>
                          {selectedReport.overall_assessment.weaknesses.map((weakness, index) => (
                            <li key={index}>{weakness}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="recommendations">
                        <h4><Diamond className="icon" /> 추천 학습</h4>
                        <ul>
                          {selectedReport.overall_assessment.recommendations.map((recommendation, index) => (
                            <li key={index}>{recommendation}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* 성과 지표 */}
                  <div className="metrics-section">
                    <h3><Target className="icon" /> 성과 지표</h3>
                    <div className="metrics-grid">
                      <div className="metric-card">
                        <div className="metric-icon"><Clock className="icon" /></div>
                        <div className="metric-content">
                          <span className="metric-label">평균 응답 시간</span>
                          <span className="metric-value">{selectedReport.performance_metrics.response_time_avg}초</span>
                        </div>
                      </div>
                      
                      <div className="metric-card">
                        <div className="metric-icon"><CheckCircle2 className="icon" /></div>
                        <div className="metric-content">
                          <span className="metric-label">답변 완성도</span>
                          <span className="metric-value">{selectedReport.performance_metrics.completeness_score}%</span>
                        </div>
                      </div>
                      
                      <div className="metric-card">
                        <div className="metric-icon"><Target className="icon" /></div>
                        <div className="metric-content">
                          <span className="metric-label">기술적 정확성</span>
                          <span className="metric-value">{selectedReport.performance_metrics.technical_accuracy}%</span>
                        </div>
                      </div>
                      
                      <div className="metric-card">
                        <div className="metric-icon"><Award className="icon" /></div>
                        <div className="metric-content">
                          <span className="metric-label">의사소통 명확성</span>
                          <span className="metric-value">{selectedReport.performance_metrics.communication_clarity}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 질문별 분석 */}
                  <div className="questions-analysis">
                    <h3><BarChart3 className="icon" /> 질문별 분석</h3>
                    <div className="question-analyses">
                      {selectedReport.question_analyses.map((analysis, index) => (
                        <div key={index} className="question-analysis-card">
                          <div className="analysis-header">
                            <div className="question-info">
                              <span className="question-number">Q{index + 1}</span>
                              <span className="question-category">{analysis.category}</span>
                              <span className="question-difficulty">{analysis.difficulty}</span>
                            </div>
                            <div className="question-score">
                              <span 
                                className={`score ${getScoreClass(analysis.score)}`}
                              >
                                {analysis.score}점
                              </span>
                            </div>
                          </div>
                          
                          <div className="analysis-content">
                            <div className="question-text">
                              <h4>질문</h4>
                              <p>{analysis.question}</p>
                            </div>
                            
                            <div className="answer-text">
                              <h4>답변</h4>
                              <p>{analysis.answer}</p>
                            </div>
                            
                            <div className="feedback-text">
                              <h4>피드백</h4>
                              <p>{analysis.feedback}</p>
                            </div>
                            
                            {analysis.improvement_suggestions.length > 0 && (
                              <div className="improvements">
                                <h4>개선 제안</h4>
                                <ul>
                                  {analysis.improvement_suggestions.map((suggestion, idx) => (
                                    <li key={idx}>{suggestion}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="no-selection">
                  <div className="no-selection-icon"><FileText className="icon" /></div>
                  <h3>리포트를 선택하세요</h3>
                  <p>왼쪽 목록에서 리포트를 클릭하면 상세 분석을 확인할 수 있습니다.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}