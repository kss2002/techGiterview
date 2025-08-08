# Node.js 18 베이스 이미지
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (개발 의존성 포함)
RUN npm ci

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 3000

# Vite 개발 서버 시작
CMD ["npm", "run", "dev"]