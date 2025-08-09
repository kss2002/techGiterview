"""
Configuration API Endpoints

환경 설정 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings, check_env_file_exists, update_api_keys

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class ConfigStatusResponse(BaseModel):
    """설정 상태 응답 모델"""
    env_file_exists: bool
    has_github_token: bool
    has_google_api_key: bool


class KeysRequiredResponse(BaseModel):
    """API 키 요구사항 응답 모델"""
    keys_required: bool
    use_local_storage: bool
    missing_keys: dict
    

class ApiKeysRequest(BaseModel):
    """API 키 설정 요청 모델"""
    github_token: str
    google_api_key: str


@router.get("/status", response_model=ConfigStatusResponse)
async def get_config_status():
    """환경 설정 상태 확인"""
    return ConfigStatusResponse(
        env_file_exists=check_env_file_exists(),
        has_github_token=bool(settings.github_token),
        has_google_api_key=bool(settings.google_api_key)
    )


@router.post("/api-keys")
async def set_api_keys(request: ApiKeysRequest):
    """API 키 설정 및 AI 서비스 재초기화"""
    try:
        # .env.dev 파일이 있는 경우에만 서버에 키 저장
        env_exists = check_env_file_exists()
        
        if env_exists:
            # 서버 모드: 기존 방식대로 전역 설정에 저장
            update_api_keys(request.github_token, request.google_api_key)
            return {
                "message": "API 키가 성공적으로 설정되었습니다.",
                "ai_service_reinitialized": True,
                "mode": "server"
            }
        else:
            # 로컬스토리지 모드: 서버에 키 저장하지 않음
            return {
                "message": "로컬스토리지 모드에서는 키가 클라이언트에서만 사용됩니다.",
                "ai_service_reinitialized": False,
                "mode": "local_storage"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 키 설정 실패: {str(e)}")


@router.get("/keys-required", response_model=KeysRequiredResponse)
async def check_keys_required():
    """API 키 입력이 필요한지 확인"""
    env_exists = check_env_file_exists()
    has_keys = bool(settings.github_token and settings.google_api_key)
    
    # .env.dev 파일이 없으면 로컬스토리지 모드 사용
    use_local_storage = not env_exists
    
    # 로컬스토리지 모드에서는 항상 키 입력 필요 (클라이언트에서 처리)
    keys_required = use_local_storage or not has_keys
    
    return KeysRequiredResponse(
        keys_required=keys_required,
        use_local_storage=use_local_storage,
        missing_keys={
            "github_token": not bool(settings.github_token),
            "google_api_key": not bool(settings.google_api_key)
        }
    )