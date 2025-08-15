import React, { Component, ReactNode } from 'react'
import { AlertTriangle, RotateCcw, ArrowLeft } from 'lucide-react'
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
    
    // 메시지 채널 오류 특별 처리
    if (error.message?.includes('message channel closed') || 
        error.message?.includes('asynchronous response')) {
      console.warn('브라우저 확장 프로그램 충돌로 인한 오류로 판단됩니다:', error.message)
      // 자동 복구 시도
      setTimeout(() => {
        if (this.state.hasError) {
          this.setState({ hasError: false, error: null, errorInfo: '' })
        }
      }, 1000)
    }
    
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
        <AlertTriangle className="icon" /> 컴포넌트 렌더링 오류
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
          <RotateCcw className="icon" /> 새로고침
        </button>
        <button
          onClick={() => window.history.back()}
          className={styles.secondaryButton}
        >
          <ArrowLeft className="icon" /> 뒤로가기
        </button>
      </div>
    </div>
  )
}