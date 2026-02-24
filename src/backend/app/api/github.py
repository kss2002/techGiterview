"""
GitHub API Integration Router

실제 GitHub API와 연동하여 저장소 분석을 수행합니다.
"""

import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from sqlalchemy import func, String

from app.core.config import settings
from app.services.github_client import GitHubClient
from app.services.local_repository_analyzer import LocalRepositoryAnalyzer
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.agents.repository_analyzer import RepositoryAnalyzer as AgentRepositoryAnalyzer

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


@router.get("/analysis/recent")
async def get_recent_analyses(limit: int = 5, db: Session = Depends(get_db)):
    """최근 분석 결과 요약 조회 (데이터베이스 기반, 추정치 미사용)"""
    try:
        # 개발 모드 활성화 여부 확인
        from app.core.config import is_development_mode_active
        if not is_development_mode_active():
            print(f"[RECENT_ANALYSES] 개발 모드 비활성화 - 빈 결과 반환")
            return {
                "success": True,
                "data": [],
                "message": "Development mode is disabled. Recent analyses are not available."
            }
        
        print(f"[RECENT_ANALYSES] 최근 분석 요청 - limit: {limit}")
        
        # 데이터베이스에서 완료된 분석 결과 조회
        from app.models.repository import RepositoryAnalysis
        from sqlalchemy import desc

        recent_analyses_db = db.query(RepositoryAnalysis)\
            .filter(RepositoryAnalysis.status == "completed")\
            .order_by(desc(RepositoryAnalysis.created_at))\
            .limit(limit)\
            .all()
        
        final_analyses = []
        
        for analysis in recent_analyses_db:
            # URL에서 owner/repo 추출
            url_parts = analysis.repository_url.replace("https://github.com/", "").split("/")
            repo_owner = url_parts[0] if len(url_parts) > 0 else "Unknown"
            repo_name = url_parts[1] if len(url_parts) > 1 else analysis.repository_name or "Unknown"
            
            # 기술 스택 정보 처리 (실데이터만)
            tech_stack_dict = analysis.tech_stack if analysis.tech_stack else {}
            tech_stack = list(tech_stack_dict.keys())[:3]

            final_analyses.append({
                "analysis_id": analysis.id.hex if hasattr(analysis.id, 'hex') else str(analysis.id).replace('-', ''),
                "repository_name": repo_name,
                "repository_owner": repo_owner,
                "primary_language": analysis.primary_language or "Unknown",
                "created_at": analysis.created_at.isoformat(),
                "tech_stack": tech_stack,
                "file_count": analysis.file_count or 0
            })
        
        print(f"[RECENT_ANALYSES] 데이터베이스에서 {len(final_analyses)}개 분석 반환")
        
        return {
            "success": True,
            "data": final_analyses,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[RECENT_ANALYSES] Error: {e}")
        return {
            "success": False,
            "data": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)):
    """분석 결과 조회 - 메모리 캐시 우선, 없으면 데이터베이스에서 조회"""
    try:
        # UUID 검증
        uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    # 1. 메모리 캐시에서 조회 (우선)
    if analysis_id in analysis_cache:
        return analysis_cache[analysis_id]
    
    # 2. 데이터베이스에서 조회 (폴백)
    try:
        from app.models.repository import RepositoryAnalysis
        
        # SQLite에서는 UUID가 문자열로 저장되므로 문자열 비교 사용
        # 하이픈이 있는 형태와 없는 형태 모두 시도
        analysis_id_no_hyphens = analysis_id.replace('-', '')
        analysis_db = db.query(RepositoryAnalysis)\
            .filter(
                func.cast(RepositoryAnalysis.id, String).in_([analysis_id, analysis_id_no_hyphens])
            )\
            .first()
        
        if not analysis_db:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # 데이터베이스 결과를 AnalysisResult 형식으로 변환
        repo_url_parts = analysis_db.repository_url.replace("https://github.com/", "").split("/")
        owner = repo_url_parts[0] if len(repo_url_parts) > 0 else "Unknown"
        repo_name = repo_url_parts[1] if len(repo_url_parts) > 1 else "Unknown"
        
        repo_info = RepositoryInfo(
            name=repo_name,
            owner=owner,
            description=f"{owner}/{repo_name} repository",
            language=analysis_db.primary_language or "Unknown",
            stars=0,  # 데이터베이스에 없는 경우 기본값
            forks=0,
            size=0,
            topics=[],
            default_branch="main"
        )
        
        # 기본 파일 정보 (실제로는 별도 테이블에서 가져와야 함)
        key_files = []
        
        # 기술 스택 정보
        tech_stack = analysis_db.tech_stack if analysis_db.tech_stack else {}
        
        analysis_result = AnalysisResult(
            success=True,
            analysis_id=str(analysis_db.id),
            repo_info=repo_info,
            tech_stack=tech_stack,
            key_files=key_files,
            summary=f"{repo_name} 저장소 분석 결과",
            recommendations=[
                "테스트 코드를 추가하여 코드 품질을 향상시키세요.",
                "Docker를 사용하여 배포 환경을 표준화하는 것을 고려해보세요.",
                "GitHub Actions을 사용하여 CI/CD 파이프라인을 구축해보세요."
            ],
            created_at=analysis_db.created_at
        )
        
        # 메모리 캐시에도 저장 (다음번 조회 최적화)
        analysis_cache[analysis_id] = analysis_result
        
        return analysis_result
        
    except Exception as e:
        print(f"[DB_FALLBACK] Error loading from database: {e}")
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/analysis/{analysis_id}/all-files", response_model=List[FileTreeNode])
async def get_all_repository_files(
    analysis_id: str,
    max_depth: int = 3,
    max_files: int = 500,
    db: Session = Depends(get_db)
):
    """분석된 저장소의 모든 파일 트리 구조 조회"""
    try:
        # UUID 검증
        uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    analyzer = LocalRepositoryAnalyzer()
    
    try:
        owner = None
        repo = None

        # 1. 메모리 캐시 우선
        if analysis_id in analysis_cache:
            analysis_result = analysis_cache[analysis_id]
            owner = analysis_result.repo_info.owner
            repo = analysis_result.repo_info.name
        else:
            # 2. DB 폴백
            from app.models.repository import RepositoryAnalysis
            analysis_db = db.query(RepositoryAnalysis).filter(
                func.cast(RepositoryAnalysis.id, String).in_([analysis_id, analysis_id.replace('-', '')])
            ).first()
            if not analysis_db:
                raise HTTPException(status_code=404, detail="Analysis not found")

            repo_url_parts = analysis_db.repository_url.replace("https://github.com/", "").split("/")
            owner = repo_url_parts[0] if len(repo_url_parts) > 0 else None
            repo = repo_url_parts[1] if len(repo_url_parts) > 1 else None

        if not owner or not repo:
            raise HTTPException(status_code=404, detail="Repository information not found")
        
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
        analyzer = LocalRepositoryAnalyzer()
        owner = analysis_result.repo_info.owner
        repo = analysis_result.repo_info.name
        
        content = await analyzer.get_file_content(owner, repo, file_path)
        
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
        async with client as github_client:
            repo_data = await github_client.get_repository_info("https://github.com/octocat/Hello-World")
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


@router.post("/analyze-simple", response_model=AnalysisResult)
async def analyze_repository_simple(
    request: RepositoryAnalysisRequest,
    github_token: Optional[str] = Header(None, alias="x-github-token"),
    google_api_key: Optional[str] = Header(None, alias="x-google-api-key"),
    db: Session = Depends(get_db)
):
    """간단한 저장소 분석 - 캐시 저장 포함"""
    try:
        # URL 유효성 검증
        repo_url_str = str(request.repo_url)
        if not repo_url_str.startswith("https://github.com/"):
            raise HTTPException(status_code=400, detail="올바른 GitHub URL이 아닙니다.")
        
        # URL에서 소유자와 저장소 이름 추출
        parts = repo_url_str.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="저장소 정보를 추출할 수 없습니다.")
        
        owner, repo_name = parts[0], parts[1]
        analysis_id = str(uuid.uuid4())
        
        print(f"[ANALYZE_SIMPLE] ========== 실제 GitHub API 분석 시작 ==========")
        print(f"[ANALYZE_SIMPLE] 저장소: {owner}/{repo_name}")
        print(f"[ANALYZE_SIMPLE] 분석 ID: {analysis_id}")
        print(f"[ANALYZE_SIMPLE] 받은 헤더:")
        print(f"[ANALYZE_SIMPLE]   - GitHub Token: {'있음' if github_token else '없음'}")
        print(f"[ANALYZE_SIMPLE]   - Google API Key: {'있음' if google_api_key else '없음'}")
        if github_token:
            print(f"[ANALYZE_SIMPLE]   - GitHub Token 값: {github_token[:20]}...")
        if google_api_key:
            print(f"[ANALYZE_SIMPLE]   - Google API Key 값: {google_api_key[:20]}...")
        
        # 실제 GitHub API를 사용한 분석 (헤더에서 받은 토큰 사용)
        
        # [ADVANCED ANALYZER] AgentRepositoryAnalyzer 사용 (PageRank + Hybrid Selection)
        print(f"[ANALYZE_SIMPLE] 고급 분석 에이전트 시작...")
        
        # AgentAnalyzer는 내부적으로 GitHubClient를 초기화하지만, 토큰 설정이 필요함
        analyzer = AgentRepositoryAnalyzer()
        
        # API 키 딕셔너리 준비
        api_keys = {}
        if github_token and github_token != "your_github_token_here":
            api_keys["github_token"] = github_token
        
        # Agent 실행
        agent_result = await analyzer.analyze_repository(repo_url_str, api_keys, use_advanced=True)
        
        if not agent_result or not agent_result.get("success", True):
             error_msg = agent_result.get("error", "Unknown error in agent analysis")
             raise HTTPException(status_code=500, detail=f"분석 에이전트 오류: {error_msg}")
             
        # 결과 매핑 (Dict -> Pydantic Models)
        
        # 1. RepositoryInfo
        repo_info_data = agent_result.get("repo_info", {})
        owner_name = repo_info_data.get("owner", {}).get("login", owner) if isinstance(repo_info_data.get("owner"), dict) else repo_info_data.get("owner", owner)
        
        repo_info = RepositoryInfo(
            name=repo_info_data.get("name", repo_name),
            owner=owner_name,
            description=repo_info_data.get("description", "") or f"{owner_name}/{repo_name}",
            language=repo_info_data.get("language") or "Unknown",
            stars=repo_info_data.get("stargazers_count", 0),
            forks=repo_info_data.get("forks_count", 0),
            size=repo_info_data.get("size", 0),
            topics=repo_info_data.get("topics", []),
            default_branch=repo_info_data.get("default_branch", "main")
        )
        
        # 2. Key Files (Dict List -> FileInfo List)
        raw_files = agent_result.get("key_files", []) or agent_result.get("analysis_result", {}).get("key_files", [])
        # Agent result structure might vary, check implementation
        if not raw_files and "important_files" in agent_result:
             raw_files = agent_result["important_files"]
             
        key_files = []
        for f in raw_files:
             # Agent might return full dict or FileInfo object (if mixed)
             # But analyze_repository returns dict mainly.
             if isinstance(f, dict):
                 key_files.append(FileInfo(
                     path=f.get("path"),
                     type=f.get("type", "file"),
                     size=f.get("size", 0),
                     content=f.get("content")
                 ))
             elif hasattr(f, "path"): # It might be an object
                 key_files.append(FileInfo(
                     path=f.path,
                     type=getattr(f, "type", "file"),
                     size=getattr(f, "size", 0),
                     content=getattr(f, "content", None)
                 ))

        # 3. Tech Stack
        tech_stack = agent_result.get("tech_stack", {}) or {}
        
        # 4. Summary & Recommendations
        summary = agent_result.get("analysis_result", {}).get("summary", "") or agent_result.get("summary", "")
        if not summary and "analysis_result" in agent_result:
             summary = agent_result["analysis_result"].get("summary", "")
             
        recommendations = agent_result.get("analysis_result", {}).get("recommendations", []) or agent_result.get("recommendations", [])
        if not recommendations and "analysis_result" in agent_result:
             recommendations = agent_result["analysis_result"].get("recommendations", [])
             
        # 5. Complexity
        complexity_score = agent_result.get("complexity_score", 0.0)
        
        # AnalysisResult 객체 생성
        analysis_result = AnalysisResult(
            success=True,
            analysis_id=analysis_id,
            repo_info=repo_info,
            tech_stack=tech_stack,
            key_files=key_files,
            summary=summary,
            recommendations=recommendations,
            created_at=datetime.now(),
            smart_file_analysis=agent_result.get("smart_file_analysis")
        )
        
        print(f"[ANALYZE_SIMPLE] 고급 분석 완료 - 파일: {len(key_files)}개, 기술스택: {len(tech_stack)}개, 복잡도: {complexity_score}")
        
        # analysis_cache에 저장하여 대시보드에서 조회 가능하도록 함
        analysis_cache[analysis_id] = analysis_result
        
        print(f"[ANALYZE_SIMPLE] 분석 결과 캐시에 저장: {analysis_id}")
        print(f"[ANALYZE_SIMPLE] 캐시 크기: {len(analysis_cache)}")
        
        # 🔥 핵심 수정: 데이터베이스에도 저장하여 면접 시작 시 조회 가능하도록 함
        try:
            from app.models.repository import RepositoryAnalysis
            
            # RepositoryAnalysis 객체 생성
            db_analysis = RepositoryAnalysis(
                id=uuid.UUID(analysis_id),
                repository_url=repo_url_str,
                repository_name=f"{repo_info.owner}/{repo_info.name}",
                primary_language=repo_info.language,
                tech_stack=tech_stack,
                file_count=len(key_files),
                complexity_score=complexity_score,
                analysis_metadata={
                    "summary": summary,
                    "recommendations": recommendations,
                    "key_files_count": len(key_files),
                    "created_by": "analyze_simple_api"
                },
                status="completed",
                completed_at=datetime.now()
            )
            
            # 데이터베이스에 저장
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
            
            print(f"[ANALYZE_SIMPLE] 데이터베이스에 저장 완료: {analysis_id}")
            print(f"[ANALYZE_SIMPLE] DB 저장 상태: {db_analysis.status}")
            
        except Exception as e:
            print(f"[ANALYZE_SIMPLE] 데이터베이스 저장 오류 (캐시는 정상): {str(e)}")
            # 데이터베이스 저장 실패해도 캐시는 정상이므로 계속 진행
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYZE_SIMPLE] 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.get("/dashboard/{analysis_id}")
async def get_dashboard_data(analysis_id: str, db: Session = Depends(get_db)):
    """대시보드 데이터 조회"""
    try:
        analysis_result = analysis_cache.get(analysis_id)
        if analysis_result is None:
            from app.models.repository import RepositoryAnalysis
            analysis_db = db.query(RepositoryAnalysis).filter(
                func.cast(RepositoryAnalysis.id, String).in_([analysis_id, analysis_id.replace('-', '')])
            ).first()
            if not analysis_db:
                raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

            repo_url_parts = analysis_db.repository_url.replace("https://github.com/", "").split("/")
            owner = repo_url_parts[0] if len(repo_url_parts) > 0 else "Unknown"
            repo_name = repo_url_parts[1] if len(repo_url_parts) > 1 else "Unknown"

            repo_info = RepositoryInfo(
                name=repo_name,
                owner=owner,
                description=f"{owner}/{repo_name} repository",
                language=analysis_db.primary_language or "Unknown",
                stars=0,
                forks=0,
                size=0,
                topics=[],
                default_branch="main"
            )
            analysis_result = AnalysisResult(
                success=True,
                analysis_id=str(analysis_db.id),
                repo_info=repo_info,
                tech_stack=analysis_db.tech_stack or {},
                key_files=[],
                summary=(analysis_db.analysis_metadata or {}).get("summary", f"{repo_name} 저장소 분석 결과"),
                recommendations=(analysis_db.analysis_metadata or {}).get("recommendations", []),
                created_at=analysis_db.created_at
            )
        
        print(f"[DASHBOARD] 분석 ID {analysis_id} 조회 - 파일 수: {len(analysis_result.key_files)}개")
        
        # AnalysisResult 객체를 딕셔너리로 변환하여 반환
        return {
            "success": True,
            "analysis_id": analysis_result.analysis_id,
            "repo_info": analysis_result.repo_info.dict() if hasattr(analysis_result.repo_info, 'dict') else analysis_result.repo_info,
            "tech_stack": analysis_result.tech_stack,
            "key_files": [
                {
                    "path": f.path,
                    "type": f.type,
                    "size": f.size,
                    "content": f.content
                } for f in analysis_result.key_files
            ] if analysis_result.key_files else [],
            "summary": analysis_result.summary,
            "recommendations": analysis_result.recommendations,
            "created_at": analysis_result.created_at.isoformat() if hasattr(analysis_result.created_at, 'isoformat') else str(analysis_result.created_at)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DASHBOARD] 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대시보드 데이터 조회 실패: {str(e)}")


@router.get("/debug/cache")
async def debug_cache():
    """메모리 캐시 상태 확인 (디버깅용)"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
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
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    cache_size_before = len(analysis_cache)
    analysis_cache.clear()
    
    return {
        "message": "캐시가 성공적으로 초기화되었습니다",
        "cleared_items": cache_size_before,
        "current_cache_size": len(analysis_cache)
    }
