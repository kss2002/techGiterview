# Python 3.11 베이스 이미지
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (최신 Python 패키지 매니저)
RUN pip install uv

# 작업 디렉토리 설정
WORKDIR /app

# uv 프로젝트 파일들 복사
COPY pyproject.toml uv.lock ./

# 가상환경 생성 및 의존성 설치
RUN uv sync --frozen

# 소스 코드 복사
COPY . .

# uv 가상환경 활성화 및 PATH 설정
ENV UV_VENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# uv 설치 확인
RUN ls -la /app/.venv/bin/

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 개발 환경 명령어 (docker-compose에서 오버라이드됨)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]