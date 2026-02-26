"""
공통 API 유틸리티 함수들

API 키 추출, 헤더 처리 등의 공통 기능
"""

from typing import Dict, Optional
from fastapi import Header

from .config import settings


def extract_api_keys_from_headers(
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key"),
    upstage_api_key: Optional[str] = Header(None, alias="x-upstage-api-key"),
) -> Dict[str, str]:
    """
    요청 헤더에서 API 키 추출 및 환경변수와 우선순위 적용
    
    우선순위:
    1. 요청 헤더의 API 키
    2. 환경변수의 API 키 (유효한 값인 경우)
    3. None (API 키 없음)
    """
    api_keys = {}
    
    # GitHub Token 우선순위 적용
    if github_token:
        api_keys["github_token"] = github_token
    elif settings.github_token and settings.github_token != "your_github_token_here":
        api_keys["github_token"] = settings.github_token
    
    # Google API Key 우선순위 적용  
    if google_api_key:
        api_keys["google_api_key"] = google_api_key
    elif settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
        api_keys["google_api_key"] = settings.google_api_key

    # Upstage API Key 우선순위 적용
    if upstage_api_key:
        api_keys["upstage_api_key"] = upstage_api_key
    elif getattr(settings, "upstage_api_key", None) and settings.upstage_api_key != "your_upstage_api_key_here":
        api_keys["upstage_api_key"] = settings.upstage_api_key
    
    return api_keys


def get_effective_api_keys(
    github_token: Optional[str] = None,
    google_api_key: Optional[str] = None,
    upstage_api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    개별 API 키 파라미터에서 우선순위 적용하여 유효한 키만 추출
    
    Args:
        github_token: GitHub 토큰
        google_api_key: Google API 키
    
    Returns:
        유효한 API 키들의 딕셔너리
    """
    api_keys = {}
    
    # GitHub Token 우선순위: 파라미터 > 환경변수
    if github_token and github_token != "your_github_token_here":
        api_keys["github_token"] = github_token
    elif settings.github_token and settings.github_token != "your_github_token_here":
        api_keys["github_token"] = settings.github_token
    
    # Google API Key 우선순위: 파라미터 > 환경변수
    if google_api_key and google_api_key != "your_google_api_key_here":
        api_keys["google_api_key"] = google_api_key
    elif settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
        api_keys["google_api_key"] = settings.google_api_key

    # Upstage API Key 우선순위: 파라미터 > 환경변수
    if upstage_api_key and upstage_api_key != "your_upstage_api_key_here":
        api_keys["upstage_api_key"] = upstage_api_key
    elif getattr(settings, "upstage_api_key", None) and settings.upstage_api_key != "your_upstage_api_key_here":
        api_keys["upstage_api_key"] = settings.upstage_api_key
    
    return api_keys


def create_safe_error_response(
    success: bool = False,
    error_code: str = "UNKNOWN_ERROR",
    message: str = "알 수 없는 오류가 발생했습니다.",
    data: Optional[Dict] = None
) -> Dict:
    """
    안전한 에러 응답 구조 생성
    
    Args:
        success: 성공 여부
        error_code: 에러 코드
        message: 사용자 친화적 메시지
        data: 추가 데이터 (선택사항)
    
    Returns:
        표준화된 에러 응답
    """
    response = {
        "success": success,
        "error": error_code,
        "message": message
    }
    
    if data:
        response["data"] = data
    
    return response
