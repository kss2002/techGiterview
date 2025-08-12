/**
 * 고도화된 분석 대시보드 컴포넌트
 * 
 * 리포지토리 메타정보, 의존성 그래프, 변경 이력, 복잡도를 종합적으로 표시하는 대시보드
 */

import React, { useState, useEffect } from 'react'
import './AnalysisDashboard.css'
import { SmartFileImportanceSection } from './SmartFileImportanceSection'
import { useChartStyles, useDynamicStyles } from '../hooks/useStyles'

// 인터페이스 정의
interface RepositoryOverview {
  name: string
  description: string
  language: string
  size: number
  stars: number
  forks: number
}

interface ComplexityAnalysis {
  distribution: { low: number; medium: number; high: number }
  average_complexity: number
  max_complexity: number
  maintainability_average: number
}

interface QualityRiskAnalysis {
  distribution: { low: number; medium: number; high: number }
  high_risk_files: Array<{
    filename: string
    risk_score: number
    complexity: number
    hotspot_score: number
  }>
}

interface DependencyAnalysis {
  graph_metrics: {
    total_nodes: number
    total_edges: number
    density: number
    clustering_coefficient: number
    strongly_connected_components: number
    critical_paths_count: number
  }
  top_central_files: Array<{
    filename: string
    centrality_score: number
    fan_in: number
    fan_out: number
    importance_score: number
  }>
  module_clusters: Array<{
    cluster_id: number
    files: string[]
    size: number
  }>
  critical_paths: Array<{
    path_id: number
    files: string[]
    length: number
  }>
}

interface ChurnAnalysis {
  hotspots: Array<{
    filename: string
    hotspot_score: number
    complexity: number
    recent_commits: number
    quality_risk: number
  }>
  author_statistics: Record<string, { commits: number; files_changed: number }>
  most_changed_files: Array<{
    filename: string
    commit_count: number
    recent_commits: number
    authors_count: number
  }>
}

interface LanguageStatistics {
  [language: string]: {
    file_count: number
    total_loc: number
    avg_complexity: number
  }
}

interface FileTypeDistribution {
  [fileType: string]: number
}

interface CriticalFile {
  path: string
  importance_score: number
  quality_risk_score: number
  complexity: number
  hotspot_score: number
  file_type: string
  language: string
  metrics_summary: {
    lines_of_code: number
    fan_in: number
    fan_out: number
    commit_frequency: number
    recent_commits: number
    authors_count: number
    centrality_score: number
  }
}

interface AnalysisDashboardData {
  repository_overview: RepositoryOverview
  complexity_analysis: ComplexityAnalysis
  quality_risk_analysis: QualityRiskAnalysis
  dependency_analysis: DependencyAnalysis
  churn_analysis: ChurnAnalysis
  language_statistics: LanguageStatistics
  file_type_distribution: FileTypeDistribution
}

// 고도화된 분석 결과 인터페이스 추가
interface AdvancedAnalysisData {
  file_metrics: Record<string, {
    path: string
    cyclomatic_complexity: number
    cognitive_complexity: number
    maintainability_index: number
    fan_in: number
    fan_out: number
    centrality_score: number
    commit_frequency: number
    recent_commits: number
    hotspot_score: number
    importance_score: number
    quality_risk_score: number
    file_type: string
    language: string
  }>
  dependency_graph: {
    nodes: string[]
    edges: [string, string][]
    node_count: number
    edge_count: number
    import_relationships: Record<string, string[]>
    module_clusters: string[][]
    critical_paths: string[][]
  }
  churn_analysis: {
    file_churns: Record<string, {
      commit_count: number
      recent_commits: number
      authors_count: number
      total_changes: number
      average_commit_size: number
    }>
    hotspots: Array<{
      filename: string
      commit_count: number
      recent_commits: number
      authors_count: number
      hotspot_score: number
    }>
    author_statistics: Record<string, {
      commits: number
      files_changed: number
    }>
  }
  analysis_summary: {
    total_files: number
    analyzed_files: number
    high_risk_files: number
    hotspot_files: number
  }
}

// 스마트 파일 중요도 분석 인터페이스 추가
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

interface ImprovementSuggestion {
  type: 'complexity' | 'churn' | 'dependency' | 'structure'
  message: string
  affected_files: number
  priority: 'high' | 'medium' | 'low'
}

interface AnalysisDashboardProps {
  dashboardData: AnalysisDashboardData
  criticalFiles: CriticalFile[]
  advancedAnalysis?: AdvancedAnalysisData  // 고도화된 분석 결과 추가
  smartFileAnalysis?: {  // 스마트 파일 중요도 분석 결과 추가
    files: SmartFileAnalysis[]
    distribution: FileImportanceDistribution
    suggestions: ImprovementSuggestion[]
  }
  onFileSelect?: (file: CriticalFile) => void
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  dashboardData,
  criticalFiles,
  advancedAnalysis,
  smartFileAnalysis,
  onFileSelect
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'complexity' | 'dependency' | 'churn' | 'files' | 'advanced'>('overview')
  const [selectedMetric, setSelectedMetric] = useState<'importance' | 'complexity' | 'risk'>('importance')
  
  // 스타일링 Hook들 추가
  const chartStyles = useChartStyles()
  const dynamicStyles = useDynamicStyles()

  // 탭 네비게이션 로직 (고도화된 분석 탭 추가)
  const availableTabs = ['overview', 'complexity', 'dependency', 'churn', 'files', 'advanced'] as const
  const availableMetrics = ['importance', 'complexity', 'risk'] as const

  // 데이터 변환 함수들 (테스트에서 검증된 로직)
  const transformToPieChartData = (langStats: LanguageStatistics) => {
    const colors = ['var(--primary-600)', 'var(--primary-500)', 'var(--primary-700)', 'var(--primary-400)', 'var(--primary-800)']
    return Object.entries(langStats).map(([lang, stats], index) => ({
      name: lang,
      value: stats.file_count,
      fill: colors[index % colors.length]
    }))
  }

  const transformToBarChartData = (distribution: { low: number; medium: number; high: number }) => {
    return [
      { name: 'low', value: distribution.low },
      { name: 'medium', value: distribution.medium },
      { name: 'high', value: distribution.high }
    ]
  }

  // 성능 지표 계산 (테스트에서 검증된 로직)
  const calculatePerformanceIndicators = () => {
    const complexityAvg = dashboardData.complexity_analysis.average_complexity
    const highRiskCount = dashboardData.quality_risk_analysis.high_risk_files.length
    const maintainability = dashboardData.complexity_analysis.maintainability_average

    const complexityHealth = complexityAvg < 5 ? 'good' : complexityAvg < 8 ? 'warning' : 'critical'
    const riskHealth = highRiskCount < 5 ? 'good' : highRiskCount < 10 ? 'warning' : 'critical'

    return {
      complexity_health: complexityHealth,
      risk_health: riskHealth,
      maintainability,
      critical_files_count: criticalFiles.length
    }
  }

  // 파일 선택 콜백 (테스트에서 검증된 로직)
  const handleFileSelect = (file: CriticalFile) => {
    if (onFileSelect) {
      onFileSelect(file)
    }
  }

  // 데이터 필터링 로직 (테스트에서 검증된 로직)
  const filterHighComplexityHotspots = () => {
    return dashboardData.churn_analysis.hotspots.filter(h => h.complexity > 7)
  }

  const filterRecentHotspots = () => {
    return dashboardData.churn_analysis.hotspots.filter(h => h.recent_commits > 2)
  }

  // 색상 할당 로직 (테스트에서 검증된 로직)
  const getColorForItem = (index: number) => {
    const colors = ['var(--primary-600)', 'var(--primary-500)', 'var(--primary-700)', 'var(--primary-400)', 'var(--primary-800)']
    return colors[index % colors.length]
  }

  // 반응형 레이아웃 로직 (테스트에서 검증된 로직)
  const getGridColumns = (screenWidth: number) => {
    if (screenWidth < 768) return 1      // Mobile
    if (screenWidth < 1024) return 2     // Tablet
    return 3                             // Desktop
  }

  const indicators = calculatePerformanceIndicators()
  const pieChartData = transformToPieChartData(dashboardData.language_statistics)
  const barChartData = transformToBarChartData(dashboardData.complexity_analysis.distribution)

  return (
    <div className="analysis-dashboard">
      {/* 헤더 */}
      <div className="dashboard-header">
        <h2>
          📊
          고도화된 분석 대시보드
        </h2>
        <div className="performance-indicators">
          <div className={`indicator ${indicators.complexity_health}`}>
            <span className="indicator-label">복잡도</span>
            <span className="indicator-value">{indicators.complexity_health}</span>
          </div>
          <div className={`indicator ${indicators.risk_health}`}>
            <span className="indicator-label">위험도</span>
            <span className="indicator-value">{indicators.risk_health}</span>
          </div>
          <div className="indicator good">
            <span className="indicator-label">유지보수성</span>
            <span className="indicator-value">{indicators.maintainability.toFixed(1)}</span>
          </div>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        {availableTabs.map(tab => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* 탭 컨텐츠 */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {/* 저장소 개요 */}
            <div className="overview-section">
              <h3>저장소 개요</h3>
              <div className="repo-stats">
                <div className="stat-card">
                  <div className="stat-icon">
                    ⭐
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{dashboardData.repository_overview.stars.toLocaleString()}</div>
                    <div className="stat-label">Stars</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">
                    🌳
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{dashboardData.repository_overview.forks.toLocaleString()}</div>
                    <div className="stat-label">Forks</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">
                    💾
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{(dashboardData.repository_overview.size / 1024).toFixed(1)}MB</div>
                    <div className="stat-label">Size</div>
                  </div>
                </div>
              </div>
            </div>

            {/* 언어별 통계 */}
            <div className="language-section">
              <h3>언어별 분포</h3>
              <div className="language-chart">
                {pieChartData.map((entry, index) => (
                  <div key={entry.name} className="language-item">
                    <div 
                      className={`${chartStyles.languageColor} ${chartStyles.getLanguageColorClass(entry.name)}`}
                      style={dynamicStyles.createBackgroundColorStyle(entry.fill)}
                    ></div>
                    <span className="language-name">{entry.name}</span>
                    <span className="language-count">{entry.value} files</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 파일 타입 분포 */}
            <div className="file-type-section">
              <h3>파일 타입 분포</h3>
              <div className="file-type-grid">
                {Object.entries(dashboardData.file_type_distribution).map(([type, count]) => (
                  <div key={type} className="file-type-card">
                    <div className="file-type-icon">
                      📄
                    </div>
                    <div className="file-type-name">{type}</div>
                    <div className="file-type-count">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'complexity' && (
          <div className="complexity-tab">
            {/* 복잡도 분포 차트 */}
            <div className="complexity-distribution">
              <h3>복잡도 분포</h3>
              <div className="complexity-chart">
                {barChartData.map((entry, index) => (
                  <div key={entry.name} className="complexity-bar">
                    <div className="bar-label">{entry.name}</div>
                    <div 
                      className={`bar-fill ${chartStyles.getChartColorClass(index)}`}
                      style={dynamicStyles.createProgressBarStyle((entry.value / Math.max(...barChartData.map(d => d.value))) * 100)}
                    >
                      <span className={chartStyles.metricValue}>{entry.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 복잡도 통계 */}
            <div className="complexity-stats">
              <h3>복잡도 통계</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-label">평균 복잡도</div>
                  <div className="stat-value">{dashboardData.complexity_analysis.average_complexity.toFixed(2)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">최대 복잡도</div>
                  <div className="stat-value">{dashboardData.complexity_analysis.max_complexity.toFixed(2)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">유지보수성 지수</div>
                  <div className="stat-value">{dashboardData.complexity_analysis.maintainability_average.toFixed(1)}</div>
                </div>
              </div>
            </div>

            {/* 위험도 높은 파일 */}
            <div className="high-risk-files">
              <h3>고위험 파일</h3>
              <div className="risk-files-list">
                {dashboardData.quality_risk_analysis.high_risk_files.map((file, index) => (
                  <div key={index} className="risk-file-item">
                    <div className="file-info">
                      <div className="file-name">{file.filename}</div>
                      <div className="file-metrics">
                        <span className="risk-score">위험도: {file.risk_score.toFixed(1)}</span>
                        <span className="complexity">복잡도: {file.complexity.toFixed(1)}</span>
                        <span className="hotspot">핫스팟: {file.hotspot_score.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className={`risk-level ${file.risk_score > 8 ? 'critical' : 'high'}`}>
                      {file.risk_score > 8 ? 'CRITICAL' : 'HIGH'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'dependency' && (
          <div className="dependency-tab">
            {/* 의존성 그래프 메트릭 */}
            <div className="graph-metrics">
              <h3>의존성 네트워크 메트릭</h3>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">총 노드 수</div>
                  <div className="metric-value">{dashboardData.dependency_analysis.graph_metrics.total_nodes}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">총 엣지 수</div>
                  <div className="metric-value">{dashboardData.dependency_analysis.graph_metrics.total_edges}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">네트워크 밀도</div>
                  <div className="metric-value">{dashboardData.dependency_analysis.graph_metrics.density.toFixed(3)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">클러스터링 계수</div>
                  <div className="metric-value">{dashboardData.dependency_analysis.graph_metrics.clustering_coefficient.toFixed(3)}</div>
                </div>
              </div>
            </div>

            {/* 중심성 높은 파일 */}
            <div className="central-files">
              <h3>중심성 높은 파일</h3>
              <div className="central-files-list">
                {dashboardData.dependency_analysis.top_central_files.map((file, index) => (
                  <div key={index} className="central-file-item">
                    <div className="file-info">
                      <div className="file-name">{file.filename}</div>
                      <div className="centrality-metrics">
                        <span className="centrality">중심성: {file.centrality_score.toFixed(3)}</span>
                        <span className="fan-in">Fan-in: {file.fan_in}</span>
                        <span className="fan-out">Fan-out: {file.fan_out}</span>
                      </div>
                    </div>
                    <div className="importance-score">
                      중요도: {file.importance_score.toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 모듈 클러스터 */}
            <div className="module-clusters">
              <h3>모듈 클러스터</h3>
              <div className="clusters-grid">
                {dashboardData.dependency_analysis.module_clusters.map((cluster, index) => (
                  <div key={cluster.cluster_id} className="cluster-card">
                    <div className="cluster-header">
                      <span className="cluster-id">클러스터 {cluster.cluster_id}</span>
                      <span className="cluster-size">{cluster.size} files</span>
                    </div>
                    <div className="cluster-files">
                      {cluster.files.map((file, fileIndex) => (
                        <div key={fileIndex} className="cluster-file">{file}</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'churn' && (
          <div className="churn-tab">
            {/* 핫스팟 분석 */}
            <div className="hotspots-section">
              <h3>코드 핫스팟</h3>
              <div className="hotspots-list">
                {dashboardData.churn_analysis.hotspots.map((hotspot, index) => (
                  <div key={index} className="hotspot-item">
                    <div className="hotspot-info">
                      <div className="hotspot-name">{hotspot.filename}</div>
                      <div className="hotspot-metrics">
                        <span className="hotspot-score">핫스팟: {hotspot.hotspot_score.toFixed(1)}</span>
                        <span className="complexity">복잡도: {hotspot.complexity.toFixed(1)}</span>
                        <span className="recent-commits">최근 커밋: {hotspot.recent_commits}</span>
                      </div>
                    </div>
                    <div className={`hotspot-level ${hotspot.hotspot_score > 20 ? 'high' : 'medium'}`}>
                      {hotspot.hotspot_score > 20 ? 'HIGH' : 'MEDIUM'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 개발자 기여도 */}
            <div className="author-stats">
              <h3>개발자 기여도</h3>
              <div className="authors-list">
                {Object.entries(dashboardData.churn_analysis.author_statistics).map(([author, stats]) => (
                  <div key={author} className="author-item">
                    <div className="author-name">{author}</div>
                    <div className="author-metrics">
                      <span className="commits">커밋: {stats.commits}</span>
                      <span className="files">파일: {stats.files_changed}</span>
                      <span className="ratio">비율: {(stats.files_changed / stats.commits).toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 가장 많이 변경된 파일 */}
            <div className="most-changed-files">
              <h3>가장 많이 변경된 파일</h3>
              <div className="changed-files-list">
                {dashboardData.churn_analysis.most_changed_files.map((file, index) => (
                  <div key={index} className="changed-file-item">
                    <div className="file-name">{file.filename}</div>
                    <div className="change-metrics">
                      <span className="total-commits">총 커밋: {file.commit_count}</span>
                      <span className="recent-commits">최근 커밋: {file.recent_commits}</span>
                      <span className="authors">개발자: {file.authors_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'files' && smartFileAnalysis && (
          <SmartFileImportanceSection
            criticalFiles={smartFileAnalysis.files}
            distribution={smartFileAnalysis.distribution}
            suggestions={smartFileAnalysis.suggestions}
            onFileSelect={(file) => {
              // SmartFileAnalysis를 CriticalFile 형태로 변환
              const criticalFile: CriticalFile = {
                path: file.file_path,
                importance_score: file.importance_score,
                quality_risk_score: file.metrics.churn_risk * 10, // 0-1을 0-10으로 변환
                complexity: file.metrics.complexity_score * 10,
                hotspot_score: file.metrics.churn_risk * 20,
                file_type: file.file_path.split('.').pop() || 'unknown',
                language: file.file_path.split('.').pop() || 'unknown',
                metrics_summary: {
                  lines_of_code: 0, // 실제 데이터 연동 시 제공
                  fan_in: Math.round(file.metrics.dependency_centrality * 10),
                  fan_out: Math.round(file.metrics.dependency_centrality * 5),
                  commit_frequency: Math.round(file.metrics.churn_risk * 50),
                  recent_commits: Math.round(file.metrics.churn_risk * 10),
                  authors_count: Math.round(file.metrics.churn_risk * 5),
                  centrality_score: file.metrics.dependency_centrality
                }
              }
              handleFileSelect(criticalFile)
            }}
          />
        )}

        {activeTab === 'files' && !smartFileAnalysis && (
          <div className="files-tab">
            <div className="no-data-message">
              <h3>스마트 파일 중요도 분석 결과가 없습니다</h3>
              <p>고급 분석을 실행하여 스마트 파일 중요도 데이터를 생성해주세요.</p>
            </div>
          </div>
        )}

        {activeTab === 'advanced' && advancedAnalysis && (
          <div className="advanced-tab">
            {/* 고도화된 분석 개요 */}
            <div className="advanced-overview">
              <h3>
                ⚙️
                고도화된 분석 결과
              </h3>
              <div className="advanced-stats">
                <div className="advanced-stat-card">
                  <div className="stat-icon">
                    📄
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{advancedAnalysis.analysis_summary.total_files}</div>
                    <div className="stat-label">총 분석 파일</div>
                  </div>
                </div>
                <div className="advanced-stat-card">
                  <div className="stat-icon">
                    ⚠️
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{advancedAnalysis.analysis_summary.high_risk_files}</div>
                    <div className="stat-label">고위험 파일</div>
                  </div>
                </div>
                <div className="advanced-stat-card">
                  <div className="stat-icon">
                    🎯
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{advancedAnalysis.analysis_summary.hotspot_files}</div>
                    <div className="stat-label">핫스팟 파일</div>
                  </div>
                </div>
                <div className="advanced-stat-card">
                  <div className="stat-icon">
                    🌐
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{advancedAnalysis.dependency_graph.node_count}</div>
                    <div className="stat-label">의존성 노드</div>
                  </div>
                </div>
              </div>
            </div>

            {/* 파일 메트릭 상세 분석 */}
            <div className="file-metrics-section">
              <h3>▲ 파일별 상세 메트릭</h3>
              <div className="metrics-grid">
                {Object.entries(advancedAnalysis.file_metrics)
                  .sort(([,a], [,b]) => b.importance_score - a.importance_score)
                  .slice(0, 10)
                  .map(([path, metrics]) => (
                    <div key={path} className="file-metric-card">
                      <div className="file-metric-header">
                        <div className="file-path">{path.split('/').pop()}</div>
                        <div className="file-type-badge">{metrics.file_type}</div>
                      </div>
                      <div className="metric-bars">
                        <div className="metric-bar">
                          <span className="metric-name">중요도</span>
                          <div className={chartStyles.progressBar.container}>
                            <div 
                              className={chartStyles.progressBar.importance}
                              style={dynamicStyles.createProgressBarStyle(metrics.importance_score)}
                            ></div>
                            <span className={chartStyles.metricValue}>{metrics.importance_score.toFixed(1)}</span>
                          </div>
                        </div>
                        <div className="metric-bar">
                          <span className="metric-name">복잡도</span>
                          <div className={chartStyles.progressBar.container}>
                            <div 
                              className={chartStyles.progressBar.complexity}
                              style={dynamicStyles.createProgressBarStyle(Math.min(metrics.cyclomatic_complexity * 10, 100))}
                            ></div>
                            <span className={chartStyles.metricValue}>{metrics.cyclomatic_complexity.toFixed(1)}</span>
                          </div>
                        </div>
                        <div className="metric-bar">
                          <span className="metric-name">핫스팟</span>
                          <div className={chartStyles.progressBar.container}>
                            <div 
                              className={chartStyles.progressBar.hotspot}
                              style={dynamicStyles.createProgressBarStyle(Math.min(metrics.hotspot_score * 5, 100))}
                            ></div>
                            <span className={chartStyles.metricValue}>{metrics.hotspot_score.toFixed(1)}</span>
                          </div>
                        </div>
                        <div className="metric-bar">
                          <span className="metric-name">중심성</span>
                          <div className={chartStyles.progressBar.container}>
                            <div 
                              className={chartStyles.progressBar.centrality}
                              style={dynamicStyles.createProgressBarStyle(metrics.centrality_score * 100)}
                            ></div>
                            <span className={chartStyles.metricValue}>{metrics.centrality_score.toFixed(3)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="additional-metrics">
                        <span>Fan-in: {metrics.fan_in}</span>
                        <span>Fan-out: {metrics.fan_out}</span>
                        <span>커밋: {metrics.commit_frequency}</span>
                        <span>최근: {metrics.recent_commits}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* 의존성 그래프 분석 */}
            <div className="dependency-graph-section">
              <h3>
                🗺️
                의존성 그래프 분석
              </h3>
              <div className="graph-overview">
                <div className="graph-metrics">
                  <div className="graph-metric">
                    <div className="metric-label">총 노드</div>
                    <div className="metric-value">{advancedAnalysis.dependency_graph.node_count}</div>
                  </div>
                  <div className="graph-metric">
                    <div className="metric-label">총 엣지</div>
                    <div className="metric-value">{advancedAnalysis.dependency_graph.edge_count}</div>
                  </div>
                  <div className="graph-metric">
                    <div className="metric-label">모듈 클러스터</div>
                    <div className="metric-value">{advancedAnalysis.dependency_graph.module_clusters.length}</div>
                  </div>
                  <div className="graph-metric">
                    <div className="metric-label">중요 경로</div>
                    <div className="metric-value">{advancedAnalysis.dependency_graph.critical_paths.length}</div>
                  </div>
                </div>
              </div>

              {/* 모듈 클러스터 표시 */}
              <div className="module-clusters-advanced">
                <h4>모듈 클러스터</h4>
                <div className="clusters-container">
                  {advancedAnalysis.dependency_graph.module_clusters.map((cluster, index) => (
                    <div key={index} className="cluster-card-advanced">
                      <div className="cluster-header-advanced">
                        <span className="cluster-id">클러스터 {index + 1}</span>
                        <span className="cluster-size">{cluster.length} files</span>
                      </div>
                      <div className="cluster-files-advanced">
                        {cluster.map((file, fileIndex) => (
                          <div key={fileIndex} className="cluster-file-advanced">
                            {file.split('/').pop()}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 중요 경로 표시 */}
              <div className="critical-paths-advanced">
                <h4>중요 의존성 경로</h4>
                <div className="paths-container">
                  {advancedAnalysis.dependency_graph.critical_paths.slice(0, 5).map((path, index) => (
                    <div key={index} className="path-card">
                      <div className="path-header">
                        <span className="path-id">경로 {index + 1}</span>
                        <span className="path-length">{path.length} 단계</span>
                      </div>
                      <div className="path-flow">
                        {path.map((file, stepIndex) => (
                          <React.Fragment key={stepIndex}>
                            <div className="path-node">{file.split('/').pop()}</div>
                            {stepIndex < path.length - 1 && <div className="path-arrow">→</div>}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 변경 이력 핫스팟 분석 */}
            <div className="churn-hotspots-section">
              <h3>
                📈
                변경 이력 핫스팟 분석
              </h3>
              <div className="hotspots-advanced-grid">
                {advancedAnalysis.churn_analysis.hotspots.slice(0, 8).map((hotspot, index) => (
                  <div key={index} className="hotspot-card-advanced">
                    <div className="hotspot-header-advanced">
                      <div className="hotspot-name">{hotspot.filename.split('/').pop()}</div>
                      <div className={`hotspot-level-badge ${hotspot.hotspot_score > 20 ? 'critical' : hotspot.hotspot_score > 10 ? 'high' : 'medium'}`}>
                        {hotspot.hotspot_score > 20 ? 'CRITICAL' : hotspot.hotspot_score > 10 ? 'HIGH' : 'MEDIUM'}
                      </div>
                    </div>
                    <div className="hotspot-metrics-advanced">
                      <div className="hotspot-metric">
                        <span className="metric-icon">
                          🎯
                        </span>
                        <span className="metric-label">핫스팟 점수</span>
                        <span className="metric-value">{hotspot.hotspot_score.toFixed(1)}</span>
                      </div>
                      <div className="hotspot-metric">
                        <span className="metric-icon">
                          🌳
                        </span>
                        <span className="metric-label">총 커밋</span>
                        <span className="metric-value">{hotspot.commit_count}</span>
                      </div>
                      <div className="hotspot-metric">
                        <span className="metric-icon">
                          🕰️
                        </span>
                        <span className="metric-label">최근 커밋</span>
                        <span className="metric-value">{hotspot.recent_commits}</span>
                      </div>
                      <div className="hotspot-metric">
                        <span className="metric-icon">
                          👥
                        </span>
                        <span className="metric-label">개발자 수</span>
                        <span className="metric-value">{hotspot.authors_count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 개발자 기여도 상세 분석 */}
            <div className="author-contribution-section">
              <h3>👥 개발자 기여도 상세 분석</h3>
              <div className="authors-advanced-grid">
                {Object.entries(advancedAnalysis.churn_analysis.author_statistics)
                  .sort(([,a], [,b]) => b.commits - a.commits)
                  .slice(0, 6)
                  .map(([author, stats]) => (
                    <div key={author} className="author-card-advanced">
                      <div className="author-info-advanced">
                        <div className="author-avatar">👤</div>
                        <div className="author-name">{author}</div>
                      </div>
                      <div className="author-metrics-advanced">
                        <div className="author-metric">
                          <span className="metric-label">총 커밋</span>
                          <span className="metric-value">{stats.commits}</span>
                        </div>
                        <div className="author-metric">
                          <span className="metric-label">변경 파일</span>
                          <span className="metric-value">{stats.files_changed}</span>
                        </div>
                        <div className="author-metric">
                          <span className="metric-label">파일/커밋 비율</span>
                          <span className="metric-value">{(stats.files_changed / stats.commits).toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisDashboard