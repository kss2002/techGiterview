import React, { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: string
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: ''
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: ''
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error,
      errorInfo: errorInfo.componentStack
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          background: '#fff',
          border: '1px solid #ff6b6b',
          borderRadius: '8px',
          margin: '20px',
          maxWidth: '800px',
          marginLeft: 'auto',
          marginRight: 'auto'
        }}>
          <h2 style={{ color: '#e53e3e', marginBottom: '16px' }}>
            ⚠️ 컴포넌트 렌더링 오류
          </h2>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            페이지를 렌더링하는 중 오류가 발생했습니다.
          </p>
          <details style={{ textAlign: 'left', marginBottom: '20px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
              오류 상세 정보 보기
            </summary>
            <div style={{
              background: '#f8f9fa',
              padding: '12px',
              borderRadius: '4px',
              marginTop: '8px',
              fontSize: '14px',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              color: '#d63384'
            }}>
              {this.state.error?.toString()}
              {this.state.errorInfo}
            </div>
          </details>
          <div>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#007bff',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '6px',
                cursor: 'pointer',
                marginRight: '12px',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              🔄 새로고침
            </button>
            <button
              onClick={() => window.history.back()}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              ← 뒤로가기
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}