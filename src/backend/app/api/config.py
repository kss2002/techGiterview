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
    """API 키 설정"""
    try:
        update_api_keys(request.github_token, request.google_api_key)
        return {"message": "API 키가 성공적으로 설정되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 키 설정 실패: {str(e)}")


@router.get("/keys-required")
async def check_keys_required():
    """API 키 입력이 필요한지 확인"""
    env_exists = check_env_file_exists()
    has_keys = bool(settings.github_token and settings.google_api_key)
    
    return {
        "keys_required": not (env_exists or has_keys),
        "missing_keys": {
            "github_token": not bool(settings.github_token),
            "google_api_key": not bool(settings.google_api_key)
        }
    }