/**
 * API 호출을 위한 유틸리티 함수들
 */

// 현재 실행 환경 감지 (개선된 로직)
const detectEnvironment = (): 'docker' | 'local' => {
  const hostname = window.location.hostname;
  const port = window.location.port;
  
  // 포트 기반 환경 감지 (더 정확한 방법)
  if (port === '9105') {
    // Docker 컨테이너에서 외부로 노출된 포트
    console.log('[API_UTILS] Docker 환경 감지 (포트 9105)');
    return 'docker';
  } else if (port === '3001') {
    // 로컬 개발 서버 포트
    console.log('[API_UTILS] 로컬 환경 감지 (포트 3001)');
    return 'local';
  }
  
  // 호스트명 기반 백업 감지
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.log('[API_UTILS] 로컬 환경 감지 (localhost)');
    return 'local';
  } else {
    console.log('[API_UTILS] Docker 환경 감지 (비-localhost 호스트)');
    return 'docker';
  }
};

// 환경에 따른 API URL 전략
const getApiBaseUrl = (): string => {
  const environment = detectEnvironment();
  
  if (environment === 'docker') {
    // Docker 환경: 상대 경로 사용 (Vite 프록시 활용)
    console.log('[API_UTILS] Docker 환경 - Vite 프록시 사용');
    return '';
  } else {
    // 로컬 환경: 프록시 우선, 직접 호출 백업
    // 먼저 프록시 사용을 시도하고, 실패하면 직접 호출
    const shouldUseProxy = import.meta.env.MODE === 'development';
    if (shouldUseProxy) {
      console.log('[API_UTILS] 로컬 환경 - Vite 프록시 사용');
      return '';
    } else {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      console.log('[API_UTILS] 로컬 환경 - 직접 API URL 사용:', apiUrl);
      return apiUrl;
    }
  }
};

// API 경로를 완전한 URL로 변환하는 함수
export const buildApiUrl = (path: string): string => {
  const baseUrl = getApiBaseUrl();
  
  // path가 이미 완전한 URL이면 그대로 반환
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  
  // path가 '/'로 시작하지 않으면 추가
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  
  // baseUrl이 있으면 조합, 없으면 상대경로 그대로 (프록시 사용)
  if (baseUrl) {
    return `${baseUrl}${normalizedPath}`;
  }
  
  return normalizedPath;
};

// fetch 래퍼 함수 (API URL 자동 변환)
export const apiFetch = async (path: string, options?: RequestInit): Promise<Response> => {
  const url = buildApiUrl(path);
  console.log(`[API_FETCH] ${options?.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      console.warn(`[API_FETCH] HTTP ${response.status} ${response.statusText} for ${url}`);
    }
    return response;
  } catch (error) {
    console.error(`[API_FETCH] Network error for ${url}:`, error);
    throw error;
  }
};

// API 상태 확인 함수
export const checkApiConnection = async (): Promise<boolean> => {
  try {
    const response = await apiFetch('/health');
    return response.ok;
  } catch (error) {
    console.warn('[API_CONNECTION] Backend connection failed:', error);
    return false;
  }
};

// 디버깅을 위한 현재 API 설정 로깅
export const logApiConfig = (): void => {
  const environment = detectEnvironment();
  const baseUrl = getApiBaseUrl();
  console.log('[API_CONFIG]', {
    environment,
    hostname: window.location.hostname,
    port: window.location.port,
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_PROXY_TARGET: import.meta.env.VITE_PROXY_TARGET,
    baseUrl,
    currentLocation: window.location.href,
    mode: import.meta.env.MODE
  });
};

// 초기화 시 설정 로깅
console.log('[API_UTILS] 초기화 중...');
logApiConfig();
