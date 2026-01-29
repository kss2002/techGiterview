
from app.services.flow_graph_analyzer import FlowGraphAnalyzer
import os

def test_techgiterview_graph():
    analyzer = FlowGraphAnalyzer()
    
    # Simulate some key files from techGiterview backend
    files = {
        "src/backend/app/main.py": "from app.api.analysis import router\nfrom app.core.config import settings",
        "src/backend/app/api/analysis.py": "from app.services.flow_graph_analyzer import FlowGraphAnalyzer",
        "src/backend/app/services/flow_graph_analyzer.py": "import networkx as nx",
        "src/backend/app/core/config.py": "import os",
    }
    
    print("--- Simulating TechGiterview Graph ---")
    graph = analyzer.build_graph(files, repo_name="techGiterview")
    
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    for u, v, data in edges:
        print(f"Edge: {u} -> {v} ({data})")
        
    if len(edges) == 0:
        print("❌ No edges found! Logic is broken.")
    else:
        print("✅ Edges found.")

if __name__ == "__main__":
    test_techgiterview_graph()
