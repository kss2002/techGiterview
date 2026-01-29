
import sys
import os

# Add src/backend to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.flow_graph_analyzer import FlowGraphAnalyzer, NodeType

def test_implicit_node_creation():
    analyzer = FlowGraphAnalyzer()
    
    files = {
        "requests/api.py": """
from . import sessions
from . import models
def request():
    pass
""",
        "requests/__init__.py": """
from .api import request
from .models import Request
"""
    }
    
    # CASE 1: 'requests/models.py' and 'requests/sessions.py' are MISSING.
    # But they are imported relatively from requests/api.py
    # and explicit relative import from requests/__init__.py
    
    print("--- Running Test Case: Implicit Node Creation ---")
    graph = analyzer.build_graph(files, repo_name="requests")
    
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    print(f"Nodes found: {len(nodes)}")
    for n, data in nodes:
        print(f" - {n}: {data.get('type')}, label={data.get('label')}")
        
    print(f"Edges found: {len(edges)}")
    for u, v, data in edges:
        print(f" - {u} -> {v} ({data.get('type')})")
        
    # Validation
    # Expect "implicit:requests.sessions" and "implicit:requests.models"
    implicit_sessions = "implicit:requests.sessions"
    implicit_models = "implicit:requests.models"
    
    has_sessions = any(n == implicit_sessions for n, _ in nodes)
    has_models = any(n == implicit_models for n, _ in nodes)
    
    if has_sessions and has_models:
        print("✅ SUCCESS: Implicit nodes created for relative imports.")
    else:
        print(f"❌ FAILURE: Missing implicit nodes. Sessions: {has_sessions}, Models: {has_models}")

def test_repo_name_prefix_matching():
    analyzer = FlowGraphAnalyzer()
    
    files = {
        "app/main.py": "import requests.auth"
    }
    
    # CASE 2: External package 'requests' is imported.
    # If repo_name is 'requests', it should be treated as internal implicits?
    # Actually, usually 'requests' is a library. But if we are analyzing 'requests' repo, 
    # and we have a file importing 'requests.auth' but we don't have 'requests/auth.py',
    # it should create an implicit node.
    
    print("\n--- Running Test Case: Repo Name Prefix ---")
    graph = analyzer.build_graph(files, repo_name="requests")
    
    edges = list(graph.edges())
    # Expect app/main.py -> implicit:requests.auth
    
    found = False
    for u, v in edges:
        if "implicit:requests.auth" in v:
            found = True
            print(f"✅ Found edge to implicit internal module: {u} -> {v}")
            
    if not found:
        print("❌ FAILURE: Did not create implicit node for repo-matched prefix.")
        for u, v in edges:
            print(f"   Existing edge: {u} -> {v}")

if __name__ == "__main__":
    test_implicit_node_creation()
    test_repo_name_prefix_matching()
