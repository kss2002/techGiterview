"""
성능 최적화 서비스
대용량 저장소 분석을 위한 성능 최적화 기능 제공

주요 기능:
- 병렬 처리를 통한 분석 시간 단축
- 메모리 사용량 최적화
- 배치 처리 최적화
- API 호출 최적화
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc
from dataclasses import dataclass
from app.services.memory_optimizer import MemoryOptimizer
from app.services.batch_processor import BatchProcessor
from app.services.api_rate_limiter import APIRateLimiter


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    start_time: float
    end_time: float
    memory_peak_mb: float
    files_processed: int
    api_calls_made: int
    cache_hits: int
    cache_misses: int
    
    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def throughput_files_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.files_processed / self.duration_seconds
        return 0.0


class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self, 
                 max_workers: int = 10,
                 max_memory_mb: int = 2048,
                 batch_size: int = 50):
        self.max_workers = max_workers
        self.max_memory_mb = max_memory_mb
        self.batch_size = batch_size
        
        self.memory_optimizer = MemoryOptimizer()
        self.batch_processor = BatchProcessor(batch_size=batch_size)
        self.api_rate_limiter = APIRateLimiter()
        
        self._metrics = None
        self._semaphore = asyncio.Semaphore(max_workers)
    
    async def analyze_repository_async(self, owner: str, repo: str) -> Dict[str, Any]:
        """비동기 저장소 분석 (최적화 적용)"""
        start_time = time.time()
        initial_memory = self._get_current_memory_mb()
        
        try:
            # 1. 저장소 메타정보 수집
            meta_info = await self._fetch_repository_metadata(owner, repo)
            
            # 2. 파일 목록 수집 (배치 처리)
            files = await self._fetch_files_in_batches(owner, repo, meta_info.get('file_count', 0))
            
            # 3. 병렬 파일 분석
            analysis_results = await self._analyze_files_parallel(files)
            
            # 4. 결과 집계
            final_result = await self._aggregate_results(analysis_results)
            
            # 성능 메트릭 계산
            end_time = time.time()
            peak_memory = self._get_current_memory_mb()
            
            self._metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                memory_peak_mb=max(peak_memory - initial_memory, 0),
                files_processed=len(files),
                api_calls_made=meta_info.get('api_calls', 0),
                cache_hits=0,  # TODO: 실제 캐시 히트 수 측정
                cache_misses=0  # TODO: 실제 캐시 미스 수 측정
            )
            
            return {
                "status": "success",
                "files_processed": len(files),
                "duration_seconds": self._metrics.duration_seconds,
                "throughput_fps": self._metrics.throughput_files_per_second,
                "memory_peak_mb": self._metrics.memory_peak_mb,
                "results": final_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "files_processed": 0
            }
    
    async def analyze_with_memory_optimization(self, repository_data: Dict[str, Any]) -> Dict[str, Any]:
        """메모리 최적화를 적용한 분석"""
        # 스트리밍 모드 활성화
        self.memory_optimizer.enable_streaming()
        
        try:
            files = repository_data.get("files", [])
            
            # 메모리 사용량 모니터링하면서 처리
            results = []
            for batch in self.batch_processor.create_batches(files, self.batch_size):
                # 메모리 압박 상황 체크
                if self._is_memory_pressure():
                    await self._handle_memory_pressure()
                
                # 배치 처리
                batch_result = await self._process_batch_with_memory_limit(batch)
                results.extend(batch_result)
                
                # 가비지 컬렉션 수행
                gc.collect()
            
            return {
                "status": "success",
                "memory_optimized": True,
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "memory_optimized": False,
                "error": str(e)
            }
    
    async def process_in_batches(self, files: List[Dict[str, Any]], batch_size: int = None) -> Dict[str, Any]:
        """배치 단위로 파일 처리"""
        if batch_size is None:
            batch_size = self.batch_size
        
        batches = self.batch_processor.create_batches(files, batch_size)
        total_processed = 0
        batch_count = 0
        
        for batch in batches:
            batch_result = await self.batch_processor.process_batch(batch)
            total_processed += batch_result.get("processed", 0)
            batch_count += 1
        
        return {
            "total_batches": batch_count,
            "total_processed": total_processed,
            "batch_size": batch_size
        }
    
    async def parallel_api_calls(self, api_calls_list: List[str]) -> Dict[str, Any]:
        """병렬 API 호출 최적화"""
        async def make_api_call(call_id: str) -> Dict[str, Any]:
            async with self._semaphore:
                # Rate limiting 적용
                await self.api_rate_limiter.acquire()
                
                # Mock API 호출 (실제로는 GitHub API 호출)
                await asyncio.sleep(0.02)  # 20ms 시뮬레이션
                
                return {
                    "api_call_id": call_id,
                    "duration": 0.02,
                    "status": "success"
                }
        
        # 병렬 실행
        results = await asyncio.gather(*[
            make_api_call(call_id) 
            for call_id in api_calls_list
        ])
        
        return {
            "parallel_calls_completed": len(results),
            "results": results
        }
    
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """성능 메트릭 반환"""
        return self._metrics
    
    # Private methods
    
    async def _fetch_repository_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """저장소 메타정보 수집"""
        # Mock implementation
        await asyncio.sleep(0.1)
        return {
            "owner": owner,
            "repo": repo,
            "file_count": 1250,
            "api_calls": 5
        }
    
    async def _fetch_files_in_batches(self, owner: str, repo: str, file_count: int) -> List[Dict[str, Any]]:
        """배치 단위로 파일 목록 수집"""
        files = []
        batch_size = 100  # GitHub API 한 번에 100개씩
        
        for i in range(0, file_count, batch_size):
            batch_files = await self._fetch_file_batch(owner, repo, i, min(batch_size, file_count - i))
            files.extend(batch_files)
        
        return files
    
    async def _fetch_file_batch(self, owner: str, repo: str, offset: int, limit: int) -> List[Dict[str, Any]]:
        """파일 배치 수집"""
        # Mock implementation
        await asyncio.sleep(0.05)
        return [
            {
                "path": f"src/file_{offset + i}.py",
                "size": 1024 + i * 10,
                "type": "python"
            }
            for i in range(limit)
        ]
    
    async def _analyze_files_parallel(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """병렬 파일 분석"""
        async def analyze_single_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
            async with self._semaphore:
                # 파일 분석 시뮬레이션
                await asyncio.sleep(0.01)
                return {
                    "file": file_info["path"],
                    "importance_score": min(0.1 + (hash(file_info["path"]) % 90) / 100, 1.0),
                    "analyzed": True
                }
        
        # 병렬 실행
        return await asyncio.gather(*[
            analyze_single_file(file_info)
            for file_info in files
        ])
    
    async def _aggregate_results(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """결과 집계"""
        total_files = len(analysis_results)
        successful_analyses = len([r for r in analysis_results if r.get("analyzed", False)])
        
        # 중요도별 분류
        critical_files = [r for r in analysis_results if r.get("importance_score", 0) >= 0.8]
        important_files = [r for r in analysis_results if 0.6 <= r.get("importance_score", 0) < 0.8]
        moderate_files = [r for r in analysis_results if 0.4 <= r.get("importance_score", 0) < 0.6]
        low_files = [r for r in analysis_results if r.get("importance_score", 0) < 0.4]
        
        return {
            "total_files": total_files,
            "successful_analyses": successful_analyses,
            "critical_files": len(critical_files),
            "important_files": len(important_files),
            "moderate_files": len(moderate_files),
            "low_files": len(low_files),
            "analysis_success_rate": successful_analyses / total_files if total_files > 0 else 0
        }
    
    def _get_current_memory_mb(self) -> float:
        """현재 메모리 사용량 (MB)"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _is_memory_pressure(self) -> bool:
        """메모리 압박 상황 체크"""
        current_memory = self._get_current_memory_mb()
        return current_memory > (self.max_memory_mb * 0.8)  # 80% 이상 사용 시 압박 상황
    
    async def _handle_memory_pressure(self):
        """메모리 압박 상황 처리"""
        # 가비지 컬렉션 강제 실행
        gc.collect()
        
        # 캐시 정리
        await self.memory_optimizer.clear_cache()
        
        # 잠시 대기 (메모리 정리 시간 확보)
        await asyncio.sleep(0.1)
    
    async def _process_batch_with_memory_limit(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """메모리 제한 하에서 배치 처리"""
        results = []
        for item in batch:
            # 메모리 사용량 체크
            if self._is_memory_pressure():
                await self._handle_memory_pressure()
            
            # 아이템 처리
            result = await self._process_single_item(item)
            results.append(result)
        
        return results
    
    async def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """단일 아이템 처리"""
        # Mock processing
        await asyncio.sleep(0.001)
        return {
            "item": item.get("path", "unknown"),
            "processed": True,
            "timestamp": time.time()
        }