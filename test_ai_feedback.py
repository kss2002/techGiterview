#!/usr/bin/env python3
"""
AI 기반 답변 피드백 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append('/home/hong/code/techGiterview/src/backend')

# 환경변수 설정 (OpenAI API 키 필요 시)
os.environ["OPENAI_API_KEY"] = "test_key"

from app.services.answer_analyzer import answer_analyzer

def test_simple_answers():
    """간단한 답변들 테스트"""
    print("=" * 50)
    print("AI 기반 답변 피드백 시스템 테스트")
    print("=" * 50)
    
    # 샘플 질문
    question = {
        "id": "docker_test",
        "question": "Docker 컨테이너 내부에서 실행되는 애플리케이션이 외부 네트워크에 연결해야 하는데, 보안상의 이유로 특정 IP 주소 대역에만 접근을 허용해야 합니다. Docker 네트워크 설정을 어떻게 구성하여 이러한 요구사항을 충족시킬 수 있는지 설명하고, 발생할 수 있는 문제점과 해결 방안에 대해 논의해 주세요.",
        "category": "technical", 
        "difficulty": "medium",
        "context": "Docker 네트워킹"
    }
    
    # 테스트 답변들
    test_answers = [
        # 매우 짧은 답변
        "모르겠어",
        
        # 기본 답변
        "Docker에서 네트워크 설정을 할 수 있습니다. iptables나 방화벽을 사용하면 됩니다.",
        
        # 상세한 답변
        """Docker 네트워크 보안 설정은 여러 계층에서 구현할 수 있습니다.

1. 사용자 정의 브리지 네트워크 생성:
```bash
docker network create --driver bridge secure-network
```

2. iptables 규칙으로 트래픽 제어:
- DOCKER-USER 체인에 규칙 추가
- 특정 IP 대역만 허용하는 규칙 설정

3. 컨테이너 실행 시 네트워크 지정:
```bash
docker run --network=secure-network myapp
```

발생 가능한 문제점:
- 복잡한 네트워크 설정으로 인한 관리 어려움
- 컨테이너 재시작 시 설정 초기화
- DNS 해결 문제

해결 방안:
- Docker Compose를 통한 설정 관리
- 네트워크 정책 자동화
- 모니터링 및 로깅 구축"""
    ]
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n[테스트 {i}] 답변 분석 결과:")
        print("-" * 30)
        print(f"답변: {answer[:50]}{'...' if len(answer) > 50 else ''}")
        
        feedback = answer_analyzer.analyze_answer(question, answer)
        
        print(f"점수: {feedback.score}/10")
        print(f"메시지: {feedback.message}")
        print(f"피드백 타입: {feedback.feedback_type.value}")
        print(f"상세: {feedback.details}")
        print("개선 제안:")
        for suggestion in feedback.suggestions:
            print(f"  - {suggestion}")
        print()

if __name__ == "__main__":
    test_simple_answers()