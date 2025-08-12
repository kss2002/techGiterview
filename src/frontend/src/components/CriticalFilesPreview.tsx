/**
 * CriticalFilesPreview 컴포넌트
 * 
 * questions-grid 상단에 표시되는 중요 파일 미리보기 컴포넌트
 * SmartFileImportanceAnalyzer에서 선정된 핵심 파일들을 컴팩트하게 표시
 */

import React from 'react'
import './CriticalFilesPreview.css'
// Font Awesome icons used via CSS classes instead of imports

// SmartFileAnalysis 인터페이스 (AnalysisDashboard.tsx와 동일)
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

interface CriticalFilesPreviewProps {
  criticalFiles: SmartFileAnalysis[]
  onFileClick?: (filePath: string) => void
  maxDisplayFiles?: number
}

// 파일 확장자에 따른 아이콘 반환
const getFileIcon = (filePath: string): React.ReactNode => {
  // filePath가 없는 경우 기본 아이콘 반환
  if (!filePath) {
    return <>📄</>
  }
  
  const extension = filePath.split('.').pop()?.toLowerCase()
  const fileName = filePath.split('/').pop()?.toLowerCase() || ''
  
  // 특수 파일명 처리
  if (fileName === 'dockerfile' || fileName.startsWith('dockerfile')) return <>🐳</>
  if (fileName === '.gitignore') return <>🚫</>
  if (fileName.startsWith('readme')) return <>📖</>
  if (fileName === 'package.json') return <>📦</>
  if (fileName === 'package-lock.json' || fileName === 'yarn.lock') return <>🔒</>
  
  // 확장자별 아이콘 매핑
  switch (extension) {
    // JavaScript/TypeScript
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
      return <>🟨</>
    // Python
    case 'py':
    case 'pyw':
    case 'pyx':
      return <>🐍</>
    // Java/Kotlin
    case 'java':
    case 'kt':
    case 'scala':
      return <>☕</>
    // Web
    case 'html':
    case 'css':
    case 'scss':
    case 'sass':
      return <>🎨</>
    // Config files
    case 'json':
    case 'yaml':
    case 'yml':
    case 'toml':
      return <>⚙️</>
    // Others
    case 'md':
    case 'txt':
      return <>📝</>
    case 'sql':
      return <>🗄️</>
    case 'dockerfile':
      return <>🐳</>
    default:
      return <>📄</>
  }
}

// 중요도 점수에 따른 색상 반환 - Primary 색상 계열로 통일
const getImportanceColor = (score: number): string => {
  if (score >= 0.9) return 'var(--importance-critical)' // 매우 높음 - Primary 700
  if (score >= 0.8) return 'var(--importance-high)' // 높음 - Primary 600
  if (score >= 0.7) return 'var(--importance-medium)' // 중간높음 - Primary 500
  if (score >= 0.6) return 'var(--importance-low)' // 중간 - Primary 400
  return 'var(--gray-500)' // 낮음 - 회색
}

// 카테고리에 따른 배지 스타일
const getCategoryBadge = (category: string): { text: string; className: string } => {
  switch (category) {
    case 'critical':
      return { text: 'CORE', className: 'badge-critical' }
    case 'important':
      return { text: 'KEY', className: 'badge-important' }
    case 'moderate':
      return { text: 'SUB', className: 'badge-moderate' }
    default:
      return { text: 'LOW', className: 'badge-low' }
  }
}

export const CriticalFilesPreview: React.FC<CriticalFilesPreviewProps> = ({
  criticalFiles,
  onFileClick,
  maxDisplayFiles = 12
}) => {
  // criticalFiles가 없거나 빈 배열인 경우 처리
  if (!criticalFiles || criticalFiles.length === 0) {
    return null
  }
  
  // 중요도 순으로 정렬 후 최대 표시 개수만큼 제한
  const displayFiles = criticalFiles
    .filter(file => file && file.file_path) // file_path가 있는 파일만 필터링
    .sort((a, b) => b.importance_score - a.importance_score)
    .slice(0, maxDisplayFiles)

  const handleFileClick = (filePath: string) => {
    if (onFileClick) {
      onFileClick(filePath)
    }
  }

  // 필터링 후 표시할 파일이 없는 경우
  if (displayFiles.length === 0) {
    return null
  }

  return (
    <div className="critical-files-preview-section">
      <div className="preview-header">
        <div className="header-content">
          <h3 className="section-title">
            🎯
            핵심 분석 파일
          </h3>
          <span className="file-count">
            {criticalFiles.length}개 파일 선정
          </span>
        </div>
        <p className="section-description">
          AI가 분석한 프로젝트의 핵심 파일들 - 질문 생성의 기반이 됩니다
        </p>
      </div>
      
      <div className="critical-files-grid">
        {displayFiles.map((file, index) => {
          const badge = getCategoryBadge(file.category)
          const importanceColor = getImportanceColor(file.importance_score)
          
          return (
            <div 
              key={file.file_path || `file-${index}`}
              className="critical-file-item"
              onClick={() => handleFileClick(file.file_path || '')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleFileClick(file.file_path || '')
                }
              }}
            >
              <div className="file-header">
                <div className="file-meta">
                  <span className="file-icon">{getFileIcon(file.file_path || '')}</span>
                  <span className="file-rank">#{index + 1}</span>
                  <span className={`category-badge ${badge.className}`}>
                    {badge.text}
                  </span>
                </div>
                <div 
                  className="importance-score"
                  style={{ color: importanceColor }}
                >
                  {(file.importance_score * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="file-path-container">
                <div className="file-path" title={file.file_path || 'Unknown file'}>
                  {file.file_path || 'Unknown file'}
                </div>
              </div>
              
              
              <div className="metrics-bar">
                <div className="metric-item">
                  <span className="metric-label">구조</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill structural"
                      style={{ width: `${file.metrics.structural_importance * 100}%` }}
                    />
                  </div>
                </div>
                <div className="metric-item">
                  <span className="metric-label">의존성</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill dependency"
                      style={{ width: `${file.metrics.dependency_centrality * 100}%` }}
                    />
                  </div>
                </div>
                <div className="metric-item">
                  <span className="metric-label">변경</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill churn"
                      style={{ width: `${file.metrics.churn_risk * 100}%` }}
                    />
                  </div>
                </div>
                <div className="metric-item">
                  <span className="metric-label">복잡도</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill complexity"
                      style={{ width: `${file.metrics.complexity_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
      
    </div>
  )
}