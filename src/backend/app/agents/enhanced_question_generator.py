"""
Enhanced Question Generator Agent

4차원 분석 결과와 실제 파일 내용을 통합하여 고품질 기술면접 질문을 생성하는 시스템
- SmartFileImportanceAnalyzer 통합
- FileContentExtractor 통합
- tiktoken 기반 토큰 관리
- 파일 유형별 특화 프롬프트
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from app.core.ai_service import ai_service
from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
from app.services.file_content_extractor import FileContentExtractor


@dataclass
class EnhancedQuestionState:
    """향상된 질문 생성 상태 관리"""
    repo_url: str
    analysis_data: Optional[Dict[str, Any]] = None
    prioritized_files: Optional[List[Dict[str, Any]]] = None
    file_contents: Optional[Dict[str, Any]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    token_budget: Optional[Dict[str, Any]] = None
    difficulty_level: str = "medium"
    question_types: Optional[List[str]] = None
    error: Optional[str] = None
    warnings: Optional[List[str]] = None


class EnhancedQuestionGenerator:
    """4차원 분석 결과 기반 향상된 질문 생성기"""
    
    def __init__(self, github_token: Optional[str] = None):
        # 기존 분석 시스템들과 통합
        self.file_importance_analyzer = SmartFileImportanceAnalyzer()
        self.file_content_extractor = FileContentExtractor(github_token=github_token)
        
        # 토큰 관리 설정 (Gemini 2.0 Flash의 1M 토큰 컨텍스트 활용)
        self.max_tokens_per_question = 100000  # 질문당 예산 대폭 확대
        self.token_safety_margin = 10000  # 안전 마진도 확대
        
        # tiktoken 인코딩 (GPT-3.5-turbo 기준)
        self.encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            except Exception as e:
                print(f"tiktoken 초기화 실패: {e}")
        
        # 파일 유형별 특화 프롬프트 템플릿
        self.specialized_prompts = {
            "controller": """
이 파일은 HTTP 요청을 처리하는 컨트롤러입니다. 다음 실제 코드 내용을 분석하여 질문을 생성해주세요:

=== 컨트롤러 파일 정보 ===
파일 경로: {file_path}
중요도 점수: {importance_score}/1.0
복잡도: {complexity_score}/1.0

=== 실제 코드 내용 ===
```{language}
{content}
```

=== 질문 생성 지침 ===
위 코드에서 실제로 구현된 내용을 바탕으로 다음 관점에서 질문하세요:
- HTTP 요청 처리 방식과 라우팅 구조
- 에러 핸들링 및 예외 처리 전략
- 입력 검증과 보안 고려사항
- RESTful API 설계 원칙 적용
- 실제 사용된 프레임워크별 특성 (Django, FastAPI, Express 등)

{difficulty_instruction}

실제 함수명, 클래스명, 변수명을 직접 언급하며 구체적인 질문을 생성해주세요.
""",
            
            "model": """
이 파일은 데이터 모델을 정의하는 파일입니다. 다음 실제 코드 내용을 분석하여 질문을 생성해주세요:

=== 모델 파일 정보 ===
파일 경로: {file_path}
중요도 점수: {importance_score}/1.0
복잡도: {complexity_score}/1.0

=== 실제 코드 내용 ===
```{language}
{content}
```

=== 질문 생성 지침 ===
위 코드에서 실제로 정의된 모델을 바탕으로 다음 관점에서 질문하세요:
- 데이터 모델 설계와 필드 정의 전략
- 관계 설정 (Foreign Key, Many-to-Many 등)
- 데이터 유효성 검사 및 제약 조건
- 인덱스 설계와 성능 최적화
- ORM 활용 방법과 쿼리 최적화

{difficulty_instruction}

실제 모델명, 필드명, 관계 설정을 직접 언급하며 구체적인 질문을 생성해주세요.
""",
            
            "service": """
이 파일은 비즈니스 로직을 처리하는 서비스입니다. 다음 실제 코드 내용을 분석하여 질문을 생성해주세요:

=== 서비스 파일 정보 ===
파일 경로: {file_path}
중요도 점수: {importance_score}/1.0
복잡도: {complexity_score}/1.0

=== 실제 코드 내용 ===
```{language}
{content}
```

=== 질문 생성 지침 ===
위 코드에서 실제로 구현된 비즈니스 로직을 바탕으로 다음 관점에서 질문하세요:
- 비즈니스 로직의 분리와 캡슐화
- 데이터 처리 및 변환 로직
- 트랜잭션 관리와 데이터 일관성
- 외부 서비스 연동 및 API 호출
- 에러 처리와 롤백 전략

{difficulty_instruction}

실제 서비스 클래스명, 메서드명, 처리 로직을 직접 언급하며 구체적인 질문을 생성해주세요.
""",
            
            "configuration": """
이 파일은 프로젝트 설정을 관리하는 파일입니다. 다음 실제 내용을 분석하여 질문을 생성해주세요:

=== 설정 파일 정보 ===
파일 경로: {file_path}
중요도 점수: {importance_score}/1.0

=== 실제 설정 내용 ===
```{language}
{content}
```

=== 질문 생성 지침 ===
위 설정에서 실제로 정의된 내용을 바탕으로 다음 관점에서 질문하세요:
- 환경별 설정 분리 전략 (dev/staging/prod)
- 보안 설정과 민감 정보 관리
- 성능 최적화 관련 설정
- 의존성 관리와 버전 호환성
- 배포 및 운영 환경 고려사항

{difficulty_instruction}

실제 설정값, 환경변수명, 의존성 정보를 직접 언급하며 구체적인 질문을 생성해주세요.
""",
            
            "general": """
다음은 프로젝트의 주요 파일입니다. 실제 코드 내용을 분석하여 질문을 생성해주세요:

=== 파일 정보 ===
파일 경로: {file_path}
중요도 점수: {importance_score}/1.0
복잡도: {complexity_score}/1.0

=== 실제 코드 내용 ===
```{language}
{content}
```

=== 질문 생성 지침 ===
위 코드에서 실제로 구현된 내용을 바탕으로 다음 관점에서 질문하세요:
- 코드 구조와 설계 패턴
- 알고리즘과 데이터 구조 선택
- 성능 최적화와 메모리 관리
- 코드 품질과 유지보수성
- 테스트 가능성과 확장성

{difficulty_instruction}

실제 함수명, 클래스명, 구현 로직을 직접 언급하며 구체적인 질문을 생성해주세요.
"""
        }
        
        # 난이도별 지시사항
        self.difficulty_instructions = {
            "easy": "초급 개발자 수준에서 기본 개념과 구현 방법에 대해 질문하세요.",
            "medium": "중급 개발자 수준에서 설계 선택 이유와 고려사항에 대해 질문하세요.",
            "hard": "고급 개발자 수준에서 최적화, 확장성, 아키텍처 관점에서 심도 있게 질문하세요."
        }
        
        # Gemini 특화 설정
        self.gemini_context_window = 1000000  # 1M 토큰
        self.gemini_optimized = True  # Gemini 최적화 모드
        
        print(f"[DEBUG] EnhancedQuestionGenerator Gemini 특화 초기화 완료:")
        print(f"  - 질문당 최대 토큰: {self.max_tokens_per_question:,}")
        print(f"  - 파일 내용 토큰 제한: 50,000")
        print(f"  - Gemini 컨텍스트 윈도우: {self.gemini_context_window:,}")
        print(f"  - 파일 크기 제한: 1MB")
    
    def integrate_smart_file_analysis(self, analysis_data: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """스마트 파일 분석 결과 통합"""
        
        result = {
            "prioritized_files": [],
            "tech_stack_context": {},
            "analysis_summary": {}
        }
        
        # 동적 가중치 적용하여 파일 중요도 재계산
        if session_id:
            # 세션별 동적 가중치 적용
            self.file_importance_analyzer.update_weights_for_session(session_id)
        
        # 스마트 파일 분석 결과 추출 (동적 가중치가 적용된 결과)
        smart_analysis = analysis_data.get("smart_file_analysis", {})
        critical_files = smart_analysis.get("critical_files", [])
        
        # 더미/샘플 데이터 제외 및 중요도 점수순으로 정렬
        filtered_files = [
            f for f in critical_files 
            if not self.file_importance_analyzer.is_excluded_file(f.get("file_path", ""))
        ]
        sorted_files = sorted(filtered_files, key=lambda x: x.get("importance_score", 0), reverse=True)
        
        # 우선순위 파일 목록 생성
        for file_info in sorted_files:
            prioritized_file = {
                "file_path": file_info.get("file_path", ""),
                "importance_score": file_info.get("importance_score", 0.0),
                "selection_reasons": file_info.get("reasons", []),
                "metrics_breakdown": file_info.get("metrics", {}),
                "file_type": self._classify_file_type(file_info.get("file_path", "")),
                "priority_rank": len(result["prioritized_files"]) + 1
            }
            result["prioritized_files"].append(prioritized_file)
        
        # 기술 스택 컨텍스트 추출
        result["tech_stack_context"] = analysis_data.get("tech_stack", {})
        
        # 분석 요약 정보
        result["analysis_summary"] = {
            "total_files_analyzed": len(critical_files),
            "high_importance_files": len([f for f in critical_files if f.get("importance_score", 0) > 0.8]),
            "average_importance": sum(f.get("importance_score", 0) for f in critical_files) / max(len(critical_files), 1)
        }
        
        return result
    
    def calculate_token_budget(self, files_content: Dict[str, str], max_tokens: int) -> Dict[str, Any]:
        """토큰 예산 계산"""
        
        budget = {
            "total_content_tokens": 0,
            "available_tokens": 0,
            "recommended_files": [],
            "token_per_file": {},
            "budget_exceeded": False
        }
        
        # 각 파일의 토큰 수 계산
        file_tokens = {}
        total_tokens = 0
        
        for file_path, content in files_content.items():
            if content:
                token_info = self.calculate_tokens(content)
                file_tokens[file_path] = token_info["token_count"]
                total_tokens += token_info["token_count"]
        
        budget["total_content_tokens"] = total_tokens
        budget["token_per_file"] = file_tokens
        
        # 토큰 제한 초과 여부 확인
        available_tokens = max_tokens - self.token_safety_margin
        budget["available_tokens"] = available_tokens
        
        if total_tokens <= available_tokens:
            # 모든 파일을 포함할 수 있음
            budget["recommended_files"] = list(files_content.keys())
        else:
            # 토큰 예산에 맞게 파일 선택
            budget["budget_exceeded"] = True
            budget["recommended_files"] = self._select_files_within_budget(
                file_tokens, available_tokens
            )
        
        return budget
    
    async def generate_enhanced_questions(
        self,
        analysis_data: Dict[str, Any],
        question_count: int = 5,
        difficulty_level: str = "medium",
        question_types: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """향상된 질문 생성 메인 함수"""
        
        generation_start_time = time.time()
        print(f"[QUESTION_GEN] ========== 질문 생성 시작 ==========")
        print(f"[QUESTION_GEN] 요청 파라미터: {question_count}개 질문, 난이도 {difficulty_level}")
        print(f"[QUESTION_GEN] 세션 ID: {session_id or 'None'}")
        
        state = EnhancedQuestionState(
            repo_url=analysis_data.get("repo_url", ""),
            analysis_data=analysis_data,
            difficulty_level=difficulty_level,
            question_types=question_types or ["code_analysis"],
            warnings=[]
        )
        
        print(f"[QUESTION_GEN] 대상 저장소: {state.repo_url}")
        print(f"[QUESTION_GEN] 질문 유형: {state.question_types}")
        
        try:
            # 1. 스마트 파일 분석 결과 통합 (동적 가중치 적용)
            print(f"[QUESTION_GEN] 1단계: 스마트 파일 분석 결과 통합")
            step_start = time.time()
            
            # 입력 데이터 분석
            smart_analysis = analysis_data.get("smart_file_analysis", {})
            files_count = len(smart_analysis.get("files", []))
            critical_files_count = len(smart_analysis.get("critical_files", []))
            print(f"[QUESTION_GEN] 입력 데이터: 전체 파일 {files_count}개, 핵심 파일 {critical_files_count}개")
            
            integration_result = self.integrate_smart_file_analysis(analysis_data, session_id)
            state.prioritized_files = integration_result["prioritized_files"]
            step_time = time.time() - step_start
            print(f"[QUESTION_GEN] 1단계 완료 ({step_time:.2f}초): {len(state.prioritized_files)}개 우선순위 파일 선정")
            
            # 2. 파일 내용 추출 및 토큰 예산 계산
            print(f"[QUESTION_GEN] 2단계: 파일 내용 추출 및 토큰 예산 계산")
            step_start = time.time()
            
            file_contents = analysis_data.get("file_contents", {})
            if file_contents:
                state.file_contents = file_contents
                content_dict = {k: v.get("content", "") for k, v in file_contents.items() if v.get("success")}
                
                # 파일 내용 통계
                total_files = len(file_contents)
                success_files = len([v for v in file_contents.values() if v.get("success")])
                total_chars = sum(len(content) for content in content_dict.values())
                print(f"[QUESTION_GEN] 파일 내용: 전체 {total_files}개, 성공 {success_files}개, 총 {total_chars:,}문자")
                
                state.token_budget = self.calculate_token_budget(content_dict, self.max_tokens_per_question)
                print(f"[QUESTION_GEN] 토큰 예산: 총 {state.token_budget.get('total_budget', 0):,} 토큰")
            else:
                state.warnings.append("파일 내용을 사용할 수 없습니다.")
                print(f"[QUESTION_GEN] 경고: 파일 내용 없음")
            
            step_time = time.time() - step_start
            print(f"[QUESTION_GEN] 2단계 완료 ({step_time:.2f}초)")
            
            # 3. 실제 파일 내용 기반 질문 생성
            print(f"[QUESTION_GEN] 3단계: 실제 파일 내용 기반 질문 생성")
            step_start = time.time()
            
            state.questions = await self._generate_content_based_questions(state, question_count)
            
            step_time = time.time() - step_start
            total_time = time.time() - generation_start_time
            
            # 결과 요약
            generated_count = len(state.questions) if state.questions else 0
            warnings_count = len(state.warnings)
            
            print(f"[QUESTION_GEN] 3단계 완료 ({step_time:.2f}초): {generated_count}개 질문 생성")
            print(f"[QUESTION_GEN] ========== 질문 생성 완료 ({total_time:.2f}초) ==========")
            print(f"[QUESTION_GEN] 최종 결과: 성공 {generated_count}개, 경고 {warnings_count}개")
            
            if state.questions:
                for i, q in enumerate(state.questions, 1):
                    q_type = q.get('type', 'unknown')
                    q_tech = q.get('tech_focus', 'unknown')
                    print(f"[QUESTION_GEN] Q{i}: {q_type} ({q_tech})")
            
            # 4. 결과 반환
            return {
                "success": True,
                "repo_url": state.repo_url,
                "difficulty": difficulty_level,
                "question_count": len(state.questions),
                "questions": state.questions,
                "token_budget_info": state.token_budget,
                "files_analyzed": len(state.prioritized_files) if state.prioritized_files else 0,
                "warnings": state.warnings
            }
            
        except Exception as e:
            error_time = time.time() - generation_start_time
            state.error = str(e)
            
            print(f"[QUESTION_GEN] ========== 질문 생성 실패 ({error_time:.2f}초) ==========")
            print(f"[QUESTION_GEN] 오류: {state.error}")
            print(f"[QUESTION_GEN] 경고 {len(state.warnings)}개: {state.warnings}")
            
            import traceback
            print(f"[QUESTION_GEN] 스택 트레이스:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": state.error,
                "repo_url": state.repo_url,
                "questions": [],
                "warnings": state.warnings or []
            }
    
    async def _generate_content_based_questions(
        self, 
        state: EnhancedQuestionState, 
        question_count: int
    ) -> List[Dict[str, Any]]:
        """실제 파일 내용 기반 질문 생성"""
        
        questions = []
        
        if not state.prioritized_files or not state.file_contents:
            return questions
        
        # 토큰 예산 내 파일들 선택
        available_files = state.token_budget.get("recommended_files", [])
        
        # 실제 파일 내용이 있고 토큰 예산 내인 파일들만 필터링
        valid_files = []
        for file_info in state.prioritized_files:
            file_path = file_info["file_path"]
            if (file_path in available_files and 
                file_path in state.file_contents and 
                state.file_contents[file_path].get("success")):
                valid_files.append(file_info)
        
        if not valid_files:
            state.warnings.append("토큰 예산 내에서 유효한 파일을 찾을 수 없습니다.")
            return questions
        
        # 질문 생성할 파일 수 결정
        files_to_process = min(question_count, len(valid_files))
        selected_files = valid_files[:files_to_process]
        
        # 각 파일에 대해 질문 생성
        for i, file_info in enumerate(selected_files):
            try:
                file_path = file_info["file_path"]
                file_content_info = state.file_contents[file_path]
                file_content = file_content_info["content"]
                
                # 토큰 제한에 맞게 내용 트렁케이션 (Gemini의 긴 컨텍스트 활용)
                truncated_content = self.truncate_content_by_tokens(
                    content=file_content,
                    max_tokens=50000,  # 파일 전체 내용 포함을 위해 대폭 확대
                    preserve_important_sections=True
                )
                
                # 다차원 컨텍스트 생성
                context = self.generate_multi_dimensional_context(file_path, state.analysis_data)
                
                # 특화 프롬프트 생성
                prompt = self.generate_enhanced_prompt(
                    file_context={
                        "file_path": file_path,
                        "content": truncated_content,
                        "importance_score": file_info["importance_score"],
                        "metrics": file_info["metrics_breakdown"],
                        "file_type": file_info["file_type"]
                    },
                    question_type="code_analysis",
                    difficulty=state.difficulty_level,
                    include_metrics=True
                )
                
                # AI 질문 생성
                ai_response = await self._generate_ai_question(prompt)
                
                if ai_response and "question" in ai_response:
                    question = {
                        "id": f"enhanced_{i}_{int(time.time() * 1000)}",
                        "type": "code_analysis",
                        "question": ai_response["question"],
                        "file_context": {
                            "file_path": file_path,
                            "importance_score": file_info["importance_score"],
                            "selection_reasons": file_info["selection_reasons"],
                            "file_type": file_info["file_type"],
                            "content_preview": truncated_content[:200] + "..." if len(truncated_content) > 200 else truncated_content
                        },
                        "multi_dimensional_context": context,
                        "difficulty": state.difficulty_level,
                        "time_estimate": self._estimate_answer_time(file_info["metrics_breakdown"]),
                        "actual_content_included": True,
                        "token_usage": self.calculate_tokens(prompt)["token_count"],
                        "importance_score": file_info["importance_score"],
                        "generated_by": "AI_Enhanced"
                    }
                    
                    # 질문 품질 검증
                    quality_score = self.validate_question_quality(question)
                    question["quality_score"] = quality_score
                    
                    if quality_score >= 0.5:  # 품질 임계값
                        questions.append(question)
                    else:
                        state.warnings.append(f"낮은 품질로 인해 제외된 질문: {file_path}")
                
            except Exception as e:
                state.warnings.append(f"질문 생성 실패 ({file_path}): {str(e)}")
                continue
        
        return questions
    
    def get_specialized_prompt_template(
        self, 
        file_type: str, 
        file_path: str, 
        difficulty: str
    ) -> str:
        """파일 유형별 특화 프롬프트 템플릿 반환"""
        
        template = self.specialized_prompts.get(file_type, self.specialized_prompts["general"])
        difficulty_instruction = self.difficulty_instructions.get(difficulty, "")
        
        # 플레이스홀더를 포함한 템플릿 반환
        return template.replace("{difficulty_instruction}", difficulty_instruction)
    
    def calculate_tokens(self, text: str) -> Dict[str, Any]:
        """tiktoken을 사용한 토큰 계산"""
        
        if not text:
            return {"token_count": 0, "text_length": 0, "tokens_per_char_ratio": 0}
        
        token_count = 0
        if TIKTOKEN_AVAILABLE and self.encoding:
            try:
                tokens = self.encoding.encode(text)
                token_count = len(tokens)
            except Exception:
                # tiktoken 실패 시 근사치 계산 (1 token ≈ 4 characters)
                token_count = len(text) // 4 + 1
        else:
            # tiktoken 없을 시 근사치 계산
            token_count = len(text) // 4 + 1
        
        return {
            "token_count": token_count,
            "text_length": len(text),
            "tokens_per_char_ratio": token_count / len(text) if len(text) > 0 else 0
        }
    
    def truncate_content_by_tokens(
        self, 
        content: str, 
        max_tokens: int, 
        preserve_important_sections: bool = True
    ) -> str:
        """토큰 제한에 맞게 내용 트렁케이션"""
        
        if not content:
            return content
        
        # 현재 토큰 수 확인
        current_tokens = self.calculate_tokens(content)["token_count"]
        if current_tokens <= max_tokens:
            return content
        
        # 중요 섹션 우선 보존
        if preserve_important_sections:
            important_sections = self._extract_important_sections(content)
            
            # 중요 섹션들을 우선으로 포함
            truncated_parts = []
            current_token_count = 0
            
            for section in important_sections:
                section_tokens = self.calculate_tokens(section)["token_count"]
                if current_token_count + section_tokens <= max_tokens - 100:  # 여유분
                    truncated_parts.append(section)
                    current_token_count += section_tokens
                else:
                    break
            
            if truncated_parts:
                result = "\n\n".join(truncated_parts)
                result += "\n\n... (content truncated for token limit)"
                return result
        
        # 단순 트렁케이션 (토큰 기준)
        lines = content.split('\n')
        truncated_lines = []
        current_token_count = 0
        
        for line in lines:
            line_tokens = self.calculate_tokens(line)["token_count"]
            if current_token_count + line_tokens <= max_tokens - 50:  # 여유분
                truncated_lines.append(line)
                current_token_count += line_tokens
            else:
                break
        
        result = '\n'.join(truncated_lines)
        if len(truncated_lines) < len(lines):
            result += "\n... (content truncated for token limit)"
        
        return result
    
    def prioritize_questions_by_importance(
        self, 
        analysis_data: Dict[str, Any], 
        max_questions: int
    ) -> List[Dict[str, Any]]:
        """중요도 기반 질문 우선순위 결정"""
        
        integration_result = self.integrate_smart_file_analysis(analysis_data)
        prioritized_files = integration_result["prioritized_files"]
        
        # 상위 중요도 파일들 선택
        selected_files = prioritized_files[:max_questions]
        
        result = []
        for file_info in selected_files:
            question_priority = {
                "file_path": file_info["file_path"],
                "importance_score": file_info["importance_score"],
                "selection_reasons": file_info["selection_reasons"],
                "metrics_breakdown": file_info["metrics_breakdown"],
                "expected_question_quality": self._estimate_question_quality(file_info)
            }
            result.append(question_priority)
        
        return result
    
    def generate_multi_dimensional_context(
        self, 
        file_path: str, 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4차원 분석 결과 기반 다차원 컨텍스트 생성"""
        
        context = {
            "structural_importance": {"score": 0.0, "explanation": ""},
            "dependency_centrality": {"score": 0.0, "explanation": ""},
            "churn_analysis": {"score": 0.0, "explanation": ""},
            "complexity_metrics": {"score": 0.0, "explanation": ""},
            "file_content": {"available": False, "size": 0},
            "importance_breakdown": {}
        }
        
        # 스마트 파일 분석에서 해당 파일 찾기
        smart_analysis = analysis_data.get("smart_file_analysis", {})
        critical_files = smart_analysis.get("critical_files", [])
        
        target_file = None
        for file_info in critical_files:
            if file_info.get("file_path") == file_path:
                target_file = file_info
                break
        
        if target_file:
            metrics = target_file.get("metrics", {})
            
            # 구조적 중요도
            structural = metrics.get("structural_importance", 0.0)
            context["structural_importance"] = {
                "score": structural,
                "explanation": self._explain_structural_importance(structural)
            }
            
            # 의존성 중심성
            dependency = metrics.get("dependency_centrality", 0.0)
            context["dependency_centrality"] = {
                "score": dependency,
                "explanation": self._explain_dependency_centrality(dependency)
            }
            
            # 변경 빈도 분석
            churn = metrics.get("churn_risk", 0.0)
            context["churn_analysis"] = {
                "score": churn,
                "explanation": self._explain_churn_analysis(churn)
            }
            
            # 복잡도 메트릭
            complexity = metrics.get("complexity_score", 0.0)
            context["complexity_metrics"] = {
                "score": complexity,
                "explanation": self._explain_complexity_metrics(complexity)
            }
            
            # 중요도 분해
            context["importance_breakdown"] = {
                "total_score": target_file.get("importance_score", 0.0),
                "contributing_factors": target_file.get("reasons", []),
                "weighted_scores": {
                    "structural": structural * 0.4,
                    "dependency": dependency * 0.3,
                    "churn": churn * 0.2,
                    "complexity": complexity * 0.1
                }
            }
        
        # 파일 내용 정보
        file_contents = analysis_data.get("file_contents", {})
        if file_path in file_contents:
            content_info = file_contents[file_path]
            context["file_content"] = {
                "available": content_info.get("success", False),
                "size": content_info.get("size", 0),
                "encoding": content_info.get("encoding", "unknown")
            }
        
        return context
    
    def generate_enhanced_prompt(
        self,
        file_context: Dict[str, Any],
        question_type: str,
        difficulty: str,
        include_metrics: bool = True
    ) -> str:
        """향상된 프롬프트 생성"""
        
        file_path = file_context["file_path"]
        content = file_context["content"]
        importance_score = file_context["importance_score"]
        metrics = file_context.get("metrics", {})
        file_type = file_context.get("file_type", "general")
        
        # 언어 추정
        language = self._infer_language_from_path(file_path)
        
        # 파일 유형별 특화 템플릿 가져오기
        template = self.get_specialized_prompt_template(file_type, file_path, difficulty)
        
        # 메트릭 정보 포함 여부
        complexity_score = metrics.get("complexity_score", 0.0) if include_metrics else 0.0
        
        # Gemini 특화 프롬프트 헤더 추가
        gemini_header = f"""# 코드 분석 및 기술면접 질문 생성

## 분석 대상 파일
- **파일 경로**: `{file_path}`
- **프로그래밍 언어**: {language}
- **중요도 점수**: {importance_score:.2f}/1.0
- **복잡도 점수**: {complexity_score:.2f}/1.0

## 전체 파일 내용 (완전 분석용)
```{language}
{content}
```

## 요구사항
{self.difficulty_instructions.get(difficulty, "")}

## 출력 형식
다음 JSON 형식으로 응답해주세요:
"""
        
        # 템플릿 변수 대체
        prompt = template.format(
            file_path=file_path,
            content=content,
            language=language,
            importance_score=importance_score,
            complexity_score=complexity_score,
            difficulty_instruction=self.difficulty_instructions.get(difficulty, "")
        )
        
        # Gemini 특화 헤더와 기존 프롬프트 결합
        full_prompt = gemini_header + "\n" + prompt
        
        return full_prompt
    
    def validate_question_quality(self, question: Dict[str, Any]) -> float:
        """질문 품질 검증"""
        
        quality_score = 0.0
        question_text = question.get("question", "")
        
        if not question_text:
            return 0.0
        
        # 1. 실제 파일 내용 참조 여부 (30점)
        if question.get("actual_content_included", False):
            quality_score += 0.3
        
        # 2. 구체적인 코드 요소 언급 (25점)
        file_context = question.get("file_context", {})
        content_preview = file_context.get("content_preview", "")
        
        if content_preview:
            # 실제 함수명, 클래스명, 변수명 등이 질문에 포함되는지 확인
            code_elements = self._extract_code_elements(content_preview)
            mentioned_elements = sum(1 for element in code_elements if element.lower() in question_text.lower())
            
            if mentioned_elements > 0:
                quality_score += min(0.25, mentioned_elements * 0.05)
        
        # 3. 질문의 구체성 (20점)
        abstract_words = ["일반적으로", "보통", "대개", "만약", "가정"]
        abstract_count = sum(1 for word in abstract_words if word in question_text)
        
        if abstract_count == 0:
            quality_score += 0.2
        elif abstract_count == 1:
            quality_score += 0.1
        
        # 4. 기술적 깊이 (15점)
        technical_indicators = ["구현", "설계", "아키텍처", "최적화", "성능", "확장성", "유지보수성"]
        technical_count = sum(1 for indicator in technical_indicators if indicator in question_text)
        
        quality_score += min(0.15, technical_count * 0.03)
        
        # 5. 질문 길이의 적절성 (10점)
        word_count = len(question_text.split())
        if 20 <= word_count <= 80:  # 적절한 길이
            quality_score += 0.1
        elif 10 <= word_count < 20 or 80 < word_count <= 100:
            quality_score += 0.05
        
        return min(1.0, quality_score)
    
    async def extract_file_contents_for_questions(
        self, 
        file_paths: List[str], 
        owner: str, 
        repo: str
    ) -> List[Dict[str, Any]]:
        """질문 생성용 파일 내용 추출"""
        
        important_files = [{"path": path} for path in file_paths]
        
        results = await self.file_content_extractor.extract_files_content(
            owner=owner,
            repo=repo,
            important_files=important_files
        )
        
        return results
    
    def integrate_with_file_analyzer(self, mock_analyzer_result: Dict[str, Any]) -> Dict[str, Any]:
        """SmartFileImportanceAnalyzer와의 통합"""
        
        # Mock 데이터를 실제 분석 데이터 형식으로 변환
        analysis_data = {
            "smart_file_analysis": mock_analyzer_result
        }
        
        return self.integrate_smart_file_analysis(analysis_data)
    
    # 내부 헬퍼 메서드들
    def _classify_file_type(self, file_path: str) -> str:
        """파일 유형 분류"""
        
        path_lower = file_path.lower()
        
        if "controller" in path_lower or "handler" in path_lower:
            return "controller"
        elif "model" in path_lower or "entity" in path_lower:
            return "model"
        elif "service" in path_lower:
            return "service"
        elif any(config in path_lower for config in ["config", "setting", "env", "package.json"]):
            return "configuration"
        elif "util" in path_lower or "helper" in path_lower:
            return "utility"
        else:
            return "general"
    
    def _select_files_within_budget(
        self, 
        file_tokens: Dict[str, int], 
        available_tokens: int
    ) -> List[str]:
        """토큰 예산 내 파일 선택"""
        
        # 토큰 수 기준으로 정렬 (적은 것부터)
        sorted_files = sorted(file_tokens.items(), key=lambda x: x[1])
        
        selected_files = []
        current_tokens = 0
        
        for file_path, tokens in sorted_files:
            if current_tokens + tokens <= available_tokens:
                selected_files.append(file_path)
                current_tokens += tokens
            else:
                break
        
        return selected_files
    
    def _extract_important_sections(self, content: str) -> List[str]:
        """중요한 코드 섹션 추출"""
        
        sections = []
        lines = content.split('\n')
        
        current_section = []
        in_important_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # 중요한 블록 시작 패턴
            if (stripped.startswith(('class ', 'def ', 'function ', 'async def')) or
                'import ' in stripped or 'from ' in stripped):
                
                if current_section and in_important_block:
                    sections.append('\n'.join(current_section))
                
                current_section = [line]
                in_important_block = True
            
            elif in_important_block:
                current_section.append(line)
                
                # 블록 종료 조건 (간단한 휴리스틱)
                if not line.startswith(' ') and not line.startswith('\t') and stripped and not stripped.startswith('#'):
                    if len(current_section) > 1:
                        sections.append('\n'.join(current_section[:-1]))
                    current_section = [line]
        
        # 마지막 섹션 추가
        if current_section and in_important_block:
            sections.append('\n'.join(current_section))
        
        return sections[:5]  # 최대 5개 섹션
    
    def _estimate_question_quality(self, file_info: Dict[str, Any]) -> float:
        """파일 정보 기반 질문 품질 추정"""
        
        importance_score = file_info.get("importance_score", 0.0)
        metrics = file_info.get("metrics_breakdown", {})
        
        # 중요도와 복잡도가 높을수록 좋은 질문 가능성 증가
        complexity = metrics.get("complexity_score", 0.0)
        
        quality_estimate = (importance_score * 0.7) + (complexity * 0.3)
        return min(1.0, quality_estimate)
    
    def _estimate_answer_time(self, metrics: Dict[str, Any]) -> str:
        """메트릭 기반 답변 예상 시간 추정"""
        
        complexity = metrics.get("complexity_score", 0.0)
        
        if complexity <= 0.3:
            return "5-7분"
        elif complexity <= 0.6:
            return "7-10분"
        elif complexity <= 0.8:
            return "10-15분"
        else:
            return "15-20분"
    
    def _extract_code_elements(self, content: str) -> List[str]:
        """코드에서 식별자 추출"""
        
        elements = []
        
        # 클래스명 추출
        class_matches = re.findall(r'class\s+(\w+)', content, re.IGNORECASE)
        elements.extend(class_matches)
        
        # 함수명 추출
        function_matches = re.findall(r'(?:def|function)\s+(\w+)', content, re.IGNORECASE)
        elements.extend(function_matches)
        
        # 변수명 추출 (간단한 패턴)
        variable_matches = re.findall(r'(\w+)\s*=', content)
        elements.extend([v for v in variable_matches if len(v) > 2])
        
        return list(set(elements))[:10]  # 중복 제거 후 최대 10개
    
    def _infer_language_from_path(self, file_path: str) -> str:
        """파일 경로에서 언어 추정"""
        
        if not file_path:
            return "text"
        
        extension = file_path.split('.')[-1].lower() if '.' in file_path else ""
        
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'java': 'java',
            'json': 'json',
            'html': 'html',
            'css': 'css',
            'md': 'markdown'
        }
        
        return language_map.get(extension, extension or "text")
    
    def _explain_structural_importance(self, score: float) -> str:
        """구조적 중요도 점수 설명"""
        if score >= 0.8:
            return "프로젝트 핵심 구조 파일 (메인 진입점, 설정 파일 등)"
        elif score >= 0.6:
            return "주요 모듈 또는 핵심 비즈니스 로직 파일"
        elif score >= 0.4:
            return "일반적인 기능 구현 파일"
        else:
            return "보조적 역할의 파일 (유틸리티, 테스트 등)"
    
    def _explain_dependency_centrality(self, score: float) -> str:
        """의존성 중심성 점수 설명"""
        if score >= 0.8:
            return "매우 많은 파일들이 참조하는 핵심 의존성"
        elif score >= 0.6:
            return "여러 모듈에서 참조하는 중요한 공통 모듈"
        elif score >= 0.4:
            return "일부 모듈에서 참조하는 유틸리티 모듈"
        else:
            return "독립적이거나 참조가 적은 모듈"
    
    def _explain_churn_analysis(self, score: float) -> str:
        """변경 빈도 분석 점수 설명"""
        if score >= 0.8:
            return "매우 활발히 변경되는 핫스팟 파일 (주의 필요)"
        elif score >= 0.6:
            return "지속적으로 개선되고 있는 활성 파일"
        elif score >= 0.4:
            return "가끔 변경되는 안정적인 파일"
        else:
            return "거의 변경되지 않는 안정된 파일"
    
    def _explain_complexity_metrics(self, score: float) -> str:
        """복잡도 메트릭 점수 설명"""
        if score >= 0.8:
            return "매우 높은 복잡도 - 리팩토링 검토 필요"
        elif score >= 0.6:
            return "높은 복잡도 - 주의 깊은 유지보수 필요"
        elif score >= 0.4:
            return "적절한 복잡도 수준"
        else:
            return "낮은 복잡도 - 단순한 구조"
    
    async def _generate_ai_question(self, prompt: str) -> Optional[Dict[str, Any]]:
        """AI를 사용한 질문 생성"""
        
        try:
            response = await ai_service.generate_analysis(prompt)
            
            if response and "content" in response:
                return {
                    "question": response["content"].strip(),
                    "type": "code_analysis"
                }
            
        except Exception as e:
            print(f"AI 질문 생성 실패: {e}")
        
        return None