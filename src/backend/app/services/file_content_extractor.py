"""
파일 내용 추출 및 저장 시스템

GitHub Raw Content API를 통한 중요 파일 내용 다운로드와 Redis 캐싱 시스템
- 파일 크기 제한: 50KB
- 바이너리 파일 필터링
- Redis 캐싱 (TTL: 24시간)
- 병렬 처리 지원
- 성능 모니터링
"""

import asyncio
import aiohttp
import base64
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import chardet

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class FileContentExtractor:
    """GitHub 파일 내용 추출 및 캐싱 시스템"""
    
    def __init__(self, github_token: Optional[str] = None, redis_url: Optional[str] = None):
        self.github_token = github_token
        self.size_limit = 1024 * 1024  # 1MB (Gemini의 긴 컨텍스트 활용)
        self.max_lines = 50000  # 최대 라인 수 대폭 확대
        
        # Redis 설정
        self.redis_client = None
        if REDIS_AVAILABLE and redis_url:
            self.redis_client = redis.from_url(redis_url)
        
        # 성능 메트릭
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "total_response_time": 0.0
        }
        
        # 텍스트 파일 확장자
        self.text_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm', '.css', '.scss', '.sass',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.txt', '.rst', '.tex', '.sql', '.sh', '.bash', '.zsh', '.fish',
            '.java', '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs', '.go', '.rs',
            '.rb', '.php', '.perl', '.pl', '.r', '.swift', '.kt', '.scala', '.clj',
            '.dockerfile', '.makefile', '.cmake', '.gradle', '.pom'
        }
        
        # 바이너리 파일 확장자
        self.binary_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
            '.exe', '.dll', '.so', '.dylib', '.bin', '.deb', '.rpm',
            '.mp3', '.wav', '.mp4', '.avi', '.mkv', '.mov', '.wmv',
            '.ttf', '.otf', '.woff', '.woff2', '.eot'
        }
    
    async def extract_file_content(
        self, 
        owner: str, 
        repo: str, 
        file_path: str
    ) -> Dict[str, Any]:
        """단일 파일 내용 추출"""
        
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            # 텍스트 파일 여부 확인
            if not self._is_text_file(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Binary file not supported",
                    "size": 0
                }
            
            # 캐시 확인
            repo_id = f"{owner}/{repo}"
            cached_content = await self._get_cached_content(repo_id, file_path)
            if cached_content:
                self.metrics["cache_hits"] += 1
                return cached_content
            
            self.metrics["cache_misses"] += 1
            
            # GitHub API에서 파일 내용 가져오기
            github_response = await self._fetch_github_content(owner, repo, file_path)
            
            if not github_response:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Failed to fetch from GitHub API",
                    "size": 0
                }
            
            # 파일 크기 확인
            file_size = github_response.get("size", 0)
            if file_size > self.size_limit:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File size ({file_size} bytes) exceeds limit ({self.size_limit} bytes)",
                    "size": file_size
                }
            
            # Base64 디코딩
            encoded_content = github_response.get("content", "")
            if not encoded_content:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "No content in GitHub response",
                    "size": 0
                }
            
            try:
                decoded_bytes = base64.b64decode(encoded_content)
            except Exception as e:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"Base64 decoding failed: {str(e)}",
                    "size": 0
                }
            
            # 바이너리 콘텐츠 확인
            if not self._is_text_content(decoded_bytes):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Binary file detected in content",
                    "size": len(decoded_bytes)
                }
            
            # 텍스트 디코딩
            decode_result = self._decode_content(decoded_bytes)
            content = decode_result["content"]
            encoding = decode_result["encoding"]
            
            # 내용 트렁케이션 (필요시)
            if len(content.split('\n')) > self.max_lines:
                content = self._truncate_content(content, self.max_lines)
            
            result = {
                "success": True,
                "file_path": file_path,
                "content": content,
                "size": len(decoded_bytes),
                "encoding": encoding,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            }
            
            # 캐시에 저장
            await self._cache_content(repo_id, file_path, result)
            
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            error_msg = str(e)
            
            # 특정 오류 타입별 메시지 개선
            if "404" in error_msg:
                error_msg = "File not found"
            elif "403" in error_msg or "rate limit" in error_msg.lower():
                error_msg = "GitHub API rate limit exceeded"
            elif "timeout" in error_msg.lower():
                error_msg = "Request timeout"
            
            return {
                "success": False,
                "file_path": file_path,
                "error": error_msg,
                "size": 0
            }
        
        finally:
            # 성능 메트릭 업데이트
            response_time = time.time() - start_time
            self.metrics["total_response_time"] += response_time
    
    async def extract_files_content(
        self, 
        owner: str, 
        repo: str, 
        important_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """여러 파일의 내용 일괄 추출"""
        
        tasks = []
        for file_info in important_files:
            file_path = file_info.get("path") or file_info.get("file_path")
            if file_path:
                task = self.extract_file_content(owner, repo, file_path)
                tasks.append(task)
        
        if not tasks:
            return []
        
        # 병렬 처리
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "file_path": "unknown"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def extract_files_content_parallel(
        self, 
        owner: str, 
        repo: str, 
        file_paths: List[str],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """병렬 처리로 파일 내용 추출 (동시 요청 수 제한)"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_semaphore(file_path: str):
            async with semaphore:
                return await self.extract_file_content(owner, repo, file_path)
        
        tasks = [extract_with_semaphore(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "file_path": file_paths[i] if i < len(file_paths) else "unknown"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _fetch_github_content(
        self, 
        owner: str, 
        repo: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """GitHub API로 파일 내용 가져오기"""
        
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechGiterview/1.0"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise Exception("404: File not found")
                    elif response.status == 403:
                        raise Exception("403: GitHub API rate limit exceeded")
                    else:
                        raise Exception(f"GitHub API error: {response.status}")
        
        except asyncio.TimeoutError:
            raise Exception("Request timeout")
        except Exception as e:
            raise e
    
    def _is_text_file(self, file_path: str) -> bool:
        """파일 확장자로 텍스트 파일 여부 판단"""
        
        # 확장자 추출
        file_path_lower = file_path.lower()
        
        # 특수 파일명 처리
        special_files = {
            'dockerfile', 'makefile', 'rakefile', 'gemfile', 'procfile',
            '.gitignore', '.gitattributes', '.dockerignore', '.eslintrc',
            '.babelrc', '.prettierrc', 'license', 'readme', 'changelog',
            'authors', 'contributors', 'copying', 'install', 'news'
        }
        
        filename = file_path_lower.split('/')[-1]
        if filename in special_files or filename.startswith('.env'):
            return True
        
        # 확장자 확인
        for ext in self.text_extensions:
            if file_path_lower.endswith(ext):
                return True
        
        # 바이너리 확장자 확인
        for ext in self.binary_extensions:
            if file_path_lower.endswith(ext):
                return False
        
        # 확장자가 없는 경우 텍스트로 가정
        if '.' not in filename:
            return True
        
        return True  # 기본적으로 텍스트 파일로 처리
    
    def _is_text_content(self, content_bytes: bytes) -> bool:
        """파일 내용으로 텍스트 파일 여부 판단"""
        
        if not content_bytes:
            return True
        
        # NULL 바이트 확인
        if b'\x00' in content_bytes[:1024]:  # 첫 1KB 확인
            return False
        
        # 비인쇄 문자 비율 확인
        sample = content_bytes[:1024]
        non_printable = sum(1 for byte in sample if byte < 32 and byte not in (9, 10, 13))
        
        if len(sample) > 0 and non_printable / len(sample) > 0.3:
            return False
        
        return True
    
    def _decode_content(self, content_bytes: bytes) -> Dict[str, str]:
        """파일 내용 디코딩"""
        
        # UTF-8 시도
        try:
            content = content_bytes.decode('utf-8')
            return {"content": content, "encoding": "utf-8"}
        except UnicodeDecodeError:
            pass
        
        # chardet로 인코딩 감지
        try:
            detected = chardet.detect(content_bytes)
            if detected['encoding'] and detected['confidence'] > 0.7:
                content = content_bytes.decode(detected['encoding'])
                return {"content": content, "encoding": detected['encoding']}
        except:
            pass
        
        # Latin-1 (거의 모든 바이트 시퀀스 처리 가능)
        try:
            content = content_bytes.decode('latin-1')
            return {"content": content, "encoding": "latin-1"}
        except UnicodeDecodeError:
            pass
        
        # 마지막 수단: 오류 무시하고 UTF-8
        content = content_bytes.decode('utf-8', errors='ignore')
        return {"content": content, "encoding": "utf-8-ignore"}
    
    def _truncate_content(self, content: str, max_lines: int) -> str:
        """긴 파일 내용 트렁케이션"""
        
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        # 중요 섹션 우선 포함
        important_lines = []
        regular_lines = []
        
        for i, line in enumerate(lines):
            if self._is_important_line(line):
                important_lines.append((i, line))
            else:
                regular_lines.append((i, line))
        
        # 중요 라인 우선 포함
        selected_lines = []
        remaining_slots = max_lines - 50  # 50라인은 truncation 메시지 등을 위해 예약
        
        # 중요 라인 추가
        for i, line in important_lines[:remaining_slots]:
            selected_lines.append((i, line))
        
        # 남은 공간에 일반 라인 추가
        remaining_slots = max_lines - 50 - len(selected_lines)
        for i, line in regular_lines[:remaining_slots]:
            selected_lines.append((i, line))
        
        # 라인 번호순 정렬
        selected_lines.sort(key=lambda x: x[0])
        
        # 결과 생성
        result_lines = []
        last_line_num = -1
        
        for line_num, line in selected_lines:
            if line_num > last_line_num + 1:
                result_lines.append(f"... (lines {last_line_num + 1}-{line_num - 1} skipped)")
            result_lines.append(line)
            last_line_num = line_num
        
        # 마지막 생략 메시지
        if last_line_num < len(lines) - 1:
            result_lines.append(f"... (content truncated, showing {len(selected_lines)} of {len(lines)} lines)")
        
        return '\n'.join(result_lines)
    
    def _is_important_line(self, line: str) -> bool:
        """중요한 라인 여부 판단"""
        
        line_stripped = line.strip()
        
        # 함수/클래스 정의
        if (line_stripped.startswith(('def ', 'class ', 'function ', 'export function')) or
            'function(' in line_stripped or 'async def' in line_stripped):
            return True
        
        # 임포트 문
        if line_stripped.startswith(('import ', 'from ', 'require ', '#include')):
            return True
        
        # 설정/상수 정의
        if (line_stripped.startswith(('const ', 'let ', 'var ', 'final ')) and
            line_stripped.isupper().replace('_', '').replace(' ', '')):
            return True
        
        # 주석 (문서)
        if line_stripped.startswith(('"""', "'''", '/**', '/*', '///', '#!')):
            return True
        
        return False
    
    def _extract_important_sections(self, content: str, language: str) -> List[str]:
        """중요 코드 섹션 추출"""
        
        sections = []
        lines = content.split('\n')
        
        if language.lower() == 'python':
            # Python 클래스와 함수 추출
            current_section = []
            indent_level = 0
            in_function_or_class = False
            
            for line in lines:
                stripped = line.strip()
                
                if stripped.startswith(('class ', 'def ', 'async def ')):
                    # 이전 섹션 저장
                    if current_section:
                        sections.append('\n'.join(current_section))
                    
                    # 새 섹션 시작
                    current_section = [line]
                    indent_level = len(line) - len(line.lstrip())
                    in_function_or_class = True
                
                elif in_function_or_class:
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
                    
                    if line.strip() and current_indent <= indent_level:
                        # 섹션 종료
                        sections.append('\n'.join(current_section))
                        current_section = []
                        in_function_or_class = False
                        
                        # 새 섹션 시작인지 확인
                        if stripped.startswith(('class ', 'def ', 'async def ')):
                            current_section = [line]
                            indent_level = current_indent
                            in_function_or_class = True
                    else:
                        current_section.append(line)
            
            # 마지막 섹션 추가
            if current_section:
                sections.append('\n'.join(current_section))
        
        elif language.lower() in ['javascript', 'typescript']:
            # JavaScript/TypeScript 함수와 클래스 추출
            brace_count = 0
            current_section = []
            in_function_or_class = False
            
            for line in lines:
                stripped = line.strip()
                
                if (re.search(r'\b(function|class|const.*=.*function|let.*=.*function|var.*=.*function)', stripped) or
                    re.search(r'\b(async\s+function|export\s+function|export\s+class)', stripped)):
                    
                    if current_section and not in_function_or_class:
                        sections.append('\n'.join(current_section))
                    
                    current_section = [line]
                    brace_count = line.count('{') - line.count('}')
                    in_function_or_class = True
                
                elif in_function_or_class:
                    current_section.append(line)
                    brace_count += line.count('{') - line.count('}')
                    
                    if brace_count <= 0:
                        sections.append('\n'.join(current_section))
                        current_section = []
                        in_function_or_class = False
        
        return sections[:10]  # 최대 10개 섹션만 반환
    
    async def _get_cached_content(self, repo_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """캐시에서 파일 내용 조회"""
        
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(repo_id, file_path)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data.decode('utf-8'))
        
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def _cache_content(self, repo_id: str, file_path: str, content_data: Dict[str, Any]) -> None:
        """파일 내용을 캐시에 저장"""
        
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(repo_id, file_path)
            cache_data = json.dumps(content_data, ensure_ascii=False)
            ttl = self._get_cache_ttl()
            
            await self.redis_client.setex(cache_key, ttl, cache_data)
        
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def _generate_cache_key(self, repo_id: str, file_path: str) -> str:
        """캐시 키 생성"""
        
        # 저장소와 파일 경로를 해시로 변환
        key_data = f"{repo_id}:{file_path}"
        file_hash = hashlib.sha256(key_data.encode()).hexdigest()
        
        return f"file_content:{repo_id.replace('/', '_')}:{file_hash}"
    
    def _get_cache_ttl(self) -> int:
        """캐시 TTL 반환 (24시간)"""
        return 24 * 60 * 60
    
    async def invalidate_file_cache(self, repo_id: str, file_path: str) -> None:
        """특정 파일의 캐시 무효화"""
        
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(repo_id, file_path)
            await self.redis_client.delete(cache_key)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
    
    async def get_cached_file_content(self, repo_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """캐시된 파일 내용 직접 조회"""
        return await self._get_cached_content(repo_id, file_path)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환"""
        
        total_requests = self.metrics["total_requests"]
        cache_hits = self.metrics["cache_hits"]
        cache_misses = self.metrics["cache_misses"]
        errors = self.metrics["errors"]
        total_time = self.metrics["total_response_time"]
        
        return {
            "total_requests": total_requests,
            "cache_hit_rate": cache_hits / max(cache_hits + cache_misses, 1),
            "error_rate": errors / max(total_requests, 1),
            "average_response_time": total_time / max(total_requests, 1),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "errors": errors
        }
    
    def reset_metrics(self) -> None:
        """성능 메트릭 초기화"""
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "total_response_time": 0.0
        }
    
    async def close(self) -> None:
        """리소스 정리"""
        if self.redis_client:
            await self.redis_client.close()