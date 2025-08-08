"""
Code Quality Agent

코드 품질을 분석하여 복잡도, 유지보수성, 디자인 패턴 등을 평가하는 LangGraph 에이전트
"""

import re
import ast
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI  # Replaced with Gemini

from app.core.config import settings
from app.core.gemini_client import get_gemini_llm


@dataclass
class QualityState:
    """코드 품질 분석 상태를 관리하는 데이터 클래스"""
    files: List[Dict[str, Any]]
    complexity_scores: Optional[Dict[str, float]] = None
    design_patterns: Optional[Dict[str, Any]] = None
    maintainability_score: Optional[float] = None
    test_coverage: Optional[float] = None
    code_smells: Optional[List[Dict[str, Any]]] = None
    quality_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CodeQualityAgent:
    """코드 품질 분석 에이전트"""
    
    def __init__(self):
        # Google Gemini LLM 초기화
        self.llm = get_gemini_llm()
        if self.llm:
            # Gemini에 맞는 설정 조정
            self.llm.temperature = 0  # 일관된 요법 분석을 위해
            print("[CODE_QUALITY] Google Gemini LLM initialized successfully")
        else:
            print("[CODE_QUALITY] Warning: Gemini LLM not available, using pattern-based analysis only")
        
        # 디자인 패턴 감지 패턴들
        self.pattern_signatures = {
            "singleton": [
                r"private\s+static\s+\w*instance",
                r"public\s+static\s+\w*getInstance",
                r"static\s+getInstance\s*\(",
                r"__new__.*cls\._instance",
                r"class\s+\w+.*:\s*\n\s*_instance\s*="
            ],
            "factory": [
                r"class\s+\w*Factory",
                r"def\s+create_\w+",
                r"function\s+create\w+",
                r"static\s+create\w*\("
            ],
            "observer": [
                r"interface\s+\w*Observer",
                r"def\s+notify",
                r"addEventListener",
                r"on\w+\s*\("
            ],
            "strategy": [
                r"interface\s+\w*Strategy",
                r"abstract.*strategy",
                r"def\s+execute.*strategy"
            ],
            "decorator": [
                r"@\w+",
                r"def\s+\w+\(.*func.*\):",
                r"function\s+\w+\(.*fn.*\)"
            ],
            "mvc": [
                r"class\s+\w*Controller",
                r"class\s+\w*Model",
                r"class\s+\w*View",
                r"def\s+render",
                r"def\s+update.*model"
            ]
        }
        
        # 코드 스멜 패턴들
        self.code_smell_patterns = {
            "long_method": {
                "pattern": r"def\s+\w+.*?(?=\n\s*def|\n\s*class|$)",
                "threshold": 50  # 50줄 이상
            },
            "large_class": {
                "pattern": r"class\s+\w+.*?(?=\nclass|\n$)",
                "threshold": 500  # 500줄 이상
            },
            "duplicate_code": {
                "pattern": r"(.{50,})",  # 50자 이상 동일한 패턴
                "threshold": 2  # 2번 이상 반복
            },
            "magic_numbers": {
                "pattern": r"\b(?<![\w.])\d{2,}\b(?![\w.])",
                "threshold": 5  # 5개 이상의 매직 넘버
            },
            "deep_nesting": {
                "pattern": r"(\s{12,})(if|for|while|try)",  # 3단계 이상 중첩
                "threshold": 1
            }
        }
    
    async def analyze_code_quality(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """코드 품질 전체 분석 수행"""
        
        # 분석 상태 초기화
        state = QualityState(files=files)
        
        try:
            # 1. 복잡도 분석
            state.complexity_scores = await self._analyze_complexity(files)
            
            # 2. 디자인 패턴 감지
            state.design_patterns = await self._detect_design_patterns(files)
            
            # 3. 유지보수성 점수 계산
            state.maintainability_score = await self._calculate_maintainability(files, state.complexity_scores)
            
            # 4. 테스트 커버리지 추정
            state.test_coverage = await self._estimate_test_coverage(files)
            
            # 5. 코드 스멜 감지
            state.code_smells = await self._detect_code_smells(files)
            
            # 6. 결과 종합
            state.quality_result = self._compile_quality_results(state)
            
            return state.quality_result
            
        except Exception as e:
            state.error = str(e)
            return {
                "success": False,
                "error": state.error,
                "complexity_score": 5.0,
                "maintainability": 5.0,
                "test_coverage": 0.0
            }
    
    async def detect_patterns(self, code_content: str) -> Dict[str, Dict[str, float]]:
        """단일 코드에서 디자인 패턴 감지"""
        patterns = {}
        
        for pattern_name, signatures in self.pattern_signatures.items():
            confidence = 0.0
            matches = 0
            
            for signature in signatures:
                if re.search(signature, code_content, re.IGNORECASE | re.MULTILINE):
                    matches += 1
                    confidence += 0.3
            
            if matches > 0:
                # 패턴별 가중치 적용
                if pattern_name == "singleton" and matches >= 2:
                    confidence = min(confidence * 1.5, 1.0)
                elif pattern_name == "mvc" and matches >= 3:
                    confidence = min(confidence * 1.2, 1.0)
                
                patterns[pattern_name] = {
                    "confidence": round(min(confidence, 1.0), 2),
                    "matches": matches
                }
        
        return patterns
    
    async def calculate_complexity(self, code_content: str) -> float:
        """단일 코드의 순환 복잡도 계산"""
        
        # 복잡도를 증가시키는 패턴들
        complexity_patterns = [
            r"\bif\b",           # if문
            r"\belif\b",         # elif문  
            r"\belse\b",         # else문
            r"\bfor\b",          # for 루프
            r"\bwhile\b",        # while 루프
            r"\btry\b",          # try-catch
            r"\bexcept\b",       # except
            r"\bfinally\b",      # finally
            r"\bswitch\b",       # switch문
            r"\bcase\b",         # case문
            r"&&|\|\|",          # 논리 연산자
            r"\?\s*.*\s*:",      # 삼항 연산자
            r"\bthrow\b",        # 예외 발생
            r"\breturn\b.*\bif\b" # 조건부 return
        ]
        
        complexity = 1  # 기본 복잡도
        
        for pattern in complexity_patterns:
            matches = len(re.findall(pattern, code_content, re.IGNORECASE))
            complexity += matches
        
        # 중첩 레벨 추가 가중치
        nesting_levels = self._calculate_nesting_depth(code_content)
        complexity += nesting_levels * 0.5
        
        return round(complexity, 2)
    
    async def _analyze_complexity(self, files: List[Dict[str, Any]]) -> Dict[str, float]:
        """각 파일의 복잡도 분석"""
        complexity_scores = {}
        
        for file_info in files:
            file_path = file_info["path"]
            content = file_info.get("content", "")
            
            if content:
                complexity = await self.calculate_complexity(content)
                complexity_scores[file_path] = complexity
        
        return complexity_scores
    
    async def _detect_design_patterns(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """모든 파일에서 디자인 패턴 감지"""
        all_patterns = {}
        pattern_counts = {}
        
        for file_info in files:
            content = file_info.get("content", "")
            if content:
                file_patterns = await self.detect_patterns(content)
                
                for pattern_name, pattern_info in file_patterns.items():
                    if pattern_name not in all_patterns:
                        all_patterns[pattern_name] = {
                            "confidence": 0.0,
                            "files": [],
                            "total_matches": 0
                        }
                    
                    all_patterns[pattern_name]["confidence"] = max(
                        all_patterns[pattern_name]["confidence"],
                        pattern_info["confidence"]
                    )
                    all_patterns[pattern_name]["files"].append(file_info["path"])
                    all_patterns[pattern_name]["total_matches"] += pattern_info["matches"]
        
        return all_patterns
    
    async def _calculate_maintainability(self, files: List[Dict[str, Any]], complexity_scores: Dict[str, float]) -> float:
        """유지보수성 점수 계산"""
        
        if not files:
            return 5.0
        
        factors = []
        
        # 1. 평균 복잡도 (낮을수록 좋음)
        avg_complexity = sum(complexity_scores.values()) / len(complexity_scores) if complexity_scores else 5.0
        complexity_factor = max(0, 10 - (avg_complexity - 1) * 2)  # 1-10 범위
        factors.append(complexity_factor)
        
        # 2. 파일 크기 (작을수록 좋음)
        total_lines = sum(len(f.get("content", "").split("\n")) for f in files)
        avg_file_size = total_lines / len(files)
        size_factor = max(0, 10 - (avg_file_size / 50))  # 50줄당 1점 감소
        factors.append(size_factor)
        
        # 3. 주석 비율 (높을수록 좋음)
        comment_ratio = self._calculate_comment_ratio(files)
        comment_factor = min(comment_ratio * 20, 10)  # 5% 주석 = 1점
        factors.append(comment_factor)
        
        # 4. 함수/메서드 평균 길이
        avg_function_length = self._calculate_avg_function_length(files)
        function_factor = max(0, 10 - (avg_function_length / 10))
        factors.append(function_factor)
        
        # 평균 계산
        maintainability = sum(factors) / len(factors)
        return round(maintainability, 2)
    
    async def _estimate_test_coverage(self, files: List[Dict[str, Any]]) -> float:
        """테스트 커버리지 추정"""
        
        test_files = []
        source_files = []
        
        for file_info in files:
            path = file_info["path"].lower()
            
            if any(keyword in path for keyword in ["test", "spec", "__test__", ".test.", ".spec."]):
                test_files.append(file_info)
            elif any(path.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go"]):
                source_files.append(file_info)
        
        if not source_files:
            return 0.0
        
        # 기본 커버리지 계산 (테스트 파일 존재 여부)
        base_coverage = min(len(test_files) / len(source_files) * 50, 50)  # 최대 50%
        
        # 테스트 코드 품질 추가 점수
        test_quality_bonus = 0.0
        if test_files:
            for test_file in test_files:
                content = test_file.get("content", "")
                # 테스트 패턴 검색
                test_patterns = len(re.findall(r"(test_\w+|it\(|describe\(|@Test)", content, re.IGNORECASE))
                test_quality_bonus += min(test_patterns * 2, 20)  # 최대 20% 추가
        
        total_coverage = min(base_coverage + test_quality_bonus, 100)
        return round(total_coverage, 2)
    
    async def _detect_code_smells(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """코드 스멜 감지"""
        code_smells = []
        
        for file_info in files:
            content = file_info.get("content", "")
            file_path = file_info["path"]
            
            if not content:
                continue
            
            # 긴 메서드 감지
            methods = re.findall(self.code_smell_patterns["long_method"]["pattern"], content, re.DOTALL)
            for method in methods:
                lines = len(method.split("\n"))
                if lines > self.code_smell_patterns["long_method"]["threshold"]:
                    code_smells.append({
                        "type": "long_method",
                        "file": file_path,
                        "severity": "medium",
                        "description": f"긴 메서드 감지 ({lines}줄)",
                        "line_count": lines
                    })
            
            # 매직 넘버 감지
            magic_numbers = re.findall(self.code_smell_patterns["magic_numbers"]["pattern"], content)
            if len(magic_numbers) >= self.code_smell_patterns["magic_numbers"]["threshold"]:
                code_smells.append({
                    "type": "magic_numbers",
                    "file": file_path,
                    "severity": "low",
                    "description": f"매직 넘버 과다 사용 ({len(magic_numbers)}개)",
                    "count": len(magic_numbers)
                })
            
            # 깊은 중첩 감지
            deep_nesting = re.findall(self.code_smell_patterns["deep_nesting"]["pattern"], content)
            if len(deep_nesting) > 0:
                code_smells.append({
                    "type": "deep_nesting",
                    "file": file_path,
                    "severity": "high",
                    "description": f"과도한 중첩 구조 ({len(deep_nesting)}개 위치)",
                    "count": len(deep_nesting)
                })
        
        return code_smells
    
    def _calculate_nesting_depth(self, code_content: str) -> int:
        """코드의 최대 중첩 깊이 계산"""
        lines = code_content.split("\n")
        max_depth = 0
        current_depth = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            
            # 들여쓰기 계산
            indent = len(line) - len(line.lstrip())
            depth = indent // 4  # 4칸 들여쓰기 기준
            
            if any(keyword in stripped for keyword in ["if", "for", "while", "try", "def", "class", "with"]):
                current_depth = depth + 1
                max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _calculate_comment_ratio(self, files: List[Dict[str, Any]]) -> float:
        """주석 비율 계산"""
        total_lines = 0
        comment_lines = 0
        
        for file_info in files:
            content = file_info.get("content", "")
            lines = content.split("\n")
            total_lines += len(lines)
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or "\"\"\"" in stripped:
                    comment_lines += 1
        
        return comment_lines / total_lines if total_lines > 0 else 0.0
    
    def _calculate_avg_function_length(self, files: List[Dict[str, Any]]) -> float:
        """평균 함수 길이 계산"""
        total_functions = 0
        total_length = 0
        
        function_patterns = [
            r"def\s+\w+.*?(?=\n\s*def|\n\s*class|$)",  # Python
            r"function\s+\w+.*?(?=\nfunction|\n}|$)",   # JavaScript
            r"public\s+\w+\s+\w+\s*\(.*?\)\s*{.*?(?=\n\s*public|\n\s*private|\n})"  # Java
        ]
        
        for file_info in files:
            content = file_info.get("content", "")
            
            for pattern in function_patterns:
                functions = re.findall(pattern, content, re.DOTALL)
                for func in functions:
                    total_functions += 1
                    total_length += len(func.split("\n"))
        
        return total_length / total_functions if total_functions > 0 else 0.0
    
    def _compile_quality_results(self, state: QualityState) -> Dict[str, Any]:
        """품질 분석 결과 종합"""
        
        # 전체 복잡도 점수 계산
        avg_complexity = sum(state.complexity_scores.values()) / len(state.complexity_scores) if state.complexity_scores else 5.0
        
        return {
            "success": True,
            "complexity_score": round(min(avg_complexity, 10), 2),
            "maintainability": state.maintainability_score or 5.0,
            "test_coverage": state.test_coverage or 0.0,
            "design_patterns": state.design_patterns or {},
            "code_smells": state.code_smells or [],
            "file_complexity": state.complexity_scores or {},
            "analysis_summary": self._generate_quality_summary(state),
            "recommendations": self._generate_recommendations(state)
        }
    
    def _generate_quality_summary(self, state: QualityState) -> str:
        """품질 분석 요약 생성"""
        complexity = sum(state.complexity_scores.values()) / len(state.complexity_scores) if state.complexity_scores else 5.0
        maintainability = state.maintainability_score or 5.0
        test_coverage = state.test_coverage or 0.0
        
        summary = f"코드 복잡도: {complexity:.1f}/10, "
        summary += f"유지보수성: {maintainability:.1f}/10, "
        summary += f"테스트 커버리지: {test_coverage:.1f}%. "
        
        if state.design_patterns:
            patterns = list(state.design_patterns.keys())[:3]
            summary += f"감지된 패턴: {', '.join(patterns)}."
        
        return summary
    
    def _generate_recommendations(self, state: QualityState) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 복잡도 기반 권장사항
        avg_complexity = sum(state.complexity_scores.values()) / len(state.complexity_scores) if state.complexity_scores else 5.0
        if avg_complexity > 7:
            recommendations.append("메서드를 더 작은 단위로 분리하여 복잡도를 낮이세요.")
        
        # 테스트 커버리지 기반 권장사항
        if state.test_coverage < 50:
            recommendations.append("테스트 커버리지를 높이기 위해 단위 테스트를 추가하세요.")
        
        # 유지보수성 기반 권장사항
        if state.maintainability_score < 6:
            recommendations.append("코드 주석을 추가하고 함수명을 더 명확하게 작성하세요.")
        
        # 코드 스멜 기반 권장사항
        if state.code_smells:
            smell_types = {smell["type"] for smell in state.code_smells}
            if "deep_nesting" in smell_types:
                recommendations.append("중첩된 조건문을 Early Return 패턴으로 개선하세요.")
            if "magic_numbers" in smell_types:
                recommendations.append("매직 넘버를 상수로 정의하여 가독성을 높이세요.")
        
        return recommendations