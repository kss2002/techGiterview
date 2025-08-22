#!/usr/bin/env python3
"""
특정 대시보드 페이지 동작 테스트
/dashboard/fe1908db-6fb5-4a65-a511-eb115997dec5 경로 테스트
"""

import asyncio
import json
import requests
from typing import Dict, Any

async def test_specific_dashboard():
    """특정 분석 ID로 대시보드 기능 테스트"""
    
    base_url = "http://127.0.0.1:8004"
    analysis_id = "fe1908db-6fb5-4a65-a511-eb115997dec5"  # 사용자 제공 분석 ID
    
    print("========== 대시보드 특정 분석 ID 테스트 ==========")
    print(f"Backend URL: {base_url}")
    print(f"Analysis ID: {analysis_id}")
    print("API 키 우선순위: .env.dev > localStorage 헤더 > 없음")
    
    # 1. 분석 데이터 존재 확인
    print("\n1. 분석 데이터 존재 확인...")
    try:
        analysis_url = f"{base_url}/api/v1/repository/analysis/{analysis_id}"
        analysis_response = requests.get(analysis_url, timeout=30)
        
        print(f"분석 데이터 조회 응답: {analysis_response.status_code}")
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            print(f"분석 데이터 존재 확인됨")
            if 'data' in analysis_data:
                repo_info = analysis_data['data']
                print(f"  - Repository: {repo_info.get('repository_name', 'Unknown')}")
                print(f"  - Language: {repo_info.get('primary_language', 'Unknown')}")
                print(f"  - Status: {repo_info.get('status', 'Unknown')}")
            else:
                repo_info = analysis_data  # 데이터가 바로 분석 정보인 경우
                print(f"  - Repository: {repo_info.get('repository_name', 'Unknown')}")
                print(f"  - Language: {repo_info.get('primary_language', 'Unknown')}")
                print(f"  - Status: {repo_info.get('status', 'Unknown')}")
        else:
            print(f"❌ 분석 데이터 조회 실패: {analysis_response.text}")
            return
            
    except Exception as e:
        print(f"❌ 분석 데이터 조회 오류: {e}")
        return
    
    # 2. 질문 생성 또는 캐시 확인
    print("\n2. 질문 데이터 확인...")
    try:
        questions_url = f"{base_url}/api/v1/questions/cache/{analysis_id}"
        questions_response = requests.get(questions_url, timeout=30)
        
        print(f"질문 캐시 조회 응답: {questions_response.status_code}")
        if questions_response.status_code == 200:
            questions_data = questions_response.json()
            print("✅ 질문 캐시 존재")
            questions = questions_data.get('data', {}).get('questions', [])
            print(f"  - 질문 수: {len(questions)}")
            if questions:
                for i, q in enumerate(questions[:3]):
                    print(f"  - 질문 {i+1}: {q.get('id', 'No ID')} ({q.get('type', 'Unknown type')})")
            question_ids = [q['id'] for q in questions[:5]]  # 최대 5개 질문
        else:
            print("질문 캐시 없음, 새로 생성 시도...")
            # 질문 생성 시도
            repo_url = repo_info.get('repository_url', 'https://github.com/example/repo')
            generate_url = f"{base_url}/api/v1/questions/generate"
            generate_data = {
                "repo_url": repo_url,
                "analysis_id": analysis_id,
                "question_count": 5,
                "difficulty_level": "medium"
            }
            
            generate_response = requests.post(generate_url, json=generate_data, timeout=60)
            print(f"질문 생성 응답: {generate_response.status_code}")
            
            if generate_response.status_code == 200:
                generate_result = generate_response.json()
                questions = generate_result.get('data', {}).get('questions', [])
                question_ids = [q['id'] for q in questions]
                print(f"✅ 질문 생성 성공: {len(questions)}개")
            else:
                print(f"❌ 질문 생성 실패: {generate_response.text}")
                return
                
    except Exception as e:
        print(f"❌ 질문 데이터 확인 오류: {e}")
        return
    
    # 3. 면접 시작 테스트 (환경변수 우선)
    print("\n3. 면접 시작 테스트 (.env.dev 우선)...")
    try:
        interview_url = f"{base_url}/api/v1/interview/start"
        interview_data = {
            "repo_url": repo_url,
            "analysis_id": analysis_id,
            "question_ids": question_ids[:3] if question_ids else [],
            "interview_type": "technical",
            "difficulty_level": "medium"
        }
        
        # 헤더는 localStorage 시뮬레이션용 (환경변수가 우선)
        interview_headers = {
            "Content-Type": "application/json",
            "x-github-token": "localStorage_token_should_be_ignored",
            "x-google-api-key": "localStorage_key_should_be_ignored"
        }
        
        print("요청 데이터:")
        print(f"  - Analysis ID: {analysis_id}")
        print(f"  - Question IDs: {question_ids[:3] if question_ids else 'None'}")
        print("  - API 키 우선순위: .env.dev 값 사용 예상")
        
        interview_response = requests.post(
            interview_url,
            json=interview_data, 
            headers=interview_headers,
            timeout=60
        )
        
        print(f"\n면접 시작 응답: {interview_response.status_code}")
        
        if interview_response.status_code == 200:
            result = interview_response.json()
            print("✅ 면접 시작 성공!")
            print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            interview_id = result['data']['interview_id']
            
            # 4. 답변 제출 테스트
            print(f"\n4. 답변 제출 테스트...")
            answer_url = f"{base_url}/api/v1/interview/answer"
            answer_data = {
                "interview_id": interview_id,
                "question_id": question_ids[0] if question_ids else "test-q1",
                "answer": "이 프로젝트는 TypeScript를 주로 사용하며, React와 Node.js 기반의 웹 애플리케이션입니다. 모듈화된 구조로 되어 있어 확장성이 좋고, 테스트 코드도 잘 작성되어 있습니다.",
                "time_taken": 45
            }
            
            answer_response = requests.post(answer_url, json=answer_data, headers=interview_headers, timeout=60)
            print(f"답변 제출 응답: {answer_response.status_code}")
            
            if answer_response.status_code == 200:
                answer_result = answer_response.json()
                print("✅ 답변 제출 성공!")
                feedback = answer_result.get('data', {}).get('feedback')
                if feedback:
                    print(f"피드백: {feedback.get('feedback', 'No feedback')}")
                    print(f"점수: {feedback.get('overall_score', 'No score')}")
            else:
                print(f"❌ 답변 제출 실패: {answer_response.text}")
                
        else:
            print(f"❌ 면접 시작 실패: {interview_response.text}")
            
    except Exception as e:
        print(f"❌ 면접 시작 테스트 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_dashboard())