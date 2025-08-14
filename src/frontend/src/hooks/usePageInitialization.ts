import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'

// 로컬스토리지 유틸리티
const getApiKeysFromStorage = () => {
  try {
    return {
      githubToken: localStorage.getItem('techgiterview_github_token') || '',
      googleApiKey: localStorage.getItem('techgiterview_google_api_key') || ''
    }
  } catch (error) {
    return { githubToken: '', googleApiKey: '' }
  }
}

// API 요청 헤더 생성
const createApiHeaders = (includeApiKeys: boolean = false) => {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  }
  
  if (includeApiKeys) {
    const { githubToken, googleApiKey } = getApiKeysFromStorage()
    if (githubToken) headers['X-GitHub-Token'] = githubToken
    if (googleApiKey) headers['X-Google-API-Key'] = googleApiKey
  }
  
  return headers
}

// API 인터페이스
interface AIProvider {
  id: string
  name: string
  model: string
  status: string
  recommended: boolean
}

interface PageInitData {
  config: {
    keys_required: boolean
    use_local_storage: boolean
    missing_keys: Record<string, boolean>
  }
  providers: AIProvider[]
}

// 통합 API 호출 함수 (새로운 단일 엔드포인트 사용)
const fetchPageInitData = async (): Promise<PageInitData> => {
  const headers = createApiHeaders(true)
  
  // 새로운 통합 API 호출
  const response = await fetch('/api/v1/homepage/init', { headers })
  
  if (!response.ok) {
    throw new Error(`Homepage Init API 오류: ${response.status}`)
  }
  
  const data = await response.json()
  
  return {
    config: data.config,
    providers: data.providers
  }
}

// 로컬스토리지에서 즉시 사용 가능한 데이터 생성
const getLocalData = (): PageInitData => {
  const { githubToken, googleApiKey } = getApiKeysFromStorage()
  const hasKeys = !!(githubToken && googleApiKey)
  
  return {
    config: {
      keys_required: !hasKeys,
      use_local_storage: true,
      missing_keys: {
        github_token: !githubToken,
        google_api_key: !googleApiKey
      }
    },
    providers: [{
      id: 'gemini_flash',
      name: 'Google Gemini 2.0 Flash (기본)',
      model: 'gemini-2.0-flash-exp',
      status: 'available',
      recommended: true
    }]
  }
}

// 메인 Hook
export const usePageInitialization = () => {
  const [localData] = useState(() => getLocalData())
  
  // React Query로 서버 데이터 가져오기 (백그라운드)
  const {
    data: serverData,
    isLoading,
    error,
    isSuccess
  } = useQuery({
    queryKey: ['page-initialization'],
    queryFn: fetchPageInitData,
    staleTime: 5 * 60 * 1000, // 5분 캐시
    retry: 2,
    retryDelay: 1000,
  })
  
  // 서버 데이터가 있으면 사용, 없으면 로컬 데이터 사용
  const effectiveData = serverData || localData
  
  // AI 제공업체 선택 상태
  const [selectedAI, setSelectedAI] = useState('')
  
  // 추천 AI 자동 선택
  useEffect(() => {
    if (effectiveData.providers.length > 0 && !selectedAI) {
      const recommended = effectiveData.providers.find(p => p.recommended)
      if (recommended) {
        setSelectedAI(recommended.id)
      } else {
        setSelectedAI(effectiveData.providers[0].id)
      }
    }
  }, [effectiveData.providers, selectedAI])
  
  return {
    // 데이터
    config: effectiveData.config,
    providers: effectiveData.providers,
    selectedAI,
    setSelectedAI,
    
    // 상태
    isLoading,
    error,
    isSuccess,
    isUsingLocalData: !serverData,
    
    // 유틸리티
    hasStoredKeys: () => {
      const { githubToken, googleApiKey } = getApiKeysFromStorage()
      return !!(githubToken && googleApiKey)
    },
    
    createApiHeaders
  }
}