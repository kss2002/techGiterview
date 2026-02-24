"""
Local Repository Analyzer Service

Extracted from API router to keep route module focused on HTTP concerns.
"""

import time
from typing import Any, Dict, List, Optional

from app.services.github_client import GitHubClient


class LocalRepositoryAnalyzer:
    """Repository helper for file-tree and file-content operations."""

    def __init__(self, github_client: Optional[GitHubClient] = None):
        self.github_client = github_client or GitHubClient()

    @staticmethod
    def _build_repo_url(owner: str, repo: str) -> str:
        return f"https://github.com/{owner}/{repo}"

    async def _get_repository_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
    ) -> List[Dict[str, Any]]:
        repo_url = self._build_repo_url(owner, repo)
        async with self.github_client as client:
            return await client.get_file_tree(repo_url, path)

    async def _get_complete_repository_tree(
        self,
        owner: str,
        repo: str,
    ) -> List[Dict[str, Any]]:
        repo_url = self._build_repo_url(owner, repo)
        async with self.github_client as client:
            return await client.get_recursive_file_tree(repo_url)

    async def get_file_content(self, owner: str, repo: str, file_path: str) -> Optional[str]:
        repo_url = self._build_repo_url(owner, repo)
        async with self.github_client as client:
            return await client.get_file_content(repo_url, file_path)

    async def get_all_files(
        self,
        owner: str,
        repo: str,
        max_depth: int = 3,
        max_files: int = 500,
    ) -> List[Dict[str, Any]]:
        """Fetch repository file tree using GitHub recursive tree API."""
        try:
            print(f"[GET_ALL_FILES] Starting Tree API fetch for {owner}/{repo}")
            start_time = time.time()

            tree_items = await self._get_complete_repository_tree(owner, repo)

            api_time = time.time() - start_time
            print(f"[GET_ALL_FILES] Tree API completed in {api_time:.2f}s, got {len(tree_items)} items")

            file_tree = self._build_file_tree_from_tree_api(tree_items, max_depth, max_files)

            total_time = time.time() - start_time
            print(f"[GET_ALL_FILES] Tree processing completed in {total_time:.2f}s, built {len(file_tree)} nodes")
            return file_tree
        except Exception as e:
            print(f"[GET_ALL_FILES] Error in get_all_files: {e}")
            print("[GET_ALL_FILES] Falling back to Contents API...")
            return await self._get_all_files_fallback(owner, repo, max_depth, max_files)

    def _build_file_tree_from_tree_api(
        self,
        tree_items: List[Dict[str, Any]],
        max_depth: int,
        max_files: int,
    ) -> List[Dict[str, Any]]:
        paths_by_depth: Dict[int, List[Dict[str, Any]]] = {}
        file_count = 0

        for item in tree_items:
            if file_count >= max_files:
                break

            path = item.get("path", "")
            if not path:
                continue

            depth = path.count("/")
            if depth > max_depth:
                continue

            name = path.split("/")[-1]
            if self._should_exclude_file_or_dir(name):
                continue

            if depth not in paths_by_depth:
                paths_by_depth[depth] = []

            item_type = item.get("type", "file")
            normalized_type = "dir" if item_type in {"tree", "dir"} else "file"

            paths_by_depth[depth].append(
                {
                    "name": name,
                    "path": path,
                    "type": normalized_type,
                    "size": item.get("size"),
                    "depth": depth,
                }
            )
            file_count += 1

        return self._build_nested_tree_structure(paths_by_depth, max_depth)

    def _should_exclude_file_or_dir(self, name: str) -> bool:
        if name.startswith(".") and name not in [".github", ".vscode"]:
            return True

        if name in ["node_modules", "venv", "__pycache__", "target", "build", "dist"]:
            return True

        if any(name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz"]):
            return True

        return False

    def _build_nested_tree_structure(
        self,
        paths_by_depth: Dict[int, List[Dict[str, Any]]],
        max_depth: int,
    ) -> List[Dict[str, Any]]:
        if 0 not in paths_by_depth:
            return []

        root_nodes = []
        for item in sorted(paths_by_depth[0], key=lambda x: (x["type"] == "file", x["name"].lower())):
            node = {
                "name": item["name"],
                "path": item["path"],
                "type": item["type"],
                "size": item["size"],
                "children": self._build_children_nodes(item["path"], paths_by_depth, 1, max_depth)
                if item["type"] == "dir"
                else None,
            }
            root_nodes.append(node)

        return root_nodes

    def _build_children_nodes(
        self,
        parent_path: str,
        paths_by_depth: Dict[int, List[Dict[str, Any]]],
        current_depth: int,
        max_depth: int,
    ) -> List[Dict[str, Any]]:
        if current_depth > max_depth or current_depth not in paths_by_depth:
            return []

        children: List[Dict[str, Any]] = []
        for item in paths_by_depth[current_depth]:
            if item["path"].startswith(parent_path + "/"):
                relative_path = item["path"][len(parent_path) + 1 :]
                if "/" not in relative_path:
                    node = {
                        "name": item["name"],
                        "path": item["path"],
                        "type": item["type"],
                        "size": item["size"],
                        "children": self._build_children_nodes(
                            item["path"], paths_by_depth, current_depth + 1, max_depth
                        )
                        if item["type"] == "dir"
                        else None,
                    }
                    children.append(node)

        return sorted(children, key=lambda x: (x["type"] == "file", x["name"].lower()))

    async def _get_all_files_fallback(
        self,
        owner: str,
        repo: str,
        max_depth: int,
        max_files: int,
    ) -> List[Dict[str, Any]]:
        """Fallback implementation using contents API."""
        print(f"[FALLBACK] Using Contents API for {owner}/{repo}")

        async def fetch_directory_recursive(path: str = "", current_depth: int = 0) -> List[Dict[str, Any]]:
            if current_depth >= max_depth:
                return []

            try:
                contents = await self._get_repository_contents(owner, repo, path)
                nodes: List[Dict[str, Any]] = []
                file_count = 0

                files = [item for item in contents if item.get("type") == "file"]
                dirs = [item for item in contents if item.get("type") == "dir"]

                for item in sorted(dirs, key=lambda x: x["name"].lower()):
                    if file_count >= max_files:
                        break

                    if item["name"].startswith(".") and item["name"] not in [".github", ".vscode"]:
                        continue
                    if item["name"] in ["node_modules", "venv", "__pycache__", "target", "build", "dist"]:
                        continue

                    children = await fetch_directory_recursive(item["path"], current_depth + 1)
                    nodes.append(
                        {
                            "name": item["name"],
                            "path": item["path"],
                            "type": "dir",
                            "size": item.get("size"),
                            "children": children if children else [],
                        }
                    )
                    file_count += 1

                for item in sorted(files, key=lambda x: x["name"].lower()):
                    if file_count >= max_files:
                        break

                    name = item["name"].lower()
                    if any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz"]):
                        continue

                    nodes.append(
                        {
                            "name": item["name"],
                            "path": item["path"],
                            "type": "file",
                            "size": item.get("size"),
                            "children": None,
                        }
                    )
                    file_count += 1

                return nodes
            except Exception as e:
                print(f"[FALLBACK] Error fetching directory {path}: {e}")
                return []

        try:
            return await fetch_directory_recursive()
        except Exception as e:
            print(f"[FALLBACK] Error in fallback method: {e}")
            return []
