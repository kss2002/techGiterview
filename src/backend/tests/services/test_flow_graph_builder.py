
import pytest
import networkx as nx
from app.services.flow_graph_analyzer import FlowGraphAnalyzer, NodeType

class TestFlowGraphBuilder:
    def test_builds_graph_with_imports(self):
        analyzer = FlowGraphAnalyzer()
        
        files = {
            "main.py": "import utils\nutils.do_something()",
            "utils.py": "def do_something(): pass"
        }
        
        graph = analyzer.build_graph(files)
        
        assert "main.py" in graph.nodes
        assert "utils.py" in graph.nodes
        assert graph.has_edge("main.py", "utils.py")
        
    def test_assigns_node_types_and_density(self):
        analyzer = FlowGraphAnalyzer()
        
        files = {
            "api.py": "@app.get('/')\ndef index(): pass",
            "model.py": "from sqlalchemy import Column\nclass User(Base): id=Column()"
        }
        
        graph = analyzer.build_graph(files)
        
        assert graph.nodes["api.py"]["type"] == NodeType.ENTRY_POINT
        assert graph.nodes["model.py"]["type"] == NodeType.DATA
        assert "density" in graph.nodes["api.py"]
