"""
Question Strategies

질문 생성 전략 및 세부 로직을 분리한 모듈
"""

import json
import random
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.core.ai_service import AIProvider

from app.agents.question_ai_caller import QuestionAICaller
from app.agents.question_file_helpers import QuestionFileHelpers
from app.agents.question_templates import QuestionTemplateManager

if TYPE_CHECKING:
    from app.agents.question_generator import QuestionState


class QuestionStrategies:
    """질문 생성 전략 모음"""

    def __init__(
        self,
        ai_caller: QuestionAICaller,
        file_helpers: QuestionFileHelpers,
        template_manager: QuestionTemplateManager,
    ) -> None:
        self.ai_caller = ai_caller
        self.file_helpers = file_helpers
        self.template_manager = template_manager
        self.api_keys: Dict[str, str] = {}
        self._metadata_question_generator = None
        self._estimate_question_time_func = None

    def set_api_keys(self, api_keys: Optional[Dict[str, str]]) -> None:
        self.api_keys = api_keys or {}

    def set_metadata_question_generator(self, generator) -> None:
        self._metadata_question_generator = generator

    def set_estimate_question_time(self, estimator) -> None:
        self._estimate_question_time_func = estimator

    def _estimate_time(self, complexity: float) -> str:
        if self._estimate_question_time_func:
            return self._estimate_question_time_func(complexity)

        if complexity <= 2.0:
            return "3-5분"
        if complexity <= 4.0:
            return "5-7분"
        if complexity <= 6.0:
            return "7-10분"
        if complexity <= 8.0:
            return "10-15분"
        return "15-20분"

    async def _generate_code_analysis_questions_with_files(
        self,
        state: "QuestionState",
        count: int,
        question_index: int,
    ) -> List[Dict[str, Any]]:
        """파일 선택 다양성을 고려한 코드 분석 질문 생성"""

        if not state.code_snippets:
            print("[QUESTION_GEN] 코드 스니펫이 없어서 코드 분석 질문 생성을 건너뜁니다.")
            return []

        # 우선순위 기준으로 정렬된 전체 파일 목록
        def get_priority_score(snippet):
            importance_scores = {"very_high": 100, "high": 80, "medium": 50, "low": 20}
            base_score = importance_scores.get(snippet["metadata"].get("importance", "low"), 20)
            if snippet["metadata"].get("has_real_content", False):
                base_score += 30
            complexity = snippet["metadata"].get("complexity", 1.0)
            base_score += min(complexity * 2, 10)
            return base_score

        all_snippets = sorted(state.code_snippets, key=get_priority_score, reverse=True)
        real_content_snippets = [s for s in all_snippets if s["metadata"].get("has_real_content", False)]

        if not real_content_snippets:
            print("[QUESTION_GEN] 실제 파일 내용이 없습니다. 메타데이터 기반 질문을 생성합니다.")
            if self._metadata_question_generator:
                return await self._metadata_question_generator(state, all_snippets, count)
            return []

        # 질문 인덱스에 따라 다른 파일 세트 선택
        selected_files = self.file_helpers._get_files_for_question_index(real_content_snippets, question_index)

        questions = []
        for snippet in selected_files[:count]:  # count만큼만 생성
            try:
                # 기존 질문 생성 로직 사용
                question = await self._generate_single_code_analysis_question(snippet, state)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"[QUESTION_GEN] 코드 분석 질문 생성 실패: {e}")
                continue

        return questions

    async def _generate_tech_stack_questions_with_files(
        self,
        state: "QuestionState",
        count: int,
        question_index: int,
    ) -> List[Dict[str, Any]]:
        """파일 선택 다양성을 고려한 기술 스택 질문 생성"""

        # 기술 스택 추출
        tech_stack = []
        if state.analysis_data and "metadata" in state.analysis_data:
            tech_stack_str = state.analysis_data["metadata"].get("tech_stack", "{}")
            try:
                tech_stack_dict = json.loads(tech_stack_str)
                tech_stack = [tech for tech, score in tech_stack_dict.items() if score >= 0.05]
            except Exception as e:
                print(f"[QUESTION_GEN] tech_stack JSON 파싱 실패: {e}")

        if not tech_stack:
            print("[QUESTION_GEN] 유효한 기술 스택이 없어서 tech_stack 질문 생성을 건너뜁니다.")
            return []

        # 질문 인덱스에 따라 다른 파일 세트 선택
        if state.code_snippets:
            all_snippets = sorted(state.code_snippets, key=lambda s: s["metadata"].get("importance", "low"), reverse=True)
            selected_files = self.file_helpers._get_files_for_question_index(all_snippets, question_index)
        else:
            selected_files = []

        questions = []
        for i in range(count):
            tech = random.choice(tech_stack)

            # 선택된 파일들을 기반으로 기술 스택 질문 생성
            file_context = ""
            if selected_files:
                file_info = []
                for snippet in selected_files[:3]:  # 최대 3개 파일
                    file_path = snippet["metadata"].get("file_path", "")
                    content_preview = snippet["content"][:300]
                    file_info.append(f"파일: {file_path}\n내용: {content_preview}...")
                file_context = "\n\n".join(file_info)

            try:
                question = await self._generate_single_tech_stack_question(tech, file_context, state)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"[QUESTION_GEN] 기술 스택 질문 생성 실패: {e}")
                continue

        return questions

    async def _generate_architecture_questions_with_files(
        self,
        state: "QuestionState",
        count: int,
        question_index: int,
    ) -> List[Dict[str, Any]]:
        """파일 선택 다양성을 고려한 아키텍처 질문 생성"""

        if not state.code_snippets:
            print("[QUESTION_GEN] 코드 스니펫이 없어서 아키텍처 질문 생성을 건너뜁니다.")
            return []

        # 질문 인덱스에 따라 다른 파일 세트 선택
        all_snippets = sorted(state.code_snippets, key=lambda s: s["metadata"].get("importance", "low"), reverse=True)
        selected_files = self.file_helpers._get_files_for_question_index(all_snippets, question_index)

        questions = []
        for i in range(count):
            try:
                # 선택된 파일들을 기반으로 아키텍처 분석
                architecture_context = self._analyze_architecture_patterns(selected_files)
                question = await self._generate_single_architecture_question(architecture_context, state)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"[QUESTION_GEN] 아키텍처 질문 생성 실패: {e}")
                continue

        return questions

    async def _generate_single_code_analysis_question(
        self,
        snippet: Dict[str, Any],
        state: "QuestionState",
    ) -> Dict[str, Any]:
        """단일 코드 분석 질문 생성"""

        from app.core.ai_service import ai_service

        extracted_elements = snippet["metadata"].get("extracted_elements", {})
        file_type = snippet["metadata"].get("file_type", "general")
        complexity = snippet["metadata"].get("complexity", 1.0)
        file_path = snippet["metadata"].get("file_path", "")

        # 기존 질문 생성 로직 사용
        context_info = []
        if extracted_elements.get("classes"):
            context_info.append(f"클래스: {', '.join(extracted_elements['classes'][:3])}")
        if extracted_elements.get("functions"):
            context_info.append(f"주요 함수: {', '.join(extracted_elements['functions'][:3])}")
        if extracted_elements.get("imports"):
            context_info.append(f"사용 라이브러리: {', '.join(extracted_elements['imports'][:2])}")

        context_str = " | ".join(context_info) if context_info else "기본 코드 구조"

        # 파일 유형별 질문 스타일 조정
        # [다양성 확보] 파일 유형별 다양한 관점(Focus Angle) 정의
        focus_options = {
            "controller": [
                "HTTP 요청 처리 및 라우팅 전략",
                "입력 데이터 유효성 검사 및 에러 핸들링",
                "API 설계 원칙 (RESTful, GraphQL 등)",
                "보안 고려사항 (인증, 권한 부여)",
            ],
            "service": [
                "핵심 비즈니스 로직 구현 방식",
                "트랜잭션 관리 및 데이터 일관성",
                "서비스 계층의 의존성 주입 및 결합도",
                "예외 처리 및 로깅 전략",
            ],
            "model": [
                "데이터 모델링 및 스키마 설계",
                "ORM 사용 방식 및 쿼리 최적화",
                "데이터 무결성 보장 방법",
                "모델 간의 관계 설정 및 연관 데이터 처리",
            ],
            "configuration": [
                "환경별 설정 관리 전략",
                "민감 정보(Secrets) 처리 방식",
                "애플리케이션 초기화 및 구성 프로세스",
                "외부 의존성 설정 방법",
            ],
            "utils": [
                "유틸리티 함수의 재사용성 및 순수성",
                "엣지 케이스 처리 및 견고성",
                "성능 최적화 및 알고리즘 효율성",
                "테스트 용이성 및 모듈화",
            ],
            "frontend": [
                "컴포넌트 구조 및 상태 관리",
                "렌더링 성능 최적화",
                "사용자 경험(UX) 및 인터랙션 처리",
                "비동기 데이터 통신 및 에러 처리",
            ],
        }

        # 랜덤하게 관점 선택하여 다양성 확보
        base_options = focus_options.get(
            file_type,
            [
                "코드 구조 및 설계 패턴",
                "유지보수성 및 확장성",
                "에러 처리 및 예외 상황 대응",
                "성능 최적화 및 리소스 관리",
            ],
        )
        selected_focus = random.choice(base_options)
        question_focus = f"{selected_focus} (이 관점을 중점적으로)"

        # 파일별 맞춤 프롬프트 생성
        if file_path.endswith("package.json"):
            prompt = f"""
다음은 실제 프로젝트의 package.json 파일입니다. 이 파일의 구체적인 내용을 바탕으로 기술면접 질문을 생성해주세요.

=== package.json 내용 ===
```json
{snippet["content"][:1500]}
```

=== 출력 형식 ===
1) 첫 줄: 핵심 질문 한 문장(헤드라인)
2) 필요할 때만 아래 선택 섹션 추가
   - **상황:**
   - **요구사항:**
   - **평가 포인트:**

=== 생성 요구사항 ===
- 실제 dependencies/devDependencies, scripts, 버전/설정값을 직접 언급
- 같은 문장/섹션 반복 금지
- HTML 태그(<div>, <strong> 등) 출력 금지
- 장황한 설명보다 간결하고 면접 친화적인 문장 우선
"""
        else:
            # Graph RAG Flow Context Injection
            flow_section = ""
            if state.flow_context:
                flow_section = f"\n{state.flow_context}\n"

            prompt = f"""
다음은 실제 프로젝트의 {file_type} 파일입니다. 이 파일의 구체적인 내용을 바탕으로 기술면접 질문을 생성해주세요.

=== 파일 정보 ===
경로: {file_path}
언어: {snippet["metadata"].get("language", "unknown")}
파일 유형: {file_type}
복잡도: {complexity:.1f}/10
{flow_section}
=== 실제 코드 내용 ===
```{snippet["metadata"].get("language", "")}
{snippet["content"][:2000]}
```

=== 질문 생성 지침 ===
1. 첫 줄에 핵심 질문 한 문장(헤드라인)만 먼저 출력하세요.
2. 필요한 경우에만 아래 섹션을 선택적으로 추가하세요:
   - **상황:**
   - **요구사항:**
   - **평가 포인트:**
3. 위 코드의 실제 함수명/변수명/클래스명과 로직을 직접 참조하세요.
4. {question_focus} 관점과 {state.difficulty_level} 난이도를 유지하세요.
5. 같은 문장/섹션 반복 금지, HTML 태그 출력 금지.
6. 'Execution Flow Context'가 있다면 파일의 역할을 간결히 반영하세요.
"""

        print(f"[QUESTION_GEN] ========== 코드 분석 질문 생성 상세 로그 ==========\n대상 파일: {file_path}\n파일 유형: {file_type}")

        # Gemini 기반 질문 생성
        try:
            ai_response = await ai_service.generate_analysis(
                prompt=prompt,
                provider=AIProvider.GEMINI_FLASH,
                api_keys=self.api_keys,
            )

            # AI 응답 null 체크 및 fallback 처리
            if ai_response and "content" in ai_response and ai_response["content"]:
                ai_question = ai_response["content"].strip()
                if ai_question:  # 빈 응답이 아닌 경우
                    print(f"[QUESTION_GEN] Gemini 코드분석 질문 생성 성공: {ai_question[:100]}...")
                else:
                    raise ValueError("AI 응답이 비어있음")
            else:
                raise ValueError("AI 응답이 None이거나 content가 없음")

        except Exception as e:
            print(f"[QUESTION_GEN] Gemini 코드분석 질문 생성 실패: {e}, fallback 질문 사용")
            # Fallback 질문 생성
            ai_question = self.ai_caller._generate_fallback_code_question(snippet, state)

        return {
            "id": f"code_analysis_{random.randint(1000, 9999)}",
            "type": "code_analysis",
            "question": ai_question,
            "code_snippet": {
                "content": snippet["content"][:800] + "..." if len(snippet["content"]) > 800 else snippet["content"],
                "language": snippet["metadata"].get("language", "unknown"),
                "file_path": file_path,
                "complexity": complexity,
                "has_real_content": True,
                "file_type": file_type,
                "extracted_elements": extracted_elements,
            },
            "difficulty": state.difficulty_level,
            "time_estimate": self._estimate_time(complexity),
            "generated_by": "AI",
            "source_file": file_path,
            "importance": snippet["metadata"].get("importance", "medium"),
            "file_type": file_type,
            "context": f"파일: {file_path} | 유형: {file_type} | 복잡도: {complexity:.1f}/10",
        }

    async def _generate_single_tech_stack_question(
        self,
        tech: str,
        file_context: str,
        state: "QuestionState",
    ) -> Dict[str, Any]:
        """단일 기술 스택 질문 생성"""

        from app.core.ai_service import ai_service

        prompt = f"""
다음은 실제 프로젝트에서 사용되고 있는 {tech} 기술입니다.

=== 프로젝트 파일 내용 ===
{file_context}

=== 출력 형식 ===
1) 첫 줄: 핵심 질문 한 문장(헤드라인)
2) 필요할 때만 아래 선택 섹션 추가
   - **상황:**
   - **요구사항:**
   - **평가 포인트:**

=== 생성 요구사항 ===
- 실제 파일에서 확인되는 {tech} 관련 코드/설정 직접 참조
- {state.difficulty_level} 난이도 유지
- 같은 문장/섹션 반복 금지
- HTML 태그 출력 금지, 과도한 장문 설명 금지
"""

        print(f"[QUESTION_GEN] ========== 기술 스택 질문 생성: {tech} ==========\n파일 컨텍스트 길이: {len(file_context)} 문자")

        try:
            ai_response = await ai_service.generate_analysis(prompt, api_keys=self.api_keys)

            # AI 응답 null 체크 및 fallback 처리
            if ai_response and "content" in ai_response and ai_response["content"]:
                ai_question = ai_response["content"].strip()
                if ai_question:  # 빈 응답이 아닌 경우
                    print(f"[QUESTION_GEN] {tech} 기술스택 질문 생성 성공")
                else:
                    raise ValueError("AI 응답이 비어있음")
            else:
                raise ValueError("AI 응답이 None이거나 content가 없음")

        except Exception as e:
            print(f"[QUESTION_GEN] Gemini 질문 생성 실패: {e}, fallback 질문 사용")
            # Fallback 질문 생성
            ai_question = f"이 프로젝트에서 {tech} 기술을 사용한 이유와 구현 방식에 대해 설명해주세요. 특히 다른 기술 대비 장점과 프로젝트에 적합한 이유를 중심으로 답변해주세요."

        return {
            "id": f"tech_stack_{random.randint(1000, 9999)}",
            "type": "tech_stack",
            "question": ai_question,
            "technology": tech,
            "difficulty": state.difficulty_level,
            "time_estimate": "7-10분",
            "generated_by": "AI",
            "context": f"{tech} 기술 스택 질문",
        }

    def _analyze_architecture_patterns(self, selected_files: List[Dict]) -> str:
        """선택된 파일들의 아키텍처 패턴 분석"""

        patterns = []
        technologies = set()
        file_types = set()

        for snippet in selected_files:
            # 기술 스택 수집
            language = snippet["metadata"].get("language", "")
            if language:
                technologies.add(language)

            # 파일 유형 수집
            file_type = snippet["metadata"].get("file_type", "")
            if file_type:
                file_types.add(file_type)

            # 파일 경로에서 패턴 추론
            file_path = snippet["metadata"].get("file_path", "")
            if "controller" in file_path.lower():
                patterns.append("MVC Controller 패턴")
            elif "service" in file_path.lower():
                patterns.append("Service Layer 패턴")
            elif "model" in file_path.lower():
                patterns.append("Domain Model 패턴")
            elif "component" in file_path.lower():
                patterns.append("Component 패턴")

        # 아키텍처 컨텍스트 생성
        context_parts = []
        if technologies:
            context_parts.append(f"사용 기술: {', '.join(sorted(technologies))}")
        if file_types:
            context_parts.append(f"파일 유형: {', '.join(sorted(file_types))}")
        if patterns:
            context_parts.append(f"감지된 패턴: {', '.join(patterns)}")

        return " | ".join(context_parts) if context_parts else "기본 프로젝트 구조"

    async def _generate_single_architecture_question(
        self,
        architecture_context: str,
        state: "QuestionState",
    ) -> Dict[str, Any]:
        """단일 아키텍처 질문 생성"""

        from app.core.ai_service import ai_service

        prompt = f"""
다음은 실제 프로젝트의 아키텍처 분석 결과입니다.

=== 아키텍처 컨텍스트 ===
{architecture_context}

=== 출력 형식 ===
1) 첫 줄: 핵심 질문 한 문장(헤드라인)
2) 필요할 때만 아래 선택 섹션 추가
   - **상황:**
   - **요구사항:**
   - **평가 포인트:**

=== 생성 요구사항 ===
- 실제 아키텍처 패턴/트레이드오프를 반영
- {state.difficulty_level} 난이도 유지
- 같은 문장/섹션 반복 금지
- HTML 태그 출력 금지, 장황한 서술 지양
"""

        print(f"[QUESTION_GEN] ========== 아키텍처 질문 생성 ==========\n컨텍스트: {architecture_context}")

        try:
            ai_response = await ai_service.generate_analysis(prompt, api_keys=self.api_keys)

            # AI 응답 null 체크 및 fallback 처리
            if ai_response and "content" in ai_response and ai_response["content"]:
                ai_question = ai_response["content"].strip()
                if ai_question:  # 빈 응답이 아닌 경우
                    print(f"[QUESTION_GEN] 아키텍처 질문 생성 성공")
                else:
                    raise ValueError("AI 응답이 비어있음")
            else:
                raise ValueError("AI 응답이 None이거나 content가 없음")

        except Exception as e:
            print(f"[QUESTION_GEN] Gemini 아키텍처 질문 생성 실패: {e}, fallback 질문 사용")
            # Fallback 질문 생성
            ai_question = "이 프로젝트의 전체적인 아키텍처 설계와 주요 구성 요소들의 역할에 대해 설명해주세요. 특히 확장성과 유지보수성을 고려한 설계 결정이 있다면 함께 설명해주세요."

        return {
            "id": f"architecture_{random.randint(1000, 9999)}",
            "type": "architecture",
            "question": ai_question,
            "difficulty": state.difficulty_level,
            "context": architecture_context,
            "time_estimate": "10-15분",
            "generated_by": "AI",
        }

    async def _generate_design_pattern_questions(
        self,
        state: "QuestionState",
        count: int,
    ) -> List[Dict[str, Any]]:
        """디자인 패턴 질문 생성"""

        questions = []

        # 분석 데이터에서 감지된 패턴 사용
        detected_patterns = []
        if state.analysis_data and "metadata" in state.analysis_data:
            # 기술 스택 기반으로 실제 패턴 추론
            tech_stack_str = state.analysis_data["metadata"].get("tech_stack", "{}")
            try:
                tech_stack_dict = json.loads(tech_stack_str)
                # 기술 스택에 따른 패턴 추론
                for tech in tech_stack_dict.keys():
                    tech_lower = tech.lower()
                    if tech_lower in ["react", "vue", "angular"]:
                        detected_patterns.extend(["Component", "Observer", "State Management"])
                    elif tech_lower in ["django", "spring", "express"]:
                        detected_patterns.extend(["MVC", "Factory", "Dependency Injection"])
                    elif tech_lower in ["java", "kotlin"]:
                        detected_patterns.extend(["Singleton", "Factory", "Builder"])
                    elif tech_lower in ["python", "flask"]:
                        detected_patterns.extend(["Decorator", "Factory", "Observer"])
                    elif tech_lower in ["javascript", "typescript"]:
                        detected_patterns.extend(["Module", "Prototype", "Factory"])
            except Exception:
                pass

        # 패턴이 감지되지 않은 경우 빈 리스트 반환
        if not detected_patterns:
            return []

        for i in range(count):
            pattern = random.choice(detected_patterns)
            template = random.choice(templates)

            question = {
                "id": f"design_pattern_{i}_{random.randint(1000, 9999)}",
                "type": "design_patterns",
                "question": template.format(pattern=pattern),
                "pattern": pattern,
                "difficulty": state.difficulty_level,
                "time_estimate": "5-8분",
            }
            questions.append(question)

        return questions

    async def _generate_problem_solving_questions(
        self,
        state: "QuestionState",
        count: int,
    ) -> List[Dict[str, Any]]:
        """문제 해결 질문 생성"""

        questions = []

        for i in range(count):
            template = random.choice(templates)

            question = {
                "id": f"problem_solving_{i}_{random.randint(1000, 9999)}",
                "type": "problem_solving",
                "question": template,
                "difficulty": state.difficulty_level,
                "time_estimate": "10-20분",
            }
            questions.append(question)

        return questions

    async def _generate_best_practice_questions(
        self,
        state: "QuestionState",
        count: int,
    ) -> List[Dict[str, Any]]:
        """베스트 프랙티스 질문 생성"""

        questions = []

        for i in range(count):
            template = random.choice(templates)

            question = {
                "id": f"best_practices_{i}_{random.randint(1000, 9999)}",
                "type": "best_practices",
                "question": template,
                "difficulty": state.difficulty_level,
                "time_estimate": "5-10분",
            }
            questions.append(question)

        return questions

    def _generate_answer_points(self, template: str, snippet: Dict[str, Any]) -> List[str]:
        """예상 답변 포인트 생성"""

        points = []

        if "복잡도" in template:
            complexity = snippet["metadata"].get("complexity", 1.0)
            if complexity > 5:
                points.extend([
                    "시간 복잡도 분석",
                    "중첩 구조 개선 방안",
                    "알고리즘 최적화",
                ])
            else:
                points.extend([
                    "기본적인 복잡도 분석",
                    "코드 가독성 개선",
                ])

        elif "버그" in template or "문제점" in template:
            points.extend([
                "Null 체크 및 예외 처리",
                "메모리 누수 가능성",
                "동시성 문제",
                "입력 검증",
            ])

        elif "리팩토링" in template:
            points.extend([
                "함수 분리",
                "변수명 개선",
                "중복 코드 제거",
                "디자인 패턴 적용",
            ])

        elif "테스트" in template:
            points.extend([
                "경계값 테스트",
                "예외 상황 테스트",
                "Mock 객체 사용",
                "통합 테스트",
            ])

        return points
