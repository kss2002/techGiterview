"""
GitHub API Client

GitHub API를 활용한 저장소 정보 수집 서비스
"""

import aiohttp
import asyncio
import json
import base64
import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from app.core.config import settings


class GitHubClient:
    """GitHub API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechGiterview/1.0"
        }
        self.session = None
        self.api_call_count = 0
        self.total_response_time = 0.0
        
        print(f"[GITHUB_CLIENT] GitHubClient 초기화 완료")
        print(f"[GITHUB_CLIENT] GitHub Token: {'설정됨' if settings.github_token else '설정되지 않음'}")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        print(f"[GITHUB_CLIENT] aiohttp 세션 시작 (timeout: 30초)")
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
        
        print(f"[GITHUB_CLIENT] 세션 종료 - 총 API 호출: {self.api_call_count}회")
        if self.api_call_count > 0:
            avg_response_time = self.total_response_time / self.api_call_count
            print(f"[GITHUB_CLIENT] 평균 응답 시간: {avg_response_time:.2f}초")
    
    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        """GitHub URL에서 owner와 repo명 추출"""
        # https://github.com/owner/repo 형태에서 owner, repo 추출
        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, repo_url)
        
        if not match:
            raise ValueError(f"유효하지 않은 GitHub URL: {repo_url}")
        
        owner, repo = match.groups()
        # .git 확장자 제거
        repo = repo.replace(".git", "")
        
        return owner, repo
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """저장소 기본 정보 조회"""
        start_time = time.time()
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        print(f"[GITHUB_CLIENT] 저장소 정보 요청: {owner}/{repo}")
        print(f"[GITHUB_CLIENT] API URL: {url}")
        
        if not self.session:
            raise RuntimeError("GitHubClient must be used as async context manager")
        
        self.api_call_count += 1
        async with self.session.get(url) as response:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            print(f"[GITHUB_CLIENT] 저장소 정보 응답: {response.status} ({response_time:.2f}초)")
            
            if response.status == 404:
                print(f"[GITHUB_CLIENT] 오류: 저장소를 찾을 수 없음 - {repo_url}")
                raise ValueError(f"저장소를 찾을 수 없습니다: {repo_url}")
            elif response.status != 200:
                print(f"[GITHUB_CLIENT] 오류: GitHub API 오류 {response.status}")
                raise RuntimeError(f"GitHub API 오류: {response.status}")
            
            data = await response.json()
            print(f"[GITHUB_CLIENT] 저장소 정보 수집 성공: {data.get('name', 'unknown')} ({data.get('language', 'unknown')} 프로젝트)")
            
            return {
                "name": data["name"],
                "owner": data["owner"]["login"],  # owner 정보 추가
                "full_name": data["full_name"],
                "description": data.get("description", ""),
                "language": data.get("language"),
                "size": data["size"],
                "stargazers_count": data["stargazers_count"],
                "forks_count": data["forks_count"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "default_branch": data["default_branch"],
                "topics": data.get("topics", []),
                "has_issues": data["has_issues"],
                "has_projects": data["has_projects"],
                "has_wiki": data["has_wiki"]
            }
    
    async def get_file_tree(self, repo_url: str, path: str = "") -> List[Dict[str, Any]]:
        """파일 트리 구조 조회"""
        start_time = time.time()
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        path_display = path if path else "루트"
        print(f"[GITHUB_CLIENT] 파일 트리 요청: {owner}/{repo}/{path_display}")
        
        if not self.session:
            raise RuntimeError("GitHubClient must be used as async context manager")
        
        self.api_call_count += 1
        async with self.session.get(url) as response:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            print(f"[GITHUB_CLIENT] 파일 트리 응답: {response.status} ({response_time:.2f}초)")
            
            if response.status != 200:
                print(f"[GITHUB_CLIENT] 파일 트리 조회 실패: {response.status} - {path_display}")
                return []
            
            data = await response.json()
            
            # 단일 파일인 경우 리스트로 감싸기
            if isinstance(data, dict):
                data = [data]
            
            files = []
            file_count = 0
            dir_count = 0
            total_size = 0
            
            for item in data:
                files.append({
                    "path": item["path"],
                    "name": item["name"],
                    "type": item["type"],  # 'file' or 'dir'
                    "size": item.get("size", 0),
                    "download_url": item.get("download_url")
                })
                
                if item["type"] == "file":
                    file_count += 1
                    total_size += item.get("size", 0)
                else:
                    dir_count += 1
            
            print(f"[GITHUB_CLIENT] 파일 트리 수집 완료: 파일 {file_count}개, 디렉토리 {dir_count}개, 총 크기 {total_size:,} bytes")
            
            return files
    
    async def get_file_content(self, repo_url: str, file_path: str) -> Optional[str]:
        """파일 내용 조회"""
        start_time = time.time()
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        
        print(f"[GITHUB_CLIENT] 파일 내용 요청: {file_path}")
        
        if not self.session:
            raise RuntimeError("GitHubClient must be used as async context manager")
        
        try:
            self.api_call_count += 1
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                print(f"[GITHUB_CLIENT] 파일 내용 응답: {response.status} ({response_time:.2f}초) - {file_path}")
                
                if response.status == 404:
                    print(f"[GITHUB_CLIENT] 파일 없음: {file_path}")
                    return None
                elif response.status == 403:
                    print(f"[GITHUB_CLIENT] API 제한 또는 액세스 거부: {file_path}")
                    # Rate limit 정보 확인
                    remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
                    reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
                    print(f"[GITHUB_CLIENT] Rate limit - 남은 요청: {remaining}, 리셋 시간: {reset_time}")
                    return None
                elif response.status != 200:
                    print(f"[GITHUB_CLIENT] 예상치 못한 상태 {response.status}: {file_path}")
                    return None
                
                data = await response.json()
                
                # 파일 크기 체크 (1MB 이상이면 스킵)
                file_size = data.get("size", 0)
                if file_size > 1024 * 1024:
                    print(f"[GITHUB_CLIENT] 파일 너무 큼 ({file_size:,} bytes > 1MB): {file_path}")
                    return None
                
                # 디렉토리인 경우 스킵
                if data.get("type") == "dir":
                    print(f"[GITHUB_CLIENT] 디렉토리임 (파일 아님): {file_path}")
                    return None
                
                print(f"[GITHUB_CLIENT] 파일 정보 - 크기: {file_size:,} bytes, 인코딩: {data.get('encoding', 'unknown')}")
                
                # Base64 디코딩
                if data.get("encoding") == "base64":
                    try:
                        decode_start = time.time()
                        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                        decode_time = time.time() - decode_start
                        
                        # 빈 내용이 아닌지 확인
                        if content.strip():
                            lines_count = content.count('\n') + 1
                            chars_count = len(content)
                            print(f"[GITHUB_CLIENT] 파일 내용 디코딩 성공 ({decode_time:.3f}초): {lines_count}줄, {chars_count:,}문자")
                            return content
                        else:
                            print(f"[GITHUB_CLIENT] 파일 내용 비어있음: {file_path}")
                            return "# Empty file"
                    except Exception as e:
                        print(f"[GITHUB_CLIENT] 파일 내용 디코딩 실패 - {file_path}: {e}")
                        return None
                
                # Base64가 아닌 경우 (일반적으로 작은 텍스트 파일)
                content = data.get("content", "")
                if content:
                    print(f"[GITHUB_CLIENT] 파일 내용 수집 성공 (비인코딩): {len(content)}문자")
                return content
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"[GITHUB_CLIENT] 파일 내용 수집 오류 ({response_time:.2f}초) - {file_path}: {e}")
            return None
    
    async def get_languages(self, repo_url: str) -> Dict[str, int]:
        """저장소 언어 통계 조회"""
        start_time = time.time()
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        print(f"[GITHUB_CLIENT] 언어 통계 요청: {owner}/{repo}")
        
        if not self.session:
            raise RuntimeError("GitHubClient must be used as async context manager")
        
        self.api_call_count += 1
        async with self.session.get(url) as response:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            print(f"[GITHUB_CLIENT] 언어 통계 응답: {response.status} ({response_time:.2f}초)")
            
            if response.status != 200:
                print(f"[GITHUB_CLIENT] 언어 통계 조회 실패: {response.status}")
                return {}
            
            languages_data = await response.json()
            total_bytes = sum(languages_data.values())
            
            print(f"[GITHUB_CLIENT] 언어 통계 수집 완료: {len(languages_data)}개 언어, 총 {total_bytes:,} bytes")
            for lang, bytes_count in sorted(languages_data.items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                print(f"[GITHUB_CLIENT]   - {lang}: {bytes_count:,} bytes ({percentage:.1f}%)")
            
            return languages_data
    
    async def get_commits(self, repo_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 커밋 정보 조회"""
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        
        if not self.session:
            raise RuntimeError("GitHubClient must be used as async context manager")
        
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return []
            
            data = await response.json()
            commits = []
            
            for commit in data:
                commits.append({
                    "sha": commit["sha"][:7],  # 짧은 해시
                    "message": commit["commit"]["message"],
                    "author": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"]
                })
            
            return commits