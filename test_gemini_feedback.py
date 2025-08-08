#!/usr/bin/env python3
"""
Google Gemini 기반 답변 피드백 시스템 테스트 스크립트
"""

import sys
import os
import asyncio
sys.path.append('/home/hong/code/techGiterview/src/backend')

# 환경변수 설정
os.environ["ENV"] = "development"

from app.services.answer_analyzer import answer_analyzer

async def test_gemini_feedback():
    """Google Gemini 기반 답변 피드백 테스트"""
    print("=" * 60)
    print("Google Gemini 기반 답변 피드백 시스템 테스트")
    print("=" * 60)
    
    # 샘플 질문
    question = {
        "id": "python_log_test",
        "question": "다음은 Python 개발자를 위한 기술 면접 질문입니다. 주어진 로그 파일(예: access.log)에서 특정 오류 메시지(예: \"Internal Server Error\")가 발생한 빈도와, 해당 오류가 발생한 시간대를 시간대별로 분석하는 Python 스크립트를 작성하는 방법을 설명하고, 실제 코드를 작성해주세요. 이때, 효율적인 파일 처리, 시간대 변환, 그리고 결과 출력을 고려해야 합니다. 로그 파일이 매우 클 경우, 메모리 효율성을 어떻게 개선할 수 있는지 설명해주세요.",
        "category": "tech_stack", 
        "difficulty": "medium",
        "context": "Python 로그 분석"
    }
    
    # 테스트 답변들
    test_answers = [
        # 매우 짧은 답변
        "모르겠어",
        
        # 기본 답변
        "Python에서 파일을 읽고 특정 문자열을 찾아서 카운트하면 됩니다. 시간은 datetime 모듈을 사용하면 됩니다.",
        
        # 중간 수준 답변
        """로그 파일 분석을 위해 다음과 같은 방법을 사용할 수 있습니다:

1. 파일 읽기: with open()을 사용해 파일을 안전하게 읽습니다
2. 정규표현식으로 오류 메시지와 시간을 추출합니다
3. datetime 모듈로 시간대별로 그룹화합니다
4. collections.Counter로 빈도를 계산합니다

대용량 파일의 경우 한 줄씩 읽어서 메모리 사용량을 줄일 수 있습니다.""",
        
        # 상세한 답변
        r"""로그 파일 분석을 위한 완전한 솔루션을 제시하겠습니다.

Python으로 로그 분석하는 코드:
```python
import re
import datetime
from collections import defaultdict, Counter

def analyze_log_errors(log_file_path, error_pattern="Internal Server Error"):
    error_counts = Counter()
    hourly_distribution = defaultdict(int)
    
    # 로그 패턴 정의
    log_pattern = re.compile(
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+|-)'
    )
    
    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if error_pattern in line:
                match = log_pattern.match(line)
                if match:
                    timestamp_str = match.group(2)
                    dt = datetime.datetime.strptime(
                        timestamp_str.split()[0], 
                        '%d/%b/%Y:%H:%M:%S'
                    )
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    hourly_distribution[hour_key] += 1
                    error_counts[error_pattern] += 1
    
    return error_counts, dict(sorted(hourly_distribution.items()))
```

메모리 효율성 개선 방안:
1. 스트리밍 처리: 파일 전체를 메모리에 로드하지 않고 한 줄씩 처리
2. 청크 기반 읽기: 대용량 파일을 일정 크기로 나누어 처리
3. 제너레이터 사용: 메모리 효율적인 데이터 처리
4. 멀티프로세싱: 파일을 여러 부분으로 나누어 병렬 처리

실제 운영에서는 ELK Stack이나 Fluentd 같은 전문 도구 사용을 권장합니다."""
    ]
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n[테스트 {i}] 답변 분석 결과:")
        print("-" * 40)
        print(f"답변: {answer[:100]}{'...' if len(answer) > 100 else ''}")
        
        try:
            feedback = await answer_analyzer.analyze_answer(question, answer)
            
            print(f"점수: {feedback.score}/10")
            print(f"메시지: {feedback.message}")
            print(f"피드백 타입: {feedback.feedback_type.value}")
            print(f"상세: {feedback.details}")
            print("개선 제안:")
            for suggestion in feedback.suggestions:
                print(f"  - {suggestion}")
            print()
            
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_feedback())