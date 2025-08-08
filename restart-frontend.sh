#!/bin/bash

# TechGiterview Frontend Docker 재시작 스크립트
echo "🚀 Frontend Docker 컨테이너 재빌드 및 시작..."

# 현재 사용자를 docker 그룹에 추가 (권한 문제 해결)
echo "📋 Docker 권한 확인 중..."
if ! groups | grep -q docker; then
    echo "❌ Docker 권한이 없습니다. 다음 명령을 실행해주세요:"
    echo "   sudo usermod -aG docker $USER"
    echo "   그 후 터미널을 다시 시작하거나 로그아웃/로그인하세요."
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 frontend 컨테이너 정리..."
docker-compose stop frontend
docker-compose rm -f frontend

# 이미지 재빌드 (캐시 무시)
echo "🔨 Frontend 이미지 재빌드..."
docker-compose build --no-cache frontend

# 컨테이너 시작
echo "▶️  Frontend 컨테이너 시작..."
docker-compose up -d frontend

# 컨테이너 상태 확인
echo "📊 컨테이너 상태 확인..."
sleep 10
docker-compose ps frontend
docker-compose logs --tail=20 frontend

echo "✅ Frontend 재시작 완료!"
echo "🌐 브라우저에서 http://localhost:9105 로 접속해보세요."