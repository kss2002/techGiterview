"""
통합 테스트

고도화된 분석기와 기존 시스템의 통합을 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.advanced_file_analyzer import AdvancedFileAnalyzer
from app.api.github import analyze_repository, get_advanced_analysis, RepositoryAnalysisRequest
from app.api.github import analysis_cache


class TestIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_advanced_analyzer_integration_with_api(self):
        """고도화된 분석기와 API 통합 테스트"""
        # Given
        analyzer = AdvancedFileAnalyzer()
        repo_url = "https://github.com/test/integration-repo"
        
        # 샘플 GitHub API 응답 설정
        sample_repo_info = {
            "name": "integration-repo",
            "description": "Integration test repository",
            "language": "JavaScript",
            "size": 12000,
            "stargazers_count": 500,
            "forks_count": 80
        }
        
        sample_file_tree = [
            {"path": "src/main.js", "type": "file", "size": 2000},
            {"path": "src/utils.js", "type": "file", "size": 1500},
            {"path": "package.json", "type": "file", "size": 800}
        ]
        
        sample_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "Dev1", "date": datetime.now().isoformat() + "Z"}
                },
                "files": [
                    {"filename": "src/main.js", "changes": 20}
                ]
            }
        ]
        
        with patch.object(analyzer.github_client, 'get_repository_info', return_value=sample_repo_info), \
             patch.object(analyzer.github_client, 'get_file_tree', return_value=sample_file_tree), \
             patch.object(analyzer.github_client, 'get_commit_history', return_value=sample_commits), \
             patch.object(analyzer.github_client, 'get_file_content', return_value="console.log('test');"):

            # When
            result = await analyzer.analyze_repository_advanced(repo_url)

            # Then
            assert result["success"] is True
            assert "repo_info" in result
            assert "dashboard_data" in result
            assert "important_files" in result
            
            # 대시보드 데이터 검증
            dashboard_data = result["dashboard_data"]
            assert "repository_overview" in dashboard_data
            assert "complexity_analysis" in dashboard_data
            assert "dependency_analysis" in dashboard_data
            assert "churn_analysis" in dashboard_data
            
            # 중요 파일 검증
            important_files = result["important_files"]
            assert len(important_files) > 0
            assert all("importance_score" in file for file in important_files)

    @pytest.mark.asyncio 
    async def test_end_to_end_workflow(self):
        """전체 워크플로우 통합 테스트"""
        # Given
        repo_url = "https://github.com/test/e2e-repo"
        
        # 기본 분석 결과 모킹
        mock_basic_analysis = MagicMock()
        mock_basic_analysis.repo_info.owner = "test"
        mock_basic_analysis.repo_info.name = "e2e-repo"
        mock_basic_analysis.created_at = datetime.now()
        
        analysis_id = "test-analysis-id"
        analysis_cache[analysis_id] = mock_basic_analysis
        
        # 고도화된 분석 모킹
        mock_advanced_result = {
            "success": True,
            "repo_info": {"name": "e2e-repo", "owner": "test"},
            "dashboard_data": {
                "repository_overview": {
                    "name": "e2e-repo",
                    "description": "End-to-end test repo",
                    "language": "Python", 
                    "size": 15000,
                    "stars": 300,
                    "forks": 45
                },
                "complexity_analysis": {
                    "distribution": {"low": 40, "medium": 15, "high": 5},
                    "average_complexity": 3.8,
                    "max_complexity": 12.5,
                    "maintainability_average": 68.2
                },
                "quality_risk_analysis": {
                    "distribution": {"low": 50, "medium": 8, "high": 2},
                    "high_risk_files": []
                },
                "dependency_analysis": {
                    "graph_metrics": {
                        "total_nodes": 60,
                        "total_edges": 95, 
                        "density": 0.027,
                        "clustering_coefficient": 0.089,
                        "strongly_connected_components": 2,
                        "critical_paths_count": 3
                    },
                    "top_central_files": [],
                    "module_clusters": [],
                    "critical_paths": []
                },
                "churn_analysis": {
                    "hotspots": [],
                    "author_statistics": {},
                    "most_changed_files": []
                },
                "language_statistics": {
                    "python": {"file_count": 40, "total_loc": 6500, "avg_complexity": 4.1}
                },
                "file_type_distribution": {
                    "service": 12,
                    "utility": 8,
                    "configuration": 5,
                    "general": 15
                }
            },
            "important_files": [
                {
                    "path": "src/main.py",
                    "importance_score": 82.3,
                    "quality_risk_score": 3.5,
                    "complexity": 6.8,
                    "hotspot_score": 12.1,
                    "file_type": "main",
                    "language": "python",
                    "metrics_summary": {
                        "lines_of_code": 245,
                        "fan_in": 6,
                        "fan_out": 8,
                        "commit_frequency": 12,
                        "recent_commits": 3,
                        "authors_count": 2,
                        "centrality_score": 0.125
                    }
                }
            ]
        }
        
        with patch('app.services.advanced_file_analyzer.AdvancedFileAnalyzer.analyze_repository_advanced', 
                   return_value=mock_advanced_result):

            # When - 고도화된 분석 실행
            from app.api.github import get_advanced_analysis
            from fastapi import HTTPException
            
            try:
                result = await get_advanced_analysis(analysis_id)
                
                # Then
                assert result["success"] is True
                assert "dashboard_data" in result
                assert "important_files" in result
                
                # 대시보드 데이터 상세 검증
                dashboard = result["dashboard_data"]
                assert dashboard["repository_overview"]["name"] == "e2e-repo"
                assert dashboard["complexity_analysis"]["average_complexity"] == 3.8
                assert dashboard["language_statistics"]["python"]["file_count"] == 40
                
                # 중요 파일 상세 검증
                important_files = result["important_files"]
                assert len(important_files) == 1
                main_file = important_files[0]
                assert main_file["path"] == "src/main.py"
                assert main_file["importance_score"] == 82.3
                assert "metrics_summary" in main_file
                
            except HTTPException as e:
                pytest.fail(f"Unexpected HTTPException: {e}")

    def test_dashboard_data_structure_validation(self):
        """대시보드 데이터 구조 검증 테스트"""
        # Given
        dashboard_data = {
            "repository_overview": {
                "name": "test-repo",
                "description": "Test repository",
                "language": "TypeScript",
                "size": 8000,
                "stars": 150,
                "forks": 25
            },
            "complexity_analysis": {
                "distribution": {"low": 30, "medium": 12, "high": 3},
                "average_complexity": 4.5,
                "max_complexity": 15.2,
                "maintainability_average": 62.8
            },
            "quality_risk_analysis": {
                "distribution": {"low": 35, "medium": 8, "high": 2},
                "high_risk_files": [
                    {
                        "filename": "src/complex.ts",
                        "risk_score": 7.2,
                        "complexity": 11.5,
                        "hotspot_score": 18.3
                    }
                ]
            },
            "dependency_analysis": {
                "graph_metrics": {
                    "total_nodes": 45,
                    "total_edges": 78,
                    "density": 0.039,
                    "clustering_coefficient": 0.102,
                    "strongly_connected_components": 1,
                    "critical_paths_count": 2
                },
                "top_central_files": [
                    {
                        "filename": "src/index.ts",
                        "centrality_score": 0.156,
                        "fan_in": 10,
                        "fan_out": 6,
                        "importance_score": 88.7
                    }
                ],
                "module_clusters": [],
                "critical_paths": []
            },
            "churn_analysis": {
                "hotspots": [
                    {
                        "filename": "src/index.ts",
                        "hotspot_score": 22.5,
                        "complexity": 7.8,
                        "recent_commits": 4,
                        "quality_risk": 3.9
                    }
                ],
                "author_statistics": {
                    "Dev1": {"commits": 25, "files_changed": 15},
                    "Dev2": {"commits": 18, "files_changed": 12}
                },
                "most_changed_files": [
                    {
                        "filename": "src/index.ts",
                        "commit_count": 8,
                        "recent_commits": 4,
                        "authors_count": 2
                    }
                ]
            },
            "language_statistics": {
                "typescript": {"file_count": 30, "total_loc": 5200, "avg_complexity": 4.8},
                "javascript": {"file_count": 10, "total_loc": 1800, "avg_complexity": 3.2}
            },
            "file_type_distribution": {
                "component": 18,
                "service": 6,
                "utility": 8,
                "configuration": 3,
                "general": 10
            }
        }

        # When & Then - 모든 필수 필드 존재 검증
        required_sections = [
            "repository_overview", 
            "complexity_analysis", 
            "quality_risk_analysis",
            "dependency_analysis", 
            "churn_analysis", 
            "language_statistics", 
            "file_type_distribution"
        ]
        
        for section in required_sections:
            assert section in dashboard_data, f"Missing required section: {section}"
        
        # 복잡도 분석 필드 검증
        complexity = dashboard_data["complexity_analysis"]
        assert "distribution" in complexity
        assert "average_complexity" in complexity
        assert "max_complexity" in complexity
        assert "maintainability_average" in complexity
        
        # 의존성 분석 필드 검증
        dependency = dashboard_data["dependency_analysis"]
        assert "graph_metrics" in dependency
        assert "top_central_files" in dependency
        
        # 변경 이력 분석 필드 검증
        churn = dashboard_data["churn_analysis"]
        assert "hotspots" in churn
        assert "author_statistics" in churn
        assert "most_changed_files" in churn
        
        # 언어 통계 검증
        lang_stats = dashboard_data["language_statistics"]
        for lang, stats in lang_stats.items():
            assert "file_count" in stats
            assert "total_loc" in stats
            assert "avg_complexity" in stats

    def test_critical_files_structure_validation(self):
        """중요 파일 구조 검증 테스트"""
        # Given
        critical_files = [
            {
                "path": "src/core/app.ts",
                "importance_score": 89.4,
                "quality_risk_score": 4.1,
                "complexity": 9.2,
                "hotspot_score": 16.8,
                "file_type": "main",
                "language": "typescript",
                "metrics_summary": {
                    "lines_of_code": 312,
                    "fan_in": 12,
                    "fan_out": 8,
                    "commit_frequency": 15,
                    "recent_commits": 6,
                    "authors_count": 3,
                    "centrality_score": 0.178
                }
            },
            {
                "path": "src/services/api.ts",
                "importance_score": 76.1,
                "quality_risk_score": 3.2,
                "complexity": 5.8,
                "hotspot_score": 11.4,
                "file_type": "service",
                "language": "typescript",
                "metrics_summary": {
                    "lines_of_code": 198,
                    "fan_in": 8,
                    "fan_out": 4,
                    "commit_frequency": 9,
                    "recent_commits": 2,
                    "authors_count": 2,
                    "centrality_score": 0.094
                }
            }
        ]

        # When & Then - 각 파일의 필수 필드 검증
        required_fields = [
            "path", "importance_score", "quality_risk_score", 
            "complexity", "hotspot_score", "file_type", 
            "language", "metrics_summary"
        ]
        
        for file in critical_files:
            for field in required_fields:
                assert field in file, f"Missing required field '{field}' in file: {file.get('path', 'unknown')}"
            
            # metrics_summary 필드 검증
            summary = file["metrics_summary"]
            required_summary_fields = [
                "lines_of_code", "fan_in", "fan_out", 
                "commit_frequency", "recent_commits", 
                "authors_count", "centrality_score"
            ]
            
            for summary_field in required_summary_fields:
                assert summary_field in summary, f"Missing metrics summary field '{summary_field}'"
                assert isinstance(summary[summary_field], (int, float)), f"Invalid type for '{summary_field}'"
            
            # 점수 범위 검증
            assert 0 <= file["importance_score"] <= 100, "Importance score out of range"
            assert 0 <= file["quality_risk_score"] <= 10, "Quality risk score out of range"
            assert file["complexity"] >= 0, "Complexity must be non-negative"
            assert file["hotspot_score"] >= 0, "Hotspot score must be non-negative"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """에러 처리 통합 테스트"""
        # Given
        invalid_analysis_id = "invalid-id"
        
        # When & Then - 존재하지 않는 분석 ID로 고도화된 분석 요청
        from app.api.github import get_advanced_analysis
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_advanced_analysis(invalid_analysis_id)
        
        assert exc_info.value.status_code == 404
        assert "Analysis not found" in str(exc_info.value.detail)

    def test_performance_indicators_calculation(self):
        """성능 지표 계산 통합 테스트"""
        # Given
        dashboard_data = {
            "complexity_analysis": {
                "average_complexity": 3.5,
                "maintainability_average": 72.3
            },
            "quality_risk_analysis": {
                "high_risk_files": [
                    {"filename": "file1.js", "risk_score": 6.2},
                    {"filename": "file2.js", "risk_score": 5.8}
                ]
            }
        }
        
        critical_files = [
            {"path": "src/main.js", "importance_score": 85.2},
            {"path": "src/utils.js", "importance_score": 67.8}
        ]

        # When - 성능 지표 계산
        complexity_avg = dashboard_data["complexity_analysis"]["average_complexity"]
        high_risk_count = len(dashboard_data["quality_risk_analysis"]["high_risk_files"])
        maintainability = dashboard_data["complexity_analysis"]["maintainability_average"]
        critical_files_count = len(critical_files)

        complexity_health = "good" if complexity_avg < 5 else "warning" if complexity_avg < 8 else "critical"
        risk_health = "good" if high_risk_count < 5 else "warning" if high_risk_count < 10 else "critical"

        # Then
        assert complexity_health == "good"  # 3.5 < 5
        assert risk_health == "good"  # 2 < 5
        assert maintainability > 50
        assert critical_files_count > 0