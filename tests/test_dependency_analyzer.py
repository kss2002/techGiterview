"""
Dependency Analyzer 테스트

NetworkX 라이브러리를 활용한 의존성 그래프 분석 시스템 테스트
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from app.services.dependency_analyzer import (
    DependencyAnalyzer,
    DependencyGraph,
    DependencyNode,
    CentralityMetrics
)


class TestDependencyAnalyzer:
    """Dependency Analyzer 테스트 클래스"""
    
    @pytest.fixture
    def analyzer(self):
        """DependencyAnalyzer 인스턴스"""
        return DependencyAnalyzer()
    
    @pytest.fixture
    def sample_package_json(self):
        """테스트용 package.json 데이터"""
        return {
            "name": "test-project",
            "dependencies": {
                "react": "^18.2.0",
                "axios": "^1.4.0",
                "lodash": "^4.17.21"
            },
            "devDependencies": {
                "jest": "^29.5.0",
                "typescript": "^5.0.0"
            }
        }
    
    @pytest.fixture
    def sample_requirements_txt(self):
        """테스트용 requirements.txt 데이터"""
        return """fastapi==0.104.1
pydantic==2.5.0
uvicorn[standard]==0.24.0
pytest==7.4.3
redis>=4.0.0
sqlalchemy==2.0.23"""
    
    @pytest.fixture
    def sample_pom_xml(self):
        """테스트용 pom.xml 데이터"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-boot-starter</artifactId>
            <version>2.7.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>2.7.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>"""

    def test_parse_package_json(self, analyzer, sample_package_json):
        """package.json 파싱 테스트"""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_package_json))):
            dependencies = analyzer._parse_package_json("package.json")
        
        assert len(dependencies) == 5  # 3 prod + 2 dev
        assert "react" in dependencies
        assert "jest" in dependencies
        assert dependencies["react"]["version"] == "^18.2.0"
        assert dependencies["react"]["type"] == "production"
        assert dependencies["jest"]["type"] == "development"
    
    def test_parse_requirements_txt(self, analyzer, sample_requirements_txt):
        """requirements.txt 파싱 테스트"""
        with patch("builtins.open", mock_open(read_data=sample_requirements_txt)):
            dependencies = analyzer._parse_requirements_txt("requirements.txt")
        
        assert len(dependencies) == 6
        assert "fastapi" in dependencies
        assert dependencies["fastapi"]["version"] == "==0.104.1"
        assert dependencies["fastapi"]["type"] == "production"
        assert dependencies["redis"]["version"] == ">=4.0.0"
    
    def test_parse_pom_xml(self, analyzer, sample_pom_xml):
        """pom.xml 파싱 테스트"""
        with patch("builtins.open", mock_open(read_data=sample_pom_xml)):
            dependencies = analyzer._parse_pom_xml("pom.xml")
        
        assert len(dependencies) == 3
        assert "spring-boot-starter" in dependencies
        assert dependencies["spring-boot-starter"]["version"] == "2.7.0"
        assert dependencies["spring-boot-starter"]["type"] == "production"
        assert dependencies["junit"]["type"] == "test"
    
    def test_build_dependency_graph(self, analyzer):
        """의존성 그래프 구성 테스트"""
        dependencies = {
            "react": {"version": "^18.2.0", "type": "production"},
            "axios": {"version": "^1.4.0", "type": "production"},
            "lodash": {"version": "^4.17.21", "type": "production"},
            "jest": {"version": "^29.5.0", "type": "development"}
        }
        
        graph = analyzer._build_dependency_graph(dependencies)
        
        assert graph.number_of_nodes() == 4
        assert graph.has_node("react")
        assert graph.has_node("axios")
        assert graph.has_node("lodash")
        assert graph.has_node("jest")
        
        # 노드 속성 확인
        react_attrs = graph.nodes["react"]
        assert react_attrs["version"] == "^18.2.0"
        assert react_attrs["type"] == "production"
    
    def test_calculate_centrality_metrics(self, analyzer):
        """중앙성 지표 계산 테스트"""
        import networkx as nx
        
        # 테스트용 그래프 생성
        graph = nx.DiGraph()
        graph.add_node("A", type="production")
        graph.add_node("B", type="production")
        graph.add_node("C", type="production")
        graph.add_node("D", type="development")
        
        # 의존성 관계 추가 (A->B, A->C, B->C, D->A)
        graph.add_edge("A", "B")
        graph.add_edge("A", "C") 
        graph.add_edge("B", "C")
        graph.add_edge("D", "A")
        
        metrics = analyzer._calculate_centrality_metrics(graph)
        
        assert "betweenness" in metrics
        assert "closeness" in metrics
        assert "pagerank" in metrics
        assert len(metrics["betweenness"]) == 4
        assert len(metrics["closeness"]) == 4
        assert len(metrics["pagerank"]) == 4
        
        # A가 가장 중요한 노드여야 함 (많은 의존성을 가짐)
        assert metrics["pagerank"]["A"] > metrics["pagerank"]["D"]
    
    def test_apply_depth_weights(self, analyzer):
        """의존성 깊이별 가중치 적용 테스트"""
        import networkx as nx
        
        graph = nx.DiGraph()
        nodes = ["root", "level1_a", "level1_b", "level2_a", "level3_a"]
        for node in nodes:
            graph.add_node(node, type="production")
        
        # 깊이별 연결: root -> level1_a -> level2_a -> level3_a
        #                root -> level1_b
        graph.add_edge("root", "level1_a")
        graph.add_edge("root", "level1_b")
        graph.add_edge("level1_a", "level2_a")
        graph.add_edge("level2_a", "level3_a")
        
        weighted_metrics = analyzer._apply_depth_weights(graph)
        
        assert "weighted_importance" in weighted_metrics
        # 깊이가 깊을수록 가중치가 감소해야 함
        assert weighted_metrics["weighted_importance"]["root"] > weighted_metrics["weighted_importance"]["level1_a"]
        assert weighted_metrics["weighted_importance"]["level1_a"] > weighted_metrics["weighted_importance"]["level2_a"]
    
    @pytest.mark.asyncio
    async def test_analyze_dependencies_full_workflow(self, analyzer):
        """의존성 분석 전체 워크플로우 테스트"""
        # Mock 의존성 데이터 직접 반환
        mock_dependencies = {
            "react": {"version": "^18.2.0", "type": "production", "source": "package.json"},
            "axios": {"version": "^1.4.0", "type": "production", "source": "package.json"},
            "fastapi": {"version": "0.104.1", "type": "production", "source": "requirements.txt"},
            "pydantic": {"version": "2.5.0", "type": "production", "source": "requirements.txt"}
        }
        
        with patch.object(analyzer, '_find_dependency_files', return_value=mock_dependencies):
            result = await analyzer.analyze_dependencies("/fake/repo/path")
            
            assert isinstance(result, DependencyGraph)
            assert result.total_dependencies == 4
            assert len(result.centrality_metrics.betweenness) > 0
            assert result.dependencies["react"].name == "react" 
            assert result.dependencies["fastapi"].name == "fastapi"
    
    def test_dependency_node_creation(self):
        """DependencyNode 생성 테스트"""
        node = DependencyNode(
            name="react",
            version="^18.2.0",
            dependency_type="production",
            file_source="package.json"
        )
        
        assert node.name == "react"
        assert node.version == "^18.2.0"
        assert node.dependency_type == "production"
        assert node.file_source == "package.json"
    
    def test_centrality_metrics_creation(self):
        """CentralityMetrics 생성 테스트"""
        metrics = CentralityMetrics(
            betweenness={"A": 0.5, "B": 0.3},
            closeness={"A": 0.8, "B": 0.6},
            pagerank={"A": 0.4, "B": 0.6},
            weighted_importance={"A": 0.7, "B": 0.5}
        )
        
        assert metrics.betweenness["A"] == 0.5
        assert metrics.closeness["B"] == 0.6
        assert metrics.pagerank["B"] == 0.6
        assert metrics.weighted_importance["A"] == 0.7
    
    def test_dependency_graph_creation(self):
        """DependencyGraph 생성 테스트"""
        dependencies = {
            "react": DependencyNode("react", "^18.2.0", "production", "package.json"),
            "jest": DependencyNode("jest", "^29.5.0", "development", "package.json")
        }
        
        metrics = CentralityMetrics(
            betweenness={"react": 0.5, "jest": 0.3},
            closeness={"react": 0.8, "jest": 0.6},
            pagerank={"react": 0.4, "jest": 0.6},
            weighted_importance={"react": 0.7, "jest": 0.5}
        )
        
        graph = DependencyGraph(
            dependencies=dependencies,
            centrality_metrics=metrics,
            total_dependencies=2,
            production_count=1,
            development_count=1
        )
        
        assert graph.total_dependencies == 2
        assert graph.production_count == 1
        assert graph.development_count == 1
        assert len(graph.dependencies) == 2
        assert isinstance(graph.centrality_metrics, CentralityMetrics)
    
    def test_error_handling_missing_files(self, analyzer):
        """의존성 파일이 없는 경우 에러 처리 테스트"""
        with patch.object(Path, 'exists', return_value=False):
            dependencies = analyzer._find_dependency_files("/nonexistent/path")
            assert dependencies == {}
    
    def test_error_handling_malformed_json(self, analyzer):
        """잘못된 JSON 파일 처리 테스트"""
        malformed_json = '{"dependencies": {"react": }'  # 잘못된 JSON
        
        with patch("builtins.open", mock_open(read_data=malformed_json)), \
             pytest.raises(ValueError, match="Invalid JSON"):
            analyzer._parse_package_json("package.json")
    
    def test_networkx_integration(self, analyzer):
        """NetworkX 라이브러리 통합 테스트"""
        dependencies = {
            "A": {"version": "1.0.0", "type": "production"},
            "B": {"version": "2.0.0", "type": "production"},
            "C": {"version": "3.0.0", "type": "development"}
        }
        
        graph = analyzer._build_dependency_graph(dependencies)
        
        # NetworkX 기능 테스트
        assert hasattr(graph, 'number_of_nodes')
        assert hasattr(graph, 'number_of_edges')
        assert graph.number_of_nodes() == 3
        
        # 중앙성 계산 테스트
        metrics = analyzer._calculate_centrality_metrics(graph)
        assert all(key in metrics for key in ["betweenness", "closeness", "pagerank"])


class TestDependencyAnalyzerIntegration:
    """의존성 분석기 통합 테스트"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_project_analysis(self):
        """실제 프로젝트 의존성 분석 테스트 (Mock)"""
        analyzer = DependencyAnalyzer()
        
        # 실제 파일 내용을 시뮬레이션
        real_package_json = {
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0", 
                "axios": "^1.4.0",
                "styled-components": "^5.3.9"
            },
            "devDependencies": {
                "jest": "^29.5.0",
                "testing-library/react": "^13.4.0"
            }
        }
        
        # Mock 의존성 데이터
        mock_dependencies = {
            "react": {"version": "^18.2.0", "type": "production", "source": "package.json"},
            "react-dom": {"version": "^18.2.0", "type": "production", "source": "package.json"},
            "axios": {"version": "^1.4.0", "type": "production", "source": "package.json"},
            "styled-components": {"version": "^5.3.9", "type": "production", "source": "package.json"},
            "jest": {"version": "^29.5.0", "type": "development", "source": "package.json"},
            "testing-library/react": {"version": "^13.4.0", "type": "development", "source": "package.json"}
        }
        
        with patch.object(analyzer, '_find_dependency_files', return_value=mock_dependencies):
            result = await analyzer.analyze_dependencies("/mock/react/project")
            
            assert result.total_dependencies == 6
            assert result.production_count == 4
            assert result.development_count == 2
            assert "react" in result.dependencies
            assert result.dependencies["react"].dependency_type == "production"
    
    def test_performance_large_dependency_graph(self):
        """대용량 의존성 그래프 성능 테스트"""
        # 100개의 의존성을 가진 프로젝트 시뮬레이션
        large_dependencies = {
            f"package_{i}": {"version": f"{i}.0.0", "type": "production" if i % 2 == 0 else "development"}
            for i in range(100)
        }
        
        import time
        start_time = time.time()
        
        analyzer = DependencyAnalyzer()
        graph = analyzer._build_dependency_graph(large_dependencies)
        metrics = analyzer._calculate_centrality_metrics(graph)
        
        end_time = time.time()
        
        # 성능 검증 (1초 이내 완료)
        assert end_time - start_time < 1.0
        assert len(metrics["pagerank"]) == 100
        assert graph.number_of_nodes() == 100