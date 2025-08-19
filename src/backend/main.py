"""
TechGiterview FastAPI Application

GitHub 기반 기술면접 준비 AI 에이전트 메인 애플리케이션
"""

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
# from app.core.database import close_db_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    print("[START] TechGiterview 서버 시작")
    yield
    # 종료 시 정리
    # await close_db_connections()
    print("[STOP] TechGiterview 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="TechGiterview API",
    description="GitHub 기반 기술면접 준비 AI 에이전트",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "TechGiterview API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "environment": settings.env
    }


# 실제 GitHub API 라우터 추가
from app.api.github import router as github_router
from app.api.analysis import router as analysis_router
from app.api.questions import router as questions_router
from app.api.ai_settings import router as ai_settings_router
from app.api.interview import router as interview_router
from app.api.websocket import router as websocket_router
from app.api.config import router as config_router
from app.api.homepage import router as homepage_router

# GitHub API 라우터 추가
app.include_router(github_router, prefix="/api/v1/repository", tags=["repository"])

# 고급 분석 API 라우터 추가 (SmartFileImportanceAnalyzer 포함)
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])

# 질문 생성 API 라우터 추가
app.include_router(questions_router, prefix="/api/v1/questions", tags=["questions"])

# AI 설정 API 라우터 추가
app.include_router(ai_settings_router, tags=["ai-settings"])

# 면접 API 라우터 추가
app.include_router(interview_router, prefix="/api/v1/interview", tags=["interview"])

# WebSocket 라우터 추가
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# Config 라우터 추가
app.include_router(config_router, tags=["config"])

# Homepage 라우터 추가
app.include_router(homepage_router, tags=["homepage"])

# Reports 라우터 추가
from app.api.reports import router as reports_router
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )