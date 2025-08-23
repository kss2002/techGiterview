#!/usr/bin/env python3
"""
즉시 실행 가능한 스키마 수정 스크립트

배포 환경에서 바로 실행하여 누락된 컬럼을 추가하는 스크립트
"""

import sys
import os

# Docker 컨테이너 내부에서 실행할 때 경로 추가
sys.path.append('/app')

def fix_interview_sessions_table():
    """interview_sessions 테이블에 누락된 컬럼 즉시 추가"""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        print("🔧 interview_sessions 테이블 스키마 수정 시작...")
        
        with engine.connect() as conn:
            # 1. 현재 테이블 구조 확인
            print("📋 현재 테이블 구조 확인...")
            try:
                result = conn.execute(text("PRAGMA table_info(interview_sessions)"))
                columns = [row[1] for row in result]  # 컬럼명만 추출
                print(f"기존 컬럼: {columns}")
                
                # feedback 컬럼 확인
                has_feedback = 'feedback' in columns
                print(f"feedback 컬럼 존재: {'✅' if has_feedback else '❌'}")
                
                if has_feedback:
                    print("✅ feedback 컬럼이 이미 존재합니다. 수정 불필요.")
                    return True
                    
            except Exception as e:
                print(f"⚠️  테이블 구조 확인 실패: {e}")
                return False
            
            # 2. feedback 컬럼 추가
            print("🔧 feedback 컬럼 추가 중...")
            try:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN feedback JSON NULL"))
                conn.commit()
                print("✅ feedback 컬럼 추가 완료")
                
                # 3. 추가 확인
                result = conn.execute(text("PRAGMA table_info(interview_sessions)"))
                updated_columns = [row[1] for row in result]
                print(f"업데이트된 컬럼: {updated_columns}")
                
                if 'feedback' in updated_columns:
                    print("🎉 스키마 수정 성공!")
                    return True
                else:
                    print("❌ 컬럼이 추가되지 않았습니다.")
                    return False
                    
            except Exception as e:
                print(f"❌ 컬럼 추가 실패: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 스키마 수정 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fixed_schema():
    """수정된 스키마로 면접 세션 생성 테스트"""
    try:
        print("\n🧪 수정된 스키마 테스트...")
        
        from app.models.interview import InterviewSession
        from app.core.database import SessionLocal
        import uuid
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # 테스트 세션 생성 (저장하지는 않음)
            test_session = InterviewSession(
                id=uuid.uuid4(),
                user_id=None,
                analysis_id=uuid.uuid4(),
                interview_type="technical", 
                difficulty="medium",
                status="active",
                started_at=datetime.utcnow(),
                feedback={"test": "schema_fixed"}
            )
            
            print("✅ InterviewSession 모델 인스턴스 생성 성공")
            print(f"  - feedback 필드 값: {test_session.feedback}")
            
            # SELECT 쿼리 테스트
            print("📋 SELECT 쿼리 테스트...")
            result = db.execute(text("SELECT COUNT(*) FROM interview_sessions"))
            count = result.scalar()
            print(f"✅ SELECT 쿼리 성공 - 기존 세션 수: {count}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 스키마 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    print("🚀 즉시 스키마 수정 시작\n")
    
    # 1. 스키마 수정
    if not fix_interview_sessions_table():
        print("❌ 스키마 수정 실패")
        return False
    
    # 2. 수정된 스키마 테스트
    if not test_fixed_schema():
        print("❌ 스키마 테스트 실패")
        return False
    
    print("\n🎉 스키마 수정 및 테스트 완료!")
    print("📝 다음 단계:")
    print("   1. 백엔드 컨테이너 재시작: docker-compose restart backend")
    print("   2. 면접 시작 API 테스트")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 스키마 수정 성공 - 배포 환경 복구 완료")
        sys.exit(0)
    else:
        print("\n❌ 스키마 수정 실패 - 수동 확인 필요")
        sys.exit(1)