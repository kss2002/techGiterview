"""
Dependency Analyzer

NetworkX 라이브러리를 활용한 의존성 그래프 분석 시스템
package.json, requirements.txt, pom.xml 등 파일 파싱하여 의존성 트리 구성
"""

import json
import re
import xml.etree.ElementTree as ET
import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import networkx as nx


@dataclass
class DependencyNode:
    """의존성 노드 정보"""
    name: str
    version: str
    dependency_type: str  # production, development, test
    file_source: str  # 어떤 파일에서 발견되었는지


@dataclass
class CentralityMetrics:
    """중앙성 지표"""
    betweenness: Dict[str, float]
    closeness: Dict[str, float]  
    pagerank: Dict[str, float]
    weighted_importance: Dict[str, float]


@dataclass
class DependencyGraph:
    """의존성 그래프 결과"""
    dependencies: Dict[str, DependencyNode]
    centrality_metrics: CentralityMetrics
    total_dependencies: int
    production_count: int
    development_count: int
    test_count: int = 0


class DependencyAnalyzer:
    """의존성 그래프 분석기"""
    
    def __init__(self):
        """초기화"""
        self.supported_files = {
            "package.json": self._parse_package_json,
            "requirements.txt": self._parse_requirements_txt,
            "pom.xml": self._parse_pom_xml,
            "Cargo.toml": self._parse_cargo_toml,
            "go.mod": self._parse_go_mod
        }
    
    async def analyze_dependencies(self, repo_path: str) -> DependencyGraph:
        """
        저장소의 의존성을 분석하여 그래프 구성
        
        Args:
            repo_path: 저장소 경로
            
        Returns:
            DependencyGraph: 의존성 분석 결과
        """
        # 1. 의존성 파일 탐색 및 파싱
        all_dependencies = self._find_dependency_files(repo_path)
        
        if not all_dependencies:
            return DependencyGraph(
                dependencies={},
                centrality_metrics=CentralityMetrics({}, {}, {}, {}),
                total_dependencies=0,
                production_count=0,
                development_count=0
            )
        
        # 2. NetworkX 그래프 구성
        graph = self._build_dependency_graph(all_dependencies)
        
        # 3. 중앙성 지표 계산
        centrality_metrics = self._calculate_centrality_metrics(graph)
        
        # 4. 깊이별 가중치 적용
        weighted_metrics = self._apply_depth_weights(graph)
        centrality_metrics.update(weighted_metrics)
        
        # 5. DependencyNode 객체들 생성
        dependency_nodes = {}
        for name, attrs in graph.nodes(data=True):
            dependency_nodes[name] = DependencyNode(
                name=name,
                version=attrs.get('version', 'unknown'),
                dependency_type=attrs.get('type', 'production'),
                file_source=attrs.get('source', 'unknown')
            )
        
        # 6. 통계 계산
        production_count = sum(1 for node in dependency_nodes.values() 
                             if node.dependency_type == 'production')
        development_count = sum(1 for node in dependency_nodes.values() 
                              if node.dependency_type == 'development')
        test_count = sum(1 for node in dependency_nodes.values() 
                        if node.dependency_type == 'test')
        
        return DependencyGraph(
            dependencies=dependency_nodes,
            centrality_metrics=CentralityMetrics(
                betweenness=centrality_metrics.get('betweenness', {}),
                closeness=centrality_metrics.get('closeness', {}),
                pagerank=centrality_metrics.get('pagerank', {}),
                weighted_importance=centrality_metrics.get('weighted_importance', {})
            ),
            total_dependencies=len(dependency_nodes),
            production_count=production_count,
            development_count=development_count,
            test_count=test_count
        )
    
    def _find_dependency_files(self, repo_path: str) -> Dict[str, Any]:
        """저장소에서 의존성 파일들을 찾아 파싱"""
        all_dependencies = {}
        repo_path = Path(repo_path)
        
        for filename, parser in self.supported_files.items():
            file_path = repo_path / filename
            if file_path.exists():
                try:
                    dependencies = parser(str(file_path))
                    all_dependencies.update(dependencies)
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")
                    continue
        
        return all_dependencies
    
    def _parse_package_json(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """package.json 파일 파싱"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in package.json")
        
        dependencies = {}
        
        # production dependencies
        for name, version in data.get('dependencies', {}).items():
            dependencies[name] = {
                'version': version,
                'type': 'production',
                'source': 'package.json'
            }
        
        # development dependencies  
        for name, version in data.get('devDependencies', {}).items():
            dependencies[name] = {
                'version': version,
                'type': 'development',
                'source': 'package.json'
            }
        
        return dependencies
    
    def _parse_requirements_txt(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """requirements.txt 파일 파싱"""
        dependencies = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 버전 정보 파싱 (name==version, name>=version 등)
                match = re.match(r'^([a-zA-Z0-9_-]+(?:\[[^\]]*\])?)(.*)', line)
                if match:
                    name = match.group(1)
                    version_part = match.group(2).strip()
                    
                    # 버전 정보가 있으면 전체 유지, 없으면 'latest'
                    version = version_part if version_part else 'latest'
                    
                    dependencies[name] = {
                        'version': version,
                        'type': 'production',
                        'source': 'requirements.txt'
                    }
        
        return dependencies
    
    def _parse_pom_xml(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """pom.xml 파일 파싱"""
        dependencies = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # XML 네임스페이스 처리
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            if root.tag.startswith('{'):
                namespace_uri = root.tag.split('}')[0][1:]
                namespace = {'maven': namespace_uri}
            
            # dependencies 섹션 찾기
            deps_section = root.find('.//maven:dependencies', namespace)
            if deps_section is None:
                deps_section = root.find('.//dependencies')  # 네임스페이스 없이 시도
            
            if deps_section is not None:
                for dep in deps_section.findall('.//maven:dependency', namespace):
                    if dep is None:
                        dep = deps_section.find('.//dependency')  # 네임스페이스 없이 시도
                    
                    artifact_id = dep.find('.//maven:artifactId', namespace)
                    version = dep.find('.//maven:version', namespace)
                    scope = dep.find('.//maven:scope', namespace)
                    
                    if artifact_id is None:
                        artifact_id = dep.find('.//artifactId')
                    if version is None:
                        version = dep.find('.//version')
                    if scope is None:
                        scope = dep.find('.//scope')
                    
                    if artifact_id is not None:
                        name = artifact_id.text
                        version_text = version.text if version is not None else 'unknown'
                        scope_text = scope.text if scope is not None else 'compile'
                        
                        dep_type = 'test' if scope_text == 'test' else 'production'
                        
                        dependencies[name] = {
                            'version': version_text,
                            'type': dep_type,
                            'source': 'pom.xml'
                        }
            
        except ET.ParseError:
            raise ValueError("Invalid XML format in pom.xml")
        
        return dependencies
    
    def _parse_cargo_toml(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """Cargo.toml 파일 파싱 (기본 구현)"""
        # 간단한 정규식 기반 파싱 (toml 라이브러리 없이)
        dependencies = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # [dependencies] 섹션 찾기
            deps_match = re.search(r'\[dependencies\](.*?)(?=\[|$)', content, re.DOTALL)
            if deps_match:
                deps_section = deps_match.group(1)
                
                # name = "version" 패턴 찾기
                for line in deps_section.split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        parts = line.split('=', 1)
                        name = parts[0].strip()
                        version = parts[1].strip().strip('"').strip("'")
                        
                        dependencies[name] = {
                            'version': version,
                            'type': 'production',
                            'source': 'Cargo.toml'
                        }
        except Exception:
            pass  # 파싱 실패 시 빈 딕셔너리 반환
        
        return dependencies
    
    def _parse_go_mod(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """go.mod 파일 파싱 (기본 구현)"""
        dependencies = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('require '):
                        # require github.com/gorilla/mux v1.8.0
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[1]
                            version = parts[2]
                            
                            dependencies[name] = {
                                'version': version,
                                'type': 'production',
                                'source': 'go.mod'
                            }
        except Exception:
            pass  # 파싱 실패 시 빈 딕셔너리 반환
        
        return dependencies
    
    def _build_dependency_graph(self, dependencies: Dict[str, Dict[str, str]]) -> nx.DiGraph:
        """의존성 딕셔너리로부터 NetworkX 그래프 구성"""
        graph = nx.DiGraph()
        
        # 노드 추가 (의존성들)
        for name, info in dependencies.items():
            graph.add_node(
                name,
                version=info['version'],
                type=info['type'],
                source=info.get('source', 'unknown')
            )
        
        # 실제 의존성 관계는 파일 내용 분석을 통해 구성 가능
        # 현재는 기본적인 노드만 추가 (추후 확장 가능)
        
        return graph
    
    def _calculate_centrality_metrics(self, graph: nx.DiGraph) -> Dict[str, Dict[str, float]]:
        """중앙성 지표 계산"""
        metrics = {}
        
        if graph.number_of_nodes() == 0:
            return {
                'betweenness': {},
                'closeness': {},
                'pagerank': {}
            }
        
        try:
            # Betweenness Centrality (중개 중앙성)
            metrics['betweenness'] = nx.betweenness_centrality(graph)
            
            # Closeness Centrality (근접 중앙성)
            if nx.is_strongly_connected(graph) or graph.number_of_nodes() == 1:
                metrics['closeness'] = nx.closeness_centrality(graph)
            else:
                # 강하게 연결되지 않은 그래프의 경우 각 연결 컴포넌트별로 계산
                metrics['closeness'] = {}
                for node in graph.nodes():
                    try:
                        metrics['closeness'][node] = nx.closeness_centrality(graph, node)
                    except:
                        metrics['closeness'][node] = 0.0
            
            # PageRank (페이지랭크)
            if graph.number_of_edges() > 0:
                metrics['pagerank'] = nx.pagerank(graph, alpha=0.85, max_iter=100, tol=1e-6)
            else:
                # 엣지가 없는 경우 균등 분배
                metrics['pagerank'] = {node: 1.0 / graph.number_of_nodes() 
                                     for node in graph.nodes()}
                
        except Exception as e:
            # 계산 실패 시 기본값 설정
            print(f"Error calculating centrality metrics: {e}")
            default_value = 1.0 / max(1, graph.number_of_nodes())
            metrics = {
                'betweenness': {node: default_value for node in graph.nodes()},
                'closeness': {node: default_value for node in graph.nodes()},
                'pagerank': {node: default_value for node in graph.nodes()}
            }
        
        return metrics
    
    def _apply_depth_weights(self, graph: nx.DiGraph) -> Dict[str, Dict[str, float]]:
        """의존성 깊이별 가중치 적용"""
        weighted_importance = {}
        
        if graph.number_of_nodes() == 0:
            return {'weighted_importance': {}}
        
        # 각 노드의 깊이 계산 (루트에서의 거리)
        # 여러 루트가 있을 수 있으므로 in-degree가 0인 노드들을 루트로 간주
        roots = [node for node in graph.nodes() if graph.in_degree(node) == 0]
        
        if not roots:
            # 순환 의존성이 있는 경우 모든 노드를 동등하게 처리
            base_weight = 1.0
            for node in graph.nodes():
                weighted_importance[node] = base_weight
        else:
            # 루트에서의 최단 거리 기반 가중치 계산
            for node in graph.nodes():
                min_depth = float('inf')
                
                for root in roots:
                    try:
                        if nx.has_path(graph, root, node):
                            depth = nx.shortest_path_length(graph, root, node)
                            min_depth = min(min_depth, depth)
                        elif root == node:
                            min_depth = 0
                    except nx.NetworkXNoPath:
                        continue
                
                if min_depth == float('inf'):
                    min_depth = 0  # 연결되지 않은 노드는 깊이 0으로 처리
                
                # 깊이별 가중치: 깊이가 깊을수록 낮은 가중치
                # weight = 1 / (1 + depth * 0.5)
                weight = 1.0 / (1.0 + min_depth * 0.5)
                weighted_importance[node] = weight
        
        return {'weighted_importance': weighted_importance}
    
    # ========== 코드 레벨 의존성 분석 (새로 추가) ==========
    
    def detect_language(self, file_path: str) -> str:
        """파일 확장자로 언어 감지"""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        return language_map.get(ext, 'unknown')
    
    def extract_imports_from_content(self, content: str, language: str) -> Set[str]:
        """파일 내용에서 import 문 추출"""
        imports = set()
        
        # 언어별 import 패턴
        import_patterns = {
            'python': [
                r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
                r'^\s*from\s+\.\s*import\s+([a-zA-Z_][a-zA-Z0-9_.,\s]+)',
                r'^\s*from\s+\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import'
            ],
            'javascript': [
                r'^\s*import\s+.*\s+from\s+[\'"]([^\'\"]+)[\'"]',
                r'^\s*const\s+.*\s*=\s*require\([\'"]([^\'\"]+)[\'"]\)',
                r'^\s*import\s+[\'"]([^\'\"]+)[\'"]',
                r'^\s*import\([\'"]([^\'\"]+)[\'"]\)'
            ],
            'typescript': [
                r'^\s*import\s+.*\s+from\s+[\'"]([^\'\"]+)[\'"]',
                r'^\s*import\s+[\'"]([^\'\"]+)[\'"]',
                r'^\s*import\s+type\s+.*\s+from\s+[\'"]([^\'\"]+)[\'"]'
            ],
            'java': [
                r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_.]*);',
                r'^\s*import\s+static\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            ],
            'go': [
                r'^\s*import\s+"([^"]+)"',
                r'^\s*import\s+\(\s*"([^"]+)"\s*\)'
            ],
            'rust': [
                r'^\s*use\s+([a-zA-Z_][a-zA-Z0-9_::]*)',
                r'^\s*extern\s+crate\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ]
        }
        
        if language not in import_patterns:
            return imports
        
        patterns = import_patterns[language]
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
                
            for pattern in patterns:
                matches = re.findall(pattern, line, re.MULTILINE)
                for match in matches:
                    if match:
                        # 상대 경로 처리
                        if match.startswith('.'):
                            imports.add(match)
                        else:
                            imports.add(match.split('.')[0])  # 패키지 이름만
        
        # Python AST 파싱 (더 정확한 분석)
        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
            except:
                pass  # AST 파싱 실패 시 regex 결과 사용
        
        return imports
    
    def resolve_local_dependencies(self, file_path: str, imports: Set[str], all_files: List[str]) -> Set[str]:
        """로컬 파일 의존성 해결"""
        local_deps = set()
        file_dir = os.path.dirname(file_path)
        
        # 파일명 매핑 생성
        file_map = {}
        for f in all_files:
            base_name = os.path.splitext(os.path.basename(f))[0]
            file_map[base_name] = f
            
            # 디렉토리명도 포함
            dir_parts = f.split('/')
            for part in dir_parts[:-1]:  # 파일명 제외
                if part and part not in file_map:
                    file_map[part] = f
        
        for imp in imports:
            # 상대 경로 처리
            if imp.startswith('.'):
                relative_path = os.path.join(file_dir, imp.lstrip('.'))
                for f in all_files:
                    if f.startswith(relative_path):
                        local_deps.add(f)
            
            # 모듈명으로 매칭
            elif imp in file_map:
                local_deps.add(file_map[imp])
            
            # 부분 매칭
            else:
                for f in all_files:
                    if imp.lower() in f.lower():
                        local_deps.add(f)
        
        return local_deps
    
    def build_code_dependency_graph(self, file_contents: Dict[str, str], all_repo_files: Optional[List[str]] = None) -> nx.DiGraph:
        """
        코드 레벨 의존성 그래프 구성
        
        Args:
            file_contents: 파일 경로와 내용의 매핑
            all_repo_files: 저장소의 모든 파일 경로 리스트 (Ghost Node 해결용)
        """
        print(f"[DEPENDENCY_ANALYZER] {len(file_contents)}개 파일의 코드 의존성 그래프 구성 시작")
        
        code_graph = nx.DiGraph()
        file_imports = {}
        
        # 1단계: 모든 파일의 import 정보 수집
        # all_repo_files가 제공되지 않으면 file_contents의 키만 사용 (기존 동작 호환)
        all_files = all_repo_files if all_repo_files else list(file_contents.keys())
        
        for file_path, content in file_contents.items():
            if not content or content.startswith('# File'):
                continue
                
            language = self.detect_language(file_path)
            if language == 'unknown':
                continue
            
            # Import 문 추출
            imports = self.extract_imports_from_content(content, language)
            
            # 로컬 의존성 해결
            local_deps = self.resolve_local_dependencies(file_path, imports, all_files)
            
            file_imports[file_path] = {
                'language': language,
                'external_imports': imports - local_deps,
                'local_dependencies': local_deps,
                'total_imports': len(imports)
            }
            
            # 그래프에 노드 추가
            code_graph.add_node(file_path)
        
        # 2단계: 의존성 엣지 추가
        for file_path, import_info in file_imports.items():
            for dep_file in import_info['local_dependencies']:
                # 내용이 없는 파일(Ghost Node)이라도 의존성 관계가 있으면 그래프에 추가
                code_graph.add_edge(file_path, dep_file)
        
        print(f"[DEPENDENCY_ANALYZER] 코드 의존성 그래프 구성 완료: {code_graph.number_of_nodes()}개 노드, {code_graph.number_of_edges()}개 엣지")
        return code_graph
    
    def calculate_code_centrality_metrics(self, code_graph: nx.DiGraph, file_paths: Optional[List[str]] = None) -> Dict[str, float]:
        """코드 레벨 중심성 메트릭 계산"""
        if not code_graph.nodes():
            print("[DEPENDENCY_ANALYZER] 빈 코드 의존성 그래프 - 기본값 반환")
            return {fp: 0.1 for fp in (file_paths or [])}
        
        centrality_scores = {}
        
        try:
            # PageRank 계산 (의존성 중요도)
            pagerank_scores = nx.pagerank(code_graph, alpha=0.85, max_iter=100)
            
            # Betweenness Centrality 계산 (연결 중요도)
            if code_graph.number_of_edges() > 0:
                betweenness_scores = nx.betweenness_centrality(code_graph, k=min(100, len(code_graph.nodes())))
            else:
                betweenness_scores = {node: 0.0 for node in code_graph.nodes()}
            
            # In-degree (피의존성) 계산
            in_degrees = dict(code_graph.in_degree())
            max_in_degree = max(in_degrees.values()) if in_degrees.values() else 1
            
            # Out-degree (의존성) 계산  
            out_degrees = dict(code_graph.out_degree())
            max_out_degree = max(out_degrees.values()) if out_degrees.values() else 1
            
            print(f"[DEPENDENCY_ANALYZER] 코드 중심성 메트릭 계산 완료")
            print(f"[DEPENDENCY_ANALYZER] - PageRank 범위: {min(pagerank_scores.values()):.3f} ~ {max(pagerank_scores.values()):.3f}")
            print(f"[DEPENDENCY_ANALYZER] - Betweenness 범위: {min(betweenness_scores.values()):.3f} ~ {max(betweenness_scores.values()):.3f}")
            print(f"[DEPENDENCY_ANALYZER] - In-degree 범위: 0 ~ {max_in_degree}")
            
            # 점수 계산 대상: 지정된 파일 목록이 있으면 그것만, 없으면 그래프의 모든 노드
            target_nodes = file_paths if file_paths is not None else list(code_graph.nodes())
            
            # 통합 중심성 점수 계산
            for file_path in target_nodes:
                if file_path not in code_graph.nodes():
                    centrality_scores[file_path] = 0.05  # 최소값
                    continue
                
                # PageRank (30%) + Betweenness (25%) + In-degree (25%) + Out-degree (20%)
                pagerank = pagerank_scores.get(file_path, 0.0)
                betweenness = betweenness_scores.get(file_path, 0.0)
                in_degree_norm = in_degrees.get(file_path, 0) / max_in_degree if max_in_degree > 0 else 0
                out_degree_norm = out_degrees.get(file_path, 0) / max_out_degree if max_out_degree > 0 else 0
                
                # 가중 평균으로 통합 점수 계산 (0-1 범위로 정규화)
                integrated_score = (
                    pagerank * 0.30 +
                    betweenness * 0.25 +
                    in_degree_norm * 0.25 +
                    out_degree_norm * 0.20
                )
                
                # 0.05 ~ 1.0 범위로 조정
                centrality_scores[file_path] = max(0.05, min(1.0, integrated_score))
        
        except Exception as e:
            print(f"[DEPENDENCY_ANALYZER] 코드 중심성 계산 오류: {e}")
            # 오류 시 기본값
            centrality_scores = {fp: 0.1 for fp in file_paths}
        
        return centrality_scores
    
    def analyze_code_dependency_centrality(self, file_contents: Dict[str, str]) -> Dict[str, float]:
        """코드 레벨 의존성 중심성 종합 분석"""
        print(f"[DEPENDENCY_ANALYZER] 코드 의존성 중심성 분석 시작: {len(file_contents)}개 파일")
        
        # 1. 코드 의존성 그래프 구성
        code_graph = self.build_code_dependency_graph(file_contents)
        
        # 2. 중심성 메트릭 계산
        file_paths = list(file_contents.keys())
        centrality_scores = self.calculate_code_centrality_metrics(code_graph, file_paths)
        
        # 3. 결과 요약
        if centrality_scores:
            avg_score = sum(centrality_scores.values()) / len(centrality_scores)
            high_centrality_files = [fp for fp, score in centrality_scores.items() if score > avg_score * 1.5]
            
            print(f"[DEPENDENCY_ANALYZER] 코드 중심성 분석 완료")
            print(f"[DEPENDENCY_ANALYZER] - 평균 중심성: {avg_score:.3f}")
            print(f"[DEPENDENCY_ANALYZER] - 고중심성 파일: {len(high_centrality_files)}개")
            if high_centrality_files[:5]:
                print(f"[DEPENDENCY_ANALYZER] - 상위 파일: {[os.path.basename(f) for f in high_centrality_files[:5]]}")
        
        return centrality_scores