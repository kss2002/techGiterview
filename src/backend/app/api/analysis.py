"""
Advanced Repository Analysis API Router

고도화된 저장소 분석 기능을 제공하는 API 엔드포인트
"""

from typing import Dict, List, Any, Optional
import asyncio
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.agents.repository_analyzer import RepositoryAnalyzer
from app.services.advanced_file_analyzer import AdvancedFileAnalyzer
from app.services.flow_graph_analyzer import FlowGraphAnalyzer
from app.services.flow_analysis_service import FlowAnalysisService

router = APIRouter()

# 분석 상태 캐시 (실제로는 Redis나 DB 사용)
analysis_cache = {}


class RepositoryAnalysisRequest(BaseModel):
    """저장소 분석 요청"""
    repo_url: str
    analysis_depth: str = "standard"  # basic, standard, deep
    use_advanced: bool = True
    max_files: int = 15


class AnalysisStatusResponse(BaseModel):
    """분석 상태 응답"""
    analysis_id: str
    status: str  # pending, analyzing, completed, failed
    progress: int  # 0-100
    current_step: str
    estimated_duration: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AdvancedAnalysisRequest(BaseModel):
    """고도화된 분석 요청"""
    repo_url: str
    max_files: int = 20
    include_dashboard: bool = True


@router.post("/repository/analyze", response_model=Dict[str, Any])
async def analyze_repository(
    request: RepositoryAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """GitHub 저장소 종합 분석"""
    
    try:
        analysis_id = str(uuid.uuid4())
        
        # 분석 상태 초기화
        analysis_cache[analysis_id] = {
            "status": "pending",
            "progress": 0,
            "current_step": "초기화 중",
            "start_time": datetime.now(),
            "repository_url": request.repo_url,
            "use_advanced": request.use_advanced
        }
        
        # 백그라운드에서 분석 실행
        background_tasks.add_task(
            run_analysis_task,
            analysis_id,
            request.repo_url,
            request.analysis_depth,
            request.use_advanced
        )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "message": "분석이 시작되었습니다",
            "estimated_duration": 120 if request.use_advanced else 60  # 초
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """분석 진행 상황 조회"""
    
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다")
    
    cache_data = analysis_cache[analysis_id]
    
    # 경과 시간 계산
    elapsed = (datetime.now() - cache_data["start_time"]).seconds
    estimated_duration = cache_data.get("estimated_duration")
    
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=cache_data["status"],
        progress=cache_data["progress"],
        current_step=cache_data["current_step"],
        estimated_duration=estimated_duration,
        result=cache_data.get("result"),
        error=cache_data.get("error")
    )


@router.get("/analysis/{analysis_id}/graph")
async def get_analysis_graph(analysis_id: str):
    """분석 결과에 대한 코드 그래프 데이터 조회"""
    
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다")
    
    cache_data = analysis_cache[analysis_id]
    
    if cache_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 완료되지 않았습니다")
        
    result = cache_data.get("result", {})
    
    # key_files에서 파일 내용 및 메타데이터 추출
    file_map = {}
    metadata_map = {}
    
    if "key_files" in result:
        for f in result["key_files"]:
            path = f.get("path")
            if f.get("content"):
                file_map[path] = f.get("content")
            
            # Store metadata for graph injection
            metadata_map[path] = {
                "importance_score": f.get("importance_score", 0),
                "selection_reason": f.get("selection_reason", ""),
                "importance_level": f.get("importance", "low")
            }
                
    if not file_map:
        return {"nodes": [], "links": []}
        
    # 그래프 생성
    try:
        analyzer = FlowGraphAnalyzer()
        
        # Extract repo name for internal prefix detection
        repo_name = None
        if "repo_info" in result:
             repo_name = result["repo_info"].get("name")
        
        graph = analyzer.build_graph(file_map, repo_name=repo_name)
        
        # Frontend 호환 포맷으로 변환
        nodes = []
        links = []
        
        for node, attrs in graph.nodes(data=True):
            node_type = attrs.get("type", "unknown")
            # NodeType enum 처리
            if hasattr(node_type, "value"):
                node_type = node_type.value
            
            # Get metadata
            meta = metadata_map.get(node, {})
            score = meta.get("importance_score", 0)
            
            # Fallback to visual density if score is missing (e.g. for implicit nodes)
            val = score if score > 0 else attrs.get("density", 0.1)
                
            nodes.append({
                "id": node,
                "name": node.split('/')[-1],
                "val": val, # Used for visual importance
                "type": node_type,
                "density": attrs.get("density", 0),
                "reason": meta.get("selection_reason", ""),
                "importance": meta.get("importance_level", "low")
            })
            
        for u, v, attrs in graph.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "type": attrs.get("type", "dependency")
            })
            
        return {"nodes": nodes, "links": links}
        
    except Exception as e:
        print(f"[GRAPH_API] Error building graph: {e}")
        return {"nodes": [], "links": []}


@router.get("/analysis/{analysis_id}/result")
async def get_analysis_result(analysis_id: str):
    """분석 완료 결과 조회"""
    
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다")
    
    cache_data = analysis_cache[analysis_id]
    
    if cache_data["status"] != "completed":
        return {
            "success": False,
            "message": f"분석이 아직 완료되지 않았습니다. 현재 상태: {cache_data['status']}"
        }
    
    return {
        "success": True,
        "analysis_id": analysis_id,
        "result": cache_data.get("result"),
        "analysis_duration": (cache_data.get("end_time", datetime.now()) - cache_data["start_time"]).seconds
    }


@router.post("/repository/analyze-advanced")
async def analyze_repository_advanced(request: AdvancedAnalysisRequest):
    """고도화된 저장소 분석 (실시간)"""
    
    try:
        analyzer = AdvancedFileAnalyzer()
        
        # 고도화된 분석 실행
        result = await analyzer.analyze_repository_advanced(request.repo_url)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "분석 실패"))
        
        # 응답 데이터 구성
        response_data = {
            "success": True,
            "repository_url": request.repo_url,
            "analysis_result": result,
            "important_files": result.get("important_files", []),
            "file_metrics_summary": {
                "total_files": len(result.get("file_metrics", {})),
                "analyzed_files": result.get("analysis_summary", {}).get("analyzed_files", 0),
                "high_risk_files": result.get("analysis_summary", {}).get("high_risk_files", 0)
            }
        }
        
        # 대시보드 데이터 포함 (요청시)
        if request.include_dashboard:
            response_data["dashboard_data"] = result.get("dashboard_data")
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/stats/{owner}/{repo}")
async def get_repository_stats(owner: str, repo: str):
    """저장소 통계 정보 조회"""
    
    try:
        from app.services.github_client import GitHubClient
        
        repo_url = f"https://github.com/{owner}/{repo}"
        
        async with GitHubClient() as client:
            stats = await client.get_repository_stats(repo_url)
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "success": True,
            "repository_url": repo_url,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/compare")
async def compare_repositories(repository_urls: List[str]):
    """여러 저장소 비교 분석"""
    
    if len(repository_urls) > 5:
        raise HTTPException(status_code=400, detail="최대 5개의 저장소만 비교 가능합니다")
    
    try:
        analyzer = RepositoryAnalyzer()
        results = []
        
        # 각 저장소 병렬 분석
        tasks = [
            analyzer.analyze_repository(url, use_advanced=True)
            for url in repository_urls
        ]
        
        analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(analysis_results):
            if isinstance(result, Exception):
                results.append({
                    "repository_url": repository_urls[i],
                    "success": False,
                    "error": str(result)
                })
            else:
                results.append({
                    "repository_url": repository_urls[i],
                    "success": True,
                    "analysis": result
                })
        
        # 비교 메트릭 계산
        comparison_metrics = _calculate_comparison_metrics(results)
        
        return {
            "success": True,
            "repositories": results,
            "comparison": comparison_metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """분석 결과 삭제"""
    
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다")
    
    del analysis_cache[analysis_id]
    
    return {
        "success": True,
        "message": "분석 결과가 삭제되었습니다"
    }


@router.get("/analysis/cache/status")
async def get_cache_status():
    """분석 캐시 상태 조회"""
    
    cache_info = {}
    for analysis_id, cache_data in analysis_cache.items():
        cache_info[analysis_id] = {
            "status": cache_data["status"],
            "progress": cache_data["progress"],
            "repository_url": cache_data.get("repository_url"),
            "start_time": cache_data["start_time"].isoformat(),
            "use_advanced": cache_data.get("use_advanced", False)
        }
    
    return {
        "success": True,
        "total_analyses": len(analysis_cache),
        "cache_details": cache_info
    }


async def run_analysis_task(
    analysis_id: str,
    repository_url: str,
    analysis_depth: str,
    use_advanced: bool
):
    """백그라운드 분석 태스크"""
    
    try:
        # 분석 상태 업데이트
        analysis_cache[analysis_id].update({
            "status": "analyzing",
            "progress": 10,
            "current_step": "저장소 정보 수집 중"
        })
        
        analyzer = RepositoryAnalyzer()
        
        # 단계별 진행 상황 업데이트
        analysis_cache[analysis_id].update({
            "progress": 30,
            "current_step": "파일 구조 분석 중"
        })
        
        # 실제 분석 실행
        result = await analyzer.analyze_repository(repository_url, use_advanced=use_advanced)
        
        analysis_cache[analysis_id].update({
            "progress": 80,
            "current_step": "결과 종합 중"
        })
        
        if result["success"]:
            # 성공적 완료
            analysis_cache[analysis_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "분석 완료",
                "result": result,
                "end_time": datetime.now()
            })
        else:
            # 분석 실패
            analysis_cache[analysis_id].update({
                "status": "failed",
                "progress": 0,
                "current_step": "분석 실패",
                "error": result.get("error", "알 수 없는 오류"),
                "end_time": datetime.now()
            })
            
    except Exception as e:
        # 예외 발생
        analysis_cache[analysis_id].update({
            "status": "failed",
            "progress": 0,
            "current_step": "분석 오류",
            "error": str(e),
            "end_time": datetime.now()
        })


def _calculate_comparison_metrics(results: List[Dict]) -> Dict[str, Any]:
    """저장소 비교 메트릭 계산"""
    
    successful_results = [r for r in results if r["success"]]
    
    if not successful_results:
        return {"error": "비교할 수 있는 유효한 분석 결과가 없습니다"}
    
    # 복잡도 점수 비교
    complexity_scores = [
        r["analysis"].get("complexity_score", 0)
        for r in successful_results
    ]
    
    # 파일 개수 비교
    file_counts = [
        r["analysis"].get("file_count", 0)
        for r in successful_results
    ]
    
    # 기술 스택 다양성 비교
    tech_diversities = [
        len(r["analysis"].get("tech_stack", {}))
        for r in successful_results
    ]
    
    return {
        "complexity_comparison": {
            "average": round(sum(complexity_scores) / len(complexity_scores), 2),
            "max": max(complexity_scores),
            "min": min(complexity_scores),
            "scores": complexity_scores
        },
        "size_comparison": {
            "average_files": round(sum(file_counts) / len(file_counts)),
            "max_files": max(file_counts),
            "min_files": min(file_counts),
            "file_counts": file_counts
        },
        "tech_diversity_comparison": {
            "average": round(sum(tech_diversities) / len(tech_diversities), 2),
            "max": max(tech_diversities),
            "min": min(tech_diversities),
            "diversities": tech_diversities
        },
        "total_repositories": len(successful_results),
        "failed_analyses": len(results) - len(successful_results)
    }


# 추가 유틸리티 엔드포인트들

@router.post("/analysis/bulk")
async def bulk_analyze_repositories(
    repository_urls: List[str],
    background_tasks: BackgroundTasks,
    use_advanced: bool = True
):
    """여러 저장소 일괄 분석"""
    
    if len(repository_urls) > 10:
        raise HTTPException(status_code=400, detail="최대 10개의 저장소만 일괄 분석 가능합니다")
    
    bulk_id = str(uuid.uuid4())
    analysis_ids = []
    
    for repo_url in repository_urls:
        analysis_id = str(uuid.uuid4())
        analysis_ids.append(analysis_id)
        
        # 각 저장소 분석 태스크 추가
        analysis_cache[analysis_id] = {
            "status": "pending",
            "progress": 0,
            "current_step": "대기 중",
            "start_time": datetime.now(),
            "repository_url": repo_url,
            "use_advanced": use_advanced,
            "bulk_id": bulk_id
        }
        
        background_tasks.add_task(
            run_analysis_task,
            analysis_id,
            repo_url,
            "standard",
            use_advanced
        )
    
    return {
        "success": True,
        "bulk_id": bulk_id,
        "analysis_ids": analysis_ids,
        "total_repositories": len(repository_urls),
        "message": "일괄 분석이 시작되었습니다"
    }


@router.get("/analysis/bulk/{bulk_id}/status")
async def get_bulk_analysis_status(bulk_id: str):
    """일괄 분석 상태 조회"""
    
    # bulk_id로 관련 분석들 찾기
    related_analyses = {
        aid: data for aid, data in analysis_cache.items()
        if data.get("bulk_id") == bulk_id
    }
    
    if not related_analyses:
        raise HTTPException(status_code=404, detail="일괄 분석 ID를 찾을 수 없습니다")
    
    # 전체 진행 상황 계산
    total_progress = sum(data["progress"] for data in related_analyses.values())
    average_progress = total_progress // len(related_analyses)
    
    completed_count = sum(1 for data in related_analyses.values() if data["status"] == "completed")
    failed_count = sum(1 for data in related_analyses.values() if data["status"] == "failed")
    
    overall_status = "completed" if completed_count == len(related_analyses) else "analyzing"
    if failed_count > 0 and completed_count + failed_count == len(related_analyses):
        overall_status = "partially_completed"
    
    return {
        "success": True,
        "bulk_id": bulk_id,
        "overall_status": overall_status,
        "overall_progress": average_progress,
        "total_repositories": len(related_analyses),
        "completed": completed_count,
        "failed": failed_count,
        "individual_statuses": {
            aid: {
                "status": data["status"],
                "progress": data["progress"],
                "repository_url": data["repository_url"]
            }
            for aid, data in related_analyses.items()
        }
    }