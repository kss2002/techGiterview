#!/bin/bash

# TechGiterview Main Startup Script
# 메인 시작 스크립트 - 환경에 따라 적절한 스크립트를 실행

set -e

echo "🚀 TechGiterview 시작"
echo "===================="

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(dirname "$0")/scripts"

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "❌ scripts 디렉토리를 찾을 수 없습니다."
    exit 1
fi

# 환경 감지
ENVIRONMENT=${ENVIRONMENT:-"development"}

echo "🔍 현재 환경: $ENVIRONMENT"

# 사용법 출력 함수
show_usage() {
    echo ""
    echo "사용법: $0 [환경] [옵션]"
    echo ""
    echo "환경:"
    echo "  dev, development    개발 환경으로 시작"
    echo "  prod, production    프로덕션 환경으로 배포"
    echo "  stop               개발 환경 종료"
    echo ""
    echo "옵션:"
    echo "  --help, -h         이 도움말 표시"
    echo "  --version, -v      버전 정보 표시"
    echo ""
    echo "예시:"
    echo "  $0 dev             # 개발 환경 시작"
    echo "  $0 prod            # 프로덕션 배포"
    echo "  $0 stop            # 개발 환경 종료"
    echo ""
}

# 버전 정보 출력
show_version() {
    echo "TechGiterview v1.0.0"
    echo "GitHub 기반 기술면접 준비 AI 에이전트"
    echo ""
    echo "Components:"
    echo "  - Backend: FastAPI + Python"
    echo "  - Frontend: React + TypeScript"
    echo "  - Database: PostgreSQL + Redis + ChromaDB"
    echo "  - AI: LangChain + OpenAI"
    echo ""
}

# 인자 처리
case "${1:-dev}" in
    "dev"|"development")
        echo "🔧 개발 환경을 시작합니다..."
        exec "$SCRIPT_DIR/dev-start.sh"
        ;;
    
    "prod"|"production")
        echo "🚀 프로덕션 환경으로 배포합니다..."
        exec "$SCRIPT_DIR/prod-deploy.sh"
        ;;
    
    "stop")
        echo "🛑 개발 환경을 종료합니다..."
        exec "$SCRIPT_DIR/dev-stop.sh"
        ;;
    
    "--help"|"-h"|"help")
        show_usage
        exit 0
        ;;
    
    "--version"|"-v"|"version")
        show_version
        exit 0
        ;;
    
    *)
        echo "❌ 알 수 없는 명령어: $1"
        show_usage
        exit 1
        ;;
esac