#!/usr/bin/env python3
"""
간단한 API 키 헤더 전달 테스트
면접 시작 API가 API 키를 올바르게 받고 로깅하는지 확인
"""

import requests
import json

def test_header_transmission():
    """API 키 헤더 전달 및 로깅 테스트"""
    
    base_url = "http://127.0.0.1:8004"
    analysis_id = "85b50ffd-c902-4f7a-803b-790b6fd8e115"
    
    # 테스트용 API 키
    github_token = "ghp_test12345abcdefghijklmnopqrstuvwxyz"
    google_api_key = "AIzaSyTest123456789abcdefghijklmnopqrstuvwxyz"
    
    print("========== API 키 헤더 전달 테스트 ==========")
    print(f"Backend URL: {base_url}")
    print(f"Analysis ID: {analysis_id}")
    print(f"GitHub Token: {github_token[:15]}...")
    print(f"Google API Key: {google_api_key[:15]}...")
    
    # 1. 먼저 질문을 캐시에 직접 생성 (빠른 테스트를 위해)
    print("\n1. 테스트용 질문 캐시 생성...")
    cache_url = f"{base_url}/api/v1/questions/cache/test-questions"
    test_questions = [
        {
            "id": "test-q1",
            "question": "이 프로젝트의 주요 기술 스택에 대해 설명해주세요.",
            "type": "tech_stack",
            "difficulty": "medium"
        },
        {
            "id": "test-q2", 
            "question": "코드 품질을 높이기 위한 방법들을 제시해주세요.",
            "type": "code_quality",
            "difficulty": "medium"
        }
    ]
    
    # 2. 면접 시작 요청 (중요: API 키 헤더 포함)
    print("\n2. 면접 시작 요청 - API 키 헤더 확인...")
    interview_url = f"{base_url}/api/v1/interview/start"
    interview_data = {
        "repo_url": "https://github.com/microsoft/vscode",
        "analysis_id": analysis_id,
        "question_ids": ["test-q1", "test-q2"],  # 테스트 질문 ID 사용
        "interview_type": "technical",
        "difficulty_level": "medium"
    }
    
    # API 키를 헤더에 포함
    interview_headers = {
        "Content-Type": "application/json",
        "x-github-token": github_token,
        "x-google-api-key": google_api_key
    }
    
    print(f"요청 헤더:")
    print(f"  x-github-token: {github_token[:20]}...")
    print(f"  x-google-api-key: {google_api_key[:20]}...")
    
    try:
        print("\n실제 요청 전송 중...")
        response = requests.post(
            interview_url,
            json=interview_data,
            headers=interview_headers,
            timeout=30
        )
        
        print(f"\n응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 요청 성공!")
            print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 요청 실패")
            print(f"응답: {response.text}")
        
        # 백엔드 로그에서 다음과 같은 메시지가 나타나야 함:
        # [INTERVIEW_START] 받은 헤더:
        # [INTERVIEW_START]   - GitHub Token: 있음
        # [INTERVIEW_START]   - Google API Key: 있음
        # [INTERVIEW_START]   - GitHub Token 값: ghp_test12345...
        # [INTERVIEW_START]   - Google API Key 값: AIzaSyTest123...
        
        print("\n📋 백엔드 로그를 확인하세요:")
        print("  - [INTERVIEW_START] 받은 헤더: 섹션에서")
        print("  - GitHub Token: 있음")
        print("  - Google API Key: 있음")
        print("  - 각 키의 앞 20자리 값이 로깅되는지 확인")
        
    except Exception as e:
        print(f"❌ 요청 오류: {e}")

if __name__ == "__main__":
    test_header_transmission()