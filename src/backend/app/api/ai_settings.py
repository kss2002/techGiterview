"""
AI 설정 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.ai_service import ai_service, AIProvider

router = APIRouter(prefix="/api/v1/ai", tags=["ai-settings"])


class AIProviderInfo(BaseModel):
    id: str
    name: str
    model: str
    status: str
    recommended: bool


class AIProviderSelectionRequest(BaseModel):
    provider_id: str


@router.get("/providers", response_model=List[AIProviderInfo])
async def get_available_providers():
    """사용 가능한 AI 제공업체 목록 조회"""
    try:
        providers = ai_service.get_available_providers()
        return [AIProviderInfo(**provider) for provider in providers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 제공업체 목록 조회 실패: {str(e)}")


@router.get("/providers/preferred")
async def get_preferred_provider():
    """현재 우선 순위에 따른 추천 AI 제공업체 조회"""
    try:
        preferred = ai_service.get_preferred_provider()
        if preferred is None:
            raise HTTPException(status_code=404, detail="사용 가능한 AI 제공업체가 없습니다")
        
        provider_info = ai_service.available_providers[preferred]
        return {
            "id": preferred.value,
            "name": ai_service._get_provider_display_name(preferred),
            "model": provider_info["model"],
            "status": provider_info["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 AI 제공업체 조회 실패: {str(e)}")


@router.post("/test")
async def test_ai_provider(request: AIProviderSelectionRequest):
    """선택된 AI 제공업체 테스트"""
    try:
        # AIProvider enum으로 변환
        provider = None
        for p in AIProvider:
            if p.value == request.provider_id:
                provider = p
                break
        
        if provider is None:
            raise HTTPException(status_code=400, detail="잘못된 AI 제공업체 ID입니다")
        
        if provider not in ai_service.available_providers:
            raise HTTPException(status_code=400, detail="요청된 AI 제공업체를 사용할 수 없습니다")
        
        # 간단한 테스트 프롬프트로 AI 응답 테스트
        test_prompt = "Hello, please respond with a simple greeting in Korean."
        result = await ai_service.generate_analysis(test_prompt, provider)
        
        return {
            "status": "success",
            "provider": request.provider_id,
            "test_response": result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"],
            "model": result["model"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "provider": request.provider_id,
            "error": str(e)
        }


@router.post("/providers/select")
async def select_ai_provider(request: AIProviderSelectionRequest):
    """AI 제공업체 선택"""
    try:
        # AIProvider enum으로 변환
        provider = None
        for p in AIProvider:
            if p.value == request.provider_id:
                provider = p
                break
        
        if provider is None:
            raise HTTPException(status_code=400, detail="잘못된 AI 제공업체 ID입니다")
        
        # 프로바이더 설정
        success = ai_service.set_selected_provider(provider)
        
        if not success:
            raise HTTPException(status_code=400, detail="요청된 AI 제공업체를 사용할 수 없습니다")
        
        # 현재 선택된 프로바이더 정보 반환
        selected = ai_service.get_selected_provider()
        provider_info = ai_service.available_providers[selected]
        
        return {
            "status": "success",
            "message": f"{ai_service._get_provider_display_name(selected)} AI가 선택되었습니다",
            "selected_provider": {
                "id": selected.value,
                "name": ai_service._get_provider_display_name(selected),
                "model": provider_info["model"],
                "status": provider_info["status"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 제공업체 선택 실패: {str(e)}")


@router.get("/providers/current")
async def get_current_provider():
    """현재 선택된 AI 제공업체 조회"""
    try:
        current = ai_service.get_preferred_provider()
        if current is None:
            raise HTTPException(status_code=404, detail="사용 가능한 AI 제공업체가 없습니다")
        
        provider_info = ai_service.available_providers[current]
        is_user_selected = current == ai_service.get_selected_provider()
        
        return {
            "id": current.value,
            "name": ai_service._get_provider_display_name(current),
            "model": provider_info["model"],
            "status": provider_info["status"],
            "is_user_selected": is_user_selected,
            "selection_type": "user_selected" if is_user_selected else "auto_priority"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"현재 AI 제공업체 조회 실패: {str(e)}")