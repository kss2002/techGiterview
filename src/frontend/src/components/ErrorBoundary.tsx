import React, { Component, ReactNode } from 'react'
import { useErrorBoundaryStyles } from '../hooks/useStyles'

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

      return <ErrorFallback error={this.state.error} errorInfo={this.state.errorInfo} />
    }

    return this.props.children
  }
}

// 에러 폴백 컴포넌트 분리 (함수형 컴포넌트로 Hook 사용 가능)
function ErrorFallback({ error, errorInfo }: { error: Error | null; errorInfo: string }) {
  const styles = useErrorBoundaryStyles()

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>
        ⚠️ 컴포넌트 렌더링 오류
      </h2>
      <p className={styles.message}>
        페이지를 렌더링하는 중 오류가 발생했습니다.
      </p>
      <details className={styles.details}>
        <summary>
          오류 상세 정보 보기
        </summary>
        <div className={styles.detailsContent}>
          {error?.toString()}
          {errorInfo}
        </div>
      </details>
      <div className={styles.actions}>
        <button
          onClick={() => window.location.reload()}
          className={styles.primaryButton}
        >
          🔄 새로고침
        </button>
        <button
          onClick={() => window.history.back()}
          className={styles.secondaryButton}
        >
          ← 뒤로가기
        </button>
      </div>
    </div>
  )
}