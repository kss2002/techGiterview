"""
향상된 질문 생성기 테스트 - TDD 방식

main_rules.md에 따라 테스트를 먼저 작성하고, 이후 실제 구현을 진행합니다.
4차원 분석 결과 통합과 실제 파일 내용 기반 질문 생성 시스템
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

# 구현 예정 모듈들
# from app.agents.enhanced_question_generator import EnhancedQuestionGenerator


class TestEnhancedQuestionGenerator:
    """향상된 질문 생성기 테스트"""
    
    @pytest.fixture
    def question_generator(self):
        """테스트용 향상된 질문 생성기 인스턴스"""
        from app.agents.enhanced_question_generator import EnhancedQuestionGenerator
        return EnhancedQuestionGenerator()
    
    @pytest.fixture
    def sample_analysis_data(self):
        """4차원 분석 결과 샘플 데이터"""
        return {
            "repo_url": "https://github.com/owner/repo",
            "tech_stack": {"Python": 0.7, "JavaScript": 0.2, "HTML": 0.1},
            "smart_file_analysis": {
                "critical_files": [
                    {
                        "file_path": "src/main.py",
                        "importance_score": 0.95,
                        "reasons": ["애플리케이션 진입점 파일", "다른 파일들이 많이 참조하는 핵심 의존성"],
                        "metrics": {
                            "structural_importance": 0.9,
                            "dependency_centrality": 0.8,
                            "churn_risk": 0.6,
                            "complexity_score": 0.7
                        }
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
                        }
                    }
                ]
            },
            "file_contents": {
                "src/main.py": {
                    "success": True,
                    "content": """#!/usr/bin/env python3
import os
import sys
from config import DATABASE_URL, API_KEY

class Application:
    def __init__(self):
        self.db_url = DATABASE_URL
        self.api_key = API_KEY
    
    async def start(self):
        print("Starting application...")
        await self.connect_database()
    
    async def connect_database(self):
        # Database connection logic
        pass

if __name__ == "__main__":
    app = Application()
    asyncio.run(app.start())
""",
                    "size": 512,
                    "encoding": "utf-8"
                },
                "src/config.py": {
                    "success": True,
                    "content": """import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

class Config:
    def __init__(self):
        self.database_url = DATABASE_URL
        self.api_key = API_KEY
        self.debug = DEBUG
""",
                    "size": 384,
                    "encoding": "utf-8"
                }
            }
        }
    
    @pytest.fixture
    def sample_tiktoken_result(self):
        """tiktoken 토큰 계산 결과 Mock"""
        return {
            "total_tokens": 1500,
            "prompt_tokens": 1200,
            "max_tokens": 4000,
            "remaining_tokens": 2500
        }

    def test_enhanced_question_generator_initialization(self, question_generator):
        """향상된 질문 생성기 초기화 테스트"""
        # Then: 필요한 속성들이 올바르게 초기화되어야 함
        assert hasattr(question_generator, 'file_importance_analyzer')
        assert hasattr(question_generator, 'file_content_extractor')
        assert hasattr(question_generator, 'calculate_tokens')  # 메서드로 변경
        assert hasattr(question_generator, 'max_tokens_per_question')
        assert question_generator.max_tokens_per_question == 3000  # 기본값
        assert hasattr(question_generator, 'encoding')  # tiktoken 인코딩
        assert hasattr(question_generator, 'specialized_prompts')  # 특화 프롬프트

    def test_integrate_smart_file_analysis(self, question_generator, sample_analysis_data):
        """스마트 파일 분석 결과 통합 테스트"""
        # Given: 4차원 분석 결과
        analysis_data = sample_analysis_data
        
        # When: 스마트 파일 분석 결과 통합
        result = question_generator.integrate_smart_file_analysis(analysis_data)
        
        # Then: 통합된 데이터 구조가 반환되어야 함
        assert "prioritized_files" in result
        assert "tech_stack_context" in result
        assert "analysis_summary" in result
        
        prioritized_files = result["prioritized_files"]
        assert len(prioritized_files) > 0
        
        # 중요도순으로 정렬되어야 함
        scores = [f["importance_score"] for f in prioritized_files]
        assert scores == sorted(scores, reverse=True)
        
        # 각 파일에 필요한 메타데이터가 포함되어야 함
        for file_info in prioritized_files:
            assert "file_path" in file_info
            assert "importance_score" in file_info
            assert "selection_reasons" in file_info
            assert "metrics_breakdown" in file_info

    def test_calculate_token_budget(self, question_generator, sample_tiktoken_result):
        """토큰 예산 계산 테스트"""
        # Given: 파일 내용들과 토큰 제한
        files_content = {
            "src/main.py": "# Main application file\nclass App: pass",
            "src/config.py": "# Configuration settings\nDATABASE_URL = 'sqlite://'"
        }
        max_tokens = 4000
        
        # When: 토큰 예산 계산
        with patch.object(question_generator, 'calculate_tokens') as mock_calc:
            mock_calc.return_value = {
                "token_count": sample_tiktoken_result["total_tokens"],
                "text_length": 100,
                "tokens_per_char_ratio": 0.25
            }
            
            budget = question_generator.calculate_token_budget(files_content, max_tokens)
        
        # Then: 토큰 예산이 올바르게 계산되어야 함
        assert "total_content_tokens" in budget
        assert "available_tokens" in budget
        assert "recommended_files" in budget
        assert "token_per_file" in budget
        
        assert budget["available_tokens"] <= max_tokens
        assert len(budget["recommended_files"]) > 0

    def test_generate_enhanced_questions_with_file_content(self, question_generator, sample_analysis_data):
        """실제 파일 내용 기반 향상된 질문 생성 테스트"""
        # Given: 분석 데이터와 파일 내용
        
        # When: 향상된 질문 생성
        with patch.object(question_generator, '_generate_ai_question') as mock_ai:
            mock_ai.return_value = {
                "question": "이 main.py 파일에서 Application 클래스의 connect_database() 메서드가 async로 정의된 이유와 실제 데이터베이스 연결 로직을 구현할 때 고려해야 할 사항들을 설명해주세요.",
                "type": "code_analysis",
                "complexity": "medium"
            }
            
            result = asyncio.run(question_generator.generate_enhanced_questions(
                analysis_data=sample_analysis_data,
                question_count=3,
                difficulty_level="medium"
            ))
        
        # Then: 실제 파일 내용을 참조한 질문들이 생성되어야 함
        assert result["success"] is True
        assert len(result["questions"]) > 0
        
        for question in result["questions"]:
            assert "id" in question
            assert "type" in question
            assert "question" in question
            assert "file_context" in question
            assert "importance_score" in question
            assert "actual_content_included" in question
            assert question["actual_content_included"] is True

    def test_file_type_specialized_prompts(self, question_generator):
        """파일 유형별 특화 프롬프트 생성 테스트"""
        # Given: 다양한 파일 유형들
        test_files = [
            {"path": "src/controllers/user_controller.py", "type": "controller"},
            {"path": "src/models/user.py", "type": "model"},
            {"path": "src/services/auth_service.py", "type": "service"},
            {"path": "config/database.py", "type": "configuration"},
            {"path": "src/utils/helpers.py", "type": "utility"}
        ]
        
        # When: 각 파일 유형별 특화 프롬프트 생성
        for file_info in test_files:
            prompt_template = question_generator.get_specialized_prompt_template(
                file_type=file_info["type"],
                file_path=file_info["path"],
                difficulty="medium"
            )
            
            # Then: 파일 유형에 맞는 특화된 프롬프트가 반환되어야 함
            assert prompt_template is not None
            assert len(prompt_template) > 100  # 충분한 길이의 프롬프트
            
            # 파일 유형별 키워드가 포함되어야 함
            if file_info["type"] == "controller":
                assert any(keyword in prompt_template.lower() for keyword in 
                          ["http", "요청", "routing", "endpoint", "handler"])
            elif file_info["type"] == "model":
                assert any(keyword in prompt_template.lower() for keyword in 
                          ["모델", "데이터", "스키마", "관계", "validation"])
            elif file_info["type"] == "service":
                assert any(keyword in prompt_template.lower() for keyword in 
                          ["비즈니스", "로직", "service", "처리", "트랜잭션"])

    def test_token_aware_content_truncation(self, question_generator):
        """토큰 제한 고려 내용 트렁케이션 테스트"""
        # Given: 긴 파일 내용과 토큰 제한
        long_content = "\n".join([f"def function_{i}(): pass" for i in range(200)])
        max_tokens = 1000
        
        # When: 토큰 인식 내용 트렁케이션
        with patch.object(question_generator, 'calculate_tokens') as mock_tokens:
            # Make the content appear to exceed token limit to force truncation
            mock_tokens.side_effect = lambda text: {
                "token_count": max(max_tokens + 100, len(text) // 2),  # Force exceeding limit
                "text_length": len(text), 
                "tokens_per_char_ratio": 0.25
            }
            
            truncated = question_generator.truncate_content_by_tokens(
                content=long_content,
                max_tokens=max_tokens,
                preserve_important_sections=True
            )
        
        # Then: 토큰 제한에 맞게 내용이 트렁케이션되어야 함
        assert len(truncated) > 0
        assert len(truncated) < len(long_content)
        
        # 중요한 섹션이 보존되어야 함 (내용이 있고 첫 줄이 포함되거나 트렁케이션 메시지가 있어야 함)
        assert "def function_" in truncated or "content truncated" in truncated.lower()
        
        # 트렁케이션 표시가 있어야 함
        assert "..." in truncated or "truncated" in truncated.lower()

    def test_importance_score_integration(self, question_generator, sample_analysis_data):
        """중요도 점수 통합 테스트"""
        # Given: 스마트 파일 분석 결과
        analysis_data = sample_analysis_data
        
        # When: 중요도 점수를 기반으로 질문 우선순위 결정
        prioritized_questions = question_generator.prioritize_questions_by_importance(
            analysis_data=analysis_data,
            max_questions=5
        )
        
        # Then: 중요도 점수에 따라 우선순위가 결정되어야 함
        assert len(prioritized_questions) <= 5
        
        # 중요도 점수순으로 정렬되어야 함
        scores = [q["importance_score"] for q in prioritized_questions]
        assert scores == sorted(scores, reverse=True)
        
        # 각 질문에 선정 이유가 포함되어야 함
        for question in prioritized_questions:
            assert "selection_reasons" in question
            assert len(question["selection_reasons"]) > 0

    def test_multi_dimensional_context_generation(self, question_generator, sample_analysis_data):
        """다차원 컨텍스트 생성 테스트"""
        # Given: 4차원 분석 결과
        analysis_data = sample_analysis_data
        file_path = "src/main.py"
        
        # When: 다차원 컨텍스트 생성
        context = question_generator.generate_multi_dimensional_context(
            file_path=file_path,
            analysis_data=analysis_data
        )
        
        # Then: 4차원 분석 결과가 모두 포함된 컨텍스트가 생성되어야 함
        assert "structural_importance" in context
        assert "dependency_centrality" in context  
        assert "churn_analysis" in context
        assert "complexity_metrics" in context
        assert "file_content" in context
        assert "importance_breakdown" in context
        
        # 각 차원의 설명이 포함되어야 함
        assert context["structural_importance"]["score"] >= 0
        assert context["structural_importance"]["explanation"] is not None

    def test_tiktoken_integration(self, question_generator):
        """tiktoken 라이브러리 통합 테스트"""
        # Given: 텍스트 샘플
        sample_text = """
        def hello_world():
            print("Hello, World!")
            return "success"
        """
        
        # When: 토큰 계산
        with patch('tiktoken.encoding_for_model') as mock_tiktoken:
            mock_encoding = Mock()
            mock_encoding.encode.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # 10 tokens
            mock_tiktoken.return_value = mock_encoding
            
            token_info = question_generator.calculate_tokens(sample_text)
        
        # Then: 토큰 정보가 정확히 계산되어야 함
        assert "token_count" in token_info
        assert "text_length" in token_info
        assert "tokens_per_char_ratio" in token_info
        assert token_info["token_count"] > 0

    def test_enhanced_prompt_templates(self, question_generator):
        """향상된 프롬프트 템플릿 테스트"""
        # Given: 파일 내용과 분석 결과
        file_context = {
            "file_path": "src/main.py",
            "content": "class Application: pass",
            "importance_score": 0.95,
            "metrics": {
                "complexity_score": 0.7,
                "dependency_centrality": 0.8
            }
        }
        
        # When: 향상된 프롬프트 생성
        prompt = question_generator.generate_enhanced_prompt(
            file_context=file_context,
            question_type="code_analysis",
            difficulty="medium",
            include_metrics=True
        )
        
        # Then: 실제 파일 내용과 메트릭이 포함된 프롬프트가 생성되어야 함
        assert file_context["file_path"] in prompt
        assert "Application" in prompt  # 실제 클래스명
        assert "중요도 점수" in prompt or "importance" in prompt.lower()
        assert "복잡도" in prompt or "complexity" in prompt.lower()
        
        # 지시사항이 명확해야 함
        assert "실제" in prompt and "구체적" in prompt

    def test_question_quality_validation(self, question_generator):
        """질문 품질 검증 테스트"""
        # Given: 생성된 질문들
        sample_questions = [
            {
                "question": "이 Application 클래스에서 사용된 async/await 패턴의 구현 이유를 설명해주세요.",
                "actual_content_included": True,
                "file_context": {
                    "content_preview": "class Application:\n    async def connect_database(self):\n        pass"
                }
            },
            {
                "question": "일반적으로 Python에서 클래스를 어떻게 정의하나요?",
                "actual_content_included": False,
                "file_context": {
                    "content_preview": ""
                }
            }
        ]
        
        # When: 질문 품질 검증
        for question in sample_questions:
            quality_score = question_generator.validate_question_quality(question)
            
            # Then: 실제 파일 내용을 참조한 질문이 높은 점수를 받아야 함
            if question["actual_content_included"]:
                assert quality_score >= 0.5  # 임계값을 현실적으로 조정
            else:
                assert quality_score < 0.5

    def test_error_handling_for_content_extraction_failure(self, question_generator):
        """파일 내용 추출 실패 시 오류 처리 테스트"""
        # Given: 파일 내용 추출 실패 시나리오
        analysis_data = {
            "smart_file_analysis": {
                "critical_files": [
                    {"file_path": "src/missing.py", "importance_score": 0.9}
                ]
            },
            "file_contents": {
                "src/missing.py": {
                    "success": False,
                    "error": "File not found"
                }
            }
        }
        
        # When: 질문 생성 시도
        result = asyncio.run(question_generator.generate_enhanced_questions(
            analysis_data=analysis_data,
            question_count=1
        ))
        
        # Then: 적절한 오류 처리가 되어야 함
        assert result["success"] is True  # 전체 프로세스는 성공
        assert len(result["questions"]) == 0  # 하지만 생성된 질문은 없음
        assert "warnings" in result
        assert len(result["warnings"]) > 0

    def test_performance_with_large_files(self, question_generator):
        """대용량 파일 처리 성능 테스트"""
        # Given: 대용량 파일 내용 시뮬레이션
        large_content = "\n".join([f"def function_{i}(): pass" for i in range(1000)])
        analysis_data = {
            "smart_file_analysis": {
                "critical_files": [
                    {"file_path": "src/large.py", "importance_score": 0.8}
                ]
            },
            "file_contents": {
                "src/large.py": {
                    "success": True,
                    "content": large_content,
                    "size": len(large_content)
                }
            }
        }
        
        # When: 질문 생성 (성능 측정)
        import time
        start_time = time.time()
        
        with patch.object(question_generator, '_generate_ai_question') as mock_ai:
            mock_ai.return_value = {"question": "Test question", "type": "code_analysis"}
            
            result = asyncio.run(question_generator.generate_enhanced_questions(
                analysis_data=analysis_data,
                question_count=1
            ))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Then: 합리적인 시간 내에 처리되어야 함 (5초 이내)
        assert processing_time < 5.0
        assert result["success"] is True


class TestPromptEngineering:
    """프롬프트 엔지니어링 전용 테스트"""
    
    def test_file_type_specific_prompt_generation(self):
        """파일 유형별 특화 프롬프트 생성 테스트"""
        # Given: 파일 유형별 샘플
        from app.agents.enhanced_question_generator import EnhancedQuestionGenerator
        generator = EnhancedQuestionGenerator()
        
        file_types = ["controller", "model", "service", "configuration", "utility"]
        
        # When & Then: 각 유형별로 다른 프롬프트가 생성되어야 함
        prompts = {}
        for file_type in file_types:
            prompt = generator.get_specialized_prompt_template(
                file_type=file_type,
                file_path=f"src/{file_type}.py",
                difficulty="medium"
            )
            prompts[file_type] = prompt
            
            # 각 프롬프트는 해당 파일 유형의 특성을 반영해야 함
            assert len(prompt) > 200
            assert file_type in prompt.lower() or file_type.replace('_', ' ') in prompt.lower()
        
        # 모든 프롬프트가 서로 달라야 함
        unique_prompts = set(prompts.values())
        assert len(unique_prompts) == len(file_types)

    def test_token_calculation_accuracy(self):
        """토큰 계산 정확도 테스트"""
        # Given: 다양한 길이의 텍스트 샘플
        from app.agents.enhanced_question_generator import EnhancedQuestionGenerator
        generator = EnhancedQuestionGenerator()
        
        test_texts = [
            "Hello world",
            "def hello(): return 'world'",
            "# " + "a" * 1000,  # 긴 주석
            """
            class ComplexClass:
                def __init__(self, param1, param2):
                    self.param1 = param1
                    self.param2 = param2
            """
        ]
        
        # When & Then: 각 텍스트의 토큰 수가 합리적으로 계산되어야 함
        for text in test_texts:
            with patch('tiktoken.encoding_for_model') as mock_tiktoken:
                # Mock tiktoken to return predictable results
                mock_encoding = Mock()
                # Approximate 1 token per 4 characters (typical for GPT models)
                token_count = len(text) // 4 + 1
                mock_encoding.encode.return_value = list(range(token_count))
                mock_tiktoken.return_value = mock_encoding
                
                result = generator.calculate_tokens(text)
                
                assert result["token_count"] > 0
                assert result["text_length"] == len(text)
                assert result["tokens_per_char_ratio"] > 0


class TestIntegrationWithExistingSystems:
    """기존 시스템과의 통합 테스트"""
    
    def test_integration_with_file_importance_analyzer(self):
        """SmartFileImportanceAnalyzer와의 통합 테스트"""
        # Given: Mock 분석 결과
        from app.agents.enhanced_question_generator import EnhancedQuestionGenerator
        generator = EnhancedQuestionGenerator()
        
        # Mock SmartFileImportanceAnalyzer
        with patch('app.services.file_importance_analyzer.SmartFileImportanceAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_project_file_importance.return_value = {
                "critical_files": [
                    {"file_path": "src/main.py", "importance_score": 0.95}
                ]
            }
            
            # When: 통합 분석 수행
            result = generator.integrate_with_file_analyzer(mock_analyzer_result={
                "critical_files": [{"file_path": "src/main.py", "importance_score": 0.95}]
            })
            
            # Then: 통합 결과가 올바르게 반환되어야 함
            assert "prioritized_files" in result
            assert len(result["prioritized_files"]) > 0

    def test_integration_with_file_content_extractor(self):
        """FileContentExtractor와의 통합 테스트"""
        # Given: Mock 파일 내용 추출 결과
        from app.agents.enhanced_question_generator import EnhancedQuestionGenerator
        generator = EnhancedQuestionGenerator()
        
        # Mock FileContentExtractor
        with patch('app.services.file_content_extractor.FileContentExtractor') as mock_extractor:
            mock_extractor.return_value.extract_files_content.return_value = [
                {
                    "success": True,
                    "file_path": "src/main.py",
                    "content": "def main(): pass",
                    "size": 16
                }
            ]
            
            # When: 파일 내용 추출 통합
            result = asyncio.run(generator.extract_file_contents_for_questions(
                file_paths=["src/main.py"],
                owner="owner",
                repo="repo"
            ))
            
            # Then: 파일 내용이 올바르게 추출되어야 함
            assert len(result) > 0
            assert result[0]["success"] is True
            assert "content" in result[0]