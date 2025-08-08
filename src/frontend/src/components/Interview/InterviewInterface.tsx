/**
 * Mock Interview Interface Component
 * 
 * 실시간 모의면접을 위한 메인 인터페이스 컴포넌트
 * WebSocket을 통한 실시간 커뮤니케이션 지원
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './InterviewInterface.css';

interface Question {
  id: string;
  type: string;
  question: string;
  code_snippet?: {
    content: string;
    language: string;
    file_path: string;
    complexity: number;
  };
  difficulty: string;
  time_estimate: string;
  introduction?: string;
}

interface Evaluation {
  overall_score: number;
  criteria_scores: {
    technical_accuracy: number;
    code_quality: number;
    problem_solving: number;
    communication: number;
  };
  feedback: string;
  suggestions: string[];
}

interface InterviewStatus {
  interview_id: string;
  status: 'preparing' | 'in_progress' | 'paused' | 'completed';
  progress: {
    current_question: number;
    total_questions: number;
    completed_questions: number;
  };
  elapsed_time: number;
  total_score: number;
}

const InterviewInterface: React.FC = () => {
  const { interviewId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();
  
  // WebSocket 연결
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  
  // 면접 상태
  const [interviewStatus, setInterviewStatus] = useState<InterviewStatus | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  
  // 타이머 관련
  const [timeRemaining, setTimeRemaining] = useState(600); // 10분 기본값
  const [isTimerActive, setIsTimerActive] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // UI 상태
  const [showEvaluation, setShowEvaluation] = useState(false);
  const [interviewCompleted, setInterviewCompleted] = useState(false);
  const [finalReport, setFinalReport] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // WebSocket 연결 설정
  const connectWebSocket = useCallback(() => {
    if (!interviewId) return;

    const wsUrl = `ws://localhost:8001/ws/interview/${interviewId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
      setError(null);
      
      // 초기 사용자 ID 전송 (실제로는 인증에서 가져와야 함)
      const userId = localStorage.getItem('user_id') || 'test_user';
      wsRef.current?.send(JSON.stringify({
        user_id: userId
      }));
    };

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
      
      // 재연결 시도 (5초 후)
      if (!interviewCompleted) {
        setTimeout(() => {
          connectWebSocket();
        }, 5000);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket 연결 오류가 발생했습니다.');
    };
  }, [interviewId, interviewCompleted]);

  // WebSocket 메시지 처리
  const handleWebSocketMessage = (message: any) => {
    console.log('Received message:', message);

    switch (message.type) {
      case 'connection_established':
        console.log('면접 세션에 연결됨');
        break;

      case 'interview_started':
        setCurrentQuestion(message.current_question);
        setInterviewStatus({
          interview_id: message.interview_id,
          status: 'in_progress',
          progress: {
            current_question: 1,
            total_questions: message.total_questions,
            completed_questions: 0
          },
          elapsed_time: 0,
          total_score: 0
        });
        setTimeRemaining(message.time_per_question);
        setIsTimerActive(true);
        break;

      case 'answer_evaluated':
        setEvaluation(message.evaluation);
        setShowEvaluation(true);
        setIsTimerActive(false);
        
        if (message.next_question) {
          setCurrentQuestion(message.next_question);
        }
        
        if (message.progress) {
          setInterviewStatus(prev => prev ? {
            ...prev,
            progress: message.progress
          } : null);
        }
        break;

      case 'interview_completed':
        setInterviewCompleted(true);
        setFinalReport(message.final_report);
        setIsTimerActive(false);
        break;

      case 'interview_paused':
        setIsTimerActive(false);
        setInterviewStatus(prev => prev ? { ...prev, status: 'paused' } : null);
        break;

      case 'interview_resumed':
        setIsTimerActive(true);
        setInterviewStatus(prev => prev ? { ...prev, status: 'in_progress' } : null);
        break;

      case 'error':
        setError(message.message);
        setIsSubmitting(false);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // 답변 제출
  const submitAnswer = useCallback(() => {
    if (!userAnswer.trim() || !wsConnected || isSubmitting) return;

    setIsSubmitting(true);
    setShowEvaluation(false);
    
    const timeTaken = timeRemaining > 0 ? (600 - timeRemaining) : 600;

    wsRef.current?.send(JSON.stringify({
      type: 'submit_answer',
      answer: userAnswer.trim(),
      time_taken: timeTaken
    }));

    setUserAnswer('');
    setIsTimerActive(false);
  }, [userAnswer, wsConnected, isSubmitting, timeRemaining]);

  // 다음 질문으로 이동
  const moveToNextQuestion = useCallback(() => {
    setShowEvaluation(false);
    setEvaluation(null);
    setTimeRemaining(600);
    setIsTimerActive(true);
    setIsSubmitting(false);
  }, []);

  // 면접 일시정지/재개
  const togglePause = useCallback(() => {
    if (!wsConnected) return;

    const action = interviewStatus?.status === 'paused' ? 'resume_interview' : 'pause_interview';
    wsRef.current?.send(JSON.stringify({ type: action }));
  }, [wsConnected, interviewStatus?.status]);

  // 면접 종료
  const endInterview = useCallback(() => {
    if (!wsConnected) return;

    wsRef.current?.send(JSON.stringify({ type: 'end_interview' }));
  }, [wsConnected]);

  // 타이머 관리
  useEffect(() => {
    if (isTimerActive && timeRemaining > 0) {
      timerRef.current = setTimeout(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
    } else if (timeRemaining === 0 && isTimerActive) {
      // 시간 초과 시 자동 제출
      setIsTimerActive(false);
      if (userAnswer.trim()) {
        submitAnswer();
      } else {
        wsRef.current?.send(JSON.stringify({
          type: 'submit_answer',
          answer: '시간이 초과되어 답변을 제출하지 못했습니다.',
          time_taken: 600
        }));
      }
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isTimerActive, timeRemaining, userAnswer, submitAnswer]);

  // WebSocket 연결 초기화
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [connectWebSocket]);

  // 시간 포맷팅
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // 면접 시작 (개발용)
  const startInterview = () => {
    if (!wsConnected) return;

    const repoUrl = localStorage.getItem('repo_url') || 'https://github.com/facebook/react';
    wsRef.current?.send(JSON.stringify({
      type: 'start_interview',
      repo_url: repoUrl,
      difficulty_level: 'medium',
      question_count: 5,
      time_per_question: 600
    }));
  };

  if (interviewCompleted && finalReport) {
    return (
      <div className="interview-completed">
        <h2>면접이 완료되었습니다!</h2>
        <div className="final-report">
          <div className="score-summary">
            <h3>총점: {finalReport.total_score}/10</h3>
            <p>소요 시간: {Math.floor(finalReport.total_duration / 60)}분 {finalReport.total_duration % 60}초</p>
          </div>
          
          <div className="feedback-section">
            <h4>전체 피드백</h4>
            <ul>
              {finalReport.overall_feedback.map((feedback: string, index: number) => (
                <li key={index}>{feedback}</li>
              ))}
            </ul>
          </div>
          
          <div className="recommendations">
            <h4>개선 권장사항</h4>
            <ul>
              {finalReport.recommendations.map((rec: string, index: number) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
          
          <button onClick={() => navigate('/dashboard')} className="return-button">
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-interface">
      <div className="interview-header">
        <div className="status-info">
          <span className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '연결됨' : '연결 끊김'}
          </span>
          {interviewStatus && (
            <span className="progress">
              {interviewStatus.progress.current_question} / {interviewStatus.progress.total_questions}
            </span>
          )}
        </div>
        
        <div className="timer">
          <span className={timeRemaining < 60 ? 'warning' : ''}>
            남은 시간: {formatTime(timeRemaining)}
          </span>
        </div>
        
        <div className="controls">
          <button onClick={togglePause} disabled={!wsConnected}>
            {interviewStatus?.status === 'paused' ? '재개' : '일시정지'}
          </button>
          <button onClick={endInterview} disabled={!wsConnected} className="end-button">
            면접 종료
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {!currentQuestion ? (
        <div className="interview-setup">
          <h2>면접 준비</h2>
          <p>면접을 시작하려면 아래 버튼을 클릭하세요.</p>
          <button onClick={startInterview} disabled={!wsConnected}>
            면접 시작
          </button>
        </div>
      ) : (
        <>
          <div className="question-section">
            <div className="question-header">
              <h3>질문 {interviewStatus?.progress.current_question}</h3>
              <span className="question-type">{currentQuestion.type}</span>
              <span className="difficulty">{currentQuestion.difficulty}</span>
            </div>
            
            {currentQuestion.introduction && (
              <div className="question-introduction">
                {currentQuestion.introduction}
              </div>
            )}
            
            <div className="question-content">
              <p>{currentQuestion.question}</p>
            </div>
            
            {currentQuestion.code_snippet && (
              <div className="code-snippet">
                <div className="code-header">
                  <span>{currentQuestion.code_snippet.file_path}</span>
                  <span>{currentQuestion.code_snippet.language}</span>
                </div>
                <pre><code>{currentQuestion.code_snippet.content}</code></pre>
              </div>
            )}
          </div>

          <div className="answer-section">
            <textarea
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="답변을 입력하세요..."
              disabled={isSubmitting || interviewStatus?.status === 'paused'}
              rows={10}
            />
            
            <div className="answer-controls">
              <span className="char-count">{userAnswer.length} 글자</span>
              <button
                onClick={submitAnswer}
                disabled={!userAnswer.trim() || !wsConnected || isSubmitting}
                className="submit-button"
              >
                {isSubmitting ? '제출 중...' : '답변 제출'}
              </button>
            </div>
          </div>

          {showEvaluation && evaluation && (
            <div className="evaluation-section">
              <h4>평가 결과</h4>
              <div className="score-display">
                <span className="overall-score">
                  전체 점수: {evaluation.overall_score}/10
                </span>
              </div>
              
              <div className="criteria-scores">
                <div>기술적 정확성: {evaluation.criteria_scores.technical_accuracy}/10</div>
                <div>코드 품질: {evaluation.criteria_scores.code_quality}/10</div>
                <div>문제 해결: {evaluation.criteria_scores.problem_solving}/10</div>
                <div>의사소통: {evaluation.criteria_scores.communication}/10</div>
              </div>
              
              <div className="feedback">
                <p><strong>피드백:</strong> {evaluation.feedback}</p>
              </div>
              
              {evaluation.suggestions.length > 0 && (
                <div className="suggestions">
                  <strong>개선 제안:</strong>
                  <ul>
                    {evaluation.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <button onClick={moveToNextQuestion} className="next-button">
                다음 질문으로
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default InterviewInterface;