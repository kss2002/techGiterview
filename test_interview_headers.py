#!/usr/bin/env python3
"""
면접 시작 API 헤더 테스트 스크립트
프로덕션 환경과 유사한 조건으로 API 키 헤더를 포함한 면접 시작 요청 테스트
"""

import asyncio
import json
import requests
from typing import Dict, Any

async def test_interview_start_with_headers():
    """API 키 헤더를 포함한 면접 시작 테스트"""
    
    # 테스트 데이터
    base_url = "http://127.0.0.1:8004"
    analysis_id = "85b50ffd-c902-4f7a-803b-790b6fd8e115"  # 기존 분석 ID
    repo_url = "https://github.com/microsoft/vscode"
    
    # 테스트용 API 키 (실제로는 localStorage에서 가져옴)
    github_token = "github_pat_11ABCDEFGH_1234567890abcdefghijklmnopqrstuvwxyz"
    google_api_key = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    
    print("========== 면접 시작 API 헤더 테스트 ==========")
    print(f"Backend URL: {base_url}")
    print(f"Analysis ID: {analysis_id}")
    print(f"GitHub Token: {github_token[:20]}...")
    print(f"Google API Key: {google_api_key[:20]}...")
    
    # 1. 먼저 질문 생성 (질문 캐시 확인용)
    print("\n1. 질문 캐시 상태 확인...")
    questions_url = f"{base_url}/api/v1/questions/generate"
    questions_data = {
        "repo_url": repo_url,
        "analysis_id": analysis_id,
        "question_count": 3,
        "difficulty_level": "medium"
    }
    questions_headers = {
        "Content-Type": "application/json",
        "x-github-token": github_token,
        "x-google-api-key": google_api_key
    }
    
    try:
        questions_response = requests.post(
            questions_url, 
            json=questions_data,
            headers=questions_headers,
            timeout=30
        )
        print(f"질문 생성 응답: {questions_response.status_code}")
        if questions_response.status_code == 200:
            questions_result = questions_response.json()
            questions_data = questions_result.get('data', {}).get('questions', [])
            print(f"질문 수: {len(questions_data)}")
            if questions_data:
                question_ids = [q["id"] for q in questions_data]
                print(f"질문 ID들: {question_ids}")
            else:
                print("질문이 생성되지 않았습니다. 테스트용 질문 ID 사용...")
                # 테스트용 질문 ID 생성
                question_ids = [
                    "q1-test-header-validation",
                    "q2-test-header-validation",
                    "q3-test-header-validation"
                ]
        else:
            print(f"질문 생성 실패: {questions_response.text}")
            print("테스트용 질문 ID 사용...")
            question_ids = [
                "q1-test-header-validation",
                "q2-test-header-validation", 
                "q3-test-header-validation"
            ]
            
    except Exception as e:
        print(f"질문 생성 요청 오류: {e}")
        return
    
    # 2. 면접 시작 요청 (API 키 헤더 포함)
    print("\n2. 면접 시작 요청 (API 키 헤더 포함)...")
    interview_url = f"{base_url}/api/v1/interview/start"
    interview_data = {
        "repo_url": repo_url,
        "analysis_id": analysis_id,
        "question_ids": question_ids[:3],  # 첫 3개 질문만 사용
        "interview_type": "technical",
        "difficulty_level": "medium"
    }
    interview_headers = {
        "Content-Type": "application/json",
        "x-github-token": github_token,
        "x-google-api-key": google_api_key
    }
    
    print(f"요청 데이터: {json.dumps(interview_data, indent=2)}")
    print(f"요청 헤더: {json.dumps({k: v[:20] + '...' if k.startswith('x-') else v for k, v in interview_headers.items()}, indent=2)}")
    
    try:
        interview_response = requests.post(
            interview_url,
            json=interview_data,
            headers=interview_headers,
            timeout=60
        )
        
        print(f"\n면접 시작 응답: {interview_response.status_code}")
        print(f"응답 내용: {json.dumps(interview_response.json(), indent=2, ensure_ascii=False)}")
        
        if interview_response.status_code == 200:
            result = interview_response.json()
            if result.get("success"):
                interview_id = result["data"]["interview_id"]
                print(f"\n✅ 면접 시작 성공!")
                print(f"Interview ID: {interview_id}")
                print(f"질문 수: {result['data']['question_count']}")
                
                # 3. 답변 제출 테스트 (API 키 헤더 포함)
                print("\n3. 답변 제출 테스트 (API 키 헤더 포함)...")
                answer_url = f"{base_url}/api/v1/interview/answer"
                answer_data = {
                    "interview_id": interview_id,
                    "question_id": question_ids[0],
                    "answer": "이것은 테스트 답변입니다. API 키 헤더가 올바르게 전달되는지 확인하는 답변입니다.",
                    "time_taken": 30
                }
                answer_headers = {
                    "Content-Type": "application/json",
                    "x-github-token": github_token,
                    "x-google-api-key": google_api_key
                }
                
                answer_response = requests.post(
                    answer_url,
                    json=answer_data,
                    headers=answer_headers,
                    timeout=60
                )
                
                print(f"답변 제출 응답: {answer_response.status_code}")
                if answer_response.status_code == 200:
                    answer_result = answer_response.json()
                    print(f"답변 제출 결과: {json.dumps(answer_result, indent=2, ensure_ascii=False)}")
                    print("✅ 답변 제출 성공!")
                else:
                    print(f"❌ 답변 제출 실패: {answer_response.text}")
                
            else:
                print(f"❌ 면접 시작 실패: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ 면접 시작 HTTP 오류: {interview_response.text}")
            
    except Exception as e:
        print(f"❌ 면접 시작 요청 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_interview_start_with_headers())