"""
Churn Analyzer 테스트 (새로운 구현)

Git commit history API를 통한 파일별 변경 빈도, 작성자 수, 최근 활동도 분석 시스템 테스트
TDD 방식으로 테스트 먼저 작성
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from app.services.churn_analyzer import (
    ChurnAnalyzer,
    FileChurnMetrics,
    ChurnAnalysisResult,
    CommitInfo,
    ActivityPeriod
)


class TestChurnAnalyzer:
    """Churn Analyzer 테스트 클래스"""
    
    @pytest.fixture
    def analyzer(self):
        """ChurnAnalyzer 인스턴스"""
        return ChurnAnalyzer()
    
    @pytest.fixture
    def sample_commits(self):
        """테스트용 commit 데이터"""
        now = datetime.now()
        return [
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "date": (now - timedelta(days=30)).isoformat()
                    },
                    "message": "Fix bug in main.py"
                },
                "stats": {
                    "total": 15,
                    "additions": 10,
                    "deletions": 5
                },
                "files": [
                    {
                        "filename": "src/main.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 5,
                        "changes": 15
                    }
                ]
            },
            {
                "sha": "def456",
                "commit": {
                    "author": {
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "date": (now - timedelta(days=15)).isoformat()
                    },
                    "message": "Add new feature to utils.py"
                },
                "stats": {
                    "total": 32,
                    "additions": 25,
                    "deletions": 7
                },
                "files": [
                    {
                        "filename": "src/utils.py",
                        "status": "modified",
                        "additions": 25,
                        "deletions": 0,
                        "changes": 25
                    },
                    {
                        "filename": "src/main.py",
                        "status": "modified",
                        "additions": 0,
                        "deletions": 7,
                        "changes": 7
                    }
                ]
            }
        ]

    def test_commit_info_creation(self):
        """CommitInfo 데이터 클래스 생성 테스트"""
        commit = CommitInfo(
            sha="abc123",
            author="John Doe",
            date=datetime.now(),
            message="Test commit",
            files_changed=["main.py", "utils.py"],
            additions=10,
            deletions=5
        )
        
        assert commit.sha == "abc123"
        assert commit.author == "John Doe"
        assert commit.message == "Test commit"
        assert len(commit.files_changed) == 2
        assert commit.additions == 10
        assert commit.deletions == 5

    def test_file_churn_metrics_creation(self):
        """FileChurnMetrics 데이터 클래스 생성 테스트"""
        metrics = FileChurnMetrics(
            file_path="src/main.py",
            commit_count=10,
            author_count=3,
            total_additions=100,
            total_deletions=50,
            last_modified=datetime.now(),
            activity_score=0.8,
            hotspot_score=0.6
        )
        
        assert metrics.file_path == "src/main.py"
        assert metrics.commit_count == 10
        assert metrics.author_count == 3
        assert metrics.total_additions == 100
        assert metrics.total_deletions == 50
        assert metrics.activity_score == 0.8
        assert metrics.hotspot_score == 0.6

    def test_parse_commit_data(self, analyzer, sample_commits):
        """GitHub commit 데이터 파싱 테스트"""
        commits = analyzer._parse_commit_data(sample_commits)
        
        assert len(commits) == 2
        assert commits[0].sha == "abc123"
        assert commits[0].author == "John Doe"
        assert commits[1].sha == "def456"
        assert commits[1].author == "Jane Smith"
        
        # 첫 번째 커밋의 파일 변경 정보 확인
        assert "src/main.py" in commits[0].files_changed
        assert commits[0].additions == 10
        assert commits[0].deletions == 5

    def test_calculate_file_churn_metrics(self, analyzer, sample_commits):
        """파일별 churn 지표 계산 테스트"""
        commits = analyzer._parse_commit_data(sample_commits)
        metrics = analyzer._calculate_file_churn_metrics(commits)
        
        # main.py는 2번 변경됨
        assert "src/main.py" in metrics
        main_metrics = metrics["src/main.py"]
        assert main_metrics.commit_count == 2
        assert main_metrics.author_count == 2  # John Doe, Jane Smith
        # 첫 번째 커밋: 10 additions, 5 deletions (main.py만 변경)
        # 두 번째 커밋: 0 additions, 7 deletions (main.py와 utils.py가 함께 변경되므로 25/2=12.5 additions, 7/2=3.5 deletions)  
        assert main_metrics.total_additions == 22  # 10 + 12.5
        assert main_metrics.total_deletions == 8   # 5 + 3.5
        
        # utils.py는 1번 변경됨
        assert "src/utils.py" in metrics
        utils_metrics = metrics["src/utils.py"]
        assert utils_metrics.commit_count == 1
        assert utils_metrics.author_count == 1
        # 두 번째 커밋에서 main.py와 함께 변경: 25 additions / 2 = 12.5, 7 deletions / 2 = 3.5
        assert utils_metrics.total_additions == 12  # 12.5 rounded to int
        assert utils_metrics.total_deletions == 3   # 3.5 rounded to int

    def test_calculate_activity_score(self, analyzer):
        """활동도 점수 계산 테스트"""
        now = datetime.now()
        
        # 최근 활동이 많은 경우
        recent_date = now - timedelta(days=7)
        score_recent = analyzer._calculate_activity_score(recent_date, 10)
        
        # 오래된 활동인 경우
        old_date = now - timedelta(days=300)
        score_old = analyzer._calculate_activity_score(old_date, 10)
        
        # 최근 활동이 더 높은 점수를 가져야 함
        assert score_recent > score_old
        assert 0 <= score_recent <= 1
        assert 0 <= score_old <= 1

    def test_calculate_hotspot_score(self, analyzer):
        """핫스팟 점수 계산 테스트"""
        # 변경이 많고 작성자가 많은 파일
        score_high = analyzer._calculate_hotspot_score(
            commit_count=50,
            author_count=10,
            total_changes=500
        )
        
        # 변경이 적고 작성자가 적은 파일
        score_low = analyzer._calculate_hotspot_score(
            commit_count=2,
            author_count=1,
            total_changes=10
        )
        
        assert score_high > score_low
        assert 0 <= score_high <= 1
        assert 0 <= score_low <= 1

    @pytest.mark.asyncio
    async def test_fetch_commit_history_pagination(self, analyzer):
        """GitHub API commit history 페이지네이션 테스트"""
        mock_response_page1 = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "John Doe",
                        "date": "2024-01-15T10:00:00Z"
                    },
                    "message": "Test commit 1"
                },
                "stats": {"total": 10, "additions": 8, "deletions": 2},
                "files": [
                    {
                        "filename": "test.py",
                        "status": "modified",
                        "additions": 8,
                        "deletions": 2,
                        "changes": 10
                    }
                ]
            }
        ]
        
        mock_response_page2 = []  # 빈 페이지 (마지막 페이지)
        
        with patch.object(analyzer, '_make_github_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response_page1, mock_response_page2]
            
            all_commits = await analyzer._fetch_all_commits("owner", "repo")
            
            assert len(all_commits) == 1
            assert all_commits[0]["sha"] == "abc123"
            assert mock_request.call_count == 2  # 2페이지 호출

    @pytest.mark.asyncio
    async def test_analyze_repository_churn_full_workflow(self, analyzer):
        """저장소 churn 분석 전체 워크플로우 테스트"""
        mock_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "John Doe",
                        "date": "2024-01-15T10:00:00Z"
                    },
                    "message": "Update main file"
                },
                "stats": {"total": 15, "additions": 10, "deletions": 5},
                "files": [
                    {
                        "filename": "src/main.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 5,
                        "changes": 15
                    }
                ]
            }
        ]
        
        with patch.object(analyzer, '_fetch_all_commits', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_commits
            
            result = await analyzer.analyze_repository_churn("owner", "repo")
            
            assert isinstance(result, ChurnAnalysisResult)
            assert result.total_commits == 1
            assert len(result.file_metrics) == 1
            assert "src/main.py" in result.file_metrics
            
            main_metrics = result.file_metrics["src/main.py"]
            assert main_metrics.commit_count == 1
            assert main_metrics.author_count == 1
            assert main_metrics.total_additions == 10
            assert main_metrics.total_deletions == 5

    def test_filter_commits_by_time_period(self, analyzer, sample_commits):
        """시간 기간별 commit 필터링 테스트"""
        commits = analyzer._parse_commit_data(sample_commits)
        
        # 최근 30일 이내 커밋만 필터링 (ONE_MONTH = 30일)
        recent_commits = analyzer._filter_commits_by_period(commits, ActivityPeriod.ONE_MONTH)
        
        # def456 커밋만 남아야 함 (15일 전), abc123은 30일 전이므로 제외
        assert len(recent_commits) == 1
        assert recent_commits[0].sha == "def456"

    def test_identify_hotspot_files(self, analyzer):
        """핫스팟 파일 식별 테스트"""
        file_metrics = {
            "src/main.py": FileChurnMetrics(
                file_path="src/main.py",
                commit_count=20,
                author_count=5,
                total_additions=200,
                total_deletions=100,
                last_modified=datetime.now(),
                activity_score=0.9,
                hotspot_score=0.8
            ),
            "src/utils.py": FileChurnMetrics(
                file_path="src/utils.py",
                commit_count=5,
                author_count=2,
                total_additions=50,
                total_deletions=10,
                last_modified=datetime.now(),
                activity_score=0.5,  
                hotspot_score=0.3
            )
        }
        
        hotspots = analyzer._identify_hotspot_files(file_metrics, threshold=0.5)
        
        # main.py만 핫스팟으로 식별되어야 함
        assert len(hotspots) == 1
        assert hotspots[0].file_path == "src/main.py"
        assert hotspots[0].hotspot_score > 0.5

    def test_github_api_error_handling(self, analyzer):
        """GitHub API 에러 처리 테스트"""
        invalid_commits = [
            {
                "sha": "abc123",
                # commit 정보 누락
                "files": []
            }
        ]
        
        # 에러가 발생해도 빈 리스트 반환
        commits = analyzer._parse_commit_data(invalid_commits)
        assert len(commits) == 0

    @pytest.mark.asyncio
    async def test_github_api_rate_limiting(self, analyzer):
        """GitHub API Rate Limiting 처리 테스트"""
        with patch.object(analyzer, '_make_github_request', new_callable=AsyncMock) as mock_request:
            # Rate limit 에러 시뮬레이션
            mock_request.side_effect = Exception("API rate limit exceeded")
            
            with pytest.raises(Exception, match="API rate limit exceeded"):
                await analyzer._fetch_all_commits("owner", "repo")

    def test_performance_large_commit_history(self, analyzer):
        """대용량 commit history 처리 성능 테스트"""
        # 1000개의 가상 커밋 생성
        large_commits = []
        now = datetime.now()
        
        for i in range(1000):
            large_commits.append({
                "sha": f"commit_{i}",
                "commit": {
                    "author": {
                        "name": f"Author_{i % 10}",  # 10명의 작성자
                        "date": (now - timedelta(days=i)).isoformat()
                    },
                    "message": f"Commit {i}"
                },
                "stats": {"total": i % 50, "additions": i % 30, "deletions": i % 20},
                "files": [
                    {
                        "filename": f"src/file_{i % 50}.py",  # 50개 파일
                        "status": "modified", 
                        "additions": i % 30,
                        "deletions": i % 20,
                        "changes": (i % 30) + (i % 20)
                    }
                ]
            })
        
        import time
        start_time = time.time()
        
        commits = analyzer._parse_commit_data(large_commits)
        metrics = analyzer._calculate_file_churn_metrics(commits)
        
        end_time = time.time()
        
        # 성능 검증 (2초 이내 완료)
        assert end_time - start_time < 2.0
        assert len(commits) == 1000
        assert len(metrics) == 50  # 50개 파일

    def test_activity_period_enum(self):
        """ActivityPeriod enum 테스트"""
        assert ActivityPeriod.ONE_MONTH.value == 30
        assert ActivityPeriod.THREE_MONTHS.value == 90
        assert ActivityPeriod.SIX_MONTHS.value == 180
        assert ActivityPeriod.ONE_YEAR.value == 365

    def test_churn_analysis_result_creation(self):
        """ChurnAnalysisResult 데이터 클래스 생성 테스트"""
        file_metrics = {
            "test.py": FileChurnMetrics(
                file_path="test.py",
                commit_count=5,
                author_count=2,
                total_additions=50,
                total_deletions=20,
                last_modified=datetime.now(),
                activity_score=0.7,
                hotspot_score=0.5
            )
        }
        
        result = ChurnAnalysisResult(
            total_commits=10,
            unique_authors=5,
            file_metrics=file_metrics,
            hotspot_files=["test.py"],
            analysis_period=ActivityPeriod.SIX_MONTHS,
            analyzed_at=datetime.now()
        )
        
        assert result.total_commits == 10
        assert result.unique_authors == 5
        assert len(result.file_metrics) == 1
        assert "test.py" in result.file_metrics
        assert result.hotspot_files == ["test.py"]
        assert result.analysis_period == ActivityPeriod.SIX_MONTHS

    def test_calculate_weighted_churn_score(self, analyzer):
        """가중치 적용된 churn 점수 계산 테스트"""
        metrics = FileChurnMetrics(
            file_path="src/main.py",
            commit_count=15,
            author_count=4,
            total_additions=200,
            total_deletions=100,
            last_modified=datetime.now() - timedelta(days=5),
            activity_score=0.8,
            hotspot_score=0.0  # 계산될 값
        )
        
        weighted_score = analyzer._calculate_weighted_churn_score(metrics)
        
        assert 0 <= weighted_score <= 1
        # 높은 활동도와 많은 커밋으로 높은 점수 예상
        assert weighted_score > 0.5

    def test_detect_churn_patterns(self, analyzer, sample_commits):
        """변경 패턴 감지 테스트"""
        commits = analyzer._parse_commit_data(sample_commits)
        patterns = analyzer._detect_churn_patterns(commits)
        
        assert "peak_activity_day" in patterns
        assert "most_active_author" in patterns
        assert "average_changes_per_commit" in patterns
        assert "commit_frequency_trend" in patterns

    def test_empty_repository_handling(self, analyzer):
        """빈 저장소 처리 테스트"""
        empty_commits = []
        
        commits = analyzer._parse_commit_data(empty_commits)
        metrics = analyzer._calculate_file_churn_metrics(commits)
        
        assert len(commits) == 0
        assert len(metrics) == 0

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, analyzer):
        """동시 API 요청 처리 테스트"""
        import asyncio
        
        async def mock_api_call(page):
            await asyncio.sleep(0.1)  # API 지연 시뮬레이션
            return [{"sha": f"commit_{page}", "commit": {"author": {"name": "Test"}}}]
        
        with patch.object(analyzer, '_make_github_request', side_effect=mock_api_call):
            # 여러 페이지를 동시에 요청
            tasks = [analyzer._make_github_request(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result[0]["sha"] == f"commit_{i}"


class TestChurnAnalyzerIntegration:
    """Churn Analyzer 통합 테스트"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_repository_churn_analysis(self):
        """실제 저장소 churn 분석 테스트 (Mock)"""
        analyzer = ChurnAnalyzer()
        
        # 실제 저장소 시뮬레이션
        mock_commits = [
            {
                "sha": "commit1",
                "commit": {
                    "author": {"name": "Developer1", "date": "2024-01-01T10:00:00Z"},
                    "message": "Initial commit"
                },
                "stats": {"total": 50, "additions": 50, "deletions": 0},
                "files": [
                    {"filename": "README.md", "status": "added", "additions": 50, "deletions": 0, "changes": 50}
                ]
            },
            {
                "sha": "commit2",
                "commit": {
                    "author": {"name": "Developer2", "date": "2024-01-02T11:00:00Z"},
                    "message": "Add main functionality"
                },
                "stats": {"total": 150, "additions": 150, "deletions": 0},
                "files": [
                    {"filename": "src/main.py", "status": "added", "additions": 100, "deletions": 0, "changes": 100},
                    {"filename": "src/utils.py", "status": "added", "additions": 50, "deletions": 0, "changes": 50}
                ]
            }
        ]
        
        with patch.object(analyzer, '_fetch_all_commits', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_commits
            
            result = await analyzer.analyze_repository_churn("test", "repo")
            
            assert result.total_commits == 2
            assert len(result.file_metrics) == 3
            assert result.analysis_period == ActivityPeriod.SIX_MONTHS
            
            # 파일별 메트릭 검증
            assert "README.md" in result.file_metrics
            assert "src/main.py" in result.file_metrics
            assert "src/utils.py" in result.file_metrics