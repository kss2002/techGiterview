"""
Question AI Caller

AI 호출 및 fallback 질문 생성을 분리한 모듈
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.question_file_helpers import QuestionFileHelpers
    from app.agents.question_generator import QuestionState
    from app.core.ai_service import AIProvider


class QuestionAICaller:
    """AI 호출 및 fallback 질문 생성을 담당"""

    def __init__(self, ai_service, llm):
        self.ai_service = ai_service
        self.llm = llm
        self.api_keys: Dict[str, str] = {}
        self.file_helpers: Optional["QuestionFileHelpers"] = None

    def set_api_keys(self, api_keys: Optional[Dict[str, str]]) -> None:
        self.api_keys = api_keys or {}

    def set_file_helpers(self, file_helpers: "QuestionFileHelpers") -> None:
        self.file_helpers = file_helpers

    async def _call_ai_with_retry(
        self,
        ai_function,
        prompt: str,
        max_retries: int = 3,
        provider: Optional["AIProvider"] = None,
    ) -> Dict[str, Any]:
        """AI 서비스 호출에 재시도 메커니즘 추가"""

        last_exception = None

        for attempt in range(max_retries):
            try:
                print(f"[QUESTION_GEN] AI 호출 시도 {attempt + 1}/{max_retries}")

                # provider가 지정되어 있으면 해당 provider로 호출
                if provider:
                    result = await ai_function(prompt=prompt, provider=provider, api_keys=self.api_keys)
                else:
                    result = await ai_function(prompt, api_keys=self.api_keys)

                # 응답 검증
                if result and "content" in result and result["content"].strip():
                    print(f"[QUESTION_GEN] AI 호출 성공 (시도 {attempt + 1})")
                    return result
                else:
                    print(f"[QUESTION_GEN] AI 응답이 비어있음 (시도 {attempt + 1})")
                    last_exception = Exception("Empty AI response")

            except Exception as e:
                last_exception = e
                print(f"[QUESTION_GEN] AI 호출 실패 (시도 {attempt + 1}): {str(e)}")

                # 마지막 시도가 아닌 경우 잠시 대기
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초...
                    print(f"[QUESTION_GEN] {wait_time}초 후 재시도...")
                    await asyncio.sleep(wait_time)

        # 모든 재시도가 실패한 경우
        print(f"[QUESTION_GEN] AI 호출 최종 실패 - 모든 재시도 완료")
        if last_exception:
            raise last_exception
        else:
            raise Exception("All AI call attempts failed")

    async def _generate_fallback_questions(
        self,
        state: "QuestionState",
        question_type: str,
        count: int,
        question_index: int,
    ) -> List[Dict[str, Any]]:
        """AI 생성 실패 시 사용할 fallback 질문 생성"""

        print(f"[QUESTION_GEN] fallback 질문 생성 시작: {question_type} 타입, {count}개")

        fallback_questions = []

        # 기본 메타데이터 추출
        repo_name = "프로젝트"
        tech_stack = []

        if state.analysis_data and "metadata" in state.analysis_data:
            metadata = state.analysis_data["metadata"]
            repo_name = metadata.get("repo_name", "프로젝트")

            # 기술 스택 추출
            try:
                tech_stack_str = metadata.get("tech_stack", "{}")
                tech_stack_dict = json.loads(tech_stack_str) if isinstance(tech_stack_str, str) else tech_stack_str
                if isinstance(tech_stack_dict, dict):
                    for category, techs in tech_stack_dict.items():
                        if isinstance(techs, list):
                            tech_stack.extend(techs)
                        elif isinstance(techs, str):
                            tech_stack.append(techs)
            except Exception:
                tech_stack = ["Python", "JavaScript", "React", "FastAPI"]

        # 선택된 파일 정보 가져오기
        selected_file_info = None
        if state.code_snippets:
            try:
                if self.file_helpers:
                    selected_files = self.file_helpers._get_files_for_question_index(
                        state.code_snippets, question_index
                    )
                else:
                    selected_files = [state.code_snippets[0]] if state.code_snippets else []
                if selected_files:
                    selected_file_info = selected_files[0]
            except Exception:
                selected_file_info = state.code_snippets[0] if state.code_snippets else None

        # 타입별 fallback 질문 생성
        for i in range(count):
            question_id = f"fallback_{question_type}_{question_index}_{i}"

            if question_type == "code_analysis":
                if selected_file_info:
                    file_path = selected_file_info["metadata"].get("file_path", "unknown")
                    question_text = f"{file_path} 파일의 주요 기능과 구조에 대해 설명해주세요."
                else:
                    question_text = f"{repo_name}의 핵심 코드 구조와 주요 컴포넌트에 대해 설명해주세요."

            elif question_type == "tech_stack":
                if tech_stack:
                    tech = tech_stack[i % len(tech_stack)]
                    question_text = f"이 프로젝트에서 {tech}를 선택한 이유와 어떻게 활용했는지 설명해주세요."
                else:
                    question_text = f"{repo_name}에서 사용한 주요 기술 스택과 그 선택 이유를 설명해주세요."

            elif question_type == "architecture":
                question_text = f"{repo_name}의 전체 아키텍처 설계 패턴과 주요 설계 결정사항에 대해 설명해주세요."

            else:
                question_text = f"{repo_name}의 {question_type} 관련하여 중요한 구현 결정사항과 그 이유를 설명해주세요."

            fallback_question = {
                "id": question_id,
                "type": question_type,
                "question": question_text,
                "difficulty": state.difficulty_level,
                "context": f"{repo_name} 프로젝트 분석",
                "time_estimate": "5분",
                "technology": tech_stack[0] if tech_stack else "General",
                "pattern": "fallback",
                "metadata": {
                    "is_fallback": True,
                    "generation_method": "template",
                    "question_index": question_index,
                },
            }

            fallback_questions.append(fallback_question)
            print(f"[QUESTION_GEN] fallback 질문 생성: {question_text[:50]}...")

        print(f"[QUESTION_GEN] fallback 질문 {len(fallback_questions)}개 생성 완료")
        return fallback_questions

    def _generate_fallback_code_question(self, snippet: Dict[str, Any], state: "QuestionState") -> str:
        """Gemini 실패 시 사용할 fallback 코드 질문 생성"""

        extracted_elements = snippet["metadata"].get("extracted_elements", {})
        file_path = snippet["metadata"].get("file_path", "")
        file_type = snippet["metadata"].get("file_type", "general")

        # 파일 유형별 기본 질문 템플맿
        if file_path.endswith("package.json"):
            return "이 package.json 파일에서 사용된 dependencies를 보고, 주요 라이브러리들의 역할과 선택 이유를 설명해주세요."
        elif file_path.endswith(".py"):
            if extracted_elements.get("functions"):
                func_name = extracted_elements["functions"][0]
                return f"이 Python 코드에서 `{func_name}` 함수의 주요 기능과 구현 방식을 설명해주세요."
            else:
                return "이 Python 코드의 전체적인 구조와 주요 기능을 설명해주세요."
        elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            if extracted_elements.get("functions"):
                func_name = extracted_elements["functions"][0]
                return f"이 JavaScript/TypeScript 코드에서 `{func_name}` 함수의 역할과 작동 원리를 설명해주세요."
            else:
                return "이 JavaScript/TypeScript 코드의 구조와 주요 기능을 설명해주세요."
        else:
            return f"이 {file_type} 코드의 주요 기능과 설계 의도를 설명해주세요."
