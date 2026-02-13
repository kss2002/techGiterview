/**
 * 오류 처리 유틸리티
 * 브라우저 확장 프로그램 충돌 및 기타 오류 상황 처리
 */

export interface ErrorInfo {
  message: string
  stack?: string
  timestamp: number
  userAgent: string
  url: string
}

export class ErrorHandler {
  private static instance: ErrorHandler
  private errors: ErrorInfo[] = []

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  /**
   * 확장 프로그램 관련 오류인지 확인
   */
  static isExtensionError(error: Error | string): boolean {
    const message = typeof error === 'string' ? error : error.message
    return (
      message.includes('message channel closed') ||
      message.includes('asynchronous response') ||
      message.includes('Extension context invalidated') ||
      message.includes('Could not establish connection')
    )
  }

  /**
   * 오류 로깅 및 처리
   */
  logError(error: Error | string, context?: string): void {
    const errorInfo: ErrorInfo = {
      message: typeof error === 'string' ? error : error.message,
      stack: typeof error === 'object' ? error.stack : undefined,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href
    }

    this.errors.push(errorInfo)

    // 확장 프로그램 오류는 경고로만 처리
    if (ErrorHandler.isExtensionError(error)) {
      console.warn(
        `TOOL 브라우저 확장 프로그램 충돌 감지${context ? ` (${context})` : ''}:`,
        errorInfo.message
      )
      return
    }

    // 일반 오류는 에러로 처리
    console.error(
      `ERROR 애플리케이션 오류${context ? ` (${context})` : ''}:`,
      error
    )
  }

  /**
   * 오류 통계 반환
   */
  getErrorStats(): {
    total: number
    extensionErrors: number
    appErrors: number
    recent: ErrorInfo[]
  } {
    const extensionErrors = this.errors.filter(err => 
      ErrorHandler.isExtensionError(err.message)
    )
    const appErrors = this.errors.filter(err => 
      !ErrorHandler.isExtensionError(err.message)
    )
    const recent = this.errors
      .slice(-5)
      .sort((a, b) => b.timestamp - a.timestamp)

    return {
      total: this.errors.length,
      extensionErrors: extensionErrors.length,
      appErrors: appErrors.length,
      recent
    }
  }

  /**
   * 오류 목록 초기화
   */
  clearErrors(): void {
    this.errors = []
  }
}

// 전역 인스턴스
export const errorHandler = ErrorHandler.getInstance()

// 개발 환경에서 콘솔에 오류 통계 노출
if (import.meta.env.DEV) {
  const devWindow = window as Window & {
    getErrorStats?: () => ReturnType<ErrorHandler['getErrorStats']>
    clearErrors?: () => void
  }
  devWindow.getErrorStats = () => ErrorHandler.getInstance().getErrorStats()
  devWindow.clearErrors = () => ErrorHandler.getInstance().clearErrors()
  console.log('DEV 개발 모드: 오류 통계는 getErrorStats(), 초기화는 clearErrors() 사용')
}
