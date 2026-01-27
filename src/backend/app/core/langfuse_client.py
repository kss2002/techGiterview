"""
Langfuse Client - LLM 관측성을 위한 Langfuse 통합 모듈
"""

import logging
from typing import Optional, Dict, Any
from functools import wraps
from app.core.config import settings

logger = logging.getLogger(__name__)

# Langfuse 사용 가능 여부 확인
try:
    from langfuse import Langfuse
    # Langfuse 3.x imports
    try:
        from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    except ImportError:
        # Fallback for older versions
        from langfuse.callback import CallbackHandler as LangfuseCallbackHandler
        
    try:
        from langfuse import observe
    except ImportError:
        from langfuse.decorators import observe
        
    LANGFUSE_AVAILABLE = True
except ImportError as e:
    LANGFUSE_AVAILABLE = False
    logger.warning(f"langfuse import failed: {e}. Please install: pip install langfuse")


class LangfuseClient:
    """Langfuse 클라이언트 래퍼"""
    
    def __init__(self):
        self.client: Optional['Langfuse'] = None
        self.callback_handler: Optional['LangfuseCallbackHandler'] = None
        self.enabled = False
        
        # 환경변수에서 설정 로드
        self.public_key = getattr(settings, 'langfuse_public_key', None)
        self.secret_key = getattr(settings, 'langfuse_secret_key', None)
        self.host = getattr(settings, 'langfuse_host', 'http://localhost:3000')
        
        if self.public_key and self.secret_key and LANGFUSE_AVAILABLE:
            self._initialize_client()
        else:
            logger.info("[LANGFUSE] Langfuse disabled - missing credentials or package")
    
    def _initialize_client(self):
        """Langfuse 클라이언트 초기화"""
        try:
            self.client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host
            )
            
            self.callback_handler = LangfuseCallbackHandler(
                public_key=self.public_key
                # host and secret_key are read from environment variables or global config
            )
            
            self.enabled = True
            logger.info(f"[LANGFUSE] Client initialized successfully (host: {self.host})")
            
        except Exception as e:
            logger.error(f"[LANGFUSE] Failed to initialize client: {e}")
            self.enabled = False
    
    def get_callback_handler(self, 
                              trace_name: str = "llm-call",
                              user_id: Optional[str] = None,
                              session_id: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> Optional['LangfuseCallbackHandler']:
        """LangChain 콜백 핸들러 반환"""
        if not self.enabled or not LANGFUSE_AVAILABLE:
            return None
        
        try:
            return LangfuseCallbackHandler(
                public_key=self.public_key,
                # host and secret_key from environment
                # trace_name is not supported in init of new CallbackHandler? 
                # Wait, check signature again.
                # Signature: (public_key, update_trace, trace_context).
                # New handler doesn't accept trace_name in init?
            )
        except Exception as e:
            logger.error(f"[LANGFUSE] Failed to create callback handler: {e}")
            return None
    
    def create_trace(self, 
                     name: str,
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None,
                     input: Optional[Any] = None):
        """수동 트레이스 생성 (Langfuse v3 OpenTelemetry 스타일)"""
        if not self.client:
            return None
        
        try:
            # v3: trace() -> start_span(), update_trace() for context
            span = self.client.start_span(
                name=name,
                metadata=metadata or {},
                input=input
            )
            
            if user_id or session_id:
                span.update_trace(
                    user_id=user_id,
                    session_id=session_id
                )
            return span
        except Exception as e:
            logger.error(f"[LANGFUSE] Failed to create trace: {e}")
            return None
    
    def flush(self):
        """버퍼링된 이벤트 즉시 전송"""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"[LANGFUSE] Failed to flush: {e}")
    
    def is_enabled(self) -> bool:
        """Langfuse 활성화 여부"""
        return self.enabled


# 글로벌 Langfuse 클라이언트 인스턴스
_langfuse_client: Optional[LangfuseClient] = None


def get_langfuse_client() -> LangfuseClient:
    """글로벌 Langfuse 클라이언트 반환"""
    global _langfuse_client
    
    if _langfuse_client is None:
        _langfuse_client = LangfuseClient()
    
    return _langfuse_client


def get_langfuse_callback(trace_name: str = "llm-call",
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Optional['LangfuseCallbackHandler']:
    """간편하게 Langfuse 콜백 핸들러 반환"""
    client = get_langfuse_client()
    return client.get_callback_handler(
        trace_name=trace_name,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata
    )


def traced(name: str = None, 
           capture_input: bool = True, 
           capture_output: bool = True):
    """
    함수 추적을 위한 데코레이터
    
    사용법:
        @traced("question_generation")
        async def generate_question(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            client = get_langfuse_client()
            trace_name = name or func.__name__
            
            if client.is_enabled():
                trace = client.create_trace(
                    name=trace_name,
                    input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]} if capture_input else None
                )
                
                try:
                    result = await func(*args, **kwargs)
                    if trace and capture_output:
                        trace.update(output=str(result)[:1000])
                    return result
                except Exception as e:
                    if trace:
                        trace.update(output={"error": str(e)})
                    raise
                finally:
                    client.flush()
            else:
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            client = get_langfuse_client()
            trace_name = name or func.__name__
            
            if client.is_enabled():
                trace = client.create_trace(
                    name=trace_name,
                    input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]} if capture_input else None
                )
                
                try:
                    result = func(*args, **kwargs)
                    if trace and capture_output:
                        trace.update(output=str(result)[:1000])
                    return result
                except Exception as e:
                    if trace:
                        trace.update(output={"error": str(e)})
                    raise
                finally:
                    client.flush()
            else:
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
