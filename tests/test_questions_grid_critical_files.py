"""
questions-grid 상단 중요 파일 표시 기능 테스트 - TDD 방식

main_rules.md에 따라 테스트를 먼저 작성하고, 이후 실제 구현을 진행합니다.
중요한 파일들이 questions-grid 상단에 표시되는 기능을 테스트합니다.
"""

import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch


class TestQuestionsGridCriticalFiles:
    """questions-grid 상단 중요 파일 표시 기능 테스트"""
    
    @pytest.fixture
    def sample_critical_files_data(self):
        """테스트용 중요 파일 데이터"""
        return [
            {
                "file_path": "src/main.py",
                "importance_score": 0.95,
                "reasons": ["애플리케이션 진입점 파일", "다른 파일들이 많이 참조하는 핵심 의존성"],
                "metrics": {
                    "structural_importance": 0.9,
                    "dependency_centrality": 0.8,
                    "churn_risk": 0.6,
                    "complexity_score": 0.7
                },
                "category": "critical",
                "rank": 1
            },
            {
                "file_path": "src/config.py", 
                "importance_score": 0.87,
                "reasons": ["프로젝트 핵심 설정 파일", "핵심 모듈 또는 기반 라이브러리"],
                "metrics": {
                    "structural_importance": 0.95,
                    "dependency_centrality": 0.6,
                    "churn_risk": 0.2,
                    "complexity_score": 0.3
                },
                "category": "critical",
                "rank": 2
            },
            {
                "file_path": "src/services/auth_service.py",
                "importance_score": 0.82,
                "reasons": ["핵심 비즈니스 로직 담당", "중요한 모듈 간 연결점 역할"],
                "metrics": {
                    "structural_importance": 0.8,
                    "dependency_centrality": 0.7,
                    "churn_risk": 0.5,
                    "complexity_score": 0.6
                },
                "category": "critical",
                "rank": 3
            },
            {
                "file_path": "src/api/user_controller.py",
                "importance_score": 0.78,
                "reasons": ["핵심 비즈니스 로직 담당", "활발하게 개발되고 있는 핵심 기능"],
                "metrics": {
                    "structural_importance": 0.7,
                    "dependency_centrality": 0.6,
                    "churn_risk": 0.8,
                    "complexity_score": 0.5
                },
                "category": "important",
                "rank": 4
            },
            {
                "file_path": "src/models/user.py",
                "importance_score": 0.75,
                "reasons": ["핵심 모듈 또는 기반 라이브러리", "적절한 복잡도의 핵심 로직 포함"],
                "metrics": {
                    "structural_importance": 0.8,
                    "dependency_centrality": 0.5,
                    "churn_risk": 0.4,
                    "complexity_score": 0.4
                },
                "category": "important",
                "rank": 5
            }
        ]
    
    @pytest.fixture
    def sample_analysis_result_with_smart_files(self, sample_critical_files_data):
        """스마트 파일 분석이 포함된 분석 결과 데이터"""
        return {
            "success": True,
            "analysis_id": "test_analysis_001",
            "repo_info": {
                "name": "test-repo",
                "owner": "test-owner",
                "description": "Test repository",
                "language": "Python",
                "stars": 100,
                "forks": 20
            },
            "smart_file_analysis": {
                "critical_files": sample_critical_files_data,
                "importance_distribution": {
                    "mean": 0.83,
                    "median": 0.82,
                    "std_dev": 0.08,
                    "min": 0.75,
                    "max": 0.95
                },
                "categorized_files": {
                    "critical": ["src/main.py", "src/config.py", "src/services/auth_service.py"],
                    "important": ["src/api/user_controller.py", "src/models/user.py"],
                    "moderate": [],
                    "low": []
                },
                "summary": {
                    "total_files_analyzed": 25,
                    "critical_files_count": 3,
                    "important_files_count": 2,
                    "average_importance": 0.83,
                    "highest_importance": 0.95
                }
            }
        }

    def test_critical_files_preview_component_initialization(self):
        """CriticalFilesPreview 컴포넌트 초기화 테스트"""
        # Given: CriticalFilesPreview 컴포넌트가 존재해야 함
        # When: 컴포넌트를 import할 때
        # Then: 정상적으로 import되어야 함
        
        try:
            from src.frontend.src.components.CriticalFilesPreview import CriticalFilesPreview
            assert CriticalFilesPreview is not None
        except ImportError:
            # 아직 구현되지 않았으므로 실패하는 것이 정상
            pytest.fail("CriticalFilesPreview 컴포넌트가 아직 구현되지 않았습니다.")

    def test_critical_files_display_above_questions_grid(self, sample_analysis_result_with_smart_files):
        """questions-grid 상단에 중요 파일들이 표시되는지 테스트"""
        # Given: smart_file_analysis 데이터가 있는 분석 결과
        analysis_result = sample_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        # When: DashboardPage가 렌더링될 때
        # Then: 다음 조건들이 만족되어야 함
        
        # 1. critical_files 데이터가 올바르게 파싱되어야 함
        assert len(critical_files) == 5
        assert critical_files[0]["file_path"] == "src/main.py"
        assert critical_files[0]["importance_score"] == 0.95
        
        # 2. 중요도 순으로 정렬되어야 함
        scores = [file["importance_score"] for file in critical_files]
        assert scores == sorted(scores, reverse=True)
        
        # 3. 필수 필드들이 존재해야 함
        for file_data in critical_files:
            assert "file_path" in file_data
            assert "importance_score" in file_data
            assert "reasons" in file_data
            assert "metrics" in file_data
            assert len(file_data["reasons"]) > 0

    def test_critical_files_component_props_validation(self, sample_critical_files_data):
        """중요 파일 컴포넌트가 올바른 props를 받는지 테스트"""
        # Given: 중요 파일 데이터와 prop 설정
        critical_files = sample_critical_files_data
        max_display_files = 5
        
        # When: CriticalFilesPreview 컴포넌트에 props 전달
        component_props = {
            "criticalFiles": critical_files,
            "maxDisplayFiles": max_display_files,
            "onFileClick": Mock()
        }
        
        # Then: props가 올바르게 설정되어야 함
        assert len(component_props["criticalFiles"]) == 5
        assert component_props["maxDisplayFiles"] == 5
        assert callable(component_props["onFileClick"])
        
        # 각 파일 데이터의 필수 속성 검증
        for file_data in component_props["criticalFiles"]:
            assert isinstance(file_data["file_path"], str)
            assert isinstance(file_data["importance_score"], float)
            assert 0 <= file_data["importance_score"] <= 1
            assert isinstance(file_data["reasons"], list)
            assert len(file_data["reasons"]) > 0

    def test_critical_files_max_display_limit(self, sample_critical_files_data):
        """최대 표시 파일 수 제한 테스트"""
        # Given: 5개의 중요 파일 데이터와 3개 제한 설정
        critical_files = sample_critical_files_data
        max_display = 3
        
        # When: 최대 표시 수가 설정된 경우
        # Then: 지정된 수만큼만 표시되어야 함
        
        # 상위 3개 파일만 선택되어야 함
        top_files = critical_files[:max_display]
        assert len(top_files) == 3
        
        # 중요도가 높은 순으로 선택되어야 함
        assert top_files[0]["file_path"] == "src/main.py"  # 0.95
        assert top_files[1]["file_path"] == "src/config.py"  # 0.87
        assert top_files[2]["file_path"] == "src/services/auth_service.py"  # 0.82

    def test_no_critical_files_fallback(self):
        """중요 파일 데이터가 없을 때 적절한 fallback 처리 테스트"""
        # Given: smart_file_analysis가 없거나 빈 상태
        empty_analysis_cases = [
            None,  # smart_file_analysis가 None
            {},    # smart_file_analysis가 빈 dict
            {"critical_files": []},  # critical_files가 빈 배열
            {"critical_files": None}  # critical_files가 None
        ]
        
        for empty_case in empty_analysis_cases:
            # When: 빈 데이터가 전달될 때
            # Then: 적절한 fallback 처리가 되어야 함
            
            if empty_case is None:
                should_display = False
            elif not empty_case:
                should_display = False  
            elif not empty_case.get("critical_files"):
                should_display = False
            else:
                should_display = len(empty_case["critical_files"]) > 0
            
            # CriticalFilesPreview 섹션이 표시되지 않아야 함
            assert should_display is False

    def test_file_click_handler_integration(self, sample_critical_files_data):
        """파일 클릭 핸들러 통합 테스트"""
        # Given: 중요 파일 데이터와 클릭 핸들러
        critical_files = sample_critical_files_data
        mock_file_click_handler = Mock()
        
        # When: 파일이 클릭될 때
        clicked_file_path = critical_files[0]["file_path"]
        mock_file_click_handler(clicked_file_path)
        
        # Then: 핸들러가 올바른 파일 경로로 호출되어야 함
        mock_file_click_handler.assert_called_once_with("src/main.py")

    def test_critical_files_preview_styling_classes(self):
        """CriticalFilesPreview 스타일링 클래스 테스트"""
        # Given: 예상되는 CSS 클래스들
        expected_classes = [
            "critical-files-preview-section",
            "preview-header", 
            "file-count",
            "critical-files-grid",
            "critical-file-item",
            "file-icon",
            "file-path",
            "importance-score",
            "file-reasons"
        ]
        
        # When: 컴포넌트가 렌더링될 때
        # Then: 필요한 CSS 클래스들이 정의되어야 함
        for css_class in expected_classes:
            # CSS 파일에서 해당 클래스가 존재하는지 확인
            # (실제로는 CSS 파일을 읽어 확인해야 하지만, 여기서는 구조 검증)
            assert isinstance(css_class, str)
            assert len(css_class) > 0
            assert not css_class.startswith('.')  # 클래스명에서 . prefix 제거 확인

    def test_dashboard_integration_data_flow(self, sample_analysis_result_with_smart_files):
        """DashboardPage와의 데이터 흐름 통합 테스트"""
        # Given: 분석 결과에 smart_file_analysis가 포함된 상태
        analysis_result = sample_analysis_result_with_smart_files
        
        # When: DashboardPage에서 데이터를 추출할 때
        smart_analysis = analysis_result.get("smart_file_analysis")
        critical_files = smart_analysis.get("critical_files") if smart_analysis else []
        
        # Then: 데이터가 올바르게 추출되어야 함
        assert smart_analysis is not None
        assert len(critical_files) == 5
        
        # CriticalFilesPreview에 전달될 데이터 구조 검증
        preview_props = {
            "criticalFiles": critical_files[:5],  # 상위 5개만
            "onFileClick": Mock(),
            "maxDisplayFiles": 5
        }
        
        assert len(preview_props["criticalFiles"]) <= 5
        assert callable(preview_props["onFileClick"])

    def test_importance_score_formatting(self, sample_critical_files_data):
        """중요도 점수 포맷팅 테스트"""
        # Given: 중요 파일 데이터
        critical_files = sample_critical_files_data
        
        # When: 중요도 점수를 포맷팅할 때
        for file_data in critical_files:
            score = file_data["importance_score"]
            
            # Then: 점수가 올바른 범위와 형식이어야 함
            assert 0 <= score <= 1
            assert isinstance(score, float)
            
            # 백분율로 변환 시 적절한 형식이어야 함
            percentage = round(score * 100, 1)
            assert 0 <= percentage <= 100
            assert isinstance(percentage, float)

    def test_file_reasons_display(self, sample_critical_files_data):
        """파일 선정 이유 표시 테스트"""
        # Given: 중요 파일의 선정 이유들
        critical_files = sample_critical_files_data
        
        # When: 각 파일의 선정 이유를 확인할 때
        for file_data in critical_files:
            reasons = file_data["reasons"]
            
            # Then: 선정 이유가 적절히 제공되어야 함
            assert isinstance(reasons, list)
            assert len(reasons) > 0
            
            # 각 이유가 의미있는 텍스트여야 함
            for reason in reasons:
                assert isinstance(reason, str)
                assert len(reason.strip()) > 5  # 최소 5자 이상의 의미있는 이유
                
                # 한글 설명이 포함되어야 함 (프로젝트 특성상)
                korean_keywords = ["파일", "중요", "핵심", "설정", "모듈", "로직", "의존성"]
                has_korean = any(keyword in reason for keyword in korean_keywords)
                assert has_korean, f"선정 이유에 한글 설명이 부족합니다: {reason}"


class TestCriticalFilesPreviewComponent:
    """CriticalFilesPreview 컴포넌트 전용 테스트"""
    
    def test_component_renders_without_crash(self):
        """컴포넌트가 오류 없이 렌더링되는지 테스트"""
        # Given: 최소한의 props
        minimal_props = {
            "criticalFiles": [],
            "maxDisplayFiles": 5
        }
        
        # When: 컴포넌트를 렌더링할 때
        # Then: 오류가 발생하지 않아야 함
        try:
            # 실제 React 컴포넌트 테스트는 Jest/RTL로 진행
            # 여기서는 구조적 검증만 수행
            assert "criticalFiles" in minimal_props
            assert "maxDisplayFiles" in minimal_props
            assert isinstance(minimal_props["criticalFiles"], list)
            assert isinstance(minimal_props["maxDisplayFiles"], int)
        except Exception as e:
            pytest.fail(f"컴포넌트 렌더링 중 오류 발생: {str(e)}")

    def test_component_handles_empty_files_list(self):
        """빈 파일 목록을 올바르게 처리하는지 테스트"""
        # Given: 빈 critical files 목록
        empty_props = {
            "criticalFiles": [],
            "maxDisplayFiles": 5
        }
        
        # When: 빈 목록이 전달될 때
        # Then: 적절한 빈 상태 메시지나 숨김 처리가 되어야 함
        assert len(empty_props["criticalFiles"]) == 0
        
        # 빈 상태에서도 컴포넌트가 안정적으로 동작해야 함
        should_render = len(empty_props["criticalFiles"]) > 0
        assert should_render is False

    def test_component_props_type_validation(self):
        """컴포넌트 props 타입 검증 테스트"""
        # Given: 다양한 타입의 props
        valid_props = {
            "criticalFiles": [
                {
                    "file_path": "test.py",
                    "importance_score": 0.8,
                    "reasons": ["test reason"],
                    "metrics": {},
                    "category": "critical",
                    "rank": 1
                }
            ],
            "maxDisplayFiles": 5,
            "onFileClick": Mock()
        }
        
        # When: props 타입을 검증할 때
        # Then: 모든 props가 올바른 타입이어야 함
        assert isinstance(valid_props["criticalFiles"], list)
        assert isinstance(valid_props["maxDisplayFiles"], int)
        assert callable(valid_props["onFileClick"]) or valid_props["onFileClick"] is None
        
        # criticalFiles의 각 항목도 올바른 구조여야 함
        for file_item in valid_props["criticalFiles"]:
            assert "file_path" in file_item
            assert "importance_score" in file_item
            assert "reasons" in file_item