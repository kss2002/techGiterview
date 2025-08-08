"""
분석 대시보드 컴포넌트 테스트

TDD 방식으로 대시보드 컴포넌트의 기능과 렌더링 테스트 먼저 작성
"""

import pytest
from unittest.mock import MagicMock, patch
import json

# React 컴포넌트 테스트를 위한 임시 테스트 클래스
# 실제로는 Jest + React Testing Library를 사용해야 하지만
# Python 환경에서 로직 검증을 위한 테스트


class TestAnalysisDashboardLogic:
    """대시보드 로직 테스트 (Python으로 검증)"""

    @pytest.fixture
    def sample_dashboard_data(self):
        """샘플 대시보드 데이터"""
        return {
            "repository_overview": {
                "name": "react-advanced-project",
                "description": "Advanced React project with complex architecture",
                "language": "JavaScript",
                "size": 15000,
                "stars": 1250,
                "forks": 180
            },
            "complexity_analysis": {
                "distribution": {"low": 45, "medium": 25, "high": 8},
                "average_complexity": 4.2,
                "max_complexity": 18.5,
                "maintainability_average": 65.8
            },
            "quality_risk_analysis": {
                "distribution": {"low": 52, "medium": 20, "high": 6},
                "high_risk_files": [
                    {
                        "filename": "src/complex/LegacyModule.js",
                        "risk_score": 8.5,
                        "complexity": 15.2,
                        "hotspot_score": 22.8
                    },
                    {
                        "filename": "src/utils/DataProcessor.js", 
                        "risk_score": 7.8,
                        "complexity": 12.3,
                        "hotspot_score": 18.5
                    }
                ]
            },
            "dependency_analysis": {
                "graph_metrics": {
                    "total_nodes": 78,
                    "total_edges": 142,
                    "density": 0.046,
                    "clustering_coefficient": 0.125,
                    "strongly_connected_components": 3,
                    "critical_paths_count": 5
                },
                "top_central_files": [
                    {
                        "filename": "src/App.js",
                        "centrality_score": 0.142,
                        "fan_in": 8,
                        "fan_out": 12,
                        "importance_score": 85.2
                    },
                    {
                        "filename": "src/services/ApiService.js",
                        "centrality_score": 0.098,
                        "fan_in": 15,
                        "fan_out": 5,
                        "importance_score": 78.9
                    }
                ],
                "module_clusters": [
                    {
                        "cluster_id": 0,
                        "files": ["src/components/User.js", "src/components/UserForm.js"],
                        "size": 2
                    }
                ],
                "critical_paths": [
                    {
                        "path_id": 0,
                        "files": ["src/App.js", "src/services/ApiService.js", "src/models/User.js"],
                        "length": 3
                    }
                ]
            },
            "churn_analysis": {
                "hotspots": [
                    {
                        "filename": "src/App.js",
                        "hotspot_score": 25.8,
                        "complexity": 8.5,
                        "recent_commits": 5,
                        "quality_risk": 4.2
                    },
                    {
                        "filename": "src/components/UserForm.js",
                        "hotspot_score": 18.2,
                        "complexity": 6.8,
                        "recent_commits": 3,
                        "quality_risk": 3.1
                    }
                ],
                "author_statistics": {
                    "Alice": {"commits": 45, "files_changed": 25},
                    "Bob": {"commits": 32, "files_changed": 18},
                    "Charlie": {"commits": 28, "files_changed": 15}
                },
                "most_changed_files": [
                    {
                        "filename": "src/App.js",
                        "commit_count": 15,
                        "recent_commits": 5,
                        "authors_count": 3
                    },
                    {
                        "filename": "package.json",
                        "commit_count": 12,
                        "recent_commits": 2,
                        "authors_count": 2
                    }
                ]
            },
            "language_statistics": {
                "javascript": {
                    "file_count": 45,
                    "total_loc": 8500,
                    "avg_complexity": 4.8
                },
                "typescript": {
                    "file_count": 20,
                    "total_loc": 4200,
                    "avg_complexity": 5.2
                },
                "css": {
                    "file_count": 15,
                    "total_loc": 1800,
                    "avg_complexity": 1.2
                }
            },
            "file_type_distribution": {
                "component": 25,
                "service": 8,
                "utility": 12,
                "configuration": 6,
                "general": 18
            }
        }

    @pytest.fixture
    def sample_critical_files(self):
        """샘플 중요 파일 목록"""
        return [
            {
                "path": "src/App.js",
                "importance_score": 85.2,
                "quality_risk_score": 4.2,
                "complexity": 8.5,
                "hotspot_score": 25.8,
                "file_type": "main",
                "language": "javascript",
                "metrics_summary": {
                    "lines_of_code": 320,
                    "fan_in": 8,
                    "fan_out": 12,
                    "commit_frequency": 15,
                    "recent_commits": 5,
                    "authors_count": 3,
                    "centrality_score": 0.142
                }
            },
            {
                "path": "src/services/ApiService.js",
                "importance_score": 78.9,
                "quality_risk_score": 3.8,
                "complexity": 6.2,
                "hotspot_score": 15.2,
                "file_type": "service",
                "language": "javascript",
                "metrics_summary": {
                    "lines_of_code": 280,
                    "fan_in": 15,
                    "fan_out": 5,
                    "commit_frequency": 8,
                    "recent_commits": 2,
                    "authors_count": 2,
                    "centrality_score": 0.098
                }
            }
        ]

    def test_complexity_distribution_calculation(self, sample_dashboard_data):
        """복잡도 분포 계산 테스트"""
        # Given
        complexity_data = sample_dashboard_data["complexity_analysis"]["distribution"]
        
        # When
        total_files = complexity_data["low"] + complexity_data["medium"] + complexity_data["high"]
        low_percentage = (complexity_data["low"] / total_files) * 100
        high_percentage = (complexity_data["high"] / total_files) * 100
        
        # Then
        assert total_files == 78  # 45 + 25 + 8
        assert low_percentage > 50  # 대부분 파일이 낮은 복잡도
        assert high_percentage < 15  # 높은 복잡도 파일은 소수

    def test_risk_analysis_filtering(self, sample_dashboard_data):
        """위험도 분석 필터링 테스트"""
        # Given
        high_risk_files = sample_dashboard_data["quality_risk_analysis"]["high_risk_files"]
        
        # When
        critical_risk_files = [f for f in high_risk_files if f["risk_score"] > 8.0]
        moderate_risk_files = [f for f in high_risk_files if 6.0 < f["risk_score"] <= 8.0]
        
        # Then
        assert len(critical_risk_files) == 1  # LegacyModule.js만 8.0 초과
        assert len(moderate_risk_files) == 1  # DataProcessor.js는 7.8
        assert critical_risk_files[0]["filename"] == "src/complex/LegacyModule.js"

    def test_dependency_network_metrics(self, sample_dashboard_data):
        """의존성 네트워크 메트릭 테스트"""
        # Given
        graph_metrics = sample_dashboard_data["dependency_analysis"]["graph_metrics"]
        
        # When
        nodes = graph_metrics["total_nodes"]
        edges = graph_metrics["total_edges"]
        density = graph_metrics["density"]
        
        # Then
        assert nodes > 0
        assert edges > nodes  # 최소한 노드보다 많은 엣지
        assert 0 <= density <= 1  # 밀도는 0과 1 사이
        assert density < 0.1  # 일반적으로 코드 의존성 그래프는 sparse

    def test_centrality_ranking(self, sample_dashboard_data):
        """중심성 순위 테스트"""
        # Given
        central_files = sample_dashboard_data["dependency_analysis"]["top_central_files"]
        
        # When
        sorted_by_centrality = sorted(central_files, key=lambda x: x["centrality_score"], reverse=True)
        sorted_by_importance = sorted(central_files, key=lambda x: x["importance_score"], reverse=True)
        
        # Then
        assert sorted_by_centrality[0]["filename"] == "src/App.js"  # 가장 높은 중심성
        assert sorted_by_importance[0]["filename"] == "src/App.js"  # 가장 높은 중요도
        assert sorted_by_centrality[0]["centrality_score"] > sorted_by_centrality[1]["centrality_score"]

    def test_hotspot_analysis(self, sample_dashboard_data):
        """핫스팟 분석 테스트"""
        # Given
        hotspots = sample_dashboard_data["churn_analysis"]["hotspots"]
        
        # When
        high_hotspots = [h for h in hotspots if h["hotspot_score"] > 20]
        complex_hotspots = [h for h in hotspots if h["complexity"] > 8 and h["recent_commits"] > 3]
        
        # Then
        assert len(high_hotspots) == 1  # App.js만 20 초과
        assert len(complex_hotspots) == 1  # App.js만 복잡하면서 최근 커밋 많음
        assert high_hotspots[0]["filename"] == "src/App.js"

    def test_author_contribution_analysis(self, sample_dashboard_data):
        """개발자 기여도 분석 테스트"""
        # Given
        author_stats = sample_dashboard_data["churn_analysis"]["author_statistics"]
        
        # When
        total_commits = sum(stats["commits"] for stats in author_stats.values())
        main_contributor = max(author_stats.items(), key=lambda x: x[1]["commits"])
        productivity_ratios = {
            author: stats["files_changed"] / stats["commits"] 
            for author, stats in author_stats.items()
        }
        
        # Then
        assert total_commits == 105  # 45 + 32 + 28
        assert main_contributor[0] == "Alice"  # 가장 많은 커밋
        assert all(0 < ratio <= 1 for ratio in productivity_ratios.values())  # 합리적인 비율

    def test_language_distribution_analysis(self, sample_dashboard_data):
        """언어 분포 분석 테스트"""
        # Given
        lang_stats = sample_dashboard_data["language_statistics"]
        
        # When
        total_files = sum(stats["file_count"] for stats in lang_stats.values())
        total_loc = sum(stats["total_loc"] for stats in lang_stats.values())
        dominant_language = max(lang_stats.items(), key=lambda x: x[1]["file_count"])
        most_complex_language = max(lang_stats.items(), key=lambda x: x[1]["avg_complexity"])
        
        # Then
        assert total_files == 80  # 45 + 20 + 15
        assert total_loc == 14500  # 8500 + 4200 + 1800
        assert dominant_language[0] == "javascript"  # 가장 많은 파일
        assert most_complex_language[0] == "typescript"  # 가장 높은 평균 복잡도

    def test_file_type_categorization(self, sample_dashboard_data):
        """파일 타입 분류 테스트"""
        # Given
        file_types = sample_dashboard_data["file_type_distribution"]
        
        # When
        total_typed_files = sum(file_types.values())
        component_ratio = file_types["component"] / total_typed_files
        config_ratio = file_types["configuration"] / total_typed_files
        
        # Then
        assert total_typed_files == 69  # 25 + 8 + 12 + 6 + 18
        assert component_ratio > 0.3  # 컴포넌트가 30% 이상
        assert config_ratio < 0.1  # 설정 파일은 10% 미만

    def test_critical_files_ranking(self, sample_critical_files):
        """중요 파일 순위 테스트"""
        # Given
        critical_files = sample_critical_files
        
        # When
        sorted_by_importance = sorted(critical_files, key=lambda x: x["importance_score"], reverse=True)
        high_risk_and_important = [
            f for f in critical_files 
            if f["importance_score"] > 75 and f["quality_risk_score"] > 4
        ]
        
        # Then
        assert sorted_by_importance[0]["path"] == "src/App.js"
        assert len(high_risk_and_important) == 1  # App.js만 해당
        assert all(f["importance_score"] > 70 for f in critical_files)

    def test_file_metrics_completeness(self, sample_critical_files):
        """파일 메트릭 완성도 테스트"""
        # Given
        critical_files = sample_critical_files
        
        # When & Then
        for file in critical_files:
            # 필수 필드 존재 확인
            assert "path" in file
            assert "importance_score" in file
            assert "quality_risk_score" in file
            assert "complexity" in file
            assert "file_type" in file
            assert "language" in file
            assert "metrics_summary" in file
            
            # 메트릭 요약 필드 확인
            summary = file["metrics_summary"]
            required_summary_fields = [
                "lines_of_code", "fan_in", "fan_out", "commit_frequency",
                "recent_commits", "authors_count", "centrality_score"
            ]
            for field in required_summary_fields:
                assert field in summary
                assert isinstance(summary[field], (int, float))

    def test_dashboard_data_integrity(self, sample_dashboard_data):
        """대시보드 데이터 무결성 테스트"""
        # Given
        data = sample_dashboard_data
        
        # When & Then
        # 필수 섹션 존재 확인
        required_sections = [
            "repository_overview", "complexity_analysis", "quality_risk_analysis",
            "dependency_analysis", "churn_analysis", "language_statistics", "file_type_distribution"
        ]
        for section in required_sections:
            assert section in data
            assert isinstance(data[section], dict)
        
        # 수치 데이터 유효성 확인
        complexity = data["complexity_analysis"]
        assert complexity["average_complexity"] > 0
        assert complexity["max_complexity"] >= complexity["average_complexity"]
        
        # 분포 데이터 합계 확인 (각 분포의 총합이 의미가 있는지)
        complexity_dist = complexity["distribution"]
        assert all(count >= 0 for count in complexity_dist.values())

    def test_chart_data_transformation(self, sample_dashboard_data):
        """차트 데이터 변환 테스트"""
        # Given
        lang_stats = sample_dashboard_data["language_statistics"]
        complexity_dist = sample_dashboard_data["complexity_analysis"]["distribution"]
        
        # When - 파이 차트용 데이터 변환
        pie_chart_data = [
            {"name": lang, "value": stats["file_count"], "fill": f"color-{i}"}
            for i, (lang, stats) in enumerate(lang_stats.items())
        ]
        
        # 바 차트용 데이터 변환
        bar_chart_data = [
            {"name": level, "value": count}
            for level, count in complexity_dist.items()
        ]
        
        # Then
        assert len(pie_chart_data) == 3  # javascript, typescript, css
        assert all("name" in item and "value" in item for item in pie_chart_data)
        assert len(bar_chart_data) == 3  # low, medium, high
        assert sum(item["value"] for item in bar_chart_data) == 78

    def test_performance_indicators(self, sample_dashboard_data, sample_critical_files):
        """성능 지표 테스트"""
        # Given
        complexity_avg = sample_dashboard_data["complexity_analysis"]["average_complexity"]
        high_risk_count = len(sample_dashboard_data["quality_risk_analysis"]["high_risk_files"])
        critical_files_count = len(sample_critical_files)
        
        # When - 성능 지표 계산
        complexity_health = "good" if complexity_avg < 5 else "warning" if complexity_avg < 8 else "critical"
        risk_health = "good" if high_risk_count < 5 else "warning" if high_risk_count < 10 else "critical"
        maintainability = sample_dashboard_data["complexity_analysis"]["maintainability_average"]
        
        # Then
        assert complexity_health == "good"  # 4.2 < 5
        assert risk_health == "good"  # 2 < 5
        assert maintainability > 50  # 유지보수성이 50 이상
        assert critical_files_count > 0  # 중요 파일이 존재


class TestDashboardUILogic:
    """대시보드 UI 로직 테스트"""
    
    @pytest.fixture
    def sample_critical_files(self):
        """샘플 중요 파일 목록"""
        return [
            {
                "path": "src/App.js",
                "importance_score": 85.2,
                "quality_risk_score": 4.2,
                "complexity": 8.5,
                "hotspot_score": 25.8,
                "file_type": "main",
                "language": "javascript",
                "metrics_summary": {
                    "lines_of_code": 320,
                    "fan_in": 8,
                    "fan_out": 12,
                    "commit_frequency": 15,
                    "recent_commits": 5,
                    "authors_count": 3,
                    "centrality_score": 0.142
                }
            },
            {
                "path": "src/services/ApiService.js",
                "importance_score": 78.9,
                "quality_risk_score": 3.8,
                "complexity": 6.2,
                "hotspot_score": 15.2,
                "file_type": "service",
                "language": "javascript",
                "metrics_summary": {
                    "lines_of_code": 280,
                    "fan_in": 15,
                    "fan_out": 5,
                    "commit_frequency": 8,
                    "recent_commits": 2,
                    "authors_count": 2,
                    "centrality_score": 0.098
                }
            }
        ]

    @pytest.fixture
    def sample_dashboard_data(self):
        """샘플 대시보드 데이터"""
        return {
            "repository_overview": {
                "name": "react-advanced-project",
                "description": "Advanced React project with complex architecture",
                "language": "JavaScript",
                "size": 15000,
                "stars": 1250,
                "forks": 180
            },
            "complexity_analysis": {
                "distribution": {"low": 45, "medium": 25, "high": 8},
                "average_complexity": 4.2,
                "max_complexity": 18.5,
                "maintainability_average": 65.8
            },
            "quality_risk_analysis": {
                "distribution": {"low": 52, "medium": 20, "high": 6},
                "high_risk_files": [
                    {
                        "filename": "src/complex/LegacyModule.js",
                        "risk_score": 8.5,
                        "complexity": 15.2,
                        "hotspot_score": 22.8
                    },
                    {
                        "filename": "src/utils/DataProcessor.js", 
                        "risk_score": 7.8,
                        "complexity": 12.3,
                        "hotspot_score": 18.5
                    }
                ]
            },
            "dependency_analysis": {
                "graph_metrics": {
                    "total_nodes": 78,
                    "total_edges": 142,
                    "density": 0.046,
                    "clustering_coefficient": 0.125,
                    "strongly_connected_components": 3,
                    "critical_paths_count": 5
                },
                "top_central_files": [
                    {
                        "filename": "src/App.js",
                        "centrality_score": 0.142,
                        "fan_in": 8,
                        "fan_out": 12,
                        "importance_score": 85.2
                    },
                    {
                        "filename": "src/services/ApiService.js",
                        "centrality_score": 0.098,
                        "fan_in": 15,
                        "fan_out": 5,
                        "importance_score": 78.9
                    }
                ],
                "module_clusters": [
                    {
                        "cluster_id": 0,
                        "files": ["src/components/User.js", "src/components/UserForm.js"],
                        "size": 2
                    }
                ],
                "critical_paths": [
                    {
                        "path_id": 0,
                        "files": ["src/App.js", "src/services/ApiService.js", "src/models/User.js"],
                        "length": 3
                    }
                ]
            },
            "churn_analysis": {
                "hotspots": [
                    {
                        "filename": "src/App.js",
                        "hotspot_score": 25.8,
                        "complexity": 8.5,
                        "recent_commits": 5,
                        "quality_risk": 4.2
                    },
                    {
                        "filename": "src/components/UserForm.js",
                        "hotspot_score": 18.2,
                        "complexity": 6.8,
                        "recent_commits": 3,
                        "quality_risk": 3.1
                    }
                ],
                "author_statistics": {
                    "Alice": {"commits": 45, "files_changed": 25},
                    "Bob": {"commits": 32, "files_changed": 18},
                    "Charlie": {"commits": 28, "files_changed": 15}
                },
                "most_changed_files": [
                    {
                        "filename": "src/App.js",
                        "commit_count": 15,
                        "recent_commits": 5,
                        "authors_count": 3
                    },
                    {
                        "filename": "package.json",
                        "commit_count": 12,
                        "recent_commits": 2,
                        "authors_count": 2
                    }
                ]
            },
            "language_statistics": {
                "javascript": {
                    "file_count": 45,
                    "total_loc": 8500,
                    "avg_complexity": 4.8
                },
                "typescript": {
                    "file_count": 20,
                    "total_loc": 4200,
                    "avg_complexity": 5.2
                },
                "css": {
                    "file_count": 15,
                    "total_loc": 1800,
                    "avg_complexity": 1.2
                }
            },
            "file_type_distribution": {
                "component": 25,
                "service": 8,
                "utility": 12,
                "configuration": 6,
                "general": 18
            }
        }
    
    def test_tab_navigation_logic(self):
        """탭 네비게이션 로직 테스트"""
        # Given
        available_tabs = ['overview', 'complexity', 'dependency', 'churn', 'files']
        current_tab = 'overview'
        
        # When & Then
        assert current_tab in available_tabs
        
        # 다음 탭 전환
        next_tab = 'complexity'
        assert next_tab in available_tabs
        assert next_tab != current_tab

    def test_metric_selection_logic(self):
        """메트릭 선택 로직 테스트"""
        # Given
        available_metrics = ['importance', 'complexity', 'risk']
        selected_metric = 'importance'
        
        # When & Then
        assert selected_metric in available_metrics
        
        # 메트릭 변경
        new_metric = 'complexity'
        assert new_metric in available_metrics
        assert new_metric != selected_metric

    def test_file_selection_callback(self, sample_critical_files):
        """파일 선택 콜백 테스트"""
        # Given
        selected_file = None
        
        def mock_file_select_callback(file):
            nonlocal selected_file
            selected_file = file
        
        # When
        mock_file_select_callback(sample_critical_files[0])
        
        # Then
        assert selected_file is not None
        assert selected_file["path"] == "src/App.js"
        assert "importance_score" in selected_file

    def test_data_filtering_logic(self, sample_dashboard_data):
        """데이터 필터링 로직 테스트"""
        # Given
        hotspots = sample_dashboard_data["churn_analysis"]["hotspots"]
        
        # When
        high_complexity_hotspots = [h for h in hotspots if h["complexity"] > 7]
        recent_hotspots = [h for h in hotspots if h["recent_commits"] > 2]
        
        # Then
        assert len(high_complexity_hotspots) == 1  # App.js만
        assert len(recent_hotspots) == 2  # App.js, UserForm.js 둘 다

    def test_color_assignment_logic(self):
        """색상 할당 로직 테스트"""
        # Given
        colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']
        items = ['javascript', 'typescript', 'css', 'html', 'json']
        
        # When
        color_assignments = {
            item: colors[i % len(colors)] 
            for i, item in enumerate(items)
        }
        
        # Then
        assert len(color_assignments) == len(items)
        assert all(color in colors for color in color_assignments.values())
        assert color_assignments['javascript'] == colors[0]

    def test_responsive_layout_logic(self):
        """반응형 레이아웃 로직 테스트"""
        # Given
        screen_sizes = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1440
        }
        
        def get_grid_columns(screen_width):
            if screen_width < screen_sizes['mobile']:
                return 1
            elif screen_width < screen_sizes['tablet']:
                return 2
            else:
                return 3
        
        # When & Then
        assert get_grid_columns(600) == 1  # Mobile
        assert get_grid_columns(900) == 2  # Tablet
        assert get_grid_columns(1500) == 3  # Desktop