"""
Question Template Manager

템플릿 기반 질문 생성을 분리한 모듈
"""

import random
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.question_generator import QuestionState


class QuestionTemplateManager:
    """템플릿 기반 질문 생성 및 관리"""

    async def _generate_template_questions(
        self,
        state: "QuestionState",
        question_type: Any,
        count: int,
    ) -> List[Dict[str, Any]]:
        """템플릿 기반 질문 생성 (타입별/최후 보장 메커니즘 포함)"""

        if isinstance(question_type, list):
            question_types = question_type
            print(f"[QUESTION_GEN] 템플릿 기반 질문 생성 시작 (타입: {question_types}, 개수: {count})")

            questions = []
            questions_per_type = max(1, count // len(question_types))

            for q_type in question_types:
                type_count = min(questions_per_type, count - len(questions))
                if type_count <= 0:
                    break

                try:
                    if q_type == "code_analysis":
                        template_questions = self._get_code_analysis_templates(state, type_count)
                    elif q_type == "tech_stack":
                        template_questions = self._get_tech_stack_templates(state, type_count)
                    elif q_type == "architecture":
                        template_questions = self._get_architecture_templates(state, type_count)
                    else:
                        template_questions = self._get_general_templates(state, q_type, type_count)

                    questions.extend(template_questions)
                    print(f"[QUESTION_GEN] {q_type} 템플릿 질문 {len(template_questions)}개 생성")

                except Exception as e:
                    print(f"[QUESTION_GEN] {q_type} 템플릿 질문 생성 실패: {e}")

            return questions[:count]

        print(f"[QUESTION_GEN] 템플릿 질문 생성 시작: {question_type} 타입, {count}개")

        template_questions = []

        # 기본 템플릿 질문들
        question_templates = {
            "code_analysis": [
                "이 프로젝트의 핵심 알고리즘이나 비즈니스 로직에 대해 설명해주세요.",
                "코드의 복잡한 부분이나 도전적인 구현 사항에 대해 설명해주세요.",
                "성능 최적화를 위해 어떤 방법을 사용했는지 설명해주세요.",
                "코드 리뷰 시 주의 깊게 봐야 할 부분과 그 이유를 설명해주세요.",
                "이 프로젝트에서 가장 중요한 모듈이나 컴포넌트에 대해 설명해주세요.",
            ],
            "tech_stack": [
                "이 프로젝트에서 사용한 주요 기술들의 장단점을 설명해주세요.",
                "기술 스택 선택 시 고려했던 요소들과 그 이유를 설명해주세요.",
                "다른 대안 기술들과 비교했을 때 현재 선택의 이유를 설명해주세요.",
                "프로젝트 진행 중 기술 스택 관련해서 어려움이 있었다면 어떻게 해결했는지 설명해주세요.",
                "향후 기술 스택 업그레이드나 변경 계획이 있다면 설명해주세요.",
            ],
            "architecture": [
                "이 프로젝트의 전체 아키텍처 패턴과 그 선택 이유를 설명해주세요.",
                "확장성을 고려한 설계 부분에 대해 설명해주세요.",
                "모듈 간의 의존성 관리는 어떻게 하고 있는지 설명해주세요.",
                "데이터 흐름과 상태 관리 방식에 대해 설명해주세요.",
                "시스템의 병목점이나 성능 이슈가 예상되는 부분과 대응책을 설명해주세요.",
            ],
        }

        # 기본 템플릿이 없는 경우 일반적인 질문 사용
        templates = question_templates.get(
            question_type,
            [
                f"이 프로젝트의 {question_type} 관련 주요 특징에 대해 설명해주세요.",
                f"{question_type}와 관련된 구현상의 도전과제와 해결방안을 설명해주세요.",
                f"프로젝트에서 {question_type} 측면에서 가장 중요한 부분은 무엇인지 설명해주세요.",
            ],
        )

        for i in range(count):
            template_index = i % len(templates)
            question_id = f"template_{question_type}_{i}"

            template_question = {
                "id": question_id,
                "type": question_type,
                "question": templates[template_index],
                "difficulty": state.difficulty_level,
                "context": "프로젝트 일반 분석",
                "time_estimate": "5분",
                "technology": "General",
                "pattern": "template",
                "metadata": {
                    "is_template": True,
                    "generation_method": "template",
                    "template_index": template_index,
                },
            }

            template_questions.append(template_question)
            print(f"[QUESTION_GEN] 템플릿 질문 생성: {templates[template_index][:50]}...")

        print(f"[QUESTION_GEN] 템플릿 질문 {len(template_questions)}개 생성 완료")
        return template_questions

    async def _generate_general_template_questions(
        self,
        state: "QuestionState",
        count: int,
    ) -> List[Dict[str, Any]]:
        """일반적인 템플릿 기반 질문 생성"""

        print(f"[QUESTION_GEN] 일반 템플릿 질문 생성: {count}개")

        questions = []
        general_templates = [
            ("tech_stack", "이 프로젝트에서 사용된 주요 기술 스택의 장단점과 선택 이유를 설명해주세요."),
            ("architecture", "이 프로젝트의 전체적인 아키텍처 구조와 주요 컴포넌트들의 역할을 설명해주세요."),
            ("code_analysis", "프로젝트의 코드 품질과 유지보수성을 높이기 위한 개선 방안을 제시해주세요."),
            ("best_practices", "이 프로젝트에서 적용된 개발 베스트 프랙티스와 그 효과를 설명해주세요."),
            ("problem_solving", "프로젝트 개발 과정에서 발생할 수 있는 주요 문제점들과 해결 방안을 설명해주세요."),
        ]

        for i in range(count):
            template_type, template_text = general_templates[i % len(general_templates)]

            question = {
                "id": f"general_template_{i}_{random.randint(1000, 9999)}",
                "type": template_type,
                "question": template_text,
                "difficulty": state.difficulty_level,
                "time_estimate": "5분",
                "generated_by": "general_template",
                "context": "일반 템플릿 기반 질문",
            }

            questions.append(question)

        return questions

    def _get_code_analysis_templates(self, state: "QuestionState", count: int) -> List[Dict[str, Any]]:
        """코드 분석 템플릿 질문들"""

        templates = [
            "프로젝트의 코드 구조와 모듈화 방식을 분석하고, 개선할 수 있는 부분을 제시해주세요.",
            "코드의 가독성과 유지보수성을 높이기 위해 적용할 수 있는 리팩토링 기법들을 설명해주세요.",
            "프로젝트에서 사용된 디자인 패턴들을 식별하고, 그 효과와 적용 이유를 설명해주세요.",
            "코드 품질 측정 지표들을 활용하여 이 프로젝트의 코드 품질을 평가해주세요.",
        ]

        questions = []
        for i in range(min(count, len(templates))):
            question = {
                "id": f"code_template_{i}_{random.randint(1000, 9999)}",
                "type": "code_analysis",
                "question": templates[i],
                "difficulty": state.difficulty_level,
                "time_estimate": "7분",
                "generated_by": "code_template",
            }
            questions.append(question)

        return questions

    def _get_tech_stack_templates(self, state: "QuestionState", count: int) -> List[Dict[str, Any]]:
        """기술 스택 템플릿 질문들"""

        templates = [
            "프로젝트에서 사용된 주요 프레임워크와 라이브러리들의 선택 기준과 장점을 설명해주세요.",
            "현재 기술 스택의 확장성과 성능 측면에서의 장단점을 분석해주세요.",
            "프로젝트의 기술 스택을 다른 대안들과 비교하여 평가해주세요.",
            "최신 기술 트렌드를 고려하여 현재 기술 스택의 미래 지향성을 평가해주세요.",
        ]

        questions = []
        for i in range(min(count, len(templates))):
            question = {
                "id": f"tech_template_{i}_{random.randint(1000, 9999)}",
                "type": "tech_stack",
                "question": templates[i],
                "difficulty": state.difficulty_level,
                "time_estimate": "6분",
                "generated_by": "tech_template",
            }
            questions.append(question)

        return questions

    def _get_architecture_templates(self, state: "QuestionState", count: int) -> List[Dict[str, Any]]:
        """아키텍처 템플릿 질문들"""

        templates = [
            "프로젝트의 전체 아키텍처 구조를 설명하고, 각 계층의 역할과 책임을 설명해주세요.",
            "시스템의 확장성과 가용성을 고려한 아키텍처 설계 원칙들을 설명해주세요.",
            "마이크로서비스 vs 모노리스 관점에서 현재 아키텍처의 장단점을 분석해주세요.",
            "보안과 성능을 고려한 아키텍처 최적화 방안을 제시해주세요.",
        ]

        questions = []
        for i in range(min(count, len(templates))):
            question = {
                "id": f"arch_template_{i}_{random.randint(1000, 9999)}",
                "type": "architecture",
                "question": templates[i],
                "difficulty": state.difficulty_level,
                "time_estimate": "8분",
                "generated_by": "architecture_template",
            }
            questions.append(question)

        return questions

    def _get_general_templates(
        self,
        state: "QuestionState",
        question_type: str,
        count: int,
    ) -> List[Dict[str, Any]]:
        """기타 질문 타입들의 템플릿"""

        templates = {
            "design_patterns": [
                "프로젝트에서 적용할 수 있는 디자인 패턴들과 그 활용 방안을 설명해주세요."
            ],
            "problem_solving": [
                "프로젝트 개발 과정에서 발생할 수 있는 기술적 문제들과 해결 전략을 설명해주세요."
            ],
            "best_practices": [
                "코딩 표준과 개발 베스트 프랙티스가 프로젝트에 미치는 영향을 설명해주세요."
            ],
        }

        question_templates = templates.get(question_type, ["프로젝트의 특성을 분석하고 개선 방안을 제시해주세요."])

        questions = []
        for i in range(min(count, len(question_templates))):
            question = {
                "id": f"{question_type}_template_{i}_{random.randint(1000, 9999)}",
                "type": question_type,
                "question": question_templates[i],
                "difficulty": state.difficulty_level,
                "time_estimate": "6분",
                "generated_by": f"{question_type}_template",
            }
            questions.append(question)

        return questions
