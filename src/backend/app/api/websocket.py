"""
WebSocket API for Real-time Mock Interview

실시간 모의면접을 위한 WebSocket 엔드포인트
"""

import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.websockets import WebSocketState
import logging

from app.api.interview import interview_cache, InterviewSession

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
    """모의면접 WebSocket 엔드포인트"""
    
    user_id = f"user_{interview_id}"  # 임시 사용자 ID
    try:
        # 연결 수락
        await websocket.accept()
        
        # 면접 세션 확인
        if interview_id not in interview_cache:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "면접 세션을 찾을 수 없습니다."
            }))
            await websocket.close()
            return
            
        session = interview_cache[interview_id]
        if not isinstance(session, InterviewSession):
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "잘못된 면접 세션입니다."
            }))
            await websocket.close()
            return
        
        # 연결 등록
        await manager.connect(websocket, interview_id, user_id)
        
        # 환영 메시지
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "interview_id": interview_id,
            "message": "면접 세션에 연결되었습니다.",
            "status": session.status,
            "progress": {
                "current_question": session.current_question_index + 1,
                "total_questions": len(session.question_ids)
            }
        }))
        
        # 메시지 처리 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 메시지 타입별 처리
                response = await handle_interview_message(interview_id, message)
                
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


async def handle_interview_message(interview_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """면접 메시지 처리"""
    
    message_type = message.get("type")
    
    try:
        # 면접 세션 확인
        if interview_id not in interview_cache:
            return {
                "type": "error",
                "message": "면접 세션을 찾을 수 없습니다."
            }
            
        session = interview_cache[interview_id]
        if not isinstance(session, InterviewSession):
            return {
                "type": "error",
                "message": "잘못된 면접 세션입니다."
            }
        
        if message_type == "get_status":
            # 면접 상태 조회
            from datetime import datetime
            elapsed_time = int((datetime.utcnow() - session.started_at).total_seconds())
            
            return {
                "type": "status_update",
                "status": session.status,
                "progress": {
                    "current_question": session.current_question_index + 1,
                    "total_questions": len(session.question_ids),
                    "progress_percentage": round((session.current_question_index / len(session.question_ids)) * 100, 1)
                },
                "elapsed_time": elapsed_time,
                "remaining_time": max(0, session.expected_duration * 60 - elapsed_time)
            }
        
        elif message_type == "submit_answer":
            # 답변 제출
            answer = message.get("answer", "")
            time_taken = message.get("time_taken", 0)
            
            if not answer.strip():
                return {
                    "type": "error",
                    "message": "답변이 필요합니다."
                }
            
            # 답변 저장
            response_key = f"{interview_id}_responses"
            if response_key not in interview_cache:
                interview_cache[response_key] = []
            
            from app.api.interview import QuestionResponse
            response_obj = QuestionResponse(
                question_id=session.question_ids[session.current_question_index] if session.current_question_index < len(session.question_ids) else "unknown",
                question_text="",
                user_answer=answer,
                response_time=time_taken
            )
            
            interview_cache[response_key].append(response_obj)
            
            # 다음 질문으로 이동
            session.current_question_index += 1
            
            # 면접 완료 확인
            is_completed = session.current_question_index >= len(session.question_ids)
            if is_completed:
                session.status = "completed"
            
            interview_cache[interview_id] = session
            
            response = {
                "type": "answer_submitted",
                "message": "답변이 성공적으로 제출되었습니다.",
                "progress": {
                    "current_question": session.current_question_index + 1,
                    "total_questions": len(session.question_ids),
                    "is_completed": is_completed
                }
            }
            
            if is_completed:
                response["type"] = "interview_completed"
                response["message"] = "면접이 완료되었습니다!"
                
                # 간단한 결과 요약
                responses = interview_cache.get(response_key, [])
                response["summary"] = {
                    "total_questions": len(session.question_ids),
                    "answered_questions": len(responses),
                    "completion_rate": round((len(responses) / len(session.question_ids)) * 100, 1) if session.question_ids else 0,
                    "average_response_time": round(sum(r.response_time for r in responses) / len(responses), 1) if responses else 0
                }
            
            return response
        
        elif message_type == "pause_interview":
            # 면접 일시정지
            if session.status == "active":
                session.status = "paused"
                interview_cache[interview_id] = session
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
                session.status = "active"
                interview_cache[interview_id] = session
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
            session.status = "completed"
            interview_cache[interview_id] = session
            
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