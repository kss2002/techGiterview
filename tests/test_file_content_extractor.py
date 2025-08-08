"""
파일 내용 추출 및 저장 시스템 테스트

TDD 방식으로 먼저 테스트를 작성하고, 이후 실제 구현을 진행합니다.
GitHub Raw Content API와 Redis 캐싱을 통한 파일 내용 추출 시스템
"""

import pytest
import asyncio
import base64
import hashlib
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

# 구현 예정 모듈들
# from app.services.file_content_extractor import FileContentExtractor


class TestFileContentExtractor:
    """파일 내용 추출기 테스트"""
    
    @pytest.fixture
    def extractor(self):
        """테스트용 파일 내용 추출기 인스턴스"""
        from app.services.file_content_extractor import FileContentExtractor
        return FileContentExtractor(github_token="test_token")
    
    @pytest.fixture
    def sample_file_list(self):
        """테스트용 중요 파일 목록"""
        return [
            {"path": "src/main.py", "importance_score": 0.95},
            {"path": "src/config.json", "importance_score": 0.90},
            {"path": "package.json", "importance_score": 0.85},
            {"path": "src/utils/helper.js", "importance_score": 0.75},
            {"path": "README.md", "importance_score": 0.40}
        ]
    
    @pytest.fixture
    def github_content_response(self):
        """GitHub API 응답 Mock 데이터"""
        # Base64로 인코딩된 Python 코드
        python_code = """def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
"""
        encoded_content = base64.b64encode(python_code.encode()).decode()
        
        return {
            "name": "main.py",
            "path": "src/main.py",
            "sha": "abc123def456",
            "size": len(python_code),
            "url": "https://api.github.com/repos/owner/repo/contents/src/main.py",
            "html_url": "https://github.com/owner/repo/blob/main/src/main.py",
            "git_url": "https://api.github.com/repos/owner/repo/git/blobs/abc123def456",
            "download_url": "https://raw.githubusercontent.com/owner/repo/main/src/main.py",
            "type": "file",
            "content": encoded_content,
            "encoding": "base64"
        }

    def test_extract_single_file_content(self, extractor, github_content_response):
        """단일 파일 내용 추출 테스트"""
        # Given: GitHub API 응답 Mock
        
        # When: 단일 파일 내용 추출
        with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = github_content_response
            
            result = asyncio.run(extractor.extract_file_content(
                owner="owner",
                repo="repo", 
                file_path="src/main.py"
            ))
        
        # Then: 파일 내용이 올바르게 추출되어야 함
        assert result["success"] is True
        assert result["file_path"] == "src/main.py"
        assert result["content"] is not None
        assert "def hello_world():" in result["content"]
        assert result["size"] > 0
        assert result["encoding"] == "utf-8"

    def test_extract_multiple_files_content(self, extractor, sample_file_list):
        """다중 파일 내용 일괄 추출 테스트"""
        # Given: 중요 파일 목록
        
        # When: 다중 파일 내용 추출
        with patch.object(extractor, 'extract_file_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "file_path": "test.py",
                "content": "print('test')",
                "size": 13,
                "encoding": "utf-8"
            }
            
            results = asyncio.run(extractor.extract_files_content(
                owner="owner",
                repo="repo",
                important_files=sample_file_list
            ))
        
        # Then: 모든 파일의 내용이 추출되어야 함
        assert len(results) == len(sample_file_list)
        
        for result in results:
            assert "success" in result
            assert "file_path" in result
            assert "content" in result or "error" in result

    def test_file_size_limit_filtering(self, extractor):
        """파일 크기 제한 필터링 테스트"""
        # Given: 50KB 이상의 대용량 파일
        large_content = "x" * (60 * 1024)  # 60KB
        large_file_response = {
            "name": "large_file.py",
            "path": "src/large_file.py",
            "size": len(large_content),
            "content": base64.b64encode(large_content.encode()).decode(),
            "encoding": "base64"
        }
        
        # When: 대용량 파일 내용 추출 시도
        with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = large_file_response
            
            result = asyncio.run(extractor.extract_file_content(
                owner="owner",
                repo="repo",
                file_path="src/large_file.py"
            ))
        
        # Then: 파일 크기 제한으로 인해 제외되어야 함
        assert result["success"] is False
        assert "exceeds limit" in result["error"].lower()
        assert result["size"] > extractor.size_limit

    def test_binary_file_filtering(self, extractor):
        """바이너리 파일 필터링 테스트"""
        # Given: 바이너리 파일 (이미지)
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        binary_file_response = {
            "name": "image.png",
            "path": "assets/image.png",
            "size": len(binary_content),
            "content": base64.b64encode(binary_content).decode(),
            "encoding": "base64"
        }
        
        # When: 바이너리 파일 내용 추출 시도
        with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = binary_file_response
            
            result = asyncio.run(extractor.extract_file_content(
                owner="owner",
                repo="repo",
                file_path="assets/image.png"
            ))
        
        # Then: 바이너리 파일은 제외되어야 함
        assert result["success"] is False
        assert "binary file" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_redis_caching_system(self, extractor):
        """Redis 캐싱 시스템 테스트"""
        # Given: Redis Mock과 파일 데이터
        file_path = "src/main.py"
        repo_id = "owner/repo"
        file_content = "print('Hello World')"
        file_hash = hashlib.sha256(f"{repo_id}:{file_path}".encode()).hexdigest()
        cache_key = f"file_content:{repo_id}:{file_hash}"
        
        with patch.object(extractor, 'redis_client') as mock_redis:
            # When: 캐시에서 파일 내용 조회 (첫 번째 호출)
            mock_redis.get.return_value = None  # 캐시 미스
            
            with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {
                    "content": base64.b64encode(file_content.encode()).decode(),
                    "encoding": "base64",
                    "size": len(file_content)
                }
                
                result1 = await extractor.extract_file_content("owner", "repo", file_path)
            
            # Then: API 호출 후 캐시 저장이 되어야 함
            mock_redis.setex.assert_called_once()
            assert result1["success"] is True
            
            # When: 같은 파일 두 번째 조회 (캐시 히트)
            cached_data = {
                "file_path": file_path,
                "content": file_content,
                "size": len(file_content),
                "encoding": "utf-8",
                "cached_at": "2024-01-01T00:00:00Z"
            }
            mock_redis.get.return_value = str(cached_data).encode()
            
            result2 = await extractor.get_cached_file_content(repo_id, file_path)
            
            # Then: 캐시에서 데이터가 반환되어야 함
            assert result2 is not None
            mock_redis.get.assert_called()

    def test_detect_text_file_by_extension(self, extractor):
        """파일 확장자로 텍스트 파일 감지 테스트"""
        # Given: 다양한 파일 확장자
        text_files = [
            "src/main.py", "app.js", "style.css", "index.html",
            "config.json", "README.md", "Dockerfile", ".gitignore"
        ]
        
        binary_files = [
            "image.png", "photo.jpg", "document.pdf", "archive.zip",
            "executable.exe", "library.so", "font.ttf"
        ]
        
        # When & Then: 텍스트 파일 감지
        for file_path in text_files:
            assert extractor._is_text_file(file_path) is True, f"{file_path} should be text file"
        
        for file_path in binary_files:
            assert extractor._is_text_file(file_path) is False, f"{file_path} should be binary file"

    def test_detect_text_file_by_content(self, extractor):
        """파일 내용으로 텍스트 파일 감지 테스트"""
        # Given: 다양한 파일 내용
        text_content = "def hello():\n    print('Hello World')\n"
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        mixed_content = "Hello\x00World"  # NULL 문자 포함
        
        # When & Then: 내용으로 텍스트 파일 감지
        assert extractor._is_text_content(text_content.encode()) is True
        assert extractor._is_text_content(binary_content) is False
        assert extractor._is_text_content(mixed_content.encode()) is False

    def test_content_encoding_handling(self, extractor):
        """다양한 인코딩 처리 테스트"""
        # Given: 다양한 인코딩의 파일 내용
        utf8_text = "Hello 안녕하세요 🚀"
        latin1_text = "Héllo Wörld"
        
        # When: UTF-8 인코딩 처리
        utf8_bytes = utf8_text.encode('utf-8')
        decoded_utf8 = extractor._decode_content(utf8_bytes)
        
        # Then: 올바르게 디코딩되어야 함
        assert decoded_utf8["content"] == utf8_text
        assert decoded_utf8["encoding"] == "utf-8"
        
        # When: Latin-1 인코딩 처리
        latin1_bytes = latin1_text.encode('latin-1')
        decoded_latin1 = extractor._decode_content(latin1_bytes)
        
        # Then: 적절한 인코딩으로 디코딩되어야 함
        assert decoded_latin1["content"] is not None
        assert decoded_latin1["encoding"] in ["utf-8", "latin-1", "ISO-8859-1"]

    def test_github_api_error_handling(self, extractor):
        """GitHub API 오류 처리 테스트"""
        # Given: API 오류 상황들
        
        # When: 404 파일 없음 오류
        with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("404: Not Found")
            
            result = asyncio.run(extractor.extract_file_content(
                owner="owner",
                repo="repo",
                file_path="nonexistent.py"
            ))
        
        # Then: 오류가 적절히 처리되어야 함
        assert result["success"] is False
        assert "error" in result
        assert ("404" in result["error"] or "not found" in result["error"].lower())

    def test_rate_limiting_handling(self, extractor):
        """GitHub API Rate Limiting 처리 테스트"""
        # Given: Rate Limit 에러
        
        # When: Rate Limit 도달
        with patch.object(extractor, '_fetch_github_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("403: rate limit exceeded")
            
            result = asyncio.run(extractor.extract_file_content(
                owner="owner",
                repo="repo",
                file_path="src/main.py"
            ))
        
        # Then: Rate Limiting 오류가 적절히 처리되어야 함
        assert result["success"] is False
        assert "rate limit" in result["error"].lower()

    def test_content_truncation_for_large_files(self, extractor):
        """대용량 파일 내용 트렁케이션 테스트"""
        # Given: 제한 내이지만 긴 파일
        long_content = ["print('line {}')".format(i) for i in range(1000)]
        long_text = "\n".join(long_content)
        
        # When: 트렁케이션 적용
        truncated = extractor._truncate_content(long_text, max_lines=100)
        
        # Then: 지정된 라인 수로 제한되어야 함
        lines = truncated.split('\n')
        assert len(lines) <= 150  # Allow some flexibility for truncation logic
        assert ("truncated" in truncated.lower() or len(lines) < len(long_text.split('\n')))

    def test_extract_important_code_sections(self, extractor):
        """중요 코드 섹션 추출 테스트"""
        # Given: 클래스와 함수가 포함된 Python 코드
        python_code = '''
import os
import sys

class DatabaseManager:
    def __init__(self, db_url):
        self.db_url = db_url
    
    def connect(self):
        """Connect to database"""
        pass
    
    def execute_query(self, query):
        """Execute SQL query"""
        return []

def main():
    """Main function"""
    db = DatabaseManager("sqlite:///:memory:")
    db.connect()
    return True

if __name__ == "__main__":
    main()
'''
        
        # When: 중요 섹션 추출
        sections = extractor._extract_important_sections(python_code, "python")
        
        # Then: 클래스와 함수가 식별되어야 함
        assert len(sections) > 0
        assert any("class DatabaseManager" in section for section in sections)
        assert any("def main()" in section for section in sections)


class TestContentCacheManager:
    """파일 내용 캐시 관리자 테스트"""
    
    def test_cache_key_generation(self):
        """캐시 키 생성 테스트"""
        # Given: 저장소 정보와 파일 경로
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor()
        
        repo_id = "owner/repo"
        file_path = "src/main.py"
        
        # When: 캐시 키 생성
        cache_key = extractor._generate_cache_key(repo_id, file_path)
        
        # Then: 일관된 캐시 키가 생성되어야 함
        assert cache_key.startswith("file_content:")
        assert repo_id.replace("/", "_") in cache_key or hashlib.sha256(f"{repo_id}:{file_path}".encode()).hexdigest() in cache_key

    def test_cache_expiration_handling(self):
        """캐시 만료 처리 테스트"""
        # Given: 만료된 캐시 데이터
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor()
        
        # When: TTL 설정 확인
        ttl_seconds = extractor._get_cache_ttl()
        
        # Then: 24시간 TTL이 설정되어야 함
        assert ttl_seconds == 24 * 60 * 60  # 24 hours

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """캐시 무효화 테스트"""
        # Given: 캐시된 파일 데이터
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor()
        
        with patch.object(extractor, 'redis_client') as mock_redis:
            repo_id = "owner/repo"
            file_path = "src/main.py"
            
            # When: 캐시 무효화
            await extractor.invalidate_file_cache(repo_id, file_path)
            
            # Then: Redis delete 호출되어야 함
            mock_redis.delete.assert_called_once()


class TestFileContentIntegration:
    """파일 내용 추출 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_file_extraction(self):
        """전체 파일 추출 파이프라인 테스트"""
        # Given: 전체 시스템 Mock
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor(github_token="test_token")
        
        important_files = [
            {"path": "src/main.py", "importance_score": 0.95},
            {"path": "src/utils.py", "importance_score": 0.75}
        ]
        
        # When: 전체 추출 프로세스 실행
        with patch.object(extractor, 'extract_file_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "file_path": "src/main.py",
                "content": "def main(): pass",
                "size": 15,
                "encoding": "utf-8"
            }
            
            results = await extractor.extract_files_content(
                owner="owner",
                repo="repo",
                important_files=important_files
            )
        
        # Then: 모든 파일이 처리되어야 함
        assert len(results) == len(important_files)
        assert all(result["success"] for result in results)

    def test_performance_monitoring(self):
        """성능 모니터링 테스트"""
        # Given: 성능 측정 시스템
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor()
        
        # When: 성능 메트릭 수집
        metrics = extractor.get_performance_metrics()
        
        # Then: 성능 지표가 수집되어야 함
        assert "total_requests" in metrics
        assert "cache_hit_rate" in metrics
        assert "average_response_time" in metrics
        assert "error_rate" in metrics

    def test_concurrent_file_extraction(self):
        """동시 파일 추출 테스트"""
        # Given: 동시 요청 상황
        from app.services.file_content_extractor import FileContentExtractor
        extractor = FileContentExtractor()
        
        # When: 동시 파일 추출 수행
        file_paths = [f"src/file_{i}.py" for i in range(10)]
        
        with patch.object(extractor, 'extract_file_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {"success": True, "content": "test"}
            
            results = asyncio.run(extractor.extract_files_content_parallel(
                owner="owner",
                repo="repo", 
                file_paths=file_paths
            ))
        
        # Then: 모든 파일이 병렬로 처리되어야 함
        assert len(results) == len(file_paths)
        assert mock_extract.call_count == len(file_paths)