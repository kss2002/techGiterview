# Python 3.11 베이스 이미지
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지를 pip로 직접 설치 (uv 대신)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    aiohttp \
    aioredis \
    asyncpg \
    psycopg2-binary \
    sqlalchemy \
    pydantic-settings \
    python-multipart \
    redis \
    langchain \
    langchain-google-genai \
    langgraph \
    langsmith \
    google-generativeai \
    chromadb \
    aiosqlite \
    chardet \
    lizard \
    networkx \
    scipy \
    tiktoken

# 소스 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONPATH="/app"

# uvicorn 설치 확인
RUN python -c "import uvicorn; print('uvicorn successfully installed')"
RUN which uvicorn

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 개발 환경 명령어 (docker-compose에서 오버라이드됨)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]