import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiKeySetup } from '../components/ApiKeySetup'
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

      // 저장소 분석 요청
      const response = await fetch('/api/v1/repository/analyze', {
        method: 'POST',
        headers: createApiHeaders(true),
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
      alert(error instanceof Error ? error.message : '오류가 발생했습니다.')
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
            
            {/* 상태 표시 */}
            <div className="status-indicators">
              {isUsingLocalData && (
                <div className="status-badge local">
                  💾 로컬 데이터 사용 중
                </div>
              )}
              {error && (
                <div className="status-badge error">
                  ⚠️ 서버 연결 오류 (오프라인 모드)
                </div>
              )}
              {!isLoading && !error && !isUsingLocalData && (
                <div className="status-badge online">
                  ✅ 서버 연결됨
                </div>
              )}
            </div>
          </div>

          {/* AI 모델 선택 섹션 */}
          <div className="ai-selection-section-new">
            <h3 className="ai-selection-title-new">
              🤖 AI 모델 선택
            </h3>
            {providers.length > 0 ? (
              <div className="ai-providers-grid">
                {providers.map((provider) => (
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
              <div className="no-providers">
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
                disabled={isAnalyzing}
              />
              <button 
                type="submit" 
                className="analyze-button-new"
                disabled={isAnalyzing || !repoUrl.trim() || !selectedAI}
              >
                {isAnalyzing ? (
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
                  disabled={isAnalyzing}
                >
                  {repo.split('/').slice(-2).join('/')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 기능 섹션 */}
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

      {/* 작동 원리 */}
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

      {/* API 키 설정 모달 */}
      {shouldShowApiKeySetup && (
        <ApiKeySetup onApiKeysSet={handleApiKeysSet} />
      )}
      
      {/* 푸터 */}
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