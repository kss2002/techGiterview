import type { ReactNode } from 'react'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { InterviewPage } from './InterviewPage'

const mockNavigate = vi.fn()
let sessionStatus: 'active' | 'paused' = 'paused'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({
      analysisId: 'analysis-1',
      interviewId: 'interview-1'
    })
  }
})

vi.mock('../components/v2/AppShellV2', () => ({
  AppShellV2: ({ header, sidebar, children }: { header: ReactNode; sidebar: ReactNode; children: ReactNode }) => (
    <div>
      <div>{header}</div>
      <div>{sidebar}</div>
      <div>{children}</div>
    </div>
  )
}))

vi.mock('../components/AnswerFeedback', () => ({
  AnswerFeedback: () => null
}))

vi.mock('../hooks/useResizableSidebar', () => ({
  useResizableSidebar: () => ({
    width: 300,
    isResizing: false,
    startResize: vi.fn(),
    resetWidth: vi.fn()
  })
}))

const createResponse = (body: unknown, status: number = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
  text: async () => JSON.stringify(body)
})

describe('InterviewPage', () => {
  beforeEach(() => {
    mockNavigate.mockReset()

    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.endsWith('/api/v1/interview/session/interview-1')) {
        return Promise.resolve(createResponse({
          success: true,
          data: {
            interview_id: 'interview-1',
            analysis_id: 'analysis-1',
            repo_url: 'https://github.com/example/repo',
            status: sessionStatus,
            interview_type: 'technical',
            difficulty_level: 'medium',
            started_at: '2026-03-05T10:00:00Z',
            progress: {
              current_question: 1,
              total_questions: 8,
              progress_percentage: 12.5,
              elapsed_time: 120,
              remaining_time: 1680
            }
          }
        }))
      }

      if (url.endsWith('/api/v1/interview/session/interview-1/questions')) {
        return Promise.resolve(createResponse({
          success: true,
          data: {
            current_question_index: 0,
            questions: [
              {
                id: 'q1',
                question: '**질문:** `package.json`에서 dependencies와 devDependencies 차이를 설명해보세요.',
                category: 'tech-stack',
                difficulty: 'medium',
                context: '프론트엔드 빌드 파이프라인 맥락에서 답변하세요.'
              }
            ]
          }
        }))
      }

      if (url.endsWith('/api/v1/interview/session/interview-1/data')) {
        return Promise.resolve(createResponse({
          data: {
            answers: [],
            conversations: []
          }
        }))
      }

      if (url.endsWith('/api/v1/interview/interview-1/finish')) {
        return Promise.resolve(createResponse({ success: true }))
      }

      return Promise.resolve(createResponse({ success: true }))
    }) as unknown as typeof fetch
  })

  it('opens finish confirmation modal before finishing interview', async () => {
    sessionStatus = 'paused'
    const user = userEvent.setup()

    render(<InterviewPage />)

    const settingsButton = await screen.findByRole('button', { name: '면접 설정' })
    await user.click(settingsButton)

    const settingsPopover = document.querySelector('.interview-settings-popover')
    expect(settingsPopover).not.toBeNull()
    const finishButton = within(settingsPopover as HTMLElement).getByRole('button', {
      name: '면접 종료'
    })
    await user.click(finishButton)

    expect(await screen.findByText('면접을 종료할까요?')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '취소' }))
    expect(screen.queryByText('면접을 종료할까요?')).not.toBeInTheDocument()
  })

  it('shows keyboard shortcut hints only while answer textarea is focused', async () => {
    sessionStatus = 'active'
    const user = userEvent.setup()

    render(<InterviewPage />)

    const textarea = await screen.findByPlaceholderText('답변을 입력하세요... (구체적인 예시와 함께 설명해주세요)')

    expect(screen.queryByText('Ctrl+Enter로 제출')).not.toBeInTheDocument()

    await user.click(textarea)
    expect(await screen.findByText('Ctrl+Enter로 제출')).toBeInTheDocument()

    fireEvent.blur(textarea)
    expect(screen.queryByText('Ctrl+Enter로 제출')).not.toBeInTheDocument()
  })

  it('renders normalized question headline without markdown label artifacts', async () => {
    sessionStatus = 'active'

    render(<InterviewPage />)

    await waitFor(() => {
      const questionText = document.querySelector('.interview-question-text')?.textContent ?? ''
      expect(questionText).toContain('dependencies와 devDependencies 차이를 설명해보세요.')
    })

    const questionText = document.querySelector('.interview-question-text')?.textContent ?? ''
    expect(questionText).toContain('package.json')
    expect(questionText).not.toContain('**질문:**')
    expect(questionText).not.toMatch(/^\s*질문[:：]/)
  })

  it('keeps finish button isolated to danger action class', async () => {
    sessionStatus = 'active'

    render(<InterviewPage />)

    const finishButton = await screen.findByRole('button', { name: '면접 종료' })
    expect(finishButton).toHaveClass('finish-interview-btn')
    expect(finishButton).not.toHaveClass('clear-btn')
    expect(finishButton).not.toHaveClass('save-btn')
  })
})
