
import pytest
import networkx as nx
from app.services.flow_analysis_service import FlowAnalysisService

class TestFlowAnalysisService:
    def test_pruning_logic_top_3(self):
        """
        Setup:
        Root -> A (Density 0.9)
        Root -> B (Density 0.8)
        Root -> C (Density 0.7)
        Root -> D (Density 0.1)
        
        Expectation: Path should contain Root, A, B, C. D should be pruned.
        """
        service = FlowAnalysisService()
        graph = nx.DiGraph()
        
        # Add nodes with density
        graph.add_node("root", density=1.0)
        graph.add_node("A", density=0.9)
        graph.add_node("B", density=0.8)
        graph.add_node("C", density=0.7)
        graph.add_node("D", density=0.1)
        
        # Add edges
        graph.add_edge("root", "A")
        graph.add_edge("root", "B")
        graph.add_edge("root", "C")
        graph.add_edge("root", "D")
        
        flow_path = service.extract_flow_paths(graph, entry_points=["root"], max_branches=3)
        
        nodes_in_flow = set()
        for path in flow_path:
            for node in path:
                nodes_in_flow.add(node)
                
        assert "A" in nodes_in_flow
        assert "B" in nodes_in_flow
        assert "C" in nodes_in_flow
        assert "D" not in nodes_in_flow

    def test_dead_code_exclusion(self):
        """
        Setup:
        Root -> A
        Isolated -> B
        
        Expectation: Extracted flow should NOT contain Isolated or B.
        """
        service = FlowAnalysisService()
        graph = nx.DiGraph()
        
        graph.add_edge("root", "A")
        graph.add_edge("isolated", "B")
        
        flow_path = service.extract_flow_paths(graph, entry_points=["root"])
        
        nodes_in_flow = set()
        for path in flow_path:
            for node in path:
                nodes_in_flow.add(node)
                
        assert "root" in nodes_in_flow
        assert "A" in nodes_in_flow
        assert "isolated" not in nodes_in_flow
        assert "B" not in nodes_in_flow
