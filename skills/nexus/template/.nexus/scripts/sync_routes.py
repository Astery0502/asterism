#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from graph_helpers import load_yaml, save_yaml

MANUAL_FIELDS = ["purpose", "enter_when", "avoid_when", "inspect_first"]
STRUCTURE_FIELDS = ["id", "path", "kind", "stale", "children"]


def get_repo_root(project_root: str | Path = ".") -> Path:
    project_root = Path(project_root)
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=project_root, text=True, capture_output=True, check=True)
        return Path(result.stdout.strip())
    except Exception:
        return project_root.resolve()


def git_visible_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, text=True, capture_output=True, check=True)
        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and (root / line).exists():
                files.append(line)
        return sorted(files)
    except Exception:
        return filesystem_visible_files(root)


def filesystem_visible_files(root: Path) -> list[str]:
    files = []
    for base, dirs, filenames in os.walk(root):
        base_path = Path(base)
        rel_dir = base_path.relative_to(root).as_posix()
        if rel_dir == '.':
            rel_dir = ''
        dirs[:] = [d for d in dirs if d != '.git']
        for filename in filenames:
            rel_path = (Path(rel_dir) / filename).as_posix() if rel_dir else filename
            files.append(rel_path)
    return sorted(files)


def match_any(path_str: str, patterns: list[str]) -> bool:
    name = Path(path_str).name
    return any(fnmatch.fnmatch(path_str, p) or fnmatch.fnmatch(name, p) for p in patterns)


def normalize_dir(path_str: str) -> str:
    if path_str in ('', '.'):
        return '.'
    return path_str.rstrip('/') + '/'


def path_to_id(path_str: str) -> str:
    if path_str == '.':
        return 'root'
    s = path_str.rstrip('/')
    return '.'.join(part.replace('.', '_').replace('-', '_').replace(' ', '_') for part in s.split('/'))


def collect_dirs(files: list[str]) -> set[str]:
    dirs = {'.'}
    for file_str in files:
        p = Path(file_str)
        for parent in list(p.parents)[:-1]:
            dirs.add('.' if str(parent) == '.' else normalize_dir(parent.as_posix()))
    return dirs


def build_active_nodes(files: list[str], rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exclude = rules.get('exclude', []) or []
    pins = set(rules.get('pins', []) or [])
    glob_rules = rules.get('glob_rules', []) or []
    filtered_files = [f for f in files if not match_any(f, exclude)]
    dirs = collect_dirs(filtered_files)
    nodes = {}
    for d in sorted(dirs):
        nodes[d] = {'id': path_to_id(d), 'path': d, 'kind': 'dir', 'stale': False, 'purpose': '', 'enter_when': [], 'avoid_when': [], 'inspect_first': [], 'children': []}
    promoted_files = [f for f in filtered_files if f in pins or match_any(f, glob_rules)]
    for f in sorted(set(promoted_files)):
        nodes[f] = {'id': path_to_id(f), 'path': f, 'kind': 'file', 'stale': False, 'purpose': '', 'enter_when': [], 'avoid_when': [], 'inspect_first': [], 'children': []}
    dir_paths = [p for p, node in nodes.items() if node['kind'] == 'dir']
    for d in dir_paths:
        parent = Path('.' if d == '.' else d.rstrip('/'))
        children = []
        for candidate in dir_paths:
            if candidate in (d, '.'):
                continue
            cp = Path(candidate.rstrip('/'))
            if cp.parent == parent:
                children.append(nodes[candidate]['id'])
        for candidate, node in nodes.items():
            if node['kind'] != 'file':
                continue
            if Path(candidate).parent == parent:
                children.append(node['id'])
        nodes[d]['children'] = sorted(set(children))
    return nodes


def load_existing_nodes(routes_path: Path) -> dict[str, dict[str, Any]]:
    if not routes_path.exists():
        return {}
    data = load_yaml(routes_path)
    return {item['path']: item for item in data.get('nodes', []) if item.get('path')}


def merge_nodes(existing, active_nodes):
    merged = {}
    for path, active in active_nodes.items():
        old = existing.get(path, {})
        node = old.copy()
        for field in STRUCTURE_FIELDS:
            node[field] = active[field]
        for field in MANUAL_FIELDS:
            if field not in node:
                node[field] = active[field]
        merged[path] = node
    for path, old in existing.items():
        if path in merged:
            continue
        node = old.copy()
        node.setdefault('id', path_to_id(path))
        node.setdefault('path', path)
        node.setdefault('kind', 'file' if Path(path).suffix else 'dir')
        node['stale'] = True
        node['children'] = []
        for field in MANUAL_FIELDS:
            node.setdefault(field, [] if field != 'purpose' else '')
        merged[path] = node
    nodes = list(merged.values())
    nodes.sort(key=lambda n: (1 if n.get('stale', False) else 0, 0 if n['path'] == '.' else n['path'].count('/'), n['path']))
    return nodes


def ensure_root(nodes):
    if any(node.get('path') == '.' for node in nodes):
        return nodes
    return [{'id': 'root', 'path': '.', 'kind': 'dir', 'stale': False, 'purpose': '', 'enter_when': [], 'avoid_when': [], 'inspect_first': [], 'children': []}] + nodes


def main(project_root='.', map_dir='.nexus'):
    repo_root = get_repo_root(project_root)
    rules_path = repo_root / map_dir / 'routes_rules.yaml'
    routes_path = repo_root / map_dir / 'routes.yaml'
    if not rules_path.exists():
        print(f'Error: missing rules file: {rules_path}', file=sys.stderr)
        return 1
    try:
        rules = load_yaml(rules_path)
        files = git_visible_files(repo_root)
        active_nodes = build_active_nodes(files, rules)
        existing_nodes = load_existing_nodes(routes_path)
        nodes = ensure_root(merge_nodes(existing_nodes, active_nodes))
        save_yaml(routes_path, {'version': 1, 'nodes': nodes})
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(f'Synced {routes_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
