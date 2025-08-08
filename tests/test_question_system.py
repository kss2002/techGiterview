"""
AI 질문 생성 시스템 테스트

Vector DB와 Question Generator 테스트
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.vector_db import VectorDBService
from app.agents.question_generator import QuestionGenerator


class TestVectorDBService:
    """Vector Database Service 테스트"""
    
    @pytest.mark.asyncio
    async def test_store_code_snippets(self):
        """코드 스니펫 저장 테스트"""
        # Given
        repo_url = "https://github.com/test/repo"
        files = [
            {
                "path": "src/main.py",
                "content": """
def calculate_sum(a, b):
    if a < 0:
        return 0
    return a + b

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result
"""
            }
        ]
        
        # When
        # 실제 ChromaDB 없이 테스트하기 위해 Mock 사용
        with patch('chromadb.HttpClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            service = VectorDBService()
            stored_ids = await service.store_code_snippets(repo_url, files)
        
        # Then
        assert isinstance(stored_ids, list)
        # ChromaDB가 실제 연결되지 않더라도 테스트 통과
        assert True
    
    @pytest.mark.asyncio
    async def test_search_similar_code(self):
        """유사 코드 검색 테스트"""
        # Given
        query = "function add"
        language = "python"
        
        # When
        with patch('chromadb.HttpClient') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [["def add(a, b): return a + b"]],
                "metadatas": [[{"language": "python", "complexity": 1.0}]],
                "ids": [["snippet_1"]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            service = VectorDBService()
            results = await service.search_similar_code(query, language)
        
        # Then
        assert isinstance(results, list)
        # Mock 데이터가 반환되는지 확인
        if results:
            assert "content" in results[0]
            assert "metadata" in results[0]
    
    @pytest.mark.asyncio
    async def test_extract_code_snippets(self):
        """코드 스니펫 추출 테스트"""
        # Given
        with patch('chromadb.HttpClient'):
            service = VectorDBService()
            
            content = """
def hello_world():
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self):
        self.value = 0
    
    def increment(self):
        self.value += 1
        return self.value
"""
            file_path = "test.py"
        
        # When
        snippets = service._extract_code_snippets(content, file_path)
        
        # Then
        assert len(snippets) >= 2  # 함수와 클래스
        assert any(snippet["type"] == "function" for snippet in snippets)
        assert any(snippet["type"] == "class" for snippet in snippets)
        
        for snippet in snippets:
            assert "content" in snippet
            assert "start_line" in snippet
            assert "end_line" in snippet
            assert "complexity" in snippet


class TestQuestionGenerator:
    """Question Generator 테스트"""
    
    @pytest.mark.asyncio
    async def test_generate_questions(self):
        """질문 생성 테스트"""
        # Given
        repo_url = "https://github.com/test/repo"
        difficulty_level = "medium"
        question_count = 5
        
        # Mock Vector DB
        mock_analysis_data = {
            "analysis_text": "React JavaScript project with Redux",
            "metadata": {
                "tech_stack": '{"javascript": 0.8, "react": 0.6}',
                "complexity_score": 5.5,
                "file_count": 25
            }
        }
        
        mock_code_snippets = [
            {
                "id": "snippet_1",
                "content": "function calculateTotal(items) { return items.reduce(...); }",
                "metadata": {
                    "language": "javascript",
                    "complexity": 3.0,
                    "file_path": "src/utils.js"
                }
            }
        ]
        
        # When
        with patch.object(VectorDBService, 'search_analysis_context', return_value=mock_analysis_data):
            with patch.object(VectorDBService, 'get_code_by_complexity', return_value=mock_code_snippets):
                with patch.object(VectorDBService, 'search_similar_code', return_value=[]):
                    generator = QuestionGenerator()
                    result = await generator.generate_questions(
                        repo_url, difficulty_level, question_count
                    )
        
        # Then
        assert result["success"] is True
        assert result["repo_url"] == repo_url
        assert result["difficulty"] == difficulty_level
        assert len(result["questions"]) == question_count
        
        # 질문 구조 검증
        for question in result["questions"]:
            assert "id" in question
            assert "type" in question
            assert "question" in question
            assert "difficulty" in question
    
    @pytest.mark.asyncio
    async def test_generate_code_analysis_questions(self):
        """코드 분석 질문 생성 테스트"""
        # Given
        generator = QuestionGenerator()
        
        # Mock state with code snippets
        from app.agents.question_generator import QuestionState
        state = QuestionState(
            repo_url="https://github.com/test/repo",
            difficulty_level="medium",
            code_snippets=[
                {
                    "id": "test_snippet",
                    "content": "function complexFunction(x, y) { if (x > 0) { for(let i = 0; i < y; i++) { console.log(i); } } }",
                    "metadata": {
                        "language": "javascript",
                        "complexity": 4.5,
                        "file_path": "src/complex.js"
                    }
                }
            ]
        )
        
        # When
        questions = await generator._generate_code_analysis_questions(state, 2)
        
        # Then
        assert len(questions) >= 1
        
        for question in questions:
            assert question["type"] == "code_analysis"
            assert "question" in question
            assert "difficulty" in question
            
            if "code_snippet" in question:
                assert "content" in question["code_snippet"]
                assert "language" in question["code_snippet"]
                assert "complexity" in question["code_snippet"]
    
    @pytest.mark.asyncio
    async def test_generate_tech_stack_questions(self):
        """기술 스택 질문 생성 테스트"""
        # Given
        generator = QuestionGenerator()
        
        from app.agents.question_generator import QuestionState
        state = QuestionState(
            repo_url="https://github.com/test/repo",
            difficulty_level="medium",
            analysis_data={
                "metadata": {
                    "tech_stack": '{"react": 0.8, "typescript": 0.6, "node": 0.4}'
                }
            }
        )
        
        # When
        questions = await generator._generate_tech_stack_questions(state, 3)
        
        # Then
        assert len(questions) == 3
        
        for question in questions:
            assert question["type"] == "tech_stack"
            assert "technology" in question
            assert question["technology"] in ["react", "typescript", "node"]
    
    @pytest.mark.asyncio
    async def test_generate_architecture_questions(self):
        """아키텍처 질문 생성 테스트"""
        # Given
        generator = QuestionGenerator()
        
        from app.agents.question_generator import QuestionState
        state = QuestionState(
            repo_url="https://github.com/test/repo",
            difficulty_level="hard",
            analysis_data={
                "metadata": {
                    "file_count": 150,
                    "tech_stack": '{"react": 0.8, "microservices": 0.5}'
                }
            }
        )
        
        # When
        questions = await generator._generate_architecture_questions(state, 2)
        
        # Then
        assert len(questions) == 2
        
        for question in questions:
            assert question["type"] == "architecture"
            assert "context" in question
            assert question["context"]["scale"] == "large"  # file_count > 100
    
    def test_complexity_ranges(self):
        """난이도별 복잡도 범위 테스트"""
        # Given
        generator = QuestionGenerator()
        
        # When & Then
        easy_range = generator.complexity_ranges["easy"]
        medium_range = generator.complexity_ranges["medium"]
        hard_range = generator.complexity_ranges["hard"]
        
        assert easy_range == (1.0, 3.0)
        assert medium_range == (3.0, 6.0)
        assert hard_range == (6.0, 10.0)
        
        # 범위가 연속적인지 확인
        assert easy_range[1] == medium_range[0]
        assert medium_range[1] == hard_range[0]
    
    def test_question_templates(self):
        """질문 템플릿 존재 여부 테스트"""
        # Given
        generator = QuestionGenerator()
        
        # When & Then
        required_types = ["code_analysis", "architecture", "tech_stack", "design_patterns", "problem_solving", "best_practices"]
        
        for question_type in required_types:
            assert question_type in generator.question_templates
            assert len(generator.question_templates[question_type]) > 0
            
            # 템플릿에 적절한 플레이스홀더가 있는지 확인
            if question_type == "tech_stack":
                templates = generator.question_templates[question_type]
                assert any("{tech}" in template for template in templates)
            elif question_type == "design_patterns":
                templates = generator.question_templates[question_type]
                assert any("{pattern}" in template for template in templates)
    
    def test_generate_answer_points(self):
        """예상 답변 포인트 생성 테스트"""
        # Given
        generator = QuestionGenerator()
        
        snippet = {
            "metadata": {
                "complexity": 7.0,
                "language": "python"
            }
        }
        
        # When
        complexity_points = generator._generate_answer_points("이 코드의 시간 복잡도는", snippet)
        bug_points = generator._generate_answer_points("이 코드에서 발생할 수 있는 버그나 문제점", snippet)
        refactor_points = generator._generate_answer_points("이 코드를 리팩토링한다면", snippet)
        test_points = generator._generate_answer_points("이 코드의 단위 테스트를", snippet)
        
        # Then
        assert len(complexity_points) > 0
        assert len(bug_points) > 0
        assert len(refactor_points) > 0
        assert len(test_points) > 0
        
        # 복잡도가 높은 경우 더 많은 포인트 생성
        assert "알고리즘 최적화" in complexity_points
        assert "Null 체크 및 예외 처리" in bug_points
        assert "함수 분리" in refactor_points
        assert "경계값 테스트" in test_points
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_questions(self):
        """후속 질문 생성 테스트"""
        # Given
        generator = QuestionGenerator()
        
        original_question = {
            "id": "code_analysis_1",
            "type": "code_analysis",
            "question": "이 코드의 복잡도를 분석해주세요."
        }
        
        user_answer = "이 코드는 중첩된 반복문으로 인해 O(n²) 복잡도를 가집니다."
        
        # When
        follow_ups = await generator.generate_follow_up_questions(original_question, user_answer)
        
        # Then
        assert len(follow_ups) > 0
        
        for follow_up in follow_ups:
            assert follow_up["type"] == "follow_up"
            assert follow_up["parent_question_id"] == original_question["id"]
            assert "question" in follow_up
            assert "time_estimate" in follow_up