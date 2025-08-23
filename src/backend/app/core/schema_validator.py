"""
Schema Validator and Auto-Migration System

데이터베이스 스키마 검증 및 자동 마이그레이션 시스템
누락된 컬럼을 자동으로 감지하고 추가하는 기능 제공
"""

import logging
from typing import Dict, List, Set, Optional, Any
from sqlalchemy import text, inspect, MetaData, Table, Column
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine, Base
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer, InterviewConversation, InterviewReport
from app.models.repository import RepositoryAnalysis, AnalyzedFile
from app.models.user import User

logger = logging.getLogger(__name__)


class SchemaValidator:
    """데이터베이스 스키마 검증 및 자동 마이그레이션"""
    
    def __init__(self, db_engine: Engine = None):
        self.engine = db_engine or engine
        self.inspector = inspect(self.engine)
        
        # 모델별 예상 컬럼 정의
        self.expected_columns = {
            'interview_sessions': {
                'id': {'type': 'UUID', 'nullable': False},
                'user_id': {'type': 'UUID', 'nullable': True}, 
                'analysis_id': {'type': 'UUID', 'nullable': False},
                'interview_type': {'type': 'VARCHAR', 'nullable': False},
                'difficulty': {'type': 'VARCHAR', 'nullable': False},
                'status': {'type': 'VARCHAR', 'nullable': False},
                'overall_score': {'type': 'NUMERIC', 'nullable': True},
                'feedback': {'type': 'JSON', 'nullable': True},  # 누락되기 쉬운 컬럼
                'started_at': {'type': 'DATETIME', 'nullable': True},
                'ended_at': {'type': 'DATETIME', 'nullable': True},
                'duration_minutes': {'type': 'INTEGER', 'nullable': True}
            },
            'interview_questions': {
                'id': {'type': 'UUID', 'nullable': False},
                'analysis_id': {'type': 'UUID', 'nullable': False},
                'category': {'type': 'VARCHAR', 'nullable': False},
                'difficulty': {'type': 'VARCHAR', 'nullable': False},
                'question_text': {'type': 'TEXT', 'nullable': False},
                'expected_points': {'type': 'JSON', 'nullable': True},
                'related_files': {'type': 'JSON', 'nullable': True},
                'context': {'type': 'JSON', 'nullable': True},
                'is_active': {'type': 'BOOLEAN', 'nullable': False, 'default': True},  # 질문 활성화 상태
                'created_at': {'type': 'DATETIME', 'nullable': True},
                'updated_at': {'type': 'DATETIME', 'nullable': True}  # 업데이트 시간
            },
            'interview_answers': {
                'id': {'type': 'UUID', 'nullable': False},
                'session_id': {'type': 'UUID', 'nullable': False},
                'question_id': {'type': 'UUID', 'nullable': False},
                'user_answer': {'type': 'TEXT', 'nullable': False},
                'feedback_score': {'type': 'NUMERIC', 'nullable': True},
                'feedback_message': {'type': 'TEXT', 'nullable': True},
                'feedback_details': {'type': 'JSON', 'nullable': True},
                'time_taken_seconds': {'type': 'INTEGER', 'nullable': True},
                'submitted_at': {'type': 'DATETIME', 'nullable': True},
                'updated_at': {'type': 'DATETIME', 'nullable': True}
            },
            'interview_conversations': {
                'id': {'type': 'UUID', 'nullable': False},
                'session_id': {'type': 'UUID', 'nullable': False},
                'question_id': {'type': 'UUID', 'nullable': True},
                'conversation_order': {'type': 'INTEGER', 'nullable': False},
                'speaker': {'type': 'VARCHAR', 'nullable': False},
                'message_type': {'type': 'VARCHAR', 'nullable': False},
                'message_content': {'type': 'TEXT', 'nullable': False},
                'answer_score': {'type': 'NUMERIC', 'nullable': True},
                'ai_feedback': {'type': 'TEXT', 'nullable': True},
                'extra_metadata': {'type': 'JSON', 'nullable': True},
                'created_at': {'type': 'DATETIME', 'nullable': True}
            },
            'interview_reports': {
                'id': {'type': 'UUID', 'nullable': False},
                'session_id': {'type': 'UUID', 'nullable': False},
                'overall_score': {'type': 'NUMERIC', 'nullable': False},
                'category_scores': {'type': 'JSON', 'nullable': False},
                'strengths': {'type': 'JSON', 'nullable': True},
                'improvements': {'type': 'JSON', 'nullable': True},
                'recommendations': {'type': 'JSON', 'nullable': True},
                'detailed_feedback': {'type': 'TEXT', 'nullable': True},
                'created_at': {'type': 'DATETIME', 'nullable': True}
            }
        }
    
    def validate_and_fix_schema(self) -> Dict[str, Any]:
        """스키마 검증 및 누락된 컬럼 자동 추가"""
        logger.info("[SCHEMA_VALIDATOR] 데이터베이스 스키마 검증 시작...")
        
        results = {
            'validated_tables': [],
            'missing_tables': [],
            'added_columns': [],
            'errors': [],
            'summary': {}
        }
        
        try:
            # 1. 기존 테이블 목록 조회
            existing_tables = set(self.inspector.get_table_names())
            logger.info(f"[SCHEMA_VALIDATOR] 기존 테이블: {sorted(existing_tables)}")
            
            # 2. 각 테이블별 스키마 검증 및 수정
            for table_name, expected_cols in self.expected_columns.items():
                if table_name not in existing_tables:
                    results['missing_tables'].append(table_name)
                    logger.warning(f"[SCHEMA_VALIDATOR] 테이블 누락: {table_name}")
                    continue
                
                # 기존 컬럼 정보 조회
                existing_columns = {}
                try:
                    columns_info = self.inspector.get_columns(table_name)
                    for col_info in columns_info:
                        existing_columns[col_info['name']] = col_info
                    
                    logger.info(f"[SCHEMA_VALIDATOR] {table_name} 기존 컬럼: {list(existing_columns.keys())}")
                except Exception as e:
                    logger.error(f"[SCHEMA_VALIDATOR] {table_name} 컬럼 정보 조회 실패: {e}")
                    results['errors'].append(f"{table_name}: 컬럼 정보 조회 실패 - {e}")
                    continue
                
                # 누락된 컬럼 확인 및 추가
                missing_columns = []
                for col_name, col_spec in expected_cols.items():
                    if col_name not in existing_columns:
                        missing_columns.append((col_name, col_spec))
                
                if missing_columns:
                    logger.warning(f"[SCHEMA_VALIDATOR] {table_name}에서 누락된 컬럼: {[c[0] for c in missing_columns]}")
                    
                    # 누락된 컬럼 추가 시도
                    for col_name, col_spec in missing_columns:
                        success = self._add_missing_column(table_name, col_name, col_spec)
                        if success:
                            results['added_columns'].append(f"{table_name}.{col_name}")
                            logger.info(f"[SCHEMA_VALIDATOR] ✅ 컬럼 추가 성공: {table_name}.{col_name}")
                        else:
                            results['errors'].append(f"{table_name}.{col_name}: 컬럼 추가 실패")
                            logger.error(f"[SCHEMA_VALIDATOR] ❌ 컬럼 추가 실패: {table_name}.{col_name}")
                else:
                    logger.info(f"[SCHEMA_VALIDATOR] ✅ {table_name} 스키마 정상")
                
                results['validated_tables'].append(table_name)
            
            # 3. 누락된 테이블이 있으면 전체 테이블 재생성 시도
            if results['missing_tables']:
                logger.warning(f"[SCHEMA_VALIDATOR] 누락된 테이블 발견: {results['missing_tables']}")
                self._create_missing_tables(results['missing_tables'])
            
            # 4. 결과 요약
            results['summary'] = {
                'total_tables_checked': len(self.expected_columns),
                'validated_tables': len(results['validated_tables']),
                'missing_tables': len(results['missing_tables']),
                'added_columns': len(results['added_columns']),
                'errors': len(results['errors']),
                'status': 'success' if len(results['errors']) == 0 else 'partial_success'
            }
            
            logger.info(f"[SCHEMA_VALIDATOR] 스키마 검증 완료: {results['summary']}")
            return results
            
        except Exception as e:
            logger.error(f"[SCHEMA_VALIDATOR] 스키마 검증 중 치명적 오류: {e}")
            results['errors'].append(f"치명적 오류: {e}")
            results['summary']['status'] = 'failed'
            return results
    
    def _add_missing_column(self, table_name: str, column_name: str, column_spec: Dict[str, Any]) -> bool:
        """누락된 컬럼을 테이블에 추가"""
        try:
            # SQLite와 PostgreSQL에 맞는 컬럼 타입 매핑
            type_mapping = {
                'UUID': 'TEXT',  # SQLite에서는 TEXT로 처리
                'VARCHAR': 'VARCHAR(255)',
                'TEXT': 'TEXT',
                'INTEGER': 'INTEGER',
                'NUMERIC': 'NUMERIC(3,2)',
                'DATETIME': 'DATETIME',
                'JSON': 'JSON',
                'BOOLEAN': 'BOOLEAN'  # Boolean 타입 추가
            }
            
            column_type = type_mapping.get(column_spec['type'], 'TEXT')
            nullable = 'NULL' if column_spec.get('nullable', True) else 'NOT NULL'
            
            # 기본값 설정 (타입별)
            default_value = ''
            if column_spec['type'] == 'JSON' and column_spec.get('nullable', True):
                default_value = 'DEFAULT NULL'
            elif column_spec['type'] == 'BOOLEAN' and column_spec.get('default') is not None:
                # Boolean 타입의 기본값 처리
                default_bool = column_spec['default']
                default_value = f'DEFAULT {str(default_bool).upper()}'
            elif not column_spec.get('nullable', True):
                if column_spec['type'] in ['VARCHAR', 'TEXT']:
                    default_value = "DEFAULT ''"
                elif column_spec['type'] in ['INTEGER', 'NUMERIC']:
                    default_value = 'DEFAULT 0'
                elif column_spec['type'] == 'BOOLEAN':
                    default_value = 'DEFAULT FALSE'
            
            # ALTER TABLE 문 생성 및 실행
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable} {default_value}".strip()
            
            logger.info(f"[SCHEMA_VALIDATOR] 컬럼 추가 SQL: {alter_sql}")
            
            with self.engine.connect() as conn:
                conn.execute(text(alter_sql))
                conn.commit()
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"[SCHEMA_VALIDATOR] 컬럼 추가 실패 {table_name}.{column_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"[SCHEMA_VALIDATOR] 컬럼 추가 중 예상치 못한 오류 {table_name}.{column_name}: {e}")
            return False
    
    def _create_missing_tables(self, missing_tables: List[str]):
        """누락된 테이블들을 생성"""
        try:
            logger.info(f"[SCHEMA_VALIDATOR] 누락된 테이블 생성 시도: {missing_tables}")
            
            # 모든 테이블을 한 번에 생성 (의존관계 고려)
            Base.metadata.create_all(self.engine, checkfirst=True)
            
            logger.info(f"[SCHEMA_VALIDATOR] ✅ 누락된 테이블 생성 완료: {missing_tables}")
            
        except Exception as e:
            logger.error(f"[SCHEMA_VALIDATOR] ❌ 테이블 생성 실패: {e}")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블의 상세 정보 조회"""
        try:
            if table_name not in self.inspector.get_table_names():
                return {"error": f"테이블 '{table_name}'이 존재하지 않습니다."}
            
            columns_info = self.inspector.get_columns(table_name)
            indexes_info = self.inspector.get_indexes(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            return {
                "table_name": table_name,
                "columns": columns_info,
                "indexes": indexes_info, 
                "foreign_keys": foreign_keys,
                "column_count": len(columns_info)
            }
            
        except Exception as e:
            return {"error": f"테이블 정보 조회 실패: {e}"}
    
    def check_critical_columns(self) -> Dict[str, List[str]]:
        """중요한 컬럼들이 누락되었는지 빠른 확인"""
        critical_checks = {
            'interview_sessions': ['feedback'],  # 가장 문제가 되는 컬럼
            'interview_questions': ['context', 'expected_points', 'is_active', 'updated_at'],  # 누락된 중요 컬럼 추가
            'interview_answers': ['feedback_details'],
            'interview_conversations': ['extra_metadata']
        }
        
        results = {}
        
        for table_name, critical_cols in critical_checks.items():
            missing = []
            try:
                if table_name in self.inspector.get_table_names():
                    existing_columns = {col['name'] for col in self.inspector.get_columns(table_name)}
                    missing = [col for col in critical_cols if col not in existing_columns]
                else:
                    missing = critical_cols  # 테이블 자체가 없으면 모든 컬럼이 누락
                    
                results[table_name] = missing
                
            except Exception as e:
                logger.error(f"[SCHEMA_VALIDATOR] {table_name} 중요 컬럼 체크 실패: {e}")
                results[table_name] = critical_cols  # 오류 시 모든 컬럼을 누락으로 간주
        
        return results


def auto_validate_schema() -> Dict[str, Any]:
    """스키마 자동 검증 및 수정 (외부 호출용)"""
    validator = SchemaValidator()
    return validator.validate_and_fix_schema()


def quick_check_critical_columns() -> Dict[str, List[str]]:
    """중요 컬럼 빠른 확인 (외부 호출용)"""
    validator = SchemaValidator()
    return validator.check_critical_columns()


if __name__ == "__main__":
    # 직접 실행 시 스키마 검증 수행
    logging.basicConfig(level=logging.INFO)
    result = auto_validate_schema()
    print("\n=== 스키마 검증 결과 ===")
    for key, value in result.items():
        print(f"{key}: {value}")