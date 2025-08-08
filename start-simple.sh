#!/bin/bash

# TechGiterview Simple Startup Script
# 간단한 서비스 상태 확인 및 시작

set -e

echo "🚀 TechGiterview 간편 시작"
echo "========================="

# 현재 실행 중인 서비스 확인
echo "🔍 현재 서비스 상태 확인 중..."

# 백엔드 확인 (포트 8000)
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ 백엔드: http://localhost:8000 (실행 중)"
    BACKEND_RUNNING=true
else
    echo "❌ 백엔드: http://localhost:8000 (실행 필요)"
    BACKEND_RUNNING=false
fi

# 프론트엔드 확인 (포트 3001)
if curl -s http://localhost:3001 >/dev/null 2>&1; then
    echo "✅ 프론트엔드: http://localhost:3001 (실행 중)"
    FRONTEND_RUNNING=true
else
    echo "❌ 프론트엔드: http://localhost:3001 (실행 필요)"
    FRONTEND_RUNNING=false
fi

# 포트 3000 확인 (다른 서비스)
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ℹ️  포트 3000: 다른 서비스가 사용 중"
else
    echo "✅ 포트 3000: 사용 가능"
fi

echo ""
echo "📊 실행 상태 요약:"
echo "   백엔드 (8000): $($BACKEND_RUNNING && echo "✅ 실행 중" || echo "❌ 중지됨")"
echo "   프론트엔드 (3001): $($FRONTEND_RUNNING && echo "✅ 실행 중" || echo "❌ 중지됨")"

if $BACKEND_RUNNING && $FRONTEND_RUNNING; then
    echo ""
    echo "🎉 모든 서비스가 실행 중입니다!"
    echo "   📱 프론트엔드: http://localhost:3001"
    echo "   🔗 백엔드 API: http://localhost:8000"
    echo "   📚 API 문서: http://localhost:8000/docs"
else
    echo ""
    echo "⚠️  일부 서비스가 실행되지 않았습니다."
    echo "   수동으로 서비스를 시작해주세요:"
    
    if ! $BACKEND_RUNNING; then
        echo "   🐍 백엔드 시작:"
        echo "      cd src/backend && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    fi
    
    if ! $FRONTEND_RUNNING; then
        echo "   ⚛️  프론트엔드 시작:"
        echo "      cd src/frontend && PORT=3001 npm run dev"
    fi
fi

echo ""
echo "🔧 추가 정보:"
echo "   - 건강 상태 확인: curl http://localhost:8000/health"
echo "   - 테스트 대시보드: http://localhost:3001/dashboard/e1943ef8-5e10-4bb6-b592-db70bf010c2f"
echo "   - 질문 캐시 상태: curl http://localhost:8000/api/v1/questions/debug/cache"