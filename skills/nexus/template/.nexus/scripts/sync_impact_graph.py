#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from graph_helpers import build_route_index_from_graph, load_json, load_yaml, normalize_graph_node_id, resolve_route_ref_for_file, save_yaml, validate_edge_endpoints


def main(map_dir='.nexus'):
    map_path = Path(map_dir)
    routes_path = map_path / 'routes.yaml'
    index_path = map_path / 'route-index.json'
    intent_path = map_path / 'impact.intent.yaml'
    out_path = map_path / 'impact.yaml'
    missing = [str(p) for p in (routes_path, index_path, intent_path) if not p.exists()]
    if missing:
        print(f"Error: missing required files: {', '.join(missing)}", file=sys.stderr)
        return 1
    routes = load_yaml(routes_path)
    index = load_json(index_path)
    intent = load_yaml(intent_path)
    valid_route_ids = {n['id'] for n in routes.get('nodes', [])}
    warnings = []
    nodes = []
    seen_ids = set()
    for entry in intent.get('node_intents', []):
        target = entry.get('target')
        kind = entry.get('kind')
        if not target or not kind:
            warnings.append(f'invalid node intent: {entry}')
            continue
        nid = normalize_graph_node_id(target)
        if nid in seen_ids:
            warnings.append(f'duplicate node id: {nid}')
            continue
        seen_ids.add(nid)
        route_ref = entry.get('route_ref')
        if route_ref and route_ref not in valid_route_ids:
            warnings.append(f'route_ref not found: {route_ref} for {nid}')
            route_ref = None
        file_path = nid.split(':', 1)[0]
        if not route_ref:
            route_ref = resolve_route_ref_for_file(file_path, index)
            if not route_ref:
                warnings.append(f'cannot resolve route_ref for: {nid}')
        symbol = nid.split(':', 1)[1] if ':' in nid else None
        node = {'id': nid, 'kind': kind, 'file': file_path, 'route_ref': route_ref, 'source': 'manual', 'confidence': 'curated' if route_ref else 'low'}
        if symbol:
            node['symbol'] = symbol
        if entry.get('role'):
            node['role'] = entry['role']
        nodes.append(node)
    node_ids = {n['id'] for n in nodes}
    edges = []
    for entry in intent.get('edge_intents', []):
        from_target = entry.get('from')
        to_target = entry.get('to')
        edge_type = entry.get('type')
        if not from_target or not to_target or not edge_type:
            warnings.append(f'invalid edge intent: {entry}')
            continue
        edge = {'from': normalize_graph_node_id(from_target), 'to': normalize_graph_node_id(to_target), 'type': edge_type, 'source': 'merged', 'confidence': 'curated'}
        if entry.get('when'):
            edge['when'] = entry['when']
        edges.append(edge)
    warnings.extend(validate_edge_endpoints(node_ids, edges))
    route_index = build_route_index_from_graph(nodes)
    for warning in warnings:
        print(f'WARNING: {warning}', file=sys.stderr)
    save_yaml(out_path, {'version': 1, 'graph_meta': {'compiler': 'scripts/sync_impact_graph.py', 'generated_from': [f'{map_dir}/routes.yaml', f'{map_dir}/impact.intent.yaml'], 'route_index_ref': f'{map_dir}/route-index.json'}, 'route_index': route_index, 'nodes': nodes, 'edges': edges})
    print(f'Synced {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
