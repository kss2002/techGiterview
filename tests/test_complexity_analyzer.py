"""
고급 복잡도 메트릭 분석 시스템 테스트

TDD 방식으로 먼저 테스트를 작성하고, 이후 실제 구현을 진행합니다.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

# 구현된 모듈들
from app.services.complexity_analyzer import RuleBasedComplexityAnalyzer


class TestRuleBasedComplexityAnalyzer:
    """복잡도 분석기 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """테스트용 복잡도 분석기 인스턴스"""
        return RuleBasedComplexityAnalyzer()
    
    @pytest.fixture
    def simple_python_function(self):
        """간단한 Python 함수 샘플"""
        return """
def simple_function(x):
    if x > 0:
        return x * 2
    else:
        return 0
"""
    
    @pytest.fixture
    def complex_python_function(self):
        """복잡한 Python 함수 샘플"""
        return """
def complex_function(data, mode, threshold=10):
    result = []
    
    for item in data:
        if item is None:
            continue
        
        if mode == 'filter':
            if item > threshold:
                if isinstance(item, int):
                    result.append(item * 2)
                elif isinstance(item, float):
                    result.append(item * 1.5)
                else:
                    result.append(item)
            else:
                result.append(0)
        elif mode == 'transform':
            try:
                transformed = item ** 2
                if transformed > 100:
                    result.append(transformed)
                else:
                    result.append(item)
            except:
                result.append(None)
        else:
            result.append(item)
    
    return result
"""
    
    @pytest.fixture
    def javascript_function(self):
        """JavaScript 함수 샘플"""
        return """
function processUsers(users, filter) {
    const results = [];
    
    for (let i = 0; i < users.length; i++) {
        const user = users[i];
        
        if (!user || !user.active) {
            continue;
        }
        
        switch (filter) {
            case 'admin':
                if (user.role === 'admin') {
                    results.push(user);
                }
                break;
            case 'premium':
                if (user.subscription && user.subscription.type === 'premium') {
                    results.push(user);
                }
                break;
            default:
                results.push(user);
        }
    }
    
    return results;
}
"""
    
    @pytest.fixture
    def python_class(self):
        """Python 클래스 샘플"""
        return """
class UserManager:
    def __init__(self, database):
        self.db = database
        self.cache = {}
    
    def get_user(self, user_id):
        if user_id in self.cache:
            return self.cache[user_id]
        
        user = self.db.find_user(user_id)
        if user:
            self.cache[user_id] = user
            return user
        return None
    
    def create_user(self, data):
        if not data.get('email'):
            raise ValueError("Email required")
        
        if self.db.user_exists(data['email']):
            raise ValueError("User already exists")
        
        user = self.db.create_user(data)
        self.cache[user.id] = user
        return user
"""

    def test_calculate_cyclomatic_complexity_simple(self, analyzer, simple_python_function):
        """간단한 함수의 순환복잡도 계산 테스트"""
        # Given: 간단한 if-else 구조의 함수
        
        # When: 순환복잡도 계산
        result = asyncio.run(analyzer.analyze_code_complexity(simple_python_function, "python"))
        
        # Then: 복잡도가 올바르게 계산되어야 함
        assert "cyclomatic_complexity" in result
        # if-else 구조: 기본 1 + if 1 + else 1 = 3
        assert result["cyclomatic_complexity"] == 3

    def test_calculate_cyclomatic_complexity_complex(self, analyzer, complex_python_function):
        """복잡한 함수의 순환복잡도 계산 테스트"""
        # Given: 여러 제어문이 있는 복잡한 함수
        
        # When: 순환복잡도 계산
        result = asyncio.run(analyzer.analyze_code_complexity(complex_python_function, "python"))
        
        # Then: 높은 복잡도가 계산되어야 함
        assert result["cyclomatic_complexity"] > 5
        # for, if, elif, else, try-except 등 다수의 분기점

    def test_calculate_cyclomatic_complexity_javascript(self, analyzer, javascript_function):
        """JavaScript 함수의 순환복잡도 계산 테스트"""
        # Given: JavaScript 함수
        
        # When: 순환복잡도 계산
        result = asyncio.run(analyzer.analyze_code_complexity(javascript_function, "javascript"))
        
        # Then: 올바른 복잡도가 계산되어야 함
        assert result["cyclomatic_complexity"] > 3
        # for loop, if, switch-case 구조

    def test_count_lines_of_code(self, analyzer, complex_python_function):
        """코드 라인 수 계산 테스트"""
        # Given: 코드 샘플
        
        # When: 라인 메트릭 계산
        result = asyncio.run(analyzer.analyze_code_complexity(complex_python_function, "python"))
        
        # Then: 올바른 라인 수가 계산되어야 함
        assert "lines_of_code" in result
        assert result["lines_of_code"]["total"] > 0
        assert result["lines_of_code"]["executable"] > 0
        assert result["lines_of_code"]["blank"] >= 0
        assert result["lines_of_code"]["comment"] >= 0

    def test_analyze_function_complexity(self, analyzer, complex_python_function):
        """함수별 복잡도 분석 테스트"""
        # Given: 함수가 포함된 코드
        
        # When: 함수별 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(complex_python_function, "python"))
        
        # Then: 함수별 복잡도 정보가 포함되어야 함
        assert "function_complexity" in result
        assert len(result["function_complexity"]) > 0
        
        # 함수 정보 확인
        func_info = result["function_complexity"][0]
        assert "name" in func_info
        assert "complexity" in func_info
        assert "lines" in func_info

    def test_analyze_class_complexity(self, analyzer, python_class):
        """클래스별 복잡도 분석 테스트"""
        # Given: 클래스가 포함된 코드
        
        # When: 클래스별 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(python_class, "python"))
        
        # Then: 클래스별 복잡도 정보가 포함되어야 함
        assert "class_complexity" in result
        assert len(result["class_complexity"]) > 0
        
        # 클래스 정보 확인
        class_info = result["class_complexity"][0]
        assert "name" in class_info
        assert "complexity" in class_info
        assert "methods" in class_info
        assert "lines" in class_info

    def test_identify_complex_functions(self, analyzer, complex_python_function):
        """고복잡도 함수 식별 테스트"""
        # Given: 복잡한 함수들이 있는 코드
        
        # When: 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(complex_python_function, "python"))
        
        # When: 고복잡도 함수 식별
        complex_functions = analyzer.identify_complex_functions(result, threshold=5)
        
        # Then: 복잡한 함수가 식별되어야 함
        assert isinstance(complex_functions, list)
        if complex_functions:
            assert all("name" in func for func in complex_functions)
            assert all("complexity" in func for func in complex_functions)

    def test_calculate_maintainability_index(self, analyzer, complex_python_function):
        """유지보수성 지수 계산 테스트"""
        # Given: 코드 샘플
        
        # When: 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(complex_python_function, "python"))
        
        # Then: 유지보수성 지수가 계산되어야 함
        assert "maintainability_index" in result
        assert 0 <= result["maintainability_index"] <= 100

    def test_empty_code_handling(self, analyzer):
        """빈 코드 처리 테스트"""
        # Given: 빈 코드
        empty_code = ""
        
        # When: 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(empty_code, "python"))
        
        # Then: 기본값이 반환되어야 함
        assert result["cyclomatic_complexity"] == 0
        assert result["lines_of_code"]["total"] == 0

    def test_unsupported_language_handling(self, analyzer):
        """지원하지 않는 언어 처리 테스트"""
        # Given: 지원하지 않는 언어
        code = "some code in unknown language"
        language = "unknown"
        
        # When: 복잡도 분석
        result = asyncio.run(analyzer.analyze_code_complexity(code, language))
        
        # Then: 기본값이 반환되어야 함 (에러 없이)
        assert result["cyclomatic_complexity"] == 0
        assert result["lines_of_code"]["total"] > 0  # 라인 수는 언어와 무관하게 계산됨

    @pytest.mark.asyncio
    async def test_analyze_file_complexity_batch(self, analyzer):
        """파일별 복잡도 일괄 분석 테스트"""
        # Given: 여러 파일의 내용
        file_contents = {
            "src/simple.py": "def add(a, b): return a + b",
            "src/complex.py": """
def complex_func(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
            else:
                continue
    return x
""",
            "src/empty.py": ""
        }
        
        # When: 일괄 복잡도 분석
        results = await analyzer.analyze_files_complexity(file_contents)
        
        # Then: 각 파일의 복잡도가 분석되어야 함
        assert "src/simple.py" in results
        assert "src/complex.py" in results
        assert "src/empty.py" in results
        
        # simple.py는 낮은 복잡도
        assert results["src/simple.py"]["cyclomatic_complexity"] <= 2
        
        # complex.py는 높은 복잡도
        assert results["src/complex.py"]["cyclomatic_complexity"] > 2


class TestComplexityPatterns:
    """복잡도 패턴 인식 테스트"""
    
    def test_control_flow_detection(self):
        """제어문 감지 테스트"""
        # Given: 다양한 제어문을 포함한 코드
        code_samples = {
            "if_else": "if x > 0:\n    pass\nelse:\n    pass",
            "for_loop": "for i in range(10):\n    pass",
            "while_loop": "while True:\n    break",
            "try_except": "try:\n    pass\nexcept:\n    pass",
            "switch_case": "switch(x) {\n    case 1: break;\n    default: break;\n}"
        }
        
        # When: 제어문 패턴 감지
        analyzer = RuleBasedComplexityAnalyzer()
        
        for pattern_type, code in code_samples.items():
            # switch-case는 JavaScript로 테스트
            language = "javascript" if pattern_type == "switch_case" else "python"
            result = asyncio.run(analyzer.analyze_code_complexity(code, language))
            
            # Then: 제어문이 복잡도에 반영되어야 함
            assert result["cyclomatic_complexity"] > 1, f"{pattern_type} 패턴이 복잡도에 반영되지 않음"

    def test_nested_complexity_calculation(self):
        """중첩 구조 복잡도 계산 테스트"""
        # Given: 중첩된 제어문
        nested_code = """
def nested_function(data):
    for item in data:
        if item > 0:
            for sub in item.values():
                if sub is not None:
                    try:
                        result = process(sub)
                        if result:
                            return result
                    except Exception:
                        continue
    return None
"""
        
        # When: 복잡도 계산
        analyzer = RuleBasedComplexityAnalyzer()
        result = asyncio.run(analyzer.analyze_code_complexity(nested_code, "python"))
        
        # Then: 높은 복잡도가 계산되어야 함
        assert result["cyclomatic_complexity"] >= 8  # 여러 중첩된 제어문


class TestComplexityIntegration:
    """복잡도 분석 통합 테스트"""
    
    def test_integration_with_dependency_analysis(self):
        """의존성 분석과의 통합 테스트"""
        # Given: 복잡도와 의존성 메트릭
        complexity_metrics = {
            "src/main.py": {"cyclomatic_complexity": 15, "maintainability_index": 60},
            "src/auth.py": {"cyclomatic_complexity": 8, "maintainability_index": 75},
            "src/utils.py": {"cyclomatic_complexity": 3, "maintainability_index": 90}
        }
        
        dependency_centrality = {
            "src/main.py": 0.8,
            "src/auth.py": 0.6,
            "src/utils.py": 0.4
        }
        
        # When: 통합 위험도 점수 계산
        analyzer = RuleBasedComplexityAnalyzer()
        
        integrated_scores = analyzer.calculate_integrated_complexity_risk(
            complexity_metrics, dependency_centrality
        )
        
        # Then: 통합 점수가 계산되어야 함
        assert "src/main.py" in integrated_scores
        assert "src/auth.py" in integrated_scores
        assert "src/utils.py" in integrated_scores
        
        # main.py는 높은 복잡도 + 높은 중심성으로 가장 위험해야 함
        assert integrated_scores["src/main.py"] > integrated_scores["src/utils.py"]

    def test_complexity_summary_generation(self):
        """복잡도 요약 정보 생성 테스트"""
        # Given: 파일별 복잡도 메트릭
        complexity_data = {
            "file1.py": {
                "cyclomatic_complexity": 10,
                "lines_of_code": {"total": 100, "executable": 80},
                "function_complexity": [{"name": "func1", "complexity": 5}]
            },
            "file2.py": {
                "cyclomatic_complexity": 5,
                "lines_of_code": {"total": 50, "executable": 40},
                "function_complexity": [{"name": "func2", "complexity": 3}]
            }
        }
        
        # When: 요약 정보 생성
        analyzer = RuleBasedComplexityAnalyzer()
        summary = analyzer.generate_complexity_summary(complexity_data)
        
        # Then: 요약 통계가 올바르게 생성되어야 함
        assert "total_files" in summary
        assert "average_complexity" in summary
        assert "high_complexity_files" in summary
        assert "total_lines" in summary