"""
스마트 파일 중요도 평가 시스템 테스트

TDD 방식으로 먼저 테스트를 작성하고, 이후 실제 구현을 진행합니다.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

# 구현 예정 모듈들
# from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer


class TestSmartFileImportanceAnalyzer:
    """파일 중요도 분석기 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """테스트용 파일 중요도 분석기 인스턴스"""
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        return SmartFileImportanceAnalyzer()
    
    @pytest.fixture
    def sample_dependency_data(self):
        """테스트용 의존성 데이터"""
        return {
            "src/main.ts": 0.8,  # 높은 의존성 중심성
            "src/core/config.ts": 0.9,  # 최고 의존성 중심성
            "src/utils/helper.ts": 0.6,  # 중간 의존성 중심성
            "src/components/App.tsx": 0.4,  # 낮은 의존성 중심성
            "README.md": 0.0  # 의존성 없음
        }
    
    @pytest.fixture
    def sample_churn_data(self):
        """테스트용 변경 이력 데이터"""
        return {
            "src/main.ts": {
                "commit_frequency": 15,
                "recent_activity": 0.8,
                "bug_fix_ratio": 0.3,
                "stability_score": 0.4
            },
            "src/core/config.ts": {
                "commit_frequency": 8,
                "recent_activity": 0.2,
                "bug_fix_ratio": 0.1,
                "stability_score": 0.9
            },
            "src/utils/helper.ts": {
                "commit_frequency": 20,
                "recent_activity": 0.9,
                "bug_fix_ratio": 0.4,
                "stability_score": 0.3
            },
            "src/components/App.tsx": {
                "commit_frequency": 5,
                "recent_activity": 0.3,
                "bug_fix_ratio": 0.1,
                "stability_score": 0.8
            }
        }
    
    @pytest.fixture
    def sample_complexity_data(self):
        """테스트용 복잡도 데이터"""
        return {
            "src/main.ts": {
                "cyclomatic_complexity": 12,
                "maintainability_index": 65,
                "lines_of_code": {"executable": 150}
            },
            "src/core/config.ts": {
                "cyclomatic_complexity": 3,
                "maintainability_index": 90,
                "lines_of_code": {"executable": 50}
            },
            "src/utils/helper.ts": {
                "cyclomatic_complexity": 18,
                "maintainability_index": 55,
                "lines_of_code": {"executable": 200}
            },
            "src/components/App.tsx": {
                "cyclomatic_complexity": 8,
                "maintainability_index": 75,
                "lines_of_code": {"executable": 100}
            }
        }

    def test_calculate_structural_importance_from_filename(self, analyzer):
        """파일명 패턴 기반 구조적 중요도 계산 테스트"""
        # Given: 다양한 파일명 패턴
        test_files = [
            "src/main.ts",           # 메인 파일
            "src/index.js",          # 인덱스 파일
            "src/App.tsx",           # 앱 파일
            "src/config.json",       # 설정 파일
            "package.json",          # 패키지 설정
            "src/utils/helper.ts",   # 유틸리티
            "src/components/Button.tsx",  # 일반 컴포넌트
            "README.md",             # 문서
            "test/unit.test.js"      # 테스트 파일
        ]
        
        # When: 구조적 중요도 계산
        for file_path in test_files:
            importance = analyzer.calculate_structural_importance(file_path)
            
            # Then: 0-1 범위의 중요도가 반환되어야 함
            assert 0.0 <= importance <= 1.0
        
        # 주요 파일들이 높은 점수를 가져야 함
        assert analyzer.calculate_structural_importance("src/main.ts") > 0.7
        assert analyzer.calculate_structural_importance("package.json") > 0.8
        assert analyzer.calculate_structural_importance("src/index.js") > 0.7
        
        # 일반 파일들은 낮은 점수
        assert analyzer.calculate_structural_importance("src/components/Button.tsx") <= 0.5
        assert analyzer.calculate_structural_importance("README.md") <= 0.3

    def test_calculate_comprehensive_importance_score(
        self, analyzer, sample_dependency_data, sample_churn_data, sample_complexity_data
    ):
        """종합적인 파일 중요도 점수 계산 테스트"""
        # Given: 모든 메트릭 데이터
        
        # When: 종합 중요도 점수 계산
        importance_scores = analyzer.calculate_comprehensive_importance_scores(
            dependency_centrality=sample_dependency_data,
            churn_metrics=sample_churn_data,
            complexity_metrics=sample_complexity_data
        )
        
        # Then: 모든 파일에 대한 점수가 계산되어야 함
        assert "src/main.ts" in importance_scores
        assert "src/core/config.ts" in importance_scores
        assert "src/utils/helper.ts" in importance_scores
        assert "src/components/App.tsx" in importance_scores
        
        # 점수는 0-1 범위여야 함
        for score in importance_scores.values():
            assert 0.0 <= score <= 1.0
        
        # config.ts는 높은 의존성과 안정성으로 높은 점수를 가져야 함
        assert importance_scores["src/core/config.ts"] > 0.6
        
        # main.ts는 높은 의존성과 높은 변경 빈도로 높은 점수
        assert importance_scores["src/main.ts"] > 0.5

    def test_identify_critical_files(
        self, analyzer, sample_dependency_data, sample_churn_data, sample_complexity_data
    ):
        """핵심 파일 식별 테스트"""
        # Given: 모든 메트릭 데이터
        
        # When: 핵심 파일 식별
        critical_files = analyzer.identify_critical_files(
            dependency_centrality=sample_dependency_data,
            churn_metrics=sample_churn_data,
            complexity_metrics=sample_complexity_data,
            top_n=3
        )
        
        # Then: 지정된 개수의 핵심 파일이 반환되어야 함
        assert len(critical_files) == 3
        
        # 각 파일에는 필요한 정보가 포함되어야 함
        for file_info in critical_files:
            assert "file_path" in file_info
            assert "importance_score" in file_info
            assert "reasons" in file_info
            assert "metrics" in file_info
        
        # 중요도 순으로 정렬되어야 함
        scores = [f["importance_score"] for f in critical_files]
        assert scores == sorted(scores, reverse=True)

    def test_generate_file_selection_reasons(self, analyzer):
        """파일 선정 이유 생성 테스트"""
        # Given: 파일의 메트릭 데이터
        file_metrics = {
            "dependency_centrality": 0.8,
            "churn_risk": 0.6,
            "complexity_score": 0.7,
            "structural_importance": 0.9
        }
        
        # When: 선정 이유 생성
        reasons = analyzer.generate_file_selection_reasons("src/main.ts", file_metrics)
        
        # Then: 이유 목록이 반환되어야 함
        assert isinstance(reasons, list)
        assert len(reasons) > 0
        
        # 각 이유는 문자열이어야 함
        for reason in reasons:
            assert isinstance(reason, str)
            assert len(reason) > 0

    def test_categorize_files_by_importance(
        self, analyzer, sample_dependency_data, sample_churn_data, sample_complexity_data
    ):
        """중요도별 파일 분류 테스트"""
        # Given: 모든 메트릭 데이터
        
        # When: 중요도별 파일 분류
        categorized = analyzer.categorize_files_by_importance(
            dependency_centrality=sample_dependency_data,
            churn_metrics=sample_churn_data,
            complexity_metrics=sample_complexity_data
        )
        
        # Then: 카테고리별로 분류되어야 함
        assert "critical" in categorized
        assert "important" in categorized
        assert "moderate" in categorized
        assert "low" in categorized
        
        # 각 카테고리는 리스트여야 함
        for category, files in categorized.items():
            assert isinstance(files, list)

    def test_calculate_importance_distribution(
        self, analyzer, sample_dependency_data, sample_churn_data, sample_complexity_data
    ):
        """중요도 분포 계산 테스트"""
        # Given: 모든 메트릭 데이터
        
        # When: 중요도 분포 계산
        distribution = analyzer.calculate_importance_distribution(
            dependency_centrality=sample_dependency_data,
            churn_metrics=sample_churn_data,
            complexity_metrics=sample_complexity_data
        )
        
        # Then: 분포 통계가 반환되어야 함
        assert "mean" in distribution
        assert "median" in distribution
        assert "std_dev" in distribution
        assert "min" in distribution
        assert "max" in distribution
        assert "quartiles" in distribution

    def test_get_improvement_suggestions(self, analyzer):
        """개선 제안 생성 테스트"""
        # Given: 핵심 파일 정보
        critical_files = [
            {
                "file_path": "src/main.ts",
                "importance_score": 0.85,
                "metrics": {
                    "dependency_centrality": 0.8,
                    "churn_risk": 0.7,
                    "complexity_score": 0.6
                }
            },
            {
                "file_path": "src/utils/helper.ts",
                "importance_score": 0.75,
                "metrics": {
                    "dependency_centrality": 0.6,
                    "churn_risk": 0.9,
                    "complexity_score": 0.8
                }
            }
        ]
        
        # When: 개선 제안 생성
        suggestions = analyzer.get_improvement_suggestions(critical_files)
        
        # Then: 제안 목록이 반환되어야 함
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # 각 제안은 문자열이어야 함
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_empty_data_handling(self, analyzer):
        """빈 데이터 처리 테스트"""
        # Given: 빈 메트릭 데이터
        empty_data = {}
        
        # When: 종합 중요도 점수 계산
        scores = analyzer.calculate_comprehensive_importance_scores(
            dependency_centrality=empty_data,
            churn_metrics=empty_data,
            complexity_metrics=empty_data
        )
        
        # Then: 빈 결과가 반환되어야 함
        assert scores == {}

    def test_partial_data_handling(self, analyzer, sample_dependency_data):
        """부분 데이터 처리 테스트"""
        # Given: 부분적인 메트릭 데이터 (일부만 있음)
        partial_churn = {"src/main.ts": {"commit_frequency": 10}}
        partial_complexity = {"src/main.ts": {"cyclomatic_complexity": 5}}
        
        # When: 종합 중요도 점수 계산
        scores = analyzer.calculate_comprehensive_importance_scores(
            dependency_centrality=sample_dependency_data,
            churn_metrics=partial_churn,
            complexity_metrics=partial_complexity
        )
        
        # Then: 사용 가능한 데이터로 점수가 계산되어야 함
        assert len(scores) > 0
        
        # 모든 점수는 0-1 범위여야 함
        for score in scores.values():
            assert 0.0 <= score <= 1.0


class TestFilePatternAnalysis:
    """파일 패턴 분석 테스트"""
    
    def test_detect_main_files(self):
        """메인 파일 감지 테스트"""
        # Given: 다양한 파일 패턴
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        analyzer = SmartFileImportanceAnalyzer()
        
        main_files = [
            "src/main.ts", "src/main.js", "src/index.ts", "src/index.js",
            "main.py", "app.py", "__init__.py", "App.tsx", "App.vue"
        ]
        
        non_main_files = [
            "src/components/Button.tsx", "src/views/LoginPage.tsx",
            "test/unit.test.js", "docs/README.md"
        ]
        
        # When & Then: 메인 파일 패턴 감지
        for file_path in main_files:
            importance = analyzer.calculate_structural_importance(file_path)
            assert importance > 0.6, f"{file_path} should be recognized as main file"
        
        for file_path in non_main_files:
            importance = analyzer.calculate_structural_importance(file_path)
            assert importance <= 0.6, f"{file_path} should not be recognized as main file"

    def test_detect_config_files(self):
        """설정 파일 감지 테스트"""
        # Given: 설정 파일들
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        analyzer = SmartFileImportanceAnalyzer()
        
        config_files = [
            "package.json", "tsconfig.json", "webpack.config.js",
            "babel.config.js", ".env", "Dockerfile", "docker-compose.yml"
        ]
        
        # When & Then: 설정 파일 패턴 감지
        for file_path in config_files:
            importance = analyzer.calculate_structural_importance(file_path)
            assert importance > 0.7, f"{file_path} should be recognized as config file"

    def test_detect_test_files(self):
        """테스트 파일 감지 테스트"""
        # Given: 테스트 파일들
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        analyzer = SmartFileImportanceAnalyzer()
        
        test_files = [
            "test/unit.test.js", "src/__tests__/component.test.tsx",
            "tests/integration.py", "spec/helper_spec.rb"
        ]
        
        # When & Then: 테스트 파일은 낮은 구조적 중요도
        for file_path in test_files:
            importance = analyzer.calculate_structural_importance(file_path)
            assert importance < 0.4, f"{file_path} should have low structural importance"


class TestFileImportanceIntegration:
    """파일 중요도 분석 통합 테스트"""
    
    def test_end_to_end_analysis(self):
        """전체 분석 파이프라인 테스트"""
        # Given: 종합적인 프로젝트 데이터
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        analyzer = SmartFileImportanceAnalyzer()
        
        # 실제 프로젝트 구조 시뮬레이션
        project_files = {
            "package.json": {"dependency": 0.9, "churn": 0.1, "complexity": 0.1},
            "src/main.ts": {"dependency": 0.8, "churn": 0.7, "complexity": 0.6},
            "src/config.ts": {"dependency": 0.9, "churn": 0.2, "complexity": 0.3},
            "src/utils/helper.ts": {"dependency": 0.5, "churn": 0.8, "complexity": 0.7},
            "src/components/App.tsx": {"dependency": 0.3, "churn": 0.3, "complexity": 0.4},
            "README.md": {"dependency": 0.0, "churn": 0.1, "complexity": 0.0}
        }
        
        dependency_data = {k: v["dependency"] for k, v in project_files.items()}
        churn_data = {k: {"commit_frequency": int(v["churn"] * 20)} for k, v in project_files.items()}
        complexity_data = {k: {"cyclomatic_complexity": int(v["complexity"] * 20)} for k, v in project_files.items()}
        
        # When: 전체 분석 수행
        results = analyzer.analyze_project_file_importance(
            dependency_centrality=dependency_data,
            churn_metrics=churn_data,
            complexity_metrics=complexity_data
        )
        
        # Then: 완전한 분석 결과가 반환되어야 함
        assert "critical_files" in results
        assert "importance_distribution" in results
        assert "categorized_files" in results
        assert "improvement_suggestions" in results
        assert "summary" in results
        
        # 핵심 파일들이 올바르게 식별되어야 함
        critical_files = results["critical_files"]
        top_file = critical_files[0]["file_path"]
        assert top_file in ["package.json", "src/config.ts", "src/main.ts"]

    def test_real_world_scenario(self):
        """실제 시나리오 테스트"""
        # Given: VS Code 같은 대규모 프로젝트 시뮬레이션
        from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
        analyzer = SmartFileImportanceAnalyzer()
        
        vscode_like_files = {
            "package.json": 0.95,
            "src/vs/workbench/workbench.main.ts": 0.90,
            "src/vs/base/common/lifecycle.ts": 0.85,
            "src/vs/platform/registry/common/platform.ts": 0.80,
            "src/vs/workbench/services/extensions/browser/extensionService.ts": 0.75,
            "extensions/typescript-language-features/src/extension.ts": 0.60,
            "src/vs/workbench/contrib/files/browser/fileActions.ts": 0.40,
            "test/unit/browser/workbench.test.ts": 0.20,
            "README.md": 0.10
        }
        
        # Mock 데이터 생성
        dependency_data = vscode_like_files
        churn_data = {k: {"commit_frequency": int(v * 30)} for k, v in vscode_like_files.items()}
        complexity_data = {k: {"cyclomatic_complexity": int(v * 25)} for k, v in vscode_like_files.items()}
        
        # When: 분석 수행
        results = analyzer.analyze_project_file_importance(
            dependency_centrality=dependency_data,
            churn_metrics=churn_data,
            complexity_metrics=complexity_data
        )
        
        # Then: 합리적인 결과가 나와야 함
        critical_files = results["critical_files"]
        
        # package.json과 주요 워크벤치 파일들이 상위에 있어야 함
        top_files = [f["file_path"] for f in critical_files[:3]]
        assert "package.json" in top_files
        assert any("workbench" in f for f in top_files)
        
        # 테스트 파일과 문서는 하위에 있어야 함
        all_files = [f["file_path"] for f in critical_files]
        readme_index = next((i for i, f in enumerate(all_files) if "README.md" in f), len(all_files))
        test_index = next((i for i, f in enumerate(all_files) if "test" in f), len(all_files))
        
        assert readme_index > len(critical_files) // 2  # 하반부에 위치
        assert test_index > len(critical_files) // 2   # 하반부에 위치