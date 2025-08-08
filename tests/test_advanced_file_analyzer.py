"""
고도화된 파일 분석기 테스트

TDD 방식으로 고도화된 파일 분석 시스템 테스트 먼저 작성
메타정보, 의존성 그래프, 변경 이력, 복잡도를 종합적으로 활용한 분석 테스트
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from app.services.advanced_file_analyzer import (
    AdvancedFileAnalyzer, 
    FileMetrics, 
    DependencyGraph, 
    ChurnAnalysis
)


class TestAdvancedFileAnalyzer:
    """고도화된 파일 분석기 테스트"""

    @pytest.fixture
    def analyzer(self):
        """분석기 인스턴스 생성"""
        return AdvancedFileAnalyzer()

    @pytest.fixture
    def sample_repo_info(self):
        """샘플 저장소 정보"""
        return {
            "name": "react-advanced-project",
            "description": "Advanced React project with complex architecture",
            "language": "JavaScript",
            "size": 15000,  # KB
            "stargazers_count": 1250,
            "forks_count": 180
        }

    @pytest.fixture
    def sample_file_tree(self):
        """샘플 파일 트리"""
        return [
            {"path": "src/App.js", "type": "file", "size": 2500},
            {"path": "src/components/UserManager.js", "type": "file", "size": 3200},
            {"path": "src/services/ApiService.js", "type": "file", "size": 1800},
            {"path": "src/utils/helpers.js", "type": "file", "size": 900},
            {"path": "src/config/database.js", "type": "file", "size": 1200},
            {"path": "package.json", "type": "file", "size": 800},
            {"path": "README.md", "type": "file", "size": 1500},
            {"path": "tests/App.test.js", "type": "file", "size": 600}
        ]

    @pytest.fixture
    def sample_commits(self):
        """샘플 커밋 히스토리"""
        base_date = datetime.now()
        return [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "Alice", "date": (base_date - timedelta(days=5)).isoformat() + "Z"}
                },
                "files": [
                    {"filename": "src/App.js", "changes": 15},
                    {"filename": "src/components/UserManager.js", "changes": 8}
                ]
            },
            {
                "sha": "def456", 
                "commit": {
                    "author": {"name": "Bob", "date": (base_date - timedelta(days=10)).isoformat() + "Z"}
                },
                "files": [
                    {"filename": "src/services/ApiService.js", "changes": 25},
                    {"filename": "package.json", "changes": 3}
                ]
            },
            {
                "sha": "ghi789",
                "commit": {
                    "author": {"name": "Alice", "date": (base_date - timedelta(days=15)).isoformat() + "Z"}
                },
                "files": [
                    {"filename": "src/App.js", "changes": 12},
                    {"filename": "README.md", "changes": 5}
                ]
            }
        ]

    @pytest.mark.asyncio
    async def test_analyze_repository_advanced_success(self, analyzer, sample_repo_info, sample_file_tree, sample_commits):
        """고도화된 저장소 분석 성공 테스트"""
        # Given
        repo_url = "https://github.com/test/react-project"
        
        with patch.object(analyzer.github_client, 'get_repository_info', return_value=sample_repo_info), \
             patch.object(analyzer.github_client, 'get_file_tree', return_value=sample_file_tree), \
             patch.object(analyzer.github_client, 'get_commit_history', return_value=sample_commits), \
             patch.object(analyzer.github_client, 'get_file_content', return_value="console.log('test');"):

            # When
            result = await analyzer.analyze_repository_advanced(repo_url)

            # Then
            assert result["success"] is True
            assert "repo_info" in result
            assert "file_metrics" in result
            assert "dependency_graph" in result
            assert "churn_analysis" in result
            assert "important_files" in result
            assert "dashboard_data" in result

    @pytest.mark.asyncio
    async def test_analyze_commit_history(self, analyzer, sample_commits):
        """커밋 히스토리 분석 테스트"""
        # Given
        repo_url = "https://github.com/test/repo"
        
        with patch.object(analyzer.github_client, 'get_commit_history', return_value=sample_commits), \
             patch.object(analyzer.github_client, 'get_commit_details', return_value={"files": []}):

            # When
            churn_analysis = await analyzer._analyze_commit_history(repo_url)

            # Then
            assert isinstance(churn_analysis, ChurnAnalysis)
            assert len(churn_analysis.file_churns) > 0
            assert len(churn_analysis.hotspots) > 0
            
            # App.js가 가장 많이 변경된 파일이어야 함 (2번 커밋)
            app_js_churn = churn_analysis.file_churns.get("src/App.js")
            assert app_js_churn is not None
            assert app_js_churn["commit_count"] == 2
            assert app_js_churn["total_changes"] == 27  # 15 + 12

    @pytest.mark.asyncio 
    async def test_build_dependency_graph(self, analyzer, sample_file_tree):
        """의존성 그래프 구성 테스트"""
        # Given
        repo_url = "https://github.com/test/repo"
        sample_file_content = """
        import React from 'react';
        import UserManager from './components/UserManager';
        import ApiService from './services/ApiService';
        
        function App() {
            return <div>Test</div>;
        }
        """
        
        with patch.object(analyzer.github_client, 'get_file_content', return_value=sample_file_content):

            # When  
            dependency_graph = await analyzer._build_dependency_graph(repo_url, sample_file_tree)

            # Then
            assert isinstance(dependency_graph, DependencyGraph)
            assert dependency_graph.graph.number_of_nodes() > 0
            assert len(dependency_graph.import_relationships) > 0

    @pytest.mark.asyncio
    async def test_calculate_comprehensive_metrics(self, analyzer, sample_file_tree):
        """종합 메트릭 계산 테스트"""
        # Given
        repo_url = "https://github.com/test/repo"
        dependency_graph = DependencyGraph()
        churn_analysis = ChurnAnalysis()
        
        # 샘플 변경이력 데이터 설정
        churn_analysis.file_churns = {
            "src/App.js": {
                "commit_count": 5,
                "recent_commits": 2,
                "authors_count": 2,
                "average_commit_size": 15.5
            }
        }
        
        sample_complex_code = """
        function complexFunction(x, y, z) {
            if (x > 0) {
                for (let i = 0; i < y; i++) {
                    if (i % 2 === 0) {
                        while (z > 0) {
                            z--;
                        }
                    } else {
                        try {
                            doSomething();
                        } catch (e) {
                            handleError();
                        }
                    }
                }
            }
            return x + y + z;
        }
        """
        
        with patch.object(analyzer.github_client, 'get_file_content', return_value=sample_complex_code):

            # When
            file_metrics = await analyzer._calculate_comprehensive_metrics(
                repo_url, sample_file_tree, dependency_graph, churn_analysis
            )

            # Then
            assert isinstance(file_metrics, dict)
            assert len(file_metrics) > 0
            
            # App.js 메트릭 검증
            app_metrics = file_metrics.get("src/App.js")
            if app_metrics:
                assert isinstance(app_metrics, FileMetrics)
                assert app_metrics.importance_score > 0
                assert app_metrics.cyclomatic_complexity > 1  # 복잡한 코드이므로
                assert app_metrics.commit_frequency == 5

    @pytest.mark.asyncio
    async def test_select_critical_files(self, analyzer):
        """중요 파일 선별 테스트"""
        # Given
        sample_metrics = {
            "src/App.js": FileMetrics(
                path="src/App.js",
                importance_score=85.5,
                quality_risk_score=3.2,
                cyclomatic_complexity=8.5,
                hotspot_score=15.2,
                file_type="main",
                language="javascript"
            ),
            "src/utils/helpers.js": FileMetrics(
                path="src/utils/helpers.js", 
                importance_score=45.2,
                quality_risk_score=2.1,
                cyclomatic_complexity=3.2,
                hotspot_score=5.8,
                file_type="utility",
                language="javascript"
            )
        }
        
        with patch.object(analyzer.github_client, 'get_file_content', return_value="test content"):

            # When
            critical_files = await analyzer._select_critical_files(sample_metrics, limit=5)

            # Then
            assert len(critical_files) <= 5
            assert len(critical_files) > 0
            
            # 중요도 순으로 정렬되어야 함
            first_file = critical_files[0]
            assert first_file["path"] == "src/App.js"
            assert first_file["importance_score"] == 85.5
            assert "content" in first_file
            assert "metrics_summary" in first_file

    def test_calculate_importance_score(self, analyzer):
        """중요도 점수 계산 테스트"""
        # Given
        metrics = FileMetrics(
            path="src/controllers/UserController.js",
            size=3000,
            cyclomatic_complexity=12.5,
            centrality_score=0.15,
            recent_commits=3,
            commit_frequency=8,
            fan_in=5,
            file_type="controller",
            has_main_function=False,
            is_test_file=False,
            is_config_file=False
        )

        # When
        importance_score = analyzer._calculate_importance_score(metrics)

        # Then
        assert 0 <= importance_score <= 100
        assert importance_score > 50  # controller 타입이고 복잡도가 높으므로

    def test_calculate_quality_risk_score(self, analyzer):
        """품질 위험도 점수 계산 테스트"""
        # Given
        high_risk_metrics = FileMetrics(
            path="src/complex_module.js",
            cyclomatic_complexity=20,  # 높은 복잡도
            hotspot_score=25,  # 높은 핫스팟 점수
            lines_of_code=800,  # 많은 라인 수
            fan_out=12,  # 많은 외부 의존성
            fan_in=20,  # 많은 참조
            maintainability_index=15  # 낮은 유지보수성
        )

        # When
        risk_score = analyzer._calculate_quality_risk_score(high_risk_metrics)

        # Then
        assert 0 <= risk_score <= 10
        assert risk_score >= 7  # 고위험으로 분류되어야 함

    def test_generate_dashboard_data(self, analyzer, sample_repo_info):
        """대시보드 데이터 생성 테스트"""
        # Given
        sample_file_metrics = {
            "src/App.js": FileMetrics(
                path="src/App.js",
                language="javascript",
                file_type="main", 
                cyclomatic_complexity=8.5,
                quality_risk_score=4.2,
                lines_of_code=150
            ),
            "src/service.py": FileMetrics(
                path="src/service.py",
                language="python",
                file_type="service",
                cyclomatic_complexity=5.2,
                quality_risk_score=2.8,
                lines_of_code=200
            )
        }
        
        dependency_graph = DependencyGraph()
        churn_analysis = ChurnAnalysis()
        churn_analysis.hotspots = [
            {"filename": "src/App.js", "hotspot_score": 15.2, "complexity": 8.5}
        ]

        # When
        dashboard_data = analyzer._generate_dashboard_data(
            sample_repo_info, sample_file_metrics, dependency_graph, churn_analysis
        )

        # Then
        assert "repository_overview" in dashboard_data
        assert "complexity_analysis" in dashboard_data
        assert "quality_risk_analysis" in dashboard_data
        assert "dependency_analysis" in dashboard_data
        assert "churn_analysis" in dashboard_data
        assert "language_statistics" in dashboard_data
        
        # 언어별 통계 검증
        lang_stats = dashboard_data["language_statistics"]
        assert "javascript" in lang_stats
        assert "python" in lang_stats
        assert lang_stats["javascript"]["file_count"] == 1
        assert lang_stats["python"]["file_count"] == 1

    def test_detect_language(self, analyzer):
        """언어 감지 테스트"""
        # Given & When & Then
        assert analyzer._detect_language("src/App.js") == "javascript"
        assert analyzer._detect_language("src/Component.tsx") == "typescript"
        assert analyzer._detect_language("main.py") == "python"
        assert analyzer._detect_language("Service.java") == "java"
        assert analyzer._detect_language("main.go") == "go"
        assert analyzer._detect_language("lib.rs") == "rust"
        assert analyzer._detect_language("unknown.xyz") == "unknown"

    def test_categorize_file_type(self, analyzer):
        """파일 유형 분류 테스트"""
        # Given & When & Then
        assert analyzer._categorize_file_type("src/main.py") == "main"
        assert analyzer._categorize_file_type("src/UserController.js") == "controller"
        assert analyzer._categorize_file_type("src/UserService.java") == "service" 
        assert analyzer._categorize_file_type("src/User.model.js") == "model"
        assert analyzer._categorize_file_type("src/api/routes.js") == "router"
        assert analyzer._categorize_file_type("src/utils/helper.py") == "utility"
        assert analyzer._categorize_file_type("config/settings.py") == "configuration"
        assert analyzer._categorize_file_type("src/components/Button.jsx") == "component"
        assert analyzer._categorize_file_type("src/random.js") == "general"

    def test_is_test_file(self, analyzer):
        """테스트 파일 여부 확인 테스트"""
        # Given & When & Then
        assert analyzer._is_test_file("test_user.py") is True
        assert analyzer._is_test_file("user_test.py") is True
        assert analyzer._is_test_file("user.test.js") is True
        assert analyzer._is_test_file("user.spec.js") is True
        assert analyzer._is_test_file("user_spec.py") is True
        assert analyzer._is_test_file("regular_file.py") is False

    def test_is_config_file(self, analyzer):
        """설정 파일 여부 확인 테스트"""
        # Given & When & Then
        assert analyzer._is_config_file("config.py") is True
        assert analyzer._is_config_file("settings.json") is True
        assert analyzer._is_config_file(".env") is True
        assert analyzer._is_config_file("package.json") is True
        assert analyzer._is_config_file("requirements.txt") is True
        assert analyzer._is_config_file("pom.xml") is True
        assert analyzer._is_config_file("regular_file.py") is False

    def test_calculate_complexity_metrics(self, analyzer):
        """복잡도 메트릭 계산 테스트"""
        # Given
        complex_python_code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            for i in range(z):
                if i % 2 == 0:
                    try:
                        result = process(i)
                        if result and result > 10:
                            return result
                    except Exception as e:
                        while y > 0:
                            y -= 1
                elif i % 3 == 0:
                    continue
            else:
                pass
        elif y < 0:
            return -1
    return 0
        """

        # When
        metrics = analyzer._calculate_complexity_metrics(complex_python_code, "python")

        # Then
        assert "cyclomatic" in metrics
        assert "cognitive" in metrics
        assert "halstead" in metrics
        assert "maintainability" in metrics
        
        assert metrics["cyclomatic"] > 5  # 복잡한 코드이므로 높은 순환 복잡도
        assert metrics["cognitive"] > 0   # 인지 복잡도 존재
        assert 0 <= metrics["maintainability"] <= 171  # 유지보수성 지수 범위

    def test_extract_imports(self, analyzer):
        """import 관계 추출 테스트"""
        # Given
        python_code = """
import os
import sys
from typing import Dict, List
from .models import User
from app.services import ApiService
        """
        
        javascript_code = """
import React from 'react';
import { useState, useEffect } from 'react';
import UserComponent from './components/User';
const ApiService = require('./services/api');
        """

        # When
        python_imports = analyzer._extract_imports(python_code, "test.py")
        js_imports = analyzer._extract_imports(javascript_code, "test.js")

        # Then
        assert len(python_imports) > 0
        assert len(js_imports) > 0
        
        # Python imports 검증
        assert any("os" in imp for imp in python_imports)
        assert any("typing" in imp for imp in python_imports)
        
        # JavaScript imports 검증  
        assert any("react" in imp.lower() for imp in js_imports)

    def test_has_main_function(self, analyzer):
        """메인 함수 존재 여부 확인 테스트"""
        # Given
        python_main = """
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
        """
        
        java_main = """
public class TestApp {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
        """
        
        regular_code = """
def helper_function():
    return "not main"
        """

        # When & Then
        assert analyzer._has_main_function(python_main, "python") is True
        assert analyzer._has_main_function(java_main, "java") is True
        assert analyzer._has_main_function(regular_code, "python") is False

    @pytest.mark.asyncio
    async def test_analyze_with_error_handling(self, analyzer):
        """에러 처리 테스트"""
        # Given
        repo_url = "https://github.com/invalid/repo"
        
        with patch.object(analyzer.github_client, 'get_repository_info', side_effect=Exception("API Error")):

            # When
            result = await analyzer.analyze_repository_advanced(repo_url)

            # Then
            assert result["success"] is False
            assert "error" in result
            assert "API Error" in result["error"]


class TestFileMetrics:
    """FileMetrics 데이터 클래스 테스트"""

    def test_file_metrics_initialization(self):
        """FileMetrics 초기화 테스트"""
        # Given & When
        metrics = FileMetrics(path="src/test.py")

        # Then
        assert metrics.path == "src/test.py"
        assert metrics.size == 0
        assert metrics.language == "unknown"
        assert metrics.cyclomatic_complexity == 0.0
        assert metrics.importance_score == 0.0

    def test_file_metrics_with_values(self):
        """FileMetrics 값 설정 테스트"""
        # Given & When
        metrics = FileMetrics(
            path="src/controller.py",
            size=2500,
            language="python",
            cyclomatic_complexity=8.5,
            importance_score=75.2,
            quality_risk_score=4.8
        )

        # Then
        assert metrics.path == "src/controller.py"
        assert metrics.size == 2500
        assert metrics.language == "python"
        assert metrics.cyclomatic_complexity == 8.5
        assert metrics.importance_score == 75.2
        assert metrics.quality_risk_score == 4.8


class TestDependencyGraph:
    """DependencyGraph 데이터 클래스 테스트"""

    def test_dependency_graph_initialization(self):
        """DependencyGraph 초기화 테스트"""
        # Given & When
        graph = DependencyGraph()

        # Then
        assert graph.graph.number_of_nodes() == 0
        assert graph.graph.number_of_edges() == 0
        assert len(graph.import_relationships) == 0
        assert len(graph.module_clusters) == 0
        assert len(graph.critical_paths) == 0


class TestChurnAnalysis:
    """ChurnAnalysis 데이터 클래스 테스트"""

    def test_churn_analysis_initialization(self):
        """ChurnAnalysis 초기화 테스트"""
        # Given & When
        churn = ChurnAnalysis()

        # Then
        assert len(churn.file_churns) == 0
        assert len(churn.hotspots) == 0
        assert len(churn.author_statistics) == 0
        assert len(churn.temporal_patterns) == 0