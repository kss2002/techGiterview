import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../utils/apiUtils'

interface RecentAnalysis {
  analysis_id: string
  repository_name: string
  repository_owner: string
  created_at: string
  tech_stack: string[]
  file_count: number
  primary_language: string
}

interface RecentReport {
  interview_id: string
  repository_name: string
  repository_owner: string
  overall_score: number
  completed_at: string
  duration_minutes: number
  questions_count: number
  answers_count: number
  category_scores: Record<string, number>
  difficulty_level: string
}

interface QuickAccessData {
  recent_analyses: RecentAnalysis[]
  recent_reports: RecentReport[]
}

interface UseQuickAccessDataResult {
  data: QuickAccessData
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export const useQuickAccessData = (limit: number = 3): UseQuickAccessDataResult => {
  const [data, setData] = useState<QuickAccessData>({ 
    recent_analyses: [], 
    recent_reports: [] 
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // 병렬로 두 API 호출 (Vite 프록시 사용)
      const [analysesResponse, reportsResponse] = await Promise.all([
        apiFetch(`/api/v1/repository/analysis/recent?limit=${limit}`),
        apiFetch(`/api/v1/reports/recent?limit=${limit}`)
      ])

      // 응답 처리
      const analysesResult = await analysesResponse.json()
      const reportsResult = await reportsResponse.json()

      // 중복 제거 로직 추가
      const analyses = analysesResult.success ? analysesResult.data : []
      const reports = reportsResult.success ? reportsResult.data.reports : []
      
      const uniqueAnalyses = analyses.filter((analysis: RecentAnalysis, index: number, arr: RecentAnalysis[]) => 
        arr.findIndex(a => a.analysis_id === analysis.analysis_id) === index
      )
      
      const uniqueReports = reports.filter((report: RecentReport, index: number, arr: RecentReport[]) => 
        arr.findIndex(r => r.interview_id === report.interview_id) === index
      )

      // 데이터 설정
      setData({
        recent_analyses: uniqueAnalyses,
        recent_reports: uniqueReports
      })

      console.log('[QUICK_ACCESS_HOOK] 데이터 로드 완료:', {
        원본_analyses: analyses.length,
        중복제거_후_analyses: uniqueAnalyses.length,
        원본_reports: reports.length,
        중복제거_후_reports: uniqueReports.length
      })
      
      // 중복이 발견된 경우 경고 로그
      if (analyses.length !== uniqueAnalyses.length) {
        console.warn('[QUICK_ACCESS_HOOK] 중복 분석 데이터 발견!', {
          원본: analyses.map(a => a.analysis_id),
          중복제거후: uniqueAnalyses.map(a => a.analysis_id)
        })
      }

    } catch (error) {
      console.error('[QUICK_ACCESS_HOOK] 데이터 로딩 오류:', error)
      setError('데이터를 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [limit])

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    isLoading,
    error,
    refetch: fetchData
  }
}

// Local Storage를 활용한 캐싱 버전
export const useQuickAccessDataWithCache = (limit: number = 3): UseQuickAccessDataResult => {
  const [data, setData] = useState<QuickAccessData>(() => {
    // 초기 데이터를 localStorage에서 로드
    try {
      const cached = localStorage.getItem('quick-access-data')
      if (cached) {
        const parsed = JSON.parse(cached)
        const cacheTime = localStorage.getItem('quick-access-data-time')
        const now = Date.now()
        
        // 5분 이내의 캐시만 사용
        if (cacheTime && (now - parseInt(cacheTime)) < 5 * 60 * 1000) {
          return parsed
        }
      }
    } catch (error) {
      console.warn('[QUICK_ACCESS_CACHE] 캐시 로드 실패:', error)
    }
    
    return { recent_analyses: [], recent_reports: [] }
  })
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [analysesResponse, reportsResponse] = await Promise.all([
        apiFetch(`/api/v1/repository/analysis/recent?limit=${limit}`),
        apiFetch(`/api/v1/reports/recent?limit=${limit}`)
      ])

      const analysesResult = await analysesResponse.json()
      const reportsResult = await reportsResponse.json()

      // 중복 제거 로직 추가
      const analyses = analysesResult.success ? analysesResult.data : []
      const reports = reportsResult.success ? reportsResult.data.reports : []
      
      const uniqueAnalyses = analyses.filter((analysis: RecentAnalysis, index: number, arr: RecentAnalysis[]) => 
        arr.findIndex(a => a.analysis_id === analysis.analysis_id) === index
      )
      
      const uniqueReports = reports.filter((report: RecentReport, index: number, arr: RecentReport[]) => 
        arr.findIndex(r => r.interview_id === report.interview_id) === index
      )

      const newData = {
        recent_analyses: uniqueAnalyses,
        recent_reports: uniqueReports
      }

      setData(newData)

      // localStorage에 캐시 저장
      try {
        localStorage.setItem('quick-access-data', JSON.stringify(newData))
        localStorage.setItem('quick-access-data-time', Date.now().toString())
      } catch (cacheError) {
        console.warn('[QUICK_ACCESS_CACHE] 캐시 저장 실패:', cacheError)
      }

    } catch (error) {
      console.error('[QUICK_ACCESS_HOOK] 데이터 로딩 오류:', error)
      setError('데이터를 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    isLoading,
    error,
    refetch: fetchData
  }
}