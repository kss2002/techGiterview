
import networkx as nx
from typing import List, Set, Dict, Any

class FlowAnalysisService:
    """
    Service to extract execution flows from the Code Graph.
    Uses Smart Pruning to avoid flow explosion.
    """

    def extract_flow_paths(
        self, 
        graph: nx.DiGraph, 
        entry_points: List[str], 
        max_depth: int = 5, 
        max_branches: int = 3
    ) -> List[List[str]]:
        """
        Extracts semantic flow paths starting from entry_points.
        Prunes paths based on node density to keep only the most meaningful flows.
        """
        all_paths = []

        for entry in entry_points:
            if not graph.has_node(entry):
                continue
            
            # DFS with pruning
            self._dfs_pruned(
                graph=graph, 
                current_node=entry, 
                current_path=[], 
                all_paths=all_paths, 
                depth=0, 
                max_depth=max_depth, 
                max_branches=max_branches
            )
            
        return all_paths

    def _dfs_pruned(
        self, 
        graph: nx.DiGraph, 
        current_node: str, 
        current_path: List[str], 
        all_paths: List[List[str]], 
        depth: int, 
        max_depth: int, 
        max_branches: int
    ):
        new_path = current_path + [current_node]
        
        # Stop condition: Max depth reached or Leaf node
        neighbors = list(graph.successors(current_node))
        if depth >= max_depth or not neighbors:
            all_paths.append(new_path)
            return

        # Sort neighbors by Density (High density first)
        # Default density 0.0 if not present
        neighbors_with_scores = []
        for n in neighbors:
            density = graph.nodes[n].get("density", 0.0)
            neighbors_with_scores.append((n, density))
        
        # Sort descending
        neighbors_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Pruning: Take top N branches
        top_neighbors = [n for n, score in neighbors_with_scores[:max_branches]]
        
        for neighbor in top_neighbors:
            # Avoid cycles
            if neighbor in new_path:
                continue
                
            self._dfs_pruned(
                graph, 
                neighbor, 
                new_path, 
                all_paths, 
                depth + 1, 
                max_depth, 
                max_branches
            )
