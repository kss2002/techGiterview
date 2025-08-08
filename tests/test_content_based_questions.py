"""
실제 파일 내용 활용 질문 생성 테스트

TDD 방식으로 EnhancedQuestionGenerator가 실제 파일 내용을 활용하여
구체적이고 실무적인 질문을 생성하는지 검증하는 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

# 테스트 대상 모듈
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from app.agents.enhanced_question_generator import EnhancedQuestionGenerator


class TestContentBasedQuestions:
    """실제 파일 내용 기반 질문 생성 검증 테스트"""
    
    @pytest.fixture
    def generator(self):
        """EnhancedQuestionGenerator 인스턴스 생성"""
        return EnhancedQuestionGenerator(github_token="test_token")
    
    @pytest.fixture
    def mock_typescript_service_content(self):
        """실제 TypeScript 서비스 파일 내용"""
        return """
export class UserService {
    private apiClient: ApiClient;
    private cache: Map<string, User> = new Map();
    
    constructor(apiClient: ApiClient) {
        this.apiClient = apiClient;
    }
    
    async getUserById(userId: string): Promise<User | null> {
        // 캐시 확인
        if (this.cache.has(userId)) {
            return this.cache.get(userId)!;
        }
        
        try {
            const response = await this.apiClient.get(`/users/${userId}`);
            const user = response.data as User;
            
            // 캐시에 저장
            this.cache.set(userId, user);
            return user;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            return null;
        }
    }
    
    async updateUserProfile(userId: string, profile: Partial<UserProfile>): Promise<boolean> {
        try {
            await this.apiClient.put(`/users/${userId}/profile`, profile);
            
            // 캐시 무효화
            this.cache.delete(userId);
            return true;
        } catch (error) {
            console.error('Failed to update user profile:', error);
            return false;
        }
    }
    
    clearCache(): void {
        this.cache.clear();
    }
}
"""
    
    @pytest.fixture
    def mock_analysis_data_with_content(self, mock_typescript_service_content):
        """파일 내용이 포함된 분석 데이터"""
        return {
            "repo_url": "https://github.com/test/business-app",
            "smart_file_analysis": {
                "files": [
                    {
                        "file_path": "src/services/UserService.ts",
                        "importance_score": 0.95,
                        "reasons": ["핵심 비즈니스 로직", "API 호출 관리", "캐싱 전략"],
                        "metrics": {
                            "structural_importance": 0.9,
                            "dependency_centrality": 0.8,
                            "churn_risk": 0.7,
                            "complexity_score": 0.6
                        },
                        "category": "critical",
                        "rank": 1
                    }
                ]
            },
            "file_contents": {
                "src/services/UserService.ts": {
                    "success": True,
                    "content": mock_typescript_service_content,
                    "size": len(mock_typescript_service_content),
                    "file_path": "src/services/UserService.ts"
                }
            },
            "tech_stack": {"typescript": 0.8, "javascript": 0.2},
            "repo_info": {"name": "business-app", "language": "TypeScript"}
        }
    
    @pytest.mark.asyncio
    async def test_questions_include_actual_code_elements(self, generator, mock_analysis_data_with_content):
        """테스트: 생성된 질문에 실제 코드 요소들이 포함되는지 검증"""
        
        # Given: 실제 파일 내용이 포함된 분석 데이터
        analysis_data = mock_analysis_data_with_content
        
        # Mock AI service response
        mock_ai_response = {
            "question": "UserService 클래스에서 getUserById 메서드가 캐시(this.cache)를 사용하는 이유와, 캐시 무효화를 updateUserProfile에서만 수행하는 설계 결정에 대해 설명해주세요. 또한 apiClient.get() 호출 시 에러 처리에서 null을 반환하는 것의 장단점은 무엇인가요?",
            "type": "implementation_analysis", 
            "difficulty": "medium",
            "tech_focus": "TypeScript",
            "expected_duration": "5-7분"
        }
        
        with patch('app.core.ai_service.ai_service.generate_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_ai_response
            
            # When: 질문 생성 실행
            result = await generator.generate_enhanced_questions(
                analysis_data=analysis_data,
                question_count=1,
                difficulty_level="medium"
            )
        
        # Then: 결과 검증
        assert result["success"], f"질문 생성 실패: {result.get('error')}"
        assert len(result["questions"]) > 0, "질문이 생성되지 않았습니다"
        
        question = result["questions"][0]
        question_text = question.get("question", "")
        
        # 실제 코드 요소들이 질문에 포함되었는지 검증
        code_elements_to_check = [
            "UserService",  # 클래스명
            "getUserById",  # 메서드명
            "apiClient",    # 속성명
            "cache",        # 캐시 변수
            "updateUserProfile"  # 다른 메서드명
        ]
        
        included_elements = []
        for element in code_elements_to_check:
            if element in question_text:
                included_elements.append(element)
        
        assert len(included_elements) >= 3, f"실제 코드 요소가 충분히 포함되지 않음. 포함된 요소: {included_elements}"
    
    @pytest.mark.asyncio
    async def test_questions_reflect_actual_implementation_details(self, generator, mock_analysis_data_with_content):
        """테스트: 질문이 실제 구현 세부사항을 반영하는지 검증"""
        
        # Given: 실제 파일 내용이 포함된 분석 데이터
        analysis_data = mock_analysis_data_with_content
        
        # Mock AI service response - 실제 구현 세부사항을 반영한 질문
        mock_ai_response = {
            "question": "이 UserService에서 Map<string, User> 타입의 캐시를 사용하고 있습니다. 만약 사용자가 많아져서 메모리 사용량이 문제가 된다면, LRU 캐시나 다른 캐싱 전략으로 어떻게 개선할 수 있을까요? 또한 현재 캐시 무효화가 updateUserProfile에서만 이루어지는데, 다른 업데이트 메서드들이 추가된다면 어떤 설계 패턴을 적용하시겠습니까?",
            "type": "optimization_design",
            "difficulty": "medium", 
            "implementation_focus": ["caching_strategy", "memory_management", "design_patterns"]
        }
        
        with patch('app.core.ai_service.ai_service.generate_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_ai_response
            
            # When: 질문 생성 실행
            result = await generator.generate_enhanced_questions(
                analysis_data=analysis_data,
                question_count=1,
                difficulty_level="medium"
            )
        
        # Then: 구현 세부사항 반영 검증
        assert result["success"], "질문 생성 실패"
        
        question = result["questions"][0]
        question_text = question.get("question", "")
        
        # 구현 세부사항 키워드 검증
        implementation_details = [
            "Map<string, User>",  # 실제 타입 정의
            "캐시",               # 구현된 기능
            "updateUserProfile",  # 실제 메서드명
            "무효화"              # 실제 구현된 로직
        ]
        
        detail_matches = sum(1 for detail in implementation_details if detail in question_text)
        assert detail_matches >= 2, f"구현 세부사항이 충분히 반영되지 않음: {question_text}"
    
    @pytest.mark.asyncio
    async def test_gemini_context_utilization(self, generator, mock_analysis_data_with_content):
        """테스트: Gemini의 긴 컨텍스트가 활용되는지 검증"""
        
        # Given: 대용량 파일 내용 (Gemini 특화 테스트)
        large_content = mock_analysis_data_with_content["file_contents"]["src/services/UserService.ts"]["content"] * 100  # 반복하여 큰 파일 시뮬레이션
        
        analysis_data = mock_analysis_data_with_content.copy()
        analysis_data["file_contents"]["src/services/UserService.ts"]["content"] = large_content
        analysis_data["file_contents"]["src/services/UserService.ts"]["size"] = len(large_content)
        
        # When: 토큰 계산 및 트렁케이션 테스트
        truncated_content = generator.truncate_content_by_tokens(
            content=large_content,
            max_tokens=50000,  # Gemini 특화 큰 제한
            preserve_important_sections=True
        )
        
        # Then: Gemini의 긴 컨텍스트 활용 검증
        assert len(truncated_content) > 10000, "Gemini의 긴 컨텍스트가 제대로 활용되지 않음"
        assert "UserService" in truncated_content, "중요한 코드 섹션이 보존되지 않음"
        assert "getUserById" in truncated_content, "핵심 메서드가 보존되지 않음"
    
    def test_tech_stack_accurate_identification(self, generator):
        """테스트: 기술 스택이 정확히 식별되는지 검증"""
        
        # Given: package.json 내용 기반 기술 스택 분석
        package_json_content = '''
{
  "name": "business-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@types/node": "^18.0.0",
    "typescript": "^4.9.0",
    "express": "^4.18.0"
  }
}
'''
        
        # When: 언어 추정
        language = generator._infer_language_from_path("package.json")
        
        # Then: 정확한 식별 검증
        assert language in ["json", "javascript", "typescript"], f"부정확한 언어 식별: {language}"
    
    def test_question_quality_validation(self, generator):
        """테스트: 생성된 질문의 품질이 검증되는지 테스트"""
        
        # Given: 다양한 품질의 질문들
        high_quality_question = {
            "question": "UserService 클래스의 getUserById 메서드에서 캐시 확인 후 API 호출하는 패턴을 사용했는데, 이 방식의 장점과 동시성 문제 해결 방안은?",
            "file_context": {
                "content_preview": "getUserById async method with cache check"
            }
        }
        
        low_quality_question = {
            "question": "TypeScript에 대해 일반적으로 설명해주세요.",
            "file_context": {
                "content_preview": ""
            }
        }
        
        # When: 질문 품질 검증
        high_score = generator.validate_question_quality(high_quality_question)
        low_score = generator.validate_question_quality(low_quality_question)
        
        # Then: 품질 점수 차이 검증
        assert high_score > low_score, f"고품질 질문({high_score})이 저품질 질문({low_score})보다 높은 점수를 받지 못함"
        assert high_score > 0.6, f"고품질 질문의 점수가 너무 낮음: {high_score}"
        assert low_score < 0.4, f"저품질 질문의 점수가 너무 높음: {low_score}"


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"])