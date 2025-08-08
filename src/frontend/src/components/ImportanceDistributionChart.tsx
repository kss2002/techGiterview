/**
 * 중요도 분포 차트 컴포넌트
 * 
 * Chart.js를 사용하여 파일 중요도 점수의 분포를 시각화
 */

import React, { useMemo } from 'react'
import './ImportanceDistributionChart.css'

interface FileImportanceData {
  file_path: string
  importance_score: number
  category: 'critical' | 'important' | 'moderate' | 'low'
}

interface ImportanceDistributionChartProps {
  files: FileImportanceData[]
  showChart?: boolean
}

export const ImportanceDistributionChart: React.FC<ImportanceDistributionChartProps> = ({
  files,
  showChart = true
}) => {
  // 히스토그램 데이터 생성
  const histogramData = useMemo(() => {
    const bins = 10
    const minScore = Math.min(...files.map(f => f.importance_score))
    const maxScore = Math.max(...files.map(f => f.importance_score))
    const binSize = (maxScore - minScore) / bins
    
    const histogram = Array(bins).fill(0).map((_, i) => ({
      range: `${(minScore + i * binSize).toFixed(2)}-${(minScore + (i + 1) * binSize).toFixed(2)}`,
      count: 0,
      files: [] as FileImportanceData[]
    }))
    
    files.forEach(file => {
      const binIndex = Math.min(
        Math.floor((file.importance_score - minScore) / binSize),
        bins - 1
      )
      histogram[binIndex].count++
      histogram[binIndex].files.push(file)
    })
    
    return histogram
  }, [files])

  // 카테고리별 분포
  const categoryDistribution = useMemo(() => {
    const distribution = {
      critical: files.filter(f => f.category === 'critical').length,
      important: files.filter(f => f.category === 'important').length,
      moderate: files.filter(f => f.category === 'moderate').length,
      low: files.filter(f => f.category === 'low').length
    }
    
    const total = files.length
    return Object.entries(distribution).map(([category, count]) => ({
      category,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0
    }))
  }, [files])

  // 통계 계산
  const statistics = useMemo(() => {
    if (files.length === 0) {
      return { mean: 0, median: 0, stdDev: 0, min: 0, max: 0 }
    }

    const scores = files.map(f => f.importance_score).sort((a, b) => a - b)
    const mean = scores.reduce((sum, score) => sum + score, 0) / scores.length
    const median = scores.length % 2 === 0
      ? (scores[scores.length / 2 - 1] + scores[scores.length / 2]) / 2
      : scores[Math.floor(scores.length / 2)]
    
    const variance = scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / scores.length
    const stdDev = Math.sqrt(variance)
    
    return {
      mean,
      median,
      stdDev,
      min: scores[0],
      max: scores[scores.length - 1]
    }
  }, [files])

  if (!showChart || files.length === 0) {
    return (
      <div className="chart-placeholder">
        <div className="placeholder-message">
          {files.length === 0 ? '분석할 데이터가 없습니다.' : '차트가 비활성화되었습니다.'}
        </div>
      </div>
    )
  }

  return (
    <div className="importance-distribution-chart">
      <div className="chart-header">
        <h3>◈ 중요도 분포 분석</h3>
        <p className="chart-description">
          파일 중요도 점수의 분포와 통계를 시각화합니다.
        </p>
      </div>

      {/* 통계 요약 */}
      <div className="statistics-summary">
        <div className="stat-item">
          <div className="stat-value">{statistics.mean.toFixed(3)}</div>
          <div className="stat-label">평균</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{statistics.median.toFixed(3)}</div>
          <div className="stat-label">중간값</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{statistics.stdDev.toFixed(3)}</div>
          <div className="stat-label">표준편차</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{statistics.min.toFixed(3)}</div>
          <div className="stat-label">최소값</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{statistics.max.toFixed(3)}</div>
          <div className="stat-label">최대값</div>
        </div>
      </div>

      {/* 히스토그램 (CSS로 구현) */}
      <div className="histogram-container">
        <h4>▲ 점수 분포 히스토그램</h4>
        <div className="histogram">
          {histogramData.map((bin, index) => (
            <div key={index} className="histogram-bar-container">
              <div 
                className="histogram-bar"
                style={{ 
                  height: `${(bin.count / Math.max(...histogramData.map(b => b.count))) * 100}%` 
                }}
                title={`${bin.range}: ${bin.count}개 파일`}
              >
                <div className="bar-count">{bin.count}</div>
              </div>
              <div className="bar-label">{bin.range}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 카테고리별 분포 (도넛 차트 스타일) */}
      <div className="category-distribution">
        <h4>◎ 카테고리별 분포</h4>
        <div className="donut-chart">
          <div className="donut-center">
            <div className="total-files">{files.length}</div>
            <div className="total-label">총 파일</div>
          </div>
          <div className="donut-segments">
            {categoryDistribution.map((item, index) => {
              const colors = {
                critical: 'var(--primary-700)',
                important: 'var(--primary-600)', 
                moderate: 'var(--primary-500)',
                low: 'var(--gray-500)'
              }
              
              return (
                <div
                  key={item.category}
                  className="donut-segment"
                  style={{
                    '--segment-color': colors[item.category as keyof typeof colors],
                    '--segment-percentage': `${item.percentage}%`
                  } as React.CSSProperties}
                >
                  <div className="segment-info">
                    <div className="segment-label">{item.category}</div>
                    <div className="segment-value">
                      {item.count}개 ({item.percentage.toFixed(1)}%)
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 상위 파일 목록 */}
      <div className="top-files">
        <h4>▲ 상위 중요도 파일</h4>
        <div className="top-files-list">
          {files
            .sort((a, b) => b.importance_score - a.importance_score)
            .slice(0, 5)
            .map((file, index) => (
              <div key={file.file_path} className="top-file-item">
                <div className="file-rank">#{index + 1}</div>
                <div className="file-info">
                  <div className="file-name">{file.file_path}</div>
                  <div className="file-score">{file.importance_score.toFixed(3)}</div>
                </div>
                <div className={`file-category ${file.category}`}>
                  {file.category}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* 분포 인사이트 */}
      <div className="distribution-insights">
        <h4>◇ 분포 인사이트</h4>
        <div className="insights-list">
          {statistics.stdDev > 0.2 && (
            <div className="insight-item">
              <span className="insight-icon">◈</span>
              <span className="insight-text">
                표준편차가 {statistics.stdDev.toFixed(3)}로 높아 파일 간 중요도 편차가 큽니다.
              </span>
            </div>
          )}
          {categoryDistribution.find(c => c.category === 'critical')?.percentage! > 30 && (
            <div className="insight-item">
              <span className="insight-icon">▲</span>
              <span className="insight-text">
                Critical 파일이 {categoryDistribution.find(c => c.category === 'critical')?.percentage.toFixed(1)}%로 높아 
                위험 분산을 고려해보세요.
              </span>
            </div>
          )}
          {statistics.mean > 0.7 && (
            <div className="insight-item">
              <span className="insight-icon">◯</span>
              <span className="insight-text">
                전체 평균 중요도가 {statistics.mean.toFixed(3)}로 높아 잘 관리되는 프로젝트입니다.
              </span>
            </div>
          )}
          {files.length > 50 && categoryDistribution.find(c => c.category === 'low')?.percentage! < 20 && (
            <div className="insight-item">
              <span className="insight-icon">◎</span>
              <span className="insight-text">
                대부분의 파일이 중요한 역할을 하고 있어 집중적인 관리가 필요합니다.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ImportanceDistributionChart