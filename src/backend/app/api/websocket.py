"""
WebSocket API for Real-time Mock Interview

실시간 모의면접을 위한 WebSocket 엔드포인트 - 데이터베이스 기반
"""

import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.interview_repository import InterviewRepository

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 활성 WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> interview_id
    
    async def connect(self, websocket: WebSocket, interview_id: str, user_id: str):
        """WebSocket 연결"""
        await websocket.accept()
        self.active_connections[interview_id] = websocket
        self.user_sessions[user_id] = interview_id
        logger.info(f"WebSocket connected: interview_id={interview_id}, user_id={user_id}")
    
    def disconnect(self, interview_id: str, user_id: str):
        """WebSocket 연결 해제"""
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"WebSocket disconnected: interview_id={interview_id}, user_id={user_id}")
    
    async def send_personal_message(self, message: str, interview_id: str):
        """개별 메시지 전송"""
        if interview_id in self.active_connections:
            websocket = self.active_connections[interview_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    # 연결이 끊어진 경우 제거
                    if interview_id in self.active_connections:
                        del self.active_connections[interview_id]

manager = ConnectionManager()


@router.websocket("/interview/{interview_id}")
async def websocket_interview_endpoint(websocket: WebSocket, interview_id: str):
    """모의면접 WebSocket 엔드포인트 - 데이터베이스 기반"""
    
    user_id = f"user_{interview_id}"  # 임시 사용자 ID
    db = None
    
    try:
        # DB 연결 (WebSocket에서는 Depends 사용 불가하므로 직접 생성)
        from app.core.database import SessionLocal
        db = SessionLocal()
        repo = InterviewRepository(db)
        
        # 연결 수락
        await websocket.accept()
        
        # 면접 세션 확인 
        import uuid
        try:
            session_uuid = uuid.UUID(interview_id)
        except ValueError:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "올바르지 않은 면접 ID 형식입니다."
            }))
            await websocket.close()
            return
            
        session = repo.get_session(session_uuid)
        if not session:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "면접 세션을 찾을 수 없습니다."
            }))
            await websocket.close()
            return
        
        # 연결 등록
        await manager.connect(websocket, interview_id, user_id)
        
        # 현재 진행상황 계산
        session_data = repo.get_session_with_details(session_uuid)
        progress = session_data['progress'] if session_data else {
            'current_question': 1,
            'total_questions': 0,
            'progress_percentage': 0
        }
        
        # 환영 메시지
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "interview_id": interview_id,
            "message": "면접 세션에 연결되었습니다.",
            "status": session.status,
            "progress": progress
        }))
        
        # 메시지 처리 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 메시지 타입별 처리
                response = await handle_interview_message(interview_id, message, repo)
                
                # 응답 전송
                await websocket.send_text(json.dumps(response))
                
                # 면접 완료 시 연결 종료
                if response.get("type") == "interview_completed":
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {interview_id}")
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "잘못된 JSON 형식입니다."
                }))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"메시지 처리 중 오류 발생: {str(e)}"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # 연결 정리
        if user_id:
            manager.disconnect(interview_id, user_id)
        if db:
            db.close()


async def handle_interview_message(interview_id: str, message: Dict[str, Any], repo: InterviewRepository) -> Dict[str, Any]:
    """면접 메시지 처리 - 데이터베이스 기반"""
    
    message_type = message.get("type")
    
    try:
        # 면접 세션 확인
        import uuid
        try:
            session_uuid = uuid.UUID(interview_id)
        except ValueError:
            return {
                "type": "error",
                "message": "올바르지 않은 면접 ID 형식입니다."
            }
            
        session = repo.get_session(session_uuid)
        if not session:
            return {
                "type": "error",
                "message": "면접 세션을 찾을 수 없습니다."
            }
        
        if message_type == "get_status":
            # 면접 상태 조회
            session_data = repo.get_session_with_details(session_uuid)
            progress = session_data['progress'] if session_data else {
                'current_question': 1,
                'total_questions': 0,
                'progress_percentage': 0,
                'elapsed_time': 0,
                'remaining_time': 0
            }
            
            return {
                "type": "status_update",
                "status": session.status,
                "progress": progress
            }
        
        elif message_type == "submit_answer":
            # 답변 제출
            answer = message.get("answer", "")
            time_taken = message.get("time_taken", 0)
            question_id = message.get("question_id")
            
            if not answer.strip():
                return {
                    "type": "error",
                    "message": "답변이 필요합니다."
                }
            
            if not question_id:
                return {
                    "type": "error", 
                    "message": "질문 ID가 필요합니다."
                }
            
            try:
                question_uuid = uuid.UUID(question_id)
            except ValueError:
                return {
                    "type": "error",
                    "message": "올바르지 않은 질문 ID 형식입니다."
                }
            
            # 답변 저장
            answer_data = {
                "answer": answer,
                "time_taken": time_taken
            }
            
            saved_answer = repo.save_answer(session_uuid, question_uuid, answer_data)
            
            # 진행상황 업데이트
            session_data = repo.get_session_with_details(session_uuid)
            progress = session_data['progress'] if session_data else {}
            
            # 면접 완료 확인 
            from app.models.interview import InterviewQuestion
            total_questions = repo.db.query(InterviewQuestion).filter(
                InterviewQuestion.analysis_id == session.analysis_id
            ).count()
            
            answered_questions = len(session_data['answers']) if session_data else 0
            is_completed = answered_questions >= total_questions
            
            if is_completed:
                repo.update_session_status(session_uuid, "completed")
            
            response = {
                "type": "answer_submitted",
                "message": "답변이 성공적으로 제출되었습니다.",
                "progress": progress,
                "is_completed": is_completed
            }
            
            if is_completed:
                response["type"] = "interview_completed"
                response["message"] = "면접이 완료되었습니다!"
                response["summary"] = {
                    "total_questions": total_questions,
                    "answered_questions": answered_questions,
                    "completion_rate": round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0
                }
            
            return response
        
        elif message_type == "pause_interview":
            # 면접 일시정지
            if session.status == "active":
                repo.update_session_status(session_uuid, "paused")
                return {
                    "type": "interview_paused",
                    "message": "면접이 일시정지되었습니다."
                }
            else:
                return {
                    "type": "error",
                    "message": "활성화된 면접만 일시정지할 수 있습니다."
                }
        
        elif message_type == "resume_interview":
            # 면접 재개
            if session.status == "paused":
                repo.update_session_status(session_uuid, "active")
                return {
                    "type": "interview_resumed",
                    "message": "면접이 재개되었습니다."
                }
            else:
                return {
                    "type": "error",
                    "message": "일시정지된 면접만 재개할 수 있습니다."
                }
        
        elif message_type == "end_interview":
            # 면접 강제 종료
            repo.update_session_status(session_uuid, "completed")
            
            return {
                "type": "interview_ended",
                "message": "면접이 종료되었습니다."
            }
        
        elif message_type == "heartbeat":
            # 연결 상태 확인
            return {
                "type": "heartbeat_response",
                "timestamp": message.get("timestamp"),
                "interview_status": session.status
            }
        
        else:
            return {
                "type": "error",
                "message": f"알 수 없는 메시지 타입: {message_type}"
            }
    
    except Exception as e:
        logger.error(f"Error in handle_interview_message: {e}")
        return {
            "type": "error",
            "message": f"메시지 처리 중 오류 발생: {str(e)}"
        }


# 개발용 테스트 엔드포인트
@router.websocket("/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """WebSocket 테스트 엔드포인트"""
    
    await websocket.accept()
    
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_test",
            "message": "WebSocket 연결 테스트 성공"
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 에코 응답
            await websocket.send_text(json.dumps({
                "type": "echo",
                "original_message": message,
                "timestamp": message.get("timestamp")
            }))
            
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")
    except Exception as e:
        logger.error(f"Test WebSocket error: {e}")