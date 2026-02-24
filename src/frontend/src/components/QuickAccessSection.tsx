import React from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  ChevronRight, 
  Clock, 
  TrendingUp, 
  Star, 
  FileText,
  GitBranch,
  CheckCircle2,
  AlertCircle,
  ArrowRight
} from 'lucide-react'
import { useQuickAccessDataWithCache } from '../hooks/useQuickAccessData'
import { usePageInitialization } from '../hooks/usePageInitialization'
import './QuickAccessSection.css'

export const QuickAccessSection: React.FC = () => {
  // 🔧 React Hooks Rules 준수 - 모든 hooks를 항상 같은 순서로 호출
  const { isDevelopmentActive } = usePageInitialization()
  const { data, isLoading, error, refetch } = useQuickAccessDataWithCache(3, isDevelopmentActive)
  const navigate = useNavigate()

  // 개발 모드에서 중복 키 디버깅을 위한 캐시 클리어 (항상 호출)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // 페이지 로드 시 캐시 클리어로 중복 데이터 방지
      localStorage.removeItem('quick-access-data')
      localStorage.removeItem('quick-access-data-time')
    }
  }, [])

  // ✅ 모든 hooks 호출 후에 조건부 렌더링 수행
  if (!isDevelopmentActive) {
    console.log('[QUICK_ACCESS] 개발 모드 비활성화 - 최근 활동 섹션 숨김')
    return null
  }


  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return '오늘'
    if (diffDays === 1) return '어제'
    if (diffDays < 7) return `${diffDays}일 전`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}주 전`
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}분`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}시간 ${mins}분` : `${hours}시간`
  }

  const handleAnalysisClick = (analysisId: string) => {
    console.log('[QUICK_ACCESS] 분석 결과 클릭:', analysisId)
    navigate(`/dashboard/${analysisId}`)
  }

  const handleReportClick = (interviewId: string) => {
    navigate(`/reports?interview=${interviewId}`)
  }

  if (isLoading) {
    return (
      <section className="quick-access-section">
        <div className="section-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="quick-access-loading">
          <div className="spinner"></div>
          <p>데이터를 불러오는 중...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="quick-access-section">
        <div className="section-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="quick-access-error">
          <AlertCircle className="error-icon" />
          <p>{error}</p>
          <button onClick={refetch} className="retry-btn">
            다시 시도
          </button>
        </div>
      </section>
    )
  }

  const hasData = data.recent_analyses.length > 0 || data.recent_reports.length > 0

  if (!hasData) {
    return (
      <section className="quick-access-section">
        <div className="section-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="quick-access-empty">
          <FileText className="empty-icon" />
          <h3>실제 분석 데이터가 없습니다</h3>
          <p>GitHub 저장소를 새로 분석하거나 실제 면접을 진행해보세요!</p>
          <div className="empty-actions">
            <button 
              onClick={() => navigate('/')} 
              className="primary-action-btn"
            >
              저장소 분석하기
            </button>
            <button 
              onClick={() => navigate('/dashboard')} 
              className="secondary-action-btn"
            >
              면접 시작하기
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="quick-access-section" aria-label="최근 활동">
      <div className="section-header">
        <h2>최근 활동</h2>
        <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
      </div>

      <div className="quick-access-grid">
        {/* 최근 분석 결과 */}
        {data.recent_analyses.length > 0 && (
          <div className="quick-access-card">
            <div className="card-header">
              <div className="card-title">
                <GitBranch className="title-icon" />
                <h3>최근 분석</h3>
              </div>
              <button 
                className="view-all-btn"
                onClick={() => navigate('/dashboard')}
                aria-label="분석 결과 전체보기"
              >
                전체보기 <ChevronRight className="btn-icon" />
              </button>
            </div>

            <div className="card-content">
              {data.recent_analyses.map((analysis) => (
                <div 
                  key={analysis.analysis_id} 
                  className="quick-item analysis-item"
                  onClick={() => handleAnalysisClick(analysis.analysis_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && handleAnalysisClick(analysis.analysis_id)}
                  aria-label={`${analysis.repository_owner}/${analysis.repository_name} 분석 결과 보기`}
                >
                  <div className="item-header">
                    <div className="item-title">
                      <span className="repo-name">
                        {analysis.repository_owner}/{analysis.repository_name}
                      </span>
                      <span className="item-date">
                        <Clock className="date-icon" />
                        {formatDate(analysis.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="item-details">
                    <div className="detail-tags">
                      <span className="language-tag">{analysis.primary_language}</span>
                      <span className="files-tag">{analysis.file_count}개 파일</span>
                      {analysis.tech_stack.slice(0, 2).map((tech, idx) => (
                        <span key={`${analysis.analysis_id}-tech-${idx}-${tech}`} className="tech-tag">{tech}</span>
                      ))}
                    </div>
                    <ArrowRight className="arrow-icon" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 최근 면접 리포트 */}
        {data.recent_reports.length > 0 && (
          <div className="quick-access-card">
            <div className="card-header">
              <div className="card-title">
                <TrendingUp className="title-icon" />
                <h3>최근 면접</h3>
              </div>
              <button 
                className="view-all-btn"
                onClick={() => navigate('/reports')}
                aria-label="면접 리포트 전체보기"
              >
                전체보기 <ChevronRight className="btn-icon" />
              </button>
            </div>

            <div className="card-content">
              {data.recent_reports.map((report) => (
                <div 
                  key={report.interview_id} 
                  className="quick-item report-item"
                  onClick={() => handleReportClick(report.interview_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && handleReportClick(report.interview_id)}
                  aria-label={`${report.repository_owner}/${report.repository_name} 면접 리포트 보기`}
                >
                  <div className="item-header">
                    <div className="item-title">
                      <span className="repo-name">
                        {report.repository_owner}/{report.repository_name}
                      </span>
                      <span className="item-date">
                        <Clock className="date-icon" />
                        {formatDate(report.completed_at)}
                      </span>
                    </div>
                  </div>

                  <div className="item-details">
                    <div className="detail-info">
                      <span className="duration-info">
                        <Star className="info-icon" />
                        {formatDuration(report.duration_minutes)}
                      </span>
                      <span className="questions-info">
                        <CheckCircle2 className="info-icon" />
                        {report.answers_count}/{report.questions_count} 답변
                      </span>
                      <span className="difficulty-tag">{report.difficulty_level}</span>
                    </div>
                    <ArrowRight className="arrow-icon" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
