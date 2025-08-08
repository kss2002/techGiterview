"""
Mock Interview System 테스트

Mock Interview Agent와 WebSocket 기능 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.mock_interview_agent import MockInterviewAgent, InterviewState


class TestMockInterviewAgent:
    """Mock Interview Agent 테스트"""
    
    @pytest.mark.asyncio
    async def test_start_interview(self):
        """면접 시작 테스트"""
        # Given
        agent = MockInterviewAgent()
        repo_url = "https://github.com/test/repo"
        user_id = "test_user"
        
        # Mock QuestionGenerator
        mock_questions = {
            "success": True,
            "questions": [
                {
                    "id": "q1",
                    "type": "code_analysis",
                    "question": "이 코드의 복잡도를 분석해주세요.",
                    "difficulty": "medium"
                },
                {
                    "id": "q2", 
                    "type": "tech_stack",
                    "question": "React의 장단점을 설명해주세요.",
                    "difficulty": "medium"
                }
            ]
        }
        
        with patch.object(agent.question_generator, 'generate_questions', return_value=mock_questions):
            # When
            result = await agent.start_interview(repo_url, user_id)
        
        # Then
        assert result["success"] is True
        assert "interview_id" in result
        assert result["total_questions"] == 2
        assert "current_question" in result
        assert result["difficulty_level"] == "medium"
        
        # 활성 세션에 추가되었는지 확인
        interview_id = result["interview_id"]
        assert interview_id in agent.active_sessions
        
        state = agent.active_sessions[interview_id]
        assert state.repo_url == repo_url
        assert state.user_id == user_id
        assert state.interview_status == "in_progress"
        assert len(state.questions) == 2
    
    @pytest.mark.asyncio
    async def test_submit_answer(self):
        """답변 제출 및 평가 테스트"""
        # Given
        agent = MockInterviewAgent()
        
        # 면접 상태 설정
        interview_id = "test_interview_id"
        state = InterviewState(
            interview_id=interview_id,
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            questions=[
                {
                    "id": "q1",
                    "type": "code_analysis", 
                    "question": "이 코드의 복잡도를 분석해주세요.",
                    "difficulty": "medium"
                }
            ],
            interview_status="in_progress"
        )
        
        agent.active_sessions[interview_id] = state
        
        # When
        result = await agent.submit_answer(
            interview_id=interview_id,
            answer="이 코드는 O(n) 복잡도를 가집니다.",
            time_taken=120
        )
        
        # Then
        assert result["success"] is True
        assert "evaluation" in result
        assert "progress" in result
        
        evaluation = result["evaluation"]
        assert "overall_score" in evaluation
        assert "criteria_scores" in evaluation
        assert "feedback" in evaluation
        
        # 답변이 저장되었는지 확인
        assert len(state.answers) == 1
        assert state.answers[0]["answer"] == "이 코드는 O(n) 복잡도를 가집니다."
        assert state.answers[0]["time_taken"] == 120
        
        # 평가가 저장되었는지 확인
        assert len(state.evaluations) == 1
    
    @pytest.mark.asyncio
    async def test_get_interview_status(self):
        """면접 상태 조회 테스트"""
        # Given
        agent = MockInterviewAgent()
        interview_id = "test_interview_id"
        
        state = InterviewState(
            interview_id=interview_id,
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            questions=[{"id": "q1"}, {"id": "q2"}, {"id": "q3"}],
            current_question_index=1,
            interview_status="in_progress",
            start_time=datetime.now()
        )
        
        # 일부 답변 추가
        state.answers = [{"question_id": "q1", "answer": "첫 번째 답변"}]
        
        agent.active_sessions[interview_id] = state
        
        # When
        result = await agent.get_interview_status(interview_id)
        
        # Then
        assert result["success"] is True
        assert result["interview_id"] == interview_id
        assert result["status"] == "in_progress"
        assert result["progress"]["current_question"] == 2  # 1-based
        assert result["progress"]["total_questions"] == 3
        assert result["progress"]["completed_questions"] == 1
        assert "elapsed_time" in result
    
    @pytest.mark.asyncio
    async def test_pause_resume_interview(self):
        """면접 일시정지/재개 테스트"""
        # Given
        agent = MockInterviewAgent()
        interview_id = "test_interview_id"
        
        state = InterviewState(
            interview_id=interview_id,
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            interview_status="in_progress"
        )
        
        agent.active_sessions[interview_id] = state
        
        # When - 일시정지
        pause_result = await agent.pause_interview(interview_id)
        
        # Then
        assert pause_result["success"] is True
        assert state.interview_status == "paused"
        
        # When - 재개
        resume_result = await agent.resume_interview(interview_id)
        
        # Then
        assert resume_result["success"] is True
        assert state.interview_status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_end_interview(self):
        """면접 종료 테스트"""
        # Given
        agent = MockInterviewAgent()
        interview_id = "test_interview_id"
        
        state = InterviewState(
            interview_id=interview_id,
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            interview_status="in_progress",
            start_time=datetime.now()
        )
        
        # 일부 평가 추가
        state.evaluations = [
            {"overall_score": 8.0},
            {"overall_score": 7.5}
        ]
        
        agent.active_sessions[interview_id] = state
        
        # When
        result = await agent.end_interview(interview_id)
        
        # Then
        assert result["success"] is True
        assert state.interview_status == "completed"
        assert state.end_time is not None
        assert state.total_score == 7.75  # 평균
        assert len(state.feedback) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_answer(self):
        """답변 평가 테스트"""
        # Given
        agent = MockInterviewAgent()
        
        question = {
            "id": "q1",
            "type": "code_analysis",
            "question": "이 코드의 복잡도를 분석해주세요."
        }
        
        answer = "이 코드는 중첩된 반복문으로 인해 O(n²) 복잡도를 가집니다."
        
        state = InterviewState(
            interview_id="test_id",
            repo_url="https://github.com/test/repo",
            user_id="test_user"
        )
        
        # When
        evaluation = await agent._evaluate_answer(question, answer, state)
        
        # Then
        assert "overall_score" in evaluation
        assert "criteria_scores" in evaluation
        assert "feedback" in evaluation
        assert "suggestions" in evaluation
        
        assert 0 <= evaluation["overall_score"] <= 10
        
        criteria_scores = evaluation["criteria_scores"]
        assert "technical_accuracy" in criteria_scores
        assert "code_quality" in criteria_scores
        assert "problem_solving" in criteria_scores
        assert "communication" in criteria_scores
        
        for score in criteria_scores.values():
            assert 0 <= score <= 10
    
    @pytest.mark.asyncio
    async def test_should_generate_follow_up(self):
        """후속 질문 생성 여부 결정 테스트"""
        # Given
        agent = MockInterviewAgent()
        
        state = InterviewState(
            interview_id="test_id",
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            follow_up_count=0
        )
        
        # 낮은 점수 평가
        low_score_evaluation = {
            "overall_score": 5.0,
            "criteria_scores": {
                "technical_accuracy": 4.0,
                "code_quality": 5.0,
                "problem_solving": 6.0,
                "communication": 5.0
            }
        }
        
        # 높은 점수 평가
        high_score_evaluation = {
            "overall_score": 9.0,
            "criteria_scores": {
                "technical_accuracy": 9.0,
                "code_quality": 9.0,
                "problem_solving": 9.0,
                "communication": 9.0
            }
        }
        
        # 평균 점수 평가
        average_evaluation = {
            "overall_score": 7.0,
            "criteria_scores": {
                "technical_accuracy": 7.0,
                "code_quality": 7.0,
                "problem_solving": 7.0,
                "communication": 7.0
            }
        }
        
        # When & Then
        assert await agent._should_generate_follow_up(low_score_evaluation, state) is True
        assert await agent._should_generate_follow_up(high_score_evaluation, state) is True
        assert await agent._should_generate_follow_up(average_evaluation, state) is False
        
        # 후속 질문 제한 테스트
        state.follow_up_count = 2
        assert await agent._should_generate_follow_up(low_score_evaluation, state) is False
    
    @pytest.mark.asyncio
    async def test_get_interview_report(self):
        """면접 리포트 생성 테스트"""
        # Given
        agent = MockInterviewAgent()
        interview_id = "test_interview_id"
        
        state = InterviewState(
            interview_id=interview_id,
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            interview_status="completed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            difficulty_level="medium",
            total_score=8.5,
            follow_up_count=1
        )
        
        # 답변과 평가 추가
        state.answers = [
            {
                "question_id": "q1",
                "question": "첫 번째 질문",
                "answer": "첫 번째 답변"
            }
        ]
        
        state.evaluations = [
            {
                "overall_score": 8.5,
                "criteria_scores": {
                    "technical_accuracy": 8.0,
                    "code_quality": 8.5,
                    "problem_solving": 8.5,
                    "communication": 9.0
                }
            }
        ]
        
        state.feedback = ["우수한 답변이었습니다."]
        
        agent.active_sessions[interview_id] = state
        
        # When
        result = await agent.get_interview_report(interview_id)
        
        # Then
        assert result["success"] is True
        
        report = result["report"]
        assert report["interview_id"] == interview_id
        assert report["repo_url"] == "https://github.com/test/repo"
        assert report["user_id"] == "test_user"
        assert report["difficulty_level"] == "medium"
        assert report["total_score"] == 8.5
        assert report["questions_answered"] == 1
        assert report["follow_up_questions"] == 1
        assert "start_time" in report
        assert "end_time" in report
        assert "total_duration" in report
        assert "overall_feedback" in report
        assert "detailed_evaluation" in report
        assert "answers" in report
        assert "recommendations" in report
    
    def test_calculate_elapsed_time(self):
        """경과 시간 계산 테스트"""
        # Given
        agent = MockInterviewAgent()
        
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 30)  # 5분 30초 후
        
        state = InterviewState(
            interview_id="test_id",
            repo_url="https://github.com/test/repo",
            user_id="test_user",
            start_time=start_time,
            end_time=end_time
        )
        
        # When
        elapsed_time = agent._calculate_elapsed_time(state)
        
        # Then
        assert elapsed_time == 330  # 5분 30초 = 330초
    
    def test_interview_state_initialization(self):
        """면접 상태 초기화 테스트"""
        # Given & When
        state = InterviewState(
            interview_id="test_id",
            repo_url="https://github.com/test/repo",
            user_id="test_user"
        )
        
        # Then
        assert state.interview_id == "test_id"
        assert state.repo_url == "https://github.com/test/repo"
        assert state.user_id == "test_user"
        assert state.current_question_index == 0
        assert state.questions == []
        assert state.answers == []
        assert state.evaluations == []
        assert state.interview_status == "preparing"
        assert state.start_time is None
        assert state.end_time is None
        assert state.difficulty_level == "medium"
        assert state.total_score == 0.0
        assert state.feedback == []
        assert state.conversation_history == []
        assert state.follow_up_count == 0
        assert state.time_per_question == 600
        assert state.error is None


class TestMockInterviewIntegration:
    """Mock Interview 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_interview_flow(self):
        """완전한 면접 플로우 테스트"""
        # Given
        agent = MockInterviewAgent()
        repo_url = "https://github.com/test/repo"
        user_id = "test_user"
        
        # Mock QuestionGenerator
        mock_questions = {
            "success": True,
            "questions": [
                {
                    "id": "q1",
                    "type": "code_analysis",
                    "question": "이 코드의 복잡도를 분석해주세요.",
                    "difficulty": "medium"
                }
            ]
        }
        
        with patch.object(agent.question_generator, 'generate_questions', return_value=mock_questions):
            # 1. 면접 시작
            start_result = await agent.start_interview(repo_url, user_id)
            assert start_result["success"] is True
            
            interview_id = start_result["interview_id"]
            
            # 2. 첫 번째 답변 제출
            answer_result = await agent.submit_answer(
                interview_id=interview_id,
                answer="이 코드는 O(n) 복잡도를 가집니다.",
                time_taken=180
            )
            assert answer_result["success"] is True
            assert answer_result["interview_completed"] is True  # 질문이 1개뿐이므로
            
            # 3. 면접 리포트 생성
            report_result = await agent.get_interview_report(interview_id)
            assert report_result["success"] is True
            
            report = report_result["report"]
            assert report["questions_answered"] == 1
            assert len(report["detailed_evaluation"]) == 1
            assert len(report["answers"]) == 1