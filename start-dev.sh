#!/bin/bash

# TechGiterview 개발 환경 시작 스크립트
# 백엔드와 프론트엔드를 동시에 실행합니다.

set -e

echo "🚀 TechGiterview 개발 환경을 시작합니다..."

# 현재 디렉토리 저장
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/src/backend"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 정리 함수
cleanup() {
    log_info "서버들을 종료하는 중..."
    jobs -p | xargs -r kill
    wait
    log_info "모든 서버가 종료되었습니다."
}

# 시그널 핸들러 설정
trap cleanup EXIT INT TERM

# 의존성 확인
check_dependencies() {
    log_info "의존성을 확인하는 중..."
    
    if ! command -v uv &> /dev/null; then
        log_error "uv가 설치되지 않았습니다. 설치해주세요."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm이 설치되지 않았습니다. 설치해주세요."
        exit 1
    fi
    
    log_success "모든 의존성이 확인되었습니다."
}

# 포트 확인 및 정리
check_ports() {
    log_info "포트 상태를 확인하는 중..."
    
    # 포트 8003 (백엔드) 확인
    if lsof -Pi :8003 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "포트 8003이 이미 사용 중입니다. 프로세스를 종료합니다."
        fuser -k 8003/tcp 2>/dev/null || true
        sleep 2
    fi
    
    # 포트 3001 (프론트엔드) 확인
    if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "포트 3001이 이미 사용 중입니다. 프로세스를 종료합니다."
        fuser -k 3001/tcp 2>/dev/null || true
        sleep 2
    fi
    
    log_success "포트가 준비되었습니다."
}

# 백엔드 시작
start_backend() {
    log_info "백엔드 서버를 시작하는 중..."
    
    cd "$BACKEND_DIR"
    
    # 백엔드 의존성 확인
    if [ ! -f "pyproject.toml" ]; then
        log_error "백엔드 디렉토리에 pyproject.toml 파일이 없습니다."
        exit 1
    fi
    
    # 백엔드 서버 시작 (백그라운드)
    PYTHONPATH="$BACKEND_DIR" uv run uvicorn main:app --host 0.0.0.0 --port 8003 --log-level info &
    BACKEND_PID=$!
    
    # 백엔드 서버 시작 대기
    log_info "백엔드 서버가 시작되기를 기다리는 중..."
    for i in {1..30}; do
        if curl -s -f http://localhost:8003/health > /dev/null 2>&1; then
            log_success "백엔드 서버가 포트 8003에서 시작되었습니다."
            return 0
        fi
        sleep 1
    done
    
    log_error "백엔드 서버 시작에 실패했습니다."
    return 1
}

# 프론트엔드 시작
start_frontend() {
    log_info "프론트엔드 서버를 시작하는 중..."
    
    cd "$FRONTEND_DIR"
    
    # 프론트엔드 의존성 확인
    if [ ! -f "package.json" ]; then
        log_error "프론트엔드 디렉토리에 package.json 파일이 없습니다."
        exit 1
    fi
    
    # 프론트엔드 서버 시작 (백그라운드)
    PORT=3001 npm run dev &
    FRONTEND_PID=$!
    
    # 프론트엔드 서버 시작 대기
    log_info "프론트엔드 서버가 시작되기를 기다리는 중..."
    for i in {1..30}; do
        if curl -s -f http://localhost:3001 > /dev/null 2>&1; then
            log_success "프론트엔드 서버가 포트 3001에서 시작되었습니다."
            return 0
        fi
        sleep 1
    done
    
    log_error "프론트엔드 서버 시작에 실패했습니다."
    return 1
}

# 메인 실행
main() {
    check_dependencies
    check_ports
    
    # 백엔드 시작
    if start_backend; then
        log_success "백엔드 준비 완료"
    else
        log_error "백엔드 시작 실패"
        exit 1
    fi
    
    # 프론트엔드 시작
    if start_frontend; then
        log_success "프론트엔드 준비 완료"
    else
        log_error "프론트엔드 시작 실패"
        exit 1
    fi
    
    echo ""
    log_success "🎉 TechGiterview 개발 환경이 성공적으로 시작되었습니다!"
    echo ""
    echo "  📱 프론트엔드: http://localhost:3001"
    echo "  🔧 백엔드 API: http://localhost:8003"
    echo "  📚 API 문서: http://localhost:8003/docs"
    echo ""
    log_info "서버를 종료하려면 Ctrl+C를 누르세요."
    echo ""
    
    # 서버들이 계속 실행되도록 대기
    wait
}

# 스크립트 실행
main "$@"