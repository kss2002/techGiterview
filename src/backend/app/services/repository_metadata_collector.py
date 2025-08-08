"""
Repository Metadata Collector

GitHub GraphQL API v4를 활용한 저장소 메타정보 수집 시스템
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import json
from urllib.parse import urlparse


@dataclass
class LanguageStats:
    """언어 통계 정보"""
    total_size: int
    languages: Dict[str, float] = field(default_factory=dict)  # 언어명: 퍼센트
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_size": self.total_size,
            "languages": self.languages
        }


@dataclass  
class ReleaseInfo:
    """릴리즈 정보"""
    total_count: int
    latest_releases: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_count": self.total_count,
            "latest_releases": self.latest_releases
        }


@dataclass
class IssueStats:
    """이슈 및 PR 통계"""
    total_issues: int
    total_prs: int
    issue_pr_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_issues": self.total_issues,
            "total_prs": self.total_prs,
            "issue_pr_ratio": self.issue_pr_ratio
        }


@dataclass
class RepositoryMetadata:
    """저장소 메타데이터"""
    name: str
    owner: str
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    primary_language: Optional[str] = None
    language_stats: Optional[LanguageStats] = None
    commit_count: int = 0
    branch_name: str = "main"
    release_count: int = 0
    release_info: Optional[ReleaseInfo] = None
    issue_count: int = 0
    pr_count: int = 0
    issue_stats: Optional[IssueStats] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = {
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "watchers": self.watchers,
            "primary_language": self.primary_language,
            "commit_count": self.commit_count,
            "branch_name": self.branch_name,
            "release_count": self.release_count,
            "issue_count": self.issue_count,
            "pr_count": self.pr_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if self.language_stats:
            data["language_stats"] = self.language_stats.to_dict()
        if self.release_info:
            data["release_info"] = self.release_info.to_dict()
        if self.issue_stats:
            data["issue_stats"] = self.issue_stats.to_dict()
            
        return data


class RepositoryMetadataCollector:
    """GitHub 저장소 메타데이터 수집기"""
    
    def __init__(self, github_token: str):
        """
        초기화
        
        Args:
            github_token: GitHub Personal Access Token
        """
        if not github_token:
            raise ValueError("GitHub token is required")
            
        self.github_token = github_token
        self.base_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting을 위한 세마포어 (동시 요청 제한)
        self.semaphore = asyncio.Semaphore(10)
    
    def _parse_repository_url(self, repo_url: str) -> tuple[str, str]:
        """
        GitHub 저장소 URL에서 owner와 repo 이름 추출
        
        Args:
            repo_url: GitHub 저장소 URL
            
        Returns:
            tuple: (owner, repo_name)
            
        Raises:
            ValueError: 유효하지 않은 URL인 경우
        """
        if not repo_url:
            raise ValueError("Invalid GitHub repository URL: empty URL")
            
        parsed = urlparse(repo_url)
        
        if parsed.netloc != "github.com":
            raise ValueError("Invalid GitHub repository URL: not a GitHub URL")
            
        path_parts = parsed.path.strip("/").split("/")
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL: missing owner or repository name")
            
        owner = path_parts[0]
        repo = path_parts[1]
        
        # .git 확장자 제거
        if repo.endswith(".git"):
            repo = repo[:-4]
            
        return owner, repo
    
    async def _make_graphql_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        GitHub GraphQL API 요청
        
        Args:
            query: GraphQL 쿼리
            variables: 쿼리 변수
            
        Returns:
            API 응답 데이터
            
        Raises:
            Exception: API 요청 실패 시
        """
        async with self.semaphore:
            payload = {
                "query": query,
                "variables": variables
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response_data = await response.json()
                    
                    if response.status != 200:
                        raise Exception(f"GitHub API request failed: {response.status}")
                    
                    if "errors" in response_data:
                        error_msg = response_data["errors"][0]["message"]
                        if "rate limit" in error_msg.lower():
                            raise Exception(f"GitHub API rate limit exceeded: {error_msg}")
                        raise Exception(f"GitHub API error: {error_msg}")
                    
                    return response_data
    
    def _build_repository_query(self) -> str:
        """저장소 정보 조회를 위한 GraphQL 쿼리 생성"""
        return """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            name
            owner {
              login
            }
            description
            stargazerCount
            forkCount
            watchers {
              totalCount
            }
            primaryLanguage {
              name
            }
            languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
              totalSize
              edges {
                size
                node {
                  name
                }
              }
            }
            defaultBranchRef {
              name
              target {
                ... on Commit {
                  history {
                    totalCount
                  }
                }
              }
            }
            releases(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
              totalCount
              nodes {
                name
                tagName
                publishedAt
              }
            }
            issues {
              totalCount
            }
            pullRequests {
              totalCount
            }
            createdAt
            updatedAt
          }
        }
        """
    
    def _calculate_language_stats(self, languages_data: Dict[str, Any]) -> LanguageStats:
        """언어 통계 계산"""
        total_size = languages_data.get("totalSize", 0)
        languages = {}
        
        for edge in languages_data.get("edges", []):
            size = edge.get("size", 0)
            name = edge.get("node", {}).get("name", "Unknown")
            
            if total_size > 0:
                percentage = (size / total_size) * 100
                languages[name] = round(percentage, 1)
        
        return LanguageStats(
            total_size=total_size,
            languages=languages
        )
    
    def _parse_release_info(self, releases_data: Dict[str, Any]) -> ReleaseInfo:
        """릴리즈 정보 파싱"""
        total_count = releases_data.get("totalCount", 0)
        latest_releases = []
        
        for release in releases_data.get("nodes", []):
            latest_releases.append({
                "name": release.get("name", ""),
                "tag_name": release.get("tagName", ""),
                "published_at": release.get("publishedAt", "")
            })
        
        return ReleaseInfo(
            total_count=total_count,
            latest_releases=latest_releases
        )
    
    def _calculate_issue_stats(self, repo_data: Dict[str, Any]) -> IssueStats:
        """이슈 및 PR 통계 계산"""
        total_issues = repo_data.get("issues", {}).get("totalCount", 0)
        total_prs = repo_data.get("pullRequests", {}).get("totalCount", 0)
        
        # Issue/PR 비율 계산 (0으로 나누기 방지)
        issue_pr_ratio = total_issues / total_prs if total_prs > 0 else 0
        
        return IssueStats(
            total_issues=total_issues,
            total_prs=total_prs,
            issue_pr_ratio=round(issue_pr_ratio, 3)
        )
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """ISO 형식 날짜 문자열을 datetime 객체로 변환"""
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    async def fetch_repository_metadata(self, repo_url: str) -> RepositoryMetadata:
        """
        저장소 메타데이터 수집
        
        Args:
            repo_url: GitHub 저장소 URL
            
        Returns:
            RepositoryMetadata: 수집된 메타데이터
            
        Raises:
            ValueError: 저장소를 찾을 수 없거나 URL이 유효하지 않은 경우
        """
        owner, repo_name = self._parse_repository_url(repo_url)
        
        query = self._build_repository_query()
        variables = {"owner": owner, "name": repo_name}
        
        response_data = await self._make_graphql_request(query, variables)
        
        repo_data = response_data.get("data", {}).get("repository")
        if not repo_data:
            raise ValueError(f"Repository not found: {owner}/{repo_name}")
        
        # 언어 통계 계산
        language_stats = None
        if "languages" in repo_data:
            language_stats = self._calculate_language_stats(repo_data["languages"])
        
        # 릴리즈 정보 파싱
        release_info = None
        if "releases" in repo_data:
            release_info = self._parse_release_info(repo_data["releases"])
        
        # 이슈 통계 계산
        issue_stats = self._calculate_issue_stats(repo_data)
        
        # 커밋 수 및 브랜치 정보
        commit_count = 0
        branch_name = "main"
        if "defaultBranchRef" in repo_data and repo_data["defaultBranchRef"]:
            branch_name = repo_data["defaultBranchRef"].get("name", "main")
            if "target" in repo_data["defaultBranchRef"]:
                commit_count = repo_data["defaultBranchRef"]["target"].get("history", {}).get("totalCount", 0)
        
        return RepositoryMetadata(
            name=repo_data.get("name", ""),
            owner=repo_data.get("owner", {}).get("login", ""),
            description=repo_data.get("description"),
            stars=repo_data.get("stargazerCount", 0),
            forks=repo_data.get("forkCount", 0),
            watchers=repo_data.get("watchers", {}).get("totalCount", 0),
            primary_language=repo_data.get("primaryLanguage", {}).get("name") if repo_data.get("primaryLanguage") else None,
            language_stats=language_stats,
            commit_count=commit_count,
            branch_name=branch_name,
            release_count=release_info.total_count if release_info else 0,
            release_info=release_info,
            issue_count=issue_stats.total_issues,
            pr_count=issue_stats.total_prs,
            issue_stats=issue_stats,
            created_at=self._parse_datetime(repo_data.get("createdAt", "")),
            updated_at=self._parse_datetime(repo_data.get("updatedAt", ""))
        )
    
    async def collect_multiple_repositories(self, repo_urls: List[str]) -> List[RepositoryMetadata]:
        """
        여러 저장소의 메타데이터를 병렬로 수집
        
        Args:
            repo_urls: GitHub 저장소 URL 리스트
            
        Returns:
            수집된 메타데이터 리스트
        """
        tasks = [self.fetch_repository_metadata(url) for url in repo_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 결과만 반환 (예외는 로깅 후 제외)
        metadata_list = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to collect metadata for {repo_urls[i]}: {result}")
            else:
                metadata_list.append(result)
        
        return metadata_list