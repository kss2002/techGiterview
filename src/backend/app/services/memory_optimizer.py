"""
메모리 최적화 서비스
대용량 데이터 처리 시 메모리 사용량을 최적화하고 관리

주요 기능:
- 스트림 방식 파일 처리
- 메모리 압박 상황 감지 및 처리
- 가비지 컬렉션 최적화
- 캐시 크기 관리
- 메모리 사용량 모니터링
"""

import gc
import sys
import psutil
import asyncio
import weakref
from typing import Dict, Any, List, Optional, Iterator, AsyncIterator
from dataclasses import dataclass
from io import StringIO
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """메모리 통계 정보"""
    current_mb: float
    peak_mb: float
    available_mb: float
    usage_percentage: float
    gc_collections: int
    cache_size_mb: float
    
    def __post_init__(self):
        self.is_pressure = self.usage_percentage > 80.0
        self.is_critical = self.usage_percentage > 95.0


class MemoryOptimizer:
    """메모리 최적화 관리자"""
    
    def __init__(self, 
                 max_memory_mb: int = 2048,
                 streaming_enabled: bool = False,
                 chunk_size_kb: int = 64):
        self.max_memory_mb = max_memory_mb
        self.streaming_enabled = streaming_enabled
        self.chunk_size_kb = chunk_size_kb
        self.chunk_size_bytes = chunk_size_kb * 1024
        
        # 캐시 관리
        self._cache: Dict[str, Any] = {}
        self._cache_size_mb = 0
        self._max_cache_size_mb = max_memory_mb * 0.3  # 전체 메모리의 30%까지 캐시 허용
        
        # 약한 참조를 이용한 객체 추적
        self._tracked_objects = weakref.WeakSet()
        
        # 통계
        self._initial_memory = self._get_current_memory_mb()
        self._peak_memory = self._initial_memory
        self._gc_collections = 0
        
        # GC 임계값 조정 (메모리 절약을 위해 더 자주 수행)
        gc.set_threshold(700, 10, 10)
    
    def enable_streaming(self):
        """스트리밍 모드 활성화"""
        self.streaming_enabled = True
        logger.info("Memory streaming mode enabled")
    
    def disable_streaming(self):
        """스트리밍 모드 비활성화"""
        self.streaming_enabled = False
        logger.info("Memory streaming mode disabled")
    
    async def process_file_stream(self, file_path: str, processor_func) -> Dict[str, Any]:
        """스트림 방식으로 파일 처리"""
        if not self.streaming_enabled:
            # 스트리밍이 비활성화된 경우 일반 처리
            return await self._process_file_normal(file_path, processor_func)
        
        processed_chunks = 0
        total_size = 0
        results = []
        
        try:
            # Mock 파일 스트림 처리 (실제로는 파일을 청크 단위로 읽음)
            async for chunk in self._read_file_chunks(file_path):
                # 메모리 압박 상황 체크
                if self.is_memory_pressure():
                    await self._handle_memory_pressure()
                
                # 청크 처리
                chunk_result = await processor_func(chunk)
                results.append(chunk_result)
                
                processed_chunks += 1
                total_size += len(chunk) if isinstance(chunk, (str, bytes)) else self.chunk_size_bytes
                
                # 주기적으로 가비지 컬렉션 수행
                if processed_chunks % 10 == 0:
                    self._force_garbage_collection()
            
            # 결과 메모리 사용량 측정
            current_memory = self._get_current_memory_mb()
            self._update_peak_memory(current_memory)
            
            return {
                "processed_chunks": processed_chunks,
                "total_size_bytes": total_size,
                "memory_peak_mb": current_memory - self._initial_memory,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
            return {
                "processed_chunks": 0,
                "memory_peak_mb": 0,
                "error": str(e)
            }
    
    def optimize_garbage_collection(self) -> Dict[str, Any]:
        """가비지 컬렉션 최적화"""
        initial_objects = len(gc.get_objects())
        initial_memory = self._get_current_memory_mb()
        
        # 수동 가비지 컬렉션 실행
        collected_objects = gc.collect()
        self._gc_collections += 1
        
        # 순환 참조 객체 정리
        collected_cycles = 0
        for generation in range(3):
            collected_cycles += gc.collect(generation)
        
        final_memory = self._get_current_memory_mb()
        memory_freed = max(0, initial_memory - final_memory)
        
        # 약한 참조로 추적 중인 객체들 정리
        self._clean_tracked_objects()
        
        logger.info(f"GC optimization: freed {memory_freed:.2f}MB, collected {collected_objects} objects")
        
        return {
            "objects_collected": collected_objects + collected_cycles,
            "memory_freed_mb": memory_freed,
            "gc_collections": self._gc_collections,
            "tracked_objects": len(self._tracked_objects)
        }
    
    def manage_cache_size(self, max_size_mb: int = None) -> Dict[str, Any]:
        """캐시 크기 관리"""
        if max_size_mb:
            self._max_cache_size_mb = max_size_mb
        
        current_cache_size = self._calculate_cache_size()
        cleanup_triggered = False
        
        if current_cache_size > self._max_cache_size_mb:
            cleanup_triggered = True
            items_removed = self._cleanup_cache()
            
            logger.info(f"Cache cleanup: removed {items_removed} items, freed {current_cache_size - self._calculate_cache_size():.2f}MB")
        
        return {
            "current_cache_size_mb": self._calculate_cache_size(),
            "max_cache_size_mb": self._max_cache_size_mb,
            "cache_cleanup_triggered": cleanup_triggered,
            "target_cache_size_mb": min(self._calculate_cache_size(), self._max_cache_size_mb)
        }
    
    async def clear_cache(self):
        """캐시 완전 정리"""
        cache_size_before = self._calculate_cache_size()
        self._cache.clear()
        self._cache_size_mb = 0
        
        # 가비지 컬렉션으로 실제 메모리 해제
        gc.collect()
        
        logger.info(f"Cache cleared: freed {cache_size_before:.2f}MB")
    
    def get_cache_size(self) -> float:
        """현재 캐시 크기 반환 (MB)"""
        return self._calculate_cache_size()
    
    def is_memory_pressure(self) -> bool:
        """메모리 압박 상황 체크"""
        current_memory = self._get_current_memory_mb()
        memory_limit = self.max_memory_mb * 0.8  # 80% 이상 사용 시 압박 상황
        
        return current_memory > memory_limit
    
    def is_memory_critical(self) -> bool:
        """메모리 위험 상황 체크"""
        current_memory = self._get_current_memory_mb()
        memory_limit = self.max_memory_mb * 0.95  # 95% 이상 사용 시 위험 상황
        
        return current_memory > memory_limit
    
    async def enable_memory_pressure_handling(self) -> bool:
        """메모리 압박 상황 처리 활성화"""
        if self.is_memory_pressure():
            await self._handle_memory_pressure()
            return True
        return False
    
    def get_memory_stats(self) -> MemoryStats:
        """메모리 통계 반환"""
        current_memory = self._get_current_memory_mb()
        system_memory = psutil.virtual_memory()
        
        return MemoryStats(
            current_mb=current_memory,
            peak_mb=self._peak_memory,
            available_mb=system_memory.available / 1024 / 1024,
            usage_percentage=(current_memory / self.max_memory_mb) * 100,
            gc_collections=self._gc_collections,
            cache_size_mb=self._calculate_cache_size()
        )
    
    def track_object(self, obj: Any):
        """객체 추적 (약한 참조로)"""
        self._tracked_objects.add(obj)
    
    @asynccontextmanager
    async def memory_managed_context(self):
        """메모리 관리 컨텍스트"""
        initial_memory = self._get_current_memory_mb()
        try:
            yield
        finally:
            # 컨텍스트 종료 시 메모리 정리
            if self.is_memory_pressure():
                await self._handle_memory_pressure()
            
            final_memory = self._get_current_memory_mb()
            if final_memory > initial_memory + 100:  # 100MB 이상 증가 시 강제 정리
                self._force_garbage_collection()
    
    # Private methods
    
    async def _process_file_normal(self, file_path: str, processor_func) -> Dict[str, Any]:
        """일반 방식 파일 처리"""
        # Mock implementation
        await asyncio.sleep(0.1)
        return {
            "processed_chunks": 1,
            "memory_peak_mb": 10.0,
            "streaming": False
        }
    
    async def _read_file_chunks(self, file_path: str) -> AsyncIterator[str]:
        """파일을 청크 단위로 읽는 비동기 제너레이터"""
        # Mock implementation - 실제로는 파일을 청크 단위로 읽음
        total_size = 100 * 1024  # 100KB 파일 시뮬레이션
        chunks_count = (total_size + self.chunk_size_bytes - 1) // self.chunk_size_bytes
        
        for i in range(chunks_count):
            chunk_size = min(self.chunk_size_bytes, total_size - i * self.chunk_size_bytes)
            chunk_data = "x" * chunk_size  # Mock 데이터
            
            yield chunk_data
            await asyncio.sleep(0.001)  # 비동기 처리 시뮬레이션
    
    async def _handle_memory_pressure(self):
        """메모리 압박 상황 처리"""
        logger.warning("Memory pressure detected, initiating cleanup")
        
        # 1. 캐시 정리
        if self._calculate_cache_size() > 0:
            self._cleanup_cache(aggressive=True)
        
        # 2. 가비지 컬렉션 강제 실행
        self._force_garbage_collection()
        
        # 3. 추적 객체 정리
        self._clean_tracked_objects()
        
        # 4. 짧은 대기 (메모리 정리 시간 확보)
        await asyncio.sleep(0.1)
        
        # 5. 여전히 압박 상황이면 경고
        if self.is_memory_critical():
            logger.error("Memory usage still critical after cleanup")
    
    def _get_current_memory_mb(self) -> float:
        """현재 프로세스 메모리 사용량 (MB)"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _update_peak_memory(self, current_memory: float):
        """피크 메모리 업데이트"""
        if current_memory > self._peak_memory:
            self._peak_memory = current_memory
    
    def _calculate_cache_size(self) -> float:
        """캐시 크기 계산 (MB)"""
        if not self._cache:
            return 0.0
        
        # 간단한 크기 추정 (실제로는 더 정확한 계산 필요)
        total_size = 0
        for key, value in self._cache.items():
            total_size += sys.getsizeof(key) + sys.getsizeof(value)
        
        return total_size / 1024 / 1024
    
    def _cleanup_cache(self, aggressive: bool = False) -> int:
        """캐시 정리"""
        items_to_remove = []
        target_size = self._max_cache_size_mb * (0.5 if aggressive else 0.8)
        
        # 크기가 큰 순서로 정렬하여 제거
        cache_items = list(self._cache.items())
        cache_items.sort(key=lambda x: sys.getsizeof(x[1]), reverse=True)
        
        current_size = self._calculate_cache_size()
        for key, value in cache_items:
            if current_size <= target_size:
                break
            
            items_to_remove.append(key)
            current_size -= sys.getsizeof(value) / 1024 / 1024
        
        # 아이템 제거
        for key in items_to_remove:
            del self._cache[key]
        
        self._cache_size_mb = self._calculate_cache_size()
        return len(items_to_remove)
    
    def _force_garbage_collection(self):
        """강제 가비지 컬렉션"""
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
        
        self._gc_collections += 1
        
        if collected > 0:
            logger.debug(f"Forced GC collected {collected} objects")
    
    def _clean_tracked_objects(self):
        """추적 중인 객체들 정리"""
        # 약한 참조이므로 이미 삭제된 객체들은 자동으로 제거됨
        alive_objects = len(self._tracked_objects)
        logger.debug(f"Tracked objects: {alive_objects} still alive")