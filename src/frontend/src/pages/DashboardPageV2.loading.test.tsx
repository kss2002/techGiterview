import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ analysisId: 'analysis-123' }),
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../components/v2/LoadingState', () => ({
  LoadingState: (props: any) => (
    <div data-testid="dashboard-loading-proxy">
      {props.progressModel?.percent}%
    </div>
  ),
}))

vi.mock('../hooks/useDashboard', () => ({
  useDashboard: () => ({
    analysisResult: null,
    isLoadingAnalysis: true,
    isLoadingAllAnalyses: false,
    loadingProgress: {
      mode: 'analysis',
      title: '분석 결과 로딩 중',
      percent: 47,
      steps: [],
      currentStepKey: 'analysis_fetch',
      currentStepLabel: '저장소 정보 조회',
      startedAt: new Date().toISOString(),
    },
    error: null,
    allAnalyses: [],
    questions: [],
    isLoadingQuestions: false,
    questionsGenerated: false,
    filteredQuestions: [],
    selectedQuestionId: null,
    questionSearch: '',
    questionCategory: 'all',
    questionDifficulty: 'all',
    activeMainTab: 'questions',
    graphData: null,
    allFiles: [],
    isLoadingAllFiles: false,
    expandedFolders: new Set<string>(),
    searchTerm: '',
    isFileModalOpen: false,
    selectedFilePath: '',
    sidebarWidth: 260,
    isResizingSidebar: false,
    startInterview: vi.fn(),
    regenerateQuestions: vi.fn(),
    loadOrGenerateQuestions: vi.fn(),
    handleSearch: vi.fn(),
    toggleFolder: vi.fn(),
    handleFileClick: vi.fn(),
    closeFileModal: vi.fn(),
    startSidebarResize: vi.fn(),
    resetSidebarWidth: vi.fn(),
    setActiveMainTab: vi.fn(),
    setSelectedQuestionId: vi.fn(),
    setQuestionSearch: vi.fn(),
    setQuestionCategory: vi.fn(),
    setQuestionDifficulty: vi.fn(),
  }),
}))

import { DashboardPageV2 } from './DashboardPageV2'

describe('DashboardPageV2 loading view', () => {
  it('passes loading progress model to LoadingState', () => {
    render(<DashboardPageV2 />)

    expect(screen.getByTestId('dashboard-loading-proxy')).toHaveTextContent('47%')
  })
})

