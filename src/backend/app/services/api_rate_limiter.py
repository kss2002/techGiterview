"""
GitHub API Rate Limiting 관리 서비스
GitHub API의 요청 제한을 효율적으로 관리하고 최적화

주요 기능:
- GitHub API Rate Limit 모니터링 및 관리
- 토큰 로테이션 전략
- 지수 백오프 및 재시도 로직
- 요청 큐 관리
"""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
import logging

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate Limit 처리 전략"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    SCHEDULED_RETRY = "scheduled_retry"
    TOKEN_ROTATION = "token_rotation"
    QUEUE_MANAGEMENT = "queue_management"


@dataclass
class RateLimitInfo:
    """Rate Limit 정보"""
    remaining: int
    limit: int
    reset_time: float
    used: int
    
    @property
    def usage_percentage(self) -> float:
        return (self.used / self.limit) * 100 if self.limit > 0 else 0
    
    @property
    def time_until_reset_minutes(self) -> float:
        return max(0, (self.reset_time - time.time()) / 60)


@dataclass
class TokenInfo:
    """토큰 정보"""
    token: str
    rate_limit: RateLimitInfo
    last_used: float
    is_active: bool = True
    
    @property
    def is_available(self) -> bool:
        return self.is_active and self.rate_limit.remaining > 10  # 최소 10개 요청 여유분 확보


class APIRateLimiter:
    """GitHub API Rate Limiter"""
    
    def __init__(self, 
                 max_requests_per_hour: int = 5000,
                 tokens: List[str] = None,
                 default_backoff_seconds: float = 1.0):
        self.max_requests_per_hour = max_requests_per_hour
        self.default_backoff_seconds = default_backoff_seconds
        
        # 토큰 관리
        self.tokens = [TokenInfo(
            token=token,
            rate_limit=RateLimitInfo(remaining=5000, limit=5000, reset_time=time.time() + 3600, used=0),
            last_used=0
        ) for token in (tokens or ["default_token"])]
        
        self.current_token_index = 0
        self._request_queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(10)  # 최대 10개 동시 요청
        
        # 통계
        self.total_requests = 0
        self.successful_requests = 0
        self.rate_limited_requests = 0
        self.token_rotations = 0
    
    async def acquire(self) -> str:
        """Rate limit를 고려하여 토큰 획득"""
        async with self._semaphore:
            # 사용 가능한 토큰 찾기
            available_token = await self._find_available_token()
            
            if available_token is None:
                # 모든 토큰이 제한 상태인 경우 대기
                await self._wait_for_token_availability()
                available_token = await self._find_available_token()
            
            if available_token is None:
                raise Exception("No available tokens after waiting")
            
            # 토큰 사용 기록
            available_token.last_used = time.time()
            self.total_requests += 1
            
            return available_token.token
    
    async def manage_requests(self, requests_count: int) -> Dict[str, Any]:
        """요청 수를 관리하고 허용 여부 결정"""
        current_token = self.tokens[self.current_token_index]
        
        # Rate limit 정보 업데이트
        await self._update_rate_limit_info(current_token)
        
        if current_token.rate_limit.remaining >= requests_count:
            return {
                "requests_allowed": True,
                "remaining_quota": current_token.rate_limit.remaining - requests_count,
                "estimated_wait_time": 0,
                "strategy": "proceed"
            }
        else:
            # 요청 수가 남은 quota를 초과하는 경우
            wait_time = await self._calculate_wait_time(current_token, requests_count)
            return {
                "requests_allowed": False,
                "remaining_quota": current_token.rate_limit.remaining,
                "estimated_wait_time": wait_time,
                "strategy": "wait_or_rotate"
            }
    
    async def handle_rate_limit_exceeded(self, requests_needed: int) -> Dict[str, Any]:
        """Rate Limit 초과 시 처리"""
        current_token = self.tokens[self.current_token_index]
        
        # 다른 토큰으로 로테이션 시도
        alternative_token = await self._find_alternative_token(requests_needed)
        
        if alternative_token:
            self.current_token_index = self.tokens.index(alternative_token)
            self.token_rotations += 1
            
            return {
                "rate_limit_exceeded": True,
                "wait_strategy": RateLimitStrategy.TOKEN_ROTATION.value,
                "estimated_wait_minutes": 0,
                "new_token_available": True
            }
        else:
            # 모든 토큰이 제한 상태인 경우 대기 전략
            wait_minutes = current_token.rate_limit.time_until_reset_minutes
            strategy = self._determine_wait_strategy(wait_minutes)
            
            return {
                "rate_limit_exceeded": True,
                "wait_strategy": strategy.value,
                "estimated_wait_minutes": min(wait_minutes, 35),  # 최대 35분
                "new_token_available": False
            }
    
    async def rotate_tokens(self, available_tokens: List[str]) -> Dict[str, Any]:
        """토큰 로테이션 수행"""
        # 기존 토큰 정보 업데이트
        for token_info in self.tokens:
            await self._update_rate_limit_info(token_info)
        
        # 사용 가능한 토큰 확인
        usable_tokens = [
            token_info for token_info in self.tokens 
            if token_info.token in available_tokens and token_info.is_available
        ]
        
        if usable_tokens:
            # 가장 여유 있는 토큰 선택
            best_token = max(usable_tokens, key=lambda t: t.rate_limit.remaining)
            self.current_token_index = self.tokens.index(best_token)
            
            return {
                "rotation_successful": True,
                "active_token": best_token.token,
                "tokens_available": len(usable_tokens),
                "remaining_requests": best_token.rate_limit.remaining
            }
        else:
            return {
                "rotation_successful": False,
                "active_token": None,
                "tokens_available": 0,
                "remaining_requests": 0
            }
    
    async def exponential_backoff_retry(self, operation_func, max_retries: int = 5) -> Any:
        """지수 백오프 재시도 로직"""
        retry_count = 0
        backoff_seconds = self.default_backoff_seconds
        
        while retry_count < max_retries:
            try:
                return await operation_func()
            except Exception as e:
                if "rate limit" in str(e).lower() or "403" in str(e):
                    self.rate_limited_requests += 1
                    
                    if retry_count < max_retries - 1:
                        # 지수 백오프 대기
                        wait_time = backoff_seconds * (2 ** retry_count) + random.uniform(0, 1)
                        logger.warning(f"Rate limited, retrying in {wait_time:.2f} seconds (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                        
                        # 토큰 로테이션 시도
                        await self._attempt_token_rotation()
                    else:
                        raise e
                else:
                    raise e
        
        raise Exception(f"Operation failed after {max_retries} retries")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Rate Limiter 통계 반환"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "success_rate_percentage": success_rate,
            "token_rotations": self.token_rotations,
            "active_tokens": len([t for t in self.tokens if t.is_active]),
            "current_token_remaining": self.tokens[self.current_token_index].rate_limit.remaining
        }
    
    # Private methods
    
    async def _find_available_token(self) -> Optional[TokenInfo]:
        """사용 가능한 토큰 찾기"""
        # 현재 토큰 먼저 확인
        current_token = self.tokens[self.current_token_index]
        await self._update_rate_limit_info(current_token)
        
        if current_token.is_available:
            return current_token
        
        # 다른 토큰들 확인
        for token_info in self.tokens:
            if token_info != current_token:
                await self._update_rate_limit_info(token_info)
                if token_info.is_available:
                    return token_info
        
        return None
    
    async def _find_alternative_token(self, requests_needed: int) -> Optional[TokenInfo]:
        """요청 수요를 만족하는 대체 토큰 찾기"""
        for token_info in self.tokens:
            await self._update_rate_limit_info(token_info)
            if token_info.is_available and token_info.rate_limit.remaining >= requests_needed:
                return token_info
        return None
    
    async def _update_rate_limit_info(self, token_info: TokenInfo):
        """토큰의 Rate Limit 정보 업데이트"""
        try:
            # Mock implementation - 실제로는 GitHub API 호출
            # headers = {"Authorization": f"token {token_info.token}"}
            # async with aiohttp.ClientSession() as session:
            #     async with session.get("https://api.github.com/rate_limit", headers=headers) as response:
            #         data = await response.json()
            #         core_info = data["resources"]["core"]
            #         token_info.rate_limit = RateLimitInfo(
            #             remaining=core_info["remaining"],
            #             limit=core_info["limit"],
            #             reset_time=core_info["reset"],
            #             used=core_info["limit"] - core_info["remaining"]
            #         )
            
            # Mock 업데이트 (테스트용)
            if time.time() > token_info.rate_limit.reset_time:
                # 리셋 시간이 지났으면 quota 재설정
                token_info.rate_limit.remaining = token_info.rate_limit.limit
                token_info.rate_limit.reset_time = time.time() + 3600
                token_info.rate_limit.used = 0
            
        except Exception as e:
            logger.error(f"Failed to update rate limit info: {e}")
            token_info.is_active = False
    
    async def _wait_for_token_availability(self):
        """토큰 사용 가능해질 때까지 대기"""
        min_wait_time = min(
            token.rate_limit.time_until_reset_minutes * 60 
            for token in self.tokens
        )
        
        # 최대 5분 대기
        wait_time = min(min_wait_time, 300)
        
        if wait_time > 0:
            logger.info(f"All tokens rate limited, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
    
    async def _calculate_wait_time(self, token_info: TokenInfo, requests_needed: int) -> float:
        """대기 시간 계산"""
        if token_info.rate_limit.remaining == 0:
            # 완전히 소진된 경우 리셋까지 대기
            return token_info.rate_limit.time_until_reset_minutes * 60
        else:
            # 부분적으로 사용 가능한 경우 짧은 대기
            return min(60, token_info.rate_limit.time_until_reset_minutes * 60 / 2)
    
    def _determine_wait_strategy(self, wait_minutes: float) -> RateLimitStrategy:
        """대기 전략 결정"""
        if wait_minutes <= 5:
            return RateLimitStrategy.EXPONENTIAL_BACKOFF
        elif wait_minutes <= 15:
            return RateLimitStrategy.SCHEDULED_RETRY
        else:
            return RateLimitStrategy.QUEUE_MANAGEMENT
    
    async def _attempt_token_rotation(self):
        """토큰 로테이션 시도"""
        available_token = await self._find_available_token()
        if available_token and available_token != self.tokens[self.current_token_index]:
            self.current_token_index = self.tokens.index(available_token)
            self.token_rotations += 1
            logger.info(f"Rotated to token with {available_token.rate_limit.remaining} remaining requests")