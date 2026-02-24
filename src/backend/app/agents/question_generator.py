"""
Question Generator Agent

GitHub 저장소 분석 결과를 바탕으로 기술면접 질문을 생성하는 LangGraph 에이전트
"""

import json
import random
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.ai_service import ai_service, AIProvider
from app.core.gemini_client import get_gemini_llm
from app.services.flow_graph_analyzer import FlowGraphAnalyzer, NodeType
from app.services.flow_analysis_service import FlowAnalysisService
from app.agents.question_ai_caller import QuestionAICaller
from app.agents.question_file_helpers import QuestionFileHelpers
from app.agents.question_templates import QuestionTemplateManager
from app.agents.question_strategies import QuestionStrategies

# from app.services.vector_db import VectorDBService


@dataclass
class QuestionState:
    """질문 생성 상태를 관리하는 데이터 클래스"""
    repo_url: str
    analysis_data: Optional[Dict[str, Any]] = None
    code_snippets: Optional[List[Dict[str, Any]]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    difficulty_level: str = "medium"  # easy, medium, hard
    question_types: Optional[List[str]] = None
    error: Optional[str] = None
    flow_context: Optional[str] = None  # Graph RAG Context


class QuestionGenerator:
    """기술면접 질문 생성 에이전트"""
    
    def __init__(self):
        # self.vector_db = VectorDBService()
        
        # Google Gemini LLM 초기화
        self.llm = get_gemini_llm()
        self.ai_service = ai_service
        
        if self.llm:
            # Gemini에 맞는 설정 조정
            self.llm.temperature = 0.7  # 창의적인 질문 생성을 위해
            print("[QUESTION_GENERATOR] Google Gemini LLM initialized successfully")
        else:
            print("[QUESTION_GENERATOR] Warning: Gemini LLM not available, using template-based generation")
        
        # 더미 템플릿 제거 - 실제 파일 내용만으로 질문 생성
        
        # 난이도별 복잡도 범위
        self.complexity_ranges = {
            "easy": (1.0, 3.0),
            "medium": (3.0, 6.0), 
            "hard": (6.0, 10.0)
        }
        
        self.ai_caller = QuestionAICaller(self.ai_service, self.llm)
        self.file_helpers = QuestionFileHelpers()
        self.template_manager = QuestionTemplateManager()
        self.strategies = QuestionStrategies(self.ai_caller, self.file_helpers, self.template_manager)
        self.ai_caller.set_file_helpers(self.file_helpers)
        self.strategies.set_metadata_question_generator(self._generate_metadata_based_questions)
        self.strategies.set_estimate_question_time(self._estimate_question_time)

    def _extract_flow_context(self, code_snippets: List[Dict[str, Any]]) -> str:
        """코드 스니펫들로부터 실행 흐름 문맥 추출 (Graph RAG)"""
        try:
            # 1. 파일 내용 맵 준비
            file_map = {
                s["id"]: s["content"] 
                for s in code_snippets 
                if s["metadata"].get("has_real_content", False)
            }
            
            if not file_map:
                return ""
                
            # 2. 그래프 생성 및 흐름 분석
            analyzer = FlowGraphAnalyzer()
            graph = analyzer.build_graph(file_map)
            
            # 엔트리 포인트 식별
            entry_points = [n for n, d in graph.nodes(data=True) if d.get("type") == NodeType.ENTRY_POINT]
            if not entry_points:
                # 엔트리 포인트가 없으면 모든 로직 노드를 후보로
                entry_points = [n for n, d in graph.nodes(data=True) if d.get("type") == NodeType.LOGIC]
            
            if not entry_points:
                # 그래도 없으면 모든 노드를 후보로 (순환 방지를 위해 상위 5개만)
                entry_points = list(graph.nodes())[:5]

            service = FlowAnalysisService()
            flow_paths = service.extract_flow_paths(graph, entry_points, max_depth=5, max_branches=3)
            
            if not flow_paths:
                return ""
                
            # 3. 문맥 텍스트 생성
            context_parts = []
            context_parts.append("## Execution Flow Context")
            context_parts.append("The following execution paths represent the core logic flows detected in this codebase:")

            # 노드 타입 정보 추출
            node_types = {}
            for node, attrs in graph.nodes(data=True):
                 if "type" in attrs:
                     node_types[node] = attrs["type"]

            sorted_flows = sorted(flow_paths, key=len, reverse=True)[:3]

            for i, flow in enumerate(sorted_flows, 1):
                flow_str = f"\\n[Flow {i}]"
                for j, file_path in enumerate(flow):
                    type_info = ""
                    if file_path in node_types:
                        type_info = f" ({node_types[file_path].value})"
                    indent = "  " * j
                    if j == 0:
                        flow_str += f"\\n{indent}Step {j+1}: {file_path}{type_info} (Entry)"
                    else:
                        flow_str += f"\\n{indent}-> calls {file_path}{type_info}"
                context_parts.append(flow_str)
            
            context_parts.append("\\nUse these flows to understand how data moves from Entry Points through Services to Data Models within the question.")
            return "\\n".join(context_parts)
            
        except Exception as e:
            print(f"[QUESTION_GENERATOR] Flow context extraction failed: {e}")
            return ""

    def _remove_duplicates(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """유사도가 높은 중복 질문 제거"""
        if not questions:
            return []
            
        unique_questions = []
        
        # 질문 텍스트만 추출하여 비교
        for q in questions:
            q_text = q.get("question", "")
            if not q_text:
                continue
                
            is_duplicate = False
            
            for i, existing in enumerate(unique_questions):
                existing_text = existing.get("question", "")
                
                # 1. 완전 일치 확인
                if q_text == existing_text:
                    is_duplicate = True
                    break
                
                # 2. 유사도 확인 (SequenceMatcher)
                import difflib
                ratio = difflib.SequenceMatcher(None, q_text, existing_text).ratio()
                
                # 3. 같은 파일에 대한 유사 질문인지 확인 (context/source_file)
                # 파일이 같고 질문이 60% 이상 유사하면 중복
                same_file = False
                q_file = q.get("source_file", q.get("context", ""))
                exist_file = existing.get("source_file", existing.get("context", ""))
                if q_file and exist_file and q_file == exist_file:
                    if ratio > 0.6:
                        is_duplicate = True
                        print(f"[DEDUP] 같은 파일({q_file})에 대한 중복 질문 제거: (유사도 {ratio:.2f})")
                
                elif ratio > 0.7:  # 파일이 달라도 70% 이상 유사하면 중복
                    is_duplicate = True
                    print(f"[DEDUP] 유사한 질문 제거: (유사도 {ratio:.2f})")
                
                if is_duplicate:
                    # 더 긴 질문(상세한 질문)을 유지
                    if len(q_text) > len(existing_text):
                        unique_questions[i] = q
                    break
            
            if not is_duplicate:
                unique_questions.append(q)
                
        return unique_questions
    
    async def generate_questions(
        self, 
        repo_url: str, 
        difficulty_level: str = "medium",
        question_count: int = 9,
        question_types: Optional[List[str]] = None,
        analysis_data: Optional[Dict[str, Any]] = None,
        api_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """기술면접 질문 생성"""
        
        # API 키를 인스턴스 변수로 저장
        self.api_keys = api_keys or {}
        self.ai_caller.set_api_keys(self.api_keys)
        self.strategies.set_api_keys(self.api_keys)
        
        # 상태 초기화
        state = QuestionState(
            repo_url=repo_url,
            difficulty_level=difficulty_level,
            question_types=question_types or ["tech_stack", "architecture", "code_analysis"]  # 3가지 질문 타입 균등 분배
        )
        
        try:
            # 1. 분석 데이터 설정
            if analysis_data:
                # 직접 전달받은 분석 데이터 사용
                import json
                state.analysis_data = {
                    "metadata": {
                        "tech_stack": json.dumps(analysis_data.get("tech_stack", {})),
                        "complexity_score": analysis_data.get("complexity_score", 0.0),
                        "file_count": len(analysis_data.get("key_files", [])),
                        "repo_info": analysis_data.get("repo_info", {})
                    },
                    "analysis_text": analysis_data.get("summary", "")
                }
            else:
                # 분석 데이터가 없으면 에러 반환
                raise ValueError(f"저장소 분석 데이터가 제공되지 않았습니다: {repo_url}. 먼저 저장소를 분석해주세요.")
            
            # 2. 관련 코드 스니펫 조회 (key_files 우선 활용)
            state.code_snippets = []
            if analysis_data and "key_files" in analysis_data:
                print(f"[DEBUG] key_files 개수: {len(analysis_data['key_files'])}")
                # 분석 데이터에서 파일 정보 활용
                for file_info in analysis_data["key_files"][:15]:  # Graph RAG를 위해 더 많은 파일 로드 (8 -> 15)
                    file_path = file_info.get("path", "unknown")
                    file_content = file_info.get("content", "# File content not available")
                    
                    # 파일 확장자에 따른 언어 추론
                    language = self.file_helpers._infer_language_from_path(file_path)
                    
                    # 파일 내용이 실제로 존재하는지 확인 (더욱 관대한 검사)
                    has_real_content = (
                        file_content and 
                        file_content != "null" and
                        file_content.strip() != "" and
                        len(file_content.strip()) > 10 and  # 최소 10자 이상으로 대폭 완화
                        not file_content.startswith("# File content not available") and
                        not file_content.strip() == "File content not available"
                    )
                    
                    # 추가 검사: 설정 파일이나 문서 파일은 더욱 관대하게 처리
                    file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
                    is_config_or_doc = file_ext in ['json', 'yml', 'yaml', 'toml', 'md', 'rst', 'txt', 'cfg', 'ini']
                    
                    if is_config_or_doc and file_content and len(file_content.strip()) > 5:
                        has_real_content = True  # 설정/문서 파일은 5자 이상이면 유효
                    
                    # 파일 유형별 중요도 자동 설정
                    file_importance = self.file_helpers._determine_file_importance(file_path, file_content)
                    
                    snippet_data = {
                        "id": file_path,
                        "content": file_content,
                        "metadata": {
                            "language": language,
                            "file_path": file_path,
                            "complexity": self.file_helpers._estimate_code_complexity(file_content) if has_real_content else 1.0,
                            "has_real_content": has_real_content,
                            "content_unavailable_reason": file_info.get("content_unavailable_reason"),
                            "importance": file_importance,
                            "file_type": self.file_helpers._categorize_file_type(file_path),
                            "extracted_elements": self.file_helpers._extract_code_elements(file_content, language) if has_real_content else {}
                        }
                    }
                    
                    state.code_snippets.append(snippet_data)
                
                # [Graph RAG] 실행 흐름 문맥 추출
                state.flow_context = self._extract_flow_context(state.code_snippets)
                if state.flow_context:
                    print("[QUESTION_GEN] Graph RAG Flow Context Extracted")
            else:
                print(f"[DEBUG] key_files 없음. analysis_data 키들: {list(analysis_data.keys()) if analysis_data else 'None'}")
            
            # 3. 질문 생성 - 전체 파일 현황 로그 추가
            print(f"[QUESTION_GEN] ========== 질문 생성 시작 - 전체 현황 ==========")
            print(f"[QUESTION_GEN] 요청된 질문 개수: {question_count}")
            print(f"[QUESTION_GEN] 질문 타입: {state.question_types}")
            print(f"[QUESTION_GEN] 전체 파일 수: {len(state.code_snippets) if state.code_snippets else 0}")
            if state.code_snippets:
                real_content_count = sum(1 for s in state.code_snippets if s["metadata"].get("has_real_content", False))
                print(f"[QUESTION_GEN] 실제 내용이 있는 파일 수: {real_content_count}")
                print(f"[QUESTION_GEN] 파일별 상세 현황:")
                for i, snippet in enumerate(state.code_snippets[:10]):  # 최대 10개만 표시
                    file_path = snippet["metadata"].get("file_path", "unknown")
                    has_content = snippet["metadata"].get("has_real_content", False)
                    content_len = len(snippet["content"]) if snippet["content"] else 0
                    importance = snippet["metadata"].get("importance", "unknown")
                    print(f"[QUESTION_GEN]   {i+1}. {file_path} - 실제내용: {has_content} - 길이: {content_len} - 중요도: {importance}")
            print(f"[QUESTION_GEN] ========================================")
            
            state.questions = await self._generate_questions_by_type(state, question_count)
            
            # 질문 생성 완료 로그
            print(f"[QUESTION_GEN] ========== 질문 생성 최종 결과 ==========")
            print(f"[QUESTION_GEN] 생성된 총 질문 수: {len(state.questions)}")
            if state.questions:
                for i, q in enumerate(state.questions):
                    q_type = q.get("type", "unknown")
                    q_preview = q.get("question", "")[:100] + "..." if len(q.get("question", "")) > 100 else q.get("question", "")
                    source_file = q.get("source_file", q.get("context", "unknown"))
                    print(f"[QUESTION_GEN]   {i+1}. [{q_type}] {q_preview} (출처: {source_file})")
            print(f"[QUESTION_GEN] ==========================================")
            
            # 4. 결과 반환
            return {
                "success": True,
                "repo_url": repo_url,
                "difficulty": difficulty_level,
                "question_count": len(state.questions),
                "questions": state.questions,
                "analysis_context": self._extract_context_summary(state.analysis_data),
                "code_snippets_count": len(state.code_snippets) if state.code_snippets else 0
            }
            
        except Exception as e:
            state.error = str(e)
            return {
                "success": False,
                "error": state.error,
                "repo_url": repo_url,
                "questions": []
            }
    
    async def _get_relevant_code_snippets(self, state: QuestionState) -> List[Dict[str, Any]]:
        """관련 코드 스니펫 조회"""
        
        snippets = []
        
        # 난이도에 따른 복잡도 범위 설정
        min_complexity, max_complexity = self.complexity_ranges[state.difficulty_level]
        
        # 복잡도 기반 코드 조회
        complexity_snippets = await self.vector_db.get_code_by_complexity(
            min_complexity=min_complexity,
            max_complexity=max_complexity,
            limit=5
        )
        snippets.extend(complexity_snippets)
        
        # 기술 스택 기반 코드 검색
        if state.analysis_data and "metadata" in state.analysis_data:
            tech_stack_str = state.analysis_data["metadata"].get("tech_stack", "{}")
            try:
                tech_stack = json.loads(tech_stack_str)
                for tech in list(tech_stack.keys())[:3]:  # 주요 기술 3개
                    tech_snippets = await self.vector_db.search_similar_code(
                        query=tech,
                        limit=2
                    )
                    snippets.extend(tech_snippets)
            except:
                pass
        
        # 중복 제거
        seen_ids = set()
        unique_snippets = []
        for snippet in snippets:
            if snippet["id"] not in seen_ids:
                seen_ids.add(snippet["id"])
                unique_snippets.append(snippet)
        
        return unique_snippets[:8]  # 최대 8개 스니펫
    
    async def _generate_questions_by_type(self, state: QuestionState, question_count: int) -> List[Dict[str, Any]]:
        """타입별 질문 생성 - 균등 분배"""
        
        print(f"[QUESTION_GEN] ========== 타입별 질문 생성 프로세스 시작 ==========")
        print(f"[QUESTION_GEN] 총 요청 질문 개수: {question_count}")
        print(f"[QUESTION_GEN] 질문 타입들: {state.question_types}")
        
        questions = []
        questions_per_type = question_count // len(state.question_types)  # 3가지 타입이면 각 3개씩
        remaining_questions = question_count % len(state.question_types)
        
        print(f"[QUESTION_GEN] 질문 분배 계획:")
        print(f"[QUESTION_GEN]   - 기본 타입당: {questions_per_type}개")
        print(f"[QUESTION_GEN]   - 나머지 질문: {remaining_questions}개 (첫 번째 타입들에 추가)")
        
        type_generation_results = {}
        
        # 각 타입별로 정확히 지정된 수만큼 생성
        for i, question_type in enumerate(state.question_types):
            # 나머지 질문은 첫 번째 타입들에 1개씩 추가
            current_count = questions_per_type + (1 if i < remaining_questions else 0)
            
            print(f"[QUESTION_GEN] ========== {question_type} 타입 처리 시작 ==========")
            print(f"[QUESTION_GEN] 할당된 질문 개수: {current_count}개 ({questions_per_type} + {1 if i < remaining_questions else 0})")
            
            try:
                type_questions = await self._generate_questions_for_type(state, question_type, current_count)
                questions.extend(type_questions)
                
                # 결과 기록
                type_generation_results[question_type] = {
                    "requested": current_count,
                    "generated": len(type_questions),
                    "success_rate": len(type_questions) / current_count if current_count > 0 else 0
                }
                
                print(f"[QUESTION_GEN] {question_type} 타입 완료: {len(type_questions)}/{current_count}개 생성")
                
            except Exception as e:
                error_msg = f"{question_type} 타입 전체 생성 실패: {str(e)}"
                print(f"[QUESTION_GEN] ERROR: {error_msg}")
                
                type_generation_results[question_type] = {
                    "requested": current_count,
                    "generated": 0,
                    "success_rate": 0,
                    "error": error_msg
                }
        
        # 최종 결과 요약
        total_generated = len(questions)
        overall_success_rate = total_generated / question_count if question_count > 0 else 0
        
        print(f"[QUESTION_GEN] ========== 타입별 질문 생성 최종 결과 ==========")
        print(f"[QUESTION_GEN] 전체 결과: {total_generated}/{question_count}개 생성 (성공률: {overall_success_rate:.1%})")
        print(f"[QUESTION_GEN] 타입별 상세 결과:")
        
        for question_type, result in type_generation_results.items():
            status = "✅" if result["success_rate"] >= 0.8 else "⚠️" if result["success_rate"] >= 0.5 else "❌"
            print(f"[QUESTION_GEN]   {status} {question_type}: {result['generated']}/{result['requested']}개 ({result['success_rate']:.1%})")
            
            if "error" in result:
                print(f"[QUESTION_GEN]     오류: {result['error']}")
        
        # 성공률이 낮은 경우 경고
        if overall_success_rate < 0.7:
            print(f"[QUESTION_GEN] WARNING: 전체 질문 생성 성공률이 낮습니다 ({overall_success_rate:.1%})")
            print(f"[QUESTION_GEN] 부족한 질문을 템플릿 기반으로 보완합니다.")
        
        # 목표 개수에 못 미치는 경우 추가 질문 생성
        if total_generated < question_count:
            missing_count = question_count - total_generated
            print(f"[QUESTION_GEN] 부족한 질문 {missing_count}개를 보완합니다.")
            
            # 실패한 타입들을 우선으로 템플릿 기반 질문 추가
            failed_types = [qtype for qtype, result in type_generation_results.items() 
                           if result["generated"] < result["requested"]]
            
            if failed_types:
                print(f"[QUESTION_GEN] 실패한 타입들을 우선 보완: {failed_types}")
                additional_questions = await self.template_manager._generate_template_questions(state, failed_types, missing_count)
                questions.extend(additional_questions)
                print(f"[QUESTION_GEN] 템플릿 기반 질문 {len(additional_questions)}개 추가")
            
            # 여전히 부족하면 일반 템플릿 질문 추가
            if len(questions) < question_count:
                remaining = question_count - len(questions)
                general_questions = await self.template_manager._generate_general_template_questions(state, remaining)
                questions.extend(general_questions)
                print(f"[QUESTION_GEN] 일반 템플릿 질문 {len(general_questions)}개 추가")
        
        print(f"[QUESTION_GEN] =============================================")
        
        # 목표 개수에 맞춰 자르기 (혹시 초과 생성된 경우)
        final_questions = questions[:question_count]
        final_count = len(final_questions)
        
        print(f"[QUESTION_GEN] 최종 결과: {final_count}/{question_count}개 질문 확보")
        
        # 최종 성공률 계산
        final_success_rate = final_count / question_count if question_count > 0 else 0
        if final_success_rate >= 0.9:
            print(f"[QUESTION_GEN] ✅ 목표 달성: {final_success_rate:.1%} 성공률")
        elif final_success_rate >= 0.7:
            print(f"[QUESTION_GEN] ⚠️ 부분 성공: {final_success_rate:.1%} 성공률")
        else:
            print(f"[QUESTION_GEN] ❌ 목표 미달: {final_success_rate:.1%} 성공률")
        
        return final_questions
    
    async def _generate_questions_for_type(self, state: QuestionState, question_type: str, count: int) -> List[Dict[str, Any]]:
        """특정 타입의 질문 생성 - 질문 개수 보장 및 fallback 메커니즘"""
        
        print(f"[QUESTION_GEN] ========== {question_type} 타입 질문 생성 시작 ==========")
        print(f"[QUESTION_GEN] 요청된 질문 개수: {count}")
        
        questions = []
        generation_errors = []
        max_attempts = count * 2  # 최대 시도 횟수 (요청 개수의 2배)
        
        # 각 질문마다 다른 파일 세트를 사용하여 생성
        for i in range(max_attempts):
            if len(questions) >= count:  # 목표 개수에 도달하면 종료
                break
                
            question_index = i  # 순환하며 다양한 파일 선택
            print(f"[QUESTION_GEN] {question_type} - {i+1}번째 시도 (목표: {len(questions)+1}/{count})")
            
            try:
                question_list = []
                
                if question_type == "code_analysis":
                    question_list = await self.strategies._generate_code_analysis_questions_with_files(state, 1, question_index)
                elif question_type == "tech_stack":
                    question_list = await self.strategies._generate_tech_stack_questions_with_files(state, 1, question_index)
                elif question_type == "architecture":
                    question_list = await self.strategies._generate_architecture_questions_with_files(state, 1, question_index)
                elif question_type == "design_patterns":
                    question_list = await self.strategies._generate_design_pattern_questions(state, 1)
                elif question_type == "problem_solving":
                    question_list = await self.strategies._generate_problem_solving_questions(state, 1)
                elif question_type == "best_practices":
                    question_list = await self.strategies._generate_best_practice_questions(state, 1)
                else:
                    print(f"[QUESTION_GEN] 경고: 지원되지 않는 질문 타입 {question_type}")
                    # 지원되지 않는 타입의 경우 fallback 질문 생성
                    question_list = await self.ai_caller._generate_fallback_questions(state, question_type, 1, question_index)
                
                if question_list:
                    questions.extend(question_list)
                    print(f"[QUESTION_GEN] {question_type} - {i+1}번째 질문 생성 성공: {len(question_list)}개 (현재 총 {len(questions)}개)")
                else:
                    error_msg = f"{question_type} - {i+1}번째 질문 생성 실패: 빈 결과 반환"
                    print(f"[QUESTION_GEN] {error_msg}")
                    generation_errors.append(error_msg)
                    
                    # 실패 시 fallback 질문 생성 시도
                    print(f"[QUESTION_GEN] fallback 질문 생성 시도...")
                    fallback_questions = await self.ai_caller._generate_fallback_questions(state, question_type, 1, question_index)
                    if fallback_questions:
                        questions.extend(fallback_questions)
                        print(f"[QUESTION_GEN] fallback 질문 생성 성공: {len(fallback_questions)}개")
                    
            except Exception as e:
                error_msg = f"{question_type} - {i+1}번째 질문 생성 실패: {str(e)}"
                print(f"[QUESTION_GEN] ERROR: {error_msg}")
                generation_errors.append(error_msg)
                
                # 예외 발생 시에도 fallback 질문 생성 시도
                try:
                    print(f"[QUESTION_GEN] 예외 발생, fallback 질문 생성 시도...")
                    fallback_questions = await self.ai_caller._generate_fallback_questions(state, question_type, 1, question_index)
                    if fallback_questions:
                        questions.extend(fallback_questions)
                        print(f"[QUESTION_GEN] 예외 처리용 fallback 질문 생성 성공: {len(fallback_questions)}개")
                except Exception as fallback_error:
                    print(f"[QUESTION_GEN] fallback 질문 생성도 실패: {fallback_error}")
                    
                continue
        
        # 목표 개수에 미달하는 경우 추가 보정
        if len(questions) < count:
            shortage = count - len(questions)
            print(f"[QUESTION_GEN] 목표 미달: {len(questions)}/{count}개. {shortage}개 추가 생성 시도...")
            
            # 간단한 템플릿 기반 질문 생성으로 부족분 보완
            template_questions = await self.template_manager._generate_template_questions(state, question_type, shortage)
            questions.extend(template_questions)
            print(f"[QUESTION_GEN] 템플릿 기반 질문 {len(template_questions)}개 추가")
        
        # 생성 결과 요약
        success_count = len(questions)
        final_count = min(success_count, count)  # 최대 요청 개수까지만
        
        print(f"[QUESTION_GEN] ========== {question_type} 타입 질문 생성 결과 ==========")
        print(f"[QUESTION_GEN] 최종 생성: {final_count}개 / 요청: {count}개")
        print(f"[QUESTION_GEN] 성공률: {(final_count/count)*100:.1f}%")
        
        if generation_errors:
            print(f"[QUESTION_GEN] 발생한 오류 {len(generation_errors)}개:")
            for error in generation_errors[-3:]:  # 최근 3개만 출력
                print(f"[QUESTION_GEN]   - {error}")
        
        print(f"[QUESTION_GEN] ==============================================")
        
        return questions[:count]  # 요청한 개수만큼만 반환
    
    async def _generate_code_analysis_questions(self, state: QuestionState, count: int) -> List[Dict[str, Any]]:
        """코드 분석 질문 생성 - 실제 파일 내용이 있는 경우만"""
        
        questions = []
        
        if not state.code_snippets:
            print("[DEBUG] 코드 스니펫이 없어서 코드 분석 질문 생성을 건너뜁니다.")
            return []
        
        # 중요도와 내용 유무를 기준으로 우선순위 정렬
        def get_priority_score(snippet):
            importance_scores = {
                "very_high": 100,
                "high": 80,
                "medium": 50,
                "low": 20
            }
            
            base_score = importance_scores.get(snippet["metadata"].get("importance", "low"), 20)
            
            # 실제 내용이 있으면 +30점
            if snippet["metadata"].get("has_real_content", False):
                base_score += 30
            
            # 복잡도 보너스 (높은 복잡도일수록 우선)
            complexity = snippet["metadata"].get("complexity", 1.0)
            base_score += min(complexity * 2, 10)
            
            return base_score
        
        # 우선순위 기준으로 정렬
        all_snippets = sorted(state.code_snippets, key=get_priority_score, reverse=True)
        
        print(f"[DEBUG] 파일 우선순위 정렬 완료:")
        for i, snippet in enumerate(all_snippets[:5]):
            print(f"  {i+1}. {snippet['metadata'].get('file_path')} (우선순위: {get_priority_score(snippet)}, 실제내용: {snippet['metadata'].get('has_real_content')}, 중요도: {snippet['metadata'].get('importance')})")
        
        # 실제 내용이 있는 파일들만 필터링
        real_content_snippets = [s for s in all_snippets if s["metadata"].get("has_real_content", False)]
        
        print(f"[DEBUG] 실제 내용이 있는 파일: {len(real_content_snippets)}개")
        
        # 실제 내용이 있는 파일이 없으면 빈 리스트 반환
        if not real_content_snippets:
            print("[DEBUG] 실제 파일 내용이 없어서 코드 분석 질문 생성을 건너뜁니다.")
            return []
        
        for i in range(min(count, len(real_content_snippets))):
            snippet = real_content_snippets[i]
            
            print(f"[DEBUG] 질문 생성 중: {snippet['metadata'].get('file_path')} (실제내용: True)")
            
            try:
                # 실제 파일 내용이 있는 경우 - 추출된 요소들 활용
                extracted_elements = snippet["metadata"].get("extracted_elements", {})
                file_type = snippet["metadata"].get("file_type", "general")
                complexity = snippet["metadata"].get("complexity", 1.0)
                
                # 파일 유형별 맞춤 프롬프트 생성
                context_info = []
                if extracted_elements.get("classes"):
                    context_info.append(f"클래스: {', '.join(extracted_elements['classes'][:3])}")
                if extracted_elements.get("functions"):
                    context_info.append(f"주요 함수: {', '.join(extracted_elements['functions'][:3])}")
                if extracted_elements.get("imports"):
                    context_info.append(f"사용 라이브러리: {', '.join(extracted_elements['imports'][:2])}")
                
                context_str = " | ".join(context_info) if context_info else "기본 코드 구조"
                
                # 파일 경로 추출
                file_path = snippet["metadata"].get("file_path", "")
                
                # 파일 유형별 질문 스타일 조정
                if file_type == "controller":
                    question_focus = "HTTP 요청 처리, 라우팅, 에러 핸들링"
                elif file_type == "service":
                    question_focus = "비즈니스 로직, 데이터 처리, 트랜잭션"
                elif file_type == "model":
                    question_focus = "데이터 모델링, 관계 설정, 유효성 검사"
                elif file_type == "configuration":
                    question_focus = "설정 관리, 환경 분리, 보안"
                else:
                    question_focus = "코드 구조, 설계 패턴, 최적화"
                
                # 파일별 맞춤 프롬프트 생성 - 실제 파일 내용 기반
                if file_path.endswith("package.json"):
                    prompt = f"""
다음은 실제 프로젝트의 package.json 파일입니다. 이 파일의 구체적인 내용을 바탕으로 기술면접 질문을 생성해주세요.

=== package.json 내용 ===
```json
{snippet["content"][:1500]}
```

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[핵심 질문을 1-2문장으로 명확하게]

**상황:**
[간단한 맥락이나 배경 1-2문장]

**요구사항:**
- [구체적 요구사항 1]
- [구체적 요구사항 2]
- [구체적 요구사항 3]

**평가 포인트:**
- [기술적 이해도 측정 요소]
- [실무 경험 확인 요소]

=== 내용 생성 요구사항 ===
- 실제 dependencies나 devDependencies 이름들을 직접 언급
- 실제 scripts 명령어들을 직접 참조  
- 실제 버전 정보나 설정값들을 구체적으로 언급
- 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성

위 형식을 정확히 지켜서 질문 하나만 생성해주세요.
"""
                elif file_path.endswith("pyproject.toml"):
                    prompt = f"""
다음은 실제 Python 프로젝트의 pyproject.toml 파일입니다. 이 파일의 구체적인 내용을 바탕으로 기술면접 질문을 생성해주세요.

=== pyproject.toml 내용 ===
```toml
{snippet["content"][:1500]}
```

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[pyproject.toml 관련 핵심 질문 1-2문장]

**상황:**
[Python 프로젝트 맥락과 설정 배경]

**요구사항:**
- [구체적 설정 설명 요구사항]
- [도구 선택 이유 설명 요구사항]
- [프로젝트 특성 연관 설명 요구사항]

**평가 포인트:**
- [Python 빌드 시스템 이해도]
- [개발 도구 활용 경험]

=== 내용 생성 요구사항 ===
- 실제 build-system requirements를 직접 언급
- 실제 tool 설정들(isort, pytest 등)을 구체적으로 참조
- 실제 configuration 값들을 활용
- 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성

위 형식을 정확히 지켜서 질문 하나만 생성해주세요.
"""
                elif file_path.endswith("README.md") or file_path.endswith("README.rst"): 
                    prompt = f"""
다음은 실제 프로젝트의 README 파일입니다.

=== README 내용 ===
```
{snippet["content"][:1000]}
```

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[README 기반 프로젝트 이해 질문 1-2문장]

**상황:**
[프로젝트 특성과 README 역할 설명]

**요구사항:**
- [프로젝트 목적과 특징 설명 요구]
- [기술적 구현 방식 설명 요구]
- [실제 사용 경험 기반 설명 요구]

**평가 포인트:**
- [프로젝트 이해도]
- [기술적 판단 능력]

=== 내용 생성 요구사항 ===
- 실제 프로젝트 설명과 특징들을 직접 언급
- 실제 언급된 기능이나 구조를 구체적으로 참조
- 실제 설치나 기여 방법들을 활용
- 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성

위 형식을 정확히 지켜서 질문 하나만 생성해주세요:
"""
                else:
                    prompt = f"""
다음은 실제 프로젝트의 {file_type} 파일입니다. 이 파일의 구체적인 내용을 바탕으로 기술면접 질문을 생성해주세요.

=== 파일 정보 ===
경로: {snippet["metadata"].get("file_path", "unknown")}
언어: {snippet["metadata"].get("language", "unknown")}
파일 유형: {file_type}
복잡도: {complexity:.1f}/10

=== 실제 코드 내용 ===
```{snippet["metadata"].get("language", "")}
{snippet["content"][:2000]}
```

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[코드 분석 관련 핵심 질문 1-2문장]

**상황:**
[파일의 역할과 프로젝트 내 위치 설명]

**요구사항:**
- [구체적 코드 구현 설명 요구]
- [설계 선택 이유 설명 요구]
- [최적화나 개선 방안 제시 요구]

**평가 포인트:**
- [{question_focus} 이해도]
- [실제 구현 경험]

=== 질문 생성 지침 ===
1. 위 코드에서 실제로 사용된 구체적인 함수명, 변수명, 클래스명을 질문에 포함하세요
2. 코드의 실제 로직과 구현 방식을 기반으로 질문하세요
3. {state.difficulty_level} 난이도에 맞는 기술적 깊이를 유지하세요
4. "만약", "가정", "일반적으로" 같은 추상적 표현 대신 코드의 실제 내용을 직접 언급하세요
5. 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성

위 형식을 정확히 지켜서 질문 하나만 생성해주세요:
"""
                
                # 프롬프트에 파일 내용이 포함되는지 상세 디버그 로그
                print(f"[QUESTION_GEN] ========== 질문 생성 상세 로그 ==========")
                print(f"[QUESTION_GEN] 대상 파일: {file_path}")
                print(f"[QUESTION_GEN] 파일 유형: {file_type}")
                print(f"[QUESTION_GEN] 파일 내용 길이: {len(snippet['content'])} 문자")
                print(f"[QUESTION_GEN] 실제 내용 여부: {snippet['metadata'].get('has_real_content', False)}")
                print(f"[QUESTION_GEN] 파일 내용 미리보기 (첫 200자):")
                print(f"[QUESTION_GEN] {snippet['content'][:200]}...")
                print(f"[QUESTION_GEN] ---------- AI에게 전송되는 프롬프트 전체 내용 ----------")
                print(f"[QUESTION_GEN] 프롬프트 길이: {len(prompt)} 문자")
                print(f"[QUESTION_GEN] 프롬프트 내용:")
                print(prompt)
                print(f"[QUESTION_GEN] ---------- 프롬프트 전송 완료 ----------")
                
                # Gemini API 호출 (재시도 및 fallback 메커니즘 포함)
                try:
                    ai_response = await self.ai_caller._call_ai_with_retry(ai_service.generate_analysis, prompt, max_retries=3)
                    
                    # AI 응답 안전성 검증
                    if ai_response and isinstance(ai_response, dict) and "content" in ai_response and ai_response["content"]:
                        ai_question = ai_response["content"].strip()
                        if not ai_question:  # 빈 응답인 경우
                            raise Exception("AI 응답이 비어있음")
                    else:
                        raise Exception("AI 응답이 None이거나 형식이 올바르지 않음")
                        
                except Exception as ai_error:
                    print(f"[QUESTION_GEN] AI 질문 생성 실패, fallback 사용: {ai_error}")
                    # 기본적인 fallback 질문 생성
                    if "snippet" in locals() and snippet:
                        ai_question = f"이 {snippet['metadata'].get('file_type', '파일')}의 주요 기능과 구조를 분석하고 설명해주세요."
                    else:
                        ai_question = "프로젝트의 전반적인 구조와 설계 원칙을 분석해주세요."
                
                print(f"[QUESTION_GEN] ---------- AI 응답 결과 ----------")
                print(f"[QUESTION_GEN] AI 응답 길이: {len(ai_question)} 문자")
                print(f"[QUESTION_GEN] 생성된 질문 전체:")
                print(f"[QUESTION_GEN] {ai_question}")
                print(f"[QUESTION_GEN] ========== 질문 생성 완료 ==========")
                
                question = {
                    "id": f"code_analysis_{i}_{random.randint(1000, 9999)}",
                    "type": "code_analysis",
                    "question": ai_question,
                    "code_snippet": {
                        "content": snippet["content"][:800] + "..." if len(snippet["content"]) > 800 else snippet["content"],
                        "language": snippet["metadata"].get("language", "unknown"),
                        "file_path": snippet["metadata"].get("file_path", ""),
                        "complexity": snippet["metadata"].get("complexity", 1.0),
                        "has_real_content": True,
                        "file_type": snippet["metadata"].get("file_type", "general"),
                        "extracted_elements": snippet["metadata"].get("extracted_elements", {})
                    },
                    "difficulty": state.difficulty_level,
                    "time_estimate": self._estimate_question_time(snippet["metadata"].get("complexity", 1.0)),
                    "generated_by": "AI",
                    "source_file": snippet["metadata"].get("file_path", ""),
                    "importance": snippet["metadata"].get("importance", "medium"),
                    "file_type": snippet["metadata"].get("file_type", "general"),
                    "context": f"파일: {snippet['metadata'].get('file_path', 'unknown')} | 유형: {snippet['metadata'].get('file_type', 'general')} | 복잡도: {snippet['metadata'].get('complexity', 1.0):.1f}/10"
                }
                questions.append(question)
                
            except Exception as e:
                print(f"AI 질문 생성 실패 (파일: {snippet['metadata'].get('file_path')}): {e}")
                # AI 생성 실패 시 해당 파일은 건너뛰고 다음 파일로 진행
                # 더미/템플릿 질문은 생성하지 않음
                continue
        
        return questions
    
    async def _generate_tech_stack_questions(self, state: QuestionState, count: int) -> List[Dict[str, Any]]:
        """기술 스택 질문 생성"""
        
        questions = []
        
        # 분석 데이터에서 기술 스택 추출 (비중 5% 이상만)
        tech_stack = []
        print(f"[DEBUG] 분석 데이터 구조: {state.analysis_data.keys() if state.analysis_data else 'None'}")
        
        if state.analysis_data and "metadata" in state.analysis_data:
            tech_stack_str = state.analysis_data["metadata"].get("tech_stack", "{}")
            print(f"[DEBUG] tech_stack JSON 문자열: {tech_stack_str}")
            try:
                tech_stack_dict = json.loads(tech_stack_str)
                print(f"[DEBUG] 파싱된 기술 스택: {tech_stack_dict}")
                
                # 비중이 0.05 (5%) 이상인 기술만 선택
                tech_stack = [tech for tech, score in tech_stack_dict.items() if score >= 0.05]
                print(f"[DEBUG] 필터링된 기술 스택 (5% 이상): {tech_stack}")
            except Exception as e:
                print(f"[DEBUG] tech_stack JSON 파싱 실패: {e}")
                tech_stack = []
        else:
            print(f"[DEBUG] metadata 또는 tech_stack 필드가 분석 데이터에 없습니다.")
        
        if not tech_stack:
            # 기술 스택이 없는 경우 빈 리스트 반환
            print("[DEBUG] 유효한 기술 스택이 없어서 tech_stack 질문 생성을 건너뜁니다.")
            return []
        
        for i in range(count):
            tech = random.choice(tech_stack)
            
            # 실제 파일 내용을 기반으로 한 기술별 질문 생성
            try:
                # 분석된 파일 내용 가져오기
                file_context = ""
                if state.code_snippets:
                    file_info = []
                    for snippet in state.code_snippets[:3]:  # 최대 3개 파일
                        file_path = snippet["metadata"].get("file_path", "")
                        content_preview = snippet["content"][:300]
                        file_info.append(f"파일: {file_path}\n내용: {content_preview}...")
                    file_context = "\n\n".join(file_info)
                
                prompt = f"""
다음은 실제 프로젝트에서 {tech} 기술이 사용된 파일들입니다:

=== 실제 프로젝트 파일 내용 ===
{file_context}

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[{tech} 기술에 대한 핵심 질문 1-2문장]

**상황:**
[프로젝트 맥락과 {tech} 사용 배경]

**요구사항:**
- [실제 구현 관련 요구사항]
- [기술적 깊이 요구사항]
- [경험 기반 설명 요구사항]

**평가 포인트:**
- [{tech} 기술 이해도]
- [실제 프로젝트 경험]

=== 내용 요구사항 ===
- 실제 파일에서 사용된 구체적인 설정, 패키지, 코드를 직접 언급
- {state.difficulty_level} 난이도에 맞는 기술적 질문
- 일반적인 이론이 아닌 실제 구현 기반 질문
- 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성

위 형식을 정확히 지켜서 생성해주세요:
"""
                
                print(f"[QUESTION_GEN] ========== 기술스택 질문 생성 상세 로그 ==========")
                print(f"[QUESTION_GEN] 대상 기술: {tech}")
                print(f"[QUESTION_GEN] 파일 컨텍스트 길이: {len(file_context)} 문자")
                print(f"[QUESTION_GEN] 파일 컨텍스트 내용:")
                print(f"[QUESTION_GEN] {file_context[:500]}...")
                print(f"[QUESTION_GEN] ---------- 기술스택 프롬프트 전체 내용 ----------")
                print(f"[QUESTION_GEN] 프롬프트 길이: {len(prompt)} 문자")
                print(f"[QUESTION_GEN] 프롬프트 내용:")
                print(prompt)
                print(f"[QUESTION_GEN] ---------- 프롬프트 전송 완료 ----------")
                
                # Gemini API 호출 (재시도 및 fallback 메커니즘 포함)
                try:
                    ai_response = await self.ai_caller._call_ai_with_retry(ai_service.generate_analysis, prompt, max_retries=3)
                    
                    # AI 응답 안전성 검증
                    if ai_response and isinstance(ai_response, dict) and "content" in ai_response and ai_response["content"]:
                        ai_question = ai_response["content"].strip()
                        if not ai_question:  # 빈 응답인 경우
                            raise Exception("AI 응답이 비어있음")
                    else:
                        raise Exception("AI 응답이 None이거나 형식이 올바르지 않음")
                        
                except Exception as ai_error:
                    print(f"[QUESTION_GEN] AI 질문 생성 실패, fallback 사용: {ai_error}")
                    # 기본적인 fallback 질문 생성
                    if "snippet" in locals() and snippet:
                        ai_question = f"이 {snippet['metadata'].get('file_type', '파일')}의 주요 기능과 구조를 분석하고 설명해주세요."
                    else:
                        ai_question = "프로젝트의 전반적인 구조와 설계 원칙을 분석해주세요."
                
                print(f"[QUESTION_GEN] ---------- 기술스택 AI 응답 결과 ----------")
                print(f"[QUESTION_GEN] AI 응답 길이: {len(ai_question)} 문자")
                print(f"[QUESTION_GEN] 생성된 기술스택 질문:")
                print(f"[QUESTION_GEN] {ai_question}")
                print(f"[QUESTION_GEN] ========== 기술스택 질문 생성 완료 ==========")
                
                question = {
                    "id": f"tech_stack_{i}_{random.randint(1000, 9999)}",
                    "type": "tech_stack",
                    "question": ai_question,
                    "technology": tech,
                    "difficulty": state.difficulty_level,
                    "time_estimate": "3-5분",
                    "generated_by": "AI"
                }
                questions.append(question)
                
            except Exception as e:
                print(f"AI 기술 스택 질문 생성 실패 (기술: {tech}): {e}")
                # AI 생성 실패 시 해당 기술은 건너뛰고 다음으로 진행
                # 더미/템플릿 질문은 생성하지 않음
                continue
        
        return questions
    
    async def _generate_architecture_questions(self, state: QuestionState, count: int) -> List[Dict[str, Any]]:
        """아키텍처 질문 생성"""
        
        questions = []
        
        context = self._extract_architecture_context(state)
        
        # 실제 분석 데이터가 없으면 빈 리스트 반환
        if not context:
            return []
        
        for i in range(count):
            # AI를 활용한 프로젝트별 맞춤 아키텍처 질문 생성
            try:
                context_info = []
                if "project_type" in context:
                    context_info.append(f"프로젝트 타입: {context['project_type']}")
                if "scale" in context:
                    context_info.append(f"프로젝트 규모: {context['scale']}")
                if "deployment" in context:
                    context_info.append(f"배포 방식: {context['deployment']}")
                
                context_str = ", ".join(context_info) if context_info else "웹 애플리케이션"
                
                prompt = f"""
다음 프로젝트 정보를 바탕으로 아키텍처 관련 기술면접 질문을 생성해주세요.

프로젝트 정보: {context_str}

=== 질문 생성 형식 (반드시 준수) ===
다음 형식을 정확히 따라서 생성해주세요:

**질문:**
[아키텍처 관련 핵심 질문]

**상황:**
[프로젝트 규모와 복잡성 설명]

**요구사항:**
- [아키텍처 설계 설명 요구]
- [확장성 고려사항 설명 요구]
- [기술 선택 이유 설명 요구]

**평가 포인트:**
- [아키텍처 설계 능력]
- [확장성 고려 능력]

=== 내용 요구사항 ===
- 프로젝트의 특성을 고려한 아키텍처 질문
- {state.difficulty_level} 난이도에 맞는 질문
- 실제 면접에서 나올 법한 실용적 질문
- 구체적이고 기술적인 질문
- 각 섹션은 **볼드 제목:**으로 시작하고 그 아래 내용 작성
- numbered list(1., 2., 3.) 사용 금지
- 마크다운 제목 형식(#, ##) 사용 금지

위 형식을 정확히 지켜서 하나의 완전한 질문만 생성해주세요:
"""
                
                print(f"[QUESTION_GEN] ========== 아키텍처 질문 생성 상세 로그 ==========")
                print(f"[QUESTION_GEN] 컨텍스트 정보: {context_str}")
                print(f"[QUESTION_GEN] ---------- 아키텍처 프롬프트 전체 내용 ----------")
                print(f"[QUESTION_GEN] 프롬프트 길이: {len(prompt)} 문자")
                print(f"[QUESTION_GEN] 프롬프트 내용:")
                print(prompt)
                print(f"[QUESTION_GEN] ---------- 프롬프트 전송 완료 ----------")
                
                # Gemini API 호출 (재시도 및 fallback 메커니즘 포함)
                try:
                    ai_response = await self.ai_caller._call_ai_with_retry(ai_service.generate_analysis, prompt, max_retries=3)
                    
                    # AI 응답 안전성 검증
                    if ai_response and isinstance(ai_response, dict) and "content" in ai_response and ai_response["content"]:
                        ai_question = ai_response["content"].strip()
                        if not ai_question:  # 빈 응답인 경우
                            raise Exception("AI 응답이 비어있음")
                    else:
                        raise Exception("AI 응답이 None이거나 형식이 올바르지 않음")
                        
                except Exception as ai_error:
                    print(f"[QUESTION_GEN] AI 질문 생성 실패, fallback 사용: {ai_error}")
                    # 기본적인 fallback 질문 생성
                    if "snippet" in locals() and snippet:
                        ai_question = f"이 {snippet['metadata'].get('file_type', '파일')}의 주요 기능과 구조를 분석하고 설명해주세요."
                    else:
                        ai_question = "프로젝트의 전반적인 구조와 설계 원칙을 분석해주세요."
                
                print(f"[QUESTION_GEN] ---------- 아키텍처 AI 응답 결과 ----------")
                print(f"[QUESTION_GEN] AI 응답 길이: {len(ai_question)} 문자")
                print(f"[QUESTION_GEN] 생성된 아키텍처 질문:")
                print(f"[QUESTION_GEN] {ai_question}")
                print(f"[QUESTION_GEN] ========== 아키텍처 질문 생성 완료 ==========")
                
                question = {
                    "id": f"architecture_{i}_{random.randint(1000, 9999)}",
                    "type": "architecture",
                    "question": ai_question,
                    "difficulty": state.difficulty_level,
                    "context": context_str,
                    "time_estimate": "10-15분",
                    "generated_by": "AI"
                }
                questions.append(question)
                
            except Exception as e:
                print(f"AI 아키텍처 질문 생성 실패: {e}")
                # AI 생성 실패 시 해당 질문은 건너뛰고 다음으로 진행
                # 더미/템플릿 질문은 생성하지 않음
                continue
        
        return questions
    
    def _estimate_question_time(self, complexity: float) -> str:
        """복잡도에 따른 질문 답변 예상 시간 추정"""
        
        if complexity <= 2.0:
            return "3-5분"
        elif complexity <= 4.0:
            return "5-7분"
        elif complexity <= 6.0:
            return "7-10분"
        elif complexity <= 8.0:
            return "10-15분"
        else:
            return "15-20분"
    
    def _extract_context_summary(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 컨텍스트 요약 추출"""
        
        if not analysis_data:
            return {}
        
        metadata = analysis_data.get("metadata", {})
        
        return {
            "tech_stack": json.loads(metadata.get("tech_stack", "{}")),
            "complexity_score": metadata.get("complexity_score", 0.0),
            "file_count": metadata.get("file_count", 0),
            "analysis_summary": analysis_data.get("analysis_text", "")[:200] + "..."
        }
    
    def _extract_architecture_context(self, state: QuestionState) -> Dict[str, Any]:
        """아키텍처 컨텍스트 추출"""
        
        context = {}
        
        if state.analysis_data:
            metadata = state.analysis_data.get("metadata", {})
            file_count = metadata.get("file_count", 0)
            
            # 프로젝트 규모 분석
            if file_count > 100:
                context["scale"] = "large"
            elif file_count > 20:
                context["scale"] = "medium"
            elif file_count > 0:
                context["scale"] = "small"
            
            # 기술 스택으로 프로젝트 타입 추론
            tech_stack_str = metadata.get("tech_stack", "{}")
            try:
                tech_stack = json.loads(tech_stack_str)
                tech_keys = [key.lower() for key in tech_stack.keys()]
                
                if any(tech in tech_keys for tech in ["react", "vue", "angular"]):
                    context["project_type"] = "SPA (Single Page Application)"
                elif any(tech in tech_keys for tech in ["django", "flask", "fastapi"]):
                    context["project_type"] = "REST API / Web Service"
                elif any(tech in tech_keys for tech in ["spring", "spring-boot"]):
                    context["project_type"] = "Enterprise Application"
                elif any(tech in tech_keys for tech in ["express", "koa", "nestjs"]):
                    context["project_type"] = "Node.js Web Application"
                elif "dockerfile" in tech_keys or "docker" in tech_keys:
                    context["deployment"] = "Docker 기반 배포"
            except:
                pass
        
        return context
    
    async def generate_follow_up_questions(self, original_question: Dict[str, Any], user_answer: str) -> List[Dict[str, Any]]:
        """후속 질문 생성"""
        
        follow_ups = []
        
        # AI 기반 후속 질문 생성 (임시 비활성화)
        # if self.llm and user_answer:
        #     try:
        #         # AI 생성 로직
        #         pass
        #     except Exception as e:
        #         print(f"AI 후속 질문 생성 오류: {e}")
        
        # 기본 후속 질문들
        if original_question["type"] == "code_analysis":
            follow_ups.append({
                "id": f"follow_up_{original_question['id']}_default_{random.randint(1000, 9999)}",
                "type": "follow_up",
                "question": "이와 비슷한 문제를 실무에서 어떻게 해결하셨나요?",
                "parent_question_id": original_question["id"],
                "time_estimate": "3-5분"
            })
        
        return follow_ups
    
    async def _generate_metadata_based_questions(self, state: QuestionState, snippets: List[Dict], count: int) -> List[Dict[str, Any]]:
        """파일 내용이 없을 때 메타데이터와 파일명 기반으로 질문 생성"""
        
        print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성 시작 (요청: {count}개)")
        
        questions = []
        available_snippets = snippets[:count * 2]  # 더 많은 선택지 확보
        
        for i, snippet in enumerate(available_snippets):
            if len(questions) >= count:
                break
                
            file_path = snippet["metadata"].get("file_path", "unknown")
            file_type = snippet["metadata"].get("file_type", "general")
            importance = snippet["metadata"].get("importance", "medium")
            language = snippet["metadata"].get("language", "unknown")
            
            print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성: {file_path}")
            
            try:
                # 파일별 차별화된 프롬프트 생성
                question_text = self._generate_file_specific_question(snippet, state, i)
                
                if not question_text:
                    # 기본 프롬프트로 대체
                    question_text = self._generate_default_question_for_file_type(snippet)
                
                question = {
                    "id": f"metadata_based_{i}_{random.randint(1000, 9999)}",
                    "type": "code_analysis", 
                    "question": question_text,
                    "code_snippet": {
                        "content": f"# 파일: {file_path}\n# 타입: {file_type}\n# 언어: {language}\n# 중요도: {importance}\n\n# 내용을 직접 확인할 수 없지만, 파일명과 구조를 통해 분석할 수 있습니다.",
                        "language": language,
                        "file_path": file_path,
                        "complexity": 3.0,  # 메타데이터 기반이므로 중간 복잡도
                        "has_real_content": False,
                        "file_type": file_type,
                        "extracted_elements": {}
                    },
                    "difficulty": state.difficulty_level,
                    "time_estimate": "5-7분",  # 분석적 사고가 필요하므로 조금 더 길게
                    "generated_by": "metadata_template",
                    "source_file": file_path,
                    "importance": importance,
                    "file_type": file_type,
                    "context": f"파일: {file_path} | 유형: {file_type} | 언어: {language} | 메타데이터 기반 질문"
                }
                
                questions.append(question)
                print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성 성공: {file_path}")
                
            except Exception as e:
                print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성 실패 ({file_path}): {e}")
                continue
        
        print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성 완료: {len(questions)}/{count}개")
        return questions
    
    def _generate_file_specific_question(self, snippet: Dict, state: QuestionState, question_index: int) -> str:
        """파일별로 차별화된 질문 생성"""
        
        file_path = snippet["metadata"].get("file_path", "")
        file_type = snippet["metadata"].get("file_type", "general")
        language = snippet["metadata"].get("language", "unknown")
        importance = snippet["metadata"].get("importance", "medium")
        
        # 파일 유형별 차별화된 질문 생성 (질문 인덱스 기반)
        if file_path.endswith("package.json"):
            if question_index == 0:
                return f"이 package.json의 dependencies 분석을 통해 프로젝트의 기술 스택 선택 이유와 각 라이브러리의 역할을 설명해주세요. 특히 버전 관리 전략도 포함해서 설명해주세요."
            elif question_index == 1:
                return f"package.json의 scripts 섹션을 분석하여 프로젝트의 빌드/배포 파이프라인과 개발 워크플로우를 설명해주세요."
            else:
                return f"package.json의 devDependencies와 dependencies 구분을 통해 프로덕션 vs 개발환경 분리 전략을 분석해주세요."
        
        elif file_path.endswith(("babel.config.js", "babel.config.json")):
            if question_index == 0:
                return f"이 Babel 설정 파일에서 사용된 플러그인들과 프리셋의 역할을 분석하고, 모던 JavaScript 개발에서 Babel이 해결하는 문제를 설명해주세요."
            elif question_index == 1:
                return f"Babel 설정에서 loose 모드와 useBuiltIns 옵션의 의미를 설명하고, 번들 크기와 성능에 미치는 영향을 분석해주세요."
            else:
                return f"이 Babel 설정이 지원하는 JavaScript 문법과 브라우저 호환성 전략을 분석해주세요."
        
        elif file_path.endswith(("webpack.config.js", "vite.config.js", "rollup.config.js")):
            if question_index == 0:
                return f"이 번들러 설정 파일({file_path})의 entry point와 output 설정을 분석하고, 모듈 번들링 전략을 설명해주세요."
            elif question_index == 1:
                return f"설정 파일에서 사용된 플러그인들의 역할과 최적화 설정이 빌드 성능에 미치는 영향을 분석해주세요."
            else:
                return f"개발환경과 프로덕션 환경에서 다르게 적용되는 번들링 최적화 설정을 분석해주세요."
        
        elif file_path.endswith(("requirements.txt", "pyproject.toml", "setup.py")):
            if question_index == 0:
                return f"이 Python 의존성 파일({file_path})에서 사용된 주요 라이브러리들의 용도와 버전 제약 조건의 이유를 분석해주세요."
            elif question_index == 1:
                return f"Python 패키지 관리에서 이 파일의 역할과 가상환경 관리 모범 사례를 설명해주세요."
            else:
                return f"의존성 충돌 해결과 보안 측면에서 이 파일의 중요성을 분석해주세요."
        
        elif file_path.endswith((".eslintrc", ".eslintrc.js", ".eslintrc.json")):
            if question_index == 0:
                return f"이 ESLint 설정에서 사용된 rules와 extends 설정을 분석하고, 코드 품질 향상에 미치는 영향을 설명해주세요."
            elif question_index == 1:
                return f"ESLint 설정에서 parser와 환경(env) 설정의 의미와 프로젝트별 커스터마이징 방법을 설명해주세요."
            else:
                return f"이 린트 설정이 팀 협업과 코드 일관성 유지에 어떻게 기여하는지 분석해주세요."
        
        elif file_path.endswith(("tsconfig.json", "jsconfig.json")):
            if question_index == 0:
                return f"이 TypeScript/JavaScript 컴파일러 설정에서 compilerOptions의 주요 옵션들과 타입 안정성에 미치는 영향을 분석해주세요."
            elif question_index == 1:
                return f"경로 매핑(paths)과 모듈 해상도 설정이 대규모 프로젝트 구조에 미치는 영향을 설명해주세요."
            else:
                return f"strict 모드와 관련 옵션들이 코드 품질과 개발 생산성에 미치는 영향을 분석해주세요."
        
        elif file_path.endswith((".gitignore", ".dockerignore")):
            if question_index == 0:
                return f"이 ignore 파일({file_path})의 패턴 분석을 통해 프로젝트의 구조와 보안 고려사항을 설명해주세요."
            elif question_index == 1:
                return f"버전 관리에서 제외되는 파일들의 선택 기준과 협업 시 주의사항을 분석해주세요."
            else:
                return f"이 ignore 설정이 빌드 성능과 배포 최적화에 미치는 영향을 설명해주세요."
        
        elif file_path.endswith(("README.md", "CONTRIBUTING.md", "CHANGELOG.md")):
            if question_index == 0:
                return f"이 문서 파일({file_path})에서 다루어야 할 핵심 내용과 오픈소스 프로젝트 관리에서의 중요성을 설명해주세요."
            elif question_index == 1:
                return f"좋은 기술 문서 작성의 원칙과 개발자 커뮤니티 참여를 촉진하는 방법을 분석해주세요."
            else:
                return f"문서화가 프로젝트 유지보수성과 신규 개발자 온보딩에 미치는 영향을 설명해주세요."
        
        elif 'test' in file_path.lower() or 'spec' in file_path.lower():
            if question_index == 0:
                return f"이 테스트 파일({file_path})에서 사용될 것으로 예상되는 테스트 패턴과 전략을 분석하고, 테스트 주도 개발(TDD)의 장점을 설명해주세요."
            elif question_index == 1:
                return f"단위 테스트, 통합 테스트, E2E 테스트의 차이점과 이 파일이 담당하는 테스트 범위를 분석해주세요."
            else:
                return f"테스트 커버리지와 코드 품질의 관계, 그리고 효과적인 테스트 작성 방법을 설명해주세요."
        
        elif language == "python":
            if question_index == 0:
                return f"이 Python 파일({file_path})에서 예상되는 주요 디자인 패턴과 Python다운 코드 작성 원칙(Pythonic)을 설명해주세요."
            elif question_index == 1:
                return f"Python의 모듈/패키지 시스템과 이 파일이 프로젝트 전체 아키텍처에서 담당하는 역할을 분석해주세요."
            else:
                return f"Python 성능 최적화 기법과 메모리 관리, 그리고 이 파일에서 적용 가능한 개선사항을 분석해주세요."
        
        elif language in ["javascript", "typescript"]:
            if question_index == 0:
                return f"이 {language} 파일({file_path})에서 사용될 것으로 예상되는 ES6+ 문법과 함수형/객체지향 프로그래밍 패러다임을 설명해주세요."
            elif question_index == 1:
                return f"JavaScript/TypeScript의 비동기 처리 패턴과 이 파일에서의 활용 방안을 분석해주세요."
            else:
                return f"모듈 시스템(CommonJS vs ES6 modules)과 번들링 최적화가 이 파일에 미치는 영향을 설명해주세요."
        
        else:
            # 기타 파일들에 대한 기본 질문
            return None  # 기본 프롬프트 사용
    
    def _generate_default_question_for_file_type(self, snippet: Dict) -> str:
        """파일 타입별 기본 질문 생성"""
        
        file_path = snippet["metadata"].get("file_path", "")
        file_type = snippet["metadata"].get("file_type", "general")
        language = snippet["metadata"].get("language", "unknown")
        
        if file_path.endswith(("Dockerfile", "docker-compose.yml", "docker-compose.yaml")):
            return f"이 컨테이너화 설정 파일({file_path})을 통해 애플리케이션 배포 전략을 분석하고, Docker 사용의 장점과 고려사항을 설명해주세요."
        
        elif file_path.endswith((".yml", ".yaml")) and any(keyword in file_path.lower() for keyword in ["ci", "cd", "github", "action", "workflow"]):
            return f"이 CI/CD 설정 파일({file_path})의 역할과 지속적 통합/배포 파이프라인에서의 중요성을 설명해주세요."
        
        elif file_path.endswith((".env", ".env.example")):
            return f"환경변수 설정 파일({file_path})의 역할과 보안을 고려한 환경변수 관리 방법을 설명해주세요."
        
        else:
            return f"프로젝트에서 {file_path} 파일의 역할과 중요성을 분석하고, 이런 유형의 파일이 소프트웨어 개발 프로세스에서 어떤 가치를 제공하는지 설명해주세요."
        
        print(f"[QUESTION_GEN] 메타데이터 기반 질문 생성 완료: {len(questions)}/{count}개")
        return questions
    
