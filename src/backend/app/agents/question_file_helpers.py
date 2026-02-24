"""
Question File Helpers

파일 관련 처리 및 분석 유틸리티
"""

import re
from typing import Dict, List


class QuestionFileHelpers:
    """파일 관련 처리 유틸리티"""

    def _infer_language_from_path(self, file_path: str) -> str:
        """파일 경로에서 언어 추론"""
        if not file_path:
            return "unknown"

        extension = file_path.split('.')[-1].lower() if '.' in file_path else ""

        language_map = {
            'py': 'python',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'java': 'java',
            'kt': 'kotlin',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'swift': 'swift',
            'dart': 'dart',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'sass': 'sass',
            'md': 'markdown',
            'sh': 'shell',
            'sql': 'sql'
        }

        return language_map.get(extension, extension or "unknown")

    def _determine_file_importance(self, file_path: str, file_content: str) -> str:
        """파일의 중요도를 자동으로 판단"""

        # 파일명 기반 중요도
        filename = file_path.lower()

        # 최고 우선순위 파일들
        if any(name in filename for name in ["main", "app", "index", "server", "config", "settings"]):
            return "very_high"

        # 높은 우선순위 파일들
        if any(name in filename for name in ["controller", "service", "model", "handler", "router", "api"]):
            return "high"

        # 중간 우선순위 파일들
        if any(name in filename for name in ["util", "helper", "component", "view", "template"]):
            return "medium"

        # 파일 내용 기반 중요도 (실제 내용이 있는 경우)
        if file_content and len(file_content) > 100:
            # 클래스나 함수가 많이 정의된 파일
            class_count = len(re.findall(r'\bclass\s+\w+', file_content, re.IGNORECASE))
            function_count = len(re.findall(r'\b(def|function|async\s+function)\s+\w+', file_content, re.IGNORECASE))

            if class_count >= 3 or function_count >= 5:
                return "high"
            elif class_count >= 1 or function_count >= 2:
                return "medium"

        return "low"

    def _categorize_file_type(self, file_path: str) -> str:
        """파일 유형 분류"""

        filename = file_path.lower()

        # 설정 파일
        if any(name in filename for name in ["config", "setting", "env", "docker", "package.json", "requirements"]):
            return "configuration"

        # 컨트롤러
        if "controller" in filename or "handler" in filename:
            return "controller"

        # 모델/엔티티
        if "model" in filename or "entity" in filename or "schema" in filename:
            return "model"

        # 서비스/비즈니스 로직
        if "service" in filename or "business" in filename:
            return "service"

        # 유틸리티
        if "util" in filename or "helper" in filename:
            return "utility"

        # 라우터/API
        if "router" in filename or "route" in filename or "api" in filename:
            return "router"

        # 컴포넌트 (프론트엔드)
        if "component" in filename or "view" in filename:
            return "component"

        # 메인 진입점
        if any(name in filename for name in ["main", "app", "index", "server"]):
            return "main"

        return "general"

    def _estimate_code_complexity(self, file_content: str) -> float:
        """코드 복잡도 추정"""

        if not file_content or len(file_content.strip()) < 10:
            return 1.0

        # 기본 복잡도 지표들
        lines = file_content.split('\n')
        line_count = len([line for line in lines if line.strip()])

        # 제어 구조 패턴 카운트
        control_patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\btry\b', r'\bcatch\b', r'\bswitch\b', r'\bcase\b'
        ]

        control_count = sum(len(re.findall(pattern, file_content, re.IGNORECASE)) for pattern in control_patterns)

        # 함수/클래스 정의 카운트
        function_count = len(re.findall(r'\b(def|function|async\s+function)\s+\w+', file_content, re.IGNORECASE))
        class_count = len(re.findall(r'\bclass\s+\w+', file_content, re.IGNORECASE))

        # 복잡도 계산 (1-10 스케일)
        complexity = 1.0
        complexity += min(line_count / 50, 3.0)  # 줄 수 기반 (최대 3점)
        complexity += min(control_count / 10, 2.0)  # 제어 구조 기반 (최대 2점)
        complexity += min(function_count / 5, 2.0)  # 함수 수 기반 (최대 2점)
        complexity += min(class_count / 2, 2.0)  # 클래스 수 기반 (최대 2점)

        return min(complexity, 10.0)

    def _extract_code_elements(self, file_content: str, language: str) -> Dict[str, List[str]]:
        """코드에서 주요 요소들 추출"""

        elements = {
            "classes": [],
            "functions": [],
            "imports": [],
            "variables": [],
            "constants": []
        }

        if not file_content or len(file_content.strip()) < 10:
            return elements

        # 언어별 패턴 매칭
        if language in ["python"]:
            # 클래스 추출
            classes = re.findall(r'class\s+(\w+)', file_content, re.IGNORECASE)
            elements["classes"] = classes[:10]  # 최대 10개

            # 함수 추출
            functions = re.findall(r'def\s+(\w+)', file_content, re.IGNORECASE)
            elements["functions"] = functions[:15]  # 최대 15개

            # import 추출
            imports = re.findall(r'(?:from\s+\w+\s+)?import\s+(\w+)', file_content, re.IGNORECASE)
            elements["imports"] = imports[:10]

        elif language in ["javascript", "typescript"]:
            # 클래스 추출
            classes = re.findall(r'class\s+(\w+)', file_content, re.IGNORECASE)
            elements["classes"] = classes[:10]

            # 함수 추출 (function 선언과 화살표 함수)
            functions = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\()', file_content, re.IGNORECASE)
            elements["functions"] = [f[0] or f[1] for f in functions if f[0] or f[1]][:15]

            # import 추출
            imports = re.findall(r'import\s+(?:\{[^}]*\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', file_content)
            elements["imports"] = imports[:10]

        elif language in ["java"]:
            # 클래스 추출
            classes = re.findall(r'(?:public\s+)?class\s+(\w+)', file_content, re.IGNORECASE)
            elements["classes"] = classes[:10]

            # 메서드 추출
            functions = re.findall(r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(', file_content, re.IGNORECASE)
            elements["functions"] = functions[:15]

        return elements

    def _get_files_for_question_index(self, all_snippets: List[Dict], question_index: int) -> List[Dict]:
        """질문 인덱스에 따라 다른 파일 세트 반환 - 순환 선택으로 다양성 확보"""

        print(f"[QUESTION_GEN] 파일 선택 다양성 로직 시작 - 질문 {question_index + 1}번")

        if not all_snippets:
            print(f"[QUESTION_GEN] 경고: 사용 가능한 파일이 없습니다.")
            return []

        # 파일 타입별로 그룹화
        file_groups = {}
        for snippet in all_snippets:
            file_path = snippet["metadata"].get("file_path", "").lower()

            # 더 세밀한 파일 타입 분류
            if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                if 'config' in file_path or 'babel' in file_path:
                    file_type = 'build_config'
                elif 'test' in file_path or 'spec' in file_path:
                    file_type = 'test'
                else:
                    file_type = 'javascript'
            elif file_path.endswith(('.py', '.pyi')):
                if 'test' in file_path:
                    file_type = 'test'
                else:
                    file_type = 'python'
            elif file_path.endswith(('.json', '.yml', '.yaml', '.toml')):
                file_type = 'config'
            elif file_path.endswith(('.md', '.rst', '.txt')):
                file_type = 'documentation'
            elif file_path.endswith(('.html', '.css', '.scss')):
                file_type = 'frontend'
            else:
                file_type = 'general'

            if file_type not in file_groups:
                file_groups[file_type] = []
            file_groups[file_type].append(snippet)

        print(f"[QUESTION_GEN] 파일 그룹화 완료: {list(file_groups.keys())}")
        for group, files in file_groups.items():
            print(f"[QUESTION_GEN]   - {group}: {len(files)}개")

        # 순환 선택: 파일 인덱스를 순환하여 선택 (다양성 확보)
        total_files = len(all_snippets)
        if total_files == 0:
            return []

        # 우선순위 타입 정의 (질문 인덱스별로)
        priority_types_list = [
            ['config', 'build_config', 'python', 'javascript', 'documentation'],  # 1번 질문
            ['python', 'javascript', 'frontend', 'build_config', 'config'],       # 2번 질문
            ['documentation', 'test', 'frontend', 'general', 'config'],           # 3번 질문
            ['javascript', 'python', 'test', 'build_config', 'general'],          # 4번 질문
            ['frontend', 'config', 'documentation', 'python', 'javascript'],     # 5번 질문
            ['test', 'general', 'build_config', 'documentation', 'frontend'],    # 6번 질문
            ['general', 'python', 'config', 'test', 'javascript'],               # 7번 질문
            ['build_config', 'frontend', 'documentation', 'general', 'python'],  # 8번 질문
            ['config', 'test', 'javascript', 'frontend', 'documentation']        # 9번 질문
        ]

        # 질문 인덱스에 맞는 우선순위 타입 선택 (순환)
        priority_types = priority_types_list[question_index % len(priority_types_list)]
        print(f"[QUESTION_GEN] {question_index + 1}번 질문 - 우선순위 타입: {priority_types}")

        # 선택된 파일을 저장할 리스트
        selected_file = None

        # 1. 우선순위 타입에서 해당 인덱스의 파일 선택
        for file_type in priority_types:
            if file_type in file_groups and file_groups[file_type]:
                group_files = file_groups[file_type]
                # 중요도와 복잡도로 정렬
                group_files.sort(key=lambda f: (
                    {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1}.get(f["metadata"].get("importance", "low"), 1),
                    f["metadata"].get("complexity", 1.0)
                ), reverse=True)

                # 해당 타입에서 순환 선택
                file_index = question_index % len(group_files)
                selected_file = group_files[file_index]
                print(f"[QUESTION_GEN]   우선순위 선택: {selected_file['metadata'].get('file_path')} ({file_type}, 인덱스: {file_index})")
                break

        # 2. 우선순위 타입에서 선택되지 않은 경우 전체에서 순환 선택
        if not selected_file:
            # 전체 파일에서 순환 선택
            sorted_files = sorted(all_snippets, key=lambda f: (
                {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1}.get(f["metadata"].get("importance", "low"), 1),
                f["metadata"].get("complexity", 1.0)
            ), reverse=True)

            file_index = question_index % len(sorted_files)
            selected_file = sorted_files[file_index]
            print(f"[QUESTION_GEN]   전체에서 순환 선택: {selected_file['metadata'].get('file_path')} (인덱스: {file_index})")

        # 최종 선택된 파일 로깅
        if selected_file:
            file_path = selected_file["metadata"].get("file_path", "unknown")
            importance = selected_file["metadata"].get("importance", "unknown")
            has_content = selected_file["metadata"].get("has_real_content", False)
            print(f"[QUESTION_GEN] 최종 선택된 파일: {file_path} (중요도: {importance}, 실제내용: {has_content})")
            return [selected_file]
        else:
            print(f"[QUESTION_GEN] 경고: 선택된 파일이 없습니다.")
            return []

    def _select_diverse_files(self, available_files: List[Dict]) -> List[Dict]:
        """파일 유형 다양성을 고려한 파일 선택"""
        import random

        # 파일 경로 기반으로 더 정확한 유형 분류
        file_groups = {}
        for snippet in available_files:
            file_path = snippet["metadata"].get("file_path", "")

            # 파일 확장자와 경로로 세밀한 유형 분류
            if 'babel' in file_path.lower() or 'webpack' in file_path.lower():
                group = 'build_config'  # 빌드 설정 파일 우선순위 높임
            elif file_path.endswith(('.js', '.jsx')):
                group = 'javascript'
            elif file_path.endswith(('.ts', '.tsx')):
                group = 'typescript'
            elif file_path.endswith('.py'):
                group = 'python'
            elif file_path.endswith(('.json', '.yaml', '.yml')):
                group = 'config'
            elif file_path.endswith('.md'):
                group = 'docs'
            elif 'test' in file_path.lower():
                group = 'test'
            else:
                # 기존 file_type도 고려
                group = snippet["metadata"].get("file_type", "general")

            if group not in file_groups:
                file_groups[group] = []
            file_groups[group].append(snippet)

        # 그룹별 우선순위 설정 (빌드 설정 파일 등 중요한 설정 파일 우선)
        priority_groups = ['build_config', 'config', 'javascript', 'typescript', 'python', 'docs', 'test', 'general']

        selected = []
        for group in priority_groups:
            if group in file_groups:
                files = file_groups[group]
                # 중요도 순으로 정렬
                files.sort(key=lambda f: f["metadata"].get("importance", "low"), reverse=True)

                # 그룹별로 선택할 파일 수 조정
                select_count = 2 if group in ['build_config', 'config'] else 1
                type_selection = files[:select_count] if len(files) <= select_count else random.sample(files, select_count)
                selected.extend(type_selection)

                if len(selected) >= 5:  # 최대 5개까지
                    break

        return selected[:5]
