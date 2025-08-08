#!/bin/bash

# TechGiterview Development Stop Script
# 개발 환경 서비스들을 안전하게 종료하는 스크립트

set -e

echo "🛑 TechGiterview 개발 환경 종료"
echo "================================"

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 실행 중인 프로세스 확인 및 종료
echo "🔍 실행 중인 서비스 확인 중..."

# Node.js 프로세스 종료 (React 개발 서버)
if pgrep -f "react-scripts start" > /dev/null; then
    echo "⚛️  React 개발 서버 종료 중..."
    pkill -f "react-scripts start" || true
    echo "✅ React 개발 서버 종료 완료"
fi

# Python/uvicorn 프로세스 종료
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "🐍 FastAPI 서버 종료 중..."
    pkill -f "uvicorn.*main:app" || true
    echo "✅ FastAPI 서버 종료 완료"
fi

# 포트별 프로세스 강제 종료 (필요한 경우)
force_kill_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo "🔧 포트 $port ($service_name) 프로세스 강제 종료: PID $pid"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# 주요 포트 확인 및 정리
echo "🔧 포트 정리 중..."
force_kill_port 3000 "Frontend"
force_kill_port 8000 "Backend"

# Docker 서비스 종료
echo "🐳 Docker 서비스 종료 중..."
if docker-compose ps -q > /dev/null 2>&1; then
    # 실행 중인 컨테이너가 있는지 확인
    if [ "$(docker-compose ps -q | wc -l)" -gt 0 ]; then
        echo "   Docker Compose 서비스 종료 중..."
        docker-compose down
        
        # 볼륨 정리 옵션 (선택사항)
        echo ""
        read -p "🗑️  Docker 볼륨도 함께 삭제하시겠습니까? 데이터베이스 데이터가 삭제됩니다. (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "   Docker 볼륨 삭제 중..."
            docker-compose down -v
            echo "✅ Docker 볼륨 삭제 완료"
        fi
        
    else
        echo "   실행 중인 Docker 서비스가 없습니다."
    fi
else
    echo "   docker-compose.yml을 찾을 수 없습니다."
fi

# 개발 서버 관련 임시 파일 정리
echo "🧹 임시 파일 정리 중..."

# Node.js 관련 정리
if [ -d "src/frontend/.next" ]; then
    echo "   Next.js 빌드 캐시 삭제 중..."
    rm -rf src/frontend/.next
fi

# Python 관련 정리
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 로그 파일 정리 (선택사항)
if [ -d "logs" ]; then
    echo ""
    read -p "🗑️  로그 파일도 삭제하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   로그 파일 삭제 중..."
        rm -rf logs/*
        echo "✅ 로그 파일 삭제 완료"
    fi
fi

# 최종 포트 상태 확인
echo "🔍 최종 포트 상태 확인..."
for port in 3000 8000 5432 6379 8001; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  포트 $port가 여전히 사용 중입니다."
        echo "   수동으로 확인하여 종료해주세요: lsof -i :$port"
    fi
done

# Docker 이미지 정리 (선택사항)
echo ""
read -p "🗑️  사용하지 않는 Docker 이미지도 정리하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🐳 사용하지 않는 Docker 이미지 정리 중..."
    
    # dangling 이미지 삭제
    docker image prune -f
    
    # 추가 정리 옵션
    read -p "   모든 사용하지 않는 이미지를 삭제하시겠습니까? (신중하게!) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -a -f
        echo "✅ Docker 이미지 정리 완료"
    fi
fi

echo ""
echo "✅ TechGiterview 개발 환경이 성공적으로 종료되었습니다!"
echo "================================"
echo ""
echo "🔧 유용한 명령어:"
echo "   - 다시 시작: ./scripts/dev-start.sh"
echo "   - Docker 상태 확인: docker ps -a"
echo "   - 포트 사용 확인: lsof -i :8000"
echo "   - 프로세스 확인: ps aux | grep -E '(uvicorn|react-scripts)'"
echo ""
echo "💡 문제 해결:"
echo "   - 포트가 여전히 사용 중인 경우:"
echo "     sudo lsof -ti :포트번호 | xargs kill -9"
echo "   - Docker 완전 정리:"
echo "     docker system prune -a --volumes"
echo ""
echo "🎯 다음 실행 시 주의사항:"
echo "   - 환경 변수 파일(.env) 확인"
echo "   - Docker Desktop이 실행 중인지 확인"
echo "   - 필요한 의존성이 설치되어 있는지 확인"