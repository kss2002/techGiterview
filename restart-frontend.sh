#!/bin/bash

# TechGiterview Frontend Docker 재시작 스크립트 (자동화 강화)
echo "🚀 Frontend Docker 컨테이너 재빌드 및 시작..."

# 환경 감지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 현재 사용자 UID/GID 감지
USER_ID=$(id -u)
GROUP_ID=$(id -g)

echo "📋 환경 정보:"
echo "   사용자 ID: $USER_ID"
echo "   그룹 ID: $GROUP_ID"
echo "   프로젝트 루트: $PROJECT_ROOT"

# Docker 권한 확인
echo "📋 Docker 권한 확인 중..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 접근 권한이 없습니다."
    echo "💡 해결 방법:"
    echo "   1. sudo usermod -aG docker $USER"
    echo "   2. 터미널 재시작 또는 로그아웃/로그인"
    echo "   3. 또는 sudo를 사용: sudo ./restart-frontend.sh"
    
    # sudo로 재시도 제안
    read -p "sudo로 재시도하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 sudo로 재시도 중..."
        sudo USER_ID=$USER_ID GROUP_ID=$GROUP_ID bash "$0" "$@"
        exit $?
    else
        exit 1
    fi
fi

# 프로젝트 루트로 이동
cd "$PROJECT_ROOT"

# 기존 컨테이너 정리
echo "🧹 기존 frontend 컨테이너 정리..."
docker-compose stop frontend 2>/dev/null || true
docker-compose rm -f frontend 2>/dev/null || true

# 호스트 파일 권한 자동 설정 (권한 문제 예방)
echo "🔧 파일 권한 자동 설정 중..."
if [ -w ./src/frontend ]; then
    # 현재 사용자가 쓰기 권한이 있는 경우에만 실행
    chown -R $USER_ID:$GROUP_ID ./src/frontend 2>/dev/null || {
        echo "⚠️  파일 권한 설정을 건너뜁니다 (권한 부족)"
    }
else
    echo "⚠️  src/frontend 디렉토리에 쓰기 권한이 없습니다"
fi

# 이미지 재빌드 (사용자 ID/GID와 함께)
echo "🔨 Frontend 이미지 재빌드 (USER_ID=$USER_ID, GROUP_ID=$GROUP_ID)..."
USER_ID=$USER_ID GROUP_ID=$GROUP_ID docker-compose build --no-cache frontend

# 컨테이너 시작
echo "▶️  Frontend 컨테이너 시작..."
USER_ID=$USER_ID GROUP_ID=$GROUP_ID docker-compose up -d frontend

# 컨테이너 상태 확인 및 로그 출력
echo "📊 컨테이너 상태 확인..."
sleep 5

# 상태 확인
CONTAINER_STATUS=$(docker-compose ps -q frontend | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not found")
echo "   컨테이너 상태: $CONTAINER_STATUS"

# 로그 확인 (최근 20줄)
echo "📋 컨테이너 로그 (최근 20줄):"
echo "----------------------------------------"
docker-compose logs --tail=20 frontend
echo "----------------------------------------"

# 결과 출력
if [ "$CONTAINER_STATUS" = "running" ]; then
    echo "✅ Frontend 재시작 완료!"
    echo "🌐 브라우저에서 http://localhost:9105 로 접속해보세요."
    echo "🔗 API 프록시: Vite가 백엔드(http://backend:8000)로 자동 프록시됩니다."
elif [ "$CONTAINER_STATUS" = "exited" ]; then
    echo "❌ Frontend 컨테이너가 종료되었습니다."
    echo "💡 위의 로그를 확인하여 문제를 해결해주세요."
    exit 1
else
    echo "⚠️  Frontend 컨테이너 상태를 확인할 수 없습니다."
    echo "🔍 수동 확인: docker-compose ps frontend"
    exit 1
fi