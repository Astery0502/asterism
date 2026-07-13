#!/usr/bin/env python3
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any


def load_yaml_backend():
    try:
        from ruamel.yaml import YAML  # type: ignore
        return 'ruamel', YAML
    except Exception:
        pass
    try:
        import yaml  # type: ignore
        return 'pyyaml', yaml
    except Exception:
        return None, None


def load_yaml_text(text: str) -> dict[str, Any]:
    backend, module = load_yaml_backend()
    if backend == 'ruamel':
        yaml = module(typ='safe')  # type: ignore[operator]
        return yaml.load(text) or {}
    if backend == 'pyyaml':
        return module.safe_load(text) or {}  # type: ignore[union-attr]
    raise RuntimeError('Need ruamel.yaml or PyYAML to load YAML files.')


def dump_yaml(data: dict[str, Any]) -> str:
    backend, module = load_yaml_backend()
    if backend == 'ruamel':
        buffer = StringIO()
        yaml = module()  # type: ignore[operator]
        yaml.default_flow_style = False
        yaml.sort_base_mapping_type_on_output = False
        yaml.dump(data, buffer)
        return buffer.getvalue()
    if backend == 'pyyaml':
        return module.safe_dump(data, sort_keys=False, allow_unicode=True)  # type: ignore[union-attr]
    raise RuntimeError('Need ruamel.yaml or PyYAML to format YAML output.')


def write_text_if_changed(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.read_text(encoding='utf-8') == text:
        return
    p.write_text(text, encoding='utf-8')


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return load_yaml_text(p.read_text(encoding='utf-8'))


def save_yaml(path: str | Path, data: dict[str, Any]) -> None:
    write_text_if_changed(path, dump_yaml(data))


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    write_text_if_changed(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def normalize_graph_node_id(target: str) -> str:
    target = target.strip()
    while target.startswith('./'):
        target = target[2:]
    return target


def resolve_route_ref_for_file(file_path: str, route_index: dict[str, Any]) -> str | None:
    file_path = normalize_graph_node_id(file_path)
    path_map = route_index.get('path_to_route_id', {})
    best = None
    for route_path, route_id in path_map.items():
        rp = route_path.rstrip('/')
        if rp in ('', '.'):
            if best is None:
                best = (0, route_id)
            continue
        if file_path == rp or file_path.startswith(rp + '/'):
            score = len(rp)
            if best is None or score > best[0]:
                best = (score, route_id)
    return best[1] if best else None


def build_route_index_from_graph(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for node in nodes:
        route_ref = node.get('route_ref')
        if not route_ref:
            continue
        grouped.setdefault(route_ref, []).append(node['id'])
    return [{'route_ref': rid, 'graph_nodes': sorted(ids)} for rid, ids in sorted(grouped.items())]


def validate_edge_endpoints(node_ids: set[str], edges: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for edge in edges:
        if edge.get('from') not in node_ids:
            warnings.append(f"edge from unknown node: {edge.get('from')}")
        if edge.get('to') not in node_ids:
            warnings.append(f"edge to unknown node: {edge.get('to')}")
    return warnings
