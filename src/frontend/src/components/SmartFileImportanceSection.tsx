/**
 * 스마트 파일 중요도 분석 섹션 컴포넌트
 * 
 * 우리가 구현한 고급 분석 시스템(의존성, 변경 이력, 복잡도, 구조적 중요도)을 
 * 활용한 파일 중요도 시각화 및 선정 이유 표시
 */

import React, { useState, useMemo } from 'react'
import './SmartFileImportanceSection.css'
import FileDetailModal from './FileDetailModal'
import ImportanceDistributionChart from './ImportanceDistributionChart'

// 스마트 파일 중요도 분석 결과 인터페이스
interface SmartFileAnalysis {
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

interface FileImportanceDistribution {
  mean: number
  median: number
  std_dev: number
  min: number
  max: number
  quartiles: {
    q1: number
    q3: number
  }
}


interface SmartFileImportanceSectionProps {
  criticalFiles: SmartFileAnalysis[]
  distribution: FileImportanceDistribution
  suggestions: string[]
  onFileSelect?: (file: SmartFileAnalysis) => void
  showChart?: boolean
}

export const SmartFileImportanceSection: React.FC<SmartFileImportanceSectionProps> = ({
  criticalFiles,
  distribution,
  suggestions,
  onFileSelect,
  showChart = true
}) => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'critical' | 'important' | 'moderate' | 'low'>('all')
  const [sortBy, setSortBy] = useState<'importance' | 'complexity' | 'churn' | 'dependency'>('importance')
  const [showReasons, setShowReasons] = useState<Record<string, boolean>>({})
  const [modalFile, setModalFile] = useState<SmartFileAnalysis | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // 카테고리별 파일 분류
  const categorizedFiles = useMemo(() => {
    const categories = {
      critical: criticalFiles.filter(f => f.category === 'critical'),
      important: criticalFiles.filter(f => f.category === 'important'),
      moderate: criticalFiles.filter(f => f.category === 'moderate'),
      low: criticalFiles.filter(f => f.category === 'low')
    }

    if (selectedCategory === 'all') {
      return criticalFiles
    }
    return categories[selectedCategory] || []
  }, [criticalFiles, selectedCategory])

  // 정렬된 파일 목록
  const sortedFiles = useMemo(() => {
    return [...categorizedFiles].sort((a, b) => {
      switch (sortBy) {
        case 'importance':
          return b.importance_score - a.importance_score
        case 'complexity':
          return b.metrics.complexity_score - a.metrics.complexity_score
        case 'churn':
          return b.metrics.churn_risk - a.metrics.churn_risk
        case 'dependency':
          return b.metrics.dependency_centrality - a.metrics.dependency_centrality
        default:
          return 0
      }
    })
  }, [categorizedFiles, sortBy])

  // 중요도 점수 색상 계산
  const getImportanceColor = (score: number): string => {
    if (score >= 0.8) return 'var(--primary-700)' // Critical
    if (score >= 0.6) return 'var(--primary-600)' // Important  
    if (score >= 0.4) return 'var(--primary-500)' // Moderate
    return 'var(--gray-500)' // Low
  }

  // 카테고리 뱃지 색상
  const getCategoryBadgeClass = (category: string): string => {
    switch (category) {
      case 'critical': return 'badge-critical'
      case 'important': return 'badge-important'
      case 'moderate': return 'badge-moderate'
      case 'low': return 'badge-low'
      default: return 'badge-default'
    }
  }


  // 이유 표시 토글
  const toggleReasons = (filePath: string) => {
    setShowReasons(prev => ({
      ...prev,
      [filePath]: !prev[filePath]
    }))
  }

  // 파일 상세 모달 열기
  const handleFileClick = (file: SmartFileAnalysis) => {
    setModalFile(file)
    setIsModalOpen(true)
    onFileSelect?.(file)
  }

  // 파일 상세 모달 닫기
  const handleModalClose = () => {
    setIsModalOpen(false)
    setModalFile(null)
  }

  return (
    <div className="smart-file-importance-section">
      {/* 헤더 및 개요 */}
      <div className="section-header">
        <h3>◎ 스마트 파일 중요도 분석</h3>
        <p className="section-description">
          의존성, 변경 이력, 복잡도, 구조적 패턴을 종합하여 계산된 파일 중요도
        </p>
      </div>

      {/* 중요도 분포 통계 */}
      <div className="importance-distribution">
        <h4>◈ 중요도 분포 통계</h4>
        <div className="distribution-stats">
          <div className="stat-item">
            <div className="stat-label">평균</div>
            <div className="stat-value">{distribution.mean.toFixed(3)}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">중간값</div>
            <div className="stat-value">{distribution.median.toFixed(3)}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">표준편차</div>
            <div className="stat-value">{distribution.std_dev.toFixed(3)}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">최대값</div>
            <div className="stat-value">{distribution.max.toFixed(3)}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Q1-Q3</div>
            <div className="stat-value">{distribution.quartiles.q1.toFixed(2)}-{distribution.quartiles.q3.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* 중요도 분포 차트 */}
      {showChart && (
        <ImportanceDistributionChart
          files={criticalFiles.map(file => ({
            file_path: file.file_path,
            importance_score: file.importance_score,
            category: file.category
          }))}
          showChart={showChart}
        />
      )}

      {/* 카테고리별 요약 */}
      <div className="category-summary">
        <h4>◐ 카테고리별 요약</h4>
        <div className="category-cards">
          {[
            { key: 'critical', label: 'Critical', count: criticalFiles.filter(f => f.category === 'critical').length },
            { key: 'important', label: 'Important', count: criticalFiles.filter(f => f.category === 'important').length },
            { key: 'moderate', label: 'Moderate', count: criticalFiles.filter(f => f.category === 'moderate').length },
            { key: 'low', label: 'Low', count: criticalFiles.filter(f => f.category === 'low').length }
          ].map(category => (
            <div 
              key={category.key} 
              className={`category-card ${getCategoryBadgeClass(category.key)} ${selectedCategory === category.key ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category.key as any)}
            >
              <div className="category-count">{category.count}</div>
              <div className="category-label">{category.label}</div>
            </div>
          ))}
          <div 
            className={`category-card badge-default ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            <div className="category-count">{criticalFiles.length}</div>
            <div className="category-label">All</div>
          </div>
        </div>
      </div>

      {/* 정렬 및 필터 */}
      <div className="controls">
        <div className="sort-controls">
          <label>정렬 기준:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="importance">중요도 점수</option>
            <option value="complexity">복잡도</option>
            <option value="churn">변경 빈도</option>
            <option value="dependency">의존성 중심성</option>
          </select>
        </div>
      </div>

      {/* 파일 목록 */}
      <div className="files-list">
        <h4>◐ 파일 목록 ({sortedFiles.length}개)</h4>
        <div className="files-container">
          {sortedFiles.map((file, index) => (
            <div 
              key={file.file_path} 
              className="file-card"
              onClick={() => handleFileClick(file)}
            >
              {/* 파일 헤더 */}
              <div className="file-header">
                <div className="file-info">
                  <div className="file-path">{file.file_path}</div>
                  <div className="file-rank">#{file.rank}</div>
                </div>
                <div className="file-badges">
                  <span className={`category-badge ${getCategoryBadgeClass(file.category)}`}>
                    {file.category.toUpperCase()}
                  </span>
                  <span className="importance-score" style={{ color: getImportanceColor(file.importance_score) }}>
                    {file.importance_score.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* 메트릭 시각화 */}
              <div className="metrics-visualization">
                <div className="metric-bar">
                  <div className="metric-label">구조적 중요도</div>
                  <div className="metric-progress">
                    <div 
                      className="progress-fill structural"
                      style={{ width: `${file.metrics.structural_importance * 100}%` }}
                    ></div>
                    <span className="metric-value">{file.metrics.structural_importance.toFixed(2)}</span>
                  </div>
                </div>
                <div className="metric-bar">
                  <div className="metric-label">의존성 중심성</div>
                  <div className="metric-progress">
                    <div 
                      className="progress-fill dependency"
                      style={{ width: `${file.metrics.dependency_centrality * 100}%` }}
                    ></div>
                    <span className="metric-value">{file.metrics.dependency_centrality.toFixed(2)}</span>
                  </div>
                </div>
                <div className="metric-bar">
                  <div className="metric-label">변경 위험도</div>
                  <div className="metric-progress">
                    <div 
                      className="progress-fill churn"
                      style={{ width: `${file.metrics.churn_risk * 100}%` }}
                    ></div>
                    <span className="metric-value">{file.metrics.churn_risk.toFixed(2)}</span>
                  </div>
                </div>
                <div className="metric-bar">
                  <div className="metric-label">복잡도</div>
                  <div className="metric-progress">
                    <div 
                      className="progress-fill complexity"
                      style={{ width: `${file.metrics.complexity_score * 100}%` }}
                    ></div>
                    <span className="metric-value">{file.metrics.complexity_score.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* 선정 이유 */}
              <div className="selection-reasons">
                <button 
                  className="reasons-toggle"
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleReasons(file.file_path)
                  }}
                >
                  {showReasons[file.file_path] ? '▼' : '▶'} 선정 이유 ({file.reasons.length}개)
                </button>
                {showReasons[file.file_path] && (
                  <div className="reasons-list">
                    {file.reasons.map((reason, reasonIndex) => (
                      <div key={reasonIndex} className="reason-item">
                        <span className="reason-icon">•</span>
                        <span className="reason-text">{reason}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 개선 제안 */}
      <div className="improvement-suggestions">
        <h4>◇ 개선 제안</h4>
        <div className="suggestions-list">
          {suggestions.map((suggestion, index) => (
            <div key={index} className="suggestion-item">
              <div className="suggestion-message">
                <span className="suggestion-icon">◇</span>
                {suggestion}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 파일 상세 모달 */}
      <FileDetailModal
        isOpen={isModalOpen}
        file={modalFile}
        onClose={handleModalClose}
      />
    </div>
  )
}

export default SmartFileImportanceSection