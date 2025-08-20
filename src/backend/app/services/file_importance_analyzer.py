"""
스마트 파일 중요도 스코어링 알고리즘

4차원 분석 결과를 조합한 파일 중요도 스코어링 시스템:
- 메타정보 (40%): 파일 크기, 라인 수, 구조적 중요도
- 의존성 중앙성 (30%): PageRank, Betweenness, Closeness 중앙성
- 변경 빈도 (20%): Git churn 분석, 핫스팟 식별
- 복잡도 (10%): 순환복잡도, 유지보수성 지수

기획서 요구사항에 따른 정확한 가중치 적용 및 파일 크기 정규화, 경로 기반 우선순위 적용
"""

import re
import asyncio
import statistics
import math
import random
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from .git_analyzer import GitAnalyzer
from .complexity_analyzer import RuleBasedComplexityAnalyzer
from .dependency_analyzer import DependencyAnalyzer


class SmartFileImportanceAnalyzer:
    """스마트 파일 중요도 분석기"""
    
    def __init__(self, repo_path: str = "."):
        # Git 분석기 초기화
        self.git_analyzer = GitAnalyzer(repo_path)
        
        # 복잡도 분석기 초기화
        self.complexity_analyzer = RuleBasedComplexityAnalyzer()
        
        # 의존성 분석기 초기화
        self.dependency_analyzer = DependencyAnalyzer()
        
        # 파일명 패턴별 구조적 중요도 가중치
        self.structural_patterns = {
            # 메인 파일들 (높은 중요도)
            'main_files': {
                'patterns': [
                    r'^(src/)?main\.(ts|js|py|java|go|rs)$',
                    r'^(src/)?index\.(ts|js|html)$',
                    r'^(src/)?app\.(ts|js|py|java)$',
                    r'^(src/)?App\.(tsx|vue|svelte)$',
                    r'^__init__\.py$',
                    r'^setup\.(py|js)$'
                ],
                'weight': 0.9
            },
            # 설정 파일들 (매우 높은 중요도)
            'config_files': {
                'patterns': [
                    r'^package\.json$',
                    r'^tsconfig\.json$',
                    r'^webpack\.config\.(js|ts)$',
                    r'^babel\.config\.(js|json)$',
                    r'^babel\.config-.*\.(js|json)$',  # React Compiler 등 특수 babel 설정 파일
                    r'^\.babelrc(\.(js|json))?$',      # 추가 babel 설정 파일
                    r'^vite\.config\.(js|ts)$',
                    r'^rollup\.config\.(js|ts)$',
                    r'^\.env(\.|$)',
                    r'^config\.(js|ts|json|yml|yaml)$',
                    r'^settings\.(json|yml|yaml|py)$',
                    r'^Dockerfile$',
                    r'^docker-compose\.(yml|yaml)$',
                    r'^pyproject\.toml$',
                    r'^requirements\.txt$',
                    r'^requirements-.*\.txt$',
                    r'^setup\.py$',
                    r'^setup\.cfg$',
                    r'^tox\.ini$',
                    r'^pytest\.ini$',
                    r'^\.flake8$',
                    r'^\.pylintrc$',
                    r'^Pipfile$',
                    r'^poetry\.lock$',
                    r'^Cargo\.toml$',
                    r'^go\.mod$'
                ],
                'weight': 0.98  # 설정 파일 중요도 상향 조정
            },
            # 핵심 모듈들
            'core_modules': {
                'patterns': [
                    r'(src/)?(core|base|foundation|kernel)/',
                    r'(src/)?(config|configuration)/',
                    r'(src/)?(api|router|routes)/',
                    r'(src/)?(models?|entities)/',
                    r'(src/)?(services?|providers?)/',
                    r'(src/)?(store|state|redux)/',
                    r'(src/)?(types?|interfaces?)/'
                ],
                'weight': 0.8
            },
            # Django/Python 웹 프레임워크 특화 패턴 (매우 높은 중요도)
            'django_framework': {
                'patterns': [
                    # Django 핵심 파일들
                    r'.*settings\.py$',
                    r'.*urls\.py$', 
                    r'.*models\.py$',
                    r'.*views\.py$',
                    r'.*admin\.py$',
                    r'.*forms\.py$',
                    r'.*serializers\.py$',
                    r'.*apps\.py$',
                    r'manage\.py$',
                    r'wsgi\.py$',
                    r'asgi\.py$',
                    # Django 프로젝트 구조
                    r'django/.*\.py$',
                    r'.*/django/.*\.py$',
                    # Python 웹 프레임워크 공통
                    r'.*/(models|views|controllers|serializers)/.*\.py$',
                    r'.*/migrations/.*\.py$',
                    # Django 앱 구조
                    r'.*/(migrations|templates|static)/.*',
                    # Python 패키지 구조
                    r'.*/__init__\.py$',
                    r'.*/setup\.py$',
                    r'.*/conftest\.py$'
                ],
                'weight': 0.85
            },
            # 라이브러리/유틸리티
            'utilities': {
                'patterns': [
                    r'(src/)?(utils?|helpers?|tools?)/',
                    r'(src/)?(lib|libraries?)/',
                    r'(src/)?(shared|common)/',
                    r'(src/)?(constants?|config)/'
                ],
                'weight': 0.7
            },
            # 컴포넌트들 (중간 중요도)
            'components': {
                'patterns': [
                    r'(src/)?(components?|widgets?)/',
                    r'(src/)?(views?|pages?)/',
                    r'(src/)?(screens?|layouts?)/'
                ],
                'weight': 0.5
            },
            # 테스트 파일들 (낮은 중요도)
            'test_files': {
                'patterns': [
                    r'(test|tests|__tests__|spec)/',
                    r'\.(test|spec)\.(js|ts|py|java)$',
                    r'test_.*\.py$',
                    r'.*_test\.(go|rs)$'
                ],
                'weight': 0.2
            },
            # 문서 파일들 (낮은 중요도)
            'documentation': {
                'patterns': [
                    r'README\.(md|txt|rst)$',
                    r'CHANGELOG\.(md|txt)$',
                    r'LICENSE(\.|$)',
                    r'(docs?|documentation)/',
                    r'\.(md|txt|rst)$'
                ],
                'weight': 0.3
            },
            # 빌드/배포 관련
            'build_deploy': {
                'patterns': [
                    r'^Makefile$',
                    r'\.github/workflows/',
                    r'\.gitlab-ci\.yml$',
                    r'jenkins/',
                    r'scripts?/',
                    r'build/',
                    r'dist/',
                    r'deploy/'
                ],
                'weight': 0.6
            }
        }
        
        # 중요도 계산 가중치 (기획서 요구사항에 따른 정확한 비율)
        # 기본 가중치 - 동적 변동에서 사용
        self.base_importance_weights = {
            'metadata': 0.4,         # 40% - 메타정보 (파일 크기, 라인 수, 구조적 중요도)
            'dependency': 0.3,       # 30% - 의존성 중앙성 (PageRank, Betweenness, Closeness)
            'churn': 0.2,           # 20% - 변경 빈도 (Git churn 분석, 핫스팟)
            'complexity': 0.1        # 10% - 복잡도 (순환복잡도, 유지보수성)
        }
        
        # 현재 사용 중인 가중치 (동적으로 변경됨)
        self.importance_weights = self.base_importance_weights.copy()
        
        # 파일 크기 임계값 (50KB - 기획서 요구사항)
        self.size_threshold = 50 * 1024
        
        # 경로 기반 보너스/디스카운트 (기획서 요구사항)
        self.path_bonuses = {
            'src/': 1.2,
            'lib/': 1.2,
            'components/': 1.15,
            'core/': 1.25,
            'main/': 1.3,
            'app/': 1.15,
            # Django/Python 프로젝트 특화 보너스
            'django/': 1.4,        # Django 프로젝트 폴더
            'apps/': 1.3,          # Django 앱들
            'models/': 1.25,       # 모델 폴더
            'views/': 1.25,        # 뷰 폴더
            'api/': 1.2,           # API 폴더
            'serializers/': 1.2,   # 시리얼라이저 폴더
            'utils/': 1.1,         # 유틸리티 폴더
            'management/': 1.2     # Django 커맨드 폴더
        }
        
        self.path_penalties = {
            'test/': 0.3,
            'tests/': 0.3,
            '__tests__/': 0.3,
            'spec/': 0.3,
            'docs/': 0.4,
            'doc/': 0.4,
            'build/': 0.2,
            'dist/': 0.2,
            'node_modules/': 0.1,
            '.git/': 0.1,
            'vendor/': 0.2
        }
        
        # 중요도 분류 임계값 (더 많은 파일 포함을 위해 조정)
        self.importance_thresholds = {
            'critical': 0.4,   # 0.7 → 0.4로 대폭 낮춤 (실제 비즈니스 파일 선정)
            'important': 0.25, # 0.5 → 0.25로 대폭 낮춤
            'moderate': 0.15,  # 0.3 → 0.15로 대폭 낮춤  
            'low': 0.0
        }
    
    def generate_dynamic_weights(self, seed: Optional[str] = None) -> Dict[str, float]:
        """동적 가중치 생성 - 질문 생성 시마다 미세하게 변동"""
        
        # 시드 설정 (재현 가능한 랜덤성)
        if seed:
            random.seed(hash(seed) % (2**32))
        
        # 기본 가중치에서 미세한 변동 적용 (±5%)
        variation_range = 0.05
        dynamic_weights = {}
        
        total_variation = 0.0
        for key, base_weight in self.base_importance_weights.items():
            # -5% ~ +5% 범위내에서 랜덤 변동
            variation = random.uniform(-variation_range, variation_range)
            new_weight = base_weight + (base_weight * variation)
            dynamic_weights[key] = max(0.01, new_weight)  # 최소 1% 보장
            total_variation += new_weight - base_weight
        
        # 총합이 1.0이 되도록 정규화
        total_weight = sum(dynamic_weights.values())
        for key in dynamic_weights:
            dynamic_weights[key] = dynamic_weights[key] / total_weight
        
        return dynamic_weights
    
    def update_weights_for_session(self, session_id: Optional[str] = None) -> None:
        """세션에 맞춰 가중치 업데이트"""
        self.importance_weights = self.generate_dynamic_weights(session_id)
    
    def is_excluded_file(self, file_path: str, file_size: int = None, file_content: str = None) -> bool:
        """더미/샘플/테스트 데이터 제외 여부 판단 + 파일 크기 및 코드 밀도 필터링"""
        
        if not file_path:
            return True
        
        # 너무 작은 파일 제외 (50 bytes 미만)
        if file_size is not None and file_size < 50:
            return True
        
        # 코드 밀도 분석 - 파일 내용이 있는 경우만 수행
        if file_content is not None:
            if self._is_low_code_density_file(file_content):
                return True
        
        normalized_path = file_path.replace('\\', '/')
        
        # 더미/샘플 데이터 패턴 확인
        dummy_patterns = [
            # 테스트 디렉토리 및 파일 (가장 먼저 체크)
            r'(test|tests|__tests__|spec)/',
            r'\.(test|spec)\.(js|ts|py|java)$',
            r'test_.*\.py$',
            r'.*_test\.(go|rs|py|js|ts)$',
            r'.*Test\.(java|kt|cs)$',
            # 더미/샘플 디렉토리
            r'(dummy|sample|mock|fake|stub)/',
            r'(example|examples|demo|demos)/',
            r'(seed|seeds|fixtures?|factory)/',
            r'(initial|init)_?data/',
            r'(placeholder|template)s?/',
            # 더미 파일명 패턴
            r'.*\.(sample|example|dummy|mock|template)\.',
            r'(sample|example|dummy|mock|template).*\.(json|yml|yaml|xml|csv|sql)$',
            r'bootstrap.*\.(js|ts|py)$',
            r'(data/)?(dummy|sample|mock|test).*\.(csv|json|sql|xml)$',
            # 마이그레이션/시드 파일
            r'migration.*\.(sql|js|ts|py)$',
            r'seed.*\.(sql|js|ts|py)$',
            r'schema.*\.(sql|json)$',
            # 초기화 스크립트
            r'init.*\.(sh|bat|py|js)$',
            r'setup.*\.(sh|bat|py|js)$',
            # 템플릿 파일
            r'.*\.template\.',
            r'.*\.tmpl$',
            # 로그 및 임시 파일
            r'.*\.log$',
            r'.*\.tmp$',
            r'temp.*\.',
            # 백업 및 시스템 파일
            r'.*\.bak$',
            r'.*\.backup$',
            r'.*~$',
            # IDE 및 에디터 설정
            r'\.(vscode|idea|eclipse|settings)/',
            r'.*\.(orig|rej)$',
            # Dot 파일 제외 패턴 (루트 및 하위 디렉토리)
            r'^\.[^/]*$',          # 루트의 dot 파일들 (.env, .gitignore 등)
            r'/\.[^/]*$',          # 하위 디렉토리의 dot 파일들
            r'(^|/)\.[a-zA-Z]'     # 더 포괄적인 dot 파일 패턴
        ]
        
        for pattern in dummy_patterns:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                return True
        
        # 추가 제외 조건 (패턴에서 다루지 않은 나머지)
        exclude_conditions = [
            # 빈 파일 또는 매우 작은 파일
            len(normalized_path.strip()) == 0,
            # 캐시 파일
            '/cache/' in normalized_path or '.cache' in normalized_path
        ]
        
        return any(exclude_conditions)
    
    def _is_low_code_density_file(self, file_content: str) -> bool:
        """코드 밀도가 낮은 파일인지 판단 (주석 비율, 공백 라인 비율 체크)"""
        
        if not file_content or len(file_content.strip()) == 0:
            return True
        
        lines = file_content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return True
        
        comment_lines = 0
        blank_lines = 0
        import_lines = 0
        
        for line in lines:
            stripped_line = line.strip()
            
            # 공백 라인
            if not stripped_line:
                blank_lines += 1
                continue
            
            # 주석 라인 (다양한 언어 지원)
            if (stripped_line.startswith('//') or          # JS, Java, C++
                stripped_line.startswith('#') or           # Python, Shell
                stripped_line.startswith('/*') or          # CSS, JS
                stripped_line.startswith('*') or           # Multi-line comments
                stripped_line.startswith('<!--') or        # HTML
                stripped_line.startswith('--') or          # SQL
                stripped_line.startswith("'''") or         # Python docstring
                stripped_line.startswith('"""')):          # Python docstring
                comment_lines += 1
                continue
            
            # Import/Include 라인만 있는 파일 체크
            if (stripped_line.startswith('import ') or
                stripped_line.startswith('from ') or
                stripped_line.startswith('#include') or
                stripped_line.startswith('require(') or
                stripped_line.startswith('const ') and 'require(' in stripped_line or
                stripped_line.startswith('using ') or
                stripped_line.startswith('package ')):
                import_lines += 1
        
        # 주석 비율이 80% 이상이면 제외
        comment_ratio = comment_lines / total_lines
        if comment_ratio > 0.8:
            return True
        
        # 공백 라인 비율이 50% 이상이면 제외
        blank_ratio = blank_lines / total_lines
        if blank_ratio > 0.5:
            return True
        
        # Import/Include문만 있는 파일 (90% 이상)이면 제외
        import_ratio = import_lines / total_lines
        if import_ratio > 0.9:
            return True
        
        # 너무 적은 실제 코드 라인 (전체의 10% 미만)
        actual_code_lines = total_lines - comment_lines - blank_lines - import_lines
        actual_code_ratio = actual_code_lines / total_lines
        if actual_code_ratio < 0.1:
            return True
        
        return False
    
    async def _analyze_files_complexity_with_content(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """파일 내용과 함께 복잡도 분석"""
        complexity_metrics = {}
        
        for file_path in file_paths:
            if not file_path:
                continue
                
            try:
                # 파일 확장자로 언어 감지
                ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
                language = self._detect_language_from_extension(ext)
                
                # 파일 내용 읽기 (실제 파일 경로가 있는 경우)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except:
                    # 파일을 읽을 수 없는 경우 기본값
                    complexity_metrics[file_path] = self._get_default_complexity_metrics()
                    continue
                
                # 실제 복잡도 분석
                complexity_result = await self.complexity_analyzer.analyze_code_complexity(content, language)
                
                # 기존 인터페이스와 호환되는 형태로 변환
                complexity_metrics[file_path] = {
                    'cyclomatic_complexity': complexity_result.get('cyclomatic_complexity', 1),
                    'maintainability_index': complexity_result.get('maintainability_index', 75.0),
                    'lines_of_code': complexity_result.get('lines_of_code', {'executable': 10})
                }
                
            except Exception as e:
                print(f"[DEBUG] {file_path} 복잡도 분석 실패: {e}")
                complexity_metrics[file_path] = self._get_default_complexity_metrics()
        
        print(f"[DEBUG] 복잡도 분석 완료: {len(complexity_metrics)}개 파일")
        return complexity_metrics
    
    def _detect_language_from_extension(self, ext: str) -> str:
        """파일 확장자로부터 프로그래밍 언어 감지"""
        language_map = {
            'py': 'python',
            'js': 'javascript', 
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust'
        }
        return language_map.get(ext, 'unknown')
    
    def _get_default_complexity_metrics(self) -> Dict[str, Any]:
        """기본 복잡도 메트릭"""
        return {
            'cyclomatic_complexity': 2,
            'maintainability_index': 75.0,
            'lines_of_code': {'executable': 10}
        }
    
    def calculate_structural_importance(self, file_path: str) -> float:
        """파일명 패턴 기반 구조적 중요도 계산"""
        
        if not file_path:
            return 0.0
        
        # 정규화된 경로 (OS 독립적)
        normalized_path = file_path.replace('\\', '/')
        
        max_importance = 0.0
        
        # 각 패턴 카테고리별로 매칭 확인
        for category, info in self.structural_patterns.items():
            patterns = info['patterns']
            weight = info['weight']
            
            for pattern in patterns:
                if re.search(pattern, normalized_path, re.IGNORECASE):
                    max_importance = max(max_importance, weight)
                    break  # 카테고리 내에서 첫 번째 매칭으로 충분
        
        return max_importance
    
    def _calculate_path_multiplier(self, file_path: str) -> float:
        """경로 기반 보너스/디스카운트 계산"""
        
        file_path_lower = file_path.lower()
        
        # 디스카운트 먼저 확인 (우선순위)
        for penalty_path, penalty_factor in self.path_penalties.items():
            if penalty_path in file_path_lower:
                return penalty_factor
        
        # 보너스 확인
        for bonus_path, bonus_factor in self.path_bonuses.items():
            if bonus_path in file_path_lower:
                return bonus_factor
        
        # 메인 파일 패턴 확인
        file_name = Path(file_path).name.lower()
        main_patterns = ['main.', 'index.', 'app.', '__init__.py', 'package.json']
        for pattern in main_patterns:
            if pattern in file_name:
                return 1.4
        
        return 1.0  # 기본값
    
    def calculate_enhanced_importance_scores(
        self,
        metadata_scores: Dict[str, float],
        dependency_centrality: Dict[str, float],
        churn_scores: Dict[str, float],
        complexity_scores: Dict[str, float],
        file_sizes: Optional[Dict[str, int]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        기획서 요구사항에 따른 4차원 스코어링 알고리즘 (동적 가중치 적용)
        importance_score = 0.4*meta_score + 0.3*centrality_score + 0.2*churn_score + 0.1*complexity_score
        """
        
        # 세션에 맞춰 가중치 업데이트
        if session_id:
            self.update_weights_for_session(session_id)
        
        # 모든 파일 경로 수집
        all_files = set()
        all_files.update(metadata_scores.keys())
        all_files.update(dependency_centrality.keys())
        all_files.update(churn_scores.keys())
        all_files.update(complexity_scores.keys())
        
        if not all_files:
            return {}
        
        importance_scores = {}
        
        for file_path in all_files:
            # 더미/샘플/테스트 데이터 제외
            if self.is_excluded_file(file_path):
                continue
                
            # 각 차원의 점수 가져오기 (없으면 0.0)
            meta_score = metadata_scores.get(file_path, 0.0)
            dep_score = dependency_centrality.get(file_path, 0.0)
            churn_score = churn_scores.get(file_path, 0.0)
            comp_score = complexity_scores.get(file_path, 0.0)
            
            # 기획서 공식 적용: 0.4*meta + 0.3*centrality + 0.2*churn + 0.1*complexity
            base_score = (
                self.importance_weights['metadata'] * meta_score +
                self.importance_weights['dependency'] * dep_score +
                self.importance_weights['churn'] * churn_score +
                self.importance_weights['complexity'] * comp_score
            )
            
            # 파일 크기 페널티 적용 (50KB 이상 시)
            size_penalty = 1.0
            if file_sizes and file_path in file_sizes:
                file_size = file_sizes[file_path]
                if file_size > self.size_threshold:
                    # 지수적 페널티 적용
                    excess_ratio = file_size / self.size_threshold
                    size_penalty = math.exp(-0.1 * (excess_ratio - 1))
                    size_penalty = max(0.3, size_penalty)  # 최소 30% 유지
            
            # 경로 기반 보너스/디스카운트 적용
            path_multiplier = self._calculate_path_multiplier(file_path)
            
            # 최종 점수 계산
            final_score = base_score * path_multiplier * size_penalty
            final_score = max(0.0, min(1.0, final_score))  # 0-1 범위로 클램핑
            
            importance_scores[file_path] = final_score
        
        return importance_scores

    def calculate_comprehensive_importance_scores(
        self,
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """종합적인 파일 중요도 점수 계산"""
        
        # 모든 파일 경로 수집
        all_files = set()
        all_files.update(dependency_centrality.keys())
        all_files.update(churn_metrics.keys())
        all_files.update(complexity_metrics.keys())
        
        if not all_files:
            return {}
        
        importance_scores = {}
        
        for file_path in all_files:
            # 1. 구조적 중요도
            structural_score = self.calculate_structural_importance(file_path)
            
            # 2. 의존성 중심성 (정규화됨)
            dependency_score = dependency_centrality.get(file_path, 0.0)
            
            # 3. 변경 이력 위험도
            churn_data = churn_metrics.get(file_path, {})
            churn_score = self._calculate_churn_importance_score(churn_data)
            
            # 4. 복잡도 점수
            complexity_data = complexity_metrics.get(file_path, {})
            complexity_score = self._calculate_complexity_importance_score(complexity_data)
            
            # 기획서 요구사항에 따른 4차원 스코어링 공식 적용
            # importance_score = 0.4*meta_score + 0.3*centrality_score + 0.2*churn_score + 0.1*complexity_score
            comprehensive_score = (
                structural_score * self.importance_weights['metadata'] +
                dependency_score * self.importance_weights['dependency'] +
                churn_score * self.importance_weights['churn'] +
                complexity_score * self.importance_weights['complexity']
            )
            
            # 경로 기반 보너스/디스카운트 적용
            path_multiplier = self._calculate_path_multiplier(file_path)
            comprehensive_score *= path_multiplier
            
            importance_scores[file_path] = min(1.0, comprehensive_score)
        
        return importance_scores
    
    def _calculate_churn_importance_score(self, churn_data: Dict[str, Any]) -> float:
        """변경 이력 기반 중요도 점수 계산"""
        
        if not churn_data:
            return 0.0
        
        # 변경 빈도 (정규화)
        commit_frequency = churn_data.get('commit_frequency', 0)
        frequency_score = min(1.0, commit_frequency / 20.0)  # 20 커밋을 최대로 가정
        
        # 최근 활동도 (이미 0-1)
        recent_activity = churn_data.get('recent_activity', 0.0)
        
        # 버그 수정 비율 (높을수록 중요하지만 불안정)
        bug_fix_ratio = churn_data.get('bug_fix_ratio', 0.0)
        
        # 안정성 점수 (높을수록 중요하고 안정적)
        stability_score = churn_data.get('stability_score', 1.0)
        
        # 종합 점수: 활동도와 안정성의 균형
        # 높은 활동도 + 높은 안정성 = 매우 중요
        # 높은 활동도 + 낮은 안정성 = 중요하지만 위험
        churn_importance = (
            frequency_score * 0.3 +
            recent_activity * 0.3 +
            stability_score * 0.4
        )
        
        return min(1.0, churn_importance)
    
    def _calculate_complexity_importance_score(self, complexity_data: Dict[str, Any]) -> float:
        """복잡도 기반 중요도 점수 계산"""
        
        if not complexity_data:
            return 0.0
        
        # 순환복잡도 (정규화)
        cyclomatic = complexity_data.get('cyclomatic_complexity', 0)
        complexity_score = min(1.0, cyclomatic / 20.0)  # 20을 최대로 가정
        
        # 유지보수성 지수 (높을수록 좋음, 역방향 정규화)
        maintainability = complexity_data.get('maintainability_index', 100)
        maintainability_score = 1.0 - (maintainability / 100.0)
        
        # 실행 가능한 라인 수 (정규화)
        lines_data = complexity_data.get('lines_of_code', {})
        executable_lines = lines_data.get('executable', 0)
        lines_score = min(1.0, executable_lines / 200.0)  # 200 라인을 최대로 가정
        
        # 종합 복잡도 중요도
        complexity_importance = (
            complexity_score * 0.4 +
            maintainability_score * 0.3 +
            lines_score * 0.3
        )
        
        return min(1.0, complexity_importance)
    
    def identify_critical_files(
        self,
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]],
        top_n: int = 15  # 10 → 15로 증가
    ) -> List[Dict[str, Any]]:
        """핵심 파일 식별"""
        
        # 종합 중요도 점수 계산
        importance_scores = self.calculate_comprehensive_importance_scores(
            dependency_centrality, churn_metrics, complexity_metrics
        )
        
        # 점수순으로 정렬
        sorted_files = sorted(
            importance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        critical_files = []
        
        for file_path, score in sorted_files:
            # 각 파일의 상세 메트릭 수집
            file_metrics = {
                'structural_importance': self.calculate_structural_importance(file_path),
                'dependency_centrality': dependency_centrality.get(file_path, 0.0),
                'churn_risk': self._calculate_churn_importance_score(
                    churn_metrics.get(file_path, {})
                ),
                'complexity_score': self._calculate_complexity_importance_score(
                    complexity_metrics.get(file_path, {})
                )
            }
            
            # 선정 이유 생성
            reasons = self.generate_file_selection_reasons(file_path, file_metrics)
            
            critical_files.append({
                'file_path': file_path,
                'importance_score': round(score, 3),
                'reasons': reasons,
                'metrics': file_metrics
            })
        
        return critical_files
    
    def generate_file_selection_reasons(
        self, 
        file_path: str, 
        metrics: Dict[str, float]
    ) -> List[str]:
        """파일 선정 이유 생성"""
        
        reasons = []
        
        # 구조적 중요도 기반 이유
        structural = metrics.get('structural_importance', 0.0)
        if structural >= 0.9:
            if 'package.json' in file_path or 'config' in file_path.lower():
                reasons.append("프로젝트 핵심 설정 파일")
            elif 'main' in file_path or 'index' in file_path:
                reasons.append("애플리케이션 진입점 파일")
        elif structural >= 0.7:
            if 'core' in file_path or 'base' in file_path:
                reasons.append("핵심 모듈 또는 기반 라이브러리")
            elif 'api' in file_path or 'service' in file_path:
                reasons.append("핵심 비즈니스 로직 담당")
        
        # 의존성 중심성 기반 이유
        dependency = metrics.get('dependency_centrality', 0.0)
        if dependency >= 0.7:
            reasons.append("다른 파일들이 많이 참조하는 핵심 의존성")
        elif dependency >= 0.5:
            reasons.append("중요한 모듈 간 연결점 역할")
        
        # 변경 이력 기반 이유
        churn = metrics.get('churn_risk', 0.0)
        if churn >= 0.7:
            reasons.append("활발하게 개발되고 있는 핵심 기능")
        elif churn >= 0.5:
            reasons.append("지속적으로 개선되고 있는 중요 모듈")
        
        # 복잡도 기반 이유
        complexity = metrics.get('complexity_score', 0.0)
        if complexity >= 0.6:
            reasons.append("높은 복잡도로 인한 주의 필요 파일")
        elif complexity >= 0.4:
            reasons.append("적절한 복잡도의 핵심 로직 포함")
        
        # 기본 이유 (다른 이유가 없는 경우)
        if not reasons:
            if structural > 0.3:
                reasons.append("프로젝트 구조상 중요한 위치")
            else:
                reasons.append("종합 메트릭 기반 선정")
        
        return reasons
    
    def categorize_files_by_importance(
        self,
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """중요도별 파일 분류"""
        
        importance_scores = self.calculate_comprehensive_importance_scores(
            dependency_centrality, churn_metrics, complexity_metrics
        )
        
        categorized = {
            'critical': [],
            'important': [],
            'moderate': [],
            'low': []
        }
        
        for file_path, score in importance_scores.items():
            if score >= self.importance_thresholds['critical']:
                categorized['critical'].append(file_path)
            elif score >= self.importance_thresholds['important']:
                categorized['important'].append(file_path)
            elif score >= self.importance_thresholds['moderate']:
                categorized['moderate'].append(file_path)
            else:
                categorized['low'].append(file_path)
        
        # 각 카테고리 내에서 점수순 정렬
        for category in categorized:
            categorized[category].sort(
                key=lambda f: importance_scores[f],
                reverse=True
            )
        
        return categorized
    
    def calculate_importance_distribution(
        self,
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """중요도 분포 통계 계산"""
        
        importance_scores = self.calculate_comprehensive_importance_scores(
            dependency_centrality, churn_metrics, complexity_metrics
        )
        
        if not importance_scores:
            return {}
        
        scores = list(importance_scores.values())
        
        return {
            'mean': round(statistics.mean(scores), 3),
            'median': round(statistics.median(scores), 3),
            'std_dev': round(statistics.stdev(scores) if len(scores) > 1 else 0.0, 3),
            'min': round(min(scores), 3),
            'max': round(max(scores), 3),
            'quartiles': {
                'q1': round(statistics.quantiles(scores, n=4)[0] if len(scores) >= 4 else min(scores), 3),
                'q3': round(statistics.quantiles(scores, n=4)[2] if len(scores) >= 4 else max(scores), 3)
            }
        }
    
    def get_improvement_suggestions(self, critical_files: List[Dict[str, Any]]) -> List[str]:
        """개선 제안 생성"""
        
        suggestions = []
        
        # 고복잡도 파일들에 대한 제안
        high_complexity_files = [
            f for f in critical_files
            if f['metrics'].get('complexity_score', 0) > 0.7
        ]
        
        if high_complexity_files:
            suggestions.append(
                f"고복잡도 핵심 파일 {len(high_complexity_files)}개의 리팩토링을 고려하세요."
            )
        
        # 높은 변경 빈도 파일들에 대한 제안
        high_churn_files = [
            f for f in critical_files
            if f['metrics'].get('churn_risk', 0) > 0.8
        ]
        
        if high_churn_files:
            suggestions.append(
                f"자주 변경되는 핵심 파일 {len(high_churn_files)}개에 대한 테스트 코드를 강화하세요."
            )
        
        # 높은 의존성 파일들에 대한 제안
        high_dependency_files = [
            f for f in critical_files
            if f['metrics'].get('dependency_centrality', 0) > 0.8
        ]
        
        if high_dependency_files:
            suggestions.append(
                f"핵심 의존성 파일 {len(high_dependency_files)}개의 안정성 확보가 중요합니다."
            )
        
        # 설정 파일들에 대한 제안
        config_files = [
            f for f in critical_files
            if f['metrics'].get('structural_importance', 0) > 0.9
            and ('config' in f['file_path'].lower() or 'package.json' in f['file_path'])
        ]
        
        if config_files:
            suggestions.append(
                "핵심 설정 파일들의 백업 및 버전 관리를 철저히 하세요."
            )
        
        # 기본 제안들
        if len(critical_files) > 5:
            suggestions.append(
                "핵심 파일이 많습니다. 아키텍처 단순화를 고려해보세요."
            )
        
        if not suggestions:
            suggestions.append(
                "현재 프로젝트 구조가 양호합니다. 지속적인 모니터링을 권장합니다."
            )
        
        return suggestions
    
    def analyze_project_file_importance(
        self,
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """프로젝트 전체 파일 중요도 분석"""
        
        # 핵심 파일 식별 (더 많은 파일 포함)
        critical_files = self.identify_critical_files(
            dependency_centrality, churn_metrics, complexity_metrics, top_n=15
        )
        
        # 중요도 분포 계산
        distribution = self.calculate_importance_distribution(
            dependency_centrality, churn_metrics, complexity_metrics
        )
        
        # 파일 분류
        categorized = self.categorize_files_by_importance(
            dependency_centrality, churn_metrics, complexity_metrics
        )
        
        # 개선 제안
        suggestions = self.get_improvement_suggestions(critical_files)
        
        # 요약 정보
        total_files = len(set(
            list(dependency_centrality.keys()) +
            list(churn_metrics.keys()) +
            list(complexity_metrics.keys())
        ))
        
        summary = {
            'total_files_analyzed': total_files,
            'critical_files_count': len(categorized['critical']),
            'important_files_count': len(categorized['important']),
            'average_importance': distribution.get('mean', 0.0),
            'highest_importance': distribution.get('max', 0.0)
        }
        
        return {
            'critical_files': critical_files,
            'files': critical_files,  # 호환성을 위해 같은 데이터를 files에도 제공
            'importance_distribution': distribution,
            'categorized_files': categorized,
            'improvement_suggestions': suggestions,
            'summary': summary
        }
    
    async def analyze_repository(
        self,
        repo_url: str,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """저장소 전체 파일 중요도 분석 (GitHub API 데이터 기반)"""
        
        try:
            print(f"[DEBUG] SmartFileImportanceAnalyzer.analyze_repository 시작")
            
            # 기본 데이터 추출
            key_files = analysis_data.get('key_files', [])
            tech_stack = analysis_data.get('tech_stack', {})
            
            # 파일 경로 목록 생성 (Bootstrap 파일 제외)
            file_paths = []
            for f in key_files:
                if isinstance(f, dict):
                    path = f.get('path')
                elif hasattr(f, 'path'):
                    path = f.path
                else:
                    path = str(f)
                if path and not self.is_excluded_file(path):  # Bootstrap 파일 제외
                    file_paths.append(path)
            
            print(f"[DEBUG] 분석 대상 파일 수: {len(file_paths)}")
            
            # 실제 Git 변경 이력 분석
            print(f"[DEBUG] 실제 Git 변경 이력 분석 시작...")
            churn_metrics = self.git_analyzer.analyze_repository_churn(file_paths)
            
            # 실제 의존성 중심성 분석
            print(f"[DEBUG] 실제 의존성 중심성 분석 시작...")
            
            # key_files에서 파일 내용 추출
            file_contents = {}
            for f in key_files:
                file_path = None
                if isinstance(f, dict):
                    file_path = f.get('path')
                    content = f.get('content', '')
                elif hasattr(f, 'path'):
                    file_path = f.path
                    content = getattr(f, 'content', '')
                else:
                    continue
                    
                if file_path and not self.is_excluded_file(file_path) and content:
                    # 내용이 없거나 오류 메시지인 경우 제외
                    if not content.startswith('# File'):
                        file_contents[file_path] = content
            
            print(f"[DEBUG] 의존성 분석 대상 파일: {len(file_contents)}개")
            
            # 실제 의존성 중심성 계산
            if file_contents:
                dependency_centrality = self.dependency_analyzer.analyze_code_dependency_centrality(file_contents)
            else:
                # 내용이 없는 경우 기본값 사용
                dependency_centrality = {}
                for file_path in file_paths:
                    if file_path:
                        structural_score = self.calculate_structural_importance(file_path)
                        dependency_centrality[file_path] = min(0.8, structural_score * 0.6)  # 기본값을 더 보수적으로
            
            # 실제 복잡도 분석
            print(f"[DEBUG] 실제 복잡도 분석 시작...")
            complexity_metrics = await self._analyze_files_complexity_with_content(file_paths)
            
            # 향상된 메타데이터 분석 수행
            print(f"[DEBUG] 향상된 메타데이터 분석 시작...")
            enhanced_metadata_scores = self.analyze_enhanced_metadata(key_files)
            
            print(f"[DEBUG] 실제 분석 완료 - Git: {len(churn_metrics)}개, 의존성: {len(dependency_centrality)}개, 복잡도: {len(complexity_metrics)}개, 메타데이터: {len(enhanced_metadata_scores)}개")
            
            # 스마트 파일 중요도 분석 실행 (향상된 메타데이터 사용)
            smart_file_analysis = self.analyze_project_file_importance_with_enhanced_metadata(
                enhanced_metadata_scores, dependency_centrality, churn_metrics, complexity_metrics
            )
            
            print(f"[DEBUG] 스마트 파일 분석 완료 - {len(smart_file_analysis.get('critical_files', []))}개 핵심 파일")
            
            return {
                "success": True,
                "smart_file_analysis": smart_file_analysis
            }
            
        except Exception as e:
            print(f"[ERROR] SmartFileImportanceAnalyzer.analyze_repository 실패: {e}")
            import traceback
            print(f"[ERROR] 스택 트레이스:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": str(e),
                "smart_file_analysis": None
            }
    
    def analyze_enhanced_metadata(self, key_files: List[Dict]) -> Dict[str, float]:
        """향상된 파일 메타데이터 분석 (실제 파일 내용 기반)"""
        print(f"[METADATA_ANALYZER] {len(key_files)}개 파일의 향상된 메타데이터 분석 시작")
        
        metadata_scores = {}
        
        for f in key_files:
            if not isinstance(f, dict):
                continue
                
            file_path = f.get('path')
            if not file_path or self.is_excluded_file(file_path):
                continue
            
            # 기본 메타데이터
            file_size = f.get('size', 0)
            content = f.get('content', '')
            
            # 1. 파일 크기 점수 (0-1 정규화, 로그 스케일)
            if file_size > 0:
                # 로그 스케일로 정규화 (너무 큰 파일에 대한 과도한 가중치 방지)
                size_score = min(1.0, math.log(file_size + 1) / math.log(50000))  # 50KB를 기준점으로
            else:
                size_score = 0.1
            
            # 2. 확장자 기반 중요도 점수
            ext_score = self._calculate_extension_importance(file_path)
            
            # 3. 디렉토리 위치 중요도
            location_score = self._calculate_location_importance(file_path)
            
            # 4. 코드 내용 분석 (실제 내용이 있는 경우)
            content_metrics = self._analyze_content_metrics(content, file_path)
            
            # 5. 설정 파일 여부
            config_score = self._calculate_config_importance(file_path)
            
            # 6. 구조적 중요도 (기존)
            structural_score = self.calculate_structural_importance(file_path)
            
            # 통합 메타데이터 점수 계산
            # 가중치: 구조적(25%) + 내용(25%) + 위치(20%) + 확장자(15%) + 크기(10%) + 설정(5%)
            integrated_score = (
                structural_score * 0.25 +
                content_metrics['overall_score'] * 0.25 +
                location_score * 0.20 +
                ext_score * 0.15 +
                size_score * 0.10 +
                config_score * 0.05
            )
            
            # 0.05 ~ 1.0 범위로 조정
            metadata_scores[file_path] = max(0.05, min(1.0, integrated_score))
            
            # 디버그 정보 출력 (상위 파일들)
            if integrated_score > 0.7:
                print(f"[METADATA_ANALYZER] 고중요도 파일: {file_path} (점수: {integrated_score:.3f})")
                print(f"  - 구조적: {structural_score:.3f}, 내용: {content_metrics['overall_score']:.3f}")
                print(f"  - 위치: {location_score:.3f}, 확장자: {ext_score:.3f}, 크기: {size_score:.3f}")
        
        print(f"[METADATA_ANALYZER] 향상된 메타데이터 분석 완료: {len(metadata_scores)}개 파일")
        if metadata_scores:
            avg_score = sum(metadata_scores.values()) / len(metadata_scores)
            print(f"[METADATA_ANALYZER] - 평균 메타데이터 점수: {avg_score:.3f}")
            high_score_files = [fp for fp, score in metadata_scores.items() if score > 0.7]
            print(f"[METADATA_ANALYZER] - 고점수 파일: {len(high_score_files)}개")
        
        return metadata_scores
    
    def _calculate_extension_importance(self, file_path: str) -> float:
        """확장자 기반 중요도 점수"""
        ext = Path(file_path).suffix.lower()
        
        # 확장자별 중요도 매핑
        extension_weights = {
            # 소스 코드 (높음)
            '.py': 0.9, '.js': 0.9, '.ts': 0.9, '.tsx': 0.9, '.jsx': 0.9,
            '.java': 0.8, '.go': 0.8, '.rs': 0.8, '.cpp': 0.8, '.c': 0.8,
            '.php': 0.7, '.rb': 0.7, '.cs': 0.7, '.kt': 0.7,
            
            # 설정 파일 (매우 높음)
            '.json': 0.95, '.yaml': 0.9, '.yml': 0.9, '.toml': 0.9,
            '.ini': 0.8, '.conf': 0.8, '.config': 0.8,
            
            # 웹 파일
            '.html': 0.7, '.css': 0.6, '.scss': 0.6, '.less': 0.6,
            '.vue': 0.8, '.svelte': 0.8,
            
            # 문서
            '.md': 0.6, '.rst': 0.5, '.txt': 0.3,
            
            # 기타
            '.xml': 0.7, '.sql': 0.7, '.sh': 0.8, '.bat': 0.6,
            '.dockerfile': 0.9, '.gitignore': 0.6
        }
        
        return extension_weights.get(ext, 0.4)  # 기본값
    
    def _calculate_location_importance(self, file_path: str) -> float:
        """디렉토리 위치 기반 중요도"""
        path_parts = Path(file_path).parts
        
        # 루트 레벨 파일들은 높은 점수
        if len(path_parts) == 1:
            return 0.95
        
        # 중요한 디렉토리들
        important_dirs = {
            'src': 0.9, 'lib': 0.8, 'app': 0.9, 'main': 0.9,
            'components': 0.8, 'pages': 0.8, 'api': 0.9,
            'services': 0.8, 'utils': 0.7, 'helpers': 0.7,
            'models': 0.8, 'controllers': 0.8, 'views': 0.8,
            'routes': 0.8, 'middleware': 0.8, 'config': 0.9,
            'core': 0.9, 'base': 0.8, 'common': 0.7,
            'types': 0.7, 'interfaces': 0.7, 'schemas': 0.8
        }
        
        # 덜 중요한 디렉토리들
        less_important_dirs = {
            'tests': 0.3, 'test': 0.3, '__tests__': 0.3,
            'spec': 0.3, 'docs': 0.4, 'documentation': 0.4,
            'examples': 0.3, 'demo': 0.3, 'samples': 0.3,
            'node_modules': 0.1, 'vendor': 0.2, 'dist': 0.2,
            'build': 0.2, 'assets': 0.4, 'static': 0.4,
            'public': 0.5, 'tmp': 0.1, 'temp': 0.1
        }
        
        # 첫 번째 디렉토리 확인
        first_dir = path_parts[0].lower()
        if first_dir in less_important_dirs:
            return less_important_dirs[first_dir]
        elif first_dir in important_dirs:
            base_score = important_dirs[first_dir]
        else:
            base_score = 0.6
        
        # 깊이에 따른 감점 (너무 깊은 파일은 덜 중요)
        depth_penalty = max(0.0, (len(path_parts) - 3) * 0.1)
        
        return max(0.1, base_score - depth_penalty)
    
    def _analyze_content_metrics(self, content: str, file_path: str) -> Dict[str, float]:
        """파일 내용 기반 메트릭 분석"""
        if not content or content.startswith('# File'):
            return {'overall_score': 0.5, 'complexity_indicator': 0.5, 'documentation_ratio': 0.0}
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return {'overall_score': 0.1, 'complexity_indicator': 0.0, 'documentation_ratio': 0.0}
        
        # 1. 코드 밀도 분석
        non_empty_lines = len([line for line in lines if line.strip()])
        code_density = non_empty_lines / total_lines if total_lines > 0 else 0
        
        # 2. 주석/문서 비율
        comment_patterns = [r'^\s*#', r'^\s*//', r'^\s*/\*', r'^\s*"""', r"^\s*'''"]
        comment_lines = 0
        
        for line in lines:
            for pattern in comment_patterns:
                if re.match(pattern, line):
                    comment_lines += 1
                    break
        
        documentation_ratio = comment_lines / total_lines if total_lines > 0 else 0
        
        # 3. 복잡성 지표 (키워드, 구조 패턴)
        complexity_keywords = [
            'class', 'function', 'def', 'async', 'await',
            'if', 'for', 'while', 'try', 'catch', 'except',
            'import', 'export', 'const', 'let', 'var'
        ]
        
        keyword_count = 0
        for keyword in complexity_keywords:
            keyword_count += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
        
        # 키워드 밀도 (라인당 키워드 수)
        keyword_density = keyword_count / total_lines if total_lines > 0 else 0
        
        # 4. 특별한 패턴 (export, API endpoint 등)
        special_patterns = [
            r'export\s+(default\s+)?(class|function|const)',
            r'app\.(get|post|put|delete|patch)',
            r'@\w+\(',  # 데코레이터
            r'class\s+\w+.*:',  # 클래스 정의
            r'interface\s+\w+',  # 인터페이스
            r'type\s+\w+\s*='   # 타입 정의
        ]
        
        special_pattern_count = 0
        for pattern in special_patterns:
            special_pattern_count += len(re.findall(pattern, content, re.IGNORECASE))
        
        special_pattern_density = special_pattern_count / total_lines if total_lines > 0 else 0
        
        # 5. 통합 점수 계산
        # 코드 밀도(30%) + 키워드 밀도(40%) + 특별 패턴(20%) + 문서화(10%)
        complexity_score = min(1.0, 
            code_density * 0.3 +
            min(1.0, keyword_density * 10) * 0.4 +  # 정규화
            min(1.0, special_pattern_density * 20) * 0.2 +  # 정규화
            min(1.0, documentation_ratio * 5) * 0.1  # 적절한 문서화 보너스
        )
        
        return {
            'overall_score': max(0.1, complexity_score),
            'complexity_indicator': min(1.0, keyword_density * 10),
            'documentation_ratio': documentation_ratio,
            'code_density': code_density,
            'special_patterns': special_pattern_count
        }
    
    def _calculate_config_importance(self, file_path: str) -> float:
        """설정 파일 여부 및 중요도"""
        file_name = Path(file_path).name.lower()
        
        # 매우 중요한 설정 파일들
        critical_configs = [
            'package.json', 'requirements.txt', 'cargo.toml', 'go.mod', 'pom.xml',
            'dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            'makefile', 'cmake.txt', 'build.gradle',
            'webpack.config.js', 'vite.config.js', 'vite.config.ts',
            'tsconfig.json', 'jsconfig.json', 'babel.config.js',
            '.env', '.env.example', '.env.local', 'config.json', 'settings.py'
        ]
        
        # 중요한 설정 파일들
        important_configs = [
            '.gitignore', '.dockerignore', '.eslintrc', '.prettierrc',
            'jest.config.js', 'vitest.config.js', 'tailwind.config.js',
            'next.config.js', 'nuxt.config.js', 'vue.config.js',
            'svelte.config.js', 'rollup.config.js'
        ]
        
        if file_name in critical_configs:
            return 1.0
        elif file_name in important_configs:
            return 0.8
        elif file_name.startswith('.') and ('config' in file_name or 'rc' in file_name):
            return 0.7
        elif 'config' in file_name or 'setting' in file_name:
            return 0.6
        else:
            return 0.0
    
    def analyze_project_file_importance_with_enhanced_metadata(
        self,
        enhanced_metadata_scores: Dict[str, float],
        dependency_centrality: Dict[str, float],
        churn_metrics: Dict[str, Dict[str, Any]],
        complexity_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """향상된 메타데이터를 사용한 프로젝트 파일 중요도 분석"""
        
        print(f"[ENHANCED_ANALYZER] 향상된 메타데이터 기반 파일 중요도 분석 시작")
        
        # 모든 파일 경로 수집
        all_files = set()
        all_files.update(enhanced_metadata_scores.keys())
        all_files.update(dependency_centrality.keys())
        all_files.update(churn_metrics.keys())
        all_files.update(complexity_metrics.keys())
        
        print(f"[ENHANCED_ANALYZER] 전체 분석 파일 수: {len(all_files)}")
        
        # 복잡도 메트릭을 float 형태로 정규화
        normalized_complexity = {}
        for file_path, metrics in complexity_metrics.items():
            if isinstance(metrics, dict):
                # 순환복잡도와 유지보수성 지수를 조합
                cyclomatic = metrics.get('cyclomatic_complexity', 0)
                maintainability = metrics.get('maintainability_index', 100)
                
                # 정규화: 높은 복잡도 = 낮은 점수, 낮은 유지보수성 = 낮은 점수
                complexity_score = min(1.0, cyclomatic / 20.0) * 0.6  # 복잡도 패널티
                maintainability_score = maintainability / 100.0 * 0.4  # 유지보수성 보너스
                
                normalized_complexity[file_path] = max(0.05, complexity_score + maintainability_score)
            else:
                normalized_complexity[file_path] = 0.5
        
        # churn 메트릭을 float 형태로 정규화
        normalized_churn = {}
        for file_path, churn_data in churn_metrics.items():
            if isinstance(churn_data, dict):
                # 여러 churn 메트릭을 조합
                commit_freq = min(1.0, churn_data.get('commit_frequency', 1) / 20.0)
                recent_activity = churn_data.get('recent_activity', 0.1)
                bug_fix_ratio = churn_data.get('bug_fix_ratio', 0.1)
                stability = churn_data.get('stability_score', 0.8)
                
                # 통합 churn 점수: 변경 빈도와 최근 활동도는 높을수록 중요, 안정성도 고려
                churn_score = (
                    commit_freq * 0.3 +
                    recent_activity * 0.3 +
                    bug_fix_ratio * 0.2 +  # 버그 수정이 많은 파일은 중요
                    (1.0 - stability) * 0.2  # 불안정한 파일도 주의 필요
                )
                
                normalized_churn[file_path] = max(0.05, min(1.0, churn_score))
            else:
                normalized_churn[file_path] = float(churn_data) if isinstance(churn_data, (int, float)) else 0.3
        
        # 4차원 통합 중요도 점수 계산
        importance_scores = {}
        
        for file_path in all_files:
            if not file_path:
                continue
                
            # 각 차원별 점수 (0-1 정규화)
            metadata_score = enhanced_metadata_scores.get(file_path, 0.5)
            centrality_score = dependency_centrality.get(file_path, 0.1)
            churn_score = normalized_churn.get(file_path, 0.3)
            complexity_score = normalized_complexity.get(file_path, 0.5)
            
            # 기획서 요구사항에 따른 가중치 적용
            # 메타데이터 40% + 의존성 30% + 변경빈도 20% + 복잡도 10%
            final_score = (
                self.importance_weights['metadata'] * metadata_score +
                self.importance_weights['dependency'] * centrality_score +
                self.importance_weights['churn'] * churn_score +
                self.importance_weights['complexity'] * complexity_score
            )
            
            importance_scores[file_path] = max(0.05, min(1.0, final_score))
        
        # 중요도 기준으로 파일 분류 및 정렬
        sorted_files = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 파일들 선별
        critical_files = []
        for file_path, score in sorted_files:
            # 상세 정보 구성
            file_info = {
                'path': file_path,
                'importance_score': round(score, 4),
                'metadata_score': round(enhanced_metadata_scores.get(file_path, 0.5), 4),
                'dependency_score': round(dependency_centrality.get(file_path, 0.1), 4),
                'churn_score': round(normalized_churn.get(file_path, 0.3), 4),
                'complexity_score': round(normalized_complexity.get(file_path, 0.5), 4)
            }
            
            # 중요도 레벨 분류
            if score >= 0.8:
                file_info['importance_level'] = 'critical'
            elif score >= 0.6:
                file_info['importance_level'] = 'high'
            elif score >= 0.4:
                file_info['importance_level'] = 'medium'
            else:
                file_info['importance_level'] = 'low'
            
            critical_files.append(file_info)
        
        # 통계 계산
        scores = list(importance_scores.values())
        distribution = {
            'min': round(min(scores), 4) if scores else 0,
            'max': round(max(scores), 4) if scores else 0,
            'mean': round(sum(scores) / len(scores), 4) if scores else 0,
            'median': round(statistics.median(scores), 4) if scores else 0
        }
        
        # 레벨별 분류
        categorized = {
            'critical': len([f for f in critical_files if f['importance_level'] == 'critical']),
            'high': len([f for f in critical_files if f['importance_level'] == 'high']),
            'medium': len([f for f in critical_files if f['importance_level'] == 'medium']),
            'low': len([f for f in critical_files if f['importance_level'] == 'low'])
        }
        
        print(f"[ENHANCED_ANALYZER] 향상된 분석 완료:")
        print(f"[ENHANCED_ANALYZER] - 전체 파일: {len(critical_files)}개")
        print(f"[ENHANCED_ANALYZER] - Critical: {categorized['critical']}개, High: {categorized['high']}개")
        print(f"[ENHANCED_ANALYZER] - 평균 점수: {distribution['mean']:.3f}")
        
        # 상위 5개 파일 로깅
        top_files = critical_files[:5]
        print(f"[ENHANCED_ANALYZER] 상위 5개 파일:")
        for i, f in enumerate(top_files, 1):
            print(f"[ENHANCED_ANALYZER]   {i}. {f['path']} (점수: {f['importance_score']:.3f}, 레벨: {f['importance_level']})")
        
        return {
            'critical_files': critical_files,
            'files': critical_files,  # 호환성을 위해
            'importance_distribution': distribution,
            'categorized_files': categorized,
            'total_analyzed': len(critical_files),
            'analysis_method': 'enhanced_metadata_based',
            'summary': {
                'total_files': len(critical_files),
                'average_importance': distribution['mean'],
                'highest_importance': distribution['max']
            }
        }