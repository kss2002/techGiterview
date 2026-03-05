import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileText,
  GitBranch,
  Star,
  TrendingUp
} from 'lucide-react'
import { useQuickAccessDataWithCache } from '../../hooks/useQuickAccessData'
import { setAnalysisToken } from '../../utils/apiHeaders'
import './QuickAccessV2.css'

interface QuickAccessV2Props {
  limit?: number
}

const formatRelativeDate = (dateString: string): string => {
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

const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes}분`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}시간 ${mins}분` : `${hours}시간`
}

export function QuickAccessV2({ limit = 3 }: QuickAccessV2Props) {
  const navigate = useNavigate()
  const { data, isLoading, error, refetch } = useQuickAccessDataWithCache(limit)

  const handleAnalysisClick = (analysisId: string, analysisToken?: string) => {
    if (analysisToken) {
      setAnalysisToken(analysisId, analysisToken)
    }
    navigate(`/dashboard/${analysisId}`)
  }

  const handleReportClick = (interviewId: string) => {
    navigate(`/reports?interview=${interviewId}`)
  }

  if (isLoading) {
    return (
      <section className="v2-qa" aria-label="최근 활동">
        <div className="v2-qa-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="v2-qa-state">
          <div className="v2-spinner" />
          <p>활동 데이터를 불러오는 중입니다...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="v2-qa" aria-label="최근 활동">
        <div className="v2-qa-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="v2-qa-state v2-qa-state--error">
          <AlertCircle className="v2-icon-sm" />
          <p>{error}</p>
          <button className="v2-btn v2-btn-outline v2-btn-sm" onClick={refetch}>
            다시 시도
          </button>
        </div>
      </section>
    )
  }

  const hasData = data.recent_analyses.length > 0 || data.recent_reports.length > 0
  if (!hasData) {
    return (
      <section className="v2-qa" aria-label="최근 활동">
        <div className="v2-qa-header">
          <h2>최근 활동</h2>
          <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
        </div>
        <div className="v2-qa-state">
          <FileText className="v2-icon-sm" />
          <p>아직 활동 데이터가 없습니다. 저장소 분석을 시작해보세요.</p>
          <button className="v2-btn v2-btn-primary v2-btn-sm" onClick={() => navigate('/')}>
            저장소 분석 시작
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="v2-qa" aria-label="최근 활동">
      <div className="v2-qa-header">
        <h2>최근 활동</h2>
        <p>최근 분석 및 면접 결과를 빠르게 확인하세요</p>
      </div>

      <div className="v2-qa-grid">
        <article className="v2-qa-card">
          <div className="v2-qa-card-head">
            <div className="v2-qa-card-title">
              <GitBranch className="v2-icon-sm" />
              <h3>최근 분석</h3>
            </div>
            <button className="v2-btn v2-btn-ghost v2-btn-sm" onClick={() => navigate('/dashboard')}>
              전체보기
            </button>
          </div>
          <div className="v2-qa-list">
            {data.recent_analyses.length > 0 ? (
              data.recent_analyses.map((analysis) => (
                <button
                  key={analysis.analysis_id}
                  className="v2-qa-item"
                  onClick={() => handleAnalysisClick(analysis.analysis_id, analysis.analysis_token)}
                  aria-label={`${analysis.repository_owner}/${analysis.repository_name} 분석 결과 보기`}
                >
                  <div className="v2-qa-item-main">
                    <div className="v2-qa-item-title">
                      {analysis.repository_owner}/{analysis.repository_name}
                    </div>
                    <div className="v2-qa-item-meta">
                      <span className="v2-qa-meta-chip">
                        <Clock3 className="v2-icon-xs" />
                        {formatRelativeDate(analysis.created_at)}
                      </span>
                      <span className="v2-qa-meta-chip">{analysis.primary_language}</span>
                      <span className="v2-qa-meta-chip">{analysis.file_count}개 파일</span>
                    </div>
                  </div>
                  <ArrowRight className="v2-icon-xs" />
                </button>
              ))
            ) : (
              <div className="v2-qa-empty">
                <p>최근 분석이 없습니다. 첫 저장소 분석을 시작해보세요.</p>
                <button className="v2-btn v2-btn-outline v2-btn-sm" onClick={() => navigate('/')}>
                  분석 시작하기
                </button>
              </div>
            )}
          </div>
        </article>

        <article className="v2-qa-card">
          <div className="v2-qa-card-head">
            <div className="v2-qa-card-title">
              <TrendingUp className="v2-icon-sm" />
              <h3>최근 면접</h3>
            </div>
            <button className="v2-btn v2-btn-ghost v2-btn-sm" onClick={() => navigate('/reports')}>
              전체보기
            </button>
          </div>
          <div className="v2-qa-list">
            {data.recent_reports.length > 0 ? (
              data.recent_reports.map((report) => (
                <button
                  key={report.interview_id}
                  className="v2-qa-item"
                  onClick={() => handleReportClick(report.interview_id)}
                  aria-label={`${report.repository_owner}/${report.repository_name} 면접 리포트 보기`}
                >
                  <div className="v2-qa-item-main">
                    <div className="v2-qa-item-title">
                      {report.repository_owner}/{report.repository_name}
                    </div>
                    <div className="v2-qa-item-meta">
                      <span className="v2-qa-meta-chip">
                        <Clock3 className="v2-icon-xs" />
                        {formatRelativeDate(report.completed_at)}
                      </span>
                      <span className="v2-qa-meta-chip">
                        <Star className="v2-icon-xs" />
                        {formatDuration(report.duration_minutes)}
                      </span>
                      <span className="v2-qa-meta-chip">
                        <CheckCircle2 className="v2-icon-xs" />
                        {report.answers_count}/{report.questions_count}
                      </span>
                    </div>
                  </div>
                  <ArrowRight className="v2-icon-xs" />
                </button>
              ))
            ) : (
              <div className="v2-qa-empty">
                <p>아직 완료된 면접이 없습니다. 질문을 생성하고 첫 모의면접을 시작해보세요.</p>
                <button className="v2-btn v2-btn-outline v2-btn-sm" onClick={() => navigate('/dashboard')}>
                  면접 시작 경로 열기
                </button>
              </div>
            )}
          </div>
        </article>
      </div>
    </section>
  )
}
