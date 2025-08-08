"""
Git 변경 이력(Churn) 분석 시스템 테스트

TDD 방식으로 먼저 테스트를 작성하고, 이후 실제 구현을 진행합니다.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

# 구현 예정 모듈들
# from app.services.churn_analyzer import RuleBasedChurnAnalyzer


class TestRuleBasedChurnAnalyzer:
    """Git 변경 이력 분석기 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """테스트용 Churn 분석기 인스턴스"""
        from app.services.churn_analyzer import RuleBasedChurnAnalyzer
        return RuleBasedChurnAnalyzer()
    
    @pytest.fixture
    def sample_commits(self):
        """테스트용 커밋 데이터 샘플"""
        now = datetime.now()
        return [
            {
                "sha": "abc123",
                "author": "developer1",
                "date": (now - timedelta(days=1)).isoformat(),
                "message": "Fix critical bug in authentication",
                "additions": 15,
                "deletions": 8
            },
            {
                "sha": "def456", 
                "author": "developer2",
                "date": (now - timedelta(days=7)).isoformat(),
                "message": "Add new feature for user management",
                "additions": 120,
                "deletions": 5
            },
            {
                "sha": "ghi789",
                "author": "developer1",
                "date": (now - timedelta(days=30)).isoformat(),
                "message": "Refactor authentication module",
                "additions": 45,
                "deletions": 60
            },
            {
                "sha": "jkl012",
                "author": "developer3",
                "date": (now - timedelta(days=90)).isoformat(),
                "message": "Initial implementation",
                "additions": 200,
                "deletions": 0
            },
            {
                "sha": "mno345",
                "author": "developer2",
                "date": (now - timedelta(days=120)).isoformat(),
                "message": "Setup project structure",
                "additions": 50,
                "deletions": 2
            }
        ]
    
    @pytest.fixture
    def file_commit_data(self):
        """파일별 커밋 데이터"""
        return {
            "src/auth.py": [
                {"date": "2024-01-01", "author": "dev1", "additions": 10, "deletions": 5},
                {"date": "2024-01-15", "author": "dev2", "additions": 20, "deletions": 8},
                {"date": "2024-02-01", "author": "dev1", "additions": 5, "deletions": 15}
            ],
            "src/main.py": [
                {"date": "2024-01-01", "author": "dev1", "additions": 100, "deletions": 0},
                {"date": "2024-01-10", "author": "dev1", "additions": 15, "deletions": 5}
            ],
            "src/utils.py": [
                {"date": "2024-01-01", "author": "dev3", "additions": 50, "deletions": 0}
            ]
        }

    def test_calculate_recent_activity(self, analyzer, sample_commits):
        """최근 활동도 계산 테스트"""
        # Given: 다양한 시점의 커밋들
        
        # When: 최근 3개월 활동도 계산
        recent_activity = analyzer._calculate_recent_activity(sample_commits)
        
        # Then: 최근 3개월 내 커밋 비율이 계산되어야 함
        assert 0.0 <= recent_activity <= 1.0
        # 5개 커밋 중 3개가 최근 3개월 내 → 3/5 = 0.6
        assert abs(recent_activity - 0.6) < 0.1

    def test_calculate_change_velocity(self, analyzer, sample_commits):
        """변경 속도 계산 테스트"""
        # Given: 시간별 커밋 데이터
        
        # When: 변경 속도 계산
        velocity = analyzer._calculate_change_velocity(sample_commits)
        
        # Then: 합리적인 변경 속도가 계산되어야 함
        assert velocity > 0
        # 최근 커밋일수록 높은 가중치

    def test_calculate_author_diversity(self, analyzer, sample_commits):
        """작성자 다양성 계산 테스트"""
        # Given: 여러 작성자의 커밋들
        
        # When: 작성자 다양성 계산
        diversity = analyzer._calculate_author_diversity(sample_commits)
        
        # Then: 올바른 작성자 수가 반환되어야 함
        assert diversity == 3  # developer1, developer2, developer3

    def test_identify_hotspots_statistical(self, analyzer, file_commit_data):
        """통계적 핫스팟 식별 테스트"""
        # Given: 파일별 커밋 통계
        churn_metrics = {}
        for file_path, commits in file_commit_data.items():
            churn_metrics[file_path] = {
                "commit_frequency": len(commits),
                "recent_activity": 0.8 if len(commits) > 2 else 0.3,
                "change_intensity": sum(c["additions"] + c["deletions"] for c in commits)
            }
        
        # When: 핫스팟 식별
        hotspots = analyzer._identify_hotspots(churn_metrics)
        
        # Then: 변경이 잦은 파일이 핫스팟으로 식별되어야 함
        assert "src/auth.py" in hotspots  # 3번의 커밋으로 가장 많음

    def test_identify_stable_files(self, analyzer, file_commit_data):
        """안정적인 파일 식별 테스트"""
        # Given: 파일별 커밋 통계
        churn_metrics = {}
        for file_path, commits in file_commit_data.items():
            churn_metrics[file_path] = {
                "commit_frequency": len(commits),
                "recent_activity": 0.1 if len(commits) == 1 else 0.8,
                "stability_score": 1.0 / len(commits)  # 커밋 수에 반비례
            }
        
        # When: 안정적인 파일 식별
        stable_files = analyzer._identify_stable_files(churn_metrics)
        
        # Then: 변경이 적은 파일이 안정적으로 식별되어야 함
        assert "src/utils.py" in stable_files  # 1번의 커밋으로 가장 안정적

    def test_calculate_stability_score(self, analyzer, sample_commits):
        """안정성 점수 계산 테스트"""
        # Given: 커밋 이력
        
        # When: 안정성 점수 계산
        stability = analyzer._calculate_stability_score(sample_commits)
        
        # Then: 0-1 범위의 안정성 점수가 반환되어야 함
        assert 0.0 <= stability <= 1.0
        # 최근 커밋이 많을수록 낮은 안정성

    @pytest.mark.asyncio
    async def test_analyze_file_churn_metrics(self, analyzer):
        """파일별 변경 메트릭 분석 테스트"""
        # Given: 저장소 URL과 파일 경로들
        repo_url = "https://github.com/test/repo"
        file_paths = ["src/main.py", "src/auth.py", "src/utils.py"]
        
        # Mock GitHub API 응답
        analyzer.github_client = AsyncMock()
        analyzer.github_client.get_file_commit_history.return_value = [
            {"author": "dev1", "date": "2024-01-01T10:00:00Z", "additions": 10, "deletions": 5},
            {"author": "dev2", "date": "2024-01-15T10:00:00Z", "additions": 20, "deletions": 8}
        ]
        
        # When: 파일별 churn 메트릭 분석
        result = await analyzer.analyze_file_churn_metrics(repo_url, file_paths)
        
        # Then: 올바른 메트릭이 계산되어야 함
        assert "file_churn_metrics" in result
        assert "hotspot_files" in result
        assert "stable_files" in result
        
        # 각 파일의 메트릭 확인
        for file_path in file_paths:
            if file_path in result["file_churn_metrics"]:
                metrics = result["file_churn_metrics"][file_path]
                assert "commit_frequency" in metrics
                assert "recent_activity" in metrics
                assert "author_diversity" in metrics
                assert "change_velocity" in metrics
                assert "stability_score" in metrics

    def test_detect_bug_fix_patterns(self, analyzer):
        """버그 수정 패턴 감지 테스트"""
        # Given: 버그 수정 관련 커밋 메시지들
        commit_messages = [
            "Fix critical bug in authentication",
            "Hotfix for null pointer exception",
            "Bug fix: resolve memory leak",
            "Add new feature for user management",
            "Refactor authentication module"
        ]
        
        # When: 버그 수정 패턴 감지
        bug_fixes = analyzer._detect_bug_fix_commits(commit_messages)
        
        # Then: 버그 수정 커밋들이 올바르게 감지되어야 함
        assert bug_fixes == 3  # "Fix", "Hotfix", "Bug fix" 패턴

    def test_detect_refactor_patterns(self, analyzer):
        """리팩토링 패턴 감지 테스트"""
        # Given: 리팩토링 관련 커밋 메시지들
        commit_messages = [
            "Refactor authentication module",
            "Cleanup code in user service",
            "Restructure project layout",
            "Add new feature for user management",
            "Fix critical bug"
        ]
        
        # When: 리팩토링 패턴 감지
        refactor_commits = analyzer._detect_refactor_commits(commit_messages)
        
        # Then: 리팩토링 커밋들이 올바르게 감지되어야 함
        assert refactor_commits == 3  # "Refactor", "Cleanup", "Restructure"

    def test_analyze_change_patterns(self, analyzer, file_commit_data):
        """변경 패턴 분석 테스트"""
        # Given: 파일별 커밋 데이터
        
        # When: 변경 패턴 분석
        patterns = analyzer.analyze_change_patterns(file_commit_data)
        
        # Then: 변경 패턴 통계가 생성되어야 함
        assert "total_files" in patterns
        assert "total_commits" in patterns
        assert "average_commits_per_file" in patterns
        assert "most_active_file" in patterns
        assert "change_distribution" in patterns

    def test_calculate_churn_risk_score(self, analyzer):
        """변경 위험도 점수 계산 테스트"""
        # Given: 파일의 churn 메트릭
        metrics = {
            "commit_frequency": 15,
            "recent_activity": 0.8,
            "author_diversity": 3,
            "change_velocity": 5.5,
            "stability_score": 0.3
        }
        
        # When: 위험도 점수 계산
        risk_score = analyzer.calculate_churn_risk_score(metrics)
        
        # Then: 0-1 범위의 위험도 점수가 반환되어야 함
        assert 0.0 <= risk_score <= 1.0
        # 높은 커밋 빈도, 높은 최근 활동도 → 높은 위험도

    def test_empty_commit_history_handling(self, analyzer):
        """빈 커밋 이력 처리 테스트"""
        # Given: 빈 커밋 리스트
        empty_commits = []
        
        # When: 각종 메트릭 계산
        recent_activity = analyzer._calculate_recent_activity(empty_commits)
        velocity = analyzer._calculate_change_velocity(empty_commits)
        diversity = analyzer._calculate_author_diversity(empty_commits)
        stability = analyzer._calculate_stability_score(empty_commits)
        
        # Then: 기본값들이 반환되어야 함
        assert recent_activity == 0.0
        assert velocity == 0.0
        assert diversity == 0
        assert stability == 1.0  # 변경이 없으면 완전히 안정적

    def test_churn_summary_generation(self, analyzer, file_commit_data):
        """변경 이력 요약 생성 테스트"""
        # Given: 파일별 커밋 데이터
        
        # When: 요약 정보 생성
        summary = analyzer.get_churn_summary(file_commit_data)
        
        # Then: 요약 통계가 올바르게 생성되어야 함
        assert "total_files_analyzed" in summary
        assert "total_commits" in summary
        assert "most_active_file" in summary
        assert "average_commits_per_file" in summary
        assert "hotspot_count" in summary
        assert "stable_file_count" in summary


class TestChurnAnalysisIntegration:
    """Churn 분석 통합 테스트"""
    
    def test_integration_with_dependency_analyzer(self):
        """의존성 분석기와의 통합 테스트"""
        # Given: 의존성 중심성과 churn 메트릭
        dependency_centrality = {
            "src/main.py": 0.8,
            "src/auth.py": 0.6,
            "src/utils.py": 0.4
        }
        
        churn_metrics = {
            "src/main.py": {"commit_frequency": 5, "recent_activity": 0.3},
            "src/auth.py": {"commit_frequency": 12, "recent_activity": 0.9},
            "src/utils.py": {"commit_frequency": 2, "recent_activity": 0.1}
        }
        
        # When: 통합 위험도 점수 계산
        from app.services.churn_analyzer import RuleBasedChurnAnalyzer
        analyzer = RuleBasedChurnAnalyzer()
        
        integrated_scores = analyzer.calculate_integrated_risk_scores(
            dependency_centrality, churn_metrics
        )
        
        # Then: 의존성과 변경 빈도를 모두 고려한 점수가 계산되어야 함
        assert "src/main.py" in integrated_scores
        assert "src/auth.py" in integrated_scores
        assert "src/utils.py" in integrated_scores
        
        # auth.py는 높은 churn이지만 낮은 중심성
        # main.py는 높은 중심성이지만 낮은 churn
        # 통합 점수에서 이 균형이 반영되어야 함