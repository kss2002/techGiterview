import React, { useState, useEffect } from 'react'
import './ApiKeySetup.css'

// 로컬스토리지 키 상수
const STORAGE_KEYS = {
  GITHUB_TOKEN: 'techgiterview_github_token',
  GOOGLE_API_KEY: 'techgiterview_google_api_key',
} as const

// 로컬스토리지 유틸리티 함수들
const storageUtils = {
  saveApiKeys: (githubToken: string, googleApiKey: string) => {
    try {
      localStorage.setItem(STORAGE_KEYS.GITHUB_TOKEN, githubToken)
      localStorage.setItem(STORAGE_KEYS.GOOGLE_API_KEY, googleApiKey)
      console.log('API 키가 로컬스토리지에 저장되었습니다.')
    } catch (error) {
      console.warn('로컬스토리지 저장 실패:', error)
    }
  },
  
  loadApiKeys: () => {
    try {
      return {
        githubToken: localStorage.getItem(STORAGE_KEYS.GITHUB_TOKEN) || '',
        googleApiKey: localStorage.getItem(STORAGE_KEYS.GOOGLE_API_KEY) || ''
      }
    } catch (error) {
      console.warn('로컬스토리지 로드 실패:', error)
      return { githubToken: '', googleApiKey: '' }
    }
  },
  
  clearApiKeys: () => {
    try {
      localStorage.removeItem(STORAGE_KEYS.GITHUB_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.GOOGLE_API_KEY)
      console.log('저장된 API 키가 삭제되었습니다.')
    } catch (error) {
      console.warn('로컬스토리지 삭제 실패:', error)
    }
  },
  
  hasStoredKeys: () => {
    try {
      const githubToken = localStorage.getItem(STORAGE_KEYS.GITHUB_TOKEN)
      const googleApiKey = localStorage.getItem(STORAGE_KEYS.GOOGLE_API_KEY)
      return !!(githubToken && googleApiKey)
    } catch (error) {
      return false
    }
  }
}

interface ApiKeySetupProps {
  onApiKeysSet: () => void
}

interface KeysRequiredResponse {
  keys_required: boolean
  use_local_storage: boolean
  missing_keys: {
    github_token: boolean
    google_api_key: boolean
  }
}

export const ApiKeySetup: React.FC<ApiKeySetupProps> = ({ onApiKeysSet }) => {
  const [githubToken, setGithubToken] = useState('')
  const [googleApiKey, setGoogleApiKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [saveToLocalStorage, setSaveToLocalStorage] = useState(true)
  const [useLocalStorageMode, setUseLocalStorageMode] = useState(false)

  // 컴포넌트 마운트 시 모드 확인 및 저장된 키 로드
  useEffect(() => {
    const checkMode = async () => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 3000) // 3초 타임아웃
        
        const response = await fetch('/api/v1/config/keys-required', {
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)
        
        if (response.ok) {
          const data: KeysRequiredResponse = await response.json()
          setUseLocalStorageMode(data.use_local_storage)
          
          // 로컬스토리지 모드인 경우에만 저장된 키 로드
          if (data.use_local_storage) {
            const storedKeys = storageUtils.loadApiKeys()
            if (storedKeys.githubToken && storedKeys.googleApiKey) {
              setGithubToken(storedKeys.githubToken)
              setGoogleApiKey(storedKeys.googleApiKey)
              console.log('저장된 API 키를 로드했습니다.')
            }
          }
        } else {
          // 서버 응답이 실패한 경우 로컬 모드로 전환
          console.warn(`서버 응답 실패 (${response.status}), 로컬 모드로 전환`)
          setUseLocalStorageMode(true)
        }
      } catch (error) {
        console.warn('백엔드 서버 연결 실패, 로컬 모드로 전환:', error)
        // 연결 실패 시 로컬스토리지 모드로 강제 설정
        setUseLocalStorageMode(true)
        
        // 저장된 키가 있으면 자동 로드
        const storedKeys = storageUtils.loadApiKeys()
        if (storedKeys.githubToken && storedKeys.googleApiKey) {
          setGithubToken(storedKeys.githubToken)
          setGoogleApiKey(storedKeys.googleApiKey)
          console.log('오프라인 모드: 저장된 API 키를 로드했습니다.')
        }
      }
    }
    
    checkMode()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      if (useLocalStorageMode) {
        // 로컬스토리지 모드: 서버에 키를 전송하지 않고 클라이언트에서만 처리
        console.log('로컬스토리지 모드: 클라이언트 전용 처리')
        
        // 로컬스토리지에 저장 (선택사항)
        if (saveToLocalStorage) {
          storageUtils.saveApiKeys(githubToken, googleApiKey)
          console.log('API 키가 로컬스토리지에 저장되었습니다.')
        }
        
        // API 키 유효성을 테스트하기 위해 AI providers 호출
        const testResponse = await fetch('/api/v1/ai/providers', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'X-GitHub-Token': githubToken,
            'X-Google-API-Key': googleApiKey
          }
        })
        
        if (!testResponse.ok) {
          throw new Error('API 키 검증에 실패했습니다.')
        }
        
        const providers = await testResponse.json()
        if (providers.length === 0) {
          throw new Error('사용 가능한 AI 제공업체가 없습니다. API 키를 확인해주세요.')
        }
        
        console.log('API 키 검증 완료. 사용 가능한 제공업체:', providers.length)
      } else {
        // 서버 모드: 기존 방식 유지
        const response = await fetch('/api/v1/config/api-keys', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            github_token: githubToken,
            google_api_key: googleApiKey
          })
        })

        if (!response.ok) {
          throw new Error('API 키 설정에 실패했습니다.')
        }

        const result = await response.json()
        console.log('API 키 설정 완료:', result.message)
        
        // 서버 모드에서도 로컬스토리지 저장 옵션 제공
        if (saveToLocalStorage) {
          storageUtils.saveApiKeys(githubToken, googleApiKey)
        }
      }
      
      onApiKeysSet()
    } catch (error) {
      console.error('API 키 설정 오류:', error)
      setError(error instanceof Error ? error.message : 'API 키 설정에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="api-key-setup-overlay">
      <div className="api-key-setup-modal">
        <div className="setup-header">
          <h2 className="setup-title">
            🔑 API 키 설정 필요
          </h2>
          <p className="setup-description">
            TechGiterview를 사용하려면 GitHub 토큰과 Google API 키가 필요합니다.
            <br />
            {useLocalStorageMode ? (
              '개인 API 키 모드: 키는 브라우저에서만 사용되며 서버에 저장되지 않습니다.'
            ) : (
              '서버 모드: 키는 현재 세션에서 사용되며 로컬스토리지에도 저장할 수 있습니다.'
            )}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="api-key-form">
          {/* Hidden username field for accessibility */}
          <input
            type="text"
            name="username"
            autoComplete="username"
            style={{ display: 'none' }}
            value="techgiterview-user"
            readOnly
            aria-hidden="true"
          />
          
          <div className="form-group">
            <label htmlFor="github-token" className="form-label">
              🐙 GitHub Personal Access Token
            </label>
            <input
              type="password"
              id="github-token"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              className="form-input"
              autoComplete="username"
              required
              disabled={isLoading}
            />
            <div className="form-help">
              <a
                href="https://github.com/settings/tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="help-link"
              >
                GitHub에서 토큰 생성하기 ↗
              </a>
              <br />
              <small>권한: repo (읽기) 권한이 필요합니다</small>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="google-api-key" className="form-label">
              🌍 Google API Key (Gemini)
            </label>
            <input
              type="password"
              id="google-api-key"
              value={googleApiKey}
              onChange={(e) => setGoogleApiKey(e.target.value)}
              placeholder="AIzaxxxxxxxxxxxxxxxxxxxxxxxx"
              className="form-input"
              autoComplete="new-password"
              required
              disabled={isLoading}
            />
            <div className="form-help">
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="help-link"
              >
                Google AI Studio에서 키 생성하기 ↗
              </a>
              <br />
              <small>Gemini API 사용을 위한 키가 필요합니다</small>
            </div>
          </div>

          {(useLocalStorageMode || !useLocalStorageMode) && (
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={saveToLocalStorage}
                  onChange={(e) => setSaveToLocalStorage(e.target.checked)}
                  disabled={isLoading}
                />
                <span className="checkbox-text">
                  💾 브라우저에 API 키 저장 (다음에 자동 로드)
                </span>
              </label>
              <div className="form-help">
                <small>
                  {useLocalStorageMode ? (
                    '체크 시 API 키가 브라우저 로컬스토리지에 저장되어 다음 방문 시 자동으로 로드됩니다.'
                  ) : (
                    '서버 모드에서도 편의를 위해 로컬스토리지에 저장할 수 있습니다.'
                  )}
                </small>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading || !githubToken.trim() || !googleApiKey.trim()}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  설정 중...
                </>
              ) : (
                <>
                  ✅ API 키 설정
                </>
              )}
            </button>
          </div>
        </form>

        <div className="security-notice">
          🔒
          <span>
            {useLocalStorageMode ? (
              '개인 API 키 모드에서는 키가 서버에 전송되지 않고 브라우저에서만 사용됩니다. 저장 시 로컬스토리지에 보관되며 언제든지 삭제할 수 있습니다.'
            ) : (
              '서버 모드에서는 키가 서버에서 관리됩니다. 저장 옵션 체크 시 로컬스토리지에도 저장되어 편의성을 제공합니다.'
            )}
          </span>
        </div>
      </div>
    </div>
  )
}