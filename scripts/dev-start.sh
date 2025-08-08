#!/bin/bash

# TechGiterview Development Startup Script
# 개발 환경에서 전체 애플리케이션을 실행하는 스크립트
#
# 사용법:
#   ./start.sh                           # 기본 실행 (자동 포트 정리 활성화)
#   AUTO_KILL_PORTS=false ./start.sh     # 안전 모드 (기존 프로세스 유지)
#   AUTO_KILL_DOCKER_PORTS=true ./start.sh  # Docker 포트도 자동 정리
#
# 환경변수:
#   AUTO_KILL_PORTS: 애플리케이션 포트 자동 정리 (기본값: true)
#   AUTO_KILL_DOCKER_PORTS: Docker 서비스 포트 자동 정리 (기본값: false)

set -e

# wait_timeout 함수 (프로세스가 끝날 때까지 지정된 시간 대기)
wait_timeout() {
    local timeout=$1
    local pid=$2
    local count=0
    
    while [ $count -lt $timeout ]; do
        if ! kill -0 $pid 2>/dev/null; then
            return 0  # 프로세스가 종료됨
        fi
        sleep 1
        count=$((count + 1))
    done
    return 1  # 타임아웃
}

echo "🚀 TechGiterview 개발 환경 시작"
echo "=================================="

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 환경 변수 확인
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ 환경 변수 $1이 설정되지 않았습니다."
        echo "   .env 파일을 확인하거나 환경 변수를 설정해주세요."
        exit 1
    fi
}

# 필수 환경 변수 로드
if [ -f "src/backend/.env.dev" ]; then
    echo "📁 개발 환경 변수 로딩 중..."
    set -a  # automatically export all variables
    source src/backend/.env.dev
    set +a  # disable automatic export
else
    echo "⚠️  .env.dev 파일을 찾을 수 없습니다."
fi

# Docker 및 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "   https://docs.docker.com/get-docker/ 에서 Docker를 설치해주세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "   https://docs.docker.com/compose/install/ 에서 Docker Compose를 설치해주세요."
    exit 1
fi

# Node.js 및 npm 확인 (로컬 개발용)
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js가 설치되지 않았습니다. Docker만 사용하여 실행합니다."
    FRONTEND_MODE="docker"
else
    FRONTEND_MODE="local"
fi

# Python 및 uv 확인 (로컬 개발용)
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python3가 설치되지 않았습니다. Docker만 사용하여 실행합니다."
    BACKEND_MODE="docker"
else
    if command -v uv &> /dev/null; then
        BACKEND_MODE="uv"
    else
        BACKEND_MODE="python"
    fi
fi

echo "🔧 개발 모드: Frontend=$FRONTEND_MODE, Backend=$BACKEND_MODE"

# 포트 충돌 확인 및 정리
check_port() {
    local port=$1
    local service=$2
    local auto_kill=${3:-true}  # 기본값: 자동 종료 활성화
    
    if timeout 3 lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "ℹ️  포트 $port가 이미 사용 중입니다 ($service)."
        
        if [ "$auto_kill" = "true" ]; then
            echo "🔄 기존 프로세스를 종료하고 새로 시작합니다..."
            
            # 포트를 사용하는 프로세스 찾기 (타임아웃 적용)
            local pids=$(timeout 5 lsof -ti :$port 2>/dev/null || echo "")
            
            if [ ! -z "$pids" ]; then
                echo "   종료할 프로세스: $pids"
                
                # TERM 시그널로 graceful shutdown 시도
                echo $pids | xargs kill -TERM 2>/dev/null || true
                sleep 2
                
                # 아직 실행 중이면 KILL 시그널로 강제 종료
                if timeout 3 lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                    echo "   강제 종료 중..."
                    echo $pids | xargs kill -9 2>/dev/null || true
                    sleep 1
                fi
                
                # 최종 확인 (타임아웃 적용)
                if timeout 3 lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                    echo "❌ 포트 $port 정리 실패 - 수동으로 확인이 필요합니다."
                    return 1
                else
                    echo "✅ 포트 $port 정리 완료"
                fi
            else
                echo "   프로세스 정보 조회 실패 - 건너뜀"
            fi
        else
            echo "   기존 서비스가 실행 중이므로 해당 서비스는 건너뜁니다."
            return 1
        fi
    fi
    return 0
}

# 자동 정리 설정 (환경변수로 제어 가능)
AUTO_KILL_PORTS=${AUTO_KILL_PORTS:-true}
AUTO_KILL_DOCKER_PORTS=${AUTO_KILL_DOCKER_PORTS:-false}

echo "🔍 포트 충돌 확인 및 정리 중..."
if [ "$AUTO_KILL_PORTS" = "true" ]; then
    echo "   애플리케이션 포트 자동 정리: 활성화"
else
    echo "   애플리케이션 포트 자동 정리: 비활성화"
fi

if [ "$AUTO_KILL_DOCKER_PORTS" = "true" ]; then
    echo "   Docker 서비스 포트 자동 정리: 활성화"
else
    echo "   Docker 서비스 포트 자동 정리: 비활성화"
fi

# 주요 애플리케이션 포트 정리 (완전 초기화)
check_port 3000 "Frontend" "true"
check_port 8001 "Backend" "true"

# Docker 서비스 포트 정리 (완전 초기화)
check_port 5432 "PostgreSQL" "true"
check_port 6379 "Redis" "true" 
check_port 8000 "ChromaDB" "true"

# Docker 서비스 시작 (선택적) - 빠른 처리
echo "🐳 Docker 서비스 확인 중..."

# 환경변수로 Docker 스킵 가능
SKIP_DOCKER=${SKIP_DOCKER:-false}

if [ "$SKIP_DOCKER" = "true" ]; then
    echo "   Docker 단계 건너뜀 (SKIP_DOCKER=true)"
else
    if command -v docker &> /dev/null && timeout 2 docker info >/dev/null 2>&1; then
        echo "   Docker 사용 가능 - 기존 서비스 확인 중..."
        
        # 이미 실행 중인 서비스가 있는지 빠르게 확인
        if docker-compose ps --services --filter status=running 2>/dev/null | grep -q .; then
            echo "✅ Docker 서비스 이미 실행 중"
        else
            echo "   필요한 서비스 시작 중..."
            # 빠른 시작 (타임아웃 적용)
            timeout 10 docker-compose up -d postgres redis chroma >/dev/null 2>&1 || echo "   Docker 서비스 시작 건너뜀"
        fi
    else
        echo "⚠️  Docker 사용 불가 - 로컬 환경으로 계속 진행"
    fi
fi

# 백엔드 시작
echo "🐍 백엔드 시작 중..."
if check_port 8001 "Backend"; then
    if [ "$BACKEND_MODE" = "uv" ]; then
        echo "   uv를 사용하여 백엔드 실행 중..."
        cd src/backend
        
        # 가상환경 활성화 및 서버 시작
        if [ ! -d ".venv" ]; then
            echo "   가상환경 생성 중..."
            uv venv
        fi
        
        echo "   의존성 설치 중..."
        if [ -f "uv.lock" ]; then
            echo "   uv.lock 파일을 사용하여 의존성 동기화 중..."
            uv sync 2>/dev/null || echo "   의존성 동기화 실패 - 기본 설치로 진행"
        elif [ -f "pyproject.toml" ]; then
            echo "   pyproject.toml로 설치 중..."
            uv pip install -e . 2>/dev/null || echo "   의존성 설치 실패"
        else
            echo "   의존성 파일을 찾을 수 없습니다."
        fi
        
        echo "   FastAPI 서버 시작 중..."
        source .venv/bin/activate
        export PYTHONPATH=$(pwd)
        
        # main.py 사용 (상세 로깅이 포함된 엔트리포인트)
        nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload > /tmp/backend_startup.log 2>&1 &
        BACKEND_PID=$!
        echo "   백엔드 PID: $BACKEND_PID"
        cd ../..
    
    elif [ "$BACKEND_MODE" = "python" ]; then
        echo "   Python을 사용하여 백엔드 실행 중..."
        cd src/backend
        
        if [ ! -d "venv" ]; then
            echo "   가상환경 생성 중..."
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        echo "   의존성 설치 중..."
        pip install -r requirements.txt 2>/dev/null || echo "requirements.txt가 없습니다. 수동으로 패키지를 설치해주세요."
        
        echo "   FastAPI 서버 시작 중..."
        export PYTHONPATH=$(pwd)
        # main.py 사용 (상세 로깅이 포함된 엔트리포인트)
        uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
        BACKEND_PID=$!
        cd ../..
        
    else
        echo "   Docker를 사용하여 백엔드 실행 중..."
        docker-compose up -d backend
        BACKEND_PID="docker"
    fi
    
    # 백엔드 시작 대기
    echo "⏳ 백엔드 시작 대기 중..."
    max_attempts=10
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # health, docs, 또는 루트 경로 확인
        if curl -s http://localhost:8001/health >/dev/null 2>&1 || \
           curl -s http://localhost:8001/docs >/dev/null 2>&1 || \
           curl -s http://localhost:8001/ >/dev/null 2>&1; then
            echo "✅ 백엔드 시작 완료"
            break
        fi
        
        attempt=$((attempt + 1))
        echo "   백엔드 시작 대기 중... ($attempt/$max_attempts)"
        sleep 3
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "⚠️  백엔드 시작 확인 실패 - 수동으로 확인해주세요"
        echo "   로그 확인: tail -f /tmp/backend_startup.log"
        # 완전히 실패하지 않고 계속 진행
    fi
else
    echo "✅ 백엔드 이미 실행 중"
fi

# 프론트엔드 시작
echo "⚛️  프론트엔드 시작 중..."
if check_port 3000 "Frontend"; then
    # 포트 3000이 사용 중이면 3001로 시도
    if check_port 3001 "Frontend-Alt"; then
        FRONTEND_PORT=3001
        echo "   포트 3001을 사용하여 프론트엔드 실행 중..."
    else
        echo "✅ 프론트엔드 이미 3001 포트에서 실행 중"
        FRONTEND_PORT=3001
    fi
else
    FRONTEND_PORT=3000
    echo "   포트 3000을 사용하여 프론트엔드 실행 중..."
fi

if [ "$FRONTEND_MODE" = "local" ] && [ -n "$FRONTEND_PORT" ]; then
    echo "   로컬 Node.js를 사용하여 프론트엔드 실행 중..."
    cd src/frontend
    
    if [ ! -d "node_modules" ]; then
        echo "   의존성 설치 중..."
        npm install
    fi
    
    echo "   React 개발 서버 시작 중 (포트: $FRONTEND_PORT)..."
    # 백엔드 URL을 환경변수로 설정하여 프론트엔드에 전달
    VITE_API_URL=http://localhost:8001 VITE_WS_URL=ws://localhost:8001 PORT=$FRONTEND_PORT npm run dev &
    FRONTEND_PID=$!
    cd ../..
    
    # 프론트엔드 시작 대기
    echo "⏳ 프론트엔드 시작 대기 중..."
    sleep 10
    
    if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
        echo "✅ 프론트엔드 시작 완료 (포트: $FRONTEND_PORT)"
    else
        echo "⚠️  프론트엔드 시작 확인 실패 - 수동으로 확인해주세요"
    fi
else
    echo "✅ 프론트엔드 이미 실행 중"
fi

# 완료 메시지
echo ""
echo "🎉 TechGiterview 개발 환경이 성공적으로 시작되었습니다!"
echo "=================================="
if [ -n "$FRONTEND_PORT" ]; then
    echo "📱 프론트엔드: http://localhost:$FRONTEND_PORT"
else
    echo "📱 프론트엔드: http://localhost:3001 (이미 실행 중)"
fi
echo "🔗 백엔드 API: http://localhost:8001"
echo "📚 API 문서: http://localhost:8001/docs"
echo "🐘 PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo "🌈 ChromaDB: http://localhost:8000"
echo ""
echo "🔧 개발 도구:"
echo "   - API 테스트: curl http://localhost:8001/health"
echo "   - WebSocket 테스트: ws://localhost:8001/ws/test"
echo "   - 로그 확인: docker-compose logs -f"
echo ""
echo "🔄 다시 시작 옵션:"
echo "   - 포트 정리 후 재시작: ./start.sh"
echo "   - 안전 모드로 재시작: AUTO_KILL_PORTS=false ./start.sh"
echo "   - Docker 포트까지 정리: AUTO_KILL_DOCKER_PORTS=true ./start.sh"
echo ""
echo "⏹️  종료하려면 Ctrl+C를 누르거나 ./scripts/dev-stop.sh를 실행하세요"

# 정리 함수
cleanup() {
    echo ""
    echo "🛑 서비스 종료 중..."
    
    if [ "$BACKEND_PID" != "docker" ] && [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ "$FRONTEND_PID" != "docker" ] && [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    docker-compose down
    echo "✅ 모든 서비스가 종료되었습니다."
    exit 0
}

# 시그널 처리
trap cleanup SIGINT SIGTERM

# 개발 모드에서는 무한 대기
if [ "$BACKEND_MODE" != "docker" ] || [ "$FRONTEND_MODE" != "docker" ]; then
    echo "💻 개발 모드 실행 중... (Ctrl+C로 종료)"
    while true; do
        sleep 1
    done
else
    echo "🐳 Docker 모드 실행 중..."
    echo "   로그 확인: docker-compose logs -f"
    echo "   종료: docker-compose down"
fi