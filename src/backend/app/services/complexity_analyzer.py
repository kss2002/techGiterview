"""
고급 복잡도 메트릭 분석 시스템

규칙 기반으로 코드의 순환복잡도, 라인 메트릭, 함수/클래스 복잡도를 계산합니다.
머신러닝이나 도메인 키워드 없이 순수 규칙과 패턴 매칭으로 동작합니다.
"""

import re
import ast
import asyncio
import math
import tempfile
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

try:
    import lizard
    LIZARD_AVAILABLE = True
except ImportError:
    LIZARD_AVAILABLE = False


class RuleBasedComplexityAnalyzer:
    """순수 규칙 기반 복잡도 분석기"""
    
    def __init__(self):
        # 순환복잡도 증가 패턴 정의
        self.complexity_patterns = {
            'python': {
                'conditional': [
                    r'\bif\b',
                    r'\belif\b',
                    r'\belse\b',
                ],
                'loops': [
                    r'\bfor\b',
                    r'\bwhile\b',
                ],
                'exception_handling': [
                    r'\btry\b',
                    r'\bexcept\b',
                    r'\bfinally\b',
                ],
                'logical_operators': [
                    r'\band\b',
                    r'\bor\b',
                ],
                'control_flow': [
                    r'\breturn\b',
                    r'\bbreak\b',
                    r'\bcontinue\b',
                    r'\byield\b',
                ]
            },
            'javascript': {
                'conditional': [
                    r'\bif\b',
                    r'\belse\b',
                    r'\?\s*[^:]+\s*:',  # ternary operator
                ],
                'loops': [
                    r'\bfor\b',
                    r'\bwhile\b',
                    r'\bdo\b',
                ],
                'switch': [
                    r'\bcase\b',
                    r'\bdefault\b',
                ],
                'exception_handling': [
                    r'\btry\b',
                    r'\bcatch\b',
                    r'\bfinally\b',
                ],
                'logical_operators': [
                    r'&&',
                    r'\|\|',
                ],
                'control_flow': [
                    r'\breturn\b',
                    r'\bbreak\b',
                    r'\bcontinue\b',
                ]
            },
            'java': {
                'conditional': [
                    r'\bif\b',
                    r'\belse\b',
                ],
                'loops': [
                    r'\bfor\b',
                    r'\bwhile\b',
                    r'\bdo\b',
                ],
                'switch': [
                    r'\bcase\b',
                    r'\bdefault\b',
                ],
                'exception_handling': [
                    r'\btry\b',
                    r'\bcatch\b',
                    r'\bfinally\b',
                ],
                'logical_operators': [
                    r'&&',
                    r'\|\|',
                ]
            }
        }
        
        # 함수/클래스 정의 패턴
        self.function_patterns = {
            'python': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'javascript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'java': r'(public|private|protected|static|\s)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        }
        
        self.class_patterns = {
            'python': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'javascript': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'java': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        }
    
    async def analyze_code_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """코드의 전체 복잡도 분석"""
        
        if not code or not code.strip():
            return self._empty_complexity_result()
        
        # Lizard를 사용한 고급 분석 (가능한 경우)
        lizard_result = None
        if LIZARD_AVAILABLE and language.lower() in ['python', 'javascript', 'java', 'c', 'cpp']:
            lizard_result = await self._analyze_with_lizard(code, language)
        
        # 기본 메트릭 계산
        if lizard_result:
            # Lizard 결과 우선 사용
            cyclomatic_complexity = lizard_result.get("average_ccn", 1)
            lines_metrics = {
                "total": lizard_result.get("total_lines", 0),
                "executable": lizard_result.get("code_lines", 0),
                "blank": lizard_result.get("total_lines", 0) - lizard_result.get("code_lines", 0),
                "comment": 0
            }
            function_complexity = lizard_result.get("functions", [])
        else:
            # 규칙 기반 분석 사용
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(code, language)
            lines_metrics = self._calculate_lines_of_code(code)
            function_complexity = self._analyze_function_complexity(code, language)
        
        class_complexity = self._analyze_class_complexity(code, language)
        maintainability_index = self._calculate_maintainability_index(
            cyclomatic_complexity, lines_metrics
        )
        
        result = {
            "cyclomatic_complexity": cyclomatic_complexity,
            "lines_of_code": lines_metrics,
            "function_complexity": function_complexity,
            "class_complexity": class_complexity,
            "maintainability_index": maintainability_index,
            "complexity_density": round(cyclomatic_complexity / max(lines_metrics["executable"], 1), 4),
            "language": language
        }
        
        # Lizard 추가 메트릭 포함
        if lizard_result:
            result["lizard_metrics"] = {
                "total_functions": lizard_result.get("function_count", 0),
                "average_ccn": lizard_result.get("average_ccn", 0),
                "average_token_count": lizard_result.get("average_token_count", 0),
                "average_nloc": lizard_result.get("average_nloc", 0)
            }
        
        return result
    
    async def _analyze_with_lizard(self, code: str, language: str) -> Optional[Dict[str, Any]]:
        """Lizard 도구를 사용한 고급 복잡도 분석"""
        
        if not LIZARD_AVAILABLE:
            return None
        
        try:
            # 파일 확장자 매핑
            extension_map = {
                'python': '.py',
                'javascript': '.js', 
                'java': '.java',
                'c': '.c',
                'cpp': '.cpp'
            }
            
            extension = extension_map.get(language.lower(), '.txt')
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Lizard로 분석
                analysis_result = lizard.analyze_file(temp_file_path)
                
                functions = []
                total_ccn = 0
                total_token_count = 0
                total_nloc = 0
                
                for function in analysis_result.function_list:
                    func_info = {
                        'name': function.name,
                        'complexity': function.cyclomatic_complexity,
                        'lines': function.nloc,
                        'start_line': function.start_line,
                        'token_count': function.token_count,
                        'parameters': len(function.parameters) if hasattr(function, 'parameters') else 0
                    }
                    functions.append(func_info)
                    
                    total_ccn += function.cyclomatic_complexity
                    total_token_count += function.token_count
                    total_nloc += function.nloc
                
                function_count = len(functions)
                
                return {
                    'total_lines': analysis_result.nloc,
                    'code_lines': analysis_result.nloc,
                    'function_count': function_count,
                    'functions': functions,
                    'average_ccn': round(total_ccn / max(function_count, 1), 2),
                    'average_token_count': round(total_token_count / max(function_count, 1), 2),
                    'average_nloc': round(total_nloc / max(function_count, 1), 2),
                    'total_ccn': total_ccn
                }
                
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Lizard analysis failed: {e}")
            return None
    
    def _calculate_cyclomatic_complexity(self, code: str, language: str) -> int:
        """순환복잡도 계산 (McCabe 방법론)"""
        
        if not code.strip():
            return 0
        
        patterns = self.complexity_patterns.get(language.lower(), {})
        if not patterns:
            return 0  # 지원하지 않는 언어는 0 복잡도
        
        # 기본 복잡도 (모든 함수는 최소 1의 복잡도)
        base_complexity = 1
        
        complexity = base_complexity
        
        # 각 패턴별로 복잡도 증가 계산
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = len(re.findall(pattern, code, re.MULTILINE | re.IGNORECASE))
                
                # 카테고리별 가중치 적용
                if category in ['conditional', 'loops']:
                    complexity += matches
                elif category == 'switch':
                    complexity += matches
                elif category == 'exception_handling':
                    complexity += matches
                elif category == 'logical_operators':
                    # 논리 연산자는 절반의 가중치
                    complexity += matches // 2
        
        return max(complexity, base_complexity)
    
    def _calculate_lines_of_code(self, code: str) -> Dict[str, int]:
        """코드 라인 수 메트릭 계산"""
        
        if not code:
            return {"total": 0, "executable": 0, "blank": 0, "comment": 0}
        
        lines = code.split('\n')
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        executable_lines = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                comment_lines += 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                comment_lines += 1
            else:
                # 인라인 주석 체크
                if '#' in stripped or '//' in stripped:
                    # 실제 코드가 있는지 확인
                    before_comment = stripped.split('#')[0].split('//')[0].strip()
                    if before_comment:
                        executable_lines += 1
                    else:
                        comment_lines += 1
                else:
                    executable_lines += 1
        
        return {
            "total": total_lines,
            "executable": executable_lines,
            "blank": blank_lines,
            "comment": comment_lines
        }
    
    def _analyze_function_complexity(self, code: str, language: str) -> List[Dict[str, Any]]:
        """함수별 복잡도 분석"""
        
        functions = []
        
        pattern = self.function_patterns.get(language.lower())
        if not pattern:
            return functions
        
        # 함수 정의 찾기
        function_matches = re.finditer(pattern, code, re.MULTILINE)
        
        for match in function_matches:
            function_name = match.group(1) if match.groups() else "unknown"
            start_pos = match.start()
            
            # 함수 본문 추출 (간단한 휴리스틱 사용)
            function_body = self._extract_function_body(code, start_pos, language)
            
            # 함수별 복잡도 계산
            func_complexity = self._calculate_cyclomatic_complexity(function_body, language)
            func_lines = self._calculate_lines_of_code(function_body)
            
            functions.append({
                "name": function_name,
                "complexity": func_complexity,
                "lines": func_lines["executable"],
                "start_line": code[:start_pos].count('\n') + 1
            })
        
        return functions
    
    def _analyze_class_complexity(self, code: str, language: str) -> List[Dict[str, Any]]:
        """클래스별 복잡도 분석"""
        
        classes = []
        
        pattern = self.class_patterns.get(language.lower())
        if not pattern:
            return classes
        
        # 클래스 정의 찾기
        class_matches = re.finditer(pattern, code, re.MULTILINE)
        
        for match in class_matches:
            class_name = match.group(1)
            start_pos = match.start()
            
            # 클래스 본문 추출
            class_body = self._extract_class_body(code, start_pos, language)
            
            # 클래스 내 메서드 분석
            methods = self._analyze_function_complexity(class_body, language)
            
            # 클래스 전체 복잡도 (메서드들의 합)
            total_complexity = sum(method["complexity"] for method in methods)
            class_lines = self._calculate_lines_of_code(class_body)
            
            classes.append({
                "name": class_name,
                "complexity": total_complexity,
                "methods": methods,
                "lines": class_lines["executable"],
                "start_line": code[:start_pos].count('\n') + 1
            })
        
        return classes
    
    def _extract_function_body(self, code: str, start_pos: int, language: str) -> str:
        """함수 본문 추출 (간단한 휴리스틱)"""
        
        lines = code[start_pos:].split('\n')
        if not lines:
            return ""
        
        # 첫 번째 줄 (함수 정의)
        function_line = lines[0]
        
        if language.lower() == 'python':
            # Python: 들여쓰기 기반으로 함수 본문 추출
            if len(lines) < 2:
                return function_line
            
            # 함수 본문의 들여쓰기 레벨 확인
            body_lines = [function_line]
            base_indent = None
            
            for i, line in enumerate(lines[1:], 1):
                if not line.strip():  # 빈 줄
                    body_lines.append(line)
                    continue
                
                # 들여쓰기 레벨 계산
                indent = len(line) - len(line.lstrip())
                
                if base_indent is None and line.strip():
                    base_indent = indent
                
                # 함수 본문이 끝났는지 확인
                if base_indent is not None and indent < base_indent and line.strip():
                    break
                
                body_lines.append(line)
        
        else:
            # JavaScript/Java: 중괄호 기반
            brace_count = 0
            body_lines = []
            
            for line in lines:
                body_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and '{' in function_line:
                    break
        
        return '\n'.join(body_lines)
    
    def _extract_class_body(self, code: str, start_pos: int, language: str) -> str:
        """클래스 본문 추출"""
        
        # 함수 본문 추출과 유사한 로직이지만 클래스에 특화
        return self._extract_function_body(code, start_pos, language)
    
    def _calculate_maintainability_index(self, complexity: int, lines_metrics: Dict[str, int]) -> float:
        """유지보수성 지수 계산 (Microsoft 방법론 기반)"""
        
        # Halstead Volume 근사치 (실제 계산 대신 라인 수 기반 추정)
        executable_lines = max(lines_metrics["executable"], 1)
        halstead_volume = executable_lines * math.log2(executable_lines + 1)
        
        # Maintainability Index 공식
        # MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        mi = (171 
              - 5.2 * math.log(max(halstead_volume, 1)) 
              - 0.23 * complexity 
              - 16.2 * math.log(max(executable_lines, 1)))
        
        # 0-100 범위로 정규화
        return max(0.0, min(100.0, mi))
    
    async def analyze_files_complexity(self, file_contents: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """여러 파일의 복잡도 일괄 분석"""
        
        results = {}
        
        for file_path, content in file_contents.items():
            # 파일 확장자로 언어 추정
            language = self._detect_language_from_extension(file_path)
            
            try:
                complexity_result = await self.analyze_code_complexity(content, language)
                results[file_path] = complexity_result
            except Exception as e:
                print(f"Failed to analyze complexity for {file_path}: {e}")
                results[file_path] = self._empty_complexity_result()
        
        return results
    
    def _detect_language_from_extension(self, file_path: str) -> str:
        """파일 확장자로 언어 감지"""
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        for ext, lang in extension_map.items():
            if file_path.lower().endswith(ext):
                return lang
        
        return 'unknown'
    
    def identify_complex_functions(self, complexity_result: Dict[str, Any], threshold: int = 10) -> List[Dict[str, Any]]:
        """고복잡도 함수 식별"""
        
        complex_functions = []
        
        for func in complexity_result.get("function_complexity", []):
            if func["complexity"] >= threshold:
                complex_functions.append(func)
        
        # 복잡도 순으로 정렬
        complex_functions.sort(key=lambda x: x["complexity"], reverse=True)
        
        return complex_functions
    
    def calculate_integrated_complexity_risk(
        self, 
        complexity_metrics: Dict[str, Dict[str, Any]], 
        dependency_centrality: Dict[str, float]
    ) -> Dict[str, float]:
        """복잡도와 의존성 중심성을 통합한 위험도 점수"""
        
        integrated_scores = {}
        
        for file_path in set(complexity_metrics.keys()) | set(dependency_centrality.keys()):
            complexity_data = complexity_metrics.get(file_path, {})
            centrality = dependency_centrality.get(file_path, 0.0)
            
            # 복잡도 위험도 계산
            cyclomatic = complexity_data.get("cyclomatic_complexity", 0)
            maintainability = complexity_data.get("maintainability_index", 100)
            
            # 복잡도 위험도 정규화 (0-1)
            complexity_risk = min(1.0, cyclomatic / 20.0)  # 20을 최대 복잡도로 가정
            maintainability_risk = (100 - maintainability) / 100.0
            
            # 통합 위험도: 복잡도 + 의존성 중심성 + 유지보수성
            integrated_score = (
                complexity_risk * 0.4 +
                centrality * 0.35 +
                maintainability_risk * 0.25
            )
            
            integrated_scores[file_path] = min(1.0, integrated_score)
        
        return integrated_scores
    
    def generate_complexity_summary(self, complexity_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """복잡도 분석 요약 정보 생성"""
        
        if not complexity_data:
            return {}
        
        # 전체 통계
        total_files = len(complexity_data)
        complexities = [data.get("cyclomatic_complexity", 0) for data in complexity_data.values()]
        total_lines = sum(data.get("lines_of_code", {}).get("total", 0) for data in complexity_data.values())
        executable_lines = sum(data.get("lines_of_code", {}).get("executable", 0) for data in complexity_data.values())
        
        # 평균 복잡도
        avg_complexity = sum(complexities) / max(total_files, 1)
        
        # 고복잡도 파일 식별 (평균의 2배 이상)
        high_complexity_threshold = max(10, avg_complexity * 2)
        high_complexity_files = [
            {"path": path, "complexity": data.get("cyclomatic_complexity", 0)}
            for path, data in complexity_data.items()
            if data.get("cyclomatic_complexity", 0) >= high_complexity_threshold
        ]
        
        # 복잡도 순으로 정렬
        high_complexity_files.sort(key=lambda x: x["complexity"], reverse=True)
        
        # 가장 복잡한 파일
        most_complex_file = None
        max_complexity = 0
        for path, data in complexity_data.items():
            complexity = data.get("cyclomatic_complexity", 0)
            if complexity > max_complexity:
                max_complexity = complexity
                most_complex_file = path
        
        return {
            "total_files": total_files,
            "average_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "high_complexity_files": high_complexity_files[:10],  # 상위 10개
            "total_lines": total_lines,
            "executable_lines": executable_lines,
            "most_complex_file": {
                "path": most_complex_file,
                "complexity": max_complexity
            },
            "complexity_distribution": {
                "low": len([c for c in complexities if c <= 5]),
                "medium": len([c for c in complexities if 5 < c <= 10]),
                "high": len([c for c in complexities if 10 < c <= 20]),
                "very_high": len([c for c in complexities if c > 20])
            }
        }
    
    def _empty_complexity_result(self) -> Dict[str, Any]:
        """빈 복잡도 결과 반환"""
        return {
            "cyclomatic_complexity": 0,
            "lines_of_code": {"total": 0, "executable": 0, "blank": 0, "comment": 0},
            "function_complexity": [],
            "class_complexity": [],
            "maintainability_index": 100.0,
            "complexity_density": 0.0,
            "language": "unknown"
        }