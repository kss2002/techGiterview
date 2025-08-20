# TechGiterview 배포 가이드

## 🚀 배포 환경 수정사항

### 1. Docker 포트 설정 수정 완료
- **프론트엔드**: 9105:3001 (외부:내부)
- **백엔드**: 9104:8002 (외부:내부)
- **Redis**: 6379:6379

### 2. Nginx 서버 설정 업데이트 필요

기존 nginx 설정을 다음과 같이 수정해주세요:

```nginx
server {
    server_name tgv.oursophy.com;
    
    # Frontend 프록시
    location / {
        proxy_pass http://127.0.0.1:9105;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # API 프록시 (백엔드)
    location /api/ {
        proxy_pass http://127.0.0.1:9104/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket 프록시
    location /ws/ {
        proxy_pass http://127.0.0.1:9104/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/tgv.oursophy.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tgv.oursophy.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```

### 3. 배포 명령어

#### 운영 환경 배포
```bash
# 운영용 Docker Compose 실행
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 또는 별도 명령어로
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 개발 환경 실행 (로컬)
```bash
# 개발용 실행 (기본)
docker-compose up -d --build
```

### 4. 문제 해결

#### A. Vite HMR WebSocket 오류 해결
- **원인**: 운영환경에서 Vite 개발 서버 사용
- **해결**: `docker-compose.prod.yml` 사용하여 정적 빌드 배포

#### B. 포트 불일치 오류 해결
- **이전**: 프론트엔드 3001, 백엔드 8002 (로컬 개발용)
- **수정**: 프론트엔드 9105, 백엔드 9104 (배포용)

#### C. CORS 오류 해결
- **추가된 도메인**: `https://tgv.oursophy.com`
- **백엔드 CORS 설정**: 자동으로 허용됨

### 5. 배포 후 확인사항

1. **서비스 상태 확인**
```bash
docker-compose ps
docker-compose logs frontend
docker-compose logs backend
```

2. **Health Check 확인**
```bash
# 백엔드 health check
curl http://localhost:9104/health

# 프론트엔드 접근 확인
curl http://localhost:9105
```

3. **SSL/HTTPS 확인**
```bash
# 외부 접근 확인
curl -I https://tgv.oursophy.com
```

### 6. 로그 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f

# 특정 서비스 로그만
docker-compose logs -f frontend
docker-compose logs -f backend
```

### 7. 배포 롤백

문제 발생 시 이전 버전으로 롤백:

```bash
# 컨테이너 중지
docker-compose down

# 이전 이미지로 실행
docker-compose up -d
```

## ✅ 수정된 파일 목록

- `docker-compose.yml`: 포트 매핑 수정
- `docker-compose.prod.yml`: 운영 환경 설정
- `src/frontend/nginx.conf`: 내부 백엔드 포트 8002로 수정
- `src/backend/app/core/config.py`: CORS 도메인 추가
- `nginx-server.conf`: 외부 Nginx 설정 예제
- `DEPLOYMENT.md`: 이 배포 가이드

이제 배포 환경에서 Vite HMR 오류가 해결되고 모든 포트가 일치하여 정상 작동할 것입니다! 🎉