
import re
import ast
from enum import Enum
from typing import Dict, Any, List, Optional

class NodeType(Enum):
    ENTRY_POINT = "entry_point"
    LOGIC = "logic"
    DATA = "data"
    CONFIG = "config"
    UNKNOWN = "unknown"

class FlowGraphAnalyzer:
    """
    Code Analyzer that focuses on Execution Flow and Semantic Density.
    Replaces simple Complexity metrics with Logic/Data/Functional density scores.
    """

    def __init__(self):
        # Heuristic weights
        self.weights = {
            "control": 1.0,     # if, loop, try
            "data": 0.8,        # field, schema, sql
            "func": 1.0,        # map, filter, reduce
            "boilerplate": 0.1  # getter, setter
        }

    def determine_node_type(self, file_path: str, content: str) -> NodeType:
        """
        Determines if a file is an Entry Point, Logic, Data, etc.
        """
        if not content:
            return NodeType.UNKNOWN

        # 1. Check Entry Point Patterns
        if self._is_entry_point(content, file_path):
            return NodeType.ENTRY_POINT
            
        # 2. Check Data Patterns (DTOs, Models)
        if self._is_data_node(content, file_path):
            return NodeType.DATA

        # 3. Check Config Patterns
        if "config" in file_path.lower() or file_path.endswith((".json", ".yaml", ".toml")):
            return NodeType.CONFIG
            
        # Default to Logic
        return NodeType.LOGIC

    def _is_entry_point(self, content: str, file_path: str) -> bool:
        """
        Detects if file contains API routes, CLI commands, or Cron jobs.
        """
        # FastAPI / Flask
        if "@app.get" in content or "@app.post" in content or "@app.route" in content:
            return True
        
        # Django
        if "urlpatterns" in content and "path(" in content:
            return True
            
        # CLI / Scripts
        if 'if __name__ == "__main__":' in content or 'if __name__ == \'__main__\':' in content:
            return True
        
        # Click / Typer
        if "@click.command" in content or "@app.command" in content:
            return True
            
        # Public API directory
        if "/api/" in file_path or "/controllers/" in file_path:
            return True
            
        return False

    def _is_data_node(self, content: str, file_path: str) -> bool:
        """
        Detects Pydantic Models, SQLAlchemy Tables, DataClasses.
        """
        if "BaseModel" in content or "dataclass" in content:
            return True
        if "Column(" in content and "sqlalchemy" in content:
            return True
        if "/schemas/" in file_path or "/models/" in file_path or "/dtos/" in file_path:
            return True
        return False

    def calculate_semantic_density(self, content: str) -> float:
        """
        Calculates Semantic Density based on AST analysis.
        Density = Max(Control, Data, Functional) / LinesOfCode
        """
        if not content or not content.strip():
            return 0.0

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback for non-python files or invalid syntax
            return self._calculate_regex_density(content)

        scores = {
            "control": 0.0,
            "data": 0.0,
            "func": 0.0
        }

        # AST Walker
        for node in ast.walk(tree):
            # Control Flow
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                scores["control"] += 1
            
            # Data Definition
            if isinstance(node, (ast.AnnAssign)): # Type annotated assignment
                scores["data"] += 1
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "Column":
                    scores["data"] += 1
            
            # Functional
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["map", "filter", "reduce"]:
                    scores["func"] += 1
                elif isinstance(node.func, ast.Attribute) and node.func.attr in ["map", "filter", "reduce"]:
                     # items.map(...)
                    scores["func"] += 1

        # Calculate logical lines of code (ignoring empty/comments)
        lines = [line for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        loc = max(1, len(lines))

        # Weighted Score
        control_density = (scores["control"] * self.weights["control"]) / loc
        data_density = (scores["data"] * self.weights["data"]) / loc
        func_density = (scores["func"] * self.weights["func"]) / loc
        
        # Return the maximum dimension to capture "Specialized Density"
        # e.g. A Data file has high Data density but low Control density. It is still "Dense" in its paradigm.
        final_density = max(control_density, data_density, func_density)
        
        # Normalize to 0-1 range (heuristic cap)
        return min(1.0, final_density)

    def _calculate_regex_density(self, content: str) -> float:
        """Fallback for non-Python files"""
        if not content:
            return 0.0
            
        loc = max(1, len(content.splitlines()))
        
        # Simple heuristics
        control_count = len(re.findall(r'\b(if|else|for|while|try|catch|switch)\b', content))
        data_count = len(re.findall(r'\b(interface|type|struct|class|enum)\b', content))
        func_count = len(re.findall(r'\b(map|filter|reduce|forEach)\b', content))
        
        return min(1.0, (control_count + data_count + func_count) / loc)

    def build_graph(self, files: Dict[str, str], repo_name: Optional[str] = None) -> "nx.DiGraph":
        """
        Builds a NetworkX DiGraph from a dictionary of {filename: content}.
        Calculates Semantic Density and Node Type for each file.
        Extracts Imports to form Edges.
        """
        import networkx as nx
        import os
        
        graph = nx.DiGraph()
        
        # 1. Build Module Map & Identify Internal Prefixes
        module_to_file = {}
        internal_prefixes = set()
        
        # Dynamic Internal Prefix Detection
        # 1. Repo Name
        if repo_name:
            internal_prefixes.add(repo_name.lower())
            internal_prefixes.add(repo_name.replace('-', '_'))
            
        # 2. Top-level Directories from file list
        top_level_dirs = set()
        for file_path in files.keys():
            parts = file_path.split('/')
            if len(parts) > 1:
                top_dir = parts[0]
                # Exclude vendor/deps directories from being treated as "Internal"
                # This prevents "implicit:deps..." nodes from being created for vendor libs
                if top_dir.lower() not in ['deps', 'vendor', 'node_modules', 'third_party']:
                    top_level_dirs.add(top_dir)
                
        # Only add generic names if they actually exist in the repo
        internal_prefixes.update(top_level_dirs)
        
        # Also handle common 'src' pattern
        src_roots = set()
        for file_path in files.keys():
            if file_path.startswith('src/'):
                 parts = file_path.split('/')
                 if len(parts) > 2:
                     src_roots.add(parts[1])
        internal_prefixes.update(src_roots)

        print(f"[FlowGraphAnalyzer] Dynamic Internal Prefixes: {internal_prefixes}")
        
        # Build Module Map
        for file_path in files.keys():
            # Standard Module Map
            name_no_ext = os.path.splitext(file_path)[0]
            
            # Helper to add mapping
            def add_mapping(mod_path, f_path):
                mod_path = mod_path.strip('.').replace('/', '.')
                if mod_path:
                    if mod_path not in module_to_file:
                        module_to_file[mod_path] = f_path
                    # Also map last segment for fuzzy match
                    basename = mod_path.split('.')[-1]
                    if basename not in module_to_file:
                        module_to_file[basename] = f_path

            # Normal path mapping
            add_mapping(name_no_ext, file_path)
            
            # src/ handling
            parts = name_no_ext.split('/')
            if parts[0] == 'src':
                add_mapping("/".join(parts[1:]), file_path)
                
                # Special handling for src/backend/app -> app
                if len(parts) > 2 and parts[1] == 'backend' and parts[2] == 'app':
                     # Map 'app.agents.foo' -> 'src/backend/app/agents/foo.py'
                     add_mapping("/".join(parts[2:]), file_path)
                
            # Index file resolution
            basename = os.path.basename(name_no_ext)
            if basename.lower() == 'index':
                folder_path = os.path.dirname(name_no_ext)
                add_mapping(folder_path, file_path)
                if parts[0] == 'src':
                     folder_no_src = "/".join(parts[1:-1])
                     add_mapping(folder_no_src, file_path)

        # 2. Add Nodes (Explicit)
        for filename, content in files.items():
            node_type = self.determine_node_type(filename, content)
            density = self.calculate_semantic_density(content)
            loc = len([line for line in content.splitlines() if line.strip()])
            
            graph.add_node(
                filename,
                type=node_type,
                density=density,
                val=loc,
                label=os.path.basename(filename)
            )
            
        # 3. Add Edges (Dependency Resolution)
        for filename, content in files.items():
            current_module_path = self._get_module_path_from_filename(filename)
            imports = self._extract_imports(content, filename) # Pass filename for language detection
            
            for imp_name, level in imports:
                target_node = None
                target_type = "explicit"
                
                # Resolve Target
                if level > 0:
                    # Relative
                    resolved_module = self._resolve_relative_import(current_module_path, imp_name, level)
                    target_node = self._find_node_fuzzy(resolved_module, module_to_file)
                    
                    # Implicit (Relative is always internal)
                    if not target_node and resolved_module:
                        target_node = f"implicit:{resolved_module}"
                        target_type = "implicit"

                else:
                    # Absolute
                    # Handle @/ alias (simple assumption: @/ -> src/)
                    if imp_name.startswith('@/'):
                        clean_name = imp_name.replace('@/', '')
                        # Try exact match first
                        target_node = self._find_node_fuzzy(clean_name, module_to_file)
                        if not target_node:
                             # Try looking in src/
                             target_node = self._find_node_fuzzy(f"src/{clean_name}", module_to_file)
                    else:
                        target_node = self._find_node_fuzzy(imp_name, module_to_file)
                    
                    # Implicit Check (Prefixes)
                    if not target_node:
                        # e.g. import requests.models -> check if 'requests' in prefixes
                        first_segment = imp_name.split('.')[0]
                        if first_segment in internal_prefixes:
                             # It's an internal module but file missing -> Implicit
                            target_node = f"implicit:{imp_name}"
                            target_type = "implicit"
                        # If startswith @ (e.g. @components), and not found, might be internal alias
                        elif imp_name.startswith('@'):
                             target_node = f"implicit:{imp_name}"
                             target_type = "implicit"

                # Add Edge if Target Found
                if target_node and target_node != filename:
                    # If implicit, ensure node exists
                    if target_type == "implicit":
                        if not graph.has_node(target_node):
                            graph.add_node(
                                target_node,
                                type="implicit", 
                                density=0.1,
                                val=10, 
                                label=target_node.replace("implicit:", ""),
                                is_implicit=True
                            )
                    
                    graph.add_edge(filename, target_node, type="import")

        return graph

    def _find_node_fuzzy(self, name: str, mapping: Dict[str, str]) -> Optional[str]:
        """Tries to find a node with exact match or partial match"""
        name = name.replace('/', '.') # Standardize
        
        # 1. Exact match
        if name in mapping:
            return mapping[name]
            
        # 2. Exact match with index suffix
        # mapping handles folder->index, so this is covered if name is folder
        
        # 3. Partial match (submodules)
        # import a.b.c -> link to a.b if a.b.c not found
        parts = name.split('.')
        for i in range(len(parts)-1, 0, -1):
            sub = ".".join(parts[:i])
            if sub in mapping:
                return mapping[sub]
                
        return None

    def _get_module_path_from_filename(self, filename: str) -> str:
        import os
        name_no_ext = os.path.splitext(filename)[0]
        # Always return full path including __init__ for correct relative resolution
        return name_no_ext.replace('/', '.')

    def _resolve_relative_import(self, current_package: str, relative_name: str, level: int) -> str:
        """
        Resolves relative import like '..utils' from 'app.api.endpoints'
        """
        parts = current_package.split('.')
        
        if level > len(parts):
            return relative_name or ""
            
        base_parts = parts[:-level] if level < len(parts) else []
        
        base_package = ".".join(base_parts)
        
        if base_package and relative_name:
            return f"{base_package}.{relative_name}"
        elif base_package:
            return base_package
        else:
            return relative_name or ""


    def _extract_imports(self, content: str, file_path: str = "") -> List[tuple]:
        """
        Extracts imported module names and relative levels.
        Dispatches to language specific extractors.
        """
        if not content:
            return []

        # Detect language
        is_js_ts = file_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'))
        
        if is_js_ts:
            return self._extract_imports_javascript(content)
        else:
            return self._extract_imports_python(content)

    def _extract_imports_python(self, content: str) -> List[tuple]:
        """Python AST based import extraction"""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, 0))
                elif isinstance(node, ast.ImportFrom):
                    level = node.level if node.level else 0
                    module = node.module
                    
                    if not module and level > 0:
                        for alias in node.names:
                            imports.append((alias.name, level))
                    else:
                        base_mod = module if module else ""
                        for alias in node.names:
                            full_import = f"{base_mod}.{alias.name}"
                            imports.append((full_import, level))
                        if base_mod:
                            imports.append((base_mod, level))
                        
        except SyntaxError:
            pass
                
        return list(set(imports))

    def _extract_imports_javascript(self, content: str) -> List[tuple]:
        """Regex based JS/TS import extraction"""
        imports = []
        import re
        
        # 1. ES6 Import
        es6_pattern = r'import\s+(?:[\w\s{},*]+from\s+)?[\'"]([^\'\"]+)[\'"]'
        
        # 2. CommonJS Require
        cjs_pattern = r'require\([\'"]([^\'\"]+)[\'"]\)'
        
        # 3. Dynamic Import
        dyn_pattern = r'import\([\'"]([^\'\"]+)[\'"]\)'
        
        # 4. Export from (Re-export)
        export_pattern = r'export\s+(?:[\w\s{},*]+from\s+)?[\'"]([^\'\"]+)[\'"]'
        
        all_patterns = [es6_pattern, cjs_pattern, dyn_pattern, export_pattern]
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content)
            for path in matches:
                if path.startswith('./'):
                    imports.append((path[2:], 1))
                elif path.startswith('../'):
                    level = 1 + path.count('../')
                    clean_path = path.replace('../', '')
                    imports.append((clean_path, level))
                elif path.startswith('@/'):
                    imports.append((path, 0))
                else:
                    imports.append((path, 0))
                    
        return list(set(imports))
