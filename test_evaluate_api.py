#!/usr/bin/env python3
"""
실제 Gemini API 연동 테스트 스크립트
"""

import asyncio
import json
from app.agents.mock_interview_agent import MockInterviewAgent

async def test_evaluate_answer():
    """evaluate_answer 메소드 직접 테스트"""
    
    print("🧪 MockInterviewAgent evaluate_answer 테스트 시작")
    
    # Agent 인스턴스 생성
    agent = MockInterviewAgent()
    
    # 테스트 데이터
    test_question = "`pyproject.toml` 파일을 기반으로 아래 질문에 답해주세요. **질문:** Django 프로젝트에서 `pyproject.toml` 파일에 `dynamic = [\"version\"]` 설정이 되어있습니다."
    test_answer = "모르겠어"
    test_context = {
        "category": "tech_stack",
        "difficulty": "medium",
        "expected_points": ["pyproject.toml 이해", "dynamic version 설정"]
    }
    
    print(f"📝 질문: {test_question[:50]}...")
    print(f"💬 답변: {test_answer}")
    print(f"🏷️  컨텍스트: {test_context}")
    print("\n" + "="*50)
    
    try:
        # 실제 API 호출
        print("🚀 Gemini API 호출 중...")
        result = await agent.evaluate_answer(
            question=test_question,
            answer=test_answer,
            context=test_context
        )
        
        print("✅ API 호출 성공!")
        print(f"📊 응답 구조: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"\n🎯 종합 점수: {data.get('overall_score', 'N/A')}/10")
            print(f"📈 세부 점수:")
            criteria_scores = data.get('criteria_scores', {})
            for criteria, score in criteria_scores.items():
                print(f"  - {criteria}: {score}/10")
            
            print(f"\n💡 피드백:")
            print(f"  {data.get('feedback', 'N/A')}")
            
            print(f"\n📝 개선 제안:")
            suggestions = data.get('suggestions', [])
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print(f"❌ 평가 실패: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"🚨 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_evaluate_answer())