"""
Gemini Client - LangChain과 호환되는 Google Gemini 클라이언트 래퍼
"""

import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI
    LANGCHAIN_GOOGLE_AVAILABLE = True
except ImportError:
    LANGCHAIN_GOOGLE_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Please install: pip install langchain-google-genai")


class GeminiClient:
    """Google Gemini 클라이언트 래퍼 - LangChain 호환"""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.llm = None
        
        if not self.api_key:
            logger.error("Google API Key not found in environment variables")
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        if not LANGCHAIN_GOOGLE_AVAILABLE:
            logger.error("langchain-google-genai package not available")
            raise ImportError("Please install: pip install langchain-google-genai")
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Gemini LangChain 클라이언트 초기화"""
        try:
            # Google AI API 설정
            genai.configure(api_key=self.api_key)
            
            # LangChain Gemini 클라이언트 생성
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.api_key,
                temperature=0.1,
                max_tokens=8192,
                timeout=60,
                max_retries=3
            )
            
            logger.info("Gemini LangChain client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def get_llm(self) -> Optional['ChatGoogleGenerativeAI']:
        """LangChain 호환 Gemini LLM 반환"""
        return self.llm
    
    def is_available(self) -> bool:
        """Gemini 클라이언트 사용 가능 여부"""
        return self.llm is not None
    
    async def test_connection(self) -> bool:
        """Gemini API 연결 테스트"""
        if not self.llm:
            return False
        
        try:
            # 간단한 테스트 메시지
            from langchain_core.messages import HumanMessage
            test_message = [HumanMessage(content="Hello, respond with 'OK' only.")]
            response = await self.llm.ainvoke(test_message)
            
            logger.info(f"Gemini connection test successful: {response.content[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False


# 글로벌 Gemini 클라이언트 인스턴스
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """글로벌 Gemini 클라이언트 인스턴스 반환"""
    global _gemini_client
    
    if _gemini_client is None:
        try:
            _gemini_client = GeminiClient()
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}")
            raise
    
    return _gemini_client


def get_gemini_llm() -> Optional['ChatGoogleGenerativeAI']:
    """LangChain 호환 Gemini LLM 직접 반환"""
    try:
        client = get_gemini_client()
        return client.get_llm()
    except Exception as e:
        logger.error(f"Failed to get Gemini LLM: {e}")
        return None