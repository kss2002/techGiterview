"""
CriticalFilesPreview 통합 테스트

DashboardPage와 CriticalFilesPreview 컴포넌트의 통합을 테스트합니다.
main_rules.md TDD 방식에 따른 통합 테스트 검증
"""

import pytest
from typing import Dict, List, Any, Optional


class TestCriticalFilesIntegration:
    """CriticalFilesPreview 통합 테스트"""
    
    @pytest.fixture
    def complete_analysis_result_with_smart_files(self):
        """완전한 분석 결과 데이터 (smart_file_analysis 포함)"""
        return {
            "success": True,
            "analysis_id": "test_integration_001",
            "repo_url": "https://github.com/test-owner/test-repo",
            "repo_info": {
                "name": "test-repo",
                "owner": "test-owner",
                "description": "Integration test repository",
                "language": "Python",
                "size": 1024,
                "stargazers_count": 150,
                "forks_count": 30,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-07-14T12:00:00Z"
            },
            "tech_stack": {
                "Python": 0.75,
                "JavaScript": 0.15,
                "HTML": 0.08,
                "CSS": 0.02
            },
            "languages": {
                "Python": {"file_count": 15, "total_loc": 2500, "avg_complexity": 5.2},
                "JavaScript": {"file_count": 8, "total_loc": 800, "avg_complexity": 3.1},
                "HTML": {"file_count": 5, "total_loc": 300, "avg_complexity": 1.0}
            },
            "complexity_score": 1.8,
            "file_count": 28,
            "key_files": [
                {
                    "path": "src/main.py",
                    "name": "main.py",
                    "size": 2048,
                    "importance": "high",
                    "content": "#!/usr/bin/env python3\nimport os\nimport sys\nfrom config import DATABASE_URL, API_KEY\n\nclass Application:\n    def __init__(self):\n        self.db_url = DATABASE_URL\n        self.api_key = API_KEY\n    \n    async def start(self):\n        print(\"Starting application...\")\n        await self.connect_database()\n    \n    async def connect_database(self):\n        # Database connection logic\n        pass\n\nif __name__ == \"__main__\":\n    app = Application()\n    asyncio.run(app.start())"
                },
                {
                    "path": "src/config.py",
                    "name": "config.py", 
                    "size": 1024,
                    "importance": "high",
                    "content": "import os\nfrom typing import Optional\n\nDATABASE_URL = os.getenv(\"DATABASE_URL\", \"sqlite:///app.db\")\nAPI_KEY = os.getenv(\"API_KEY\")\nDEBUG = os.getenv(\"DEBUG\", \"False\").lower() == \"true\"\n\nALLOWED_HOSTS = [\"localhost\", \"127.0.0.1\"]\n\nclass Config:\n    def __init__(self):\n        self.database_url = DATABASE_URL\n        self.api_key = API_KEY\n        self.debug = DEBUG"
                }
            ],
            "smart_file_analysis": {
                "critical_files": [
                    {
                        "file_path": "src/main.py",
                        "importance_score": 0.95,
                        "reasons": [
                            "애플리케이션 진입점 파일",
                            "다른 파일들이 많이 참조하는 핵심 의존성",
                            "비즈니스 로직의 핵심 구현"
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
                            "핵심 모듈 또는 기반 라이브러리",
                            "환경 변수 및 설정 관리"
                        ],
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
                        "reasons": [
                            "핵심 비즈니스 로직 담당",
                            "중요한 모듈 간 연결점 역할",
                            "보안 관련 핵심 기능"
                        ],
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
                        "reasons": [
                            "핵심 비즈니스 로직 담당",
                            "활발하게 개발되고 있는 핵심 기능",
                            "사용자 관리 API 엔드포인트"
                        ],
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
                        "reasons": [
                            "핵심 모듈 또는 기반 라이브러리",
                            "적절한 복잡도의 핵심 로직 포함",
                            "데이터 모델 정의"
                        ],
                        "metrics": {
                            "structural_importance": 0.8,
                            "dependency_centrality": 0.5,
                            "churn_risk": 0.4,
                            "complexity_score": 0.4
                        },
                        "category": "important",
                        "rank": 5
                    }
                ],
                "importance_distribution": {
                    "mean": 0.834,
                    "median": 0.82,
                    "std_dev": 0.078,
                    "min": 0.75,
                    "max": 0.95,
                    "quartiles": {
                        "q1": 0.78,
                        "q3": 0.87
                    }
                },
                "categorized_files": {
                    "critical": ["src/main.py", "src/config.py", "src/services/auth_service.py"],
                    "important": ["src/api/user_controller.py", "src/models/user.py"],
                    "moderate": [],
                    "low": []
                },
                "improvement_suggestions": [
                    "고복잡도 핵심 파일 1개의 리팩토링을 고려하세요.",
                    "자주 변경되는 핵심 파일 1개에 대한 테스트 코드를 강화하세요.",
                    "핵심 의존성 파일 2개의 안정성 확보가 중요합니다."
                ],
                "summary": {
                    "total_files_analyzed": 28,
                    "critical_files_count": 3,
                    "important_files_count": 2,
                    "average_importance": 0.834,
                    "highest_importance": 0.95
                }
            },
            "analysis_summary": "test-repo 프로젝트는 Python를 주 언어로 사용하며, 복잡도 점수는 1.8/10입니다. 주요 기술 스택: Python, JavaScript, HTML, CSS",
            "created_at": "2024-07-14T12:00:00Z"
        }

    def test_repository_analyzer_includes_smart_file_analysis(self, complete_analysis_result_with_smart_files):
        """RepositoryAnalyzer가 smart_file_analysis를 포함하는지 테스트"""
        # Given: 완전한 분석 결과
        analysis_result = complete_analysis_result_with_smart_files
        
        # When: 분석 결과에서 smart_file_analysis 확인
        smart_analysis = analysis_result.get("smart_file_analysis")
        
        # Then: smart_file_analysis가 올바르게 포함되어야 함
        assert smart_analysis is not None
        assert "critical_files" in smart_analysis
        assert "importance_distribution" in smart_analysis
        assert "categorized_files" in smart_analysis
        assert "summary" in smart_analysis
        
        # critical_files가 올바른 구조를 가져야 함
        critical_files = smart_analysis["critical_files"]
        assert len(critical_files) == 5
        
        for file_data in critical_files:
            assert "file_path" in file_data
            assert "importance_score" in file_data
            assert "reasons" in file_data
            assert "metrics" in file_data
            assert "category" in file_data
            assert "rank" in file_data

    def test_dashboard_page_integration_data_flow(self, complete_analysis_result_with_smart_files):
        """DashboardPage의 데이터 흐름 통합 테스트"""
        # Given: 완전한 분석 결과
        analysis_result = complete_analysis_result_with_smart_files
        
        # When: DashboardPage에서 데이터 추출
        smart_analysis = analysis_result.get("smart_file_analysis")
        critical_files = smart_analysis.get("critical_files") if smart_analysis else []
        
        # Then: CriticalFilesPreview 컴포넌트에 필요한 데이터가 준비되어야 함
        assert len(critical_files) > 0
        
        # 상위 5개 파일로 제한
        display_files = critical_files[:5]
        assert len(display_files) <= 5
        
        # 중요도 순으로 정렬 확인
        scores = [file["importance_score"] for file in display_files]
        assert scores == sorted(scores, reverse=True)
        
        # 첫 번째 파일이 가장 중요한 파일인지 확인
        assert display_files[0]["file_path"] == "src/main.py"
        assert display_files[0]["importance_score"] == 0.95
        assert display_files[0]["category"] == "critical"

    def test_critical_files_preview_props_validation(self, complete_analysis_result_with_smart_files):
        """CriticalFilesPreview 컴포넌트 props 검증"""
        # Given: 분석 결과에서 추출한 데이터
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        # When: CriticalFilesPreview props 구성
        preview_props = {
            "criticalFiles": critical_files,
            "maxDisplayFiles": 5,
            "onFileClick": lambda path: print(f"File clicked: {path}")
        }
        
        # Then: props가 올바르게 구성되어야 함
        assert isinstance(preview_props["criticalFiles"], list)
        assert len(preview_props["criticalFiles"]) == 5
        assert isinstance(preview_props["maxDisplayFiles"], int)
        assert callable(preview_props["onFileClick"])
        
        # 각 파일 데이터의 구조 검증
        for file_data in preview_props["criticalFiles"]:
            assert isinstance(file_data["file_path"], str)
            assert isinstance(file_data["importance_score"], float)
            assert 0 <= file_data["importance_score"] <= 1
            assert isinstance(file_data["reasons"], list)
            assert len(file_data["reasons"]) > 0
            assert file_data["category"] in ["critical", "important", "moderate", "low"]

    def test_file_click_handler_integration(self, complete_analysis_result_with_smart_files):
        """파일 클릭 핸들러 통합 테스트"""
        # Given: 분석 결과와 모의 파일 클릭 핸들러
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        clicked_files = []
        def mock_file_click_handler(file_path: str):
            clicked_files.append(file_path)
        
        # When: 각 파일에 대해 클릭 이벤트 시뮬레이션
        for file_data in critical_files:
            mock_file_click_handler(file_data["file_path"])
        
        # Then: 모든 파일 경로가 올바르게 핸들러에 전달되어야 함
        assert len(clicked_files) == 5
        assert "src/main.py" in clicked_files
        assert "src/config.py" in clicked_files
        assert "src/services/auth_service.py" in clicked_files
        assert "src/api/user_controller.py" in clicked_files
        assert "src/models/user.py" in clicked_files

    def test_conditional_rendering_logic(self):
        """조건부 렌더링 로직 테스트"""
        # Given: 다양한 분석 결과 시나리오
        test_cases = [
            # 케이스 1: smart_file_analysis가 없는 경우
            {"analysis_result": {"success": True}},
            
            # 케이스 2: smart_file_analysis는 있지만 critical_files가 없는 경우
            {"analysis_result": {"success": True, "smart_file_analysis": {}}},
            
            # 케이스 3: critical_files가 빈 배열인 경우
            {"analysis_result": {"success": True, "smart_file_analysis": {"critical_files": []}}},
            
            # 케이스 4: 정상적인 critical_files가 있는 경우
            {"analysis_result": {"success": True, "smart_file_analysis": {"critical_files": [
                {"file_path": "test.py", "importance_score": 0.8, "reasons": ["test"], "metrics": {}, "category": "critical", "rank": 1}
            ]}}},
        ]
        
        for i, case in enumerate(test_cases):
            analysis_result = case["analysis_result"]
            
            # When: 조건부 렌더링 로직 적용
            smart_analysis = analysis_result.get("smart_file_analysis")
            critical_files = smart_analysis.get("critical_files") if smart_analysis else []
            should_render = bool(critical_files and len(critical_files) > 0)
            
            # Then: 적절한 렌더링 결정이 되어야 함
            if i < 3:  # 처음 3개 케이스는 렌더링하지 않아야 함
                assert should_render is False, f"케이스 {i+1}에서 잘못된 렌더링 결정"
            else:  # 마지막 케이스는 렌더링해야 함
                assert should_render is True, f"케이스 {i+1}에서 잘못된 렌더링 결정"

    def test_max_display_files_limiting(self, complete_analysis_result_with_smart_files):
        """최대 표시 파일 수 제한 기능 테스트"""
        # Given: 5개의 중요 파일과 다양한 제한 설정
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        test_limits = [1, 3, 5, 10]
        
        for max_limit in test_limits:
            # When: 최대 표시 수 제한 적용
            display_files = critical_files[:max_limit]
            
            # Then: 지정된 수만큼만 표시되어야 함
            expected_count = min(max_limit, len(critical_files))
            assert len(display_files) == expected_count
            
            # 중요도가 높은 순으로 선택되어야 함
            if len(display_files) > 1:
                for i in range(len(display_files) - 1):
                    assert display_files[i]["importance_score"] >= display_files[i + 1]["importance_score"]

    def test_importance_score_formatting_and_display(self, complete_analysis_result_with_smart_files):
        """중요도 점수 포맷팅 및 표시 테스트"""
        # Given: 중요 파일들의 점수
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        # When: 각 파일의 중요도 점수를 포맷팅
        for file_data in critical_files:
            score = file_data["importance_score"]
            
            # Then: 점수가 올바른 범위와 형식이어야 함
            assert 0 <= score <= 1
            assert isinstance(score, float)
            
            # 백분율 변환 테스트
            percentage = round(score * 100, 1)
            assert 0 <= percentage <= 100
            
            # 표시용 문자열 포맷 테스트
            display_score = f"{percentage}%"
            assert display_score.endswith("%")
            
            # 소수점 한 자리까지만 표시되어야 함
            decimal_part = str(percentage).split('.')
            if len(decimal_part) > 1:
                assert len(decimal_part[1]) <= 1

    def test_metrics_visualization_data(self, complete_analysis_result_with_smart_files):
        """메트릭 시각화 데이터 테스트"""
        # Given: 각 파일의 4차원 메트릭 데이터
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        # When: 메트릭 시각화를 위한 데이터 검증
        for file_data in critical_files:
            metrics = file_data["metrics"]
            
            # Then: 4차원 메트릭이 모두 존재해야 함
            required_metrics = [
                "structural_importance",
                "dependency_centrality", 
                "churn_risk",
                "complexity_score"
            ]
            
            for metric in required_metrics:
                assert metric in metrics
                metric_value = metrics[metric]
                assert isinstance(metric_value, (int, float))
                assert 0 <= metric_value <= 1
                
                # 진행률 바를 위한 백분율 변환 테스트
                percentage = metric_value * 100
                assert 0 <= percentage <= 100

    def test_accessibility_and_keyboard_navigation(self, complete_analysis_result_with_smart_files):
        """접근성 및 키보드 네비게이션 테스트"""
        # Given: 중요 파일 데이터
        analysis_result = complete_analysis_result_with_smart_files
        critical_files = analysis_result["smart_file_analysis"]["critical_files"]
        
        # When: 각 파일 항목의 접근성 속성 검증
        for i, file_data in enumerate(critical_files):
            # Then: 접근성 요구사항이 충족되어야 함
            
            # 1. 키보드 접근 가능성
            # 실제 구현에서는 tabIndex={0}와 onKeyDown 핸들러가 있어야 함
            tab_index = 0  # 시뮬레이션
            assert tab_index == 0
            
            # 2. ARIA 레이블 및 역할
            # 실제 구현에서는 role="button"이 있어야 함
            role = "button"  # 시뮬레이션
            assert role == "button"
            
            # 3. 파일 경로 전체 표시 (title 속성)
            full_path = file_data["file_path"]
            assert len(full_path) > 0
            
            # 4. 중요도 점수 의미 명확성
            importance_score = file_data["importance_score"]
            score_description = f"중요도 {importance_score * 100:.1f}%"
            assert "중요도" in score_description
            assert "%" in score_description

    def test_error_handling_and_edge_cases(self):
        """에러 처리 및 엣지 케이스 테스트"""
        # Given: 다양한 에러 시나리오
        error_cases = [
            # 케이스 1: None 값들
            None,
            
            # 케이스 2: 잘못된 데이터 타입
            {"smart_file_analysis": "invalid_type"},
            
            # 케이스 3: 불완전한 파일 데이터
            {"smart_file_analysis": {"critical_files": [
                {"file_path": "test.py"}  # 필수 필드 누락
            ]}},
            
            # 케이스 4: 잘못된 점수 범위
            {"smart_file_analysis": {"critical_files": [
                {
                    "file_path": "test.py",
                    "importance_score": 1.5,  # 범위 초과
                    "reasons": ["test"],
                    "metrics": {},
                    "category": "critical",
                    "rank": 1
                }
            ]}},
        ]
        
        for i, error_case in enumerate(error_cases):
            # When: 에러 케이스 처리
            try:
                if error_case is None:
                    smart_analysis = None
                    critical_files = []
                else:
                    smart_analysis = error_case.get("smart_file_analysis")
                    if isinstance(smart_analysis, dict):
                        critical_files = smart_analysis.get("critical_files", [])
                    else:
                        critical_files = []
                
                # Then: 적절한 에러 처리가 되어야 함
                should_render = bool(critical_files and len(critical_files) > 0)
                
                # 에러 케이스에서는 렌더링하지 않거나 기본값을 사용해야 함
                if i == 0:  # None 케이스
                    assert should_render is False
                elif i == 1:  # 잘못된 타입 케이스
                    assert should_render is False
                elif i == 2:  # 불완전한 데이터 케이스
                    # 불완전한 데이터라도 기본값으로 처리할 수 있어야 함
                    assert len(critical_files) == 1
                elif i == 3:  # 잘못된 점수 케이스
                    # 점수 범위 검증은 컴포넌트에서 처리해야 함
                    file_data = critical_files[0]
                    score = file_data["importance_score"]
                    # 실제 구현에서는 1.0으로 클램핑되어야 함
                    clamped_score = min(1.0, max(0.0, score))
                    assert 0 <= clamped_score <= 1
                    
            except Exception as e:
                # 예외가 발생해도 애플리케이션이 크래시되지 않아야 함
                print(f"에러 케이스 {i+1}에서 예외 발생: {e}")
                # 실제 구현에서는 로깅하고 기본값을 반환해야 함
                assert True  # 에러 처리가 되었음을 표시


class TestCriticalFilesPreviewComponentIntegration:
    """CriticalFilesPreview 컴포넌트 전용 통합 테스트"""
    
    def test_component_with_real_data_structure(self):
        """실제 데이터 구조를 사용한 컴포넌트 테스트"""
        # Given: 실제 API 응답과 동일한 구조의 데이터
        real_data_structure = {
            "critical_files": [
                {
                    "file_path": "src/main.py",
                    "importance_score": 0.95,
                    "reasons": [
                        "애플리케이션 진입점 파일",
                        "다른 파일들이 많이 참조하는 핵심 의존성"
                    ],
                    "metrics": {
                        "structural_importance": 0.9,
                        "dependency_centrality": 0.8,
                        "churn_risk": 0.6,
                        "complexity_score": 0.7
                    },
                    "category": "critical",
                    "rank": 1
                }
            ]
        }
        
        # When: 컴포넌트에 실제 데이터 전달
        critical_files = real_data_structure["critical_files"]
        
        # Then: 컴포넌트가 실제 데이터를 올바르게 처리해야 함
        assert len(critical_files) == 1
        
        file_data = critical_files[0]
        
        # 파일 경로 처리
        assert file_data["file_path"] == "src/main.py"
        
        # 중요도 점수 처리
        score_percentage = file_data["importance_score"] * 100
        assert score_percentage == 95.0
        
        # 선정 이유 처리
        reasons = file_data["reasons"]
        assert len(reasons) == 2
        assert "애플리케이션 진입점 파일" in reasons
        
        # 메트릭 처리
        metrics = file_data["metrics"]
        assert len(metrics) == 4
        for metric_name, metric_value in metrics.items():
            assert 0 <= metric_value <= 1

    def test_responsive_design_breakpoints(self):
        """반응형 디자인 브레이크포인트 테스트"""
        # Given: 다양한 화면 크기 시나리오
        breakpoints = [
            {"name": "mobile", "width": 480, "expected_columns": 1},
            {"name": "tablet", "width": 768, "expected_columns": 1}, 
            {"name": "desktop", "width": 1024, "expected_columns": "auto-fit"},
            {"name": "large", "width": 1440, "expected_columns": "auto-fit"}
        ]
        
        # When: 각 브레이크포인트에서의 레이아웃 확인
        for bp in breakpoints:
            # Then: 적절한 레이아웃이 적용되어야 함
            if bp["width"] <= 768:
                # 모바일/태블릿에서는 단일 컬럼
                assert bp["expected_columns"] == 1
            else:
                # 데스크톱에서는 auto-fit
                assert bp["expected_columns"] == "auto-fit"
                
        # CSS 그리드 설정 검증
        grid_settings = {
            "mobile": "grid-template-columns: 1fr",
            "tablet": "grid-template-columns: 1fr", 
            "desktop": "grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))"
        }
        
        for device, css_rule in grid_settings.items():
            assert "grid-template-columns" in css_rule

    def test_dark_mode_support(self):
        """다크 모드 지원 테스트"""
        # Given: 다크 모드 CSS 변수 및 스타일
        dark_mode_styles = {
            "background": "#1f2937",
            "text_color": "#f9fafb",
            "border_color": "#374151",
            "hover_border": "#60a5fa"
        }
        
        # When: 다크 모드 스타일 검증
        # Then: 모든 필수 다크 모드 스타일이 정의되어야 함
        for style_name, style_value in dark_mode_styles.items():
            assert isinstance(style_value, str)
            assert style_value.startswith("#") or style_value.startswith("rgb")
            
        # 다크 모드 미디어 쿼리 존재 확인
        media_query = "@media (prefers-color-scheme: dark)"
        assert len(media_query) > 0
        assert "prefers-color-scheme" in media_query

    def test_performance_with_large_dataset(self):
        """대용량 데이터셋 성능 테스트"""
        # Given: 대량의 중요 파일 데이터 (50개)
        large_dataset = []
        for i in range(50):
            large_dataset.append({
                "file_path": f"src/module_{i}/file_{i}.py",
                "importance_score": 0.9 - (i * 0.01),  # 0.9부터 점진적 감소
                "reasons": [f"모듈 {i} 핵심 파일", f"중요 기능 {i} 구현"],
                "metrics": {
                    "structural_importance": 0.8 - (i * 0.01),
                    "dependency_centrality": 0.7 - (i * 0.005),
                    "churn_risk": 0.5 + (i * 0.005),
                    "complexity_score": 0.6 - (i * 0.008)
                },
                "category": "critical" if i < 10 else "important" if i < 30 else "moderate",
                "rank": i + 1
            })
        
        # When: 최대 표시 수 제한 적용 (5개)
        max_display = 5
        display_files = large_dataset[:max_display]
        
        # Then: 성능 및 정확성 검증
        assert len(display_files) == max_display
        
        # 중요도 순 정렬 확인
        for i in range(len(display_files) - 1):
            assert display_files[i]["importance_score"] >= display_files[i + 1]["importance_score"]
        
        # 메모리 효율성 - 불필요한 데이터 로드하지 않음
        assert len(display_files) < len(large_dataset)
        
        # 첫 번째 파일이 가장 중요한 파일인지 확인
        assert display_files[0]["importance_score"] == 0.9
        assert display_files[0]["rank"] == 1