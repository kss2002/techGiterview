"""
Question Generation API Router

질문 생성 관련 API 엔드포인트
"""

from typing import Dict, List, Any, Optional
import re
import uuid
import json
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy import text

from app.agents.question_generator import QuestionGenerator
from app.core.database import engine

router = APIRouter()

# 질문 캐시 (분석 ID별로 질문 저장)
question_cache = {}


def extract_api_keys_from_headers(
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
) -> Dict[str, str]:
    """요청 헤더에서 API 키 추출"""
    api_keys = {}
    if github_token:
        api_keys["github_token"] = github_token
    if google_api_key:
        api_keys["google_api_key"] = google_api_key
    return api_keys





class QuestionGenerationRequest(BaseModel):
    """질문 생성 요청"""
    repo_url: str
    analysis_result: Optional[Dict[str, Any]] = None
    question_type: str = "technical"
    difficulty: str = "medium"
    question_count: int = 9
    force_regenerate: bool = False  # 강제 재생성 옵션


class QuestionResponse(BaseModel):
    """질문 응답"""
    id: str
    type: str
    question: str
    difficulty: str
    context: Optional[str] = None
    time_estimate: Optional[str] = None
    code_snippet: Optional[Dict[str, Any]] = None
    expected_answer_points: Optional[List[str]] = None
    technology: Optional[str] = None
    pattern: Optional[str] = None
    # 서브 질문 관련 필드
    parent_question_id: Optional[str] = None
    sub_question_index: Optional[int] = None
    total_sub_questions: Optional[int] = None
    is_compound_question: bool = False


class QuestionCacheData(BaseModel):
    """질문 캐시 데이터 구조"""
    original_questions: List[QuestionResponse]  # AI 원본 질문
    parsed_questions: List[QuestionResponse]   # 파싱된 개별 질문
    question_groups: Dict[str, List[str]]      # 그룹별 질문 관계 (parent_id -> [sub_question_ids])
    created_at: str


def create_question_groups(questions: List[QuestionResponse]) -> Dict[str, List[str]]:
    """질문 그룹 관계 생성"""
    groups = {}
    
    for question in questions:
        if question.parent_question_id:
            parent_id = question.parent_question_id
            if parent_id not in groups:
                groups[parent_id] = []
            groups[parent_id].append(question.id)
    
    return groups


def is_header_or_title(text: str) -> bool:
    """
    텍스트가 제목이나 헤더인지 확인
    """
    text = text.strip()
    
    # 1. 마크다운 헤더 패턴 (#, ##, ###)
    if re.match(r'^#{1,6}\s+', text):
        return True
    
    # 2. numbered list로 시작하는 경우는 제목이 아님 (실제 질문일 가능성 높음)
    if re.match(r'^\d+\.\s+\*\*.*\*\*', text):
        return False
        
    # 3. 질문 키워드가 포함된 경우는 제목이 아님
    question_keywords = ['설명해주세요', '어떻게', '무엇', '왜', '방법', '차이점', '장점', '단점', 
                        '예시', '구체적으로', '비교', '선택', '고려', '적용', '사용', '?']
    if any(keyword in text for keyword in question_keywords):
        return False
    
    # 4. 제목 형태 패턴 (실제 섹션 제목들만)
    title_patterns = [
        r'^[가-힣\s]*기술\s*면접\s*질문[가-힣\s]*$',  # "기술 면접 질문"으로만 구성
        r'^[가-힣\s]*아키텍처[가-힣\s]*$',           # "아키텍처"만 포함하는 단순 제목
        r'^[가-힣\s]*관련\s*질문[가-힣\s]*$',        # "관련 질문"으로만 구성
        r'^[가-힣\s]*면접\s*문제[가-힣\s]*$',        # "면접 문제"로만 구성
    ]
    
    for pattern in title_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # 5. 질문이 아닌 짧은 문장 (물음표가 없고 너무 짧은 경우)
    if (len(text) < 15 and '?' not in text and 
        not any(keyword in text for keyword in ['설명', '어떻게', '무엇', '왜'])):
        return True
    
    # 6. 마크다운 구분자
    if text in ['---', '***', '===']:
        return True
    
    return False


def is_valid_question(text: str) -> bool:
    """
    텍스트가 유효한 질문인지 확인
    """
    text = text.strip()
    
    # 1. 최소 길이 확인
    if len(text) < 10:
        return False
    
    # 2. 질문 키워드 확인
    question_indicators = [
        '?', '어떻게', '무엇', '왜', '설명', '차이점', '장점', '단점', 
        '방법', '전략', '구현', '사용', '적용', '고려', '처리', '해결'
    ]
    
    has_question_indicator = any(indicator in text for indicator in question_indicators)
    
    # 3. 제목/헤더가 아닌지 확인
    is_not_header = not is_header_or_title(text)
    
    return has_question_indicator and is_not_header


def parse_compound_question(question: QuestionResponse) -> List[QuestionResponse]:
    """
    마크다운 내용을 정리하여 질문으로 변환
    
    Args:
        question: 원본 질문 객체
        
    Returns:
        List[QuestionResponse]: 정리된 질문 리스트
    """
    question_text = question.question
    
    # 1. 마크다운 제목과 불필요한 내용 제거
    question_text = re.sub(r'^#{1,6}\s+.*$', '', question_text, flags=re.MULTILINE)  # 마크다운 제목 제거
    question_text = re.sub(r'^---+\s*$', '', question_text, flags=re.MULTILINE)     # 구분자 제거
    question_text = re.sub(r'\n\s*\n', '\n\n', question_text)                      # 여러 줄바꿈 정리
    
    # 2. 줄 단위로 분리하여 처리
    lines = question_text.split('\n')
    processed_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # 마크다운 제목 스킵
        if re.match(r'^#{1,6}\s+', line_stripped):
            continue
            
        # numbered list 항목의 번호 제거 및 정리
        clean_line = line_stripped
        
        # 다양한 numbered list 패턴 처리
        patterns_to_remove = [
            r'^\d+\.\s+',      # "1. "
            r'^\d+\)\s+',      # "1) "
            r'^\s*\d+\.\s+',  # "  1. "
        ]
        
        for pattern in patterns_to_remove:
            if re.match(pattern, clean_line):
                clean_line = re.sub(pattern, '', clean_line).strip()
                break
        
        # 빈 줄이 아닌 경우만 추가
        if clean_line:
            processed_lines.append(clean_line)
    
    # 3. 처리된 내용을 하나의 질문으로 결합
    cleaned_question = ' '.join(processed_lines).strip()
    
    # 4. 정리된 질문이 유효한지 확인
    if (len(cleaned_question) > 20 and 
        any(keyword in cleaned_question for keyword in ['설명해주세요', '어떻게', '무엇', '왜', '방법', '차이점', '?', '예시', '구체적'])):
        
        # 정리된 질문으로 업데이트
        question.question = cleaned_question
        return [question]
    
    # 5. 유효하지 않은 경우 원본 그대로 반환
    return [question]


def parse_questions_list(questions: List[QuestionResponse]) -> List[QuestionResponse]:
    """
    질문 리스트를 처리하여 compound question들을 분리
    
    Args:
        questions: 원본 질문 리스트
        
    Returns:
        List[QuestionResponse]: 파싱된 질문 리스트
    """
    parsed_questions = []
    
    for question in questions:
        # 각 질문을 파싱하여 결과 추가
        parsed_list = parse_compound_question(question)
        parsed_questions.extend(parsed_list)
    
    return parsed_questions


class QuestionGenerationResult(BaseModel):
    """질문 생성 결과"""
    success: bool
    questions: List[QuestionResponse]
    analysis_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=QuestionGenerationResult)
async def generate_questions(
    request: QuestionGenerationRequest,
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
):
    """GitHub 저장소 분석 결과를 바탕으로 기술면접 질문 생성"""
    
    try:
        # 분석 결과에서 analysis_id 추출
        analysis_id = None
        if request.analysis_result and "analysis_id" in request.analysis_result:
            analysis_id = request.analysis_result["analysis_id"]

        # 🔧 핵심 수정: 중복 요청 방지를 위한 Redis 락 사용
        if analysis_id and not request.force_regenerate:
            from app.core.database import get_redis
            import asyncio
            
            lock_key = f"question_generation_lock:{analysis_id}"
            lock_timeout = 300  # 5분 (질문 생성이 오래 걸릴 수 있음)
            
            try:
                redis = await get_redis()
                
                # 🔥 Redis 락 획득 시도 (이미 생성 중인 요청이 있으면 대기 또는 거부)
                lock_acquired = await redis.set(lock_key, "generating", ex=lock_timeout, nx=True)
                
                if not lock_acquired:
                    # 락을 획득하지 못한 경우: 다른 요청이 이미 진행 중
                    print(f"[LOCK_BLOCKED] 질문 생성이 이미 진행 중: analysis_id={analysis_id}")
                    
                    # 잠시 대기 후 캐시에서 결과 확인
                    for attempt in range(10):  # 최대 10회 시도 (약 50초)
                        await asyncio.sleep(5)
                        
                        # 정규화된 캐시 키로 확인
                        normalized_cache_key = analysis_id.replace('-', '')
                        if normalized_cache_key in question_cache:
                            cache_data = question_cache[normalized_cache_key]
                            print(f"[LOCK_WAIT_SUCCESS] 대기 중 질문 생성 완료됨: {len(cache_data.parsed_questions)}개 질문")
                            return QuestionGenerationResult(
                                success=True,
                                questions=cache_data.parsed_questions,
                                analysis_id=analysis_id
                            )
                        
                        # 하이픈 포함 키로도 확인
                        if analysis_id in question_cache:
                            cache_data = question_cache[analysis_id]
                            print(f"[LOCK_WAIT_SUCCESS] 대기 중 질문 생성 완료됨 (하이픈 키): {len(cache_data.parsed_questions)}개 질문")
                            return QuestionGenerationResult(
                                success=True,
                                questions=cache_data.parsed_questions,
                                analysis_id=analysis_id
                            )
                    
                    # 대기 시간이 초과된 경우
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "GENERATION_IN_PROGRESS",
                            "message": "질문 생성이 이미 진행 중입니다. 잠시 후 다시 시도해주세요.",
                            "analysis_id": analysis_id,
                            "suggestion": "질문 목록 조회를 통해 생성 완료 여부를 확인해주세요."
                        }
                    )
                
                # 락 획득 성공 - 질문 생성 진행
                print(f"[LOCK_ACQUIRED] 질문 생성 락 획득 성공: analysis_id={analysis_id}")
                
            except Exception as e:
                print(f"[LOCK_ERROR] Redis 락 처리 중 오류: {str(e)}")
                # Redis 연결 실패 시에도 질문 생성은 계속 진행
        
        # 이미 생성된 질문이 있는지 확인 (강제 재생성이 아닌 경우)
        if analysis_id and not request.force_regenerate:
            # 정규화된 키로 먼저 확인
            normalized_cache_key = analysis_id.replace('-', '')
            if normalized_cache_key in question_cache:
                cache_data = question_cache[normalized_cache_key]
                print(f"[CACHE_HIT] 기존 질문 반환 (정규화 키): {len(cache_data.parsed_questions)}개")
                return QuestionGenerationResult(
                    success=True,
                    questions=cache_data.parsed_questions,
                    analysis_id=analysis_id
                )
            
            # 하이픈 포함 키로도 확인
            if analysis_id in question_cache:
                cache_data = question_cache[analysis_id]
                print(f"[CACHE_HIT] 기존 질문 반환 (하이픈 키): {len(cache_data.parsed_questions)}개")
                return QuestionGenerationResult(
                    success=True,
                    questions=cache_data.parsed_questions,
                    analysis_id=analysis_id
                )
        
        # 헤더에서 API 키 추출
        api_keys = extract_api_keys_from_headers(github_token, google_api_key)
        
        # 질문 생성기 초기화
        generator = QuestionGenerator()
        
        # 질문 생성 실행 - QuestionGenerator 내부 기본값 사용 (3가지 타입 균등 분배)
        result = await generator.generate_questions(
            repo_url=request.repo_url,
            difficulty_level=request.difficulty,
            question_count=request.question_count,
            question_types=None,  # 기본값 ["tech_stack", "architecture", "code_analysis"] 사용
            analysis_data=request.analysis_result,
            api_keys=api_keys  # API 키 전달
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "질문 생성 실패"))
        
        # 응답 형식에 맞게 변환
        questions = []
        for q in result["questions"]:
            questions.append(QuestionResponse(
                id=q.get("id", ""),
                type=q.get("type", "technical"),
                question=q.get("question", ""),
                difficulty=q.get("difficulty", request.difficulty),
                context=q.get("context"),
                time_estimate=q.get("time_estimate", "5분"),
                code_snippet=q.get("code_snippet"),
                expected_answer_points=q.get("expected_answer_points"),
                technology=q.get("technology"),
                pattern=q.get("pattern")
            ))
        
        # 질문 파싱 처리 (compound question 분리)
        parsed_questions = parse_questions_list(questions)
        
        # 질문 그룹 관계 생성
        question_groups = create_question_groups(parsed_questions)
        
        # 캐시에 저장 (구조화된 데이터) - UUID 정규화하여 저장
        if analysis_id:
            from datetime import datetime
            # UUID 정규화: 하이픈 제거하여 일관성 있게 저장
            normalized_cache_key = analysis_id.replace('-', '')
            cache_data = QuestionCacheData(
                original_questions=questions,
                parsed_questions=parsed_questions,
                question_groups=question_groups,
                created_at=datetime.now().isoformat()
            )
            question_cache[normalized_cache_key] = cache_data
            print(f"[CACHE] 질문을 캐시에 저장: 원본키={analysis_id}, 정규화키={normalized_cache_key}, 질문수={len(parsed_questions)}")
            
            # 하이픈 있는 키로도 저장 (호환성 보장)
            question_cache[analysis_id] = cache_data
            
            # DB에도 저장하여 영구 보존
            await _save_questions_to_db(analysis_id, parsed_questions)
        
        # 🔧 Redis 락 해제 (질문 생성 완료)
        if analysis_id:
            try:
                from app.core.database import get_redis
                redis = await get_redis()
                lock_key = f"question_generation_lock:{analysis_id}"
                await redis.delete(lock_key)
                print(f"[LOCK_RELEASED] 질문 생성 락 해제 완료: analysis_id={analysis_id}")
            except Exception as lock_error:
                print(f"[LOCK_ERROR] Redis 락 해제 실패 (질문 생성은 성공): {str(lock_error)}")
        
        return QuestionGenerationResult(
            success=True,
            questions=parsed_questions,
            analysis_id=analysis_id
        )
        
    except Exception as e:
        # 🔧 예외 발생 시에도 Redis 락 해제
        if analysis_id:
            try:
                from app.core.database import get_redis
                redis = await get_redis()
                lock_key = f"question_generation_lock:{analysis_id}"
                await redis.delete(lock_key)
                print(f"[LOCK_RELEASED] 예외 발생으로 인한 락 해제: analysis_id={analysis_id}")
            except Exception as lock_error:
                print(f"[LOCK_ERROR] 예외 상황에서 락 해제 실패: {str(lock_error)}")
                
        return QuestionGenerationResult(
            success=False,
            questions=[],
            error=str(e)
        )


@router.get("/{analysis_id}")
async def get_questions(analysis_id: str):
    """분석 ID로 질문 조회"""
    try:
        # UUID 정규화: 하이픈 제거하여 캐시 키와 매칭
        normalized_analysis_id = analysis_id.replace('-', '')
        
        if normalized_analysis_id not in question_cache:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        cache_data = question_cache[normalized_analysis_id]
        return {
            "success": True,
            "questions": cache_data.parsed_questions,
            "question_groups": cache_data.question_groups,
            "created_at": cache_data.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}/groups")
async def get_question_groups(analysis_id: str):
    """질문 그룹 정보 조회"""
    try:
        # UUID 정규화: 하이픈 제거하여 캐시 키와 매칭
        normalized_analysis_id = analysis_id.replace('-', '')
        
        if normalized_analysis_id not in question_cache:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        cache_data = question_cache[normalized_analysis_id]
        return {
            "success": True,
            "question_groups": cache_data.question_groups,
            "total_questions": len(cache_data.parsed_questions),
            "total_groups": len(cache_data.question_groups)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_question_cache():
    """질문 캐시 초기화"""
    try:
        global question_cache
        cache_count = len(question_cache)
        question_cache.clear()
        
        return {
            "success": True,
            "message": f"질문 캐시가 초기화되었습니다. ({cache_count}개 항목 제거)",
            "cleared_count": cache_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/status")
async def get_cache_status():
    """질문 캐시 상태 조회"""
    try:
        cache_info = {}
        for analysis_id, cache_data in question_cache.items():
            cache_info[analysis_id] = {
                "original_questions_count": len(cache_data.original_questions),
                "parsed_questions_count": len(cache_data.parsed_questions),
                "groups_count": len(cache_data.question_groups),
                "created_at": cache_data.created_at
            }
        
        return {
            "success": True,
            "total_cached_analyses": len(question_cache),
            "cache_details": cache_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}")
async def get_questions_by_analysis(analysis_id: str):
    """분석 ID로 생성된 질문 조회 - 메모리 캐시 우선, 없으면 DB 조회"""
    try:
        # 1. 먼저 메모리 캐시에서 조회 (UUID 정규화)
        normalized_analysis_id = analysis_id.replace('-', '')
        if normalized_analysis_id in question_cache:
            print(f"[QUESTIONS] Found questions in memory cache for {analysis_id} (normalized: {normalized_analysis_id})")
            cache_data = question_cache[normalized_analysis_id]
            
            # 캐시 데이터 구조 확인
            questions = []
            if hasattr(cache_data, 'parsed_questions'):
                questions = cache_data.parsed_questions
            elif hasattr(cache_data, 'questions'):
                questions = cache_data.questions
            elif isinstance(cache_data, list):
                questions = cache_data
            
            return QuestionGenerationResult(
                success=True,
                questions=questions,
                analysis_id=analysis_id
            )
        
        # 2. 메모리 캐시에 없으면 DB에서 조회
        print(f"[QUESTIONS] Memory cache miss, checking database for {analysis_id}")
        db_questions = await _load_questions_from_db(analysis_id)
        
        if db_questions:
            print(f"[QUESTIONS] Found {len(db_questions)} questions in database, restoring to cache")
            
            # DB에서 가져온 질문들을 메모리 캐시에 복원
            await _restore_questions_to_cache(analysis_id, db_questions)
            
            return QuestionGenerationResult(
                success=True,
                questions=db_questions,
                analysis_id=analysis_id
            )
        
        # 3. 메모리 캐시와 DB 모두에 없음
        print(f"[QUESTIONS] No questions found for {analysis_id} in cache or database")
        return QuestionGenerationResult(
            success=False,
            questions=[],
            analysis_id=analysis_id,
            error="해당 분석 ID에 대한 질문이 없습니다."
        )
        
    except Exception as e:
        print(f"Error in get_questions_by_analysis: {e}")
        return QuestionGenerationResult(
            success=False,
            questions=[],
            analysis_id=analysis_id,
            error=f"질문 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/types")
async def get_question_types():
    """사용 가능한 질문 타입 목록 조회"""
    return {
        "question_types": [
            "code_analysis",
            "tech_stack", 
            "architecture",
            "design_patterns",
            "problem_solving",
            "best_practices"
        ],
        "difficulties": ["easy", "medium", "hard"]
    }


@router.get("/debug/cache")
async def debug_question_cache():
    """질문 캐시 상태 확인 (디버깅용)"""
    return {
        "cache_size": len(question_cache),
        "cached_analysis_ids": list(question_cache.keys()),
        "cache_details": [
            {
                "analysis_id": analysis_id,
                "original_question_count": len(cache_data.original_questions) if hasattr(cache_data, 'original_questions') else 0,
                "parsed_question_count": len(cache_data.parsed_questions) if hasattr(cache_data, 'parsed_questions') else 0,
                "question_types": list(set(q.type for q in cache_data.parsed_questions)) if hasattr(cache_data, 'parsed_questions') else []
            }
            for analysis_id, cache_data in question_cache.items()
        ]
    }


@router.get("/debug/original/{analysis_id}")
async def debug_original_questions(analysis_id: str):
    """원본 질문 확인 (디버깅용)"""
    try:
        # UUID 정규화: 하이픈 제거하여 캐시 키와 매칭
        normalized_analysis_id = analysis_id.replace('-', '')
        
        if normalized_analysis_id not in question_cache:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        cache_data = question_cache[normalized_analysis_id]
        return {
            "success": True,
            "original_questions": [
                {
                    "id": q.id,
                    "type": q.type, 
                    "question": q.question,
                    "is_compound": q.is_compound_question,
                    "total_sub_questions": q.total_sub_questions
                }
                for q in cache_data.original_questions
            ],
            "parsed_questions_count": len(cache_data.parsed_questions),
            "groups_count": len(cache_data.question_groups)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/add-test-questions/{analysis_id}")
async def add_test_questions(analysis_id: str):
    """테스트용 질문 추가 (디버깅용)"""
    try:
        from datetime import datetime
        
        # 테스트용 질문 생성
        test_questions = [
            QuestionResponse(
                id=str(uuid.uuid4()),
                type="technical",
                question="Linux 커널의 주요 서브시스템에 대해 설명해주세요.",
                difficulty="medium",
                context="Linux 커널 아키텍처",
                time_estimate="5분",
                technology="C"
            ),
            QuestionResponse(
                id=str(uuid.uuid4()),
                type="architecture",
                question="1. 메모리 관리 서브시스템의 역할은?\n2. 프로세스 스케줄러의 동작 원리는?\n3. 파일 시스템의 VFS 레이어 목적은?",
                difficulty="medium",
                context="Linux 커널 아키텍처",
                time_estimate="10분",
                technology="C"
            ),
            QuestionResponse(
                id=str(uuid.uuid4()),
                type="code_analysis",
                question="디바이스 드라이버를 작성할 때 고려해야 할 주요 요소들은 무엇인가요?",
                difficulty="medium",
                context="Linux 커널 개발",
                time_estimate="7분",
                technology="C"
            )
        ]
        
        # 질문 파싱 처리
        parsed_questions = parse_questions_list(test_questions)
        
        # 질문 그룹 관계 생성
        question_groups = create_question_groups(parsed_questions)
        
        # 캐시에 저장 (UUID 정규화)
        normalized_cache_key = analysis_id.replace('-', '')
        cache_data = QuestionCacheData(
            original_questions=test_questions,
            parsed_questions=parsed_questions,
            question_groups=question_groups,
            created_at=datetime.now().isoformat()
        )
        question_cache[normalized_cache_key] = cache_data
        # 호환성을 위해 원본 키로도 저장
        question_cache[analysis_id] = cache_data
        
        return {
            "success": True,
            "message": f"테스트 질문이 추가되었습니다. (원본: {len(test_questions)}, 파싱: {len(parsed_questions)})",
            "analysis_id": analysis_id,
            "questions": parsed_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/cache")
async def debug_question_cache():
    """질문 캐시 상태 확인 (디버깅용)"""
    return {
        "cache_size": len(question_cache),
        "cached_analysis_ids": list(question_cache.keys()),
        "cache_details": [
            {
                "analysis_id": analysis_id,
                "question_count": len(cache_data.parsed_questions),
                "created_at": cache_data.created_at
            }
            for analysis_id, cache_data in question_cache.items()
        ]
    }


@router.delete("/debug/cache")
async def clear_question_cache():
    """질문 캐시 초기화 (디버깅용)"""
    cache_size_before = len(question_cache)
    question_cache.clear()
    
    return {
        "message": "질문 캐시가 성공적으로 초기화되었습니다",
        "cleared_items": cache_size_before,
        "current_cache_size": len(question_cache)
    }


async def _load_questions_from_db(analysis_id: str) -> List[QuestionResponse]:
    """데이터베이스에서 질문 조회"""
    try:
        with engine.connect() as conn:
            # InterviewQuestion 테이블에서 질문 조회
            result = conn.execute(text(
                """
                SELECT id, category, difficulty, question_text, expected_points, 
                       related_files, context, created_at
                FROM interview_questions 
                WHERE analysis_id = :analysis_id
                ORDER BY created_at ASC
                """
            ), {"analysis_id": analysis_id})
            
            questions = []
            for row in result:
                # expected_points JSON 파싱
                expected_points = None
                if row[4]:  # expected_points 필드
                    try:
                        expected_points = json.loads(row[4]) if isinstance(row[4], str) else row[4]
                    except json.JSONDecodeError:
                        expected_points = None
                
                # 데이터베이스 row를 QuestionResponse 객체로 변환
                question = QuestionResponse(
                    id=str(row[0]),
                    type=row[1],  # category -> type
                    question=row[3],  # question_text -> question
                    difficulty=row[2],
                    context=None,  # context는 JSON이므로 간단히 None으로 처리
                    time_estimate="5분",  # 기본값
                    code_snippet=None,
                    expected_answer_points=expected_points,
                    technology=None,
                    pattern=None
                )
                questions.append(question)
            
            print(f"[DB] Loaded {len(questions)} questions from database for analysis {analysis_id}")
            return questions
            
    except Exception as e:
        print(f"[DB] Error loading questions from database: {e}")
        return []


async def _restore_questions_to_cache(analysis_id: str, questions: List[QuestionResponse]):
    """DB에서 가져온 질문들을 메모리 캐시에 복원"""
    try:
        from datetime import datetime
        
        # 질문 그룹 관계 생성
        question_groups = create_question_groups(questions)
        
        # 캐시에 저장할 데이터 구조 생성
        cache_data = QuestionCacheData(
            original_questions=questions,  # DB에서 가져온 질문들을 원본으로 처리
            parsed_questions=questions,    # 이미 파싱된 상태로 간주
            question_groups=question_groups,
            created_at=datetime.now().isoformat()
        )
        
        # 메모리 캐시에 저장 (UUID 정규화하여 일관성 유지)
        normalized_cache_key = analysis_id.replace('-', '')
        question_cache[normalized_cache_key] = cache_data
        # 호환성을 위해 원본 키로도 저장
        question_cache[analysis_id] = cache_data
        
        print(f"[CACHE] Restored {len(questions)} questions to memory cache for analysis {analysis_id} (normalized: {normalized_cache_key})")
        
    except Exception as e:
        print(f"[CACHE] Error restoring questions to cache: {e}")


async def _save_questions_to_db(analysis_id: str, questions: List[QuestionResponse]):
    """생성된 질문들을 데이터베이스에 저장 - UPSERT 방식으로 개선"""
    try:
        from app.core.database import database_url
        from datetime import datetime
        current_time = datetime.now()
        
        with engine.connect() as conn:
            # 🔧 핵심 개선: DELETE-INSERT 대신 UPSERT 사용
            # 데이터베이스 종류에 따라 다른 UPSERT 구문 사용
            is_sqlite = "sqlite" in database_url.lower()
            
            print(f"[DB_UPSERT] UPSERT 방식으로 질문 저장 시작: {len(questions)}개 질문, DB타입={'SQLite' if is_sqlite else 'PostgreSQL'}")
            
            # 🔥 단계별 UPSERT: 기존 질문 ID 조회 후 새 질문 처리
            for question in questions:
                if is_sqlite:
                    # SQLite: INSERT OR REPLACE 사용 (updated_at 컬럼 없음)
                    conn.execute(text(
                        """
                        INSERT OR REPLACE INTO interview_questions 
                        (id, analysis_id, category, difficulty, question_text, expected_points, created_at)
                        VALUES (:id, :analysis_id, :category, :difficulty, :question_text, :expected_points, 
                                COALESCE((SELECT created_at FROM interview_questions WHERE id = :id), :created_at))
                        """
                    ), {
                        "id": question.id,
                        "analysis_id": analysis_id,
                        "category": question.type,
                        "difficulty": question.difficulty,
                        "question_text": question.question,
                        "expected_points": json.dumps(question.expected_answer_points) if question.expected_answer_points else None,
                        "created_at": current_time
                    })
                else:
                    # PostgreSQL: INSERT ... ON CONFLICT DO UPDATE 사용 (updated_at 컬럼 없음)
                    conn.execute(text(
                        """
                        INSERT INTO interview_questions 
                        (id, analysis_id, category, difficulty, question_text, expected_points, created_at)
                        VALUES (:id, :analysis_id, :category, :difficulty, :question_text, :expected_points, :created_at)
                        ON CONFLICT (id) DO UPDATE SET
                            category = EXCLUDED.category,
                            difficulty = EXCLUDED.difficulty,
                            question_text = EXCLUDED.question_text,
                            expected_points = EXCLUDED.expected_points
                        """
                    ), {
                        "id": question.id,
                        "analysis_id": analysis_id,
                        "category": question.type,
                        "difficulty": question.difficulty,
                        "question_text": question.question,
                        "expected_points": json.dumps(question.expected_answer_points) if question.expected_answer_points else None,
                        "created_at": current_time
                    })
            
            # 🔧 추가 개선: 현재 질문 세트에 없는 기존 질문들은 비활성화 (삭제하지 않음)
            current_question_ids = [q.id for q in questions]
            if current_question_ids:
                question_ids_placeholder = ','.join([f"'{qid}'" for qid in current_question_ids])
                
                # 현재 질문 세트에 없는 기존 질문들 비활성화
                result = conn.execute(text(
                    f"""
                    UPDATE interview_questions 
                    SET is_active = FALSE, updated_at = :updated_at
                    WHERE analysis_id = :analysis_id 
                    AND id NOT IN ({question_ids_placeholder})
                    AND is_active = TRUE
                    """
                ), {
                    "analysis_id": analysis_id,
                    "updated_at": current_time
                })
                
                deactivated_count = result.rowcount if hasattr(result, 'rowcount') else 0
                if deactivated_count > 0:
                    print(f"[DB_UPSERT] 기존 질문 {deactivated_count}개 비활성화 (삭제하지 않음)")
            
            # 변경사항 커밋
            conn.commit()
            
            print(f"[DB_UPSERT] UPSERT 완료: {len(questions)}개 질문 저장/업데이트, analysis_id={analysis_id}")
            print(f"[DB_UPSERT] ✅ 장점: 질문 삭제 없이 원자적 업데이트로 캐시-DB 일관성 보장")
            
    except Exception as e:
        print(f"[DB_UPSERT_ERROR] UPSERT 저장 실패: {str(e)}")
        print(f"[DB_UPSERT_ERROR] 폴백: 기존 DELETE-INSERT 방식으로 재시도...")
        
        # 🔧 폴백: UPSERT 실패 시 기존 방식으로 재시도
        try:
            with engine.connect() as conn:
                # 기존 질문 삭제
                conn.execute(text(
                    "DELETE FROM interview_questions WHERE analysis_id = :analysis_id"
                ), {"analysis_id": analysis_id})
                
                # 새로운 질문들 저장
                from datetime import datetime
                current_time = datetime.now()
                
                for question in questions:
                    conn.execute(text(
                        """
                        INSERT INTO interview_questions 
                        (id, analysis_id, category, difficulty, question_text, expected_points, created_at)
                        VALUES (:id, :analysis_id, :category, :difficulty, :question_text, :expected_points, :created_at)
                        """
                    ), {
                        "id": question.id,
                        "analysis_id": analysis_id,
                        "category": question.type,
                        "difficulty": question.difficulty,
                        "question_text": question.question,
                        "expected_points": json.dumps(question.expected_answer_points) if question.expected_answer_points else None,
                        "created_at": current_time
                    })
                
                conn.commit()
                print(f"[DB_FALLBACK] 폴백 저장 성공: {len(questions)}개 질문")
                
        except Exception as fallback_error:
            print(f"[DB_FALLBACK_ERROR] 폴백도 실패: {str(fallback_error)}")
            # DB 저장 실패는 질문 생성 자체를 실패시키지 않음