#!/usr/bin/env python3
"""
피드백 점수 표시 문제 해결 테스트
현재 활성화된 면접 세션에서 실제 답변 제출
"""

import requests
import json

def test_feedback_fix():
    """실제 활성 세션에서 답변 제출하여 피드백 확인"""
    
    print("🧪 피드백 점수 표시 문제 해결 테스트")
    print("=" * 60)
    
    # 현재 활성화된 면접 세션 ID (백엔드 로그에서 확인)
    interview_id = "585ebd21-ad91-4cb8-8b31-920f17a7596f"
    
    # 첫 번째 질문 ID (Django 프로젝트의 첫 번째 질문)
    question_id = "452f4726-2edb-4e50-9762-b75b3c96e98c"
    
    # 테스트 답변 (의도적으로 짧은 답변)
    test_answer = "모르겠어요. pyproject.toml은 Python 프로젝트 설정 파일인데 정확한 내용은 잘 모르겠습니다."
    
    print(f"📝 테스트 데이터:")
    print(f"  - Interview ID: {interview_id}")
    print(f"  - Question ID: {question_id}")
    print(f"  - Answer: {test_answer}")
    print("\n" + "=" * 50)
    
    try:
        # 답변 제출 API 호출
        print("🚀 답변 제출 API 호출 중...")
        response = requests.post(
            "http://localhost:3001/api/v1/interview/answer",
            json={
                "interview_id": interview_id,
                "question_id": question_id,
                "answer": test_answer,
                "time_taken": 45
            },
            headers={"Content-Type": "application/json"},
            timeout=60  # Gemini API 호출 시간을 고려하여 60초로 설정
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
                    print(f"\n🤖 실제 피드백 데이터 확인:")
                    print(f"  📊 종합점수: {feedback.get('overall_score', 'N/A')}/10")
                    print(f"  💬 피드백: {feedback.get('feedback', 'N/A')}")
                    print(f"  📝 개선제안: {len(feedback.get('suggestions', []))}개")
                    
                    # 데이터 구조 확인
                    print(f"\n🔍 데이터 구조 분석:")
                    for key, value in feedback.items():
                        print(f"  - {key}: {type(value)} = {value if len(str(value)) < 100 else str(value)[:100] + '...'}")
                else:
                    print("❌ 피드백 데이터가 없습니다.")
            else:
                print(f"❌ API 응답 실패: {result.get('message', 'Unknown')}")
                
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"🔍 에러 내용: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  요청 시간 초과 (Gemini API 응답 대기 중일 수 있습니다)")
    except requests.exceptions.RequestException as e:
        print(f"🚨 네트워크 오류: {str(e)}")
    except Exception as e:
        print(f"🚨 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    test_feedback_fix()