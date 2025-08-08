#!/bin/bash

# TechGiterview Production Deployment Script
# 프로덕션 환경 배포를 위한 스크립트

set -e

echo "🚀 TechGiterview 프로덕션 배포"
echo "================================"

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 환경 변수 및 설정 확인
DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-"docker"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
BUILD_VERSION=${BUILD_VERSION:-$(date +%Y%m%d-%H%M%S)}

echo "📋 배포 설정:"
echo "   - 배포 모드: $DEPLOYMENT_MODE"
echo "   - 환경: $ENVIRONMENT"
echo "   - 빌드 버전: $BUILD_VERSION"

# 필수 도구 확인
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1이 설치되지 않았습니다."
        echo "   설치 가이드: $2"
        exit 1
    fi
}

echo "🔍 필수 도구 확인 중..."
check_tool "docker" "https://docs.docker.com/get-docker/"
check_tool "docker-compose" "https://docs.docker.com/compose/install/"

if [ "$DEPLOYMENT_MODE" = "kubernetes" ]; then
    check_tool "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    check_tool "helm" "https://helm.sh/docs/intro/install/"
fi

# 환경 설정 파일 확인
echo "📁 환경 설정 확인 중..."
if [ ! -f "src/backend/.env.prod" ]; then
    echo "❌ 프로덕션 환경 설정 파일(.env.prod)이 없습니다."
    echo "   .env.prod 파일을 생성하고 필요한 환경 변수를 설정해주세요."
    exit 1
fi

# 환경 변수 로드
export $(cat src/backend/.env.prod | grep -v '^#' | xargs)

# 필수 환경 변수 확인
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ 필수 환경 변수 $1이 설정되지 않았습니다."
        exit 1
    fi
}

echo "🔐 필수 환경 변수 확인 중..."
check_env_var "DATABASE_URL"
check_env_var "REDIS_URL"
check_env_var "SECRET_KEY"
check_env_var "GITHUB_TOKEN"

# 보안 검사
echo "🔒 보안 검사 중..."

# 기본 시크릿 키 사용 여부 확인
if [[ "$SECRET_KEY" == *"your-secret-key-here"* ]] || [[ ${#SECRET_KEY} -lt 32 ]]; then
    echo "❌ 안전하지 않은 SECRET_KEY가 설정되어 있습니다."
    echo "   32자 이상의 강력한 시크릿 키를 생성해주세요."
    exit 1
fi

# .env 파일이 Git에 포함되지 않았는지 확인
if git check-ignore src/backend/.env.prod >/dev/null 2>&1; then
    echo "✅ .env.prod 파일이 Git에서 제외되어 있습니다."
else
    echo "⚠️  .env.prod 파일이 Git에 포함될 수 있습니다."
    echo "   .gitignore에 .env.prod를 추가하는 것을 권장합니다."
fi

# 코드 품질 검사
echo "🧪 코드 품질 검사 중..."

# 백엔드 테스트 실행
if [ -f "src/backend/pyproject.toml" ]; then
    echo "   백엔드 테스트 실행 중..."
    cd src/backend
    
    if command -v uv &> /dev/null; then
        uv run pytest tests/ -v
    else
        python -m pytest tests/ -v
    fi
    
    cd ../..
    echo "✅ 백엔드 테스트 통과"
else
    echo "⚠️  백엔드 테스트 설정이 없습니다."
fi

# 프론트엔드 빌드 테스트
if [ -f "src/frontend/package.json" ]; then
    echo "   프론트엔드 빌드 테스트 중..."
    cd src/frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    npm run build
    cd ../..
    echo "✅ 프론트엔드 빌드 성공"
else
    echo "⚠️  프론트엔드 설정이 없습니다."
fi

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."

# 백엔드 이미지 빌드
echo "   백엔드 이미지 빌드 중..."
docker build -t techgiterview-backend:$BUILD_VERSION -f src/backend/Dockerfile src/backend/
docker tag techgiterview-backend:$BUILD_VERSION techgiterview-backend:latest

# 프론트엔드 이미지 빌드
echo "   프론트엔드 이미지 빌드 중..."
docker build -t techgiterview-frontend:$BUILD_VERSION -f src/frontend/Dockerfile src/frontend/
docker tag techgiterview-frontend:$BUILD_VERSION techgiterview-frontend:latest

echo "✅ Docker 이미지 빌드 완료"

# 이미지 보안 스캔 (선택사항)
if command -v trivy &> /dev/null; then
    echo "🔍 보안 스캔 실행 중..."
    trivy image --severity HIGH,CRITICAL techgiterview-backend:$BUILD_VERSION
    trivy image --severity HIGH,CRITICAL techgiterview-frontend:$BUILD_VERSION
    echo "✅ 보안 스캔 완료"
else
    echo "⚠️  Trivy가 설치되지 않아 보안 스캔을 건너뜁니다."
    echo "   보안을 위해 Trivy 설치를 권장합니다: https://aquasecurity.github.io/trivy/"
fi

# 배포 실행
case "$DEPLOYMENT_MODE" in
    "docker")
        echo "🐳 Docker Compose 프로덕션 배포..."
        
        # 프로덕션 compose 파일 사용
        if [ -f "docker-compose.prod.yml" ]; then
            docker-compose -f docker-compose.prod.yml down --remove-orphans
            docker-compose -f docker-compose.prod.yml up -d
        else
            echo "❌ docker-compose.prod.yml 파일이 없습니다."
            echo "   프로덕션용 Docker Compose 파일을 생성해주세요."
            exit 1
        fi
        ;;
        
    "kubernetes")
        echo "☸️  Kubernetes 배포..."
        
        # Kubernetes 매니페스트 적용
        if [ -d "k8s" ]; then
            # ConfigMap 및 Secret 생성
            kubectl create configmap techgiterview-config \
                --from-env-file=src/backend/.env.prod \
                --dry-run=client -o yaml | kubectl apply -f -
            
            # 애플리케이션 배포
            kubectl apply -f k8s/
            
            # 배포 상태 확인
            kubectl rollout status deployment/techgiterview-backend
            kubectl rollout status deployment/techgiterview-frontend
        else
            echo "❌ Kubernetes 매니페스트 디렉토리(k8s/)가 없습니다."
            exit 1
        fi
        ;;
        
    "aws")
        echo "☁️  AWS 배포..."
        
        # AWS CLI 확인
        if ! command -v aws &> /dev/null; then
            echo "❌ AWS CLI가 설치되지 않았습니다."
            exit 1
        fi
        
        # ECR에 이미지 푸시 (예시)
        if [ ! -z "$AWS_ECR_REPOSITORY" ]; then
            echo "   ECR에 이미지 푸시 중..."
            
            # ECR 로그인
            aws ecr get-login-password --region $AWS_REGION | \
                docker login --username AWS --password-stdin $AWS_ECR_REPOSITORY
            
            # 이미지 태그 및 푸시
            docker tag techgiterview-backend:$BUILD_VERSION $AWS_ECR_REPOSITORY/techgiterview-backend:$BUILD_VERSION
            docker tag techgiterview-frontend:$BUILD_VERSION $AWS_ECR_REPOSITORY/techgiterview-frontend:$BUILD_VERSION
            
            docker push $AWS_ECR_REPOSITORY/techgiterview-backend:$BUILD_VERSION
            docker push $AWS_ECR_REPOSITORY/techgiterview-frontend:$BUILD_VERSION
        fi
        
        # ECS 또는 EKS 배포 로직 추가 가능
        echo "⚠️  AWS 배포 로직을 추가로 구현해주세요."
        ;;
        
    *)
        echo "❌ 지원하지 않는 배포 모드: $DEPLOYMENT_MODE"
        echo "   지원되는 모드: docker, kubernetes, aws"
        exit 1
        ;;
esac

# 배포 후 헬스 체크
echo "🏥 배포 후 헬스 체크..."

# 서비스 시작 대기
sleep 30

# API 헬스 체크
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s "$BACKEND_URL/health" >/dev/null 2>&1; then
        echo "✅ 백엔드 헬스 체크 성공"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   백엔드 헬스 체크 시도 $attempt/$max_attempts..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ 백엔드 헬스 체크 실패"
    echo "   로그 확인: docker-compose logs backend"
    exit 1
fi

# 프론트엔드 헬스 체크
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}
if curl -s "$FRONTEND_URL" >/dev/null 2>&1; then
    echo "✅ 프론트엔드 헬스 체크 성공"
else
    echo "⚠️  프론트엔드 헬스 체크 실패"
    echo "   수동으로 확인해주세요: $FRONTEND_URL"
fi

# 서비스 상태 체크
echo "🔍 서비스 상태 체크..."
if curl -s "$BACKEND_URL/api/v1/health/services" | grep -q "healthy"; then
    echo "✅ 모든 서비스가 정상 상태입니다"
else
    echo "⚠️  일부 서비스에 문제가 있을 수 있습니다"
    echo "   상세 확인: $BACKEND_URL/api/v1/health/services"
fi

# 배포 완료
echo ""
echo "🎉 TechGiterview 프로덕션 배포가 완료되었습니다!"
echo "========================================"
echo "📊 배포 정보:"
echo "   - 빌드 버전: $BUILD_VERSION"
echo "   - 배포 시간: $(date)"
echo "   - 배포 모드: $DEPLOYMENT_MODE"
echo ""
echo "🌐 서비스 URL:"
echo "   - 프론트엔드: $FRONTEND_URL"
echo "   - 백엔드 API: $BACKEND_URL"
echo "   - API 문서: $BACKEND_URL/docs"
echo ""
echo "🔧 관리 명령어:"
case "$DEPLOYMENT_MODE" in
    "docker")
        echo "   - 로그 확인: docker-compose -f docker-compose.prod.yml logs -f"
        echo "   - 서비스 재시작: docker-compose -f docker-compose.prod.yml restart"
        echo "   - 서비스 중지: docker-compose -f docker-compose.prod.yml down"
        ;;
    "kubernetes")
        echo "   - 팟 상태 확인: kubectl get pods"
        echo "   - 로그 확인: kubectl logs -l app=techgiterview"
        echo "   - 서비스 재시작: kubectl rollout restart deployment/techgiterview-backend"
        ;;
esac

echo ""
echo "📈 모니터링:"
echo "   - 헬스 체크: $BACKEND_URL/health"
echo "   - 서비스 상태: $BACKEND_URL/api/v1/health/services"
echo "   - 메트릭: $BACKEND_URL/metrics (구현 필요)"
echo ""
echo "🚨 문제 발생 시:"
echo "   - 로그 확인"
echo "   - 이전 버전으로 롤백"
echo "   - 헬스 체크 URL 모니터링"
echo ""
echo "✅ 배포 스크립트 실행 완료"