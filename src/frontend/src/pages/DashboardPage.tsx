import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  LayoutDashboard,
  Github,
  Lightbulb,
  Tag,
  FileText,
  Star,
  GitFork,
  Code,
  Clock,
  CheckCircle,
  ArrowRight,
  Folder,
  File,
  ChevronRight,
  Search,
  Minus,
  Play,
  RefreshCw, // Added RefreshCw
  BarChart3,
  FileCode,
  Database,
  Image,
  Archive,
  Globe,
  Settings,
  BookOpen,
  Cpu,
  Monitor,
  Smartphone,
  Palette,
  Zap,
  Shield,
  Users,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  Info,
  Terminal,
  ZoomIn,
  ZoomOut,
  Maximize
} from 'lucide-react'
import { FileContentModal } from '../components/FileContentModal'
import { CriticalFilesPreview } from '../components/CriticalFilesPreview'
import CodeGraphViewer from '../components/CodeGraphViewer'
import { apiFetch } from '../utils/apiUtils'
import { createApiHeaders, getApiKeysFromStorage } from '../utils/apiHeaders'
import { formatQuestionForDisplay } from '../utils/questionFormatter'
import './DashboardPage-CLEAN.css'

// TypeScript 타입 확장
declare global {
  interface Window {
    cssDebugObserver?: MutationObserver
  }
}

interface RepositoryInfo {
  name: string
  owner: string
  url?: string
  description: string | null
  language: string | null
  stars: number
  forks: number
  size: number
  topics: string[]
  default_branch: string
}

interface FileInfo {
  path: string
  type: string
  size: number
  content?: string
  importance?: 'high' | 'medium' | 'low'
}

// SmartFileAnalysis 인터페이스 정의 (CriticalFilesPreview와 동일)
interface SmartFileAnalysis {
  file_path: string
  importance_score: number
  reasons: string[]
  metrics: {
    structural_importance: number
    dependency_centrality: number
    churn_risk: number
    complexity_score: number
  }
  category: 'critical' | 'important' | 'moderate' | 'low'
  rank: number
}

interface AnalysisResult {
  success: boolean
  analysis_id: string
  repo_info: RepositoryInfo
  tech_stack: Record<string, number>
  key_files: FileInfo[]
  summary: string
  recommendations: string[]
  created_at: string
  smart_file_analysis?: {
    critical_files: SmartFileAnalysis[]
    importance_distribution?: {
      mean: number
      median: number
      std_dev: number
      min: number
      max: number
    }
    categorized_files?: {
      critical: string[]
      important: string[]
      moderate: string[]
      low: string[]
    }
    summary?: {
      total_files_analyzed: number
      critical_files_count: number
      important_files_count: number
      average_importance: number
      highest_importance: number
    }
  }
}

interface Question {
  id: string
  type: string
  question: string
  question_headline?: string
  question_details_markdown?: string
  question_has_details?: boolean
  difficulty: string
  context?: string
  time_estimate?: string
  code_snippet?: {
    content: string
    language: string
    file_path: string
    complexity: number
    has_real_content?: boolean
    content_unavailable_reason?: string
  }
  expected_answer_points?: string[]
  technology?: string
  pattern?: string
  // 서브 질문 관련 필드
  parent_question_id?: string
  sub_question_index?: number
  total_sub_questions?: number
  is_compound_question?: boolean
  // 파일 연관성 필드
  source_file?: string
  importance?: 'high' | 'medium' | 'low'
  generated_by?: string
}

interface FileTreeNode {
  name: string
  path: string
  type: string // "file" or "dir"
  size?: number
  children?: FileTreeNode[]
}

const sanitizeQuestions = (items: Question[]): Question[] => {
  const sanitized = items.map((question) => {
    const formatted = formatQuestionForDisplay(question)
    return {
      ...question,
      question: formatted.normalizedQuestion,
      question_headline: formatted.headline || undefined,
      question_details_markdown: formatted.detailsMarkdown || undefined,
      question_has_details: formatted.hasDetails
    }
  })

  const deduped: Question[] = []
  const seen = new Set<string>()

  sanitized.forEach((question) => {
    const key = `${question.id}::${(question.question_headline || question.question || '').trim().toLowerCase()}`
    const normalizedKey = `${(question.question_headline || question.question || '').trim().toLowerCase()}::${(question.type || '').toLowerCase()}`
    if (seen.has(key) || seen.has(normalizedKey)) {
      return
    }
    seen.add(key)
    seen.add(normalizedKey)
    deduped.push(question)
  })

  return deduped
}

// 파일 확장자에 따른 React 아이콘 컴포넌트 반환
const getFileIcon = (filePath: string): React.ReactNode => {
  const extension = filePath.split('.').pop()?.toLowerCase()
  const fileName = filePath.split('/').pop()?.toLowerCase() || ''

  // 특수 파일명 먼저 처리
  if (fileName === 'dockerfile' || fileName.startsWith('dockerfile')) {
    return <Monitor className="file-icon file-icon-monitor" />
  }
  if (fileName === '.gitignore') {
    return <Github className="file-icon file-icon-github" />
  }
  if (fileName.startsWith('readme')) {
    return <BookOpen className="file-icon file-icon-book" />
  }
  if (fileName === 'license' || fileName.startsWith('license')) {
    return <Shield className="file-icon file-icon-shield" />
  }
  if (fileName === 'package.json') {
    return <Settings className="file-icon file-icon-settings" />
  }
  if (fileName === 'package-lock.json' || fileName === 'yarn.lock') {
    return <Archive className="file-icon file-icon-archive" />
  }

  // 확장자별 처리
  switch (extension) {
    case 'js':
    case 'jsx':
      return <FileCode className="file-icon file-icon-javascript" />
    case 'ts':
    case 'tsx':
      return <FileCode className="file-icon file-icon-typescript" />
    case 'vue':
      return <FileCode className="file-icon file-icon-vue" />
    case 'py':
    case 'pyw':
    case 'pyx':
      return <Cpu className="file-icon file-icon-python" />
    case 'java':
    case 'kt':
    case 'scala':
      return <Cpu className="file-icon file-icon-java" />
    case 'html':
    case 'htm':
      return <Globe className="file-icon file-icon-html" />
    case 'css':
    case 'scss':
    case 'sass':
    case 'less':
      return <Palette className="file-icon file-icon-css" />
    case 'json':
    case 'yaml':
    case 'yml':
    case 'toml':
    case 'ini':
    case 'conf':
    case 'config':
      return <Settings className="file-icon file-icon-config" />
    case 'md':
      return <FileText className="file-icon file-icon-markdown" />
    case 'txt':
      return <FileText className="file-icon file-icon-text" />
    case 'pdf':
      return <File className="file-icon file-icon-pdf" />
    case 'sql':
    case 'db':
    case 'sqlite':
      return <Database className="file-icon file-icon-database" />
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
      return <Image className="file-icon file-icon-image" />
    case 'zip':
    case 'tar':
    case 'gz':
      return <Archive className="file-icon file-icon-archive" />
    default:
      return <File className="file-icon file-icon-default" />
  }
}

// 분석 목록을 위한 인터페이스 (QuickAccessSection과 동일)
interface RecentAnalysis {
  analysis_id: string
  repository_name: string
  repository_owner: string
  created_at: string
  tech_stack: string[]
  file_count: number
  primary_language: string
}

export const DashboardPage: React.FC = () => {
  const SIDEBAR_STORAGE_KEY = 'techgiterview_dashboard_sidebar_width'
  const SIDEBAR_DEFAULT_WIDTH = 240
  const SIDEBAR_MIN_WIDTH = 200
  const SIDEBAR_MAX_WIDTH = 420

  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [questions, setQuestionsInternal] = useState<Question[]>([])
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false)
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false)
  const [questionsGenerated, setQuestionsGenerated] = useState(false)

  // Graph State
  const [graphData, setGraphData] = useState<any>(null)
  const [isLoadingGraph, setIsLoadingGraph] = useState(false)

  // 전체 분석 목록을 위한 상태
  const [allAnalyses, setAllAnalyses] = useState<RecentAnalysis[]>([])
  const [isLoadingAllAnalyses, setIsLoadingAllAnalyses] = useState(false)

  // 질문 상태 변경 추적을 위한 래퍼 함수
  const setQuestions = (newQuestions: Question[]) => {
    const sanitizedQuestions = sanitizeQuestions(newQuestions || [])
    console.log('[Questions State] Updating questions state:', {
      previousCount: questions.length,
      newCount: sanitizedQuestions.length,
      timestamp: new Date().toISOString(),
      stackTrace: new Error().stack?.split('\n').slice(1, 4).join('\n')
    })
    setQuestionsInternal(sanitizedQuestions)
    console.log('[Questions State] Questions state updated:', sanitizedQuestions.length)
  }
  const [allFiles, setAllFiles] = useState<FileTreeNode[]>([])
  const [isLoadingAllFiles, setIsLoadingAllFiles] = useState(false)
  const [showAllFiles, setShowAllFiles] = useState(true)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredFiles, setFilteredFiles] = useState<FileTreeNode[]>([])
  const [isFileModalOpen, setIsFileModalOpen] = useState(false)
  const [selectedFilePath, setSelectedFilePath] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY)
      const parsed = saved ? parseInt(saved, 10) : SIDEBAR_DEFAULT_WIDTH
      return Number.isFinite(parsed) ? parsed : SIDEBAR_DEFAULT_WIDTH
    } catch {
      return SIDEBAR_DEFAULT_WIDTH
    }
  })
  const [isResizingSidebar, setIsResizingSidebar] = useState(false)
  const sidebarWidthRef = useRef(sidebarWidth)
  // 질문 카드 펼침/접기 상태 (Accordion)
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set())
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null)
  const [expandedCodeSnippets, setExpandedCodeSnippets] = useState<Set<string>>(new Set())
  const [activeMainTab, setActiveMainTab] = useState<'questions' | 'graph'>('questions')
  const [questionSearch, setQuestionSearch] = useState('')
  const [questionCategory, setQuestionCategory] = useState('all')
  const [questionDifficulty, setQuestionDifficulty] = useState('all')
  // CSS 클래스 기반 시스템에서는 강제 리렌더링 불필요
  const navigate = useNavigate()
  const { analysisId } = useParams<{ analysisId: string }>()

  // 컴포넌트 상태 추적 (개발 모드에서만)
  if (process.env.NODE_ENV === 'development') {
    console.log('[Dashboard] 렌더링:', {
      analysisId,
      hasResult: !!analysisResult,
      questionsCount: questions.length,
      error
    })
  }

  useEffect(() => {
    console.log('DashboardPage analysisId:', analysisId) // 디버깅용
    if (analysisId) {
      // URL 파라미터에서 분석 ID를 가져와서 API에서 데이터 로드
      loadAnalysisResult(analysisId)
    } else {
      // 분석 ID가 없으면 전체 분석 목록 표시
      console.log('No analysisId, showing all analyses')
      loadAllAnalyses()
    }
  }, [analysisId, navigate])

  // 파일 트리 정렬 완료 - 더 이상 복잡한 분석 불필요
  useEffect(() => {
    console.log("✅ 파일 트리 정렬 시스템이 성공적으로 단순화되었습니다.")
  }, [])

  useEffect(() => {
    sidebarWidthRef.current = sidebarWidth
  }, [sidebarWidth])

  useEffect(() => {
    if (!isResizingSidebar) return

    const handleMouseMove = (event: MouseEvent) => {
      const maxWidth = Math.min(SIDEBAR_MAX_WIDTH, window.innerWidth - 360)
      const nextWidth = Math.max(SIDEBAR_MIN_WIDTH, Math.min(event.clientX, maxWidth))
      setSidebarWidth(nextWidth)
      sidebarWidthRef.current = nextWidth
    }

    const handleMouseUp = () => {
      setIsResizingSidebar(false)
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(sidebarWidthRef.current))
      } catch {
        // ignore localStorage errors
      }
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizingSidebar])

  const startSidebarResize = (event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsResizingSidebar(true)
  }

  const resetSidebarWidth = () => {
    setSidebarWidth(SIDEBAR_DEFAULT_WIDTH)
    try {
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(SIDEBAR_DEFAULT_WIDTH))
    } catch {
      // ignore localStorage errors
    }
  }

  /**
   * ============================================
   * 통합 파일 트리 들여쓰기 시스템
   * ============================================
   * 
   * CSS 변수 기반 중앙 관리: design-tokens.css에서 --file-tree-indent-per-level로 통합 관리
   * CSS 클래스 기반 적용: .file-tree-depth-0 ~ .file-tree-depth-6 클래스로 깊이별 들여쓰기
   * 반응형 자동 처리: CSS 미디어 쿼리로 데스크톱(4px), 태블릿(3px), 모바일(2px) 자동 적용
   * DOM 조작 없음: React 인라인 스타일이나 useEffect DOM 조작 완전 제거
   * 성능 최적화: 불필요한 리렌더링, 윈도우 리사이즈 이벤트, 강제 업데이트 제거
   * 
   * 핵심 파일:
   * - design-tokens.css: CSS 변수 및 미디어 쿼리 정의
   * - DashboardPage.css: .file-tree-depth-* 클래스 정의  
   * - DashboardPage.tsx: getDepthClassName() 함수로 CSS 클래스 동적 할당
   */

  // 전체 분석 목록 로드 함수
  const loadAllAnalyses = async () => {
    console.log('[Dashboard] Loading all analyses...')
    setIsLoadingAllAnalyses(true)
    setError(null)

    try {
      const response = await apiFetch('/api/v1/repository/analysis/recent?limit=50') // 더 많은 결과 가져오기
      console.log('[Dashboard] All analyses response received:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('[Dashboard] All analyses data:', data)

      if (data.success) {
        setAllAnalyses(data.data || [])
        console.log(`[Dashboard] Loaded ${data.data?.length || 0} analyses`)
      } else {
        throw new Error('Failed to load analyses')
      }
    } catch (error) {
      console.error('[Dashboard] Error loading all analyses:', error)
      setError('분석 목록을 불러오는데 실패했습니다.')
      setAllAnalyses([])
    } finally {
      setIsLoadingAllAnalyses(false)
    }
  }

  const loadAnalysisResult = async (analysisId: string) => {
    console.log('[Dashboard] Starting loadAnalysisResult for ID:', analysisId)
    console.log('[Dashboard] API URL will be:', `/api/v1/repository/analysis/${analysisId}`)

    setIsLoadingAnalysis(true)
    setError(null)

    try {
      console.log('[Dashboard] Making fetch request...')
      const response = await apiFetch(`/api/v1/repository/analysis/${analysisId}`)
      console.log('[Dashboard] Response received:', {
        status: response.status,
        statusText: response.statusText,
        url: response.url,
        headers: Object.fromEntries(response.headers.entries())
      })

      if (response.status === 202) {
        // 분석이 아직 진행 중
        const result = await response.json()
        console.log('[Dashboard] ⏳ Analysis still in progress:', result)
        setError(`분석이 진행 중입니다. 상태: ${result.detail}`)
        return
      }

      if (!response.ok) {
        const errorText = await response.text()
        console.error('[Dashboard] API error response:', {
          status: response.status,
          statusText: response.statusText,
          errorText
        })
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const result = await response.json()
      console.log('[Dashboard] Analysis result loaded successfully:', {
        analysis_id: result.analysis_id,
        repo_name: result.repo_info?.name,
        repo_owner: result.repo_info?.owner,
        key_files_count: result.key_files?.length,
        tech_stack: Object.keys(result.tech_stack || {}),
        has_smart_analysis: !!result.smart_file_analysis
      })
      setAnalysisResult(result)

      // Load Graph Data
      fetchGraphData(result.analysis_id)

      // 자동으로 전체 파일 목록 로드
      try {
        const filesResponse = await apiFetch(`/api/v1/repository/analysis/${result.analysis_id}/all-files?max_depth=3&max_files=500`)
        if (filesResponse.ok) {
          const files = await filesResponse.json()
          setAllFiles(files)
          setFilteredFiles(files)
          setShowAllFiles(true)
          // 최상위 폴더만 펼치기 (스크롤 압박 해소)
          const topLevelFolders = new Set<string>()
          files.forEach((node: FileTreeNode) => {
            if (node.type === 'dir') {
              topLevelFolders.add(node.path)
            }
          })
          setExpandedFolders(topLevelFolders)
        }
      } catch (error) {
        console.error('Error loading all files:', error)
      }

      // 질문이 아직 생성되지 않았다면 자동 로드/생성
      if (!questionsGenerated) {
        console.log('[Dashboard] Auto-loading questions...')
        await loadOrGenerateQuestions(result)
      }
    } catch (error) {
      console.error('[Dashboard] Critical error loading analysis:', {
        error,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        errorStack: error instanceof Error ? error.stack : undefined,
        analysisId
      })
      setError(error instanceof Error ? error.message : 'Unknown error occurred')
    } finally {
      console.log('[Dashboard] Analysis loading finished, setting isLoadingAnalysis to false')
      setIsLoadingAnalysis(false)
    }
  }

  const fetchGraphData = async (id: string) => {
    setIsLoadingGraph(true)
    try {
      const res = await apiFetch(`/api/v1/repository/analysis/${id}/graph`)
      if (res.ok) {
        const data = await res.json()
        setGraphData(data)
      }
    } catch (e) {
      console.error("Failed to fetch graph data", e)
    } finally {
      setIsLoadingGraph(false)
    }
  }

  const loadOrGenerateQuestions = async (analysisToUse: AnalysisResult) => {
    console.log('[Questions] Starting loadOrGenerateQuestions for analysis:', analysisToUse.analysis_id)
    console.log('[Questions] Current questions state:', {
      questionsCount: questions.length,
      questionsGenerated,
      isLoadingQuestions
    })

    setIsLoadingQuestions(true)

    const waitForGeneratedQuestions = async (analysisId: string, maxAttempts: number = 12, delayMs: number = 5000) => {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        console.log(`[Questions] ⏳ Waiting for in-progress generation... (${attempt}/${maxAttempts})`)
        await new Promise((resolve) => setTimeout(resolve, delayMs))

        const pollResponse = await apiFetch(`/api/v1/questions/analysis/${analysisId}`, {
          method: 'GET',
          headers: createApiHeaders(false)
        })

        if (!pollResponse.ok) {
          continue
        }

        const pollResult = await pollResponse.json()
        if (pollResult.success && pollResult.questions && pollResult.questions.length > 0) {
          console.log('[Questions] ✅ In-progress generation completed during polling:', pollResult.questions.length)
          setQuestions(pollResult.questions)
          setQuestionsGenerated(true)
          return true
        }
      }

      return false
    }

    try {
      // 먼저 이미 생성된 질문이 있는지 확인
      const checkUrl = `/api/v1/questions/analysis/${analysisToUse.analysis_id}`
      console.log('[Questions] Fetching existing questions from:', checkUrl)

      const checkResponse = await apiFetch(checkUrl, {
        method: 'GET',
        headers: createApiHeaders(false) // 질문 조회는 API 키 불필요
      })
      console.log('[Questions] Check response received:', {
        status: checkResponse.status,
        statusText: checkResponse.statusText,
        ok: checkResponse.ok,
        url: checkResponse.url
      })

      if (checkResponse.ok) {
        const checkResult = await checkResponse.json()
        console.log('[Questions] Parsed check result:', {
          success: checkResult.success,
          questionsLength: checkResult.questions?.length || 0,
          questionsExists: !!checkResult.questions,
          analysisId: checkResult.analysis_id,
          error: checkResult.error
        })

        if (checkResult.success && checkResult.questions && checkResult.questions.length > 0) {
          // 이미 생성된 질문이 있음
          console.log('[Questions] Found existing questions, setting state:', checkResult.questions.length)
          setQuestions(checkResult.questions)
          setQuestionsGenerated(true)
          console.log('[Questions] Questions state updated successfully')
          return
        } else {
          console.log('[Questions] No existing questions found, will generate new ones')
        }
      } else {
        console.warn('[Questions] Check response not ok:', {
          status: checkResponse.status,
          statusText: checkResponse.statusText
        })
      }

      // 질문이 없으면 새로 생성
      console.log('[Questions] Generating new questions...')
      const generatePayload = {
        repo_url: `https://github.com/${analysisToUse.repo_info.owner}/${analysisToUse.repo_info.name}`,
        analysis_result: analysisToUse,
        question_type: "technical",
        difficulty: "medium"
      }
      console.log('[Questions] Generation payload:', generatePayload)

      const generateResponse = await apiFetch('/api/v1/questions/generate', {
        method: 'POST',
        headers: createApiHeaders(true), // API 키 포함하여 헤더 생성
        body: JSON.stringify(generatePayload)
      })

      console.log('[Questions] 📥 Generate response received:', {
        status: generateResponse.status,
        statusText: generateResponse.statusText,
        ok: generateResponse.ok
      })

      if (!generateResponse.ok) {
        const errorText = await generateResponse.text()
        console.error('[Questions] Generate response error:', errorText)

        // 백엔드에서 이미 생성 중인 경우(409)에는 폴링으로 완료 대기
        if (generateResponse.status === 409) {
          const recovered = await waitForGeneratedQuestions(analysisToUse.analysis_id)
          if (recovered) return
        }

        throw new Error(`질문 생성에 실패했습니다. (${generateResponse.status}: ${errorText})`)
      }

      const generateResult = await generateResponse.json()
      console.log('[Questions] Parsed generate result:', {
        success: generateResult.success,
        questionsLength: generateResult.questions?.length || 0,
        questionsExists: !!generateResult.questions,
        analysisId: generateResult.analysis_id,
        error: generateResult.error
      })

      if (generateResult.success) {
        console.log('[Questions] Generated questions successfully, setting state:', generateResult.questions?.length || 0)
        setQuestions(generateResult.questions || [])
        setQuestionsGenerated(true)
        console.log('[Questions] Generated questions state updated successfully')
      } else {
        console.error('[Questions] Generate result not successful:', generateResult.error)
        throw new Error(`질문 생성 실패: ${generateResult.error}`)
      }
    } catch (error) {
      console.error('[Questions] Critical error in loadOrGenerateQuestions:', {
        error,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        errorStack: error instanceof Error ? error.stack : undefined,
        analysisId: analysisToUse.analysis_id
      })
      // 질문 생성에 실패해도 대시보드는 표시
    } finally {
      console.log('[Questions] 🏁 loadOrGenerateQuestions finished, setting isLoadingQuestions to false')
      setIsLoadingQuestions(false)
    }
  }

  const regenerateQuestions = async () => {
    if (!analysisResult) return

    setIsLoadingQuestions(true)
    try {
      // 강제 재생성 옵션을 사용하여 질문 생성
      const response = await apiFetch('/api/v1/questions/generate', {
        method: 'POST',
        headers: createApiHeaders(true), // API 키 포함하여 헤더 생성
        body: JSON.stringify({
          repo_url: `https://github.com/${analysisResult.repo_info.owner}/${analysisResult.repo_info.name}`,
          analysis_result: analysisResult,
          question_type: "technical",
          difficulty: "medium",
          force_regenerate: true
        })
      })

      if (!response.ok) {
        if (response.status === 409) {
          // 이미 생성 중이면 기존 생성 완료를 기다린다.
          for (let attempt = 1; attempt <= 12; attempt++) {
            await new Promise((resolve) => setTimeout(resolve, 5000))
            const poll = await apiFetch(`/api/v1/questions/analysis/${analysisResult.analysis_id}`, {
              method: 'GET',
              headers: createApiHeaders(false)
            })
            if (!poll.ok) continue
            const pollResult = await poll.json()
            if (pollResult.success && pollResult.questions && pollResult.questions.length > 0) {
              setQuestions(pollResult.questions || [])
              setQuestionsGenerated(true)
              return
            }
          }
        }

        throw new Error('질문 재생성에 실패했습니다.')
      }

      const result = await response.json()
      if (result.success) {
        setQuestions(result.questions || [])
        setQuestionsGenerated(true)
      }
    } catch (error) {
      console.error('Error regenerating questions:', error)
      alert('질문 재생성에 실패했습니다.')
    } finally {
      setIsLoadingQuestions(false)
    }
  }

  const loadAllFiles = async () => {
    if (!analysisResult || !analysisId) return

    setIsLoadingAllFiles(true)
    try {
      const response = await apiFetch(`/api/v1/repository/analysis/${analysisId}/all-files?max_depth=3&max_files=500`)

      if (!response.ok) {
        throw new Error('전체 파일 목록을 불러올 수 없습니다.')
      }

      const files = await response.json()
      setAllFiles(files)
      setFilteredFiles(files)
      setShowAllFiles(true)
      setSearchTerm('')
    } catch (error) {
      console.error('Error loading all files:', error)
      alert('전체 파일 목록을 불러오는데 실패했습니다.')
    } finally {
      setIsLoadingAllFiles(false)
    }
  }

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFolders(newExpanded)
  }

  // 질문 카드 펼침/접기 토글
  const toggleQuestionExpand = (questionId: string) => {
    const newExpanded = new Set(expandedQuestions)
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId)
    } else {
      newExpanded.add(questionId)
    }
    setExpandedQuestions(newExpanded)
  }

  const toggleCodeSnippetExpand = (questionId: string) => {
    const next = new Set(expandedCodeSnippets)
    if (next.has(questionId)) {
      next.delete(questionId)
    } else {
      next.add(questionId)
    }
    setExpandedCodeSnippets(next)
  }

  const filterFiles = (nodes: FileTreeNode[], term: string): FileTreeNode[] => {
    if (!term) return nodes

    return nodes.reduce((filtered: FileTreeNode[], node) => {
      if (node.type === 'dir') {
        const filteredChildren = filterFiles(node.children || [], term)
        const hasMatchingChildren = filteredChildren.length > 0
        const nameMatches = node.name.toLowerCase().includes(term.toLowerCase())

        if (nameMatches || hasMatchingChildren) {
          filtered.push({
            ...node,
            children: filteredChildren
          })
        }
      } else {
        if (node.name.toLowerCase().includes(term.toLowerCase())) {
          filtered.push(node)
        }
      }
      return filtered
    }, [])
  }

  const handleSearch = (term: string) => {
    setSearchTerm(term)
    if (!term) {
      setFilteredFiles(allFiles)
    } else {
      const filtered = filterFiles(allFiles, term)
      setFilteredFiles(filtered)
      // 검색 시 모든 폴더 자동 확장
      const expandAll = new Set<string>()
      const expandAllFolders = (nodes: FileTreeNode[]) => {
        nodes.forEach(node => {
          if (node.type === 'dir') {
            expandAll.add(node.path)
            if (node.children) {
              expandAllFolders(node.children)
            }
          }
        })
      }
      expandAllFolders(filtered)
      setExpandedFolders(expandAll)
    }
  }

  const handleFileClick = (file: FileTreeNode) => {
    if (file.type === 'file') {
      setSelectedFilePath(file.path)
      setIsFileModalOpen(true)
    }
  }

  const closeFileModal = () => {
    setIsFileModalOpen(false)
    setSelectedFilePath('')
  }


  // 들여쓰기 시스템 완전 제거 - depth 관련 함수들 비활성화

  const renderFileTree = (nodes: FileTreeNode[], depth: number = 0): JSX.Element[] => {
    // 구조 개선된 파일 트리 렌더링 - 올바른 들여쓰기 적용

    return nodes.map((node, index) => {
      const nodeKey = node.path
      const isExpanded = expandedFolders.has(node.path)

      return (
        <React.Fragment key={nodeKey}>
          {/* 현재 노드 렌더링 */}
          <div
            className="file-tree-node"
          >
            {node.type === 'dir' ? (
              <button
                className="folder-toggle"
                onClick={() => toggleFolder(node.path)}
              >
                <ChevronRight className={`chevron-icon ${isExpanded ? 'rotated' : ''}`} />
                <Folder className="folder-icon" />
                <span className="folder-name">{node.name}</span>
              </button>
            ) : (
              <div
                className="file-item-tree"
                onClick={() => handleFileClick(node)}
              >
                {getFileIcon(node.name)}
                <span className={`file-name ${searchTerm && node.name.toLowerCase().includes(searchTerm.toLowerCase()) ? 'highlight' : ''}`}>
                  {node.name}
                </span>
                {node.size && (
                  <span className="file-size">{(node.size / 1024).toFixed(1)} KB</span>
                )}
              </div>
            )}
          </div>

          {/* 하위 폴더가 있고 확장된 경우에만 렌더링 */}
          {node.type === 'dir' && isExpanded && node.children && (
            <div className="file-tree-children">
              {renderFileTree(node.children, depth + 1)}
            </div>
          )}
        </React.Fragment>
      )
    })
  }

  const startInterview = async () => {
    if (!analysisResult) return

    // 질문이 로드되지 않았으면 먼저 로드
    if (questions.length === 0) {
      console.log('질문이 없습니다. 질문을 먼저 생성합니다.')
      await loadOrGenerateQuestions(analysisResult)
      if (questions.length === 0) {
        throw new Error('질문 생성에 실패했습니다.')
      }
    }

    console.log('면접 시작 요청:', {
      repo_url: `https://github.com/${analysisResult.repo_info.owner}/${analysisResult.repo_info.name}`,
      analysis_id: analysisResult.analysis_id,
      question_ids: questions.map(q => q.id),
      questions_count: questions.length
    })

    try {
      // API 키 헤더 포함하여 면접 시작 요청
      const apiHeaders = createApiHeaders(true)
      const { githubToken, googleApiKey, upstageApiKey, selectedProvider } = getApiKeysFromStorage()
      console.log('[DASHBOARD] 면접 시작 요청 헤더:', JSON.stringify(apiHeaders, null, 2))
      console.log('[DASHBOARD] localStorage 키 확인:', {
        githubToken: githubToken ? '설정됨' : '없음',
        googleApiKey: googleApiKey ? '설정됨' : '없음',
        upstageApiKey: upstageApiKey ? '설정됨' : '없음',
        selectedProvider
      })

      const response = await apiFetch('/api/v1/interview/start', {
        method: 'POST',
        headers: apiHeaders,
        body: JSON.stringify({
          repo_url: `https://github.com/${analysisResult.repo_info.owner}/${analysisResult.repo_info.name}`,
          analysis_id: analysisResult.analysis_id,
          question_ids: questions.map(q => q.id)
        })
      })

      console.log('[DASHBOARD] 면접 시작 응답 상태:', response.status, response.statusText)

      if (!response.ok) {
        throw new Error('면접 시작에 실패했습니다.')
      }

      const result = await response.json()
      if (result.success) {
        navigate(`/dashboard/${analysisResult.analysis_id}/interview/${result.data.interview_id}`)
      }
    } catch (error) {
      console.error('Error starting interview:', error)
      alert('면접 시작에 실패했습니다.')
    }
  }

  const getDifficultyClass = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
      case 'beginner':
      case 'low':
        return 'difficulty-easy'
      case 'medium':
      case 'intermediate':
      case 'normal':
        return 'difficulty-medium'
      case 'hard':
      case 'advanced':
      case 'high':
        return 'difficulty-hard'
      default: return 'difficulty-default'
    }
  }

  const filteredQuestions = questions.filter(q => {
    const matchSearch = !questionSearch ||
      (q.question_headline || q.question || '').toLowerCase().includes(questionSearch.toLowerCase())
    const matchCat = questionCategory === 'all' ||
      (q.type || '').toLowerCase() === questionCategory.toLowerCase()
    const matchDiff = questionDifficulty === 'all' ||
      getDifficultyClass(q.difficulty) === `difficulty-${questionDifficulty}`
    return matchSearch && matchCat && matchDiff
  })

  const getCategoryIcon = (category: string): React.ReactNode => {
    if (!category) return <Code className="category-icon category-icon-default" />
    switch (category.toLowerCase()) {
      case 'technical':
        return <Terminal className="category-icon category-icon-technical" />
      case 'architectural':
        return <Monitor className="category-icon category-icon-architectural" />
      case 'scenario':
        return <MessageSquare className="category-icon category-icon-scenario" />
      case 'algorithm':
        return <Zap className="category-icon category-icon-algorithm" />
      case 'data-structure':
        return <Database className="category-icon category-icon-datastructure" />
      case 'system-design':
        return <TrendingUp className="category-icon category-icon-systemdesign" />
      case 'code-review':
        return <CheckCircle className="category-icon category-icon-codereview" />
      case 'best-practices':
        return <Star className="category-icon category-icon-bestpractices" />
      case 'debugging':
        return <AlertTriangle className="category-icon category-icon-debugging" />
      default:
        return <Code className="category-icon category-icon-default" />
    }
  }

  // key_files를 smart_file_analysis 형태로 변환하는 헬퍼 함수
  const convertKeyFilesToSmartAnalysis = (keyFiles: FileInfo[]): SmartFileAnalysis[] => {
    return keyFiles.slice(0, 12).map((file, index) => ({
      file_path: file.path || 'unknown-file',
      importance_score: file.importance === 'high' ? 0.9 - (index * 0.05) : 0.7 - (index * 0.05),
      reasons: [
        file.importance === 'high' ? '높은 중요도로 분류된 핵심 파일' : '중요 파일로 선정',
        file.size > 10000 ? '대용량 파일로 핵심 로직 포함 추정' : '프로젝트 구조상 중요 위치',
        getFileTypeReason(file.path)
      ].filter(Boolean),
      metrics: {
        structural_importance: file.importance === 'high' ? 0.9 : 0.7,
        dependency_centrality: 0.6 + (Math.random() * 0.3),
        churn_risk: 0.4 + (Math.random() * 0.4),
        complexity_score: file.size > 5000 ? 0.7 : 0.4
      },
      category: file.importance === 'high' ? 'critical' : 'important',
      rank: index + 1
    }))
  }

  // 파일 경로 기반 선정 이유 생성
  const getFileTypeReason = (filePath: string): string => {
    const fileName = filePath.split('/').pop()?.toLowerCase() || ''
    const extension = fileName.split('.').pop()?.toLowerCase() || ''

    if (fileName === 'package.json') return '프로젝트 설정 및 의존성 관리 파일'
    if (fileName === 'readme.md') return '프로젝트 문서화 및 가이드 파일'
    if (fileName.includes('config') || fileName.includes('settings')) return '프로젝트 설정 파일'
    if (extension === 'ts' || extension === 'tsx') return 'TypeScript 핵심 소스 파일'
    if (extension === 'js' || extension === 'jsx') return 'JavaScript 핵심 소스 파일'
    if (extension === 'py') return 'Python 핵심 소스 파일'
    if (fileName.includes('main') || fileName.includes('index')) return '애플리케이션 진입점 파일'
    return '프로젝트 핵심 구성 요소'
  }

  // 질문을 그룹화하는 함수
  const groupQuestions = (questions: Question[]) => {
    const groups: { [key: string]: Question[] } = {}
    const standalone: Question[] = []

    questions.forEach(question => {
      if (question.parent_question_id) {
        // 서브 질문인 경우
        if (!groups[question.parent_question_id]) {
          groups[question.parent_question_id] = []
        }
        groups[question.parent_question_id].push(question)
      } else {
        // 독립 질문인 경우
        standalone.push(question)
      }
    })

    // 서브 질문들을 인덱스 순으로 정렬
    Object.keys(groups).forEach(parentId => {
      groups[parentId].sort((a, b) => (a.sub_question_index || 0) - (b.sub_question_index || 0))
    })

    return { groups, standalone }
  }

  // 로딩 상태
  if (isLoadingAnalysis || isLoadingAllAnalyses) {
    console.log('[Dashboard] Rendering loading state')
    return (
      <div className="dashboard-loading">
        <div className="loading-content">
          <div className="progress-container">
            <div className="spinner-large"></div>
            <div className="progress-info">
              <h3 className="progress-title">
                {analysisId ? '📊 분석 결과 로딩 중' : '📋 분석 목록 로딩 중'}
              </h3>
              <div className="progress-steps">
                <div className="progress-step active">
                  <div className="step-indicator"></div>
                  <span>저장소 정보 조회</span>
                </div>
                <div className="progress-step">
                  <div className="step-indicator"></div>
                  <span>파일 구조 분석</span>
                </div>
                <div className="progress-step">
                  <div className="step-indicator"></div>
                  <span>AI 질문 생성</span>
                </div>
              </div>
              <p className="progress-time">⏱️ 예상 소요 시간: 1~3분</p>
              <p className="progress-hint">큰 저장소일수록 더 오래 걸릴 수 있습니다.</p>
              <button
                className="btn btn-outline btn-cancel"
                onClick={() => navigate('/')}
              >
                취소하고 홈으로
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }


  // analysisId가 없는 경우 - 분석 목록 표시
  if (!analysisId) {
    console.log('[Dashboard] Rendering analyses list')
    return (
      <div
        className={`dashboard-page dx-dark ${isResizingSidebar ? 'sidebar-resizing' : ''}`}
        style={{ ['--dashboard-sidebar-width' as any]: `${sidebarWidth}px` }}
      >
        <div className="dashboard-header">
          <div className="header-content">
            <h1>
              <LayoutDashboard className="section-icon" />
              전체 분석 결과
            </h1>
            <p className="repo-url">지금까지 분석한 모든 GitHub 저장소를 확인하세요</p>
            <p className="analysis-id">총 {allAnalyses.length}개의 분석 결과가 있습니다</p>
          </div>
        </div>

        <div className="dashboard-content">

          {/* 검색 및 정렬 */}
          <div className="dashboard-filters">
            <div className="search-container">
              <Search className="search-icon" />
              <input
                type="text"
                placeholder="저장소 이름으로 검색..."
                className="search-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {(() => {
            // 검색어로 필터링
            const filteredAnalyses = allAnalyses.filter(analysis =>
              searchTerm === '' ||
              `${analysis.repository_owner}/${analysis.repository_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
              analysis.primary_language?.toLowerCase().includes(searchTerm.toLowerCase())
            )

            return filteredAnalyses.length === 0 && !error ? (
              <div className="analyses-empty">
                <div className="empty-state">
                  <LayoutDashboard className="empty-icon" />
                  <h3>{searchTerm ? '검색 결과가 없습니다' : '분석 결과가 없습니다'}</h3>
                  <p>{searchTerm ? `"${searchTerm}"에 해당하는 저장소가 없습니다` : 'GitHub 저장소를 분석해보세요!'}</p>
                  <button onClick={() => searchTerm ? setSearchTerm('') : navigate('/')} className="btn btn-primary">
                    {searchTerm ? '검색 초기화' : '🏠 홈으로 가기'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="analyses-grid">
                {filteredAnalyses.map((analysis) => (
                  <div
                    key={analysis.analysis_id}
                    className="card analysis-card"
                    onClick={() => navigate(`/dashboard/${analysis.analysis_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && navigate(`/dashboard/${analysis.analysis_id}`)}
                  >
                    <div className="analysis-header">
                      <div className="repo-info">
                        <Github className="repo-icon" />
                        <h3>{analysis.repository_owner}/{analysis.repository_name}</h3>
                      </div>
                      <div className="analysis-meta">
                        <div className="analysis-date">
                          <Clock className="date-icon" />
                          <span>{new Date(analysis.created_at).toLocaleDateString('ko-KR', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}</span>
                        </div>
                      </div>
                    </div>

                    <div className="analysis-content">
                      <div className="analysis-details">
                        <div className="detail-item">
                          <Code className="detail-icon" />
                          <span className="detail-label">주언어</span>
                          <span className="detail-value">{analysis.primary_language}</span>
                        </div>
                        <div className="detail-item">
                          <FileText className="detail-icon" />
                          <span className="detail-label">파일 수</span>
                          <span className="detail-value">{analysis.file_count}개</span>
                        </div>
                      </div>

                      <div className="tech-stack-section">
                        <h4 className="tech-stack-title">기술 스택</h4>
                        <div className="tech-stack">
                          {analysis.tech_stack.slice(0, 4).map((tech, idx) => (
                            <span key={idx} className="tech-tag">{tech}</span>
                          ))}
                          {analysis.tech_stack.length > 4 && (
                            <span className="tech-more">+{analysis.tech_stack.length - 4}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="analysis-footer">
                      <div className="analysis-actions">
                        <ArrowRight className="action-icon" />
                        <span>상세 분석 보기</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
          })()}
        </div>
      </div>
    )
  }

  // 분석 결과가 없거나 오류가 있는 경우 (특정 analysisId가 있을 때만)
  if (!analysisResult || error) {
    console.log('[Dashboard] Rendering error state:', {
      hasAnalysisResult: !!analysisResult,
      error,
      analysisId
    })
    return (
      <div className="dashboard-error">
        <div className="error-content">
          <h2>{error ? '오류 발생' : '분석 결과를 찾을 수 없습니다'}</h2>
          <p>분석 ID: <code>{analysisId}</code></p>
          {error ? (
            <p className="error-message">오류: {error}</p>
          ) : (
            <p>분석이 완료되지 않았거나 잘못된 ID일 수 있습니다.</p>
          )}
          <div className="error-actions">
            <button onClick={() => navigate('/')} className="btn btn-outline">
              🏠 홈으로 돌아가기
            </button>
            <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
              📊 전체 분석 보기
            </button>
            <button
              onClick={() => {
                setError(null)
                if (analysisId) loadAnalysisResult(analysisId)
              }}
              className="btn btn-ghost"
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    )
  }

  console.log('[Dashboard] Rendering main dashboard content')

  return (
    <div
      className={`dashboard-page dx-dark ${isResizingSidebar ? 'sidebar-resizing' : ''}`}
      style={{ ['--dashboard-sidebar-width' as any]: `${sidebarWidth}px` }}
    >
      <div className="dashboard-header layout-fixed-header">
        <div className="header-content">
          <h1>
            <LayoutDashboard className="inline-block w-8 h-8 mr-3" />
            {analysisResult.repo_info.owner} / {analysisResult.repo_info.name}
            {analysisResult.repo_info.language && (
              <span className="header-lang-badge">{analysisResult.repo_info.language}</span>
            )}
            <span className="header-stat"><Star className="section-icon compact" />{analysisResult.repo_info.stars.toLocaleString()}</span>
            <span className="header-stat"><GitFork className="section-icon compact" />{analysisResult.repo_info.forks.toLocaleString()}</span>
          </h1>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-primary interview-cta"
            onClick={startInterview}
            disabled={isLoadingQuestions || questions.length === 0}
          >
            <Play className="btn-icon" />
            {isLoadingQuestions ? '질문 로딩 중...' : '면접 시작하기'}
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* 좌측 사이드바 (25%) */}
        <aside className="dashboard-sidebar layout-fixed-sidebar">
          {/* 저장소 정보 */}
          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <Github className="section-icon" /> 저장소 정보
            </div>
            <div className="sidebar-section-content">
              <div className="repo-details">
                <h3 className="repo-title">{analysisResult.repo_info.owner}/{analysisResult.repo_info.name}</h3>
                <p className="repo-description">{analysisResult.repo_info.description}</p>
                <div className="repo-stats">
                  <div className="stat">
                    <Star className="section-icon compact" />
                    <span className="stat-value">{analysisResult.repo_info.stars.toLocaleString()}</span>
                    <span className="stat-label">Stars</span>
                  </div>
                  <div className="stat">
                    <GitFork className="section-icon compact" />
                    <span className="stat-value">{analysisResult.repo_info.forks.toLocaleString()}</span>
                    <span className="stat-label">Forks</span>
                  </div>
                  <div className="stat">
                    <Code className="section-icon compact" />
                    <span className="stat-value">{analysisResult.repo_info.language}</span>
                    <span className="stat-label">Language</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 주요 파일 트리 - 사이드바로 이동 */}
          <div className="sidebar-section sidebar-section-grow">
            <div className="sidebar-section-header">
              <FileText className="section-icon" /> 주요 파일
              <div className="file-actions file-actions-right">
                {!showAllFiles && (
                  <button
                    className="btn btn-ghost btn-xs"
                    onClick={loadAllFiles}
                    disabled={isLoadingAllFiles}
                  >
                    {isLoadingAllFiles ? '...' : '전체'}
                  </button>
                )}
              </div>
            </div>

            <div className="sidebar-section-content sidebar-section-content-nopad">
              {!showAllFiles ? (
                <div className="files-loading files-loading-pad">
                  <div className="spinner"></div>
                  <p>불러오는 중...</p>
                </div>
              ) : (
                <div className="all-files-container">
                  {isLoadingAllFiles ? (
                    <div className="files-loading files-loading-pad">
                      <div className="spinner"></div>
                      <p>로딩 중...</p>
                    </div>
                  ) : (
                    <div className="file-tree">
                      {allFiles.length > 0 ? (
                        <>
                          <div className="file-tree-header">
                            <div className="file-tree-controls mb-2">
                              <div className="file-search-wrapper">
                                <Search className="section-icon file-search-icon" />
                                <input
                                  type="text"
                                  placeholder="검색..."
                                  value={searchTerm}
                                  onChange={(e) => handleSearch(e.target.value)}
                                  className="form-input form-input-sm w-full file-search-input"
                                />
                              </div>
                            </div>
                          </div>
                          <div className="file-tree-content px-2 pb-2">
                            {renderFileTree(searchTerm ? filteredFiles : allFiles)}
                          </div>
                        </>
                      ) : (
                        <p className="no-files p-4">파일을 불러올 수 없습니다.</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          <div
            className={`sidebar-resize-handle ${isResizingSidebar ? 'active' : ''}`}
            role="separator"
            aria-orientation="vertical"
            aria-label="사이드바 너비 조절"
            title="드래그하여 사이드바 너비 조절 (더블클릭: 기본값)"
            onMouseDown={startSidebarResize}
            onDoubleClick={resetSidebarWidth}
          />
        </aside>

        {/* 우측 메인 콘텐츠 (75%) */}
        <main className="dashboard-main layout-fixed-main">
          {/* Stats Bar */}
          <div className="stats-bar">
            {/* Tech Stack */}
            <div className="stat-card">
              <div className="stat-card-title">Tech Stack</div>
              <div className="tech-stack-mini">
                {Object.entries(analysisResult.tech_stack || {})
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 3)
                  .map(([tech, score], i) => {
                    const colors = ['#3b82f6', '#3fb950', '#d29922']
                    return (
                      <div key={i} className="tech-mini-row">
                        <span className="tech-mini-name">{tech}</span>
                        <div className="tech-mini-bar-track">
                          <div className="tech-mini-bar-fill" style={{ width: `${Math.max(4, score * 100)}%`, background: colors[i] }} />
                        </div>
                        <span className="tech-mini-pct">{(score * 100).toFixed(0)}%</span>
                      </div>
                    )
                  })}
              </div>
            </div>
            {/* Questions */}
            <div className="stat-card">
              <div className="stat-card-title">Questions</div>
              <div className="stat-card-value accent">{questions.length}</div>
              <div className="stat-card-sub">
                {Object.entries(
                  questions.reduce((acc: Record<string, number>, q) => {
                    const t = (q.type || 'Other').slice(0, 8)
                    acc[t] = (acc[t] || 0) + 1
                    return acc
                  }, {})
                ).slice(0, 3).map(([t, c]) => `${t}: ${c}`).join(' · ')}
              </div>
            </div>
            {/* Files */}
            <div className="stat-card">
              <div className="stat-card-title">Key Files</div>
              <div className="stat-card-value accent">{analysisResult.key_files?.length || 0}</div>
              <div className="stat-card-sub">{analysisResult.repo_info.language} · {analysisResult.repo_info.size.toLocaleString()} KB</div>
            </div>
            {/* Recommendations */}
            <div className="stat-card">
              <div className="stat-card-title">Insights</div>
              <div className="stat-card-value accent">{analysisResult.recommendations?.length || 0}</div>
              <div className="stat-card-sub">개선 제안 항목</div>
              <div className="mini-progress-track">
                <div className="mini-progress-fill" style={{ width: '60%', background: '#3fb950' }} />
              </div>
            </div>
          </div>

          {/* 1. Project Health Row */}
          <div className="grid-cols-2 project-health-row">
            {/* Tech Stack */}
            <div className="card-premium">
              <div className="card-header card-header-compact">
                <h2><Tag className="section-icon" /> 기술 스택</h2>
              </div>
              <div className="tech-stack-grid tech-stack-grid-compact">
                {Object.entries(analysisResult.tech_stack || {})
                  .sort(([, a], [, b]) => b - a)
                  .map(([tech, score], index) => (
                    <div key={index} className="tech-stack-item">
                      <div className="tech-tag tech-tag-compact">
                        <span className="tech-tag-name">{tech}</span>
                        <span className="tech-tag-value">{(score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="tech-progress-track">
                        <div className="tech-progress-fill" style={{ width: `${Math.max(4, score * 100)}%` }} />
                      </div>
                    </div>
                  ))
                }
              </div>
            </div>

            {/* Suggestions */}
            <div className="card-premium">
              <div className="card-header card-header-compact">
                <h2><CheckCircle className="section-icon section-icon-success" /> 개선 제안</h2>
              </div>
              <div className="card-body card-body-compact">
                <div className="recommendations-list">
                  {analysisResult.recommendations.length > 0 ? (
                    analysisResult.recommendations.slice(0, 3).map((recommendation, index) => (
                      <div key={index} className="recommendation-item recommendation-item-compact">
                        <ArrowRight className="section-icon section-icon-xs" />
                        <span className="recommendation-text">{recommendation}</span>
                      </div>
                    ))
                  ) : (
                    <p className="no-recommendations">프로젝트 구조가 훌륭합니다!</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="dashboard-main-tabs">
            <button
              className={`dashboard-main-tab ${activeMainTab === 'questions' ? 'active' : ''}`}
              onClick={() => setActiveMainTab('questions')}
            >
              <MessageSquare className="section-icon section-icon-sm" />
              면접 질문
            </button>
            <button
              className={`dashboard-main-tab ${activeMainTab === 'graph' ? 'active' : ''}`}
              onClick={() => setActiveMainTab('graph')}
            >
              <GitFork className="section-icon section-icon-sm" />
              코드 그래프
            </button>
          </div>

          {/* 2. 면접 질문 리스트 (Primary) */}
          <div className="card card-lg questions-panel" style={{ display: activeMainTab === 'questions' ? 'block' : 'none' }}>
            <div className="card-header">
              <h2><MessageSquare className="section-icon" /> 생성된 면접 질문</h2>
              {/* 질문 액션 버튼들 */}
              <div className="question-actions">
                <button
                  className="btn btn-outline"
                  onClick={regenerateQuestions}
                  disabled={isLoadingQuestions}
                >
                  {isLoadingQuestions ? '생성 중...' : '질문 재생성'}
                </button>
                <button
                  className="btn btn-primary"
                  onClick={startInterview}
                  disabled={questions.length === 0 || isLoadingQuestions}
                  title={
                    isLoadingQuestions
                      ? '질문 생성이 완료되면 면접을 시작할 수 있습니다.'
                      : questions.length === 0
                        ? '먼저 질문을 생성해주세요.'
                        : '현재 화면의 질문들로 모의면접을 시작합니다.'
                  }
                >
                  <Play className="section-icon section-icon-sm" />
                  {isLoadingQuestions ? '준비 중...' : '이 질문들로 모의면접 시작'}
                </button>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="questions-filter-bar">
              <div className="filter-search-wrap">
                <Search className="filter-search-icon" />
                <input
                  type="text"
                  className="filter-search-input"
                  placeholder="질문 검색..."
                  value={questionSearch}
                  onChange={(e) => setQuestionSearch(e.target.value)}
                />
              </div>
              <select
                className="filter-select"
                value={questionCategory}
                onChange={(e) => setQuestionCategory(e.target.value)}
              >
                <option value="all">전체 유형</option>
                <option value="technical">Technical</option>
                <option value="architectural">Architectural</option>
                <option value="scenario">Scenario</option>
                <option value="algorithm">Algorithm</option>
                <option value="system-design">System Design</option>
              </select>
              <select
                className="filter-select"
                value={questionDifficulty}
                onChange={(e) => setQuestionDifficulty(e.target.value)}
              >
                <option value="all">전체 난이도</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
              <span className="questions-count-badge">{filteredQuestions.length}/{questions.length}</span>
            </div>

            {/* 중요 파일 미리보기 */}
            {(() => {
              const criticalFiles = analysisResult?.smart_file_analysis?.critical_files
                || (analysisResult?.key_files ? convertKeyFilesToSmartAnalysis(analysisResult.key_files) : [])
              return criticalFiles.length > 0 ? (
                <CriticalFilesPreview
                  criticalFiles={criticalFiles}
                  onFileClick={(filePath: string) => {
                    setSelectedFilePath(filePath)
                    setIsFileModalOpen(true)
                  }}
                />
              ) : null
            })()}

            {/* Master/Detail Split */}
            <div className="questions-split">
              {/* LEFT: Question List (Master) */}
              <div className="questions-list-pane">
                {filteredQuestions.length === 0 ? (
                  <div className="questions-empty-state">
                    <div className="empty-state-content">
                      <MessageSquare className="empty-state-icon" />
                      <h3>{questions.length === 0 ? '질문을 불러오는 중입니다' : '검색 결과가 없습니다'}</h3>
                      <p>{questions.length === 0
                        ? 'AI가 저장소를 분석하여 맞춤형 면접 질문을 준비하고 있습니다.'
                        : '다른 검색어나 필터를 사용해보세요.'
                      }</p>
                      {questions.length === 0 && (
                        <button className="btn btn-outline" onClick={() => analysisResult && loadOrGenerateQuestions(analysisResult)} disabled={isLoadingQuestions}>
                          {isLoadingQuestions ? '로딩 중...' : '질문 다시 불러오기'}
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  filteredQuestions.map((question, index) => {
                    const formattedQuestion = formatQuestionForDisplay(question)
                    const isSelected = selectedQuestionId === question.id
                    const globalIndex = questions.findIndex(q => q.id === question.id)

                    return (
                      <div
                        key={question.id}
                        className={`question-list-card ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedQuestionId(isSelected ? null : question.id)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelectedQuestionId(isSelected ? null : question.id) } }}
                      >
                        <div className="qlc-header">
                          <span className="question-number">Q{globalIndex + 1}</span>
                          {getCategoryIcon(question.type)}
                          <span className="category-name">{question.type}</span>
                          <span className={`difficulty-badge ${getDifficultyClass(question.difficulty)}`}>{question.difficulty}</span>
                          {question.time_estimate && (
                            <span className="qlc-time"><Clock className="qlc-time-icon" />{question.time_estimate}</span>
                          )}
                        </div>
                        <div className="qlc-preview">
                          {formattedQuestion.headline || question.question}
                        </div>
                        {question.source_file && (
                          <div className="qlc-file">
                            {getFileIcon(question.source_file)}
                            <span className="qlc-file-path">{question.source_file}</span>
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
              </div>

              {/* RIGHT: Question Detail (Detail) */}
              <div className="questions-detail-pane">
                {(() => {
                  const selected = selectedQuestionId
                    ? questions.find(q => q.id === selectedQuestionId)
                    : null

                  if (!selected) {
                    return (
                      <div className="detail-empty-state">
                        <MessageSquare className="detail-empty-icon" />
                        <p className="detail-empty-text">질문을 선택하세요</p>
                        <p className="detail-empty-sub">왼쪽 목록에서 질문을 클릭하면 상세 내용이 표시됩니다</p>
                      </div>
                    )
                  }

                  const formattedSelected = formatQuestionForDisplay(selected)
                  const selectedIndex = questions.findIndex(q => q.id === selected.id)
                  const isCodeExpanded = expandedCodeSnippets.has(selected.id)

                  return (
                    <div className="detail-content">
                      {/* Detail Header */}
                      <div className="detail-header">
                        <div className="detail-breadcrumb">
                          <span className="question-number">Q{selectedIndex + 1}</span>
                          {getCategoryIcon(selected.type)}
                          <span className="category-name">{selected.type}</span>
                          <span className={`difficulty-badge ${getDifficultyClass(selected.difficulty)}`}>{selected.difficulty}</span>
                        </div>
                        {selected.time_estimate && (
                          <span className="detail-time"><Clock className="detail-time-icon" />예상 {selected.time_estimate}</span>
                        )}
                      </div>

                      {/* Detail Body */}
                      <div className="detail-body">
                        {/* Full Question Text */}
                        <div className="detail-question-title">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {formattedSelected.headline || selected.question}
                          </ReactMarkdown>
                        </div>

                        {/* Details Markdown */}
                        {formattedSelected.hasDetails && formattedSelected.detailsMarkdown && (
                          <div className="detail-context-card">
                            <div className="detail-section-label">문맥</div>
                            <div className="question-details-markdown">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{formattedSelected.detailsMarkdown}</ReactMarkdown>
                            </div>
                          </div>
                        )}

                        {/* Source File */}
                        {selected.source_file && (
                          <div className="detail-source-file">
                            <span className="detail-section-label">📄 근거 파일</span>
                            {getFileIcon(selected.source_file)}
                            <span className="detail-source-path">{selected.source_file}</span>
                            {selected.importance && (
                              <span className={`importance-badge ${selected.importance}`}>
                                {selected.importance === 'high' ? '[CORE] 핵심' : '[SUB] 보조'}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Code Snippet */}
                        {selected.code_snippet && (
                          <div className="question-code">
                            <div className="code-header">
                              {getFileIcon(selected.code_snippet.file_path)}
                              <span className="code-file-path">{selected.code_snippet.file_path}</span>
                              {selected.code_snippet.has_real_content === false && (
                                <span className="content-status warning">[WARN] 내용 없음</span>
                              )}
                              {selected.code_snippet.has_real_content === true && (
                                <span className="content-status success">[OK] 실제 코드</span>
                              )}
                            </div>
                            <pre className={`code-snippet ${isCodeExpanded ? 'expanded' : 'collapsed'}`}>
                              {selected.code_snippet.content}
                            </pre>
                            {Boolean(selected.code_snippet.content) && (
                              <button
                                className="code-expand-btn"
                                onClick={() => toggleCodeSnippetExpand(selected.id)}
                              >
                                {isCodeExpanded ? '코드 접기 ▲' : '코드 더 보기 ▼'}
                              </button>
                            )}
                          </div>
                        )}

                        {/* Expected Answer Points */}
                        {selected.expected_answer_points && selected.expected_answer_points.length > 0 && (
                          <div className="detail-answer-points">
                            <div className="detail-section-label">핵심 답변 포인트</div>
                            <ul className="answer-points-list">
                              {selected.expected_answer_points.map((point, i) => (
                                <li key={i} className="answer-point-item">{point}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Detail Footer CTA */}
                      <div className="detail-footer">
                        <button
                          className="btn btn-outline"
                          onClick={regenerateQuestions}
                          disabled={isLoadingQuestions}
                        >
                          {isLoadingQuestions ? '생성 중...' : '질문 재생성'}
                        </button>
                        <button
                          className="btn btn-primary detail-cta-primary"
                          onClick={startInterview}
                          disabled={questions.length === 0 || isLoadingQuestions}
                        >
                          <Play className="btn-icon" />
                          이 질문으로 모의면접 시작
                        </button>
                      </div>
                    </div>
                  )
                })()}
              </div>
            </div>
          </div>

          {/* 3. 코드 흐름 그래프 (Secondary) */}
          <div className="card-premium graph-canvas graph-canvas-lg graph-panel" style={{ display: activeMainTab === 'graph' ? 'block' : 'none' }}>
            <div className="graph-toolbar">
              <button className="graph-tool-btn" title="Zoom In"><ZoomIn size={18} /></button>
              <button className="graph-tool-btn" title="Zoom Out"><ZoomOut size={18} /></button>
              <button className="graph-tool-btn" title="Fit View"><Maximize size={18} /></button>
            </div>
            <div className="card-header graph-header">
              <h2><GitFork className="section-icon" /> 코드 흐름 그래프</h2>
              <div className="header-actions">
                {isLoadingGraph && <span className="graph-loading-status">로딩 중...</span>}
              </div>
            </div>
            <div className="card-body graph-body">
              {graphData && graphData.nodes && graphData.nodes.length > 0 ? (
                <div className="graph-view">
                  <CodeGraphViewer graphData={graphData} />
                </div>
              ) : (
                <div className="graph-empty-state">
                  {isLoadingGraph ? (
                    <>
                      <div className="spinner spinner-graph"></div>
                      <p>그래프 데이터를 불러오는 중...</p>
                    </>
                  ) : (
                    <>
                      <GitFork className="section-icon section-icon-empty" />
                      <p className="graph-empty-title">표시할 그래프 데이터가 없습니다.</p>
                      <p className="graph-empty-description">이 저장소에 대한 코드 구조 분석 데이터가 비어 있습니다.</p>
                      <button
                        className="btn btn-outline"
                        onClick={() => {
                          if (confirm('분석을 다시 시도하시겠습니까? 기존 결과는 덮어씌워질 수 있습니다.')) {
                            // Redirect to home with repo URL to trigger re-analysis
                            const repoUrl = analysisResult?.repo_info?.url || `https://github.com/${analysisResult?.repo_info?.owner}/${analysisResult?.repo_info?.name}`;
                            window.location.href = `/?repo=${encodeURIComponent(repoUrl)}&retry=true`;
                          }
                        }}
                      >
                        <RefreshCw className="section-icon section-icon-refresh" size={14} />
                        분석 다시 시도
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 요약 */}
          <div className="summary-section">
            <div className="card-header">
              <h2><BarChart3 className="section-icon" /> 분석 요약</h2>
            </div>
            <div className="summary-content"><p>{analysisResult.summary}</p></div>
          </div>
        </main>
      </div>

      {/* 파일 내용 모달 */}
      <FileContentModal
        isOpen={isFileModalOpen}
        onClose={closeFileModal}
        filePath={selectedFilePath}
        analysisId={analysisId || ''}
      />
    </div>
  )
}
