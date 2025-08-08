import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { AnswerFeedback } from '../components/AnswerFeedback'
import './InterviewPage.css'

interface Question {
  id: string
  question: string
  category: string
  difficulty: string
  context?: string
  parent_question_id?: string
  sub_question_index?: number
  total_sub_questions?: number
  is_compound_question?: boolean
}

interface QuestionGroup {
  parentId: string
  parentTitle: string
  subQuestions: Question[]
  currentSubIndex: number
  isCompleted: boolean
}

interface QuestionGroups {
  [parentId: string]: string[]
}

interface InterviewData {
  interview_id: string
  analysis_id: string
  repo_url: string
  status: 'active' | 'paused' | 'completed'
  interview_type: string
  difficulty_level: string
  started_at: string
  progress: {
    current_question: number
    total_questions: number
    progress_percentage: number
    elapsed_time: number
    remaining_time: number
  }
}

interface Message {
  id: string
  type: 'system' | 'question' | 'answer' | 'feedback'
  content: string
  timestamp: Date
  question_id?: string
  feedback?: AnswerFeedbackData
}

interface AnswerFeedbackData {
  score: number
  message: string
  feedback_type: 'strength' | 'improvement' | 'suggestion' | 'keyword_missing'
  details: string
  keywords_found: string[]
  keywords_missing: string[]
  suggestions: string[]
  technical_accuracy: string
}

export const InterviewPage: React.FC = () => {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  
  const [interview, setInterview] = useState<InterviewData | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [questionGroups, setQuestionGroups] = useState<QuestionGroups>({})
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [loadingStates, setLoadingStates] = useState({
    session: true,
    questions: true
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(30 * 60) // 30분
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [fontSize, setFontSize] = useState('medium')
  const [currentFeedback, setCurrentFeedback] = useState<AnswerFeedbackData | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [isFocusMode, setIsFocusMode] = useState(true)
  const [savedAnswers, setSavedAnswers] = useState<Record<string, string>>({})
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [conversationMode, setConversationMode] = useState<{
    questionId: string;
    originalAnswer: string;
    feedback: AnswerFeedbackData;
  } | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null)

  // WebSocket 연결
  useEffect(() => {
    if (!interviewId) return

    // 임시로 WebSocket 없이 진행
    setWsConnected(true)
    
    // const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/interview/${interviewId}`
    // const ws = new WebSocket(wsUrl)
    
    // ws.onopen = () => {
    //   console.log('WebSocket connected')
    //   setWsConnected(true)
    // }
    
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   handleWebSocketMessage(data)
    // }
    
    // ws.onclose = () => {
    //   console.log('WebSocket disconnected')
    //   setWsConnected(false)
    // }
    
    // ws.onerror = (error) => {
    //   console.error('WebSocket error:', error)
    //   setWsConnected(false)
    // }
    
    // wsRef.current = ws

    return () => {
      // if (ws && ws.readyState === WebSocket.OPEN) {
      //   ws.close()
      // }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [interviewId])

  // 면접 데이터 로드
  useEffect(() => {
    if (!interviewId) {
      navigate('/dashboard')
      return
    }
    
    loadInterview()
  }, [interviewId, navigate])

  // 타이머 시작
  useEffect(() => {
    if (interview && interview.status === 'active') {
      timerRef.current = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            finishInterview()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [interview])

  // 메시지 스크롤
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 키보드 단축키 처리
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'Enter':
            e.preventDefault()
            submitAnswer()
            break
          case 'ArrowLeft':
            e.preventDefault()
            navigateQuestion(-1)
            break
          case 'ArrowRight':
            e.preventDefault()
            navigateQuestion(1)
            break
          case 'd':
            e.preventDefault()
            setIsDarkMode(!isDarkMode)
            break
          case 's':
            e.preventDefault()
            saveCurrentAnswer()
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isDarkMode, currentQuestionIndex])

  // 자동 저장 기능
  useEffect(() => {
    const currentQ = questions[currentQuestionIndex]
    if (currentAnswer && interviewId && currentQ) {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }
      
      autoSaveTimer.current = setTimeout(() => {
        saveCurrentAnswer()
      }, 2000) // 2초 후 자동 저장
    }

    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }
    }
  }, [currentAnswer, interviewId, questions, currentQuestionIndex])

  // 질문 변경 시 답변 로드
  useEffect(() => {
    const currentQ = questions[currentQuestionIndex]
    if (currentQ && interviewId) {
      const savedKey = `interview_${interviewId}_${currentQ.id}`
      const saved = localStorage.getItem(savedKey)
      setCurrentAnswer(saved || '')
    }
  }, [currentQuestionIndex, interviewId, questions])

  // 세션 히스토리 로딩 (답변, 피드백, 대화 포함)
  const loadSessionHistory = async (questionsList: Question[]) => {
    if (!interviewId) return

    try {
      console.log('[HISTORY] 세션 히스토리 로딩 시작');
      const response = await fetch(`/api/v1/interview/session/${interviewId}/data`)
      
      if (!response.ok) {
        console.warn('[세션 데이터] 불러오기 실패:', response.status)
        return
      }
      
      const { data } = await response.json()
      console.log('[HISTORY] 세션 데이터 로드 완료:', data)
      
      // 답변 히스토리를 메시지로 변환
      const historyMessages: Message[] = []
      
      // 답변과 피드백을 질문 순서대로 정렬
      data.answers.forEach((answer: any) => {
        // 답변 메시지 추가
        historyMessages.push({
          id: `answer-${answer.question_id}`,
          type: 'answer',
          content: answer.user_answer,
          timestamp: new Date(answer.submitted_at),
          question_id: answer.question_id
        })
        
        // 피드백 메시지 추가 (있는 경우)
        if (answer.feedback) {
          historyMessages.push({
            id: `feedback-${answer.question_id}`,
            type: 'feedback',
            content: answer.feedback.message,
            timestamp: new Date(answer.feedback.created_at),
            question_id: answer.question_id,
            feedback: {
              score: answer.feedback.score,
              message: answer.feedback.message,
              feedback_type: answer.feedback.feedback_type,
              details: answer.feedback.details,
              keywords_found: [],
              keywords_missing: [],
              suggestions: answer.feedback.suggestions,
              technical_accuracy: answer.feedback.details
            }
          })
        }
      })
      
      // 대화 메시지 추가
      data.conversations.forEach((msg: any) => {
        if (msg.type === 'user' || msg.type === 'ai') {
          historyMessages.push({
            id: msg.id,
            type: msg.type === 'user' ? 'answer' : 'feedback',
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            question_id: msg.question_id
          })
        }
      })
      
      // 시간순으로 정렬
      historyMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
      
      // 기존 시스템 메시지와 합치기 전에 히스토리 메시지 저장
      if (historyMessages.length > 0) {
        setMessages(prev => {
          // 기존 시스템 메시지만 유지
          const systemMessages = prev.filter(msg => msg.type === 'system')
          return [...systemMessages, ...historyMessages]
        })
      }
      
      // 저장된 답변들을 상태에 반영
      const answersMap: Record<string, string> = {}
      data.answers.forEach((answer: any) => {
        answersMap[answer.question_id] = answer.user_answer
      })
      setSavedAnswers(answersMap)
      
      console.log('[HISTORY] 전체 히스토리 로드 완료:', {
        answersCount: data.answers.length,
        conversationsCount: data.conversations.length,
        messagesCount: historyMessages.length
      })
      
    } catch (error) {
      console.error('[ERROR] 세션 히스토리 로딩 실패:', error)
    }
  }

  const loadInterview = async () => {
    console.log('[LOAD] loadInterview 함수 시작');
    try {
      console.log('[API] 면접 세션 및 질문 데이터 로딩 시작');
      // 병렬 API 호출로 성능 개선
      const [sessionResponse, questionsResponse] = await Promise.all([
        fetch(`/api/v1/interview/session/${interviewId}`),
        fetch(`/api/v1/interview/session/${interviewId}/questions`)
      ])
      
      console.log('[API] API 응답 상태:', {
        session: sessionResponse.status,
        questions: questionsResponse.status
      });
      
      if (!sessionResponse.ok || !questionsResponse.ok) {
        console.log('[ERROR] API 응답 에러:', {
          sessionOk: sessionResponse.ok,
          questionsOk: questionsResponse.ok
        });
        throw new Error('면접 데이터를 불러올 수 없습니다.')
      }

      console.log('[PARSE] JSON 파싱 시작');
      const [sessionResult, questionsResult] = await Promise.all([
        sessionResponse.json(),
        questionsResponse.json()
      ])
      
      console.log('[RESULT] API 결과:', {
        sessionSuccess: sessionResult.success,
        questionsSuccess: questionsResult.success,
        sessionData: sessionResult.data,
        questionsData: questionsResult.data
      });

      if (sessionResult.success && questionsResult.success) {
        console.log('[SUCCESS] API 결과 검증 통과, 상태 업데이트 시작');
        
        setInterview(sessionResult.data)
        setQuestions(questionsResult.data.questions)
        
        console.log('[UPDATE] 상태 업데이트 완료');
        
        // 세션 히스토리 데이터 로딩
        await loadSessionHistory(questionsResult.data.questions);
        
        // 현재 질문 표시
        const currentQuestionIndex = questionsResult.data.current_question_index
        const currentQuestion = questionsResult.data.questions[currentQuestionIndex]
        
        console.log('[QUESTION] 현재 질문 정보:', {
          index: currentQuestionIndex,
          question: currentQuestion
        });
        
        // 기존 메시지가 있는지 확인
        const hasExistingMessages = messages.length > 0;
        console.log('[DEBUG] 기존 메시지 존재 여부:', hasExistingMessages, '개수:', messages.length);
        
        if (hasExistingMessages) {
          // 답변 제출 후 재로드하는 경우 - 기존 메시지 유지하고 새 질문만 추가
          console.log('[DEBUG] 기존 대화 유지하면서 새 질문 추가');
          
          // 진행 상황 업데이트 메시지 추가
          if (sessionResult.data.progress.total_questions > 0) {
            setMessages(prev => [...prev, {
              id: `progress-${Date.now()}`,
              type: 'system',
              content: `> 진행상황: ${sessionResult.data.progress.current_question}/${sessionResult.data.progress.total_questions} (${sessionResult.data.progress.progress_percentage}%)`,
              timestamp: new Date()
            }]);
          }
          
          // 새 질문 추가
          if (currentQuestion) {
            console.log('[DEBUG] 새 질문 메시지 추가');
            setMessages(prev => [...prev, {
              id: `question-${currentQuestion.id}`,
              type: 'question',
              content: currentQuestion.question,
              timestamp: new Date(),
              question_id: currentQuestion.id
            }]);
          }
        } else {
          // 첫 로드인 경우 - 초기 메시지 설정
          console.log('[DEBUG] 첫 로드 - 초기 메시지 설정');
          const initialMessages: Message[] = [
            {
              id: 'welcome',
              type: 'system',
              content: '* 모의면접을 시작합니다! 편안하게 답변해주세요.',
              timestamp: new Date()
            }
          ]
          
          // 면접 상태 메시지 표시
          if (sessionResult.data.progress.total_questions > 0) {
            initialMessages.push({
              id: 'current-status',
              type: 'system',
              content: `> 진행상황: ${sessionResult.data.progress.current_question}/${sessionResult.data.progress.total_questions} (${sessionResult.data.progress.progress_percentage}%)`,
              timestamp: new Date()
            })
          }

          // 현재 질문 표시
          if (currentQuestion) {
            console.log('[DEBUG] 현재 질문 메시지 추가');
            initialMessages.push({
              id: `question-${currentQuestion.id}`,
              type: 'question',
              content: currentQuestion.question,
              timestamp: new Date(),
              question_id: currentQuestion.id
            })
          }
          
          console.log('[DEBUG] 메시지 업데이트:', initialMessages);
          setMessages(initialMessages);
        }
        
        console.log('[DEBUG] loadInterview 완료');
      } else {
        console.log('[ERROR] API 결과 검증 실패:', {
          sessionSuccess: sessionResult.success,
          questionsSuccess: questionsResult.success
        });
      }
    } catch (error) {
      console.error('[ERROR] Error loading interview:', error)
      alert('면접 데이터를 불러오는데 실패했습니다.')
      navigate('/dashboard')
    } finally {
      console.log('[UPDATE] setIsLoading(false) 설정');
      setIsLoading(false)
    }
  }


  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'question':
        setMessages(prev => [...prev, {
          id: `question-${Date.now()}`,
          type: 'question',
          content: data.content,
          timestamp: new Date(),
          question_id: data.question_id
        }])
        break
        
      case 'feedback':
        setMessages(prev => [...prev, {
          id: `feedback-${Date.now()}`,
          type: 'feedback',
          content: data.content,
          timestamp: new Date()
        }])
        break
        
      case 'interview_completed':
        setInterview(prev => prev ? { ...prev, status: 'completed' } : null)
        setMessages(prev => [...prev, {
          id: 'completed',
          type: 'system',
          content: '면접이 완료되었습니다! 결과를 확인해보세요.',
          timestamp: new Date()
        }])
        break
    }
  }

  const submitAnswer = async () => {
    console.log('[SUBMIT] submitAnswer 함수 실행됨');
    console.log('[SUBMIT] currentAnswer:', currentAnswer);
    console.log('[SUBMIT] conversationMode:', conversationMode);
    
    if (!currentAnswer.trim()) {
      console.log('[ERROR] currentAnswer가 비어있음');
      return;
    }

    // 대화 모드인 경우 대화 처리
    if (conversationMode) {
      return await handleConversation();
    }

    // 일반 면접 답변 처리
    console.log('[SUBMIT] interview:', interview);
    console.log('[SUBMIT] interviewId:', interviewId);
    console.log('[SUBMIT] questions.length:', questions.length);
    if (!interview) {
      console.log('[ERROR] interview 객체가 없음');
      return;
    }
    if (!interviewId) {
      console.log('[ERROR] interviewId가 없음');
      return;
    }

    console.log('[SUCCESS] 모든 조건 통과, 답변 제출 시작');
    setIsSubmitting(true)
    
    try {
      const currentQuestion = questions[interview.progress.current_question - 1]
      console.log('[QUESTION] currentQuestion:', currentQuestion);
      
      if (!currentQuestion) {
        console.log('[ERROR] currentQuestion이 없음 - progress:', interview.progress);
        throw new Error('현재 질문을 찾을 수 없습니다.');
      }
      
      // 답변 메시지 추가
      const answerMessageId = `answer-${Date.now()}`;
      const answerMessage: Message = {
        id: answerMessageId,
        type: 'answer',
        content: currentAnswer,
        timestamp: new Date(),
        question_id: currentQuestion.id
      }
      
      console.log('[MESSAGE] 답변 메시지 추가:', answerMessage);
      setMessages(prev => [...prev, answerMessage])
      
      // REST API로 답변 전송
      const requestBody = {
        interview_id: interviewId,
        question_id: currentQuestion.id,
        answer: currentAnswer,
        time_taken: 60 // 임시값
      };
      
      console.log('[API] API 요청 시작:', requestBody);
      
      const response = await fetch('/api/v1/interview/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })
      
      console.log('[API] API 응답 상태:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.log('[ERROR] API 응답 에러:', errorText);
        throw new Error(`답변 제출에 실패했습니다. (${response.status})`);
      }

      const result = await response.json()
      console.log('[SUCCESS] API 응답 결과:', result);
      
      if (result.success) {
        console.log('[SUCCESS] 답변 제출 성공');
        
        // 피드백 처리 - 답변 메시지에 피드백 데이터 추가
        if (result.data.feedback) {
          console.log('[FEEDBACK] 피드백 데이터 수신:', result.data.feedback);
          
          // 방금 추가한 답변 메시지에 피드백 추가
          setMessages(prev => prev.map(msg => {
            if (msg.id === answerMessageId) {
              return {
                ...msg,
                feedback: result.data.feedback
              };
            }
            return msg;
          }));

          // 자동 대화 모드 시작 기능 제거됨 - 사용자가 현재 질문에 집중할 수 있도록 함
        }
        
        // 다음 질문으로 이동하거나 완료 처리
        if (result.data.is_completed) {
          console.log('[COMPLETE] 면접 완료');
          setMessages(prev => [...prev, {
            id: 'completed',
            type: 'system',
            content: '[COMPLETE] 모든 질문이 완료되었습니다! 수고하셨습니다.',
            timestamp: new Date()
          }])
        } else {
          console.log('[NEXT] 다음 질문으로 이동');
          // 피드백 점수가 높으면 바로 다음 질문으로, 낮으면 대화 모드 대기
          if (result.data.feedback && result.data.feedback.score >= 7.0) {
            // 점수가 높으면 바로 다음 질문으로
            setTimeout(async () => {
              await loadInterview();
            }, 3000);
          } else {
            // 자동 유도 문구 제거됨 - 사용자가 필요에 따라 직접 대화하거나 다음 질문으로 넘어갈 수 있음
          }
        }
      } else {
        console.log('[ERROR] API 호출은 성공했지만 result.success가 false');
        throw new Error(result.message || '답변 처리에 실패했습니다.');
      }
      
      console.log('[CLEAR] 답변 입력창 초기화');
      setCurrentAnswer('')
      
    } catch (error) {
      console.error('[ERROR] Error submitting answer:', error)
      const errorMessage = error instanceof Error ? error.message : '답변 제출에 실패했습니다.';
      
      // 사용자 친화적인 에러 메시지 표시
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        type: 'system',
        content: `[ERROR] ${errorMessage}`,
        timestamp: new Date()
      }]);
      
      // alert 대신 더 나은 UI 피드백
      alert(errorMessage);
    } finally {
      console.log('[UPDATE] isSubmitting을 false로 설정');
      setIsSubmitting(false)
    }
  }

  const finishInterview = async () => {
    try {
      const response = await fetch(`/api/v1/interview/${interviewId}/finish`, {
        method: 'POST'
      })
      
      if (response.ok) {
        navigate('/reports')
      }
    } catch (error) {
      console.error('Error finishing interview:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const navigateQuestion = (direction: number) => {
    if (!questions.length) return
    
    const newIndex = Math.max(0, Math.min(questions.length - 1, currentQuestionIndex + direction))
    setCurrentQuestionIndex(newIndex)
  }

  // 대화 모드 시작
  const startConversation = (questionId: string, originalAnswer: string, feedback: AnswerFeedbackData) => {
    setConversationMode({
      questionId,
      originalAnswer,
      feedback
    });
    
    // 대화 모드로 전환
    setMessages(prev => [...prev, {
      id: `conversation-start-${Date.now()}`,
      type: 'system',
      content: '[CONVERSATION] 이 문제에 대한 개별 상담을 시작합니다. 궁금한 점을 자유롭게 질문해보세요!',
      timestamp: new Date()
    }]);
  }

  // 대화 모드 종료
  const endConversation = () => {
    setConversationMode(null);
    setMessages(prev => [...prev, {
      id: `conversation-end-${Date.now()}`,
      type: 'system',
      content: '[CONVERSATION] 개별 상담을 종료합니다.',
      timestamp: new Date()
    }]);
  }

  // 대화 처리
  const handleConversation = async () => {
    if (!conversationMode) return;

    try {
      setIsSubmitting(true);
      
      // "다음 질문" 키워드 체크
      const isNextQuestionRequest = /다음\s*질문|다음으로|넘어가|다음|next/i.test(currentAnswer.trim());
      
      if (isNextQuestionRequest) {
        // 다음 질문으로 이동
        setMessages(prev => [...prev, {
          id: `next-question-${Date.now()}`,
          type: 'answer',
          content: currentAnswer,
          timestamp: new Date()
        }, {
          id: `next-question-response-${Date.now()}`,
          type: 'system',
          content: '네, 다음 질문으로 넘어가겠습니다!',
          timestamp: new Date()
        }]);
        
        // 대화 모드 종료
        setConversationMode(null);
        
        // 다음 질문 로드
        setTimeout(async () => {
          await loadInterview();
        }, 1500);
        
        setCurrentAnswer('');
        return;
      }
      
      // 사용자 질문 메시지 추가
      const userQuestion: Message = {
        id: `conversation-question-${Date.now()}`,
        type: 'answer',
        content: currentAnswer,
        timestamp: new Date(),
        question_id: conversationMode.questionId
      };
      
      setMessages(prev => [...prev, userQuestion]);
      
      // 백엔드 대화 API 호출
      const response = await fetch('/api/v1/interview/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interview_id: interviewId,
          question_id: conversationMode.questionId,
          original_answer: conversationMode.originalAnswer,
          conversation_question: currentAnswer
        })
      });
      
      if (!response.ok) {
        throw new Error(`대화 요청에 실패했습니다. (${response.status})`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // AI 응답 메시지 추가
        const aiResponse: Message = {
          id: `conversation-answer-${Date.now()}`,
          type: 'system',
          content: result.data.response,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiResponse]);
      } else {
        throw new Error(result.message || '대화 처리에 실패했습니다.');
      }
      
      setCurrentAnswer('');
      
    } catch (error) {
      console.error('[ERROR] 대화 처리 중 오류:', error);
      
      // 에러 메시지 표시
      const errorResponse: Message = {
        id: `conversation-error-${Date.now()}`,
        type: 'system',
        content: `[ERROR] ${error instanceof Error ? error.message : '대화 처리 중 오류가 발생했습니다.'}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsSubmitting(false);
    }
  }

  const goToQuestion = (index: number) => {
    if (index >= 0 && index < questions.length) {
      setCurrentQuestionIndex(index)
    }
  }

  const saveCurrentAnswer = () => {
    const currentQ = questions[currentQuestionIndex]
    if (currentQ && interviewId && currentAnswer) {
      const savedKey = `interview_${interviewId}_${currentQ.id}`
      localStorage.setItem(savedKey, currentAnswer)
      setLastSaved(new Date())
      setSavedAnswers(prev => ({
        ...prev,
        [currentQ.id]: currentAnswer
      }))
    }
  }

  // 질문 그룹 처리 함수들
  const getQuestionDisplayText = (question: Question): string => {
    if (question.parent_question_id && question.sub_question_index && question.total_sub_questions) {
      return `${question.sub_question_index}/${question.total_sub_questions}번 문제`
    }
    return `질문 ${currentQuestionIndex + 1}`
  }

  const getProgressText = (): string => {
    const currentQ = questions[currentQuestionIndex]
    if (currentQ?.parent_question_id && currentQ.sub_question_index && currentQ.total_sub_questions) {
      const groupQuestions = questions.filter(q => q.parent_question_id === currentQ.parent_question_id)
      const groupIndex = Math.floor(currentQuestionIndex / groupQuestions.length) + 1
      const totalGroups = Math.ceil(questions.length / groupQuestions.length)
      return `그룹 ${groupIndex}/${totalGroups} - ${currentQ.sub_question_index}/${currentQ.total_sub_questions}`
    }
    return `질문 ${currentQuestionIndex + 1} / ${questions.length}`
  }

  const isLastQuestionInGroup = (questionIndex: number): boolean => {
    const question = questions[questionIndex]
    if (!question?.parent_question_id) return true
    
    const groupQuestions = questions.filter(q => q.parent_question_id === question.parent_question_id)
    return question.sub_question_index === groupQuestions.length
  }

  const getNextGroupFirstQuestion = (currentIndex: number): number => {
    const currentQ = questions[currentIndex]
    if (!currentQ?.parent_question_id) return currentIndex + 1
    
    // 현재 그룹의 마지막 질문 찾기
    const currentGroupQuestions = questions.filter(q => q.parent_question_id === currentQ.parent_question_id)
    const lastQuestionInGroup = questions.findIndex(q => 
      q.parent_question_id === currentQ.parent_question_id && 
      q.sub_question_index === currentGroupQuestions.length
    )
    
    return lastQuestionInGroup + 1
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'system': return '[SYS]'
      case 'question': return '[Q]'
      case 'answer': return '[A]'
      case 'feedback': return '[FB]'
      default: return '[MSG]'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'technical': return '[TECH]'
      case 'tech_stack': return '[STACK]'
      case 'architecture': return '[ARCH]'
      case 'algorithm': return '[ALGO]'
      case 'database': return '[DB]'
      case 'frontend': return '[FRONT]'
      case 'backend': return '[BACK]'
      case 'devops': return '[OPS]'
      case 'testing': return '[TEST]'
      case 'security': return '[SEC]'
      default: return '[?]'
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'var(--primary-400)'
      case 'medium': return 'var(--primary-600)'
      case 'hard': return 'var(--primary-700)'
      default: return '#6b7280'
    }
  }

  if (isLoading) {
    return (
      <div className="interview-loading">
        <div className="spinner-large"></div>
        <p>면접을 준비하고 있습니다...</p>
        <div className="loading-progress">
          <div className="progress-item">
            <span className={loadingStates.session ? 'loading' : 'complete'}>
              {loadingStates.session ? '[LOADING]' : '[DONE]'} 면접 세션 정보
            </span>
          </div>
          <div className="progress-item">
            <span className={loadingStates.questions ? 'loading' : 'complete'}>
              {loadingStates.questions ? '[LOADING]' : '[DONE]'} 면접 질문 데이터
            </span>
          </div>
        </div>
      </div>
    )
  }

  if (!interview) {
    return (
      <div className="interview-error">
        <h2>면접을 찾을 수 없습니다</h2>
        <button onClick={() => navigate('/dashboard')}>대시보드로 돌아가기</button>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0

  return (
    <div className={`interview-page ${isDarkMode ? 'dark-mode' : ''} ${isFocusMode ? 'focus-mode' : ''} font-size-${fontSize}`}>
      {/* 헤더 */}
      <div className="interview-header">
        <div className="header-left">
          <h1>[INTERVIEW] 모의면접 진행중</h1>
          <div className="interview-info">
            <span className="question-progress">
              {getProgressText()}
            </span>
            <div className="progress-stepper">
              {questions.map((question, index) => (
                <div
                  key={index}
                  className={`step ${index <= currentQuestionIndex ? 'completed' : ''} ${index === currentQuestionIndex ? 'current' : ''}`}
                  onClick={() => goToQuestion(index)}
                  title={`${getQuestionDisplayText(question)}: ${question.question.substring(0, 50)}...`}
                >
                  {question.sub_question_index || index + 1}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <div className="settings-controls">
            <button 
              className={`setting-btn ${isDarkMode ? 'active' : ''}`}
              onClick={() => setIsDarkMode(!isDarkMode)}
              title="다크 모드 (Ctrl+D)"
            >
              {isDarkMode ? '[LIGHT]' : '[DARK]'}
            </button>
            <select 
              className="font-size-selector"
              value={fontSize}
              onChange={(e) => setFontSize(e.target.value)}
              title="폰트 크기"
            >
              <option value="small">작게</option>
              <option value="medium">보통</option>
              <option value="large">크게</option>
            </select>
          </div>
          <div className="timer">
            <span className="timer-icon">[TIME]</span>
            <span className="timer-value">{formatTime(timeRemaining)}</span>
          </div>
          <div className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {wsConnected ? '연결됨' : '연결 끊김'}
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="interview-content">
        {/* 질문 영역 */}
        <div className="question-container">
          {currentQuestion && (
            <div className="current-question">
              <div className="question-header">
                <div className="question-meta">
                  <span className="question-number">
                    {currentQuestion.parent_question_id && currentQuestion.sub_question_index 
                      ? `Q${currentQuestion.sub_question_index}` 
                      : `Q${currentQuestionIndex + 1}`}
                  </span>
                  <span className="category-icon">{getCategoryIcon(currentQuestion.category)}</span>
                  <span className="category-name">{currentQuestion.category}</span>
                  <span 
                    className="difficulty-badge"
                    style={{ backgroundColor: getDifficultyColor(currentQuestion.difficulty) }}
                  >
                    {currentQuestion.difficulty}
                  </span>
                </div>
                <div className="question-navigation">
                  <button 
                    className="nav-btn prev"
                    onClick={() => navigateQuestion(-1)}
                    disabled={currentQuestionIndex === 0}
                    title="이전 질문 (Ctrl+←)"
                  >
                    ← 이전
                  </button>
                  <button 
                    className="nav-btn next"
                    onClick={() => navigateQuestion(1)}
                    disabled={currentQuestionIndex === questions.length - 1}
                    title="다음 질문 (Ctrl+→)"
                  >
                    {isLastQuestionInGroup(currentQuestionIndex) ? '다음 그룹 →' : '다음 →'}
                  </button>
                </div>
              </div>
              <div className="question-content">
                <div className="question-text">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 20px 0', lineHeight: '1.8' }}>{children}</p>,
                      code: ({ children }) => <code style={{ background: '#f1f5f9', padding: '3px 6px', borderRadius: '4px', fontSize: '0.9em', border: '1px solid #e2e8f0' }}>{children}</code>,
                      pre: ({ children }) => <pre style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', overflow: 'auto', border: '1px solid #e2e8f0', lineHeight: '1.6' }}>{children}</pre>
                    }}
                  >
                    {currentQuestion.question}
                  </ReactMarkdown>
                </div>
                {currentQuestion.context && (
                  <div className="question-context">
                    [TIP] {currentQuestion.context}
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* 답변 히스토리 */}
          <div className="answer-history">
            {messages.filter(msg => msg.type === 'answer').map((message) => (
              <div key={message.id} className={`answer-item ${message.type === 'system' ? 'system-message' : ''}`}>
                <div className="answer-header">
                  <span className="answer-label">
                    {message.type === 'system' ? 'AI 면접관' : '내 답변'}
                  </span>
                  <span className="answer-time">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="answer-content">
                  {message.content}
                </div>
                
                {/* 답변별 피드백 표시 (사용자 답변에만) */}
                {message.type === 'answer' && message.feedback && (
                  <div className="answer-feedback-section">
                    {message.feedback.is_conversation ? (
                      // 대화형 응답 (점수 없음)
                      <div className="conversation-feedback">
                        <div className="feedback-header">
                          <span className="feedback-label">AI 응답</span>
                        </div>
                        <div className="feedback-message">
                          {message.feedback.message}
                        </div>
                      </div>
                    ) : (
                      // 정식 피드백 (점수 포함)
                      <>
                        <div className="feedback-header">
                          <span className="feedback-label">AI 피드백</span>
                          <span className="feedback-score">{message.feedback.score}/10</span>
                        </div>
                        <div className="feedback-message">
                          {message.feedback.message}
                        </div>
                        {message.feedback.suggestions && (
                          <div className="feedback-suggestions">
                            <div className="suggestions-title">개선 제안:</div>
                            <ul className="suggestions-list">
                              {message.feedback.suggestions.map((suggestion, index) => (
                                <li key={index}>{suggestion}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* 대화 모드 메시지 */}
          {conversationMode && (
            <div className="conversation-area">
              <div className="conversation-header">[CHAT] AI 멘토와 대화</div>
              {messages.filter(msg => 
                msg.type === 'system' && (
                  msg.content.includes('다음 질문으로 넘어가겠습니다') ||
                  msg.content.includes('좋은 질문이네요') ||
                  msg.content.includes('답변드리겠습니다') ||
                  msg.content.includes('안녕하세요')
                )
              ).map((message) => (
                <div key={message.id} className="conversation-message ai-message">
                  <div className="message-header">
                    <span className="message-label">AI 멘토</span>
                    <span className="message-time">{message.timestamp.toLocaleTimeString()}</span>
                  </div>
                  <div className="message-content">{message.content}</div>
                </div>
              ))}
              
              {/* 사용자 대화 질문들 */}
              {messages.filter(msg => 
                msg.type === 'answer' && conversationMode && 
                msg.question_id === conversationMode.questionId &&
                msg.content !== conversationMode.originalAnswer
              ).map((message) => (
                <div key={message.id} className="conversation-message user-message">
                  <div className="message-header">
                    <span className="message-label">내 질문</span>
                    <span className="message-time">{message.timestamp.toLocaleTimeString()}</span>
                  </div>
                  <div className="message-content">{message.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* 답변 피드백 */}
        {currentFeedback && (
          <AnswerFeedback 
            feedback={currentFeedback}
            isVisible={showFeedback}
          />
        )}
          
        {/* 답변 입력 영역 */}
        {interview.status === 'active' && currentQuestion && (
          <div className="answer-input-area">
            <div className="input-header">
              <h3>{conversationMode ? '질문 입력 (대화 모드)' : '답변 입력'}</h3>
              <div className="input-help">
                {conversationMode ? (
                  <>
                    <span>질문을 입력하고 AI와 대화하세요</span>
                    <button className="end-conversation-btn" onClick={endConversation}>
                      대화 종료
                    </button>
                  </>
                ) : (
                  <>
                    <span>Ctrl+Enter로 제출</span>
                    <span>Shift+Enter로 줄바꿈</span>
                    <span>Ctrl+S로 저장</span>
                    {lastSaved && (
                      <span className="save-status">
                        ✓ {lastSaved.toLocaleTimeString()}에 저장됨
                      </span>
                    )}
                  </>
                )}
              </div>
            </div>
            
            <div className="input-container">
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder={conversationMode ? "궁금한 점을 질문해보세요..." : "답변을 입력하세요... (구체적인 예시와 함께 설명해주세요)"}
                className="answer-textarea"
                rows={8}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && (e.ctrlKey || e.metaKey)) {
                    console.log('[KEY] Ctrl+Enter 키보드 단축키로 답변 제출 시도');
                    e.preventDefault()
                    submitAnswer()
                  }
                }}
                disabled={isSubmitting}
              />
              <div className="input-actions">
                <div className="input-stats">
                  <span className={`char-count ${currentAnswer.length > 800 ? 'warning' : ''}`}>
                    {currentAnswer.length} / 1000
                  </span>
                  <span className="word-count">
                    {currentAnswer.split(/\s+/).filter(word => word.length > 0).length} 단어
                  </span>
                </div>
                <div className="action-buttons">
                  <button
                    onClick={() => setCurrentAnswer('')}
                    className="clear-btn"
                    disabled={!currentAnswer || isSubmitting}
                  >
                    지우기
                  </button>
                  <button
                    onClick={saveCurrentAnswer}
                    className="save-btn"
                    disabled={!currentAnswer || isSubmitting}
                  >
                    저장 (Ctrl+S)
                  </button>
                  <button
                    onClick={() => {
                      console.log('[CLICK] submit-answer-btn 클릭됨');
                      console.log('[STATUS] 버튼 상태 체크:');
                      console.log('  - currentAnswer.trim():', Boolean(currentAnswer.trim()));
                      console.log('  - isSubmitting:', isSubmitting);
                      console.log('  - wsConnected:', wsConnected);
                      console.log('  - 버튼 disabled:', !currentAnswer.trim() || isSubmitting);
                      submitAnswer();
                    }}
                    disabled={!currentAnswer.trim() || isSubmitting}
                    className="submit-answer-btn"
                  >
                    {isSubmitting ? (
                      <>
                        <span className="spinner-small"></span>
                        {conversationMode ? '질문 중...' : '제출 중...'}
                      </>
                    ) : !currentAnswer.trim() ? (
                      conversationMode ? '질문을 입력해주세요' : '답변을 입력해주세요'
                    ) : (
                      conversationMode ? '질문하기 (Ctrl+Enter)' : '답변 제출 (Ctrl+Enter)'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
          
          {/* 면접 완료 */}
          {interview.status === 'completed' && (
            <div className="interview-completed">
              <div className="completion-message">
                <h3>[COMPLETE] 면접이 완료되었습니다!</h3>
                <p>수고하셨습니다. 결과 리포트를 확인해보세요.</p>
                <div className="completion-actions">
                  <button
                    onClick={() => navigate('/reports')}
                    className="view-report-btn"
                  >
                    결과 보기
                  </button>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="back-dashboard-btn"
                  >
                    대시보드로
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 사이드바 */}
        {!isFocusMode && (
          <div className="sidebar">
            <div className="sidebar-section">
              <h3>[LIST] 질문 목록</h3>
              <div className="questions-list">
                {questions.map((question, index) => (
                  <div 
                    key={question.id} 
                    className={`question-item ${
                      index === currentQuestionIndex ? 'current' : 
                      index < currentQuestionIndex ? 'completed' : 'pending'
                    }`}
                    onClick={() => goToQuestion(index)}
                  >
                    <div className="question-number">Q{index + 1}</div>
                    <div className="question-preview">
                      <span className="question-text">
                        {question.question.length > 50 
                          ? question.question.substring(0, 50) + '...'
                          : question.question
                        }
                      </span>
                      <div className="question-badges">
                        <span className="mini-category">{getCategoryIcon(question.category)}</span>
                        <span className="mini-difficulty" style={{ backgroundColor: getDifficultyColor(question.difficulty) }}>
                          {question.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          
          <div className="sidebar-section">
            <h3>[TIPS] 면접 팁</h3>
            <ul className="interview-tips">
              <li>차분하게 생각한 후 답변하세요</li>
              <li>구체적인 예시를 들어 설명하세요</li>
              <li>모르는 것은 솔직히 말하세요</li>
              <li>시간을 충분히 활용하세요</li>
            </ul>
          </div>
          
          <div className="sidebar-section">
            <h3>◇ 면접 설정</h3>
            <div className="interview-controls">
              <button
                onClick={finishInterview}
                className="finish-interview-btn"
                disabled={interview.status === 'completed'}
              >
                면접 종료
              </button>
            </div>
          </div>
        </div>
        )}
      </div>
  )
}