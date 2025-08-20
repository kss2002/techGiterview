# Node.js 18 베이스 이미지 (안정적 LTS 버전)
FROM node:18-alpine

# 빌드 인수로 호스트 사용자 UID/GID 받기
ARG USER_ID=1000
ARG GROUP_ID=1000

# 시스템 의존성 설치 (Alpine 기반)
RUN apk add --no-cache curl

# 작업 디렉토리 설정
WORKDIR /app

# 사용자/그룹 생성 (기존 것이 있으면 사용)
RUN if ! getent group $GROUP_ID >/dev/null 2>&1; then \
        addgroup -g $GROUP_ID -S nodejs; \
    fi && \
    GROUP_NAME=$(getent group $GROUP_ID | cut -d: -f1) && \
    if ! getent passwd $USER_ID >/dev/null 2>&1; then \
        adduser -S nextjs -u $USER_ID -G $GROUP_NAME; \
    else \
        echo "User ID $USER_ID already exists"; \
        USER_NAME=$(getent passwd $USER_ID | cut -d: -f1); \
        echo "Using existing user: $USER_NAME"; \
    fi

# package.json 및 package-lock.json 복사 (캐시 최적화)
COPY package*.json ./

# 의존성 설치 (개발 의존성 포함)
RUN npm ci --silent && \
    npm cache clean --force

# 소스 코드 복사 및 권한 설정
COPY --chown=$USER_ID:$GROUP_ID . .

# 작업 디렉토리 권한 설정
RUN chown -R $USER_ID:$GROUP_ID /app && \
    chmod -R 775 /app

# 개발 환경에서는 root로 실행 (권한 문제 방지)
# 프로덕션에서는 보안을 위해 non-root 사용자 권장

# 포트 노출
EXPOSE 3001

# 환경 변수 설정
ENV NODE_ENV=development
ENV PORT=3001
ENV VITE_CJS_IGNORE_WARNING=true

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:3001 || exit 1

# 개발 서버 시작
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]