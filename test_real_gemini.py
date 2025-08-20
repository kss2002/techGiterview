#!/usr/bin/env python3
"""
실제 Gemini API 직접 테스트 - 다양한 답변으로
"""

import asyncio
import json
import sys
import os
sys.path.append('/home/hong/code/techGiterview/src/backend')

from app.agents.mock_interview_agent import MockInterviewAgent

async def test_various_answers():
    """다양한 답변으로 Gemini 테스트"""
    
    print("🧪 다양한 답변으로 실제 Gemini 테스트")
    print("="*60)
    
    # Agent 인스턴스 생성
    agent = MockInterviewAgent()
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "짧은 '모르겠다' 답변",
            "question": "Django에서 ORM과 Raw SQL의 차이점과 각각의 장단점에 대해 설명해주세요.",
            "answer": "모르겠어요",
            "context": {"category": "backend", "difficulty": "medium"}
        },
        {
            "name": "성의없는 답변", 
            "question": "REST API와 GraphQL의 차이점에 대해 설명해주세요.",
            "answer": "REST는 REST고 GraphQL은 GraphQL입니다.",
            "context": {"category": "api", "difficulty": "medium"}
        },
        {
            "name": "좋은 답변",
            "question": "JavaScript의 호이스팅(Hoisting)에 대해 설명해주세요.",
            "answer": "호이스팅은 JavaScript의 실행 컨텍스트 생성 과정에서 변수 선언과 함수 선언이 해당 스코프의 최상단으로 끌어올려지는 것처럼 동작하는 특성입니다. var로 선언된 변수는 undefined로 초기화되어 호이스팅되고, let/const는 호이스팅되지만 TDZ(Temporal Dead Zone)에 있어 접근할 수 없습니다. 함수 선언문은 완전히 호이스팅되어 선언 전에도 호출 가능합니다.",
            "context": {"category": "javascript", "difficulty": "medium"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        print(f"❓ 질문: {test_case['question'][:60]}...")
        print(f"💬 답변: {test_case['answer']}")
        print(f"🏷️  카테고리: {test_case['context']['category']}")
        print("-" * 40)
        
        try:
            print("🚀 Gemini 평가 중...")
            result = await agent.evaluate_answer(
                question=test_case['question'],
                answer=test_case['answer'],
                context=test_case['context']
            )
            
            if result.get("success"):
                data = result.get("data", {})
                print(f"✅ 평가 성공!")
                print(f"🎯 종합점수: {data.get('overall_score', 'N/A')}/10")
                
                print(f"📊 세부점수:")
                scores = data.get('criteria_scores', {})
                for criteria, score in scores.items():
                    print(f"  - {criteria}: {score}/10")
                
                feedback = data.get('feedback', '')
                print(f"💡 피드백: {feedback[:100]}...")
                
                suggestions = data.get('suggestions', [])
                print(f"📝 개선제안: {len(suggestions)}개")
                for j, suggestion in enumerate(suggestions[:2], 1):
                    print(f"  {j}. {suggestion[:80]}...")
                    
            else:
                print(f"❌ 평가 실패: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"🚨 오류 발생: {str(e)}")
        
        print("=" * 60)
        await asyncio.sleep(1)  # API 호출 간격

if __name__ == "__main__":
    asyncio.run(test_various_answers())