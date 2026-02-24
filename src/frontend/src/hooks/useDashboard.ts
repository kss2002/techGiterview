import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Archive,
  BookOpen,
  CheckCircle,
  ChevronRight,
  Code,
  Cpu,
  Database,
  File,
  FileCode,
  FileText,
  Folder,
  Github,
  Globe,
  Image,
  MessageSquare,
  Monitor,
  Palette,
  Settings,
  Shield,
  Star,
  Terminal,
  TrendingUp,
  Zap
} from 'lucide-react'
import type { AnalysisResult, Question, FileTreeNode, RecentAnalysis, SmartFileAnalysis, FileInfo } from '../types/dashboard'
import { apiFetch } from '../utils/apiUtils'
import { createApiHeaders, getApiKeysFromStorage } from '../utils/apiHeaders'
import { formatQuestionForDisplay } from '../utils/questionFormatter'

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
    return React.createElement(Monitor, { className: 'file-icon file-icon-monitor' })
  }
  if (fileName === '.gitignore') {
    return React.createElement(Github, { className: 'file-icon file-icon-github' })
  }
  if (fileName.startsWith('readme')) {
    return React.createElement(BookOpen, { className: 'file-icon file-icon-book' })
  }
  if (fileName === 'license' || fileName.startsWith('license')) {
    return React.createElement(Shield, { className: 'file-icon file-icon-shield' })
  }
  if (fileName === 'package.json') {
    return React.createElement(Settings, { className: 'file-icon file-icon-settings' })
  }
  if (fileName === 'package-lock.json' || fileName === 'yarn.lock') {
    return React.createElement(Archive, { className: 'file-icon file-icon-archive' })
  }

  // 확장자별 처리
  switch (extension) {
    case 'js':
    case 'jsx':
      return React.createElement(FileCode, { className: 'file-icon file-icon-javascript' })
    case 'ts':
    case 'tsx':
      return React.createElement(FileCode, { className: 'file-icon file-icon-typescript' })
    case 'vue':
      return React.createElement(FileCode, { className: 'file-icon file-icon-vue' })
    case 'py':
    case 'pyw':
    case 'pyx':
      return React.createElement(Cpu, { className: 'file-icon file-icon-python' })
    case 'java':
    case 'kt':
    case 'scala':
      return React.createElement(Cpu, { className: 'file-icon file-icon-java' })
    case 'html':
    case 'htm':
      return React.createElement(Globe, { className: 'file-icon file-icon-html' })
    case 'css':
    case 'scss':
    case 'sass':
    case 'less':
      return React.createElement(Palette, { className: 'file-icon file-icon-css' })
    case 'json':
    case 'yaml':
    case 'yml':
    case 'toml':
    case 'ini':
    case 'conf':
    case 'config':
      return React.createElement(Settings, { className: 'file-icon file-icon-config' })
    case 'md':
      return React.createElement(FileText, { className: 'file-icon file-icon-markdown' })
    case 'txt':
      return React.createElement(FileText, { className: 'file-icon file-icon-text' })
    case 'pdf':
      return React.createElement(File, { className: 'file-icon file-icon-pdf' })
    case 'sql':
    case 'db':
    case 'sqlite':
      return React.createElement(Database, { className: 'file-icon file-icon-database' })
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
      return React.createElement(Image, { className: 'file-icon file-icon-image' })
    case 'zip':
    case 'tar':
    case 'gz':
      return React.createElement(Archive, { className: 'file-icon file-icon-archive' })
    default:
      return React.createElement(File, { className: 'file-icon file-icon-default' })
  }
}

export function useDashboard(analysisId: string | undefined) {
  const navigate = useNavigate()
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

  const loadAnalysisResult = async (analysisIdToLoad: string) => {
    console.log('[Dashboard] Starting loadAnalysisResult for ID:', analysisIdToLoad)
    console.log('[Dashboard] API URL will be:', `/api/v1/repository/analysis/${analysisIdToLoad}`)

    setIsLoadingAnalysis(true)
    setError(null)

    try {
      console.log('[Dashboard] Making fetch request...')
      const response = await apiFetch(`/api/v1/repository/analysis/${analysisIdToLoad}`)
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
        analysisId: analysisIdToLoad
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

    const waitForGeneratedQuestions = async (analysisIdToPoll: string, maxAttempts: number = 12, delayMs: number = 5000) => {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        console.log(`[Questions] ⏳ Waiting for in-progress generation... (${attempt}/${maxAttempts})`)
        await new Promise((resolve) => setTimeout(resolve, delayMs))

        const pollResponse = await apiFetch(`/api/v1/questions/analysis/${analysisIdToPoll}`, {
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

  const renderFileTreeNode = (nodes: FileTreeNode[], depth: number = 0): React.ReactElement[] => {
    // 구조 개선된 파일 트리 렌더링 - 올바른 들여쓰기 적용

    return nodes.map((node, index) => {
      const nodeKey = node.path
      const isExpanded = expandedFolders.has(node.path)
      const highlightClass = searchTerm && node.name.toLowerCase().includes(searchTerm.toLowerCase()) ? 'highlight' : ''

      const nodeContent = node.type === 'dir'
        ? React.createElement(
          'button',
          { className: 'folder-toggle', onClick: () => toggleFolder(node.path) },
          React.createElement(ChevronRight, { className: `chevron-icon ${isExpanded ? 'rotated' : ''}` }),
          React.createElement(Folder, { className: 'folder-icon' }),
          React.createElement('span', { className: 'folder-name' }, node.name)
        )
        : React.createElement(
          'div',
          { className: 'file-item-tree', onClick: () => handleFileClick(node) },
          getFileIcon(node.name),
          React.createElement('span', { className: `file-name ${highlightClass}` }, node.name),
          node.size
            ? React.createElement('span', { className: 'file-size' }, `${(node.size / 1024).toFixed(1)} KB`)
            : null
        )

      const nodeElement = React.createElement('div', { className: 'file-tree-node' }, nodeContent)

      const childrenElement = node.type === 'dir' && isExpanded && node.children
        ? React.createElement('div', { className: 'file-tree-children' }, renderFileTreeNode(node.children, depth + 1))
        : null

      return React.createElement(React.Fragment, { key: nodeKey }, nodeElement, childrenElement)
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
    if (!category) return React.createElement(Code, { className: 'category-icon category-icon-default' })
    switch (category.toLowerCase()) {
      case 'technical':
        return React.createElement(Terminal, { className: 'category-icon category-icon-technical' })
      case 'architectural':
        return React.createElement(Monitor, { className: 'category-icon category-icon-architectural' })
      case 'scenario':
        return React.createElement(MessageSquare, { className: 'category-icon category-icon-scenario' })
      case 'algorithm':
        return React.createElement(Zap, { className: 'category-icon category-icon-algorithm' })
      case 'data-structure':
        return React.createElement(Database, { className: 'category-icon category-icon-datastructure' })
      case 'system-design':
        return React.createElement(TrendingUp, { className: 'category-icon category-icon-systemdesign' })
      case 'code-review':
        return React.createElement(CheckCircle, { className: 'category-icon category-icon-codereview' })
      case 'best-practices':
        return React.createElement(Star, { className: 'category-icon category-icon-bestpractices' })
      case 'debugging':
        return React.createElement(AlertTriangle, { className: 'category-icon category-icon-debugging' })
      default:
        return React.createElement(Code, { className: 'category-icon category-icon-default' })
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
  const groupQuestions = (items: Question[]) => {
    const groups: { [key: string]: Question[] } = {}
    const standalone: Question[] = []

    items.forEach(question => {
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

  return {
    // state
    analysisResult, questions, isLoadingQuestions, isLoadingAnalysis,
    questionsGenerated, graphData, isLoadingGraph,
    allAnalyses, isLoadingAllAnalyses,
    allFiles, isLoadingAllFiles, showAllFiles,
    expandedFolders, searchTerm, filteredFiles,
    isFileModalOpen, selectedFilePath, error,
    sidebarWidth, isResizingSidebar,
    expandedQuestions, expandedCodeSnippets, activeMainTab,
    questionSearch, questionCategory, questionDifficulty, selectedQuestionId,
    filteredQuestions,
    // setters
    setActiveMainTab, setSelectedQuestionId,
    setQuestionSearch, setQuestionCategory, setQuestionDifficulty,
    setSelectedFilePath, setIsFileModalOpen,
    setQuestions,
    setExpandedQuestions, setExpandedCodeSnippets,
    // handlers
    startInterview, regenerateQuestions, loadOrGenerateQuestions,
    loadAnalysisResult, loadAllAnalyses, fetchGraphData, loadAllFiles,
    handleSearch, toggleFolder, handleFileClick, closeFileModal,
    startSidebarResize, resetSidebarWidth,
    renderFileTreeNode,
    // utilities
    sanitizeQuestions, getDifficultyClass, getCategoryIcon, getFileIcon,
    groupQuestions, convertKeyFilesToSmartAnalysis, getFileTypeReason,
  }
}
