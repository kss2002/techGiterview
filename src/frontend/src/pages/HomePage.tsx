import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiKeySetup } from '../components/ApiKeySetup'
import './HomePage.css'

// 로컬스토리지에서 API 키를 가져오는 헬퍼 함수
const getApiKeysFromStorage = () => {
  try {
    return {
      githubToken: localStorage.getItem('techgiterview_github_token') || '',
      googleApiKey: localStorage.getItem('techgiterview_google_api_key') || ''
    }
  } catch (error) {
    return { githubToken: '', googleApiKey: '' }
  }
}

// API 요청용 헤더 생성 함수
const createApiHeaders = (includeApiKeys: boolean = false) => {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  }
  
  if (includeApiKeys) {
    const { githubToken, googleApiKey } = getApiKeysFromStorage()
    if (githubToken) headers['X-GitHub-Token'] = githubToken
    if (googleApiKey) headers['X-Google-API-Key'] = googleApiKey
  }
  
  return headers
}

interface AIProvider {
  id: string
  name: string
  model: string
  status: string
  recommended: boolean
}

export const HomePage: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedAI, setSelectedAI] = useState<string>('')
  const [availableProviders, setAvailableProviders] = useState<AIProvider[]>([])
  const [isLoadingProviders, setIsLoadingProviders] = useState(true)
  const [showApiKeySetup, setShowApiKeySetup] = useState(false)
  const [isCheckingConfig, setIsCheckingConfig] = useState(true)
  const navigate = useNavigate()

  // 초기 설정 상태 확인
  useEffect(() => {
    const checkInitialConfig = async () => {
      try {
        const response = await fetch('/api/v1/config/keys-required', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          }
        })
        
        if (response.ok) {
          const result = await response.json()
          if (result.keys_required) {
            setShowApiKeySetup(true)
          }
        }
      } catch (error) {
        console.error('설정 상태 확인 실패:', error)
        // 에러가 발생해도 계속 진행 (키가 있을 수도 있음)
      } finally {
        setIsCheckingConfig(false)
      }
    }
    
    checkInitialConfig()
  }, [])

  // AI 제공업체 목록 로드
  useEffect(() => {
    if (isCheckingConfig || showApiKeySetup) return
    
    const loadAIProviders = async () => {
      try {
        const response = await fetch('/api/v1/ai/providers', {
          method: 'GET',
          headers: createApiHeaders(true), // API 키 포함하여 헤더 생성
          // 5초 타임아웃 설정
          signal: AbortSignal.timeout(5000)
        })
        
        if (response.ok) {
          const providers = await response.json()
          setAvailableProviders(providers)
          // 기본값으로 추천 제공업체 선택 (Gemini Flash 우선)
          const recommended = providers.find((p: AIProvider) => p.recommended)
          if (recommended) {
            setSelectedAI(recommended.id)
          } else if (providers.length > 0) {
            setSelectedAI(providers[0].id)
          }
        } else {
          console.error('AI 제공업체 로드 실패:', response.status, response.statusText)
          // Fallback: 기본 제공업체 목록 사용
          setAvailableProviders([
            {
              id: 'gemini_flash',
              name: 'Google Gemini 2.0 Flash',
              model: 'gemini-2.0-flash-exp',
              status: 'available',
              recommended: true
            }
          ])
          setSelectedAI('gemini_flash')
        }
      } catch (error) {
        console.error('AI 제공업체 로드 실패:', error)
        // Fallback: 기본 제공업체 목록 사용
        setAvailableProviders([
          {
            id: 'gemini_flash',
            name: 'Google Gemini 2.0 Flash',
            model: 'gemini-2.0-flash-exp',
            status: 'available',
            recommended: true
          }
        ])
        setSelectedAI('gemini_flash')
      } finally {
        setIsLoadingProviders(false)
      }
    }
    
    loadAIProviders()
  }, [isCheckingConfig, showApiKeySetup])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl.trim()) return

    setIsLoading(true)
    
    try {
      // GitHub URL 유효성 검사
      const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+/
      if (!urlPattern.test(repoUrl)) {
        alert('올바른 GitHub 저장소 URL을 입력해주세요.')
        return
      }

      // 저장소 분석 요청
      const response = await fetch('/api/v1/repository/analyze', {
        method: 'POST',
        headers: createApiHeaders(true), // API 키 포함하여 헤더 생성
        body: JSON.stringify({
          repo_url: repoUrl,
          store_results: true,
          ai_provider: selectedAI
        })
      })

      if (!response.ok) {
        throw new Error('저장소 분석에 실패했습니다.')
      }

      const result = await response.json()
      console.log('Backend response:', result) // 디버깅용
      console.log('Response keys:', Object.keys(result)) // 키 목록 확인
      
      // 응답 구조에 따라 분기 처리
      let analysisData = result;
      if (result.data) {
        // {success: true, data: {...}} 형태인 경우
        analysisData = result.data;
        console.log('Using result.data:', analysisData);
      }
      
      console.log('Analysis ID:', analysisData.analysis_id) // 분석 ID 확인
      
      if (result.success || analysisData.success) {
        // 분석 성공 시 고유 ID를 포함한 대시보드로 이동
        if (analysisData.analysis_id) {
          console.log('Navigating to:', `/dashboard/${analysisData.analysis_id}`)
          navigate(`/dashboard/${analysisData.analysis_id}`)
        } else {
          throw new Error('분석 ID를 받지 못했습니다.')
        }
      } else {
        throw new Error(analysisData.error || result.error || '분석에 실패했습니다.')
      }
      
    } catch (error) {
      console.error('Error:', error)
      alert(error instanceof Error ? error.message : '오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const sampleRepos = [
    'https://github.com/facebook/react',
    'https://github.com/microsoft/vscode',
    'https://github.com/nodejs/node',
    'https://github.com/django/django',
    'https://github.com/hong-seongmin/HWnow'
  ]

  const handleApiKeysSet = () => {
    setShowApiKeySetup(false)
    // API 키 설정 후 AI 제공업체 목록을 다시 로드
    setIsLoadingProviders(true)
  }

  if (isCheckingConfig) {
    return (
      <div className="home-page">
        <div className="loading-screen">
          <div className="spinner"></div>
          <p>설정을 확인하는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="homepage-container-new">
      <div className="hero-wrapper-new">
        <div className="hero-content">
          <h1 className="title-new">
            ⚡ TechGiterview
          </h1>
          <p className="subtitle-new">
            GitHub 저장소를 분석하여 맞춤형 기술면접을 준비하세요
          </p>
          <p className="description-new">
            AI가 당신의 코드를 분석하고 실제 면접에서 나올 수 있는 질문들을 생성합니다.
            실시간 모의면접으로 완벽한 준비를 해보세요.
          </p>
        </div>

        <div className="repo-input-section">
          {/* API 키 설정 버튼 */}
          <div className="api-key-section-new">
            <div className="api-key-header-new">
              <h3 className="api-key-title-new">
                🔑 API 키 설정
              </h3>
              <button 
                className="api-key-button-new"
                onClick={() => setShowApiKeySetup(true)}
                type="button"
              >
                ⚙️ API 키 설정
              </button>
            </div>
          </div>

          {/* AI 모델 선택 섹션 */}
          <div className="ai-selection-section-new">
            <h3 className="ai-selection-title-new">
              🤖 AI 모델 선택
            </h3>
            {isLoadingProviders ? (
              <div className="loading-providers">AI 모델을 불러오는 중...</div>
            ) : availableProviders.length > 0 ? (
              <div className="ai-providers-grid">
                {availableProviders.map((provider) => (
                  <label
                    key={provider.id}
                    className={`ai-provider-card-new ${selectedAI === provider.id ? 'selected' : ''} ${provider.recommended ? 'recommended' : ''}`}
                  >
                    <input
                      type="radio"
                      name="aiProvider"
                      value={provider.id}
                      checked={selectedAI === provider.id}
                      onChange={(e) => setSelectedAI(e.target.value)}
                      className="ai-provider-radio"
                    />
                    <div className="ai-provider-content">
                      <div className="ai-provider-name-new">
                        {provider.name}
                        {provider.recommended && <span className="recommended-badge-new">추천</span>}
                      </div>
                      <div className="ai-provider-model-new">{provider.model}</div>
                      <div className={`ai-provider-status-new ${provider.status}`}>
                        {provider.status === 'ready' ? '● 사용 가능' : '○ 설정됨'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div className="no-providers">사용 가능한 AI 모델이 없습니다.</div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="repo-form-new">
            <div className="input-group-new">
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="GitHub 저장소 URL을 입력하세요 (예: https://github.com/facebook/react)"
                className="repo-input-new"
                required
                disabled={isLoading}
              />
              <button 
                type="submit" 
                className="analyze-button-new"
                disabled={isLoading || !repoUrl.trim() || !selectedAI}
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span>
                    분석 중...
                  </>
                ) : (
                  '🚀 분석 시작'
                )}
              </button>
            </div>
          </form>

          <div className="sample-repos-new">
            <p className="sample-title-new">
              💡 샘플 저장소로 체험해보기:
            </p>
            <div className="sample-links-new">
              {sampleRepos.map((repo, index) => (
                <button
                  key={index}
                  onClick={() => setRepoUrl(repo)}
                  className="sample-repo-button-new"
                  disabled={isLoading}
                >
                  {repo.split('/').slice(-2).join('/')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="features-section-new">
        <h2 className="features-title-new">주요 기능</h2>
        <div className="features-grid-new">
          <div className="feature-card-new">
            <div className="feature-icon-new chart">
              📊
            </div>
            <h3>저장소 분석</h3>
            <p>GitHub 저장소의 코드 구조, 기술 스택, 복잡도를 자동으로 분석합니다.</p>
          </div>
          
          <div className="feature-card-new">
            <div className="feature-icon-new robot">
              🤖
            </div>
            <h3>AI 질문 생성</h3>
            <p>분석 결과를 바탕으로 맞춤형 기술면접 질문을 자동으로 생성합니다.</p>
          </div>
          
          <div className="feature-card-new">
            <div className="feature-icon-new chat">
              💬
            </div>
            <h3>실시간 모의면접</h3>
            <p>WebSocket 기반으로 실제 면접과 같은 환경에서 연습할 수 있습니다.</p>
          </div>
          
          <div className="feature-card-new">
            <div className="feature-icon-new report">
              📈
            </div>
            <h3>상세 리포트</h3>
            <p>답변에 대한 AI 평가와 개선 제안을 통해 실력을 향상시킬 수 있습니다.</p>
          </div>
        </div>
      </div>

      <div className="how-it-works-section-new">
        <h2 className="section-title-new">작동 원리</h2>
        <div className="steps-container-new">
          <div className="step-new">
            <div className="step-number-new">1</div>
            <h3>저장소 입력</h3>
            <p>GitHub 저장소 URL을 입력하면 자동으로 코드를 분석합니다.</p>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="step-new">
            <div className="step-number-new">2</div>
            <h3>AI 분석</h3>
            <p>기술 스택, 코드 품질, 복잡도를 종합적으로 평가합니다.</p>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="step-new">
            <div className="step-number-new">3</div>
            <h3>질문 생성</h3>
            <p>분석 결과를 바탕으로 맞춤형 면접 질문을 생성합니다.</p>
          </div>
          
          <div className="step-arrow-new">→</div>
          
          <div className="step-new">
            <div className="step-number-new">4</div>
            <h3>모의면접</h3>
            <p>실시간으로 질문에 답하고 즉시 피드백을 받습니다.</p>
          </div>
        </div>
      </div>

      {showApiKeySetup && (
        <ApiKeySetup onApiKeysSet={handleApiKeysSet} />
      )}
      
      {/* 푸터 섹션 */}
      <footer className="homepage-footer">
        <div className="footer-container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>⚡ TechGiterview</h3>
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
                  🐙 GitHub Repository
                </a>
                <a
                  href="https://buymeacoffee.com/oursophy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer-link"
                >
                  ☕ Buy Me a Coffee
                </a>
              </div>
            </div>
            
            <div className="footer-section">
              <h4>연락처</h4>
              <ul>
                <li>📧 hong112424@naver.com</li>
                <li>🐛 GitHub Issues</li>
                <li>💬 Discord Community</li>
                <li>📚 Documentation</li>
              </ul>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; 2024 TechGiterview. All rights reserved.</p>
            <div className="footer-legal-links">
              <a href="#privacy">개인정보처리방침</a>
              <a href="#terms">이용약관</a>
              <a href="#faq">FAQ</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}