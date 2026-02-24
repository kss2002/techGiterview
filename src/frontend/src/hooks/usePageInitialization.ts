import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { apiFetch } from '../utils/apiUtils'
import {
  createApiHeaders as createSharedApiHeaders,
  getApiKeysFromStorage,
  hasRequiredApiKeys,
} from '../utils/apiHeaders'

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
    development_mode_active?: boolean
  }
  providers: AIProvider[]
}

// 통합 API 호출 함수 (새로운 단일 엔드포인트 사용)
const fetchPageInitData = async (): Promise<PageInitData> => {
  try {
    const headers = createSharedApiHeaders(true)

    // 새로운 통합 API 호출
    const response = await apiFetch('/api/v1/homepage/init', {
      headers
    })

    if (!response.ok) {
      // 백엔드 연결 실패 시 로컬 데이터로 폴백
      console.warn(`Homepage Init API 연결 실패 (${response.status}), 로컬 모드로 전환`)
      throw new Error(`Backend connection failed: ${response.status}`)
    }

    const data = await response.json()

    return {
      config: data.config,
      providers: data.providers
    }
  } catch (error) {
    // 네트워크 에러나 연결 실패 시 로컬 데이터 사용
    console.warn('백엔드 서버 연결 실패, 로컬 모드로 전환:', error)
    throw error // React Query가 에러를 처리하도록 함
  }
}

// 로컬스토리지에서 즉시 사용 가능한 데이터 생성
const getLocalData = (): PageInitData => {
  const { githubToken, googleApiKey, upstageApiKey, selectedProvider } =
    getApiKeysFromStorage()
  const hasProviderKey =
    selectedProvider === 'gemini' ? !!googleApiKey : !!upstageApiKey
  const hasKeys = !!githubToken && hasProviderKey

  return {
    config: {
      keys_required: !hasKeys,
      use_local_storage: true,
      missing_keys: {
        github_token: !githubToken,
        google_api_key: selectedProvider === 'gemini' ? !googleApiKey : false,
        upstage_api_key: selectedProvider === 'upstage' ? !upstageApiKey : false,
      },
      development_mode_active: true // 로컬 데이터에서는 기본적으로 활성화
    },
    providers: [
      {
        id: 'upstage_solar',
        name: 'Upstage Solar Pro 3',
        model: 'solar-pro3',
        status: 'available',
        recommended: selectedProvider === 'upstage',
      },
      {
        id: 'google_gemini_flash',
        name: 'Google Gemini 2.0 Flash',
        model: 'gemini-2.0-flash',
        status: 'available',
        recommended: selectedProvider === 'gemini',
      },
    ]
  }
}

// 메인 Hook
export const usePageInitialization = () => {
  const [localData] = useState(() => getLocalData())

  // API 키 저장 상태를 추적하는 상태 추가
  const [hasStoredKeysState, setHasStoredKeysState] = useState(() =>
    hasRequiredApiKeys()
  )

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
    retry: 1, // 재시도 1번으로 줄여서 빠른 폴백
    retryDelay: 1000,
    // 에러 발생 시에도 로컬 데이터 사용하므로 silent 실패
    throwOnError: false,
    // 백그라운드에서 재시도하지 않음 (로컬 모드로 동작)
    refetchOnWindowFocus: false,
    refetchOnReconnect: true, // 네트워크 재연결 시에만 재시도
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

  useEffect(() => {
    setHasStoredKeysState(hasRequiredApiKeys(selectedAI))
  }, [selectedAI])

  const createApiHeaders = (
    includeApiKeys: boolean = false,
    aiProvider?: string
  ) =>
    createSharedApiHeaders({
      includeApiKeys,
      selectedAI: aiProvider ?? selectedAI,
    })

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
    isDevelopmentActive: effectiveData.config.development_mode_active ?? true,

    // 유틸리티
    hasStoredKeys: () => hasStoredKeysState,

    // API 키 상태를 수동으로 업데이트하는 함수 추가
    refreshStoredKeysState: () => {
      const newState = hasRequiredApiKeys(selectedAI)
      setHasStoredKeysState(newState)
      return newState
    },

    createApiHeaders
  }
}
