#!/usr/bin/env python3
"""
실제 면접 답변 API 테스트
"""

import asyncio
import json
import requests

def test_interview_answer_api():
    """실제 면접 답변 API 테스트"""
    
    print("🧪 실제 면접 답변 API 테스트 시작")
    
    # 테스트 데이터 (올바른 UUID 형식 사용)
    import uuid
    test_payload = {
        "interview_id": str(uuid.uuid4()),
        "question_id": str(uuid.uuid4()),
        "answer": "모르겠어요. 하지만 관련된 경험을 말씀드리면...",
        "time_taken": 60
    }
    
    print(f"📝 테스트 요청:")
    print(f"  - Interview ID: {test_payload['interview_id']}")
    print(f"  - Question ID: {test_payload['question_id']}")  
    print(f"  - Answer: {test_payload['answer']}")
    print(f"  - Time: {test_payload['time_taken']}초")
    print("\n" + "="*50)
    
    try:
        # API 호출
        print("🚀 면접 답변 API 호출 중...")
        response = requests.post(
            "http://localhost:3001/api/v1/interview/answer",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")
            print(f"📄 응답 내용:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("success"):
                feedback = result.get("data", {}).get("feedback")
                if feedback:
                    print(f"\n🤖 Gemini AI 피드백:")
                    print(f"  점수: {feedback.get('overall_score', 'N/A')}/10")
                    print(f"  메시지: {feedback.get('feedback', 'N/A')}")
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"🔍 에러 내용: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"🚨 네트워크 오류: {str(e)}")
    except Exception as e:
        print(f"🚨 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    test_interview_answer_api()