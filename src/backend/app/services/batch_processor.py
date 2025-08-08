"""
배치 처리 서비스
대용량 데이터를 효율적으로 청크 단위로 처리

주요 기능:
- 데이터를 배치 단위로 분할
- 병렬 배치 처리
- 배치 처리 결과 집계
- 동적 배치 크기 조정
- 배치 처리 진행 상황 모니터링
"""

import asyncio
import time
import math
from typing import List, Dict, Any, Iterator, Optional, Callable, AsyncIterator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class BatchMetrics:
    """배치 처리 메트릭"""
    total_items: int
    batch_size: int
    total_batches: int
    processed_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    @property
    def progress_percentage(self) -> float:
        if self.total_batches == 0:
            return 0.0
        return (self.processed_batches / self.total_batches) * 100
    
    @property
    def success_rate(self) -> float:
        if self.processed_batches == 0:
            return 0.0
        return (self.successful_batches / self.processed_batches) * 100
    
    @property
    def duration_seconds(self) -> float:
        end_time = self.end_time or time.time()
        return max(0, end_time - self.start_time)
    
    @property
    def throughput_items_per_second(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        processed_items = self.successful_batches * self.batch_size
        return processed_items / self.duration_seconds


@dataclass
class BatchResult:
    """배치 처리 결과"""
    batch_id: int
    items_processed: int
    success: bool
    processing_time: float
    error_message: Optional[str] = None
    results: List[Any] = field(default_factory=list)


class BatchProcessor:
    """배치 처리 관리자"""
    
    def __init__(self, 
                 batch_size: int = 50,
                 max_concurrent_batches: int = 5,
                 adaptive_sizing: bool = True):
        self.initial_batch_size = batch_size
        self.current_batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.adaptive_sizing = adaptive_sizing
        
        # 배치 처리 통계
        self.total_batches_processed = 0
        self.total_items_processed = 0
        self.average_batch_time = 0.0
        self.batch_time_history = []
        
        # 동시 실행 제어
        self._semaphore = asyncio.Semaphore(max_concurrent_batches)
        self._thread_pool = ThreadPoolExecutor(max_workers=max_concurrent_batches)
    
    def create_batches(self, items: List[Any], batch_size: int = None) -> Iterator[List[Any]]:
        """아이템 리스트를 배치로 분할"""
        if batch_size is None:
            batch_size = self.current_batch_size
        
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    async def process_batch(self, batch: List[Any]) -> Dict[str, Any]:
        """단일 배치 처리"""
        start_time = time.time()
        batch_id = id(batch)  # 간단한 배치 ID
        
        try:
            async with self._semaphore:
                # Mock 배치 처리 (실제로는 각 아이템을 처리)
                processed_items = []
                for item in batch:
                    processed_item = await self._process_single_item(item)
                    processed_items.append(processed_item)
                
                processing_time = time.time() - start_time
                
                # 통계 업데이트
                self._update_batch_statistics(processing_time)
                
                return {
                    "batch_id": batch_id,
                    "processed": len(processed_items),
                    "success": True,
                    "processing_time": processing_time,
                    "results": processed_items
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Batch {batch_id} processing failed: {e}")
            
            return {
                "batch_id": batch_id,
                "processed": 0,
                "success": False,
                "processing_time": processing_time,
                "error": str(e)
            }
    
    async def process_all_batches(self, 
                                  items: List[Any], 
                                  processor_func: Optional[Callable] = None,
                                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """모든 배치를 병렬로 처리"""
        if not items:
            return {
                "total_batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "total_items_processed": 0,
                "results": []
            }
        
        # 배치 생성
        batches = list(self.create_batches(items))
        
        # 메트릭 초기화
        metrics = BatchMetrics(
            total_items=len(items),
            batch_size=self.current_batch_size,
            total_batches=len(batches)
        )
        
        # 병렬 배치 처리
        batch_results = []
        successful_batches = 0
        failed_batches = 0
        
        async def process_single_batch(batch_index: int, batch: List[Any]) -> BatchResult:
            start_time = time.time()
            
            try:
                if processor_func:
                    # 커스텀 프로세서 함수 사용
                    result = await processor_func(batch)
                else:
                    # 기본 배치 처리
                    result = await self.process_batch(batch)
                
                processing_time = time.time() - start_time
                
                return BatchResult(
                    batch_id=batch_index,
                    items_processed=len(batch),
                    success=result.get("success", True),
                    processing_time=processing_time,
                    results=result.get("results", [])
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Batch {batch_index} failed: {e}")
                
                return BatchResult(
                    batch_id=batch_index,
                    items_processed=0,
                    success=False,
                    processing_time=processing_time,
                    error_message=str(e)
                )
        
        # 배치들을 병렬로 처리
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_with_semaphore(batch_index: int, batch: List[Any]) -> BatchResult:
            async with semaphore:
                result = await process_single_batch(batch_index, batch)
                
                # 진행 상황 업데이트
                metrics.processed_batches += 1
                if result.success:
                    metrics.successful_batches += 1
                else:
                    metrics.failed_batches += 1
                
                # 진행 상황 콜백 호출
                if progress_callback:
                    await progress_callback(metrics)
                
                # 적응형 배치 크기 조정
                if self.adaptive_sizing:
                    self._adjust_batch_size(result.processing_time)
                
                return result
        
        # 모든 배치 처리
        batch_results = await asyncio.gather(*[
            process_with_semaphore(i, batch)
            for i, batch in enumerate(batches)
        ])
        
        metrics.end_time = time.time()
        
        # 결과 집계
        all_results = []
        for batch_result in batch_results:
            if batch_result.success:
                successful_batches += 1
                all_results.extend(batch_result.results)
            else:
                failed_batches += 1
        
        logger.info(f"Batch processing complete: {successful_batches}/{len(batches)} successful, "
                   f"{metrics.duration_seconds:.2f}s, {metrics.throughput_items_per_second:.1f} items/s")
        
        return {
            "total_batches": len(batches),
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "total_items_processed": len(all_results),
            "processing_time_seconds": metrics.duration_seconds,
            "throughput_items_per_second": metrics.throughput_items_per_second,
            "success_rate_percentage": metrics.success_rate,
            "results": all_results,
            "metrics": metrics
        }
    
    async def process_stream_batches(self, 
                                     item_stream: AsyncIterator[Any],
                                     processor_func: Callable) -> AsyncIterator[Dict[str, Any]]:
        """스트림 방식으로 배치 처리"""
        current_batch = []
        batch_count = 0
        
        async for item in item_stream:
            current_batch.append(item)
            
            # 배치 크기에 도달하면 처리
            if len(current_batch) >= self.current_batch_size:
                batch_result = await processor_func(current_batch)
                yield {
                    "batch_id": batch_count,
                    "items_count": len(current_batch),
                    "result": batch_result
                }
                
                current_batch = []
                batch_count += 1
        
        # 마지막 남은 배치 처리
        if current_batch:
            batch_result = await processor_func(current_batch)
            yield {
                "batch_id": batch_count,
                "items_count": len(current_batch),
                "result": batch_result
            }
    
    def get_optimal_batch_size(self, total_items: int, target_duration_seconds: float = 2.0) -> int:
        """최적 배치 크기 계산"""
        if not self.batch_time_history:
            return self.initial_batch_size
        
        # 평균 아이템당 처리 시간 계산
        avg_time_per_item = self.average_batch_time / self.current_batch_size
        
        # 목표 시간에 맞는 배치 크기 계산
        optimal_size = int(target_duration_seconds / avg_time_per_item) if avg_time_per_item > 0 else self.initial_batch_size
        
        # 최소/최대 제한 적용
        optimal_size = max(10, min(1000, optimal_size))
        
        return optimal_size
    
    def reset_statistics(self):
        """통계 초기화"""
        self.total_batches_processed = 0
        self.total_items_processed = 0
        self.average_batch_time = 0.0
        self.batch_time_history = []
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        return {
            "total_batches_processed": self.total_batches_processed,
            "total_items_processed": self.total_items_processed,
            "average_batch_time_seconds": self.average_batch_time,
            "current_batch_size": self.current_batch_size,
            "initial_batch_size": self.initial_batch_size,
            "max_concurrent_batches": self.max_concurrent_batches,
            "adaptive_sizing_enabled": self.adaptive_sizing,
            "recent_batch_times": self.batch_time_history[-10:]  # 최근 10개
        }
    
    # Private methods
    
    async def _process_single_item(self, item: Any) -> Any:
        """단일 아이템 처리 (Mock)"""
        # Mock 처리 - 실제로는 아이템별 로직 실행
        await asyncio.sleep(0.001)  # 1ms 처리 시간 시뮬레이션
        
        return {
            "original": item,
            "processed": True,
            "timestamp": time.time()
        }
    
    def _update_batch_statistics(self, processing_time: float):
        """배치 처리 통계 업데이트"""
        self.total_batches_processed += 1
        self.total_items_processed += self.current_batch_size
        
        # 배치 시간 히스토리 관리 (최대 100개)
        self.batch_time_history.append(processing_time)
        if len(self.batch_time_history) > 100:
            self.batch_time_history.pop(0)
        
        # 평균 배치 처리 시간 계산
        self.average_batch_time = sum(self.batch_time_history) / len(self.batch_time_history)
    
    def _adjust_batch_size(self, processing_time: float):
        """적응형 배치 크기 조정"""
        if not self.adaptive_sizing:
            return
        
        target_time = 2.0  # 목표: 2초
        tolerance = 0.5    # 허용 오차: 0.5초
        
        if processing_time > target_time + tolerance:
            # 처리 시간이 너무 길면 배치 크기 감소
            new_size = max(10, int(self.current_batch_size * 0.8))
            if new_size != self.current_batch_size:
                logger.info(f"Reducing batch size: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size
                
        elif processing_time < target_time - tolerance:
            # 처리 시간이 너무 짧으면 배치 크기 증가
            new_size = min(1000, int(self.current_batch_size * 1.2))
            if new_size != self.current_batch_size:
                logger.info(f"Increasing batch size: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size
    
    def __del__(self):
        """소멸자에서 ThreadPoolExecutor 정리"""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)