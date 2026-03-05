import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { QuickAccessV2 } from './QuickAccessV2'

const mockNavigate = vi.fn()
const mockSetAnalysisToken = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

vi.mock('../../utils/apiHeaders', () => ({
  setAnalysisToken: (...args: unknown[]) => mockSetAnalysisToken(...args)
}))

const mockUseQuickAccessDataWithCache = vi.fn()

vi.mock('../../hooks/useQuickAccessData', () => ({
  useQuickAccessDataWithCache: (...args: unknown[]) => mockUseQuickAccessDataWithCache(...args)
}))

describe('QuickAccessV2', () => {
  it('renders loading state', () => {
    mockUseQuickAccessDataWithCache.mockReturnValue({
      data: { recent_analyses: [], recent_reports: [] },
      isLoading: true,
      error: null,
      refetch: vi.fn()
    })

    render(<QuickAccessV2 limit={3} />)

    expect(screen.getByText('최근 활동')).toBeInTheDocument()
    expect(screen.getByText('활동 데이터를 불러오는 중입니다...')).toBeInTheDocument()
  })

  it('renders empty state and action button', () => {
    mockUseQuickAccessDataWithCache.mockReturnValue({
      data: { recent_analyses: [], recent_reports: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<QuickAccessV2 />)

    expect(screen.getByText('아직 활동 데이터가 없습니다. 저장소 분석을 시작해보세요.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '저장소 분석 시작' })).toBeInTheDocument()
  })

  it('navigates to dashboard and stores analysis token', async () => {
    const user = userEvent.setup()

    mockUseQuickAccessDataWithCache.mockReturnValue({
      data: {
        recent_analyses: [
          {
            analysis_id: 'analysis-1',
            analysis_token: 'token-1',
            repository_name: 'repo',
            repository_owner: 'owner',
            created_at: new Date().toISOString(),
            tech_stack: ['React'],
            file_count: 10,
            primary_language: 'TypeScript'
          }
        ],
        recent_reports: []
      },
      isLoading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<QuickAccessV2 />)
    await user.click(screen.getByRole('button', { name: 'owner/repo 분석 결과 보기' }))

    expect(mockSetAnalysisToken).toHaveBeenCalledWith('analysis-1', 'token-1')
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/analysis-1')
  })

  it('renders two elevated quick-access cards in loaded state', () => {
    mockUseQuickAccessDataWithCache.mockReturnValue({
      data: {
        recent_analyses: [
          {
            analysis_id: 'analysis-1',
            analysis_token: 'token-1',
            repository_name: 'repo',
            repository_owner: 'owner',
            created_at: new Date().toISOString(),
            tech_stack: ['React'],
            file_count: 10,
            primary_language: 'TypeScript'
          }
        ],
        recent_reports: [
          {
            interview_id: 'interview-1',
            repository_name: 'repo',
            repository_owner: 'owner',
            completed_at: new Date().toISOString(),
            duration_minutes: 45,
            questions_count: 10,
            answers_count: 8
          }
        ]
      },
      isLoading: false,
      error: null,
      refetch: vi.fn()
    })

    const { container } = render(<QuickAccessV2 />)

    expect(container.querySelectorAll('.v2-qa-card')).toHaveLength(2)
    expect(container.querySelector('.v2-qa-item')).toHaveClass('v2-qa-item')
  })
})
