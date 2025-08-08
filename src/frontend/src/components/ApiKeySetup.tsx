import React, { useState } from 'react'
import './ApiKeySetup.css'

interface ApiKeySetupProps {
  onApiKeysSet: () => void
}

export const ApiKeySetup: React.FC<ApiKeySetupProps> = ({ onApiKeysSet }) => {
  const [githubToken, setGithubToken] = useState('')
  const [googleApiKey, setGoogleApiKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

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
            설정된 키는 현재 세션에서만 사용되며 저장되지 않습니다.
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
            입력하신 API 키는 안전하게 처리되며, 브라우저를 닫으면 자동으로 삭제됩니다.
          </span>
        </div>
      </div>
    </div>
  )
}