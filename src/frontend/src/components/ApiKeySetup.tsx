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

export const ApiKeySetup: React.FC<ApiKeySetupProps> = ({ onApiKeysSet }) => {
  const [githubToken, setGithubToken] = useState('')
  const [googleApiKey, setGoogleApiKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [saveToLocalStorage, setSaveToLocalStorage] = useState(true)

  // 컴포넌트 마운트 시 저장된 키 로드
  useEffect(() => {
    const storedKeys = storageUtils.loadApiKeys()
    if (storedKeys.githubToken && storedKeys.googleApiKey) {
      setGithubToken(storedKeys.githubToken)
      setGoogleApiKey(storedKeys.googleApiKey)
      console.log('저장된 API 키를 로드했습니다.')
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
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
      
      // 로컬스토리지에 저장
      if (saveToLocalStorage) {
        storageUtils.saveApiKeys(githubToken, googleApiKey)
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
            <i className="fas fa-key"></i>
            API 키 설정 필요
          </h2>
          <p className="setup-description">
            TechGiterview를 사용하려면 GitHub 토큰과 Google API 키가 필요합니다.
            <br />
            키는 브라우저 로컬스토리지에 저장하여 다음에 자동으로 로드할 수 있습니다.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="api-key-form">
          <div className="form-group">
            <label htmlFor="github-token" className="form-label">
              <i className="fab fa-github"></i>
              GitHub Personal Access Token
            </label>
            <input
              type="password"
              id="github-token"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              className="form-input"
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
              <i className="fab fa-google"></i>
              Google API Key (Gemini)
            </label>
            <input
              type="password"
              id="google-api-key"
              value={googleApiKey}
              onChange={(e) => setGoogleApiKey(e.target.value)}
              placeholder="AIzaxxxxxxxxxxxxxxxxxxxxxxxx"
              className="form-input"
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

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={saveToLocalStorage}
                onChange={(e) => setSaveToLocalStorage(e.target.checked)}
                disabled={isLoading}
              />
              <span className="checkbox-text">
                <i className="fas fa-save"></i>
                브라우저에 API 키 저장 (다음에 자동 로드)
              </span>
            </label>
            <div className="form-help">
              <small>체크 시 API 키가 브라우저 로컬스토리지에 저장되어 다음 방문 시 자동으로 로드됩니다.</small>
            </div>
          </div>

          {error && (
            <div className="error-message">
              <i className="fas fa-exclamation-triangle"></i>
              {error}
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
                  <i className="fas fa-check"></i>
                  API 키 설정
                </>
              )}
            </button>
          </div>
        </form>

        <div className="security-notice">
          <i className="fas fa-shield-alt"></i>
          <span>
            입력하신 API 키는 안전하게 처리됩니다. 저장 옵션을 체크한 경우 브라우저 로컬스토리지에 저장되며, 
            언제든지 브라우저 설정에서 삭제할 수 있습니다.
          </span>
        </div>
      </div>
    </div>
  )
}