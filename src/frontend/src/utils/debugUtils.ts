/**
 * 디버깅 및 로깅 유틸리티
 * 환경별 로그 레벨 관리 및 성능 최적화된 로깅 제공
 */

import React from 'react';

export enum LogLevel {
  OFF = 0,
  ERROR = 1,
  WARN = 2,
  INFO = 3,
  DEBUG = 4,
  TRACE = 5
}

interface LogConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableRenderLogs: boolean;
  enablePerformanceLogs: boolean;
  enableNetworkLogs: boolean;
  debounceMs: number;
}

class DebugManager {
  private config: LogConfig;
  private debounceMap = new Map<string, NodeJS.Timeout>();
  private logCounts = new Map<string, number>();

  constructor() {
    // 환경별 기본 설정
    this.config = {
      level: this.getLogLevel(),
      enableConsole: import.meta.env.DEV,
      enableRenderLogs: import.meta.env.VITE_DEBUG_RENDER === 'true',
      enablePerformanceLogs: import.meta.env.VITE_DEBUG_PERFORMANCE === 'true',
      enableNetworkLogs: import.meta.env.VITE_DEBUG_NETWORK === 'true',
      debounceMs: 100
    };
  }

  private getLogLevel(): LogLevel {
    const envLevel = import.meta.env.VITE_LOG_LEVEL?.toUpperCase();
    switch (envLevel) {
      case 'OFF': return LogLevel.OFF;
      case 'ERROR': return LogLevel.ERROR;
      case 'WARN': return LogLevel.WARN;
      case 'INFO': return LogLevel.INFO;
      case 'DEBUG': return LogLevel.DEBUG;
      case 'TRACE': return LogLevel.TRACE;
      default: return import.meta.env.DEV ? LogLevel.DEBUG : LogLevel.WARN;
    }
  }

  private shouldLog(level: LogLevel, category?: string): boolean {
    if (!this.config.enableConsole) return false;
    if (level > this.config.level) return false;
    
    // 카테고리별 세부 제어
    if (category === 'render' && !this.config.enableRenderLogs) return false;
    if (category === 'performance' && !this.config.enablePerformanceLogs) return false;
    if (category === 'network' && !this.config.enableNetworkLogs) return false;
    
    return true;
  }

  private formatMessage(level: string, category: string, message: string, data?: any): [string, any?] {
    const timestamp = new Date().toISOString().substr(11, 12);
    const prefix = `[${timestamp}] [${level}] [${category.toUpperCase()}]`;
    
    if (data !== undefined) {
      return [`${prefix} ${message}`, data];
    }
    return [`${prefix} ${message}`];
  }

  private logWithDebounce(key: string, logFn: () => void): void {
    // 기존 타이머 취소
    if (this.debounceMap.has(key)) {
      clearTimeout(this.debounceMap.get(key)!);
    }

    // 새 타이머 설정
    const timer = setTimeout(() => {
      logFn();
      this.debounceMap.delete(key);
    }, this.config.debounceMs);

    this.debounceMap.set(key, timer);
  }

  /**
   * 에러 로그
   */
  public error(category: string, message: string, error?: any): void {
    if (!this.shouldLog(LogLevel.ERROR, category)) return;
    
    const [formattedMsg, data] = this.formatMessage('ERROR', category, message, error);
    console.error(formattedMsg, data);
  }

  /**
   * 경고 로그
   */
  public warn(category: string, message: string, data?: any): void {
    if (!this.shouldLog(LogLevel.WARN, category)) return;
    
    const [formattedMsg, logData] = this.formatMessage('WARN', category, message, data);
    console.warn(formattedMsg, logData);
  }

  /**
   * 정보 로그
   */
  public info(category: string, message: string, data?: any): void {
    if (!this.shouldLog(LogLevel.INFO, category)) return;
    
    const [formattedMsg, logData] = this.formatMessage('INFO', category, message, data);
    console.info(formattedMsg, logData);
  }

  /**
   * 디버그 로그
   */
  public debug(category: string, message: string, data?: any): void {
    if (!this.shouldLog(LogLevel.DEBUG, category)) return;
    
    const [formattedMsg, logData] = this.formatMessage('DEBUG', category, message, data);
    console.log(formattedMsg, logData);
  }

  /**
   * 렌더링 로그 (디바운싱 적용)
   */
  public renderLog(componentName: string, message: string, data?: any): void {
    if (!this.shouldLog(LogLevel.DEBUG, 'render')) return;

    const key = `render-${componentName}-${message}`;
    this.logWithDebounce(key, () => {
      const [formattedMsg, logData] = this.formatMessage('RENDER', componentName, message, data);
      console.log(formattedMsg, logData);
    });
  }

  /**
   * 성능 로그
   */
  public performanceLog(operation: string, duration: number, data?: any): void {
    if (!this.shouldLog(LogLevel.INFO, 'performance')) return;
    
    const message = `${operation} completed in ${duration}ms`;
    const [formattedMsg, logData] = this.formatMessage('PERF', 'performance', message, data);
    console.log(formattedMsg, logData);
  }

  /**
   * 네트워크 로그
   */
  public networkLog(method: string, url: string, status: number, duration?: number): void {
    if (!this.shouldLog(LogLevel.INFO, 'network')) return;
    
    const message = `${method} ${url} → ${status}${duration ? ` (${duration}ms)` : ''}`;
    const [formattedMsg] = this.formatMessage('NET', 'network', message);
    console.log(formattedMsg);
  }

  /**
   * 조건부 로그 (한 번만)
   */
  public logOnce(key: string, level: LogLevel, category: string, message: string, data?: any): void {
    if (this.logCounts.has(key)) return;
    
    this.logCounts.set(key, 1);
    
    switch (level) {
      case LogLevel.ERROR:
        this.error(category, message, data);
        break;
      case LogLevel.WARN:
        this.warn(category, message, data);
        break;
      case LogLevel.INFO:
        this.info(category, message, data);
        break;
      case LogLevel.DEBUG:
        this.debug(category, message, data);
        break;
    }
  }

  /**
   * 설정 업데이트
   */
  public updateConfig(newConfig: Partial<LogConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 모든 디바운스 타이머 정리
   */
  public cleanup(): void {
    this.debounceMap.forEach(timer => clearTimeout(timer));
    this.debounceMap.clear();
    this.logCounts.clear();
  }
}

// 전역 인스턴스 생성
const debugManager = new DebugManager();

// 편의 함수들
export const debugLog = {
  error: (category: string, message: string, error?: any) => debugManager.error(category, message, error),
  warn: (category: string, message: string, data?: any) => debugManager.warn(category, message, data),
  info: (category: string, message: string, data?: any) => debugManager.info(category, message, data),
  debug: (category: string, message: string, data?: any) => debugManager.debug(category, message, data),
  render: (componentName: string, message: string, data?: any) => debugManager.renderLog(componentName, message, data),
  performance: (operation: string, duration: number, data?: any) => debugManager.performanceLog(operation, duration, data),
  network: (method: string, url: string, status: number, duration?: number) => debugManager.networkLog(method, url, status, duration),
  once: (key: string, level: LogLevel, category: string, message: string, data?: any) => debugManager.logOnce(key, level, category, message, data)
};

// React Hook
export function useDebugLog(componentName: string) {
  const renderLog = React.useCallback((message: string, data?: any) => {
    debugManager.renderLog(componentName, message, data);
  }, [componentName]);

  const debugOnce = React.useCallback((key: string, message: string, data?: any) => {
    debugManager.logOnce(`${componentName}-${key}`, LogLevel.DEBUG, componentName, message, data);
  }, [componentName]);

  React.useEffect(() => {
    return () => debugManager.cleanup();
  }, []);

  return { renderLog, debugOnce };
}

// 성능 측정 유틸리티
export function measurePerformance<T>(
  operation: string,
  fn: () => T,
  logResult: boolean = true
): T {
  const start = performance.now();
  const result = fn();
  const duration = performance.now() - start;
  
  if (logResult) {
    debugManager.performanceLog(operation, duration);
  }
  
  return result;
}

// 비동기 성능 측정
export async function measureAsyncPerformance<T>(
  operation: string,
  fn: () => Promise<T>,
  logResult: boolean = true
): Promise<T> {
  const start = performance.now();
  const result = await fn();
  const duration = performance.now() - start;
  
  if (logResult) {
    debugManager.performanceLog(operation, duration);
  }
  
  return result;
}

export default debugManager;