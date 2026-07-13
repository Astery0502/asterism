#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from graph_helpers import dump_yaml, load_yaml, load_yaml_text, normalize_graph_node_id


DEFAULT_OUTPUT = {
    'status': 'error',
    'reason': '',
    'node_count': 0,
    'edge_count': 0,
    'node_intents': [],
    'edge_intents': [],
    'errors': [],
    'warnings': [],
    'duplicates': {'existing': [], 'batch': []},
    'meta': {},
}


def build_error_output(reason: str, errors: list[str], warnings: list[str], map_dir: str) -> dict[str, Any]:
    return {
        **DEFAULT_OUTPUT,
        'status': 'error',
        'reason': reason,
        'errors': errors,
        'warnings': warnings,
        'meta': {
            'source': 'stdin',
            'rules_source': f'{map_dir}/impact-rules.yaml',
            'routes_source': f'{map_dir}/routes.yaml',
            'intent_source': f'{map_dir}/impact.intent.yaml',
        },
    }


def load_candidate_payload(stdin_text: str) -> dict[str, Any]:
    text = stdin_text.strip()
    if not text:
        return {}
    return load_yaml_text(text)


def normalize_path_string(value: str) -> str:
    return normalize_graph_node_id(value.replace('\\', '/'))


def normalize_required_ref(field: str, value: Any, errors: list[str], warnings: list[str], context: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context} is missing required field '{field}'")
        return None
    normalized = normalize_path_string(value)
    if not normalized:
        errors.append(f"{context} is missing required field '{field}'")
        return None
    if normalized != value:
        warnings.append(f"{context} field '{field}' normalized '{value}' to '{normalized}'")
    return normalized


def normalize_required_string(field: str, value: Any, errors: list[str], warnings: list[str], context: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context} is missing required field '{field}'")
        return None
    normalized = value.strip()
    if normalized != value:
        warnings.append(f"{context} field '{field}' normalized '{value}' to '{normalized}'")
    return normalized


def normalize_optional_string(field: str, value: Any, warnings: list[str], context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        warnings.append(f"{context} field '{field}' must be a string; dropping it")
        return None
    normalized = value.strip()
    if normalized != value:
        warnings.append(f"{context} field '{field}' normalized '{value}' to '{normalized}'")
    if not normalized:
        warnings.append(f"{context} field '{field}' dropped empty value")
        return None
    return normalized


def load_rule_sets(rules_data: dict[str, Any]) -> tuple[set[str], set[str]]:
    node_rule_ids = set()
    edge_rule_ids = set()
    for entry in rules_data.get('rule_catalog', []) or []:
        if not isinstance(entry, dict):
            continue
        rule_id = entry.get('id')
        scope = entry.get('scope')
        if not isinstance(rule_id, str) or not isinstance(scope, str):
            continue
        if scope in ('node', 'node_edge'):
            node_rule_ids.add(rule_id)
        if scope in ('edge', 'node_edge'):
            edge_rule_ids.add(rule_id)
    return node_rule_ids, edge_rule_ids


def load_route_ids(routes_data: dict[str, Any]) -> set[str]:
    route_ids = set()
    for entry in routes_data.get('nodes', []) or []:
        if not isinstance(entry, dict):
            continue
        route_id = entry.get('id')
        if isinstance(route_id, str) and route_id:
            route_ids.add(route_id)
    return route_ids


def existing_node_keys(intent_data: dict[str, Any]) -> set[tuple[str, str, str | None]]:
    keys = set()
    for entry in intent_data.get('node_intents', []) or []:
        if not isinstance(entry, dict):
            continue
        target = entry.get('target')
        kind = entry.get('kind')
        if not isinstance(target, str) or not isinstance(kind, str):
            continue
        route_ref = entry.get('route_ref')
        route_ref = route_ref if isinstance(route_ref, str) and route_ref.strip() else None
        keys.add((normalize_path_string(target), kind.strip(), route_ref.strip() if isinstance(route_ref, str) else None))
    return keys


def existing_edge_keys(intent_data: dict[str, Any]) -> set[tuple[str, str, str, str | None]]:
    keys = set()
    for entry in intent_data.get('edge_intents', []) or []:
        if not isinstance(entry, dict):
            continue
        from_ref = entry.get('from')
        to_ref = entry.get('to')
        edge_type = entry.get('type')
        if not isinstance(from_ref, str) or not isinstance(to_ref, str) or not isinstance(edge_type, str):
            continue
        when = entry.get('when')
        when = when if isinstance(when, str) and when.strip() else None
        keys.add((normalize_path_string(from_ref), normalize_path_string(to_ref), edge_type.strip(), when.strip() if isinstance(when, str) else None))
    return keys


def node_duplicate_record(key: tuple[str, str, str | None]) -> dict[str, Any]:
    return {
        'intent_type': 'node',
        'key': {
            'target': key[0],
            'kind': key[1],
            'route_ref': key[2],
        },
    }


def edge_duplicate_record(key: tuple[str, str, str, str | None]) -> dict[str, Any]:
    return {
        'intent_type': 'edge',
        'key': {
            'from': key[0],
            'to': key[1],
            'type': key[2],
            'when': key[3],
        },
    }


def normalize_node_intent(entry: Any, index: int, node_rule_ids: set[str], valid_route_ids: set[str], errors: list[str], warnings: list[str]) -> dict[str, Any] | None:
    context = f'node intent at index {index}'
    if not isinstance(entry, dict):
        errors.append(f'{context} must be a mapping')
        return None

    note_id = normalize_optional_string('note_id', entry.get('note_id'), warnings, context)
    target = normalize_required_ref('target', entry.get('target'), errors, warnings, context)
    kind = normalize_required_string('kind', entry.get('kind'), errors, warnings, context)
    route_ref = normalize_optional_string('route_ref', entry.get('route_ref'), warnings, context)
    role = normalize_optional_string('role', entry.get('role'), warnings, context)

    if target is None or kind is None:
        return None
    if kind not in node_rule_ids:
        errors.append(f"{context} has invalid rule id '{kind}' for field 'kind'")
        return None
    if route_ref is not None and route_ref not in valid_route_ids:
        errors.append(f"{context} route_ref '{route_ref}' not found in .nexus/routes.yaml")
        return None

    normalized = {'target': target, 'kind': kind}
    if note_id is not None:
        normalized['note_id'] = note_id
    if route_ref is not None:
        normalized['route_ref'] = route_ref
    if role is not None:
        normalized['role'] = role
    return normalized


def normalize_edge_intent(entry: Any, index: int, edge_rule_ids: set[str], errors: list[str], warnings: list[str]) -> dict[str, Any] | None:
    context = f'edge intent at index {index}'
    if not isinstance(entry, dict):
        errors.append(f'{context} must be a mapping')
        return None

    note_id = normalize_optional_string('note_id', entry.get('note_id'), warnings, context)
    from_ref = normalize_required_ref('from', entry.get('from'), errors, warnings, context)
    to_ref = normalize_required_ref('to', entry.get('to'), errors, warnings, context)
    edge_type = normalize_required_string('type', entry.get('type'), errors, warnings, context)
    when = normalize_optional_string('when', entry.get('when'), warnings, context)

    if from_ref is None or to_ref is None or edge_type is None:
        return None
    if edge_type not in edge_rule_ids:
        errors.append(f"{context} has invalid rule id '{edge_type}' for field 'type'")
        return None

    normalized = {'from': from_ref, 'to': to_ref, 'type': edge_type}
    if note_id is not None:
        normalized['note_id'] = note_id
    if when is not None:
        normalized['when'] = when
    return normalized


def validate_candidate_intents(map_dir: str = '.nexus', stdin_text: str = '') -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    map_path = Path(map_dir)
    rules_path = map_path / 'impact-rules.yaml'
    routes_path = map_path / 'routes.yaml'
    intent_path = map_path / 'impact.intent.yaml'

    missing = [str(path) for path in (rules_path, routes_path, intent_path) if not path.exists()]
    if missing:
        missing_errors = [f'missing required file: {path}' for path in missing]
        return build_error_output('invalid_candidate_intents', missing_errors, warnings, map_dir)

    try:
        payload = load_candidate_payload(stdin_text)
    except Exception as exc:
        return build_error_output('invalid_candidate_intents', [f'failed to load candidate payload: {exc}'], warnings, map_dir)
    if not isinstance(payload, dict):
        return build_error_output('invalid_candidate_intents', ['top-level candidate payload must be a mapping'], warnings, map_dir)

    node_candidates = payload.get('node_intents', [])
    edge_candidates = payload.get('edge_intents', [])
    if 'node_intents' in payload and not isinstance(node_candidates, list):
        errors.append("top-level field 'node_intents' must be a list")
    if 'edge_intents' in payload and not isinstance(edge_candidates, list):
        errors.append("top-level field 'edge_intents' must be a list")
    if errors:
        return build_error_output('invalid_candidate_intents', errors, warnings, map_dir)

    try:
        rules_data = load_yaml(rules_path)
        routes_data = load_yaml(routes_path)
        intent_data = load_yaml(intent_path)
    except Exception as exc:
        return build_error_output('invalid_candidate_intents', [f'failed to load nexus sources: {exc}'], warnings, map_dir)

    node_rule_ids, edge_rule_ids = load_rule_sets(rules_data)
    valid_route_ids = load_route_ids(routes_data)
    existing_node = existing_node_keys(intent_data)
    existing_edge = existing_edge_keys(intent_data)

    normalized_nodes = []
    for index, entry in enumerate(node_candidates):
        normalized = normalize_node_intent(entry, index, node_rule_ids, valid_route_ids, errors, warnings)
        if normalized is not None:
            normalized_nodes.append(normalized)

    normalized_edges = []
    for index, entry in enumerate(edge_candidates):
        normalized = normalize_edge_intent(entry, index, edge_rule_ids, errors, warnings)
        if normalized is not None:
            normalized_edges.append(normalized)

    if errors:
        return build_error_output('invalid_candidate_intents', errors, warnings, map_dir)

    duplicates = {'existing': [], 'batch': []}
    accepted_nodes = []
    seen_nodes = set()
    for entry in normalized_nodes:
        key = (entry['target'], entry['kind'], entry.get('route_ref'))
        if key in existing_node:
            duplicates['existing'].append(node_duplicate_record(key))
            warnings.append(f"filtered existing duplicate node intent for target '{entry['target']}'")
            continue
        if key in seen_nodes:
            duplicates['batch'].append(node_duplicate_record(key))
            warnings.append(f"filtered batch duplicate node intent for target '{entry['target']}'")
            continue
        seen_nodes.add(key)
        accepted_nodes.append(entry)

    accepted_edges = []
    seen_edges = set()
    for entry in normalized_edges:
        key = (entry['from'], entry['to'], entry['type'], entry.get('when'))
        if key in existing_edge:
            duplicates['existing'].append(edge_duplicate_record(key))
            warnings.append(f"filtered existing duplicate edge intent from '{entry['from']}' to '{entry['to']}'")
            continue
        if key in seen_edges:
            duplicates['batch'].append(edge_duplicate_record(key))
            warnings.append(f"filtered batch duplicate edge intent from '{entry['from']}' to '{entry['to']}'")
            continue
        seen_edges.add(key)
        accepted_edges.append(entry)

    if not node_candidates and not edge_candidates:
        status = 'skip'
        reason = 'no_candidate_intents'
    elif not accepted_nodes and not accepted_edges:
        status = 'skip'
        reason = 'no_new_intents'
    else:
        status = 'ready'
        reason = 'validated_intents_ready'

    return {
        'status': status,
        'reason': reason,
        'node_count': len(accepted_nodes),
        'edge_count': len(accepted_edges),
        'node_intents': accepted_nodes,
        'edge_intents': accepted_edges,
        'errors': [],
        'warnings': warnings,
        'duplicates': duplicates,
        'meta': {
            'source': 'stdin',
            'rules_source': f'{map_dir}/impact-rules.yaml',
            'routes_source': f'{map_dir}/routes.yaml',
            'intent_source': f'{map_dir}/impact.intent.yaml',
            'candidate_node_count': len(node_candidates),
            'candidate_edge_count': len(edge_candidates),
            'accepted_node_count': len(accepted_nodes),
            'accepted_edge_count': len(accepted_edges),
            'duplicate_existing_node_count': sum(1 for item in duplicates['existing'] if item['intent_type'] == 'node'),
            'duplicate_existing_edge_count': sum(1 for item in duplicates['existing'] if item['intent_type'] == 'edge'),
            'duplicate_batch_node_count': sum(1 for item in duplicates['batch'] if item['intent_type'] == 'node'),
            'duplicate_batch_edge_count': sum(1 for item in duplicates['batch'] if item['intent_type'] == 'edge'),
        },
    }


def main(map_dir: str = '.nexus') -> int:
    output = validate_candidate_intents(map_dir=map_dir, stdin_text=sys.stdin.read())
    sys.stdout.write(dump_yaml(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
