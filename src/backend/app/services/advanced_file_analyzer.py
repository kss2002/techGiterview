"""
Advanced File Analyzer Service

메타정보, 의존성 그래프, 변경 이력, 복잡도를 종합적으로 활용한 고도화된 파일 분석 시스템
"""

import ast
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, Counter
import networkx as nx
from datetime import datetime, timedelta

from app.services.github_client import GitHubClient
from app.core.config import settings


@dataclass
class FileMetrics:
    """파일별 종합 메트릭"""
    path: str
    
    # 기본 메타정보
    size: int = 0
    lines_of_code: int = 0
    language: str = "unknown"
    
    # 복잡도 메트릭
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    halstead_complexity: float = 0.0
    maintainability_index: float = 0.0
    
    # 의존성 메트릭
    fan_in: int = 0  # 이 파일을 참조하는 파일 수
    fan_out: int = 0  # 이 파일이 참조하는 파일 수
    dependency_depth: int = 0  # 의존성 트리에서의 깊이
    centrality_score: float = 0.0  # 네트워크 중심성 점수
    
    # 변경 이력 메트릭
    commit_frequency: int = 0  # 총 커밋 횟수
    recent_commits: int = 0  # 최근 6개월 커밋 횟수
    authors_count: int = 0  # 기여한 개발자 수
    average_commit_size: float = 0.0  # 평균 변경 라인 수
    hotspot_score: float = 0.0  # 변경 빈도 * 복잡도
    
    # 종합 점수
    importance_score: float = 0.0
    quality_risk_score: float = 0.0
    
    # 추가 메타데이터
    file_type: str = "unknown"
    is_test_file: bool = False
    is_config_file: bool = False
    has_main_function: bool = False


@dataclass 
class DependencyGraph:
    """의존성 그래프 정보"""
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    import_relationships: Dict[str, List[str]] = field(default_factory=dict)
    module_clusters: List[List[str]] = field(default_factory=list)
    critical_paths: List[List[str]] = field(default_factory=list)


@dataclass
class ChurnAnalysis:
    """변경 이력 분석 결과"""
    file_churns: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hotspots: List[Dict[str, Any]] = field(default_factory=list) 
    author_statistics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    temporal_patterns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


class AdvancedFileAnalyzer:
    """고도화된 파일 분석기"""
    
    def __init__(self):
        self.github_client = GitHubClient()
        
        # 언어별 복잡도 분석 패턴
        self.complexity_patterns = {
            'python': {
                'decision_points': [r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bexcept\b', r'\band\b', r'\bor\b'],
                'nesting_indicators': [r':\s*$'],
                'function_def': r'^\s*def\s+(\w+)',
                'class_def': r'^\s*class\s+(\w+)',
                'import_patterns': [r'^\s*import\s+(\w+)', r'^\s*from\s+(\w+)\s+import']
            },
            'javascript': {
                'decision_points': [r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bcatch\b', r'\b&&\b', r'\|\|'],
                'nesting_indicators': [r'\{'],
                'function_def': r'function\s+(\w+)|(\w+)\s*=\s*\(',
                'class_def': r'class\s+(\w+)',
                'import_patterns': [r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', r'require\s*\(\s*[\'"]([^\'"]+)[\'"]']
            },
            'java': {
                'decision_points': [r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bcatch\b', r'\b&&\b', r'\|\|'],
                'nesting_indicators': [r'\{'],
                'function_def': r'(public|private|protected)?\s*\w+\s+(\w+)\s*\(',
                'class_def': r'class\s+(\w+)',
                'import_patterns': [r'import\s+([^;]+);']
            }
        }
    
    async def analyze_repository_advanced(self, repo_url: str) -> Dict[str, Any]:
        """고도화된 저장소 분석 수행"""
        
        print(f"[고도화 분석] 저장소 분석 시작: {repo_url}")
        
        try:
            # GitHub 클라이언트를 컨텍스트 매니저로 사용
            async with self.github_client as client:
                # 임시로 클라이언트를 클래스 변수에 설정
                self._current_client = client
                
                # 1. 기본 저장소 정보 수집
                repo_info = await client.get_repository_info(repo_url)
                file_tree = await client.get_file_tree(repo_url)
                
                # 2. Git 커밋 히스토리 분석
                churn_analysis = await self._analyze_commit_history(repo_url)
                
                # 3. 의존성 그래프 구성
                dependency_graph = await self._build_dependency_graph(repo_url, file_tree)
                
                # 4. 파일별 종합 메트릭 계산
                file_metrics = await self._calculate_comprehensive_metrics(
                    repo_url, file_tree, dependency_graph, churn_analysis
                )
                
                # 5. 중요 파일 선별 (상위 15개)
                important_files = await self._select_critical_files(file_metrics, limit=15, repo_url=repo_url)
                
                # 6. 분석 대시보드 데이터 생성
                dashboard_data = self._generate_dashboard_data(
                    repo_info, file_metrics, dependency_graph, churn_analysis
                )
                
                # 클라이언트 변수 정리
                self._current_client = None
            
            return {
                "success": True,
                "repo_info": repo_info,
                "file_metrics": {path: metrics.__dict__ for path, metrics in file_metrics.items()},
                "dependency_graph": self._serialize_dependency_graph(dependency_graph),
                "churn_analysis": churn_analysis.__dict__,
                "important_files": important_files,
                "dashboard_data": dashboard_data,
                "analysis_summary": {
                    "total_files": len(file_metrics),
                    "analyzed_files": len([m for m in file_metrics.values() if m.importance_score > 0]),
                    "high_risk_files": len([m for m in file_metrics.values() if m.quality_risk_score > 7.0]),
                    "hotspot_files": len(churn_analysis.hotspots)
                }
            }
            
        except Exception as e:
            print(f"[고도화 분석] 오류 발생: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_commit_history(self, repo_url: str) -> ChurnAnalysis:
        """Git 커밋 히스토리 분석"""
        
        print("[변경이력 분석] 커밋 히스토리 수집 중...")
        
        try:
            # GitHub API로 커밋 히스토리 가져오기 (최근 100개)
            client = getattr(self, '_current_client', None) or self.github_client
            commits = await client.get_commit_history(repo_url, limit=100)
            
            file_churns = defaultdict(lambda: {
                'commit_count': 0,
                'recent_commits': 0,
                'authors': set(),
                'total_changes': 0,
                'recent_changes': 0,
                'first_commit': None,
                'last_commit': None
            })
            
            author_stats = defaultdict(lambda: {'commits': 0, 'files_changed': set()})
            from datetime import timezone
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            
            for commit in commits:
                commit_date = datetime.fromisoformat(commit['commit']['author']['date'].replace('Z', '+00:00'))
                author = commit['commit']['author']['name']
                
                # 커밋별 파일 변경 정보 가져오기
                if 'files' in commit:
                    files_changed = commit['files']
                else:
                    # GitHub API로 개별 커밋의 파일 변경 정보 가져오기
                    commit_detail = await client.get_commit_details(repo_url, commit['sha'])
                    files_changed = commit_detail.get('files', [])
                
                for file_change in files_changed:
                    filename = file_change['filename']
                    changes = file_change.get('changes', 0)
                    
                    # 파일별 변경 통계 업데이트
                    file_churns[filename]['commit_count'] += 1
                    file_churns[filename]['authors'].add(author)
                    file_churns[filename]['total_changes'] += changes
                    
                    if not file_churns[filename]['first_commit']:
                        file_churns[filename]['first_commit'] = commit_date
                    file_churns[filename]['last_commit'] = commit_date
                    
                    # 최근 6개월 변경사항
                    if commit_date > six_months_ago:
                        file_churns[filename]['recent_commits'] += 1
                        file_churns[filename]['recent_changes'] += changes
                    
                    # 작성자 통계
                    author_stats[author]['commits'] += 1
                    author_stats[author]['files_changed'].add(filename)
            
            # authors set을 count로 변환
            for filename in file_churns:
                file_churns[filename]['authors_count'] = len(file_churns[filename]['authors'])
                file_churns[filename]['authors'] = list(file_churns[filename]['authors'])
                file_churns[filename]['average_commit_size'] = (
                    file_churns[filename]['total_changes'] / file_churns[filename]['commit_count']
                    if file_churns[filename]['commit_count'] > 0 else 0
                )
            
            # 핫스팟 계산 (변경 빈도가 높은 파일들)
            hotspots = []
            for filename, churn_data in file_churns.items():
                if churn_data['commit_count'] >= 1:  # 최소 1번 이상 변경된 파일
                    hotspot_score = churn_data['recent_commits'] * 2 + churn_data['commit_count']
                    hotspots.append({
                        'filename': filename,
                        'commit_count': churn_data['commit_count'],
                        'recent_commits': churn_data['recent_commits'],
                        'authors_count': churn_data['authors_count'],
                        'hotspot_score': hotspot_score
                    })
            
            # 핫스팟 점수 순으로 정렬
            hotspots.sort(key=lambda x: x['hotspot_score'], reverse=True)
            
            # 작성자 통계 정리
            for author in author_stats:
                author_stats[author]['files_changed'] = len(author_stats[author]['files_changed'])
            
            return ChurnAnalysis(
                file_churns=dict(file_churns),
                hotspots=hotspots[:20],  # 상위 20개 핫스팟
                author_statistics=dict(author_stats),
                temporal_patterns={}  # 추후 구현
            )
            
        except Exception as e:
            print(f"[변경이력 분석] 오류: {e}")
            return ChurnAnalysis()
    
    async def _build_dependency_graph(self, repo_url: str, file_tree: List[Dict]) -> DependencyGraph:
        """의존성 그래프 구성"""
        
        print("[의존성 분석] 의존성 그래프 구성 중...")
        
        graph = nx.DiGraph()
        import_relationships = {}
        
        # 소스 파일들만 필터링
        source_files = [
            f for f in file_tree 
            if f['type'] == 'file' and self._is_analyzable_file(f['path'])
        ]
        
        # 파일 내용 분석하여 import 관계 추출
        for file_info in source_files[:50]:  # 분석 시간 단축을 위해 상위 50개만
            file_path = file_info['path']
            try:
                client = getattr(self, '_current_client', None) or self.github_client
                file_content = await client.get_file_content(repo_url, file_path)
                if file_content:
                    imports = self._extract_imports(file_content, file_path)
                    import_relationships[file_path] = imports
                    
                    # 그래프에 노드와 엣지 추가
                    graph.add_node(file_path)
                    for imported_file in imports:
                        # 실제 파일 경로로 매핑
                        resolved_path = self._resolve_import_path(imported_file, file_path, source_files)
                        if resolved_path:
                            graph.add_edge(file_path, resolved_path)
                            
            except Exception as e:
                print(f"[의존성 분석] 파일 분석 실패 {file_path}: {e}")
                continue
        
        # 네트워크 분석
        critical_paths = []
        module_clusters = []
        
        try:
            # 강연결 성분 찾기 (모듈 클러스터)
            if graph.number_of_nodes() > 0:
                strongly_connected = list(nx.strongly_connected_components(graph))
                module_clusters = [list(component) for component in strongly_connected if len(component) > 1]
                
                # 중요 경로 찾기 (PageRank 활용)
                if graph.number_of_edges() > 0:
                    pagerank_scores = nx.pagerank(graph)
                    top_nodes = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    # 상위 노드들 간의 경로 찾기
                    for i, (node1, _) in enumerate(top_nodes[:5]):
                        for node2, _ in top_nodes[i+1:i+3]:
                            try:
                                if nx.has_path(graph, node1, node2):
                                    path = nx.shortest_path(graph, node1, node2)
                                    if len(path) > 2:
                                        critical_paths.append(path)
                            except:
                                continue
                                
        except Exception as e:
            print(f"[의존성 분석] 네트워크 분석 오류: {e}")
        
        return DependencyGraph(
            graph=graph,
            import_relationships=import_relationships,
            module_clusters=module_clusters,
            critical_paths=critical_paths
        )
    
    async def _calculate_comprehensive_metrics(
        self, 
        repo_url: str, 
        file_tree: List[Dict], 
        dependency_graph: DependencyGraph,
        churn_analysis: ChurnAnalysis
    ) -> Dict[str, FileMetrics]:
        """파일별 종합 메트릭 계산"""
        
        print("[종합 메트릭] 파일별 메트릭 계산 중...")
        
        file_metrics = {}
        
        # 의존성 그래프에서 중심성 점수 계산
        centrality_scores = {}
        if dependency_graph.graph.number_of_nodes() > 0:
            try:
                # PageRank 중심성
                pagerank_centrality = nx.pagerank(dependency_graph.graph)
                # Betweenness 중심성  
                betweenness_centrality = nx.betweenness_centrality(dependency_graph.graph)
                
                for node in dependency_graph.graph.nodes():
                    centrality_scores[node] = (
                        pagerank_centrality.get(node, 0) * 0.6 + 
                        betweenness_centrality.get(node, 0) * 0.4
                    )
            except:
                centrality_scores = {}
        
        # 분석 가능한 파일들 처리
        analyzable_files = [f for f in file_tree if f['type'] == 'file' and self._is_analyzable_file(f['path'])]
        
        for file_info in analyzable_files[:30]:  # 상위 30개 파일만 상세 분석
            file_path = file_info['path']
            
            try:
                # 기본 메타정보
                metrics = FileMetrics(path=file_path)
                metrics.size = file_info.get('size', 0)
                metrics.language = self._detect_language(file_path)
                metrics.file_type = self._categorize_file_type(file_path)
                metrics.is_test_file = self._is_test_file(file_path)
                metrics.is_config_file = self._is_config_file(file_path)
                
                # 파일 내용 분석
                try:
                    client = getattr(self, '_current_client', None) or self.github_client
                    file_content = await client.get_file_content(repo_url, file_path)
                    if file_content and len(file_content.strip()) > 0:
                        # 복잡도 메트릭 계산
                        complexity_metrics = self._calculate_complexity_metrics(file_content, metrics.language)
                        metrics.cyclomatic_complexity = complexity_metrics['cyclomatic']
                        metrics.cognitive_complexity = complexity_metrics['cognitive'] 
                        metrics.halstead_complexity = complexity_metrics['halstead']
                        metrics.maintainability_index = complexity_metrics['maintainability']
                        metrics.lines_of_code = len([line for line in file_content.split('\n') if line.strip()])
                        metrics.has_main_function = self._has_main_function(file_content, metrics.language)
                        
                except Exception as e:
                    print(f"[메트릭 계산] 파일 내용 분석 실패 {file_path}: {e}")
                
                # 의존성 메트릭
                if file_path in dependency_graph.graph:
                    metrics.fan_in = dependency_graph.graph.in_degree(file_path)
                    metrics.fan_out = dependency_graph.graph.out_degree(file_path)
                    metrics.centrality_score = centrality_scores.get(file_path, 0)
                    
                    # 의존성 깊이 계산 (루트에서의 거리)
                    try:
                        # 진입차수가 0인 노드들을 루트로 간주
                        roots = [n for n in dependency_graph.graph.nodes() if dependency_graph.graph.in_degree(n) == 0]
                        if roots:
                            depths = []
                            for root in roots:
                                if nx.has_path(dependency_graph.graph, root, file_path):
                                    depth = nx.shortest_path_length(dependency_graph.graph, root, file_path)
                                    depths.append(depth)
                            metrics.dependency_depth = min(depths) if depths else 0
                    except:
                        metrics.dependency_depth = 0
                
                # 변경 이력 메트릭
                if file_path in churn_analysis.file_churns:
                    churn_data = churn_analysis.file_churns[file_path]
                    metrics.commit_frequency = churn_data['commit_count']
                    metrics.recent_commits = churn_data['recent_commits']
                    metrics.authors_count = churn_data['authors_count']
                    metrics.average_commit_size = churn_data['average_commit_size']
                    
                    # 핫스팟 점수 계산 (변경빈도 * 복잡도)
                    metrics.hotspot_score = (
                        metrics.recent_commits * 2 + metrics.commit_frequency
                    ) * (1 + metrics.cyclomatic_complexity / 10)
                
                # 종합 중요도 점수 계산
                metrics.importance_score = self._calculate_importance_score(metrics)
                
                # 품질 위험도 점수 계산  
                metrics.quality_risk_score = self._calculate_quality_risk_score(metrics)
                
                file_metrics[file_path] = metrics
                
            except Exception as e:
                print(f"[메트릭 계산] 파일 처리 실패 {file_path}: {e}")
                continue
        
        return file_metrics
    
    def _calculate_importance_score(self, metrics: FileMetrics) -> float:
        """파일 중요도 점수 계산 (0-100점)"""
        
        score = 0.0
        
        # 1. 기본 파일 타입 점수 (0-30점)
        type_scores = {
            'main': 30, 'controller': 25, 'service': 22, 'model': 20,
            'router': 18, 'configuration': 15, 'component': 12, 'utility': 10, 'general': 5
        }
        base_score = type_scores.get(metrics.file_type, 5)
        score += base_score
        
        # 2. 복잡도 점수 (0-25점)
        complexity_score = min(metrics.cyclomatic_complexity * 2, 25)
        score += complexity_score
        
        # 3. 중심성 점수 (0-20점)
        centrality_score = metrics.centrality_score * 100
        score += centrality_score
        
        # 4. 변경 빈도 점수 (0-15점)
        churn_score = min(metrics.recent_commits * 3 + metrics.commit_frequency * 1, 15)
        score += churn_score
        
        # 5. Fan-in 점수 (0-10점) - 다른 파일들이 많이 참조하는 파일
        fan_in_score = min(metrics.fan_in * 2, 10)
        score += fan_in_score
        
        # 6. 추가 보너스/패널티
        if metrics.has_main_function:
            score += 8
        if metrics.is_test_file:
            score *= 0.6  # 테스트 파일은 중요도를 낮춤
        if metrics.is_config_file and metrics.commit_frequency > 5:
            score += 5  # 자주 변경되는 설정 파일은 중요
        
        # 7. 크기 보너스 (큰 파일일수록 중요할 가능성)
        if metrics.size > 2000:
            score += 3
        elif metrics.size > 1000:
            score += 1
        
        return round(min(score, 100), 2)
    
    def _calculate_quality_risk_score(self, metrics: FileMetrics) -> float:
        """품질 위험도 점수 계산 (0-10점, 높을수록 위험)"""
        
        risk_score = 0.0
        
        # 1. 복잡도 위험 (0-3점)
        if metrics.cyclomatic_complexity > 15:
            risk_score += 3
        elif metrics.cyclomatic_complexity > 10:
            risk_score += 2
        elif metrics.cyclomatic_complexity > 5:
            risk_score += 1
        
        # 2. 핫스팟 위험 (0-2점)
        if metrics.hotspot_score > 20:
            risk_score += 2
        elif metrics.hotspot_score > 10:
            risk_score += 1
        
        # 3. 크기 위험 (0-2점)
        if metrics.lines_of_code > 500:
            risk_score += 2
        elif metrics.lines_of_code > 200:
            risk_score += 1
        
        # 4. 의존성 위험 (0-2점)
        if metrics.fan_out > 10:  # 너무 많은 외부 의존성
            risk_score += 1
        if metrics.fan_in > 15:   # 너무 많은 파일이 의존
            risk_score += 1
        
        # 5. 유지보수성 위험 (0-1점)
        if metrics.maintainability_index < 20:
            risk_score += 1
        
        return round(min(risk_score, 10), 2)
    
    async def _select_critical_files(self, file_metrics: Dict[str, FileMetrics], limit: int = 15, repo_url: str = "") -> List[Dict[str, Any]]:
        """중요도 기반 핵심 파일 선별"""
        
        # 중요도 점수 기준으로 정렬
        sorted_files = sorted(
            file_metrics.items(), 
            key=lambda x: x[1].importance_score, 
            reverse=True
        )
        
        critical_files = []
        for file_path, metrics in sorted_files[:limit]:
            
            # 파일 내용 가져오기 (실제 질문 생성용)
            try:
                client = getattr(self, '_current_client', None) or self.github_client
                file_content = await client.get_file_content(repo_url, file_path)  # repo_url 매개변수 추가 필요
                if not file_content:
                    file_content = "# 파일 내용을 가져올 수 없습니다"
            except:
                file_content = "# 파일 내용을 가져올 수 없습니다"
            
            critical_files.append({
                "path": file_path,
                "content": file_content,
                "importance_score": metrics.importance_score,
                "quality_risk_score": metrics.quality_risk_score,
                "complexity": metrics.cyclomatic_complexity,
                "hotspot_score": metrics.hotspot_score,
                "file_type": metrics.file_type,
                "language": metrics.language,
                "metrics_summary": {
                    "lines_of_code": metrics.lines_of_code,
                    "fan_in": metrics.fan_in,
                    "fan_out": metrics.fan_out,
                    "commit_frequency": metrics.commit_frequency,
                    "recent_commits": metrics.recent_commits,
                    "authors_count": metrics.authors_count,
                    "centrality_score": round(metrics.centrality_score, 4)
                }
            })
        
        print(f"[중요 파일 선별] {len(critical_files)}개 파일 선별 완료")
        return critical_files
    
    def _generate_dashboard_data(
        self, 
        repo_info: Dict, 
        file_metrics: Dict[str, FileMetrics],
        dependency_graph: DependencyGraph,
        churn_analysis: ChurnAnalysis
    ) -> Dict[str, Any]:
        """분석 대시보드 데이터 생성"""
        
        # 메트릭 집계
        all_metrics = list(file_metrics.values())
        
        complexity_distribution = {
            'low': len([m for m in all_metrics if m.cyclomatic_complexity <= 5]),
            'medium': len([m for m in all_metrics if 5 < m.cyclomatic_complexity <= 15]),
            'high': len([m for m in all_metrics if m.cyclomatic_complexity > 15])
        }
        
        risk_distribution = {
            'low': len([m for m in all_metrics if m.quality_risk_score <= 3]),
            'medium': len([m for m in all_metrics if 3 < m.quality_risk_score <= 6]),
            'high': len([m for m in all_metrics if m.quality_risk_score > 6])
        }
        
        # 언어별 통계
        language_stats = {}
        for metrics in all_metrics:
            lang = metrics.language
            if lang not in language_stats:
                language_stats[lang] = {
                    'file_count': 0,
                    'total_loc': 0,
                    'avg_complexity': 0,
                    'total_complexity': 0
                }
            language_stats[lang]['file_count'] += 1
            language_stats[lang]['total_loc'] += metrics.lines_of_code
            language_stats[lang]['total_complexity'] += metrics.cyclomatic_complexity
        
        # 평균 계산
        for lang_stat in language_stats.values():
            if lang_stat['file_count'] > 0:
                lang_stat['avg_complexity'] = round(
                    lang_stat['total_complexity'] / lang_stat['file_count'], 2
                )
        
        # 의존성 그래프 통계
        dependency_stats = {
            'total_nodes': dependency_graph.graph.number_of_nodes(),
            'total_edges': dependency_graph.graph.number_of_edges(),
            'density': round(nx.density(dependency_graph.graph), 4) if dependency_graph.graph.number_of_nodes() > 1 else 0,
            'clustering_coefficient': round(nx.average_clustering(dependency_graph.graph), 4) if dependency_graph.graph.number_of_nodes() > 2 else 0,
            'strongly_connected_components': len(dependency_graph.module_clusters),
            'critical_paths_count': len(dependency_graph.critical_paths)
        }
        
        # 상위 핫스팟 파일들
        top_hotspots = sorted([
            {
                'filename': metrics.path,
                'hotspot_score': metrics.hotspot_score,
                'complexity': metrics.cyclomatic_complexity,
                'recent_commits': metrics.recent_commits,
                'quality_risk': metrics.quality_risk_score
            }
            for metrics in all_metrics if metrics.hotspot_score > 0
        ], key=lambda x: x['hotspot_score'], reverse=True)[:10]
        
        # 중심성 높은 파일들
        top_central_files = sorted([
            {
                'filename': metrics.path,
                'centrality_score': metrics.centrality_score,
                'fan_in': metrics.fan_in,
                'fan_out': metrics.fan_out,
                'importance_score': metrics.importance_score
            }
            for metrics in all_metrics if metrics.centrality_score > 0
        ], key=lambda x: x['centrality_score'], reverse=True)[:10]
        
        return {
            "repository_overview": {
                "name": repo_info.get('name', ''),
                "description": repo_info.get('description', ''),
                "language": repo_info.get('language', ''),
                "size": repo_info.get('size', 0),
                "stars": repo_info.get('stargazers_count', 0),
                "forks": repo_info.get('forks_count', 0)
            },
            "complexity_analysis": {
                "distribution": complexity_distribution,
                "average_complexity": round(sum(m.cyclomatic_complexity for m in all_metrics) / len(all_metrics), 2) if all_metrics else 0,
                "max_complexity": max((m.cyclomatic_complexity for m in all_metrics), default=0),
                "maintainability_average": round(sum(m.maintainability_index for m in all_metrics) / len(all_metrics), 2) if all_metrics else 0
            },
            "quality_risk_analysis": {
                "distribution": risk_distribution,
                "high_risk_files": [
                    {
                        'filename': m.path,
                        'risk_score': m.quality_risk_score,
                        'complexity': m.cyclomatic_complexity,
                        'hotspot_score': m.hotspot_score
                    }
                    for m in all_metrics if m.quality_risk_score > 6
                ][:10]
            },
            "dependency_analysis": {
                "graph_metrics": dependency_stats,
                "top_central_files": top_central_files,
                "module_clusters": [
                    {"cluster_id": i, "files": cluster, "size": len(cluster)}
                    for i, cluster in enumerate(dependency_graph.module_clusters)
                ],
                "critical_paths": [
                    {"path_id": i, "files": path, "length": len(path)}
                    for i, path in enumerate(dependency_graph.critical_paths)
                ]
            },
            "churn_analysis": {
                "hotspots": top_hotspots,
                "author_statistics": dict(list(churn_analysis.author_statistics.items())[:10]),
                "most_changed_files": sorted([
                    {
                        'filename': filename,
                        'commit_count': data['commit_count'],
                        'recent_commits': data['recent_commits'],
                        'authors_count': data['authors_count']
                    }
                    for filename, data in churn_analysis.file_churns.items()
                ], key=lambda x: x['commit_count'], reverse=True)[:15]
            },
            "language_statistics": language_stats,
            "file_type_distribution": {
                file_type: len([m for m in all_metrics if m.file_type == file_type])
                for file_type in set(m.file_type for m in all_metrics)
            }
        }
    
    # ========== 유틸리티 메서드들 ==========
    
    def _is_analyzable_file(self, file_path: str) -> bool:
        """분석 가능한 파일인지 확인"""
        analyzable_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', 
            '.php', '.rb', '.cpp', '.c', '.cs', '.swift', '.kt'
        ]
        return any(file_path.endswith(ext) for ext in analyzable_extensions)
    
    def _detect_language(self, file_path: str) -> str:
        """파일 경로에서 언어 감지"""
        ext_to_lang = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'javascript', '.tsx': 'typescript', '.java': 'java',
            '.go': 'go', '.rs': 'rust', '.php': 'php', '.rb': 'ruby',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.swift': 'swift', '.kt': 'kotlin'
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        return 'unknown'
    
    def _categorize_file_type(self, file_path: str) -> str:
        """파일 유형 분류"""
        filename = file_path.lower()
        
        if any(name in filename for name in ['main', 'app', 'index']):
            return 'main'
        elif any(name in filename for name in ['controller', 'handler']):
            return 'controller'
        elif 'service' in filename:
            return 'service'
        elif any(name in filename for name in ['model', 'entity']):
            return 'model'
        elif any(name in filename for name in ['router', 'route']):
            return 'router'
        elif any(name in filename for name in ['util', 'helper']):
            return 'utility'
        elif any(name in filename for name in ['config', 'setting']):
            return 'configuration'
        elif any(name in filename for name in ['component', 'view']):
            return 'component'
        else:
            return 'general'
    
    def _is_test_file(self, file_path: str) -> bool:
        """테스트 파일 여부 확인"""
        test_patterns = ['test_', '_test.', '.test.', 'spec.', '_spec.']
        return any(pattern in file_path.lower() for pattern in test_patterns)
    
    def _is_config_file(self, file_path: str) -> bool:
        """설정 파일 여부 확인"""
        config_patterns = ['config', 'setting', '.env', 'package.json', 'requirements.txt', 'pom.xml']
        return any(pattern in file_path.lower() for pattern in config_patterns)
    
    def _extract_imports(self, content: str, file_path: str) -> List[str]:
        """파일에서 import/include 관계 추출"""
        language = self._detect_language(file_path)
        imports = []
        
        if language in self.complexity_patterns:
            patterns = self.complexity_patterns[language].get('import_patterns', [])
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)
        
        return imports
    
    def _resolve_import_path(self, import_name: str, current_file: str, all_files: List[Dict]) -> Optional[str]:
        """import 문을 실제 파일 경로로 해석"""
        # 간단한 해석 로직 (실제로는 더 복잡함)
        for file_info in all_files:
            file_path = file_info['path']
            if import_name in file_path or file_path.endswith(f"{import_name}.py") or file_path.endswith(f"{import_name}.js"):
                return file_path
        return None
    
    def _calculate_complexity_metrics(self, content: str, language: str) -> Dict[str, float]:
        """복잡도 메트릭 계산"""
        if language not in self.complexity_patterns:
            return {'cyclomatic': 1.0, 'cognitive': 1.0, 'halstead': 1.0, 'maintainability': 50.0}
        
        patterns = self.complexity_patterns[language]
        
        # 순환 복잡도 (Cyclomatic Complexity)
        cyclomatic = 1.0  # 기본값
        for pattern in patterns['decision_points']:
            cyclomatic += len(re.findall(pattern, content, re.IGNORECASE))
        
        # 인지 복잡도 (Cognitive Complexity) - 중첩 레벨 고려
        cognitive = 0.0
        lines = content.split('\n')
        nesting_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # 중첩 레벨 증가
            for pattern in patterns['nesting_indicators']:
                if re.search(pattern, line):
                    nesting_level += 1
                    break
            
            # 결정 포인트에 중첩 레벨 가중치 적용
            for pattern in patterns['decision_points']:
                if re.search(pattern, stripped, re.IGNORECASE):
                    cognitive += 1 + nesting_level
                    break
        
        # Halstead 복잡도 (간단한 근사치)
        operators = len(re.findall(r'[+\-*/=<>]+', content))
        operands = len(re.findall(r'\b\w+\b', content))
        unique_operators = len(set(re.findall(r'[+\-*/=<>]+', content)))
        unique_operands = len(set(re.findall(r'\b\w+\b', content)))
        
        if unique_operators > 0 and unique_operands > 0:
            vocabulary = unique_operators + unique_operands
            length = operators + operands
            volume = length * (vocabulary.bit_length() if vocabulary > 0 else 1)
            halstead = volume / 100  # 정규화
        else:
            halstead = 1.0
            
        # 유지보수성 지수 (간단한 근사치)
        loc = len([line for line in lines if line.strip()])
        maintainability = max(0, 171 - 5.2 * (halstead**0.23) - 0.23 * cyclomatic - 16.2 * (loc**0.5) / 100)
        
        return {
            'cyclomatic': round(cyclomatic, 2),
            'cognitive': round(cognitive, 2), 
            'halstead': round(halstead, 2),
            'maintainability': round(maintainability, 2)
        }
    
    def _has_main_function(self, content: str, language: str) -> bool:
        """메인 함수 존재 여부 확인"""
        main_patterns = {
            'python': [r'if\s+__name__\s*==\s*["\']__main__["\']', r'def\s+main\s*\('],
            'java': [r'public\s+static\s+void\s+main\s*\('],
            'javascript': [r'function\s+main\s*\(', r'const\s+main\s*='],
            'go': [r'func\s+main\s*\('],
            'rust': [r'fn\s+main\s*\(']
        }
        
        if language in main_patterns:
            for pattern in main_patterns[language]:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
        return False
    
    def _serialize_dependency_graph(self, dependency_graph: DependencyGraph) -> Dict[str, Any]:
        """의존성 그래프 직렬화"""
        return {
            'nodes': list(dependency_graph.graph.nodes()),
            'edges': list(dependency_graph.graph.edges()),
            'node_count': dependency_graph.graph.number_of_nodes(),
            'edge_count': dependency_graph.graph.number_of_edges(),
            'import_relationships': dependency_graph.import_relationships,
            'module_clusters': dependency_graph.module_clusters,
            'critical_paths': dependency_graph.critical_paths
        }