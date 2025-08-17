/**
 * 파일 상세 정보 모달 컴포넌트
 * 
 * SmartFileImportanceSection에서 파일 클릭 시 표시되는 상세 정보 모달
 * 파일의 종합적인 분석 결과와 메트릭을 시각화
 */

import React, { useState } from 'react'
import './FileDetailModal.css'

// 파일 상세 정보 인터페이스
interface FileDetailInfo {
  file_path: string
  importance_score: number
  reasons: string[]
  metrics: {
    structural_importance: number
    dependency_centrality: number
    churn_risk: number
    complexity_score: number
  }
  category: 'critical' | 'important' | 'moderate' | 'low'
  rank: number
  additional_info?: {
    file_size: string
    last_modified: string
    contributors: string[]
    dependencies: string[]
    dependents: string[]
    lines_of_code?: number
    test_coverage?: number
  }
}

interface FileDetailModalProps {
  isOpen: boolean
  file: FileDetailInfo | null
  onClose: () => void
}

type TabType = 'overview' | 'metrics' | 'dependencies' | 'history'

export const FileDetailModal: React.FC<FileDetailModalProps> = ({
  isOpen,
  file,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  if (!isOpen || !file) {
    return null
  }

  // 중요도 점수에 따른 색상 결정
  const getImportanceColor = (score: number): string => {
    if (score >= 0.8) return 'var(--primary-700)' // Critical
    if (score >= 0.6) return 'var(--primary-600)' // Important  
    if (score >= 0.4) return 'var(--primary-500)' // Moderate
    return 'var(--gray-500)' // Low
  }

  // 카테고리 배지 클래스
  const getCategoryBadgeClass = (category: string): string => {
    switch (category) {
      case 'critical': return 'badge-critical'
      case 'important': return 'badge-important'
      case 'moderate': return 'badge-moderate'
      case 'low': return 'badge-low'
      default: return 'badge-default'
    }
  }

  // 메트릭 설명 매핑
  const getMetricDescription = (metricName: string): string => {
    const descriptions = {
      structural_importance: '파일의 구조적 중요성 (진입점, 설정 파일 등)',
      dependency_centrality: '다른 파일들로부터의 의존성 중심도',
      churn_risk: '최근 변경 빈도 및 변경 위험도',
      complexity_score: '코드 복잡도 (순환복잡도, 중첩 깊이 등)'
    }
    return descriptions[metricName as keyof typeof descriptions] || ''
  }

  // 모달 외부 클릭 시 닫기
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  // ESC 키로 모달 닫기
  React.useEffect(() => {
    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey)
      // 스크롤 방지
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="file-detail-modal">
        {/* 모달 헤더 */}
        <div className="modal-header">
          <div className="header-content">
            <div className="file-info">
              <h2 className="file-path">{file.file_path}</h2>
              <div className="file-badges">
                <span className={`category-badge ${getCategoryBadgeClass(file.category)}`}>
                  {file.category.toUpperCase()}
                </span>
                <span className="rank-badge">#{file.rank}</span>
                <span 
                  className="importance-score"
                  style={{ color: getImportanceColor(file.importance_score) }}
                >
                  {file.importance_score.toFixed(3)}
                </span>
              </div>
            </div>
            <button className="close-button" onClick={onClose} aria-label="모달 닫기">
              X
            </button>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="tab-navigation">
          {[
            { key: 'overview', label: '개요', icon: '◐' },
            { key: 'metrics', label: '메트릭', icon: '◈' },
            { key: 'dependencies', label: '의존성', icon: '◇' },
            { key: 'history', label: '변경 이력', icon: '▲' }
          ].map(tab => (
            <button
              key={tab.key}
              className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key as TabType)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* 모달 컨텐츠 */}
        <div className="modal-content">
          {/* 개요 탭 */}
          {activeTab === 'overview' && (
            <div className="tab-content">
              <div className="overview-grid">
                {/* 기본 정보 */}
                <div className="info-card">
                  <h3>◐ 파일 정보</h3>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">파일 크기:</span>
                      <span className="info-value">
                        {file.additional_info?.file_size || 'N/A'}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">최종 수정:</span>
                      <span className="info-value">
                        {file.additional_info?.last_modified || 'N/A'}
                      </span>
                    </div>
                    {file.additional_info?.lines_of_code && (
                      <div className="info-item">
                        <span className="info-label">코드 라인 수:</span>
                        <span className="info-value">
                          {file.additional_info.lines_of_code.toLocaleString()}
                        </span>
                      </div>
                    )}
                    {file.additional_info?.test_coverage !== undefined && (
                      <div className="info-item">
                        <span className="info-label">테스트 커버리지:</span>
                        <span className="info-value">
                          {file.additional_info.test_coverage}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 선정 이유 */}
                <div className="info-card">
                  <h3>◎ 선정 이유</h3>
                  <div className="reasons-list">
                    {file.reasons.map((reason, index) => (
                      <div key={index} className="reason-item">
                        <span className="reason-icon">•</span>
                        <span className="reason-text">{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 기여자 정보 */}
                {file.additional_info?.contributors && (
                  <div className="info-card">
                    <h3>● 기여자</h3>
                    <div className="contributors-list">
                      {file.additional_info.contributors.slice(0, 5).map((contributor, index) => (
                        <div key={index} className="contributor-item">
                          <span className="contributor-avatar">●</span>
                          <span className="contributor-name">{contributor}</span>
                        </div>
                      ))}
                      {file.additional_info.contributors.length > 5 && (
                        <div className="contributor-item">
                          <span className="more-contributors">
                            +{file.additional_info.contributors.length - 5} more
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 메트릭 탭 */}
          {activeTab === 'metrics' && (
            <div className="tab-content">
              <div className="metrics-detailed">
                <div className="score-overview">
                  <div className="score-circle">
                    <div className="score-value">{file.importance_score.toFixed(3)}</div>
                    <div className="score-label">종합 중요도</div>
                  </div>
                </div>

                <div className="metrics-breakdown">
                  {Object.entries(file.metrics).map(([metricName, value]) => (
                    <div key={metricName} className="metric-detail-card">
                      <div className="metric-header">
                        <div className="metric-name">
                          {metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div className="metric-score">{value.toFixed(3)}</div>
                      </div>
                      
                      <div className="metric-progress-bar">
                        <div 
                          className={`progress-fill ${metricName}`}
                          style={{ width: `${value * 100}%` }}
                        ></div>
                      </div>
                      
                      <div className="metric-description">
                        {getMetricDescription(metricName)}
                      </div>
                      
                      {/* 가중치 정보 */}
                      <div className="metric-weight">
                        가중치: {
                          metricName === 'structural_importance' ? '40%' :
                          metricName === 'dependency_centrality' ? '30%' :
                          metricName === 'churn_risk' ? '20%' : '10%'
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 의존성 탭 */}
          {activeTab === 'dependencies' && (
            <div className="tab-content">
              <div className="dependencies-grid">
                {/* 의존 관계 */}
                {file.additional_info?.dependencies && (
                  <div className="dependency-card">
                    <h3>□ Dependencies (이 파일이 사용하는)</h3>
                    <div className="dependency-list">
                      {file.additional_info.dependencies.map((dep, index) => (
                        <div key={index} className="dependency-item">
                          <span className="dependency-icon">□</span>
                          <span className="dependency-name">{dep}</span>
                        </div>
                      ))}
                      {file.additional_info.dependencies.length === 0 && (
                        <div className="no-dependencies">의존성이 없습니다.</div>
                      )}
                    </div>
                  </div>
                )}

                {/* 의존받는 관계 */}
                {file.additional_info?.dependents && (
                  <div className="dependency-card">
                    <h3>◇ Dependents (이 파일을 사용하는)</h3>
                    <div className="dependency-list">
                      {file.additional_info.dependents.map((dep, index) => (
                        <div key={index} className="dependency-item">
                          <span className="dependency-icon">◇</span>
                          <span className="dependency-name">{dep}</span>
                        </div>
                      ))}
                      {file.additional_info.dependents.length === 0 && (
                        <div className="no-dependencies">이 파일을 참조하는 파일이 없습니다.</div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* 중심성 지표 */}
              <div className="centrality-info">
                <h3>◎ 중심성 분석</h3>
                <div className="centrality-score">
                  <div className="centrality-value">
                    {file.metrics.dependency_centrality.toFixed(3)}
                  </div>
                  <div className="centrality-description">
                    이 파일의 의존성 중심성 점수입니다.<br/>
                    높을수록 다른 파일들이 많이 참조하는 핵심 파일입니다.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 변경 이력 탭 */}
          {activeTab === 'history' && (
            <div className="tab-content">
              <div className="history-overview">
                <div className="churn-info">
                  <h3>▲ 변경 빈도 분석</h3>
                  <div className="churn-metrics">
                    <div className="churn-score">
                      <div className="churn-value">
                        {file.metrics.churn_risk.toFixed(3)}
                      </div>
                      <div className="churn-label">변경 위험도</div>
                    </div>
                    <div className="churn-description">
                      <div className="description-item">
                        <strong>높은 변경 빈도</strong>는 활발한 개발을 의미하지만, 
                        동시에 불안정성을 나타낼 수도 있습니다.
                      </div>
                      <div className="description-item">
                        이 파일의 변경 패턴을 주의 깊게 모니터링하여 
                        코드 품질을 유지하는 것이 중요합니다.
                      </div>
                    </div>
                  </div>
                </div>

                {/* 변경 추천사항 */}
                <div className="change-recommendations">
                  <h3>◇ 권장사항</h3>
                  <div className="recommendations-list">
                    {file.metrics.churn_risk > 0.7 && (
                      <div className="recommendation-item high-priority">
                        <span className="rec-icon">▲</span>
                        <span className="rec-text">
                          높은 변경 빈도 - 코드 안정성 검토 및 테스트 강화 필요
                        </span>
                      </div>
                    )}
                    {file.metrics.complexity_score > 0.6 && (
                      <div className="recommendation-item medium-priority">
                        <span className="rec-icon">▣</span>
                        <span className="rec-text">
                          복잡도 개선 - 함수 분리 및 리팩토링 고려
                        </span>
                      </div>
                    )}
                    {file.metrics.dependency_centrality > 0.8 && (
                      <div className="recommendation-item low-priority">
                        <span className="rec-icon">◎</span>
                        <span className="rec-text">
                          핵심 의존성 파일 - 변경 시 영향도 분석 필수
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FileDetailModal