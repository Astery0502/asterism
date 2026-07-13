#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from graph_helpers import load_yaml, save_json


def main(map_dir='.nexus'):
    map_path = Path(map_dir)
    routes_path = map_path / 'routes.yaml'
    impact_path = map_path / 'impact.yaml'
    out_path = map_path / 'route-index.json'
    if not routes_path.exists():
        print(f'Error: missing routes file: {routes_path}', file=sys.stderr)
        return 1
    routes = load_yaml(routes_path)
    impact = load_yaml(impact_path) if impact_path.exists() else {}
    by_route_id = {}
    path_to_route_id = {}
    for node in routes.get('nodes', []):
        route_id = node['id']
        by_route_id[route_id] = {'path': node['path'], 'kind': node['kind'], 'children': node.get('children', []), 'graph_nodes': []}
        path_to_route_id[node['path']] = route_id
    graph_node_to_route_id = {}
    for gnode in impact.get('nodes', []):
        rid = gnode.get('route_ref')
        if rid in by_route_id:
            by_route_id[rid]['graph_nodes'].append(gnode['id'])
        graph_node_to_route_id[gnode['id']] = rid
    for data in by_route_id.values():
        data['graph_nodes'] = sorted(set(data['graph_nodes']))
    save_json(out_path, {'version': 1, 'routes_ref': str(routes_path).replace('\\', '/'), 'impact_ref': str(impact_path).replace('\\', '/'), 'by_route_id': by_route_id, 'path_to_route_id': path_to_route_id, 'graph_node_to_route_id': graph_node_to_route_id})
    print(f'Synced {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
