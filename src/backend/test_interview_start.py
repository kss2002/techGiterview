#!/usr/bin/env python3
"""
면접 시작 기능 테스트 스크립트
"""

import asyncio
import requests
import json
from datetime import datetime

async def test_interview_start():
    """면접 시작 API 테스트"""
    print("🚀 면접 시작 기능 테스트 시작\n")
    
    # 테스트용 분석 ID (로그에서 확인된 ID 사용)
    analysis_id = "92f14bd4-8ea5-4d64-9fa3-e3741ab6dd85"
    base_url = "http://127.0.0.1:8002"
    
    # 테스트용 헤더
    headers = {
        "Content-Type": "application/json",
        "x-github-token": "github_pat_11ARXVKRY...",
        "x-google-api-key": "AIzaSyAwnmVjg0fMbaTl..."
    }
    
    print(f"⚡ 테스트 설정:")
    print(f"   - 분석 ID: {analysis_id}")
    print(f"   - 백엔드 URL: {base_url}")
    print(f"   - GitHub Token: {'설정됨' if headers.get('x-github-token') else '없음'}")
    print(f"   - Google API Key: {'설정됨' if headers.get('x-google-api-key') else '없음'}")
    
    try:
        # 1. 분석 데이터 확인
        print(f"\n📋 1. 분석 데이터 확인...")
        analysis_response = requests.get(f"{base_url}/api/v1/repository/analysis/{analysis_id}")
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            print(f"   ✅ 분석 데이터 존재: {analysis_data['data']['repository_name']}")
        else:
            print(f"   ❌ 분석 데이터 없음: {analysis_response.status_code}")
            print(f"   응답: {analysis_response.text[:200]}")
            return False
        
        # 2. 질문 데이터 확인
        print(f"\n📋 2. 질문 데이터 확인...")
        questions_response = requests.get(f"{base_url}/api/v1/questions/analysis/{analysis_id}")
        
        if questions_response.status_code == 200:
            questions_data = questions_response.json()
            if questions_data['data']['questions']:
                print(f"   ✅ 질문 데이터 존재: {len(questions_data['data']['questions'])}개")
                question_ids = [q['id'] for q in questions_data['data']['questions'][:3]]  # 처음 3개만 사용
            else:
                print(f"   ❌ 질문이 없음")
                return False
        else:
            print(f"   ❌ 질문 조회 실패: {questions_response.status_code}")
            print(f"   응답: {questions_response.text[:200]}")
            return False
        
        # 3. 면접 시작 요청
        print(f"\n🚀 3. 면접 시작 요청...")
        interview_start_data = {
            "repo_url": "https://github.com/django/django",
            "analysis_id": analysis_id,
            "question_ids": question_ids,
            "interview_type": "technical",
            "difficulty_level": "medium"
        }
        
        print(f"   요청 데이터:")
        print(f"     - 질문 ID: {question_ids}")
        print(f"     - 면접 타입: {interview_start_data['interview_type']}")
        print(f"     - 난이도: {interview_start_data['difficulty_level']}")
        
        start_response = requests.post(
            f"{base_url}/api/v1/interview/start",
            headers=headers,
            json=interview_start_data
        )
        
        print(f"\n   응답 상태: {start_response.status_code}")
        print(f"   응답 내용:")
        
        if start_response.status_code == 200:
            start_result = start_response.json()
            print(json.dumps(start_result, indent=2, ensure_ascii=False))
            
            interview_id = start_result['data']['interview_id']
            print(f"\n   ✅ 면접 시작 성공!")
            print(f"   📝 면접 ID: {interview_id}")
            
            # 4. 면접 세션 조회 테스트
            print(f"\n📋 4. 면접 세션 조회 테스트...")
            session_response = requests.get(f"{base_url}/api/v1/interview/session/{interview_id}")
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                print(f"   ✅ 면접 세션 조회 성공!")
                print(f"   상태: {session_data['data']['status']}")
                print(f"   시작 시간: {session_data['data']['started_at']}")
            else:
                print(f"   ❌ 면접 세션 조회 실패: {session_response.status_code}")
                print(f"   응답: {session_response.text[:200]}")
                return False
            
            return True
            
        else:
            print(f"   ❌ 면접 시작 실패")
            print(f"   오류 내용: {start_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    success = asyncio.run(test_interview_start())
    
    print(f"\n{'='*50}")
    print(f"📋 테스트 결과")
    print(f"{'='*50}")
    
    if success:
        print(f"🎉 면접 시작 기능 테스트 성공!")
        print(f"   모든 단계가 정상적으로 완료되었습니다.")
    else:
        print(f"❌ 면접 시작 기능 테스트 실패")
        print(f"   로그를 확인하여 문제를 해결하세요.")

if __name__ == "__main__":
    main()