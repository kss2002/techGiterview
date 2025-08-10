"""
GitHub API Integration Router

실제 GitHub API와 연동하여 저장소 분석을 수행합니다.
"""

import asyncio
import aiohttp
import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.core.config import settings
# from app.core.database import get_db
# from app.models.repository import RepositoryAnalysis

# 임시 메모리 저장소
analysis_cache = {}


router = APIRouter()


class RepositoryAnalysisRequest(BaseModel):
    """저장소 분석 요청"""
    repo_url: HttpUrl
    store_results: bool = True


class RepositoryInfo(BaseModel):
    """저장소 기본 정보"""
    name: str
    owner: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    size: int
    topics: List[str]
    default_branch: str


class FileInfo(BaseModel):
    """파일 정보"""
    path: str
    type: str
    size: int
    content: Optional[str] = None


class FileTreeNode(BaseModel):
    """파일 트리 노드"""
    name: str
    path: str
    type: str  # "file" or "dir"
    size: Optional[int] = None
    children: Optional[List['FileTreeNode']] = None

# Forward reference 해결을 위해 모델 업데이트
FileTreeNode.model_rebuild()


class AnalysisResult(BaseModel):
    """분석 결과"""
    success: bool
    analysis_id: str
    repo_info: RepositoryInfo
    tech_stack: Dict[str, float]
    key_files: List[FileInfo]
    summary: str
    recommendations: List[str]
    created_at: datetime
    smart_file_analysis: Optional[Dict[str, Any]] = None


class GitHubClient:
    """실제 GitHub API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechGiterview/1.0"
        }
        if settings.github_token and settings.github_token != "your_github_token_here":
            self.headers["Authorization"] = f"token {settings.github_token}"
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """저장소 기본 정보 조회"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 404:
                    raise HTTPException(status_code=404, detail="Repository not found")
                elif response.status != 200:
                    raise HTTPException(status_code=response.status, detail="GitHub API error")
                
                return await response.json()
    
    async def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """저장소 내용 조회"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    return []
                return await response.json()
    
    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """파일 내용 조회"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                if data.get("type") == "file" and data.get("content"):
                    import base64
                    return base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
                return None
    
    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """저장소 사용 언어 조회"""
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    return {}
                return await response.json()


class RepositoryAnalyzer:
    """실제 저장소 분석기"""
    
    def __init__(self):
        self.github_client = GitHubClient()
        # SmartFileImportanceAnalyzer 추가
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        self.smart_file_analyzer = SmartFileImportanceAnalyzer()
        self.important_files = [
            "package.json", "requirements.txt", "Cargo.toml", "go.mod", 
            "pom.xml", "build.gradle", "composer.json", "Gemfile",
            "Dockerfile", "docker-compose.yml", "README.md", ".gitignore",
            "main.py", "app.py", "index.js", "main.js", "App.js", "main.go"
        ]
        self.tech_stack_patterns = {
            "React": ["package.json", "react", "jsx", "tsx"],
            "Vue.js": ["package.json", "vue", ".vue"],
            "Angular": ["package.json", "angular", "@angular"],
            "Node.js": ["package.json", "node_modules", "npm"],
            "Python": ["requirements.txt", ".py", "pip", "conda"],
            "Django": ["manage.py", "django", "settings.py"],
            "FastAPI": ["fastapi", "uvicorn", "main.py"],
            "Flask": ["flask", "app.py"],
            "Go": ["go.mod", ".go", "main.go"],
            "Java": ["pom.xml", ".java", "build.gradle"],
            "Spring": ["spring", "springframework"],
            "Docker": ["Dockerfile", "docker-compose.yml"],
            "TypeScript": [".ts", ".tsx", "typescript"],
            "JavaScript": [".js", ".jsx"],
            "Rust": ["Cargo.toml", ".rs"],
            "C++": [".cpp", ".hpp", ".cc"],
            "C#": [".cs", ".csproj", ".sln"],
            "PHP": [".php", "composer.json"],
            "Ruby": [".rb", "Gemfile", "rails"],
            "Swift": [".swift", "Package.swift"],
            "Kotlin": [".kt", ".kts"],
        }
    
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """GitHub URL에서 owner와 repo 추출"""
        if not url.startswith("https://github.com/"):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
        parts = url.replace("https://github.com/", "").strip("/").split("/")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
        
        return parts[0], parts[1]
    
    async def analyze_tech_stack(self, owner: str, repo: str, languages: Dict[str, int]) -> Dict[str, float]:
        """기술 스택 분석"""
        tech_scores = {}
        total_bytes = sum(languages.values()) if languages else 1
        
        # 언어별 비율 계산
        for lang, bytes_count in languages.items():
            percentage = bytes_count / total_bytes
            tech_scores[lang] = round(percentage, 3)
        
        # 파일 기반 기술 스택 검출
        try:
            contents = await self.github_client.get_repository_contents(owner, repo)
            file_names = [item["name"] for item in contents if item["type"] == "file"]
            
            for tech, patterns in self.tech_stack_patterns.items():
                score = 0
                for pattern in patterns:
                    if any(pattern.lower() in file_name.lower() for file_name in file_names):
                        score += 0.1
                    
                    # package.json 내용 확인
                    if pattern == "package.json" and "package.json" in file_names:
                        package_content = await self.github_client.get_file_content(owner, repo, "package.json")
                        if package_content:
                            for other_pattern in patterns[1:]:  # 첫 번째는 파일명이므로 제외
                                if other_pattern.lower() in package_content.lower():
                                    score += 0.2
                
                if score > 0:
                    tech_scores[tech] = min(score, 1.0)
        
        except Exception as e:
            print(f"Tech stack analysis error: {e}")
        
        return tech_scores
    
    async def get_key_files(self, owner: str, repo: str) -> List[FileInfo]:
        """주요 파일 추출"""
        key_files = []
        
        try:
            contents = await self.github_client.get_repository_contents(owner, repo)
            
            for item in contents:
                if item["type"] == "file" and item["name"] in self.important_files:
                    # 모든 파일의 내용을 가져오기 (크기 제한 없음)
                    file_content = await self.github_client.get_file_content(owner, repo, item["path"])
                    
                    key_files.append(FileInfo(
                        path=item["path"],
                        type=item["type"],
                        size=item["size"],
                        content=file_content
                    ))
            
            # src 폴더의 중요 파일들도 확인
            try:
                src_contents = await self.github_client.get_repository_contents(owner, repo, "src")
                for item in src_contents[:5]:  # 최대 5개까지만
                    if item["type"] == "file" and any(ext in item["name"] for ext in [".py", ".js", ".ts", ".go", ".java"]):
                        # 모든 파일의 내용을 가져오기 (크기 제한 없음)
                        file_content = await self.github_client.get_file_content(owner, repo, item["path"])
                        
                        key_files.append(FileInfo(
                            path=item["path"],
                            type=item["type"],
                            size=item["size"],
                            content=file_content
                        ))
            except:
                pass
                
        except Exception as e:
            print(f"Key files extraction error: {e}")
        
        return key_files
    
    async def get_all_files(self, owner: str, repo: str, max_depth: int = 3, max_files: int = 500) -> List[FileTreeNode]:
        """재귀적으로 모든 파일을 트리 구조로 가져오기"""
        
        async def fetch_directory_recursive(path: str = "", current_depth: int = 0) -> List[FileTreeNode]:
            if current_depth >= max_depth:
                return []
            
            try:
                contents = await self.github_client.get_repository_contents(owner, repo, path)
                nodes = []
                file_count = 0
                
                # 파일과 디렉토리를 분리하여 정렬
                files = [item for item in contents if item["type"] == "file"]
                dirs = [item for item in contents if item["type"] == "dir"]
                
                # 디렉토리 먼저 추가
                for item in sorted(dirs, key=lambda x: x["name"].lower()):
                    if file_count >= max_files:
                        break
                    
                    # 숨김 폴더나 불필요한 폴더 제외
                    if item["name"].startswith('.') and item["name"] not in ['.github', '.vscode']:
                        continue
                    if item["name"] in ['node_modules', 'venv', '__pycache__', 'target', 'build', 'dist']:
                        continue
                    
                    children = await fetch_directory_recursive(item["path"], current_depth + 1)
                    
                    node = FileTreeNode(
                        name=item["name"],
                        path=item["path"],
                        type="dir",
                        children=children if children else []
                    )
                    nodes.append(node)
                    file_count += 1
                
                # 파일들 추가
                for item in sorted(files, key=lambda x: x["name"].lower()):
                    if file_count >= max_files:
                        break
                    
                    # 바이너리 파일이나 불필요한 파일 제외
                    name = item["name"].lower()
                    if any(name.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz']):
                        continue
                    
                    node = FileTreeNode(
                        name=item["name"],
                        path=item["path"],
                        type="file",
                        size=item["size"]
                    )
                    nodes.append(node)
                    file_count += 1
                
                return nodes
                
            except Exception as e:
                print(f"Error fetching directory {path}: {e}")
                return []
        
        try:
            return await fetch_directory_recursive()
        except Exception as e:
            print(f"Error in get_all_files: {e}")
            return []
    
    def generate_summary(self, repo_info: RepositoryInfo, tech_stack: Dict[str, float]) -> str:
        """프로젝트 요약 생성"""
        main_tech = max(tech_stack.items(), key=lambda x: x[1])[0] if tech_stack else "Unknown"
        
        summary = f"이 프로젝트는 {main_tech}을(를) 주요 기술로 사용하는 "
        
        if repo_info.stars > 1000:
            summary += "인기 있는 "
        elif repo_info.stars > 100:
            summary += "관심받는 "
        
        summary += f"오픈소스 프로젝트입니다. "
        
        if repo_info.description:
            summary += f"프로젝트 설명: {repo_info.description}"
        
        return summary
    
    def generate_recommendations(self, tech_stack: Dict[str, float], key_files: List[FileInfo]) -> List[str]:
        """개선 제안 생성"""
        recommendations = []
        
        # README 확인
        if not any("README" in f.path.upper() for f in key_files):
            recommendations.append("프로젝트에 README.md 파일을 추가하여 프로젝트 설명을 제공하세요.")
        
        # 테스트 파일 확인
        has_tests = any("test" in f.path.lower() for f in key_files)
        if not has_tests:
            recommendations.append("테스트 코드를 추가하여 코드 품질을 향상시키세요.")
        
        # Docker 확인
        has_docker = any("Dockerfile" in f.path for f in key_files)
        if not has_docker and len(tech_stack) > 1:
            recommendations.append("Docker를 사용하여 배포 환경을 표준화하는 것을 고려해보세요.")
        
        # CI/CD 확인
        has_ci = any(".github" in f.path for f in key_files)
        if not has_ci:
            recommendations.append("GitHub Actions을 사용하여 CI/CD 파이프라인을 구축해보세요.")
        
        return recommendations
    
    def calculate_complexity_score(self, tech_stack: Dict[str, float], key_files: List[FileInfo], languages: Dict[str, int]) -> float:
        """복잡도 점수 계산"""
        complexity_factors = []
        
        # 1. 기술 스택 다양성 (0-2점)
        tech_diversity = min(len(tech_stack) / 5, 1.0) * 2
        complexity_factors.append(tech_diversity)
        
        # 2. 파일 수 기반 복잡도 (0-2점)
        file_complexity = min(len(key_files) / 20, 1.0) * 2
        complexity_factors.append(file_complexity)
        
        # 3. 언어 다양성 (0-2점)
        lang_diversity = min(len(languages) / 3, 1.0) * 2
        complexity_factors.append(lang_diversity)
        
        # 4. 파일 크기 기반 복잡도 (0-2점)
        total_size = sum(f.size for f in key_files)
        size_complexity = min(total_size / 100000, 1.0) * 2  # 100KB 기준
        complexity_factors.append(size_complexity)
        
        # 5. 기본 복잡도 (0-2점)
        base_complexity = 2.0
        complexity_factors.append(base_complexity)
        
        # 평균 계산 (0-10 범위)
        return round(sum(complexity_factors) / len(complexity_factors), 2)


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_repository(
    request: RepositoryAnalysisRequest,
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key")
):
    """실제 GitHub 저장소 분석 - 상세 RepositoryAnalyzer 사용"""
    
    # 헤더에서 API 키 추출
    api_keys = {}
    if github_token:
        api_keys["github_token"] = github_token
    if google_api_key:
        api_keys["google_api_key"] = google_api_key
    
    # 상세 로깅이 포함된 RepositoryAnalyzer 사용
    from app.agents.repository_analyzer import RepositoryAnalyzer
    analyzer = RepositoryAnalyzer()
    
    # 고유 분석 ID 생성
    analysis_id = str(uuid.uuid4())
    
    try:
        print(f"[GITHUB_API] ========== 저장소 분석 시작 ==========")
        print(f"[GITHUB_API] 요청 URL: {request.repo_url}")
        print(f"[GITHUB_API] 분석 ID: {analysis_id}")
        print(f"[GITHUB_API] API 키 정보: GitHub Token={github_token is not None}, Google API Key={google_api_key is not None}")
        
        # API 키를 포함하여 실제 RepositoryAnalyzer.analyze_repository() 사용
        analysis_result = await analyzer.analyze_repository(str(request.repo_url), api_keys=api_keys)
        
        if not analysis_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Repository analysis failed: {analysis_result.get('error', 'Unknown error')}"
            )
        
        # RepositoryAnalyzer 결과를 API 응답 형식으로 변환
        repo_info_data = analysis_result.get("repo_info", {})
        repo_info = RepositoryInfo(
            name=repo_info_data.get("name", ""),
            owner=repo_info_data.get("owner", ""),  # 직접 owner 필드 사용
            description=repo_info_data.get("description"),
            language=repo_info_data.get("language"),
            stars=repo_info_data.get("stargazers_count", 0),
            forks=repo_info_data.get("forks_count", 0),
            size=repo_info_data.get("size", 0),
            topics=[],  # TODO: topics 정보 추가
            default_branch="main"  # TODO: default_branch 정보 추가
        )
        
        # key_files 변환
        key_files_data = analysis_result.get("key_files", [])
        key_files = [
            FileInfo(
                path=f.get("path", ""),
                type="file",
                size=f.get("size", 0),
                content=f.get("content")
            )
            for f in key_files_data
        ]
        
        # tech_stack과 smart_file_analysis 가져오기
        tech_stack = analysis_result.get("tech_stack", {})
        smart_file_analysis = analysis_result.get("smart_file_analysis")
        
        # 요약 및 추천사항
        summary = analysis_result.get("analysis_summary", "분석이 완료되었습니다.")
        recommendations = [
            "프로젝트에 README.md 파일을 추가하여 프로젝트 설명을 제공하세요.",
            "테스트 코드를 추가하여 코드 품질을 향상시키세요.",
            "Docker를 사용하여 배포 환경을 표준화하는 것을 고려해보세요.",
            "GitHub Actions을 사용하여 CI/CD 파이프라인을 구축해보세요."
        ]
        
        print(f"[GITHUB_API] 분석 완료 - 기술스택: {len(tech_stack)}개, 핵심파일: {len(key_files)}개")
        
        # 결과 객체 생성
        result = AnalysisResult(
            success=True,
            analysis_id=analysis_id,
            repo_info=repo_info,
            tech_stack=tech_stack,
            key_files=key_files,
            summary=summary,
            recommendations=recommendations,
            created_at=datetime.utcnow(),
            smart_file_analysis=smart_file_analysis
        )
        
        # 임시 메모리 캐시에 저장
        analysis_cache[analysis_id] = result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str):
    """분석 결과 조회"""
    try:
        # UUID 검증
        uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    # 메모리 캐시에서 조회
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_cache[analysis_id]


@router.get("/analysis/{analysis_id}/all-files", response_model=List[FileTreeNode])
async def get_all_repository_files(analysis_id: str, max_depth: int = 3, max_files: int = 500):
    """분석된 저장소의 모든 파일 트리 구조 조회"""
    try:
        # UUID 검증
        uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    # 메모리 캐시에서 분석 결과 조회
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_result = analysis_cache[analysis_id]
    analyzer = RepositoryAnalyzer()
    
    try:
        # 저장소 정보에서 owner와 repo 추출
        owner = analysis_result.repo_info.owner
        repo = analysis_result.repo_info.name
        
        # 모든 파일을 트리 구조로 가져오기
        file_tree = await analyzer.get_all_files(owner, repo, max_depth, max_files)
        
        return file_tree
        
    except Exception as e:
        error_msg = str(e)
        
        # GitHub API 관련 에러 처리
        if "Connection timeout" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail="GitHub API 연결 시간 초과. 잠시 후 다시 시도해주세요."
            )
        elif "404" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404, 
                detail="저장소 또는 파일을 찾을 수 없습니다. 저장소 URL을 확인해주세요."
            )
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            raise HTTPException(
                status_code=403, 
                detail="GitHub API 접근 권한이 부족합니다. 비공개 저장소이거나 API 토큰을 확인해주세요."
            )
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="GitHub API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"파일 목록을 가져오는 중 오류가 발생했습니다: {error_msg}"
            )


@router.get("/analysis/{analysis_id}/file-content")
async def get_file_content(analysis_id: str, file_path: str):
    """특정 파일의 내용 조회 - 캐시 우선, 없으면 GitHub API 요청"""
    try:
        # UUID 검증
        uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    # 메모리 캐시에서 분석 결과 조회
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_result = analysis_cache[analysis_id]
    
    try:
        # 1. 먼저 캐시된 파일 목록에서 내용 찾기
        cached_content = None
        cached_file_info = None
        
        # smart_file_analysis에서 찾기
        if hasattr(analysis_result, 'smart_file_analysis') and analysis_result.smart_file_analysis:
            smart_files = analysis_result.smart_file_analysis.get('files', [])
            for file_info in smart_files:
                if file_info.get('file_path') == file_path or file_info.get('path') == file_path:
                    cached_content = file_info.get('content')
                    cached_file_info = file_info
                    break
        
        # key_files에서도 찾기
        if not cached_content and hasattr(analysis_result, 'key_files'):
            for file_info in analysis_result.key_files:
                if (hasattr(file_info, 'path') and file_info.path == file_path) or \
                   (isinstance(file_info, dict) and file_info.get('path') == file_path):
                    cached_content = getattr(file_info, 'content', None) or file_info.get('content')
                    cached_file_info = file_info
                    break
        
        # 2. 캐시된 내용이 있으면 바로 반환
        if cached_content and not cached_content.startswith('# File'):
            file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            file_size = len(cached_content)
            
            # 파일 크기 제한 없음 - 전체 내용 표시
            
            return {
                "success": True,
                "file_path": file_path,
                "content": cached_content,
                "size": file_size,
                "extension": file_extension,
                "is_binary": False,
                "source": "cache"  # 캐시에서 가져왔음을 표시
            }
        
        # 3. 캐시에 없으면 GitHub API에서 가져오기 (fallback)
        print(f"[FILE_CONTENT] 캐시에 없는 파일, GitHub API 요청: {file_path}")
        analyzer = RepositoryAnalyzer()
        owner = analysis_result.repo_info.owner
        repo = analysis_result.repo_info.name
        
        content = await analyzer.github_client.get_file_content(owner, repo, file_path)
        
        if content is None:
            raise HTTPException(status_code=404, detail="File not found or is binary")
        
        # 파일 크기 제한 없음 - 전체 내용 표시
        
        # 파일 정보 추가
        file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "extension": file_extension,
            "is_binary": False,
            "source": "github_api"  # GitHub API에서 가져왔음을 표시
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file content: {str(e)}")


@router.get("/analysis", response_model=List[Dict[str, Any]])
async def list_analyses(skip: int = 0, limit: int = 10):
    """분석 히스토리 목록 조회"""
    # 메모리 캐시에서 목록 조회
    analyses_list = []
    for analysis_id, result in analysis_cache.items():
        analyses_list.append({
            "analysis_id": analysis_id,
            "repository_url": f"https://github.com/{result.repo_info.owner}/{result.repo_info.name}",
            "repository_name": f"{result.repo_info.owner}/{result.repo_info.name}",
            "primary_language": result.repo_info.language,
            "complexity_score": 5.0,  # 임시값
            "created_at": result.created_at,
            "status": "completed"
        })
    
    # 날짜순 정렬 및 페이지네이션
    analyses_list.sort(key=lambda x: x["created_at"], reverse=True)
    return analyses_list[skip:skip + limit]


@router.get("/test")
async def test_github_connection():
    """GitHub API 연결 테스트"""
    client = GitHubClient()
    
    try:
        # 공개 저장소로 테스트
        repo_data = await client.get_repository_info("octocat", "Hello-World")
        return {
            "success": True,
            "message": "GitHub API connection successful",
            "test_repo": repo_data["name"],
            "authenticated": "Authorization" in client.headers
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"GitHub API connection failed: {str(e)}",
            "authenticated": "Authorization" in client.headers
        }


@router.get("/debug/cache")
async def debug_cache():
    """메모리 캐시 상태 확인 (디버깅용)"""
    return {
        "cache_size": len(analysis_cache),
        "cached_analysis_ids": list(analysis_cache.keys()),
        "analysis_details": [
            {
                "id": analysis_id,
                "repo": f"{result.repo_info.owner}/{result.repo_info.name}",
                "created_at": result.created_at.isoformat()
            }
            for analysis_id, result in analysis_cache.items()
        ]
    }


@router.delete("/debug/cache")
async def clear_cache():
    """메모리 캐시 초기화 (디버깅용)"""
    cache_size_before = len(analysis_cache)
    analysis_cache.clear()
    
    return {
        "message": "캐시가 성공적으로 초기화되었습니다",
        "cleared_items": cache_size_before,
        "current_cache_size": len(analysis_cache)
    }