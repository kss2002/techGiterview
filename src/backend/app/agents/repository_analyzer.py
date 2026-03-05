"""
Repository Analyzer Agent

GitHub 저장소를 분석하여 기술 스택, 파일 구조, 중요도 등을 파악하는 LangGraph 에이전트
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.services.github_client import GitHubClient
from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
from app.core.config import settings
from app.core.gemini_client import get_gemini_llm


@dataclass
class AnalysisState:
    """분석 상태를 관리하는 데이터 클래스"""
    repo_url: str
    repo_info: Optional[Dict] = None
    file_tree: Optional[List[Dict]] = None
    languages: Optional[Dict] = None
    tech_stack: Optional[Dict] = None
    important_files: Optional[List[Dict]] = None
    complexity_score: Optional[float] = None
    smart_file_analysis: Optional[Dict] = None
    analysis_result: Optional[Dict] = None
    error: Optional[str] = None


class RepositoryAnalyzer:
    """저장소 분석 에이전트"""
    
    def __init__(self, repo_path: str = "."):
        self.github_client = GitHubClient()
        self.smart_file_analyzer = SmartFileImportanceAnalyzer(repo_path)
        
        # Google Gemini LLM 초기화
        self.llm = get_gemini_llm()
        if self.llm:
            print("[REPO_ANALYZER] Google Gemini LLM initialized successfully")
        else:
            print("[REPO_ANALYZER] Warning: Gemini LLM not available, using pattern-based analysis only")
        
        # 기술 스택 감지 패턴
        self.tech_patterns = {
            # Frontend Frameworks
            "react": [r"react", r"jsx", r"tsx"],
            "vue": [r"vue", r"\.vue$"],
            "angular": [r"angular", r"@angular"],
            "svelte": [r"svelte"],
            
            # Backend Frameworks  
            "django": [r"django", r"manage\.py"],
            "flask": [r"flask", r"app\.py"],
            "fastapi": [r"fastapi", r"uvicorn"],
            "express": [r"express", r"app\.js", r"server\.js"],
            "spring": [r"spring", r"\.java$", r"pom\.xml"],
            
            # Languages
            "javascript": [r"\.js$", r"package\.json"],
            "typescript": [r"\.ts$", r"\.tsx$", r"tsconfig\.json"],
            "python": [r"\.py$", r"requirements\.txt", r"setup\.py"],
            "java": [r"\.java$", r"pom\.xml", r"build\.gradle"],
            "go": [r"\.go$", r"go\.mod"],
            "rust": [r"\.rs$", r"Cargo\.toml"],
            "php": [r"\.php$", r"composer\.json"],
            
            # Databases
            "postgresql": [r"postgres", r"psycopg2"],
            "mysql": [r"mysql", r"pymysql"],
            "mongodb": [r"mongo", r"mongoose"],
            "redis": [r"redis"],
            
            # Tools & Configs
            "docker": [r"Dockerfile", r"docker-compose"],
            "kubernetes": [r"\.yaml$", r"\.yml$", r"k8s"],
            "webpack": [r"webpack"],
            "vite": [r"vite"],
            "jest": [r"jest", r"\.test\."],
            "pytest": [r"pytest", r"test_.*\.py"],
        }
    
    async def analyze_repository(self, repo_url: str, api_keys: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """저장소 전체 분석 수행"""
        
        print(f"[REPO_ANALYZER] ========== 저장소 분석 시작 ==========")
        print(f"[REPO_ANALYZER] 대상 저장소: {repo_url}")
        print(f"[REPO_ANALYZER] API 키 제공: {api_keys is not None}")
        
        # API 키를 GitHubClient에 전달
        if api_keys and "github_token" in api_keys:
            self.github_client.set_token(api_keys["github_token"])
            print(f"[REPO_ANALYZER] GitHub 토큰 설정됨")
        
        # 분석 상태 초기화
        state = AnalysisState(repo_url=repo_url)
        analysis_start_time = time.time()
        
        try:
            # GitHub 클라이언트를 컨텍스트 매니저로 사용
            async with self.github_client as client:
                # 1. 기본 정보 수집
                print(f"[REPO_ANALYZER] 1단계: 저장소 기본 정보 수집")
                step_start = time.time()
                state.repo_info = await client.get_repository_info(repo_url)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 1단계 완료 ({step_time:.2f}초): {state.repo_info.get('name', 'unknown')} - {state.repo_info.get('language', 'unknown')}, {state.repo_info.get('size', 0):,}KB")
                
                # 2. 언어 통계 수집
                print(f"[REPO_ANALYZER] 2단계: 언어 통계 수집")
                step_start = time.time()
                state.languages = await client.get_languages(repo_url)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 2단계 완료 ({step_time:.2f}초): {len(state.languages)}개 언어 발견")
                
                # 3. 파일 트리 수집 (루트 레벨)
                print(f"[REPO_ANALYZER] 3단계: 파일 트리 수집 (루트 레벨)")
                step_start = time.time()
                state.file_tree = await client.get_file_tree(repo_url)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 3단계 완료 ({step_time:.2f}초): {len(state.file_tree)}개 파일/디렉토리 발견")
                
                # 4. 중요 파일 선택 및 내용 수집 (SmartFileImportanceAnalyzer 활용)
                print(f"[REPO_ANALYZER] 4단계: 중요 파일 선택 및 내용 수집 (스마트 분석)")
                step_start = time.time()
                state.important_files = await self._select_important_files(client, repo_url, state.file_tree, target_count=12)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 4단계 완료 ({step_time:.2f}초): {len(state.important_files)}개 중요 파일 선정")
                
                # 5. 기술 스택 식별
                print(f"[REPO_ANALYZER] 5단계: 기술 스택 식별")
                step_start = time.time()
                state.tech_stack = await self._identify_tech_stack(state.important_files, state.languages)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 5단계 완료 ({step_time:.2f}초): {len(state.tech_stack)}개 기술 스택 식별")
                
                # 6. 복잡도 점수 계산
                print(f"[REPO_ANALYZER] 6단계: 복잡도 점수 계산")
                step_start = time.time()
                state.complexity_score = await self._calculate_complexity_score(state)
                step_time = time.time() - step_start
                print(f"[REPO_ANALYZER] 6단계 완료 ({step_time:.2f}초): 복잡도 점수 {state.complexity_score:.2f}")
                
                # 7. 스마트 파일 중요도 분석
                print(f"[REPO_ANALYZER] 7단계: 스마트 파일 중요도 분석")
                step_start = time.time()
                state.smart_file_analysis = await self._analyze_file_importance(repo_url, state)
                step_time = time.time() - step_start
                smart_files_count = len(state.smart_file_analysis.get('files', [])) if state.smart_file_analysis else 0
                print(f"[REPO_ANALYZER] 7단계 완료 ({step_time:.2f}초): {smart_files_count}개 핵심 파일 분석")
                
                # 8. 결과 종합
                print(f"[REPO_ANALYZER] 8단계: 결과 종합")
                step_start = time.time()
                state.analysis_result = self._compile_results(state)
                step_time = time.time() - step_start
                
                total_time = time.time() - analysis_start_time
                print(f"[REPO_ANALYZER] 8단계 완료 ({step_time:.2f}초)")
                print(f"[REPO_ANALYZER] ========== 분석 완료 ({total_time:.2f}초) ==========")
                
                return state.analysis_result
                
        except Exception as e:
            state.error = str(e)
            return {
                "success": False,
                "error": state.error,
                "repo_url": repo_url
            }
    
    async def _select_important_files(self, client: GitHubClient, repo_url: str, file_tree: List[Dict], target_count: int = 12) -> List[Dict]:
        """SmartFileImportanceAnalyzer 결과를 활용한 중요한 파일 선택"""
        
        print(f"[DEBUG] 파일 트리 총 개수: {len(file_tree)}")
        print(f"[DEBUG] 목표 파일 개수: {target_count}")
        print(f"[DEBUG] 파일들 (처음 10개): {[f.get('path', 'no-path') for f in file_tree[:10]]}")
        
        # 1단계: 확장된 파일 트리 수집 (중요 디렉토리 포함)
        extended_file_tree = await self._get_extended_file_tree(client, repo_url, file_tree)
        print(f"[DEBUG] 확장된 파일 트리 개수: {len(extended_file_tree)}")
        
        # 2단계: 파일 내용을 포함한 분석 데이터 구성 (SmartFileImportanceAnalyzer의 실제 분석 사용)
        # 기존 메타데이터 스코어링은 SmartFileImportanceAnalyzer의 analyze_enhanced_metadata에서 처리됨
        
        # 3단계: SmartFileImportanceAnalyzer로 실제 파일 중요도 분석
        try:
            # 더미 값 대신 SmartFileImportanceAnalyzer의 실제 분석을 사용하도록 변경
            # analyze_repository 메서드에서 모든 실제 분석이 수행됨
            
            # 간단한 파일 선택을 위한 기본 중요도만 계산 (실제 분석은 나중에 수행됨)
            basic_importance_scores = {}
            for file_info in extended_file_tree:
                if file_info['type'] == 'file':
                    file_path = file_info['path']
                    if not self.smart_file_analyzer.is_excluded_file(file_path, file_info.get('size', 0)):
                        # 기본 구조적 중요도만 사용 (실제 분석은 analyze_repository에서)
                        structural_score = self.smart_file_analyzer.calculate_structural_importance(file_path)
                        basic_importance_scores[file_path] = structural_score
            
            importance_scores = basic_importance_scores
            
            print(f"[DEBUG] 중요도 스코어링 완료: {len(importance_scores)}개 파일")
            
            # 4단계: 중요도 점수 기준으로 상위 파일 선택
            selected_files = await self._select_by_importance_scores(
                client, repo_url, extended_file_tree, importance_scores, target_count
            )
            
            print(f"[REPO_ANALYZER] ========== 스마트 파일 선정 완료 ==========")
            print(f"[REPO_ANALYZER] 선택된 중요 파일: 총 {len(selected_files)}개 (목표: {target_count}개)")
            
            return selected_files
            
        except Exception as e:
            print(f"[ERROR] SmartFileImportanceAnalyzer 오류: {e}")
            print(f"[FALLBACK] 기존 방식으로 파일 선택")
            
            # 오류 시 기존 방식으로 폴백
            return await self._select_important_files_fallback(client, repo_url, file_tree, target_count)
    
    async def _get_extended_file_tree(self, client: GitHubClient, repo_url: str, base_file_tree: List[Dict]) -> List[Dict]:
        """중요 디렉토리를 포함한 확장된 파일 트리 수집"""
        
        extended_tree = base_file_tree.copy()
        
        # 중요 디렉토리 목록 (기술 스택별로 동적 조정 가능)
        important_dirs = ['src/', 'lib/', 'app/', 'components/', 'pages/', 'api/', 'utils/', 'services/', 
                         'models/', 'views/', 'controllers/', 'routes/', 'middleware/', 'config/', 'types/']
        
        existing_dirs = {f['path'] for f in base_file_tree if f['type'] == 'dir'}
        
        for dir_name in important_dirs:
            if any(d.startswith(dir_name) for d in existing_dirs):
                try:
                    # 디렉토리 내 파일들 수집 (1레벨만)
                    dir_files = await client.get_file_tree(repo_url, dir_name.rstrip('/'))
                    
                    # 기존 트리에 없는 파이만 추가
                    existing_paths = {f['path'] for f in extended_tree}
                    for file_info in dir_files:
                        if file_info['path'] not in existing_paths:
                            extended_tree.append(file_info)
                    
                    print(f"[DEBUG] {dir_name} 디렉토리에서 {len(dir_files)}개 파일 추가")
                    
                except Exception as e:
                    # 디렉토리가 없거나 접근 불가 시 무시
                    print(f"[DEBUG] {dir_name} 디렉토리 수집 실패: {e}")
                    continue
        
        return extended_tree
    
    def _build_metadata_for_scoring(self, file_tree: List[Dict]) -> Dict[str, float]:
        """SmartFileImportanceAnalyzer를 위한 메타데이터 스코어 구성"""
        
        metadata_scores = {}
        
        for file_info in file_tree:
            if file_info['type'] != 'file':
                continue
                
            file_path = file_info['path']
            
            # 더미/테스트 파일 제외 (SmartFileImportanceAnalyzer의 로직 활용)
            file_size = file_info.get('size', 0)
            if self.smart_file_analyzer.is_excluded_file(file_path, file_size):
                continue
            
            # 파일 크기 기반 점수 (정규화)
            file_size = file_info.get('size', 0)
            size_score = min(1.0, file_size / 10000) if file_size > 0 else 0.1
            
            # 구조적 중요도 점수 (SmartFileImportanceAnalyzer 활용)
            structural_score = self.smart_file_analyzer.calculate_structural_importance(file_path)
            
            # 메타데이터 점수 조합 (크기 30% + 구조적 중요도 70%)
            metadata_score = (size_score * 0.3) + (structural_score * 0.7)
            
            metadata_scores[file_path] = metadata_score
        
        return metadata_scores
    
    async def _select_by_importance_scores(
        self, 
        client: GitHubClient, 
        repo_url: str, 
        file_tree: List[Dict], 
        importance_scores: Dict[str, float],
        target_count: int
    ) -> List[Dict]:
        """중요도 점수 기준으로 파일 선택 및 내용 수집"""
        
        # 점수 기준으로 정렬
        sorted_files = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        
        selected_files = []
        file_tree_dict = {f['path']: f for f in file_tree if f['type'] == 'file'}
        
        print(f"[DEBUG] 중요도 스코어 상위 {min(target_count, len(sorted_files))}개 파일:")
        
        for i, (file_path, score) in enumerate(sorted_files[:target_count]):
            file_info = file_tree_dict.get(file_path)
            if not file_info:
                continue
            
            # 중요도 레벨 결정
            if score >= 0.4:
                importance_level = "critical"
            elif score >= 0.25:
                importance_level = "important"
            elif score >= 0.15:
                importance_level = "moderate"
            else:
                importance_level = "low"
            
            print(f"[DEBUG]   {i+1}. {file_info['name']} (점수: {score:.3f}, 레벨: {importance_level})")
            
            # 파일 내용 수집
            content = await client.get_file_content(repo_url, file_path)
            
            # 내용이 있는 경우 코드 밀도 분석으로 재검증
            if content and self.smart_file_analyzer._is_low_code_density_file(content):
                print(f"[DEBUG]   {file_info['name']} - 코드 밀도 낮음으로 제외")
                continue
            
            file_entry = {
                **file_info,
                "importance": importance_level,
                "importance_score": score,
                "selection_reason": "smart_importance_analyzer"
            }
            
            if content:
                file_entry["content"] = content
            else:
                file_entry["content"] = "# File content not available - API error or binary file"
                file_entry["content_unavailable_reason"] = "api_error_or_binary"
            
            selected_files.append(file_entry)
        
        # 선택 통계 로깅
        total_with_content = len([f for f in selected_files if f.get('content') and not f['content'].startswith('# File')])
        total_without_content = len(selected_files) - total_with_content
        
        print(f"[REPO_ANALYZER] 내용 수집 성공: {total_with_content}개")
        print(f"[REPO_ANALYZER] 내용 수집 실패: {total_without_content}개")
        print(f"[REPO_ANALYZER] 파일 목록: {[f.get('name', 'no-name') for f in selected_files]}")
        
        # 중요도 레벨별 통계
        level_stats = {}
        for f in selected_files:
            level = f.get('importance', 'unknown')
            level_stats[level] = level_stats.get(level, 0) + 1
        print(f"[REPO_ANALYZER] 중요도 레벨별 분포: {level_stats}")
        
        return selected_files
    
    async def _select_important_files_fallback(self, client: GitHubClient, repo_url: str, file_tree: List[Dict], target_count: int) -> List[Dict]:
        """기존 방식 폴백 (오류 시 사용)"""
        
        important_files = []
        
        # 우선순위 파일들 정의
        priority_files = [
            "package.json", "requirements.txt", "Cargo.toml", "pom.xml", "go.mod",
            "README.md", "README.rst", "CONTRIBUTING.md",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            "tsconfig.json", "webpack.config.js", "vite.config.js",
            "main.py", "app.py", "index.js", "index.ts", "server.js"
        ]
        
        # 우선순위 파일들 먼저 수집
        for file_info in file_tree:
            if file_info["type"] == "file" and file_info["name"] in priority_files:
                content = await client.get_file_content(repo_url, file_info["path"])
                
                file_entry = {
                    **file_info,
                    "importance": "important",
                    "selection_reason": "priority_file_fallback"
                }
                
                if content:
                    file_entry["content"] = content
                else:
                    file_entry["content"] = "# File content not available"
                    file_entry["content_unavailable_reason"] = "api_error_or_binary"
                
                important_files.append(file_entry)
        
        # 목표 개수에 미달하면 크기 기준으로 소스 파일 추가
        if len(important_files) < target_count:
            source_files = [f for f in file_tree if f["type"] == "file" and self._is_source_file(f["name"])]
            source_files.sort(key=lambda x: x.get("size", 0), reverse=True)
            
            existing_paths = {f["path"] for f in important_files}
            needed_count = target_count - len(important_files)
            
            for file_info in source_files[:needed_count]:
                if file_info["path"] not in existing_paths:
                    content = await client.get_file_content(repo_url, file_info["path"])
                    
                    file_entry = {
                        **file_info,
                        "importance": "moderate",
                        "selection_reason": "size_based_fallback"
                    }
                    
                    if content:
                        file_entry["content"] = content
                    else:
                        file_entry["content"] = "# File content not available"
                        file_entry["content_unavailable_reason"] = "api_error_or_binary"
                    
                    important_files.append(file_entry)
        
        return important_files
    
    def _is_source_file(self, filename: str) -> bool:
        """소스 파일 여부 판단"""
        source_extensions = [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".php", ".rb"]
        return any(filename.endswith(ext) for ext in source_extensions)
    
    async def _identify_tech_stack(self, files: List[Dict], languages: Dict[str, int]) -> Dict[str, float]:
        """기술 스택 식별"""
        
        tech_scores = {}
        total_language_bytes = sum(languages.values()) if languages else 1
        
        # 언어 통계 기반 점수
        for lang, bytes_count in languages.items():
            lang_lower = lang.lower()
            confidence = bytes_count / total_language_bytes
            tech_scores[lang_lower] = confidence
        
        print(f"[REPO_ANALYZER] 파일 내용 기반 기술 스택 감지")
        # 파일 내용 기반 기술 스택 감지
        pattern_matches = {}
        
        for tech, patterns in self.tech_patterns.items():
            score = 0.0
            matches = 0
            file_matches = []
            
            for file_info in files:
                file_path = file_info["path"]
                file_content = file_info.get("content", "")
                file_name = file_info.get("name", "")
                
                for pattern in patterns:
                    # 파일명 패턴 매칭
                    if re.search(pattern, file_path, re.IGNORECASE):
                        score += 0.3
                        matches += 1
                        file_matches.append(f"{file_name} (파일명)")
                    
                    # 파일 내용 패턴 매칭
                    if re.search(pattern, file_content, re.IGNORECASE):
                        score += 0.2
                        matches += 1
                        file_matches.append(f"{file_name} (내용)")
            
            if matches > 0:
                # 점수 정규화 (0-1 범위)
                normalized_score = min(score / len(files), 1.0)
                tech_scores[tech] = max(tech_scores.get(tech, 0), normalized_score)
                
                pattern_matches[tech] = {
                    'score': normalized_score,
                    'matches': matches,
                    'files': file_matches[:3]  # 처음 3개만 표시
                }
        
        # 패턴 매칭 결과 로그
        if pattern_matches:
            print(f"[REPO_ANALYZER] 패턴 매칭 결과:")
            for tech, match_info in sorted(pattern_matches.items(), key=lambda x: x[1]['score'], reverse=True):
                print(f"[REPO_ANALYZER]   {tech}: {match_info['score']:.3f} ({match_info['matches']}개 매칭)")
                if match_info['files']:
                    print(f"[REPO_ANALYZER]     매칭 파일: {', '.join(match_info['files'])}")
        
        # 최종 점수 필터링 및 로그
        original_count = len(tech_scores)
        filtered_scores = {tech: score for tech, score in tech_scores.items() if score >= 0.1}
        
        print(f"[REPO_ANALYZER] 점수 필터링: {original_count}개 → {len(filtered_scores)}개 (임계값 0.1 이상)")
        
        # 최종 점수 표시
        if filtered_scores:
            sorted_tech = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)
            print(f"[REPO_ANALYZER] 최종 기술 스택 ({len(sorted_tech)}개):")
            for tech, score in sorted_tech:
                print(f"[REPO_ANALYZER]   {tech}: {score:.3f}")
        else:
            print(f"[REPO_ANALYZER] 식별된 기술 스택 없음")
        
        return filtered_scores
    
    async def _calculate_complexity_score(self, state: AnalysisState) -> float:
        """복잡도 점수 계산"""
        
        complexity_factors = []
        
        # 1. 파일 수 기반 복잡도
        if state.file_tree:
            file_count = len([f for f in state.file_tree if f["type"] == "file"])
            file_complexity = min(file_count / 50, 1.0) * 2  # 최대 2점
            complexity_factors.append(file_complexity)
        
        # 2. 기술 스택 다양성
        if state.tech_stack:
            tech_diversity = min(len(state.tech_stack) / 5, 1.0) * 2  # 최대 2점
            complexity_factors.append(tech_diversity)
        
        # 3. 저장소 크기
        if state.repo_info:
            size_kb = state.repo_info.get("size", 0)
            size_complexity = min(size_kb / 10000, 1.0) * 2  # 최대 2점
            complexity_factors.append(size_complexity)
        
        # 4. 언어 다양성
        if state.languages:
            lang_diversity = min(len(state.languages) / 3, 1.0) * 2  # 최대 2점
            complexity_factors.append(lang_diversity)
        
        # 5. 코드 복잡도 (파일 내용 기반)
        code_complexity = await self._analyze_code_complexity(state.important_files)
        complexity_factors.append(code_complexity)
        
        # 평균 계산 (0-10 범위)
        if complexity_factors:
            return round(sum(complexity_factors) / len(complexity_factors), 2)
        
        return 5.0  # 기본값
    
    async def _analyze_code_complexity(self, files: List[Dict]) -> float:
        """코드 내용 기반 복잡도 분석"""
        
        if not files:
            return 2.0
        
        total_lines = 0
        complex_patterns = 0
        
        # 복잡도를 나타내는 패턴들
        complexity_patterns = [
            r"\bif\b", r"\bfor\b", r"\bwhile\b", r"\btry\b", r"\bcatch\b",
            r"\bswitch\b", r"\bcase\b", r"function\s*\(", r"def\s+\w+",
            r"class\s+\w+", r"async\s+", r"await\s+", r"Promise"
        ]
        
        for file_info in files:
            content = file_info.get("content", "")
            lines = content.split("\n")
            total_lines += len(lines)
            
            for pattern in complexity_patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                complex_patterns += matches
        
        if total_lines == 0:
            return 2.0
        
        # 복잡도 계산 (라인당 복잡 패턴 비율)
        complexity_ratio = complex_patterns / total_lines
        complexity_score = min(complexity_ratio * 20, 2.0)  # 최대 2점
        
        return complexity_score
    
    async def _analyze_file_importance(self, repo_url: str, state: AnalysisState) -> Optional[Dict[str, Any]]:
        """스마트 파일 중요도 분석 수행"""
        
        try:
            print(f"[DEBUG] SmartFileImportanceAnalyzer 시작")
            
            # 분석 데이터 구성
            analysis_data = {
                "repo_url": repo_url,
                "key_files": state.important_files or [],
                "tech_stack": state.tech_stack or {},
                "repo_info": state.repo_info or {}
            }
            
            # SmartFileImportanceAnalyzer를 사용하여 분석
            result = await self.smart_file_analyzer.analyze_repository(repo_url, analysis_data)
            
            if result.get("success"):
                print(f"[DEBUG] SmartFileImportanceAnalyzer 성공")
                return result.get("smart_file_analysis")
            else:
                print(f"[DEBUG] SmartFileImportanceAnalyzer 실패: {result.get('error')}")
                return None
                
        except Exception as e:
            print(f"[ERROR] SmartFileImportanceAnalyzer 예외: {e}")
            return None
    
    def _compile_results(self, state: AnalysisState) -> Dict[str, Any]:
        """분석 결과 종합"""
        
        print(f"[DEBUG] _compile_results - state.repo_url: {state.repo_url}")
        
        return {
            "success": True,
            "repo_url": state.repo_url,
            "repo_info": {
                "name": state.repo_info.get("name", ""),
                "owner": state.repo_info.get("owner", ""),  # owner 정보 추가
                "description": state.repo_info.get("description", ""),
                "language": state.repo_info.get("language", ""),
                "size": state.repo_info.get("size", 0),
                "stargazers_count": state.repo_info.get("stargazers_count", 0),
                "forks_count": state.repo_info.get("forks_count", 0),
                "created_at": state.repo_info.get("created_at", ""),
                "updated_at": state.repo_info.get("updated_at", "")
            },
            "tech_stack": state.tech_stack or {},
            "languages": state.languages or {},
            "complexity_score": state.complexity_score or 0.0,
            "file_count": len([f for f in (state.file_tree or []) if f["type"] == "file"]),
            "key_files": [
                {
                    "path": f["path"],
                    "name": f["name"], 
                    "size": f.get("size", 0),
                    "importance": f.get("importance", "low"),
                    "content": f.get("content", "# File content not available"),
                    "content_unavailable_reason": f.get("content_unavailable_reason")
                }
                for f in (state.important_files or [])
            ],
            "smart_file_analysis": state.smart_file_analysis,
            "analysis_summary": self._generate_summary(state)
        }
    
    def _generate_summary(self, state: AnalysisState) -> str:
        """분석 결과 요약 생성"""
        
        if not state.repo_info:
            return "분석에 실패했습니다."
        
        name = state.repo_info.get("name", "Unknown")
        language = state.repo_info.get("language", "Unknown")
        complexity = state.complexity_score or 0
        
        tech_list = ", ".join(list((state.tech_stack or {}).keys())[:5])
        
        summary = f"{name} 프로젝트는 {language}를 주 언어로 사용하며, "
        summary += f"복잡도 점수는 {complexity}/10입니다. "
        
        if tech_list:
            summary += f"주요 기술 스택: {tech_list}"
        
        return summary
    
    async def get_all_files(self, owner: str, repo: str, max_depth: int = 3, max_files: int = 500) -> List[Dict[str, Any]]:
        """저장소의 모든 파일을 트리 구조로 조회"""
        from app.services.github_client import GitHubClient
        
        print(f"[REPO_ANALYZER] get_all_files 시작: {owner}/{repo}, depth={max_depth}, max_files={max_files}")
        
        async with GitHubClient() as client:
            result = await self._get_files_recursive(client, f"https://github.com/{owner}/{repo}", "", max_depth, max_files, 0)
            print(f"[REPO_ANALYZER] get_all_files 완료: {len(result)}개 파일 발견")
            return result
    
    async def _get_files_recursive(self, client, repo_url: str, path: str, max_depth: int, max_files: int, current_depth: int) -> List[Dict[str, Any]]:
        """재귀적으로 파일 트리 구조 조회"""
        if current_depth >= max_depth:
            return []
        
        try:
            file_tree = await client.get_file_tree(repo_url, path)
            all_files = []
            
            for item in file_tree:
                if len(all_files) >= max_files:
                    break
                
                file_info = {
                    "name": item["name"],
                    "path": item["path"],
                    "type": item["type"],
                    "size": item.get("size", 0),
                    "download_url": item.get("download_url")
                }
                
                all_files.append(file_info)
                
                # 디렉토리인 경우 재귀적으로 탐색
                if item["type"] == "dir" and current_depth < max_depth - 1:
                    children = await self._get_files_recursive(
                        client, repo_url, item["path"], max_depth, max_files - len(all_files), current_depth + 1
                    )
                    all_files.extend(children)
            
            return all_files[:max_files]
            
        except Exception as e:
            print(f"Error fetching directory {path}: {e}")
            return []