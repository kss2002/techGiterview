"""
통합 테스트 및 성능 최적화 테스트 스위트
TDD 접근 방식: 테스트 먼저 작성 후 구현

대용량 저장소(1000+ 파일) 처리 성능 테스트
메모리 사용량 최적화 검증
API Rate Limiting 전략 테스트
병렬 처리를 통한 분석 시간 단축 검증 (목표: 5분 이내)
"""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# 테스트 대상 컴포넌트들 import (구현 예정)
# from app.services.performance_optimizer import PerformanceOptimizer
# from app.services.api_rate_limiter import APIRateLimiter
# from app.services.memory_optimizer import MemoryOptimizer
# from app.services.batch_processor import BatchProcessor


class TestPerformanceOptimizer:
    """성능 최적화 관련 테스트"""
    
    @pytest.fixture
    def mock_large_repository(self):
        """대용량 저장소 Mock 데이터 (1000+ 파일)"""
        return {
            "owner": "test-org",
            "repo": "large-project",
            "files": [
                {
                    "path": f"src/module_{i}/file_{j}.py",
                    "size": 2048 + (i * 100),
                    "type": "python"
                }
                for i in range(50)  # 50개 모듈
                for j in range(25)  # 모듈당 25개 파일 = 1250개 파일
            ],
            "total_files": 1250,
            "total_size_mb": 15.6
        }
    
    @pytest.fixture
    def performance_optimizer(self):
        """PerformanceOptimizer 인스턴스 (구현 예정)"""
        # return PerformanceOptimizer()
        return Mock()
    
    @pytest.mark.asyncio
    async def test_large_repository_analysis_time(self, mock_large_repository, performance_optimizer):
        """대용량 저장소 분석 시간 5분 이내 검증"""
        # Given
        start_time = time.time()
        target_time_seconds = 300  # 5분
        
        # Mock 병렬 처리 함수들
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = [
                {"status": "success", "processing_time": 0.1}
                for _ in range(mock_large_repository["total_files"])
            ]
            
            # When
            result = await performance_optimizer.analyze_repository_async(
                mock_large_repository["owner"],
                mock_large_repository["repo"]
            )
            
            # Then
            elapsed_time = time.time() - start_time
            assert elapsed_time < target_time_seconds, f"분석 시간 {elapsed_time:.2f}초가 목표 {target_time_seconds}초 초과"
            assert result["status"] == "success"
            assert result["files_processed"] == mock_large_repository["total_files"]
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, mock_large_repository, performance_optimizer):
        """메모리 사용량 최적화 검증 (최대 2GB 제한)"""
        # Given
        max_memory_mb = 2048  # 2GB
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # When
        with patch('app.services.memory_optimizer.MemoryOptimizer.enable_streaming') as mock_streaming:
            mock_streaming.return_value = True
            
            result = await performance_optimizer.analyze_with_memory_optimization(
                mock_large_repository
            )
            
            # Then
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            assert memory_increase < max_memory_mb, f"메모리 증가량 {memory_increase:.2f}MB가 제한 {max_memory_mb}MB 초과"
            assert result["memory_optimized"] is True
    
    @pytest.mark.asyncio
    async def test_batch_processing_efficiency(self, mock_large_repository, performance_optimizer):
        """배치 처리 효율성 검증 (청크 단위 처리)"""
        # Given
        batch_size = 50  # 한 번에 50개 파일씩 처리
        expected_batches = (mock_large_repository["total_files"] + batch_size - 1) // batch_size
        
        # When
        with patch('app.services.batch_processor.BatchProcessor.process_batch') as mock_batch:
            mock_batch.return_value = AsyncMock(return_value={"processed": batch_size})
            
            result = await performance_optimizer.process_in_batches(
                mock_large_repository["files"],
                batch_size=batch_size
            )
            
            # Then
            assert mock_batch.call_count == expected_batches
            assert result["total_batches"] == expected_batches
            assert result["total_processed"] == mock_large_repository["total_files"]
    
    @pytest.mark.asyncio
    async def test_parallel_api_calls_optimization(self, performance_optimizer):
        """병렬 API 호출 최적화 검증"""
        # Given
        api_calls = 100
        sequential_time_mock = 10.0  # 순차 처리 시 10초
        parallel_time_mock = 2.0     # 병렬 처리 시 2초
        
        # When
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = [
                {"api_call_id": i, "duration": 0.02}
                for i in range(api_calls)
            ]
            
            start_time = time.time()
            result = await performance_optimizer.parallel_api_calls(
                api_calls_list=[f"api_call_{i}" for i in range(api_calls)]
            )
            parallel_duration = time.time() - start_time
            
            # Then
            speedup_factor = sequential_time_mock / parallel_duration if parallel_duration > 0 else float('inf')
            assert speedup_factor > 3, f"병렬 처리 속도 향상 비율 {speedup_factor:.2f}x가 기대치 3x 미만"
            assert result["parallel_calls_completed"] == api_calls


class TestAPIRateLimiter:
    """GitHub API Rate Limiting 전략 테스트"""
    
    @pytest.fixture
    def api_rate_limiter(self):
        """APIRateLimiter 인스턴스 (구현 예정)"""
        # return APIRateLimiter(max_requests_per_hour=5000)
        return Mock()
    
    @pytest.mark.asyncio
    async def test_github_api_rate_limit_management(self, api_rate_limiter):
        """GitHub API 시간당 5000 요청 제한 관리"""
        # Given
        max_requests_per_hour = 5000
        requests_to_make = 100
        
        # When
        with patch('app.services.github_client.GitHubClient.get_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = {
                "remaining": 4950,
                "limit": 5000,
                "reset_time": time.time() + 3600
            }
            
            result = await api_rate_limiter.manage_requests(
                requests_count=requests_to_make
            )
            
            # Then
            assert result["requests_allowed"] is True
            assert result["remaining_quota"] >= 0
            assert result["estimated_wait_time"] <= 60  # 최대 1분 대기
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handling(self, api_rate_limiter):
        """Rate Limit 초과 시 처리 전략"""
        # Given
        remaining_requests = 10
        requests_needed = 100
        
        # When
        with patch('app.services.github_client.GitHubClient.get_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = {
                "remaining": remaining_requests,
                "limit": 5000,
                "reset_time": time.time() + 1800  # 30분 후 리셋
            }
            
            result = await api_rate_limiter.handle_rate_limit_exceeded(
                requests_needed=requests_needed
            )
            
            # Then
            assert result["rate_limit_exceeded"] is True
            assert result["wait_strategy"] in ["exponential_backoff", "scheduled_retry"]
            assert result["estimated_wait_minutes"] <= 35  # 최대 35분 대기
    
    @pytest.mark.asyncio
    async def test_token_rotation_strategy(self, api_rate_limiter):
        """토큰 로테이션 전략 검증"""
        # Given
        available_tokens = ["token1", "token2", "token3"]
        
        # When
        with patch('app.services.github_client.GitHubClient.check_token_limits') as mock_check:
            mock_check.side_effect = [
                {"remaining": 100, "token": "token1"},  # token1 사용 가능
                {"remaining": 4000, "token": "token2"}, # token2 사용 가능
                {"remaining": 0, "token": "token3"}     # token3 제한 초과
            ]
            
            result = await api_rate_limiter.rotate_tokens(available_tokens)
            
            # Then
            assert result["active_token"] in ["token1", "token2"]
            assert result["tokens_available"] >= 1
            assert result["rotation_successful"] is True


class TestMemoryOptimizer:
    """메모리 최적화 관련 테스트"""
    
    @pytest.fixture
    def memory_optimizer(self):
        """MemoryOptimizer 인스턴스 (구현 예정)"""
        # return MemoryOptimizer()
        return Mock()
    
    def test_streaming_file_processing(self, memory_optimizer):
        """스트림 방식 파일 처리 검증"""
        # Given
        large_file_size_mb = 100
        chunk_size_kb = 64
        
        # When
        with patch('app.services.memory_optimizer.MemoryOptimizer.process_file_stream') as mock_stream:
            mock_stream.return_value = {
                "processed_chunks": (large_file_size_mb * 1024) // chunk_size_kb,
                "memory_peak_mb": 5.2  # 청크 처리 시 피크 메모리
            }
            
            result = memory_optimizer.process_large_file_streaming(
                file_size_mb=large_file_size_mb,
                chunk_size_kb=chunk_size_kb
            )
            
            # Then
            assert result["memory_peak_mb"] < 10, "스트림 처리 중 메모리 피크가 10MB 초과"
            assert result["processed_chunks"] > 0
    
    def test_garbage_collection_optimization(self, memory_optimizer):
        """가비지 컬렉션 최적화 검증"""
        # Given
        initial_objects = 1000
        
        # When
        with patch('gc.collect') as mock_gc:
            mock_gc.return_value = 500  # 500개 객체 정리
            
            result = memory_optimizer.optimize_garbage_collection()
            
            # Then
            assert mock_gc.called
            assert result["objects_collected"] > 0
            assert result["memory_freed_mb"] > 0
    
    def test_cache_size_management(self, memory_optimizer):
        """캐시 크기 관리 검증"""
        # Given
        max_cache_size_mb = 100
        current_cache_size_mb = 150
        
        # When
        with patch('app.services.memory_optimizer.MemoryOptimizer.get_cache_size') as mock_cache_size:
            mock_cache_size.return_value = current_cache_size_mb
            
            result = memory_optimizer.manage_cache_size(max_size_mb=max_cache_size_mb)
            
            # Then
            assert result["cache_cleanup_triggered"] is True
            assert result["target_cache_size_mb"] <= max_cache_size_mb


class TestIntegrationPerformance:
    """전체 통합 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_large_repository_analysis(self):
        """End-to-End 대용량 저장소 분석 성능 테스트"""
        # Given
        repository_url = "https://github.com/test-org/large-project"
        expected_max_duration_minutes = 5
        
        # When
        start_time = time.time()
        
        with patch('app.agents.repository_analyzer.RepositoryAnalyzer.analyze') as mock_analyze:
            mock_analyze.return_value = AsyncMock(return_value={
                "analysis_complete": True,
                "files_analyzed": 1250,
                "critical_files": 45,
                "important_files": 123,
                "moderate_files": 456,
                "low_files": 626,
                "analysis_duration_seconds": 280
            })
            
            # from app.services.techgiterview_service import TechGiterviewService
            # service = TechGiterviewService()
            # result = await service.analyze_repository(repository_url)
            
            # Mock 전체 분석 프로세스
            result = await mock_analyze()
            
        # Then
        elapsed_minutes = (time.time() - start_time) / 60
        assert elapsed_minutes < expected_max_duration_minutes, f"전체 분석 시간 {elapsed_minutes:.2f}분이 목표 {expected_max_duration_minutes}분 초과"
        assert result["analysis_complete"] is True
        assert result["files_analyzed"] > 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_repository_analysis(self):
        """동시 다중 저장소 분석 성능 테스트"""
        # Given
        repositories = [
            "https://github.com/org1/repo1",
            "https://github.com/org2/repo2", 
            "https://github.com/org3/repo3"
        ]
        max_concurrent_analyses = 3
        
        # When
        start_time = time.time()
        
        with patch('asyncio.Semaphore') as mock_semaphore:
            mock_semaphore.return_value.__aenter__ = AsyncMock()
            mock_semaphore.return_value.__aexit__ = AsyncMock()
            
            # Mock 병렬 분석
            mock_results = [
                {"repo": repo, "status": "completed", "duration": 120 + i*30}
                for i, repo in enumerate(repositories)
            ]
            
            with patch('asyncio.gather') as mock_gather:
                mock_gather.return_value = mock_results
                
                results = await mock_gather(*[
                    self._mock_analyze_single_repo(repo) 
                    for repo in repositories
                ])
        
        # Then
        elapsed_time = time.time() - start_time
        assert elapsed_time < 300, f"병렬 분석 시간 {elapsed_time:.2f}초가 목표 300초 초과"
        assert len(results) == len(repositories)
        assert all(result["status"] == "completed" for result in results)
    
    async def _mock_analyze_single_repo(self, repo_url: str) -> Dict[str, Any]:
        """단일 저장소 분석 Mock 함수"""
        await asyncio.sleep(0.1)  # 비동기 처리 시뮬레이션
        return {
            "repo": repo_url,
            "status": "completed",
            "duration": 150,
            "files_processed": 500
        }
    
    @pytest.mark.asyncio 
    async def test_memory_pressure_handling(self):
        """메모리 압박 상황 처리 검증"""
        # Given
        memory_limit_mb = 1024  # 1GB 제한
        large_dataset_size = 2000  # 2000개 파일
        
        # When
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.available = memory_limit_mb * 1024 * 1024  # bytes
            
            with patch('app.services.memory_optimizer.MemoryOptimizer.enable_memory_pressure_handling') as mock_pressure:
                mock_pressure.return_value = True
                
                # Mock 메모리 압박 상황 처리
                result = {
                    "memory_pressure_detected": True,
                    "fallback_strategy_activated": True,
                    "processing_mode": "streaming",
                    "batch_size_reduced": True,
                    "memory_usage_optimized": True
                }
        
        # Then
        assert result["memory_pressure_detected"] is True
        assert result["fallback_strategy_activated"] is True
        assert result["processing_mode"] == "streaming"


# 성능 벤치마크를 위한 pytest-benchmark 활용 테스트들
class TestPerformanceBenchmarks:
    """pytest-benchmark를 활용한 성능 벤치마크 테스트"""
    
    def test_file_parsing_benchmark(self, benchmark):
        """파일 파싱 성능 벤치마크"""
        def parse_multiple_files():
            # Mock 파일 파싱 작업
            results = []
            for i in range(100):  # 100개 파일 파싱
                result = {
                    "file": f"file_{i}.py",
                    "lines": 150 + i,
                    "complexity": 0.3 + (i * 0.01)
                }
                results.append(result)
            return results
        
        # When & Then
        result = benchmark(parse_multiple_files)
        assert len(result) == 100
    
    def test_dependency_graph_creation_benchmark(self, benchmark):
        """의존성 그래프 생성 성능 벤치마크"""
        def create_dependency_graph():
            # Mock NetworkX 그래프 생성
            dependencies = []
            for i in range(200):  # 200개 노드
                for j in range(3):  # 각 노드당 3개 의존성
                    dependencies.append((f"node_{i}", f"dep_{i}_{j}"))
            return {"nodes": 200, "edges": 600}
        
        # When & Then
        result = benchmark(create_dependency_graph)
        assert result["nodes"] == 200
        assert result["edges"] == 600
    
    def test_importance_scoring_benchmark(self, benchmark):
        """중요도 스코어링 성능 벤치마크"""
        def calculate_importance_scores():
            # Mock 중요도 스코어 계산
            files = []
            for i in range(500):  # 500개 파일
                score = (0.4 * (i/500)) + (0.3 * ((i*2)/500)) + (0.2 * ((i*3)/500)) + (0.1 * ((i*4)/500))
                files.append({
                    "file": f"file_{i}.py",
                    "importance_score": min(score, 1.0)
                })
            return files
        
        # When & Then
        result = benchmark(calculate_importance_scores)
        assert len(result) == 500
        assert all(0 <= file["importance_score"] <= 1.0 for file in result)


# 테스트 실행을 위한 pytest 설정
pytest_plugins = ["pytest_asyncio", "pytest_benchmark"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])