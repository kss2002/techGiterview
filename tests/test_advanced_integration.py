"""
Advanced File Analysis Integration Tests

고도화된 파일 분석 시스템의 통합 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.advanced_file_analyzer import AdvancedFileAnalyzer, FileMetrics
from app.services.github_client import GitHubClient
from app.agents.repository_analyzer import RepositoryAnalyzer
from app.agents.question_generator import QuestionGenerator
from app.api.analysis import analyze_repository_advanced


class TestAdvancedFileAnalyzer:
    """고도화된 파일 분석기 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        return AdvancedFileAnalyzer()
    
    @pytest.fixture
    def mock_github_client(self):
        mock_client = AsyncMock(spec=GitHubClient)
        
        # 기본 저장소 정보
        mock_client.get_repository_info.return_value = {
            "name": "test-repo",
            "description": "Test repository",
            "language": "Python",
            "size": 1024,
            "stargazers_count": 10,
            "forks_count": 5,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "default_branch": "main"
        }
        
        # 파일 트리 목록
        mock_client.get_file_tree.return_value = [
            {
                "path": "main.py",
                "name": "main.py",
                "type": "file",
                "size": 1000
            },
            {
                "path": "utils/helper.py",
                "name": "helper.py", 
                "type": "file",
                "size": 500
            },
            {
                "path": "requirements.txt",
                "name": "requirements.txt",
                "type": "file",
                "size": 200
            }
        ]
        
        # 파일 내용
        file_contents = {
            "main.py": """
import asyncio
from utils.helper import process_data

class DataProcessor:
    def __init__(self):
        self.data = []
    
    async def process(self, input_data):
        result = await process_data(input_data)
        return result

if __name__ == "__main__":
    processor = DataProcessor()
    asyncio.run(processor.process("test"))
""",
            "utils/helper.py": """
async def process_data(data):
    if not data:
        raise ValueError("Data is required")
    
    processed = data.upper()
    return processed

def validate_input(data):
    return isinstance(data, str) and len(data) > 0
""",
            "requirements.txt": """
asyncio>=3.4.3
pytest>=6.0.0
"""
        }
        
        async def mock_get_file_content(repo_url, path):
            return file_contents.get(path, None)
        
        mock_client.get_file_content.side_effect = mock_get_file_content
        
        # 비동기 컨텍스트 매니저 설정
        async def mock_aenter(self):
            return mock_client
        
        async def mock_aexit(self, exc_type, exc_val, exc_tb):
            return None
            
        mock_client.__aenter__ = mock_aenter
        mock_client.__aexit__ = mock_aexit
        
        # 커밋 히스토리
        mock_client.get_commit_history.return_value = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "Developer", "date": "2024-01-01T00:00:00Z"},
                    "message": "Initial commit"
                },
                "files": [
                    {
                        "filename": "main.py",
                        "status": "added",
                        "additions": 20,
                        "deletions": 0,
                        "changes": 20
                    }
                ]
            }
        ]
        
        return mock_client
    
    @pytest.mark.asyncio
    async def test_analyze_repository_advanced_success(self, analyzer, mock_github_client):
        """고도화된 저장소 분석 성공 테스트"""
        
        # GitHub 클라이언트 모킹
        with patch.object(analyzer, 'github_client', mock_github_client):
            result = await analyzer.analyze_repository_advanced("https://github.com/test/repo")
        
        # 기본 검증
        assert result["success"] is True
        assert "repo_info" in result
        assert "file_metrics" in result
        assert "important_files" in result
        assert "dashboard_data" in result
        
        # 중요 파일 검증
        important_files = result["important_files"]
        assert len(important_files) > 0
        
        # 첫 번째 중요 파일 검증
        first_file = important_files[0]
        assert "path" in first_file
        assert "content" in first_file
        assert "importance_score" in first_file
        assert "complexity" in first_file
        
    @pytest.mark.asyncio
    async def test_file_metrics_calculation(self, analyzer):
        """파일 메트릭 계산 테스트"""
        
        metrics = FileMetrics(path="test.py")
        metrics.cyclomatic_complexity = 10.0
        metrics.recent_commits = 5
        metrics.fan_in = 3
        metrics.file_type = "main"
        
        # 중요도 점수 계산
        importance_score = analyzer._calculate_importance_score(metrics)
        
        assert importance_score > 0
        assert isinstance(importance_score, float)
        
        # 품질 위험도 계산
        risk_score = analyzer._calculate_quality_risk_score(metrics)
        
        assert risk_score >= 0
        assert risk_score <= 10
    
    @pytest.mark.asyncio
    async def test_dependency_graph_building(self, analyzer, mock_github_client):
        """의존성 그래프 구성 테스트"""
        
        file_tree = [
            {"path": "main.py", "type": "file"},
            {"path": "utils/helper.py", "type": "file"}
        ]
        
        # Set the _current_client attribute and mock GitHub client
        analyzer._current_client = mock_github_client
        dependency_graph = await analyzer._build_dependency_graph("https://github.com/test/repo", file_tree)
        
        assert dependency_graph.graph.number_of_nodes() >= 0
        assert hasattr(dependency_graph, 'import_relationships')
        assert hasattr(dependency_graph, 'module_clusters')
    
    def test_language_detection(self, analyzer):
        """언어 감지 테스트"""
        
        test_cases = [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("component.tsx", "typescript"),
            ("Main.java", "java"),
            ("main.go", "go"),
            ("lib.rs", "rust"),
            ("unknown.xyz", "unknown")
        ]
        
        for file_path, expected_language in test_cases:
            detected = analyzer._detect_language(file_path)
            assert detected == expected_language
    
    def test_file_type_categorization(self, analyzer):
        """파일 타입 분류 테스트"""
        
        test_cases = [
            ("main.py", "main"),
            ("app.py", "main"),
            ("controllers/user_controller.py", "controller"),
            ("services/data_service.py", "service"),
            ("models/user.py", "model"),
            ("utils/helper.py", "utility"),
            ("config/settings.py", "configuration")
        ]
        
        for file_path, expected_type in test_cases:
            file_type = analyzer._categorize_file_type(file_path)
            assert file_type == expected_type


class TestRepositoryAnalyzerIntegration:
    """Repository Analyzer 통합 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        return RepositoryAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_with_advanced_enabled(self, analyzer):
        """고도화된 분석 활성화 테스트"""
        
        # GitHub 클라이언트 모킹 (AsyncMock으로 비동기 컨텍스트 매니저 지원)
        mock_github_client = AsyncMock()
        
        # Async 메서드들을 적절히 모킹
        async def mock_get_repo_info(repo_url):
            return {"name": "test-repo", "description": "Test repository", "language": "Python"}
            
        async def mock_get_languages(repo_url):
            return {"Python": 1000}
            
        async def mock_get_file_tree(repo_url):
            return []
        
        mock_github_client.get_repository_info.side_effect = mock_get_repo_info
        mock_github_client.get_languages.side_effect = mock_get_languages
        mock_github_client.get_file_tree.side_effect = mock_get_file_tree
        
        # Advanced analyzer 모킹
        mock_advanced_result = {
            "success": True,
            "important_files": [
                {
                    "path": "main.py",
                    "content": "print('Hello World')",
                    "importance_score": 85.5,
                    "complexity": 5.2,
                    "file_type": "main"
                }
            ],
            "dashboard_data": {}
        }
        
        with patch.object(analyzer.advanced_analyzer, 'analyze_repository_advanced', 
                         return_value=mock_advanced_result) as mock_advanced:
            with patch.object(analyzer, 'github_client', mock_github_client):
                # 기본 분석 메서드들 모킹
                with patch.object(analyzer, '_identify_tech_stack', return_value={}):
                    with patch.object(analyzer, '_calculate_complexity_score', return_value=5.0):
                        
                        result = await analyzer.analyze_repository(
                            "https://github.com/test/repo", 
                            use_advanced=True
                        )
        
        # 결과 검증
        print(f"Result: {result}")  # 디버깅용
        
        # 고도화된 분석이 호출되었는지 확인
        mock_advanced.assert_called_once()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_with_advanced_disabled(self, analyzer):
        """고도화된 분석 비활성화 테스트"""
        
        # GitHub 클라이언트 모킹
        mock_github_client = AsyncMock()
        
        # Async 메서드들을 적절히 모킹
        async def mock_get_repo_info(repo_url):
            return {"name": "test-repo", "description": "Test repository", "language": "Python"}
            
        async def mock_get_languages(repo_url):
            return {"Python": 1000}
            
        async def mock_get_file_tree(repo_url):
            return []
        
        mock_github_client.get_repository_info.side_effect = mock_get_repo_info
        mock_github_client.get_languages.side_effect = mock_get_languages
        mock_github_client.get_file_tree.side_effect = mock_get_file_tree
        
        with patch.object(analyzer, '_select_important_files', return_value=[]) as mock_select:
            with patch.object(analyzer, 'github_client', mock_github_client):
                with patch.object(analyzer, '_identify_tech_stack', return_value={}):
                    with patch.object(analyzer, '_calculate_complexity_score', return_value=5.0):
                        
                        result = await analyzer.analyze_repository(
                            "https://github.com/test/repo", 
                            use_advanced=False
                        )
        
        # 결과 검증
        print(f"Result: {result}")  # 디버깅용
        
        # 기본 파일 선택이 호출되었는지 확인
        mock_select.assert_called_once()
        assert result["has_advanced_analysis"] is False


class TestQuestionGeneratorIntegration:
    """Question Generator 통합 테스트"""
    
    @pytest.fixture
    def generator(self):
        return QuestionGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_questions_with_advanced_files(self, generator):
        """고도화된 파일 분석 결과로 질문 생성 테스트"""
        
        analysis_data = {
            "has_advanced_analysis": True,
            "advanced_analysis": {
                "important_files": [
                    {
                        "path": "main.py",
                        "content": """
def main():
    print("Hello World")
    return 0

if __name__ == "__main__":
    main()
""",
                        "importance_score": 90.0,
                        "complexity": 2.5,
                        "file_type": "main",
                        "language": "python",
                        "metrics_summary": {
                            "lines_of_code": 6,
                            "fan_in": 0,
                            "fan_out": 1
                        }
                    }
                ]
            },
            "tech_stack": {"python": 0.8},
            "complexity_score": 3.0
        }
        
        # AI 서비스 모킹
        with patch('app.core.ai_service.ai_service.generate_analysis') as mock_ai:
            mock_ai.return_value = {
                "content": "이 main.py 파일의 main() 함수에서 사용된 print 문의 역할과 반환값의 의미를 설명해주세요."
            }
            
            result = await generator.generate_questions(
                repo_url="https://github.com/test/repo",
                difficulty_level="medium",
                question_count=3,
                analysis_data=analysis_data,
                use_advanced_files=True
            )
        
        # 결과 검증
        assert result["success"] is True
        assert len(result["questions"]) > 0
        
        # 첫 번째 질문 검증
        first_question = result["questions"][0]
        assert "id" in first_question
        assert "question" in first_question
        assert "source_file" in first_question
        assert first_question["source_file"]["path"] == "main.py"
    
    @pytest.mark.asyncio
    async def test_process_advanced_file(self, generator):
        """고도화된 파일 처리 테스트"""
        
        from app.agents.question_generator import QuestionState
        
        state = QuestionState(repo_url="https://github.com/test/repo")
        
        file_info = {
            "path": "service.py",
            "content": "class UserService:\n    def get_user(self, id):\n        return User.find(id)",
            "importance_score": 75.0,
            "complexity": 3.2,
            "file_type": "service",
            "language": "python",
            "metrics_summary": {
                "fan_in": 2,
                "recent_commits": 3
            }
        }
        
        generator._process_advanced_file(state, file_info)
        
        assert len(state.code_snippets) == 1
        snippet = state.code_snippets[0]
        assert snippet["path"] == "service.py"
        assert snippet["has_real_content"] is True
        assert snippet["importance_score"] == 75.0
    
    def test_calculate_advanced_priority(self, generator):
        """고도화된 우선순위 계산 테스트"""
        
        priority = generator._calculate_advanced_priority(
            importance_score=80.0,
            complexity=5.5,
            file_type="main",
            metrics={"fan_in": 4, "recent_commits": 6}
        )
        
        assert priority > 80.0  # 기본 점수보다 높아야 함
        assert isinstance(priority, float)
    
    def test_validate_file_content(self, generator):
        """파일 내용 유효성 검사 테스트"""
        
        valid_cases = [
            "def hello():\n    print('Hello World')",
            "class MyClass:\n    pass",
            "function test() { return 'test'; }"
        ]
        
        invalid_cases = [
            "",
            "# File content not available",
            "null",
            "   ",
            "short"  # 20자 미만
        ]
        
        for content in valid_cases:
            assert generator._validate_file_content(content) is True
        
        for content in invalid_cases:
            assert generator._validate_file_content(content) is False


class TestAPIIntegration:
    """API 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_analyze_repository_advanced_endpoint(self):
        """고도화된 분석 API 엔드포인트 테스트"""
        
        from app.api.analysis import AdvancedAnalysisRequest
        
        request = AdvancedAnalysisRequest(
            repository_url="https://github.com/test/repo",
            max_files=15,
            include_dashboard=True
        )
        
        # AdvancedFileAnalyzer 모킹
        mock_result = {
            "success": True,
            "important_files": [
                {
                    "path": "main.py",
                    "content": "print('test')",
                    "importance_score": 85.0
                }
            ],
            "dashboard_data": {"test": "data"}
        }
        
        with patch('app.api.analysis.AdvancedFileAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze_repository_advanced.return_value = mock_result
            mock_analyzer_class.return_value = mock_analyzer
            
            # 실제 함수 호출 (함수 import 필요)
            from app.api.analysis import analyze_repository_advanced
            
            result = await analyze_repository_advanced(request)
        
        # 결과 검증
        assert result["success"] is True
        assert "important_files" in result
        assert "dashboard_data" in result
        assert len(result["important_files"]) > 0


class TestEndToEndIntegration:
    """전체 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_advanced_analysis(self):
        """전체 파이프라인 (고도화된 분석 -> 질문 생성) 테스트"""
        
        # 1. Repository Analyzer로 고도화된 분석 수행
        analyzer = RepositoryAnalyzer()
        
        mock_advanced_result = {
            "success": True,
            "important_files": [
                {
                    "path": "app.py",
                    "content": """
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

if __name__ == '__main__':
    app.run(debug=True)
""",
                    "importance_score": 92.5,
                    "complexity": 4.8,
                    "file_type": "main",
                    "language": "python"
                }
            ],
            "dashboard_data": {}
        }
        
        with patch.object(analyzer.advanced_analyzer, 'analyze_repository_advanced', 
                         return_value=mock_advanced_result):
            with patch.object(analyzer.github_client, '__aenter__', return_value=AsyncMock()):
                with patch.object(analyzer.github_client, '__aexit__', return_value=None):
                    with patch.object(analyzer, '_identify_tech_stack', return_value={"python": 0.7, "flask": 0.5}):
                        with patch.object(analyzer, '_calculate_complexity_score', return_value=4.5):
                            
                            analysis_result = await analyzer.analyze_repository(
                                "https://github.com/test/flask-app",
                                use_advanced=True
                            )
        
        # 2. Question Generator로 질문 생성
        generator = QuestionGenerator()
        
        with patch('app.core.ai_service.ai_service.generate_analysis') as mock_ai:
            mock_ai.return_value = {
                "content": "이 Flask 애플리케이션의 app.py에서 정의된 get_users() 함수의 라우팅 방식과 데이터 직렬화 과정을 분석하고, RESTful API 설계 관점에서 개선점을 제시해주세요."
            }
            
            questions_result = await generator.generate_questions(
                repo_url="https://github.com/test/flask-app",
                difficulty_level="medium",
                question_count=5,
                question_types=["code_analysis", "tech_stack"],
                analysis_data=analysis_result,
                use_advanced_files=True
            )
        
        # 최종 검증
        assert analysis_result["success"] is True
        assert analysis_result["has_advanced_analysis"] is True
        
        assert questions_result["success"] is True
        assert len(questions_result["questions"]) > 0
        
        # 생성된 질문이 실제 파일 내용을 참조하는지 확인
        first_question = questions_result["questions"][0]
        assert "get_users" in first_question["question"] or "Flask" in first_question["question"]
        assert first_question["source_file"]["path"] == "app.py"
    
    @pytest.mark.asyncio
    async def test_error_handling_fallback(self):
        """오류 처리 및 폴백 테스트"""
        
        analyzer = RepositoryAnalyzer()
        
        # 고도화된 분석 실패 시나리오
        with patch.object(analyzer.advanced_analyzer, 'analyze_repository_advanced', 
                         return_value={"success": False, "error": "Analysis failed"}):
            with patch.object(analyzer, '_select_important_files', return_value=[]):
                with patch.object(analyzer.github_client, '__aenter__', return_value=AsyncMock()):
                    with patch.object(analyzer.github_client, '__aexit__', return_value=None):
                        with patch.object(analyzer, '_identify_tech_stack', return_value={}):
                            with patch.object(analyzer, '_calculate_complexity_score', return_value=3.0):
                                
                                result = await analyzer.analyze_repository(
                                    "https://github.com/test/repo",
                                    use_advanced=True
                                )
        
        # 폴백이 정상 작동하는지 확인
        assert result["success"] is True
        assert result["has_advanced_analysis"] is False


@pytest.mark.asyncio
async def test_performance_benchmarks():
    """성능 벤치마크 테스트"""
    
    import time
    
    analyzer = AdvancedFileAnalyzer()
    
    # 대용량 파일 트리 시뮬레이션
    large_file_tree = [
        {"path": f"file_{i}.py", "type": "file", "size": 1000}
        for i in range(100)
    ]
    
    # Create a mock GitHub client
    mock_client = AsyncMock()
    mock_client.get_repository_info.return_value = {"name": "large-repo"}
    mock_client.get_file_tree.return_value = large_file_tree
    mock_client.get_file_content.return_value = "def test(): pass"
    mock_client.get_commit_history.return_value = []
    
    # Patch the github_client attribute
    with patch.object(analyzer, 'github_client', mock_client):
        
        start_time = time.time()
        
        result = await analyzer.analyze_repository_advanced("https://github.com/test/large-repo")
        
        end_time = time.time()
        duration = end_time - start_time
    
    # 성능 기준: 5초 이내 완료
    assert duration < 5.0
    assert result["success"] is True


if __name__ == "__main__":
    # 개별 테스트 실행
    pytest.main([__file__, "-v"])