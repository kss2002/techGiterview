#!/usr/bin/env python3
"""
Schema Validator 테스트 스크립트

배포 전에 스키마 검증 시스템이 제대로 작동하는지 확인
"""

import sys
import os
sys.path.append('/app')  # Docker 컨테이너 내부 경로 추가

import asyncio
from app.core.schema_validator import SchemaValidator, auto_validate_schema, quick_check_critical_columns

def test_schema_validator():
    """스키마 검증기 테스트"""
    print("🔍 Schema Validator 테스트 시작...")
    
    try:
        # 1. 스키마 검증기 인스턴스 생성
        validator = SchemaValidator()
        print("✅ SchemaValidator 인스턴스 생성 성공")
        
        # 2. 중요 컬럼 빠른 확인
        print("\n📋 중요 컬럼 빠른 확인...")
        critical_missing = quick_check_critical_columns()
        print(f"누락된 중요 컬럼: {critical_missing}")
        
        # 3. 전체 스키마 검증 및 자동 수정
        print("\n🔧 전체 스키마 검증 및 자동 마이그레이션...")
        result = auto_validate_schema()
        
        print(f"\n📊 검증 결과:")
        print(f"  - 검증된 테이블: {result['validated_tables']}")
        print(f"  - 누락된 테이블: {result['missing_tables']}")
        print(f"  - 추가된 컬럼: {result['added_columns']}")
        print(f"  - 오류: {result['errors']}")
        print(f"  - 요약: {result['summary']}")
        
        # 4. 특정 테이블 정보 확인
        print("\n📋 interview_sessions 테이블 상세 정보:")
        table_info = validator.get_table_info('interview_sessions')
        if 'error' not in table_info:
            columns = [col['name'] for col in table_info['columns']]
            print(f"  컬럼 목록: {columns}")
            print(f"  컬럼 수: {table_info['column_count']}")
            
            # feedback 컬럼 확인
            has_feedback = 'feedback' in columns
            print(f"  feedback 컬럼 존재: {'✅' if has_feedback else '❌'}")
        else:
            print(f"  오류: {table_info['error']}")
        
        # 5. 최종 결과
        if result['summary']['status'] == 'success':
            print("\n🎉 스키마 검증 및 자동 마이그레이션 성공!")
            return True
        elif result['summary']['status'] == 'partial_success':
            print("\n⚠️  스키마 검증 부분 성공 (일부 문제 해결됨)")
            return True
        else:
            print("\n❌ 스키마 검증 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n🔗 데이터베이스 연결 테스트...")
    
    try:
        from app.core.database import engine, SessionLocal
        from sqlalchemy import text
        
        # 연결 테스트
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 데이터베이스 연결 성공")
            
        # 세션 테스트
        db = SessionLocal()
        try:
            # 간단한 쿼리 실행
            result = db.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✅ 세션 테스트 성공 - 테이블 수: {table_count}")
            return True
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def test_interview_session_model():
    """InterviewSession 모델 테스트"""
    print("\n🏗️  InterviewSession 모델 테스트...")
    
    try:
        from app.models.interview import InterviewSession
        from app.models.repository import RepositoryAnalysis
        from app.core.database import SessionLocal
        import uuid
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # 샘플 분석 데이터 확인 (있는 것 중에서 사용)
            analysis = db.query(RepositoryAnalysis).first()
            if not analysis:
                print("⚠️  분석 데이터가 없음 - 모델 테스트만 수행")
                analysis_id = uuid.uuid4()
            else:
                analysis_id = analysis.id
                print(f"✅ 기존 분석 데이터 사용: {analysis_id}")
            
            # 새 면접 세션 생성 (실제로 저장하지는 않음)
            test_session = InterviewSession(
                id=uuid.uuid4(),
                user_id=None,  # 게스트 사용자
                analysis_id=analysis_id,
                interview_type="technical",
                difficulty="medium",
                status="active",
                started_at=datetime.utcnow(),
                feedback={"test": "data"}  # 이 필드가 문제가 되는 부분
            )
            
            print("✅ InterviewSession 모델 인스턴스 생성 성공")
            print(f"  - ID: {test_session.id}")
            print(f"  - 분석 ID: {test_session.analysis_id}")
            print(f"  - 상태: {test_session.status}")
            print(f"  - 피드백 필드: {test_session.feedback}")
            
            # 실제 저장은 하지 않음 (테스트 목적)
            # db.add(test_session)
            # db.commit()
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Schema Validator 전체 테스트 시작\n")
    
    results = []
    
    # 1. 데이터베이스 연결 테스트
    results.append(("데이터베이스 연결", test_database_connection()))
    
    # 2. 스키마 검증기 테스트
    results.append(("스키마 검증기", test_schema_validator()))
    
    # 3. 모델 테스트
    results.append(("InterviewSession 모델", test_interview_session_model()))
    
    # 최종 결과 출력
    print("\n" + "="*50)
    print("📋 테스트 결과 요약")
    print("="*50)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n전체 결과: {success_count}/{len(results)} 성공")
    
    if success_count == len(results):
        print("🎉 모든 테스트 통과! 배포 준비 완료")
        return True
    else:
        print("⚠️  일부 테스트 실패 - 배포 전 문제 해결 필요")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)