import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Zap, 
  Key, 
  Settings, 
  HardDrive, 
  AlertTriangle, 
  CheckCircle,
  Github,
  Sparkles
} from 'lucide-react'
import { ApiKeySetup } from '../components/ApiKeySetup'
import { QuickAccessSection } from '../components/QuickAccessSection'
import { usePageInitialization } from '../hooks/usePageInitialization'
import './HomePage.css'

export const HomePage: React.FC = () => {
  const navigate = useNavigate()
  
  // 모든 초기화 로직을 Hook으로 위임
  const {
    config,
    providers,
    selectedAI,
    setSelectedAI,
    isLoading,
    error,
    isUsingLocalData,
    hasStoredKeys,
    createApiHeaders
  } = usePageInitialization()
  
  // 컴포넌트 상태 (최소화)
  const [repoUrl, setRepoUrl] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showApiKeySetup, setShowApiKeySetup] = useState(false)
  
  // API 키 설정 모달 표시 여부 결정
  const shouldShowApiKeySetup = showApiKeySetup || (config.keys_required && !hasStoredKeys())
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl.trim() || !selectedAI) return

    setIsAnalyzing(true)
    
    try {
      // GitHub URL 유효성 검사
      const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+/
      if (!urlPattern.test(repoUrl)) {
        alert('올바른 GitHub 저장소 URL을 입력해주세요.')
        return
      }

      // 저장소 분석 요청 (임시로 간단한 분석 사용)
      const apiHeaders = createApiHeaders(true)
      console.log('[HOMEPAGE] 분석 요청 헤더:', JSON.stringify(apiHeaders, null, 2))
      console.log('[HOMEPAGE] localStorage 키 확인:', {
        githubToken: localStorage.getItem('techgiterview_github_token') ? '설정됨' : '없음',
        googleApiKey: localStorage.getItem('techgiterview_google_api_key') ? '설정됨' : '없음'
      })
      
      const response = await fetch('/api/v1/repository/analyze-simple', {
        method: 'POST',
        headers: apiHeaders,
        body: JSON.stringify({
          repo_url: repoUrl
        })
      })
      
      console.log('[HOMEPAGE] 응답 상태:', response.status, response.statusText)

      if (!response.ok) {
        // 403 에러 처리 (API 키 필요)
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || 'GitHub API 접근이 제한되었습니다. API 키 설정이 필요합니다.')
        }
        throw new Error('저장소 분석에 실패했습니다.')
      }

      const result = await response.json()
      
      // 응답 구조에 따라 분기 처리
      let analysisData = result
      if (result.data) {
        analysisData = result.data
      }
      
      if (result.success || analysisData.success) {
        if (analysisData.analysis_id) {
          navigate(`/dashboard/${analysisData.analysis_id}`)
        } else {
          throw new Error('분석 ID를 받지 못했습니다.')
        }
      } else {
        throw new Error(analysisData.error || result.error || '분석에 실패했습니다.')
      }
      
    } catch (error) {
      console.error('Analysis error:', error)
      const errorMessage = error instanceof Error ? error.message : '오류가 발생했습니다.'
      
      // 403 에러 시 API 키 설정 모달 자동 열기
      if (errorMessage.includes('API 키') || errorMessage.includes('접근이 제한')) {
        setShowApiKeySetup(true)
        alert(errorMessage + '\n\nAPI 키 설정 창을 열어드립니다.')
      } else {
        alert(errorMessage)
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleApiKeysSet = () => {
    setShowApiKeySetup(false)
    // React Query가 자동으로 데이터를 refetch함
  }

  const sampleRepos = [
    'https://github.com/facebook/react',
    'https://github.com/microsoft/vscode',
    'https://github.com/nodejs/node',
    'https://github.com/django/django',
    'https://github.com/hong-seongmin/HWnow'
  ]

  return (
    <div className="home-page">
      <section className="section">
        <div className="container">
          <h1 className="heading-1 text-center">
            <Zap className="title-icon" aria-hidden="true" />
            TechGiterview
          </h1>
          <p className="text-subtitle text-center">
            GitHub 저장소를 분석하여 맞춤형 기술면접을 준비하세요
          </p>
          <p className="text-lead text-center">
            AI가 당신의 코드를 분석하고 실제 면접에서 나올 수 있는 질문들을 생성합니다.
            실시간 모의면접으로 완벽한 준비를 해보세요.
          </p>
        </div>

        <div className="container">
          {/* API 키 설정 버튼 */}
          <div className="card">
            <div className="card-body flex justify-between items-center">
              <h3 className="heading-4 flex items-center gap-sm">
                <Key className="icon" />
                API 키 설정
              </h3>
              <button 
                className="btn btn-outline btn-sm hover-scale-sm active-scale-sm focus-ring"
                onClick={() => setShowApiKeySetup(true)}
                type="button"
              >
                <Settings className="icon" />
                API 키 설정
              </button>
            </div>
            
            {/* 상태 표시 */}
            <div className="status-indicators">
              {isUsingLocalData && (
                <div className="status-badge local">
                  <HardDrive className="icon" />
                  로컬 데이터 사용 중
                </div>
              )}
              {error && (
                <div className="status-badge error">
                  <AlertTriangle className="icon" />
                  서버 연결 오류 (오프라인 모드)
                </div>
              )}
              {!isLoading && !error && !isUsingLocalData && (
                <div className="status-badge online">
                  <CheckCircle className="icon" />
                  서버 연결됨
                </div>
              )}
            </div>
          </div>

          {/* AI 모델 선택 및 분석 시작 통합 섹션 */}
          <div className="card">
            <div className="card-body">
              <h3 className="heading-4 flex items-center gap-sm">
                AI 모델 선택 및 분석 시작
              </h3>
              
              {/* AI 모델 선택 */}
              {providers.length > 0 ? (
                <div className="grid grid-auto-fit gap-md" style={{marginBottom: '1.5rem'}}>
                  {providers.map((provider) => (
                    <label
                      key={provider.id}
                      className={`card hover-lift-sm cursor-pointer transition-fast ${selectedAI === provider.id ? 'border-primary-500 bg-primary-50' : ''} ${provider.recommended ? 'border-brand-green-300' : ''}`}
                    >
                      <input
                        type="radio"
                        name="aiProvider"
                        value={provider.id}
                        checked={selectedAI === provider.id}
                        onChange={(e) => setSelectedAI(e.target.value)}
                        className="form-radio sr-only"
                      />
                      <div className="card-body">
                        <div className="heading-4 flex items-center justify-between">
                          {provider.name}
                          {provider.recommended && <span className="badge badge-success">추천</span>}
                        </div>
                        <div className="text-body-sm text-muted">{provider.model}</div>
                        <div className={`text-body-sm ${provider.status === 'ready' ? 'text-success' : 'text-muted'}`}>
                          {provider.status === 'ready' ? '● 사용 가능' : '○ 설정됨'}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="no-providers" style={{marginBottom: '1.5rem'}}>
                  {isLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                      <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                      <span>AI 모델을 불러오는 중...</span>
                    </div>
                  ) : (
                    '사용 가능한 AI 모델이 없습니다.'
                  )}
                </div>
              )}
              
              {/* 분석 시작 폼 */}
              <form onSubmit={handleSubmit} className="input-form" role="form" aria-label="저장소 분석 요청">
                <div className="url-input-group">
                  <label htmlFor="repo-url-input" className="sr-only">
                    GitHub 저장소 URL
                  </label>
                  <input
                    id="repo-url-input"
                    type="url"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="GitHub 저장소 URL을 입력하세요 (예: https://github.com/facebook/react)"
                    className="form-input form-input-lg focus-ring transition-fast"
                    required
                    disabled={isAnalyzing}
                    aria-describedby="url-help"
                  />
                  <div id="url-help" className="sr-only">
                    분석하고 싶은 GitHub 저장소의 전체 URL을 입력해주세요. 예: https://github.com/facebook/react
                  </div>
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-xl hover-lift active-scale focus-ring"
                    disabled={isAnalyzing || !repoUrl.trim() || !selectedAI}
                    aria-label={isAnalyzing ? "저장소 분석 중..." : "저장소 분석 시작"}
                  >
                    {isAnalyzing ? (
                      <>
                        <span className="spinner"></span>
                        분석 중...
                      </>
                    ) : (
                      '분석 시작'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div className="card">
            <div className="card-body text-center">
              <p className="text-body">
              샘플 저장소로 체험해보기:
            </p>
              <div className="flex flex-wrap justify-center gap-sm">
              {sampleRepos.map((repo, index) => (
                <button
                  key={index}
                  onClick={() => setRepoUrl(repo)}
                  className="btn btn-ghost btn-sm hover-scale-sm active-scale-sm focus-ring"
                  disabled={isAnalyzing}
                >
                  {repo.split('/').slice(-2).join('/')}
                </button>
              ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 최근 활동 섹션 */}
      <section className="section bg-gray-50">
        <div className="container">
          <QuickAccessSection />
        </div>
      </section>

      {/* 기능 섹션 */}
      <section className="section">
        <div className="container">
          <h2 className="heading-2 text-center">주요 기능</h2>
          <div className="grid grid-auto-fit gap-lg">
          <div className="card hover-lift-sm animate-fade-in text-center">
            <div className="card-body">
              <div className="text-5xl mb-4">
                CHART
              </div>
              <h3 className="heading-3">저장소 분석</h3>
              <p className="text-body">GitHub 저장소의 코드 구조, 기술 스택, 복잡도를 자동으로 분석합니다.</p>
            </div>
          </div>
          
          <div className="card hover-lift-sm animate-fade-in text-center">
            <div className="card-body">
              <div className="text-5xl mb-4">
                AI
              </div>
              <h3 className="heading-3">AI 질문 생성</h3>
              <p className="text-body">분석 결과를 바탕으로 맞춤형 기술면접 질문을 자동으로 생성합니다.</p>
            </div>
          </div>
          
          <div className="card hover-lift-sm animate-fade-in text-center">
            <div className="card-body">
              <div className="text-5xl mb-4">
                CHAT
              </div>
              <h3 className="heading-3">실시간 모의면접</h3>
              <p className="text-body">WebSocket 기반으로 실제 면접과 같은 환경에서 연습할 수 있습니다.</p>
            </div>
          </div>
          
          <div className="card hover-lift-sm animate-fade-in text-center">
            <div className="card-body">
              <div className="text-5xl mb-4">
                CHART
              </div>
              <h3 className="heading-3">상세 리포트</h3>
              <p className="text-body">답변에 대한 AI 평가와 개선 제안을 통해 실력을 향상시킬 수 있습니다.</p>
            </div>
          </div>
          </div>
        </div>
      </section>

      {/* 작동 원리 */}
      <section className="section">
        <div className="container">
          <h2 className="heading-2 text-center">작동 원리</h2>
          <div className="flex justify-center items-center gap-lg flex-wrap">
          <div className="card hover-scale-sm animate-fade-in-up text-center position-relative">
            <div className="card-body">
              <div className="badge badge-primary text-lg mb-4">1</div>
              <h3 className="heading-4">저장소 입력</h3>
              <p className="text-body-sm">GitHub 저장소 URL을 입력하면 자동으로 코드를 분석합니다.</p>
            </div>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="card hover-scale-sm animate-fade-in-up text-center position-relative">
            <div className="card-body">
              <div className="badge badge-primary text-lg mb-4">2</div>
              <h3 className="heading-4">AI 분석</h3>
              <p className="text-body-sm">기술 스택, 코드 품질, 복잡도를 종합적으로 평가합니다.</p>
            </div>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="card hover-scale-sm animate-fade-in-up text-center position-relative">
            <div className="card-body">
              <div className="badge badge-primary text-lg mb-4">3</div>
              <h3 className="heading-4">질문 생성</h3>
              <p className="text-body-sm">분석 결과를 바탕으로 맞춤형 면접 질문을 생성합니다.</p>
            </div>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="card hover-scale-sm animate-fade-in-up text-center position-relative">
            <div className="card-body">
              <div className="badge badge-primary text-lg mb-4">4</div>
              <h3 className="heading-4">모의면접</h3>
              <p className="text-body-sm">실시간으로 질문에 답하고 즉시 피드백을 받습니다.</p>
            </div>
          </div>
          </div>
        </div>
      </section>

      {/* API 키 설정 모달 */}
      {shouldShowApiKeySetup && (
        <ApiKeySetup onApiKeysSet={handleApiKeysSet} />
      )}
      
      {/* 푸터 */}
      <footer className="homepage-footer">
        <div className="footer-container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>
                <Zap className="icon" />
                TechGiterview
              </h3>
              <p>GitHub 기반 AI 기술면접 준비 플랫폼</p>
            </div>
            
            <div className="footer-section">
              <h4>링크</h4>
              <div className="footer-links">
                <a
                  href="https://github.com/hong-seongmin/techGiterview"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer-link"
                >
                  GitHub Repository
                </a>
                <a
                  href="https://buymeacoffee.com/oursophy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer-link"
                >
                  Buy Me a Coffee
                </a>
              </div>
            </div>
            
            <div className="footer-section">
              <h4>연락처</h4>
              <ul>
                <li>EMAIL hong112424@naver.com</li>

              </ul>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; 2025 TechGiterview. All rights reserved.</p>

          </div>
        </div>
      </footer>
    </div>
  )
}