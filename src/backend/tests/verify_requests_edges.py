
from app.services.flow_graph_analyzer import FlowGraphAnalyzer

def test_requests_graph_simulation():
    analyzer = FlowGraphAnalyzer()
    
    # Files seen in the Requests screenshot
    files = {
        "HISTORY.md": "# History",
        "tox.ini": "[tox]\nenvlist = py37",
        "requirements-dev.txt": "pytest",
        "pyproject.toml": "[build-system]",
        "LICENSE": "Apache 2.0",
        "AUTHORS.rst": "Kenneth Reitz",
        "setup.py": """
import os
import sys
from setuptools import setup
setup(name='requests')
""",
        "README.md": "# Requests",
        "Makefile": "init:\n\tpip install",
        ".coveragerc": "[run]\nsource=requests"
    }
    
    print("--- Simulating Requests Repository Analysis ---")
    graph = analyzer.build_graph(files, repo_name="requests")
    
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    print(f"Files Analyzed: {len(files)}")
    print(f"Nodes in Graph: {len(nodes)}")
    print(f"Edges in Graph: {len(edges)}")
    
    if len(edges) == 0:
        print("✅ Result: 0 Edges. (Expected, as these files are independent)")
    else:
        print(f"❌ Result: {len(edges)} Edges found.")
        for u, v in edges:
            print(f"  {u} -> {v}")

if __name__ == "__main__":
    test_requests_graph_simulation()
