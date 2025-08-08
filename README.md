# TechGiterview 🚀

> GitHub 저장소를 분석하여 맞춤형 기술면접 질문을 생성하는 AI 플랫폼

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/hong-seongmin/techGiterview.svg)](https://github.com/hong-seongmin/techGiterview/stargazers)

## ✨ 주요 기능

- **🔍 스마트 저장소 분석**: GitHub 저장소의 코드 구조, 기술 스택, 복잡도를 AI가 자동 분석
- **❓ 맞춤형 질문 생성**: Google Gemini 기반으로 저장소에 특화된 기술면접 질문 생성
- **💬 실시간 모의면접**: WebSocket 기반 대화형 면접 시뮬레이션
- **📊 상세 분석 리포트**: 파일 중요도, 기술 스택 분포, 복잡도 점수 제공
- **🎨 직관적 UI**: React + TypeScript 기반 모던 웹 인터페이스

## 🚀 빠른 시작

### 1. 프로젝트 클론 & 설정

```bash
git clone https://github.com/hong-seongmin/techGiterview.git
cd techGiterview
```

### 2. 환경 변수 설정

```bash
# 백엔드 환경 변수 생성
cp src/backend/.env.example src/backend/.env.dev

# 필수 API 키 설정
GITHUB_TOKEN=your_github_token        # GitHub API 접근용
GOOGLE_API_KEY=your_google_api_key    # Gemini AI 사용용
```

### 3. 개발 서버 시작

```bash
# 개발 환경 시작 (Docker + Node.js)
./scripts/dev-start.sh

# 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# API 문서: http://localhost:8001/docs
```

## 🛠 기술 스택

### Backend
- **FastAPI** - 고성능 Python API 프레임워크
- **Google Gemini 2.0 Flash** - 최신 AI 모델로 질문 생성
- **LangGraph** - AI 에이전트 워크플로우 관리
- **PostgreSQL** - 메인 데이터베이스
- **Redis** - 캐싱 및 세션 관리
- **ChromaDB** - 벡터 임베딩 저장소

### Frontend  
- **React 18** - 모던 UI 라이브러리
- **TypeScript** - 타입 안전성
- **Vite** - 빠른 빌드 도구
- **WebSocket** - 실시간 통신

## 🧪 테스트

```bash
# 백엔드 테스트
cd src/backend && uv run pytest tests/ -v

# 프론트엔드 테스트  
cd src/frontend && npm test

# 통합 테스트
./scripts/run-tests.sh
```

## 🤝 기여하기

1. 프로젝트 Fork
2. 기능 브랜치 생성: `git checkout -b feature/amazing-feature`
3. 변경사항 커밋: `git commit -m 'Add amazing feature'`
4. 브랜치 Push: `git push origin feature/amazing-feature`
5. Pull Request 생성

## ☕ 후원

이 프로젝트가 도움이 되셨다면 커피 한 잔으로 응원해주세요!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/oursophy)

## 📄 라이선스

MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👨‍💻 개발자

**Hong Seongmin** - [GitHub](https://github.com/hong-seongmin)

---

⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!