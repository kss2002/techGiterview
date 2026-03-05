"""
Graph context builder for enhanced question generation.
"""

from __future__ import annotations

from typing import Dict, Iterable, List


class GraphContextBuilder:
    """코드 플로우 경로를 LLM 프롬프트용 텍스트로 변환한다."""

    @staticmethod
    def _normalize_path_nodes(path: object) -> List[str]:
        if isinstance(path, list):
            return [str(node) for node in path if node]
        if isinstance(path, tuple):
            return [str(node) for node in path if node]
        if isinstance(path, dict):
            nodes = path.get("nodes") or path.get("path") or []
            if isinstance(nodes, (list, tuple)):
                return [str(node) for node in nodes if node]
        return []

    def build_flow_context(
        self,
        flow_paths: Iterable[object],
        file_map: Dict[str, str],
        node_types: Dict[str, object] | None = None,
    ) -> str:
        node_types = node_types or {}
        sections: List[str] = ["### Execution Flow Context"]

        rendered = 0
        for idx, raw_path in enumerate(flow_paths, start=1):
            nodes = self._normalize_path_nodes(raw_path)
            if len(nodes) < 2:
                continue

            rendered += 1
            sections.append(f"Flow {idx}: {' -> '.join(nodes)}")

            # Include light metadata for first/last node only to keep prompt compact.
            first = nodes[0]
            last = nodes[-1]
            first_type = node_types.get(first, "unknown")
            last_type = node_types.get(last, "unknown")
            sections.append(f"- Entry: {first} ({first_type})")
            sections.append(f"- Exit: {last} ({last_type})")

            for focus_node in (first, last):
                content = file_map.get(focus_node)
                if not content:
                    continue
                preview = content.strip().replace("\n", " ")[:220]
                if preview:
                    sections.append(f"- {focus_node} preview: {preview}")

            if rendered >= 3:
                break

        if rendered == 0:
            return ""
        return "\n".join(sections)

