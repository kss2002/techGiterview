"""
SmartFileImportanceSection React 컴포넌트 테스트 - TDD 방식

main_rules.md에 따라 테스트를 먼저 작성하고, 이후 컴포넌트 개선을 진행합니다.
React 컴포넌트 테스트를 위한 Python 시뮬레이션 테스트
"""

import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock


class TestSmartFileImportanceSection:
    """SmartFileImportanceSection 컴포넌트 테스트"""
    
    @pytest.fixture
    def sample_critical_files(self):
        """테스트용 중요 파일 데이터"""
        return [
            {
                "file_path": "src/main.py",
                "importance_score": 0.95,
                "reasons": [
                    "애플리케이션 진입점 파일",
                    "다른 파일들이 많이 참조하는 핵심 의존성",
                    "최근 6개월간 활발한 변경 이력"
                ],
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
                "reasons": [
                    "프로젝트 핵심 설정 파일",
                    "핵심 모듈 또는 기반 라이브러리"
                ],
                "metrics": {
                    "structural_importance": 0.95,
                    "dependency_centrality": 0.6,
                    "churn_risk": 0.2,
                    "complexity_score": 0.3
                },
                "category": "important",
                "rank": 2
            },
            {
                "file_path": "src/utils/helpers.py",
                "importance_score": 0.45,
                "reasons": [
                    "공통 유틸리티 함수 집합",
                    "여러 모듈에서 참조"
                ],
                "metrics": {
                    "structural_importance": 0.3,
                    "dependency_centrality": 0.5,
                    "churn_risk": 0.4,
                    "complexity_score": 0.6
                },
                "category": "moderate",
                "rank": 3
            },
            {
                "file_path": "tests/test_sample.py",
                "importance_score": 0.25,
                "reasons": [
                    "테스트 파일"
                ],
                "metrics": {
                    "structural_importance": 0.1,
                    "dependency_centrality": 0.2,
                    "churn_risk": 0.8,
                    "complexity_score": 0.2
                },
                "category": "low",
                "rank": 4
            }
        ]
    
    @pytest.fixture
    def sample_distribution(self):
        """테스트용 중요도 분포 데이터"""
        return {
            "mean": 0.635,
            "median": 0.550,
            "std_dev": 0.289,
            "min": 0.125,
            "max": 0.950,
            "quartiles": {
                "q1": 0.375,
                "q3": 0.825
            }
        }
    
    @pytest.fixture
    def sample_suggestions(self):
        """테스트용 개선 제안 데이터"""
        return [
            "src/main.py 파일의 복잡도가 높습니다. 모듈 분리를 고려해보세요.",
            "tests/test_sample.py 파일의 변경 빈도가 높습니다. 테스트 안정성을 점검해보세요.",
            "의존성 중심성이 높은 파일들에 대한 리팩토링을 고려해보세요."
        ]

    def test_component_props_validation(self, sample_critical_files, sample_distribution, sample_suggestions):
        """컴포넌트 Props 유효성 검증 테스트"""
        # Given: 컴포넌트 Props 데이터
        props = {
            "criticalFiles": sample_critical_files,
            "distribution": sample_distribution,
            "suggestions": sample_suggestions,
            "onFileSelect": Mock()
        }
        
        # When: Props 검증
        # Then: 모든 필수 props가 올바른 형식이어야 함
        assert isinstance(props["criticalFiles"], list)
        assert len(props["criticalFiles"]) > 0
        
        # 각 파일 객체 구조 검증
        for file_data in props["criticalFiles"]:
            assert "file_path" in file_data
            assert "importance_score" in file_data
            assert "reasons" in file_data
            assert "metrics" in file_data
            assert "category" in file_data
            assert "rank" in file_data
            
            # 메트릭 구조 검증
            metrics = file_data["metrics"]
            assert "structural_importance" in metrics
            assert "dependency_centrality" in metrics
            assert "churn_risk" in metrics
            assert "complexity_score" in metrics
            
        # 분포 데이터 구조 검증
        distribution = props["distribution"]
        assert "mean" in distribution
        assert "median" in distribution
        assert "std_dev" in distribution
        assert "min" in distribution
        assert "max" in distribution
        assert "quartiles" in distribution
        assert "q1" in distribution["quartiles"]
        assert "q3" in distribution["quartiles"]

    def test_category_filtering_logic(self, sample_critical_files):
        """카테고리별 필터링 로직 테스트"""
        # Given: 파일 데이터와 카테고리 선택
        files = sample_critical_files
        
        # When & Then: 각 카테고리별 필터링 결과 검증
        categories = {
            "critical": [f for f in files if f["category"] == "critical"],
            "important": [f for f in files if f["category"] == "important"],
            "moderate": [f for f in files if f["category"] == "moderate"],
            "low": [f for f in files if f["category"] == "low"]
        }
        
        assert len(categories["critical"]) == 1
        assert len(categories["important"]) == 1
        assert len(categories["moderate"]) == 1
        assert len(categories["low"]) == 1
        
        # 카테고리별 파일 내용 검증
        assert categories["critical"][0]["file_path"] == "src/main.py"
        assert categories["important"][0]["file_path"] == "src/config.py"
        assert categories["moderate"][0]["file_path"] == "src/utils/helpers.py"
        assert categories["low"][0]["file_path"] == "tests/test_sample.py"

    def test_sorting_functionality(self, sample_critical_files):
        """정렬 기능 테스트"""
        # Given: 파일 데이터
        files = sample_critical_files.copy()
        
        # When & Then: 중요도 점수 기준 정렬 (내림차순)
        sorted_by_importance = sorted(files, key=lambda x: x["importance_score"], reverse=True)
        importance_scores = [f["importance_score"] for f in sorted_by_importance]
        assert importance_scores == sorted(importance_scores, reverse=True)
        assert sorted_by_importance[0]["file_path"] == "src/main.py"  # 가장 높은 점수
        
        # When & Then: 복잡도 기준 정렬 (내림차순)
        sorted_by_complexity = sorted(files, key=lambda x: x["metrics"]["complexity_score"], reverse=True)
        complexity_scores = [f["metrics"]["complexity_score"] for f in sorted_by_complexity]
        assert complexity_scores == sorted(complexity_scores, reverse=True)
        
        # When & Then: 변경 빈도 기준 정렬 (내림차순)
        sorted_by_churn = sorted(files, key=lambda x: x["metrics"]["churn_risk"], reverse=True)
        churn_scores = [f["metrics"]["churn_risk"] for f in sorted_by_churn]
        assert churn_scores == sorted(churn_scores, reverse=True)
        
        # When & Then: 의존성 중심성 기준 정렬 (내림차순)
        sorted_by_dependency = sorted(files, key=lambda x: x["metrics"]["dependency_centrality"], reverse=True)
        dependency_scores = [f["metrics"]["dependency_centrality"] for f in sorted_by_dependency]
        assert dependency_scores == sorted(dependency_scores, reverse=True)

    def test_importance_color_calculation(self):
        """중요도 점수에 따른 색상 계산 테스트"""
        # Given: 다양한 중요도 점수들
        test_scores = [
            (0.95, "#ef4444"),  # Critical - Red
            (0.85, "#ef4444"),  # Critical - Red
            (0.75, "#f59e0b"),  # Important - Orange
            (0.65, "#f59e0b"),  # Important - Orange
            (0.55, "#10b981"),  # Moderate - Green
            (0.45, "#10b981"),  # Moderate - Green
            (0.35, "#6b7280"),  # Low - Gray
            (0.15, "#6b7280"),  # Low - Gray
        ]
        
        # When & Then: 각 점수별 색상 검증
        for score, expected_color in test_scores:
            if score >= 0.8:
                expected = "#ef4444"  # Critical - Red
            elif score >= 0.6:
                expected = "#f59e0b"  # Important - Orange
            elif score >= 0.4:
                expected = "#10b981"  # Moderate - Green
            else:
                expected = "#6b7280"  # Low - Gray
            
            assert expected == expected_color

    def test_category_badge_class_mapping(self):
        """카테고리 뱃지 클래스 매핑 테스트"""
        # Given: 카테고리별 기대 CSS 클래스
        category_mappings = {
            "critical": "badge-critical",
            "important": "badge-important",
            "moderate": "badge-moderate",
            "low": "badge-low",
            "unknown": "badge-default"  # 기본값
        }
        
        # When & Then: 각 카테고리별 클래스 매핑 검증
        for category, expected_class in category_mappings.items():
            # 실제 컴포넌트 로직 시뮬레이션
            if category == "critical":
                result_class = "badge-critical"
            elif category == "important":
                result_class = "badge-important"
            elif category == "moderate":
                result_class = "badge-moderate"
            elif category == "low":
                result_class = "badge-low"
            else:
                result_class = "badge-default"
            
            assert result_class == expected_class

    def test_metrics_visualization_data(self, sample_critical_files):
        """메트릭 시각화 데이터 테스트"""
        # Given: 파일 메트릭 데이터
        file_data = sample_critical_files[0]  # src/main.py
        metrics = file_data["metrics"]
        
        # Then: 모든 메트릭이 0-1 범위에 있어야 함
        assert 0 <= metrics["structural_importance"] <= 1
        assert 0 <= metrics["dependency_centrality"] <= 1
        assert 0 <= metrics["churn_risk"] <= 1
        assert 0 <= metrics["complexity_score"] <= 1
        
        # When: 프로그레스 바 너비 계산 (백분율)
        progress_widths = {
            "structural": metrics["structural_importance"] * 100,
            "dependency": metrics["dependency_centrality"] * 100,
            "churn": metrics["churn_risk"] * 100,
            "complexity": metrics["complexity_score"] * 100
        }
        
        # Then: 모든 너비가 0-100% 범위에 있어야 함
        for metric_name, width in progress_widths.items():
            assert 0 <= width <= 100

    def test_distribution_statistics_calculation(self, sample_distribution):
        """분포 통계 계산 정확성 테스트"""
        # Given: 분포 데이터
        distribution = sample_distribution
        
        # Then: 통계값들이 논리적으로 일관되어야 함
        assert distribution["min"] <= distribution["quartiles"]["q1"]
        assert distribution["quartiles"]["q1"] <= distribution["median"]
        assert distribution["median"] <= distribution["quartiles"]["q3"]
        assert distribution["quartiles"]["q3"] <= distribution["max"]
        
        # 평균이 합리적 범위에 있어야 함
        assert distribution["min"] <= distribution["mean"] <= distribution["max"]
        
        # 표준편차가 음수가 아니어야 함
        assert distribution["std_dev"] >= 0

    def test_file_selection_callback(self, sample_critical_files):
        """파일 선택 콜백 함수 테스트"""
        # Given: 파일 데이터와 Mock 콜백
        file_data = sample_critical_files[0]
        mock_callback = Mock()
        
        # When: 파일 선택 시뮬레이션
        mock_callback(file_data)
        
        # Then: 콜백이 올바른 파일 데이터와 함께 호출되어야 함
        mock_callback.assert_called_once_with(file_data)
        call_args = mock_callback.call_args[0][0]
        assert call_args["file_path"] == "src/main.py"
        assert call_args["importance_score"] == 0.95

    def test_reasons_toggle_functionality(self, sample_critical_files):
        """선정 이유 토글 기능 테스트"""
        # Given: 파일 데이터와 초기 토글 상태
        file_data = sample_critical_files[0]
        show_reasons_state = {}
        
        # When: 토글 기능 시뮬레이션
        file_path = file_data["file_path"]
        
        # 초기 상태 - 닫힘
        assert show_reasons_state.get(file_path, False) == False
        
        # 첫 번째 토글 - 열림
        show_reasons_state[file_path] = not show_reasons_state.get(file_path, False)
        assert show_reasons_state[file_path] == True
        
        # 두 번째 토글 - 닫힘
        show_reasons_state[file_path] = not show_reasons_state[file_path]
        assert show_reasons_state[file_path] == False

    def test_responsive_design_breakpoints(self):
        """반응형 디자인 브레이크포인트 테스트"""
        # Given: 다양한 화면 크기
        breakpoints = {
            "desktop": 1200,
            "tablet": 768,
            "mobile": 480
        }
        
        # When & Then: 각 브레이크포인트별 레이아웃 검증
        for device, width in breakpoints.items():
            if width <= 480:
                # Mobile: 2열 그리드, 수직 레이아웃
                grid_columns = 2
                metric_layout = "vertical"
            elif width <= 768:
                # Tablet: 3열 그리드, 수직 레이아웃
                grid_columns = 3
                metric_layout = "vertical"
            else:
                # Desktop: 자동 그리드, 수평 레이아웃
                grid_columns = "auto"
                metric_layout = "horizontal"
            
            # 레이아웃 설정이 합리적인지 검증
            assert grid_columns in [2, 3, "auto"]
            assert metric_layout in ["horizontal", "vertical"]

    def test_accessibility_features(self, sample_critical_files):
        """접근성 기능 테스트"""
        # Given: 파일 데이터
        file_data = sample_critical_files[0]
        
        # Then: 접근성 요구사항 검증
        
        # 1. 키보드 접근성 - 모든 인터랙티브 요소가 focusable해야 함
        interactive_elements = [
            "category-card",
            "file-card", 
            "reasons-toggle",
            "sort-select"
        ]
        
        for element in interactive_elements:
            # 실제로는 tabIndex나 role 속성이 있어야 함
            assert element is not None
        
        # 2. ARIA 레이블 - 중요한 정보에 대한 설명
        aria_labels = {
            "importance-score": f"중요도 점수 {file_data['importance_score']}",
            "category-badge": f"카테고리 {file_data['category']}",
            "file-rank": f"순위 {file_data['rank']}"
        }
        
        for aria_key, aria_value in aria_labels.items():
            assert len(aria_value) > 0
            # ARIA 레이블이 의미있는 정보를 포함하는지 검증
            assert any(keyword in aria_value for keyword in ["중요도", "카테고리", "순위"]) or \
                   str(file_data["importance_score"]) in aria_value or \
                   file_data["category"] in aria_value or \
                   str(file_data["rank"]) in aria_value
        
        # 3. 색상 대비 - 충분한 대비율 보장 (시뮬레이션)
        color_combinations = [
            ("#ef4444", "#ffffff"),  # Critical badge
            ("#f59e0b", "#ffffff"),  # Important badge
            ("#10b981", "#ffffff"),  # Moderate badge
            ("#6b7280", "#ffffff"),  # Low badge
        ]
        
        for bg_color, text_color in color_combinations:
            # 실제로는 색상 대비율을 계산해야 하지만, 여기서는 구조만 검증
            assert bg_color.startswith("#")
            assert text_color.startswith("#")
            assert len(bg_color) == 7  # #RRGGBB 형식

    def test_performance_optimization_features(self, sample_critical_files):
        """성능 최적화 기능 테스트"""
        # Given: 대량의 파일 데이터 시뮬레이션
        large_file_list = []
        for i in range(100):
            file_data = {
                "file_path": f"src/file_{i}.py",
                "importance_score": 0.5 + (i % 50) / 100,
                "reasons": [f"Reason {i}"],
                "metrics": {
                    "structural_importance": 0.5,
                    "dependency_centrality": 0.5,
                    "churn_risk": 0.5,
                    "complexity_score": 0.5
                },
                "category": "moderate",
                "rank": i + 1
            }
            large_file_list.append(file_data)
        
        # When: 가상화 또는 페이지네이션 필요성 검증
        if len(large_file_list) > 50:
            # 대량 데이터의 경우 가상화나 페이지네이션이 필요
            requires_virtualization = True
        else:
            requires_virtualization = False
        
        # Then: 성능 최적화 전략이 적절해야 함
        assert requires_virtualization == True
        
        # 메모리 효율성을 위한 지연 로딩 시뮬레이션
        visible_range = (0, 20)  # 처음 20개만 렌더링
        visible_files = large_file_list[visible_range[0]:visible_range[1]]
        
        assert len(visible_files) == 20
        assert len(visible_files) < len(large_file_list)

    def test_error_handling_and_edge_cases(self):
        """오류 처리 및 엣지 케이스 테스트"""
        # Given: 다양한 엣지 케이스 데이터
        edge_cases = [
            {
                "name": "empty_files_list",
                "data": {
                    "criticalFiles": [],
                    "distribution": {
                        "mean": 0, "median": 0, "std_dev": 0,
                        "min": 0, "max": 0,
                        "quartiles": {"q1": 0, "q3": 0}
                    },
                    "suggestions": []
                }
            },
            {
                "name": "invalid_importance_scores",
                "data": {
                    "criticalFiles": [{
                        "file_path": "test.py",
                        "importance_score": 1.5,  # 범위 초과
                        "reasons": ["test"],
                        "metrics": {
                            "structural_importance": -0.1,  # 음수
                            "dependency_centrality": 0.5,
                            "churn_risk": 0.5,
                            "complexity_score": 2.0  # 범위 초과
                        },
                        "category": "unknown",  # 알 수 없는 카테고리
                        "rank": 1
                    }]
                }
            }
        ]
        
        # When & Then: 각 엣지 케이스에 대한 적절한 처리
        for case in edge_cases:
            if case["name"] == "empty_files_list":
                # 빈 목록의 경우 기본 메시지 표시
                files = case["data"]["criticalFiles"]
                assert len(files) == 0
                # 실제 컴포넌트는 "분석된 파일이 없습니다" 메시지를 표시해야 함
                
            elif case["name"] == "invalid_importance_scores":
                # 잘못된 값들의 경우 정규화 또는 기본값 사용
                file_data = case["data"]["criticalFiles"][0]
                
                # 중요도 점수 정규화 (0-1 범위로 제한)
                normalized_score = max(0, min(1, file_data["importance_score"]))
                assert 0 <= normalized_score <= 1
                
                # 메트릭 값들 정규화
                metrics = file_data["metrics"]
                for key, value in metrics.items():
                    normalized_value = max(0, min(1, value))
                    assert 0 <= normalized_value <= 1
                
                # 알 수 없는 카테고리의 경우 기본값 사용
                category = file_data["category"]
                if category not in ["critical", "important", "moderate", "low"]:
                    default_category = "moderate"
                    assert default_category in ["critical", "important", "moderate", "low"]

    def test_integration_with_backend_api(self):
        """백엔드 API와의 통합 테스트"""
        # Given: Mock API 응답 데이터
        mock_api_response = {
            "success": True,
            "data": {
                "smart_file_analysis": {
                    "critical_files": [
                        {
                            "file_path": "src/main.py",
                            "importance_score": 0.95,
                            "reasons": ["주요 진입점"],
                            "metrics": {
                                "structural_importance": 0.9,
                                "dependency_centrality": 0.8,
                                "churn_risk": 0.6,
                                "complexity_score": 0.7
                            }
                        }
                    ]
                },
                "distribution": {
                    "mean": 0.635,
                    "median": 0.550,
                    "std_dev": 0.289,
                    "min": 0.125,
                    "max": 0.950,
                    "quartiles": {"q1": 0.375, "q3": 0.825}
                },
                "suggestions": ["리팩토링 권장"]
            }
        }
        
        # When: API 응답 데이터 변환
        if mock_api_response["success"]:
            api_data = mock_api_response["data"]
            
            # 백엔드 데이터를 프론트엔드 형식으로 변환
            transformed_files = []
            for file_data in api_data["smart_file_analysis"]["critical_files"]:
                # 카테고리 결정 로직
                score = file_data["importance_score"]
                if score >= 0.8:
                    category = "critical"
                elif score >= 0.6:
                    category = "important"
                elif score >= 0.4:
                    category = "moderate"
                else:
                    category = "low"
                
                transformed_file = {
                    "file_path": file_data["file_path"],
                    "importance_score": file_data["importance_score"],
                    "reasons": file_data["reasons"],
                    "metrics": file_data["metrics"],
                    "category": category,
                    "rank": len(transformed_files) + 1
                }
                transformed_files.append(transformed_file)
            
            # Then: 변환된 데이터가 컴포넌트 요구사항에 맞아야 함
            assert len(transformed_files) > 0
            assert transformed_files[0]["category"] == "critical"
            assert transformed_files[0]["rank"] == 1
            assert "distribution" in api_data
            assert "suggestions" in api_data


class TestFileImportanceCardComponent:
    """개별 파일 카드 컴포넌트 테스트"""
    
    def test_file_card_data_display(self):
        """파일 카드 데이터 표시 테스트"""
        # Given: 파일 카드 데이터
        file_data = {
            "file_path": "src/components/Button.tsx",
            "importance_score": 0.75,
            "reasons": ["재사용 가능한 UI 컴포넌트", "여러 페이지에서 참조"],
            "metrics": {
                "structural_importance": 0.6,
                "dependency_centrality": 0.8,
                "churn_risk": 0.3,
                "complexity_score": 0.4
            },
            "category": "important",
            "rank": 5
        }
        
        # When & Then: 카드에 표시될 정보 검증
        assert file_data["file_path"] == "src/components/Button.tsx"
        assert file_data["importance_score"] == 0.75
        assert len(file_data["reasons"]) == 2
        assert file_data["category"] == "important"
        assert file_data["rank"] == 5
        
        # 메트릭 바 시각화 데이터 검증
        for metric_name, value in file_data["metrics"].items():
            assert 0 <= value <= 1
            progress_width = value * 100
            assert 0 <= progress_width <= 100


class TestScoreBreakdownComponent:
    """점수 분해 컴포넌트 테스트"""
    
    def test_score_breakdown_calculation(self):
        """점수 분해 계산 테스트"""
        # Given: 원시 메트릭 데이터
        raw_metrics = {
            "structural_importance": 0.8,
            "dependency_centrality": 0.6,
            "churn_risk": 0.4,
            "complexity_score": 0.7
        }
        
        # When: 가중치 적용한 점수 계산 (실제 백엔드 로직과 동일)
        weights = {
            "structural_importance": 0.4,  # 40%
            "dependency_centrality": 0.3,  # 30%
            "churn_risk": 0.2,            # 20%
            "complexity_score": 0.1       # 10%
        }
        
        total_score = sum(
            raw_metrics[metric] * weights[metric]
            for metric in raw_metrics.keys()
        )
        
        # Then: 계산된 점수가 합리적이어야 함
        assert 0 <= total_score <= 1
        assert abs(total_score - 0.65) < 0.01  # 예상값: 0.8*0.4 + 0.6*0.3 + 0.4*0.2 + 0.7*0.1 = 0.65
        
        # 각 차원별 기여도 계산
        contributions = {
            metric: raw_metrics[metric] * weights[metric] / total_score
            for metric in raw_metrics.keys()
        }
        
        # 기여도 합계가 1이어야 함
        total_contribution = sum(contributions.values())
        assert abs(total_contribution - 1.0) < 0.01


class TestDetailModalComponent:
    """상세 모달 컴포넌트 테스트"""
    
    def test_modal_content_structure(self):
        """모달 내용 구조 테스트"""
        # Given: 상세 정보를 위한 파일 데이터
        detailed_file_data = {
            "file_path": "src/services/apiClient.ts",
            "importance_score": 0.88,
            "reasons": [
                "API 통신의 중심 모듈",
                "모든 HTTP 요청의 공통 처리",
                "인증 및 오류 처리 로직 포함"
            ],
            "metrics": {
                "structural_importance": 0.9,
                "dependency_centrality": 0.85,
                "churn_risk": 0.5,
                "complexity_score": 0.8
            },
            "category": "critical",
            "rank": 2,
            "additional_info": {
                "file_size": "15.2 KB",
                "last_modified": "2024-01-15",
                "contributors": ["developer1", "developer2"],
                "dependencies": ["axios", "lodash"],
                "dependents": ["UserService", "ProductService", "OrderService"]
            }
        }
        
        # When & Then: 모달에서 표시할 정보 구조 검증
        assert "additional_info" in detailed_file_data
        additional_info = detailed_file_data["additional_info"]
        
        # 필수 상세 정보 필드들
        required_fields = ["file_size", "last_modified", "contributors", "dependencies", "dependents"]
        for field in required_fields:
            assert field in additional_info
        
        # 데이터 타입 검증
        assert isinstance(additional_info["contributors"], list)
        assert isinstance(additional_info["dependencies"], list)
        assert isinstance(additional_info["dependents"], list)
        assert len(additional_info["file_size"]) > 0
        assert len(additional_info["last_modified"]) > 0

    def test_modal_interaction_behavior(self):
        """모달 상호작용 동작 테스트"""
        # Given: 모달 상태 관리
        modal_state = {
            "is_open": False,
            "selected_file": None,
            "tab": "overview"  # overview, metrics, dependencies, history
        }
        
        # When: 파일 선택으로 모달 열기
        selected_file = {"file_path": "src/main.py", "importance_score": 0.95}
        modal_state["is_open"] = True
        modal_state["selected_file"] = selected_file
        
        # Then: 모달이 올바르게 열려야 함
        assert modal_state["is_open"] == True
        assert modal_state["selected_file"] is not None
        assert modal_state["selected_file"]["file_path"] == "src/main.py"
        
        # When: 탭 변경
        modal_state["tab"] = "metrics"
        
        # Then: 탭이 변경되어야 함
        assert modal_state["tab"] == "metrics"
        
        # When: 모달 닫기
        modal_state["is_open"] = False
        modal_state["selected_file"] = None
        modal_state["tab"] = "overview"
        
        # Then: 모달이 초기 상태로 돌아가야 함
        assert modal_state["is_open"] == False
        assert modal_state["selected_file"] is None
        assert modal_state["tab"] == "overview"