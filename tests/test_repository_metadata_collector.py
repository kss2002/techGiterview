"""
Repository Metadata Collector 테스트

GitHub GraphQL API v4를 활용한 저장소 메타정보 수집 시스템 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.repository_metadata_collector import (
    RepositoryMetadataCollector,
    RepositoryMetadata,
    LanguageStats,
    ReleaseInfo,
    IssueStats
)


class TestRepositoryMetadataCollector:
    """Repository Metadata Collector 테스트 클래스"""
    
    @pytest.fixture
    def mock_github_token(self):
        """테스트용 GitHub 토큰"""
        return "ghp_test_token_12345"
    
    @pytest.fixture
    def collector(self, mock_github_token):
        """RepositoryMetadataCollector 인스턴스"""
        return RepositoryMetadataCollector(github_token=mock_github_token)
    
    @pytest.fixture
    def sample_repository_url(self):
        """테스트용 저장소 URL"""
        return "https://github.com/octocat/Hello-World"
    
    @pytest.fixture
    def sample_graphql_response(self):
        """GitHub GraphQL API 응답 예시"""
        return {
            "data": {
                "repository": {
                    "name": "Hello-World",
                    "owner": {"login": "octocat"},
                    "description": "My first repository on GitHub!",
                    "stargazerCount": 1500,
                    "forkCount": 123,
                    "watchers": {"totalCount": 89},
                    "primaryLanguage": {"name": "Python"},
                    "languages": {
                        "totalSize": 125000,
                        "edges": [
                            {"size": 75000, "node": {"name": "Python"}},
                            {"size": 30000, "node": {"name": "JavaScript"}},
                            {"size": 20000, "node": {"name": "HTML"}}
                        ]
                    },
                    "defaultBranchRef": {
                        "name": "main",
                        "target": {
                            "history": {
                                "totalCount": 234
                            }
                        }
                    },
                    "releases": {
                        "totalCount": 5,
                        "nodes": [
                            {
                                "name": "v2.0.0",
                                "tagName": "v2.0.0",
                                "publishedAt": "2024-01-15T10:30:00Z"
                            }
                        ]
                    },
                    "issues": {
                        "totalCount": 45
                    },
                    "pullRequests": {
                        "totalCount": 78
                    },
                    "createdAt": "2023-01-01T00:00:00Z",
                    "updatedAt": "2024-01-20T15:45:00Z"
                }
            }
        }
    
    def test_parse_repository_url_valid(self, collector, sample_repository_url):
        """유효한 GitHub URL 파싱 테스트"""
        owner, repo = collector._parse_repository_url(sample_repository_url)
        
        assert owner == "octocat"
        assert repo == "Hello-World"
    
    def test_parse_repository_url_invalid(self, collector):
        """유효하지 않은 URL 파싱 테스트"""
        invalid_urls = [
            "https://gitlab.com/user/repo",
            "https://github.com/user",
            "not-a-url",
            ""
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid GitHub repository URL"):
                collector._parse_repository_url(invalid_url)
    
    @pytest.mark.asyncio
    async def test_fetch_repository_metadata_success(self, collector, sample_repository_url, sample_graphql_response):
        """저장소 메타정보 수집 성공 테스트"""
        with patch.object(collector, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_graphql_response
            
            metadata = await collector.fetch_repository_metadata(sample_repository_url)
            
            assert isinstance(metadata, RepositoryMetadata)
            assert metadata.name == "Hello-World"
            assert metadata.owner == "octocat"
            assert metadata.description == "My first repository on GitHub!"
            assert metadata.stars == 1500
            assert metadata.forks == 123
            assert metadata.watchers == 89
            assert metadata.primary_language == "Python"
            assert metadata.commit_count == 234
            assert metadata.branch_name == "main"
            assert metadata.release_count == 5
            assert metadata.issue_count == 45
            assert metadata.pr_count == 78
    
    @pytest.mark.asyncio
    async def test_fetch_repository_metadata_not_found(self, collector):
        """존재하지 않는 저장소 테스트"""
        not_found_response = {
            "data": {
                "repository": None
            },
            "errors": [
                {"message": "Could not resolve to a Repository with the name 'nonexistent/repo'."}
            ]
        }
        
        with patch.object(collector, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = not_found_response
            
            with pytest.raises(ValueError, match="Repository not found"):
                await collector.fetch_repository_metadata("https://github.com/nonexistent/repo")
    
    def test_calculate_language_stats(self, collector, sample_graphql_response):
        """언어 통계 계산 테스트"""
        languages_data = sample_graphql_response["data"]["repository"]["languages"]
        language_stats = collector._calculate_language_stats(languages_data)
        
        assert isinstance(language_stats, LanguageStats)
        assert language_stats.total_size == 125000
        assert len(language_stats.languages) == 3
        assert language_stats.languages["Python"] == 60.0  # 75000/125000 * 100
        assert language_stats.languages["JavaScript"] == 24.0  # 30000/125000 * 100
        assert language_stats.languages["HTML"] == 16.0  # 20000/125000 * 100
    
    def test_parse_release_info(self, collector, sample_graphql_response):
        """릴리즈 정보 파싱 테스트"""
        releases_data = sample_graphql_response["data"]["repository"]["releases"]
        release_info = collector._parse_release_info(releases_data)
        
        assert isinstance(release_info, ReleaseInfo)
        assert release_info.total_count == 5
        assert len(release_info.latest_releases) == 1
        assert release_info.latest_releases[0]["name"] == "v2.0.0"
        assert release_info.latest_releases[0]["tag_name"] == "v2.0.0"
    
    def test_calculate_issue_stats(self, collector, sample_graphql_response):
        """이슈 통계 계산 테스트"""
        repo_data = sample_graphql_response["data"]["repository"]
        issue_stats = collector._calculate_issue_stats(repo_data)
        
        assert isinstance(issue_stats, IssueStats)
        assert issue_stats.total_issues == 45
        assert issue_stats.total_prs == 78
        assert issue_stats.issue_pr_ratio == pytest.approx(0.577, rel=1e-3)  # 45/78
    
    @pytest.mark.asyncio
    async def test_collect_with_rate_limiting(self, collector, sample_repository_url):
        """Rate Limiting 적용 테스트"""
        with patch.object(collector, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            # Rate limit 에러를 직접 발생시키도록 설정
            async def mock_graphql_error(*args, **kwargs):
                raise Exception("GitHub API rate limit exceeded: API rate limit exceeded")
            
            mock_request.side_effect = mock_graphql_error
            
            with pytest.raises(Exception, match="API rate limit"):
                await collector.fetch_repository_metadata(sample_repository_url)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, collector):
        """동시 요청 처리 테스트"""
        urls = [
            "https://github.com/user1/repo1",
            "https://github.com/user2/repo2", 
            "https://github.com/user3/repo3"
        ]
        
        mock_responses = [
            {"data": {"repository": {"name": "repo1", "owner": {"login": "user1"}}}},
            {"data": {"repository": {"name": "repo2", "owner": {"login": "user2"}}}},
            {"data": {"repository": {"name": "repo3", "owner": {"login": "user3"}}}}
        ]
        
        with patch.object(collector, '_make_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = mock_responses
            
            tasks = [collector.fetch_repository_metadata(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 3
            assert all(not isinstance(result, Exception) for result in results)
    
    def test_jwt_token_validation(self, mock_github_token):
        """JWT 토큰 검증 테스트"""
        # 유효한 토큰
        collector = RepositoryMetadataCollector(github_token=mock_github_token)
        assert collector.github_token == mock_github_token
        
        # 빈 토큰
        with pytest.raises(ValueError, match="GitHub token is required"):
            RepositoryMetadataCollector(github_token="")
        
        # None 토큰
        with pytest.raises(ValueError, match="GitHub token is required"):
            RepositoryMetadataCollector(github_token=None)


class TestRepositoryMetadata:
    """RepositoryMetadata 데이터 클래스 테스트"""
    
    def test_repository_metadata_creation(self):
        """RepositoryMetadata 생성 테스트"""
        metadata = RepositoryMetadata(
            name="test-repo",
            owner="test-user",
            description="Test repository",
            stars=100,
            forks=20,
            watchers=50,
            primary_language="Python",
            language_stats=LanguageStats(
                total_size=10000,
                languages={"Python": 80.0, "JavaScript": 20.0}
            ),
            commit_count=150,
            branch_name="main",
            release_info=ReleaseInfo(
                total_count=3,
                latest_releases=[{"name": "v1.0.0", "tag_name": "v1.0.0"}]
            ),
            issue_stats=IssueStats(
                total_issues=25,
                total_prs=15,
                issue_pr_ratio=1.67
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert metadata.name == "test-repo"
        assert metadata.owner == "test-user"
        assert metadata.stars == 100
        assert isinstance(metadata.language_stats, LanguageStats)
        assert isinstance(metadata.release_info, ReleaseInfo)
        assert isinstance(metadata.issue_stats, IssueStats)
    
    def test_repository_metadata_serialization(self):
        """RepositoryMetadata 직렬화 테스트"""
        metadata = RepositoryMetadata(
            name="test-repo",
            owner="test-user",
            description="Test repository",
            stars=100,
            forks=20,
            watchers=50,
            primary_language="Python"
        )
        
        # to_dict 메서드가 있다면 테스트
        if hasattr(metadata, 'to_dict'):
            data_dict = metadata.to_dict()
            assert isinstance(data_dict, dict)
            assert data_dict["name"] == "test-repo"
            assert data_dict["owner"] == "test-user"


@pytest.mark.integration
class TestRepositoryMetadataCollectorIntegration:
    """통합 테스트 (실제 GitHub API 호출)"""
    
    @pytest.mark.skip(reason="Requires real GitHub token")
    @pytest.mark.asyncio
    async def test_real_github_api_call(self):
        """실제 GitHub API 호출 테스트 (토큰 필요)"""
        # 실제 GitHub 토큰이 환경변수에 있을 때만 실행
        import os
        token = os.getenv("GITHUB_TOKEN")
        
        if not token:
            pytest.skip("GITHUB_TOKEN environment variable not set")
        
        collector = RepositoryMetadataCollector(github_token=token)
        metadata = await collector.fetch_repository_metadata(
            "https://github.com/octocat/Hello-World"
        )
        
        assert metadata.name == "Hello-World"
        assert metadata.owner == "octocat"
        assert metadata.stars > 0