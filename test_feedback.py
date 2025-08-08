#!/usr/bin/env python3
"""
답변 피드백 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append('/home/hong/code/techGiterview/src/backend')

from app.services.answer_analyzer import answer_analyzer

def test_docker_answer():
    """Docker 관련 답변 테스트"""
    print("=" * 50)
    print("Docker 레이어 캐싱 답변 테스트")
    print("=" * 50)
    
    # 샘플 질문
    question = {
        "id": "docker_test",
        "question": "Docker 이미지를 빌드할 때, 레이어 캐싱을 활용하여 빌드 시간을 단축하는 방법은?",
        "category": "technical", 
        "difficulty": "medium",
        "context": "Docker 최적화"
    }
    
    # 테스트 답변들
    test_answers = [
        # 우수한 답변
        """Docker 레이어 캐싱을 활용하면 빌드 시간을 대폭 단축할 수 있습니다. 

핵심은 Dockerfile의 명령어 순서를 최적화하는 것입니다. 자주 변경되지 않는 명령어(base image, system packages 설치)를 먼저 배치하고, 자주 변경되는 소스 코드 복사는 나중에 배치해야 합니다.

예를 들어:
```dockerfile
FROM node:16
COPY package.json package-lock.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
```

이렇게 하면 package.json이 변경되지 않는 한 npm install 레이어는 캐시에서 재사용됩니다.

또한 multi-stage build를 활용하여 최종 이미지 크기도 줄일 수 있습니다. 실제 프로덕션에서 이 방법으로 빌드 시간을 70% 단축했던 경험이 있습니다.""",
        
        # 보통 답변
        """Docker에서 레이어 캐싱을 사용하면 빌드가 빨라집니다. 
        
Dockerfile을 작성할 때 변경이 적은 것부터 먼저 쓰고, 소스코드 같이 자주 바뀌는 것은 나중에 써야 합니다. 

package.json 복사하고 npm install 한 다음에 소스코드를 복사하면 됩니다.""",
        
        # 개선 필요한 답변
        "모르겠어요. 캐시를 쓰면 빨라진다는 건 알겠는데 구체적으로 어떻게 하는지는 잘 모르겠습니다."
    ]
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n[테스트 {i}] 답변 분석 결과:")
        print("-" * 30)
        
        feedback = answer_analyzer.analyze_answer(question, answer)
        
        print(f"점수: {feedback.score}/10")
        print(f"메시지: {feedback.message}")
        print(f"피드백 타입: {feedback.feedback_type.value}")
        print(f"상세: {feedback.details}")
        print(f"찾은 키워드: {', '.join(feedback.keywords_found)}")
        print(f"누락 키워드: {', '.join(feedback.keywords_missing[:3])}")
        print(f"기술 정확성: {feedback.technical_accuracy}")
        print("개선 제안:")
        for suggestion in feedback.suggestions:
            print(f"  - {suggestion}")
        print()

def test_architecture_answer():
    """아키텍처 관련 답변 테스트"""
    print("=" * 50)
    print("마이크로서비스 아키텍처 답변 테스트") 
    print("=" * 50)
    
    question = {
        "id": "arch_test",
        "question": "마이크로서비스 아키텍처의 장단점과 도입 고려사항은?",
        "category": "architecture",
        "difficulty": "hard",
        "context": "시스템 설계"
    }
    
    answer = """마이크로서비스 아키텍처는 각 서비스가 독립적으로 배포되고 확장될 수 있어 장점이 많습니다.

장점:
- 서비스별 독립적인 배포와 확장 가능
- 기술 스택의 다양성 허용
- 장애 격리 효과
- 팀별 자율성 증대

단점:  
- 네트워크 통신 오버헤드 증가
- 분산 시스템 복잡도 상승
- 데이터 일관성 관리 어려움
- 모니터링과 디버깅 복잡

도입 고려사항:
- 팀 규모와 조직 구조 적합성
- API Gateway를 통한 라우팅 관리
- Service Mesh 도입 검토
- 분산 트랜잭션 패턴 (Saga, CQRS)
- 통합 모니터링 시스템 구축

실제 경험상 작은 서비스부터 점진적으로 분리하는 것이 안전합니다."""
    
    feedback = answer_analyzer.analyze_answer(question, answer)
    
    print(f"점수: {feedback.score}/10")
    print(f"메시지: {feedback.message}")
    print(f"찾은 키워드: {', '.join(feedback.keywords_found)}")
    print(f"누락 키워드: {', '.join(feedback.keywords_missing[:3])}")
    print("개선 제안:")
    for suggestion in feedback.suggestions:
        print(f"  - {suggestion}")

if __name__ == "__main__":
    test_docker_answer()
    test_architecture_answer()