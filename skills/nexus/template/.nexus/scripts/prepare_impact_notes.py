#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from graph_helpers import dump_yaml, load_yaml


DEFAULT_OUTPUT = {
    'status': 'error',
    'reason': '',
    'pending_count': 0,
    'notes': [],
    'errors': [],
    'warnings': [],
    'meta': {},
}


def normalize_text(value: str) -> str:
    return ' '.join(value.split())


def normalize_path(value: str) -> str:
    normalized = value.strip().replace('\\', '/')
    while normalized.startswith('./'):
        normalized = normalized[2:]
    return normalized


def normalize_string_list(note_id: str, field: str, value: Any, *, path_mode: bool = False) -> tuple[list[str], list[str]]:
    warnings = []
    if value is None:
        return [], warnings
    if not isinstance(value, list):
        return [], [f"note {note_id} field '{field}' must be a list; ignoring it"]

    normalized = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            warnings.append(f"note {note_id} field '{field}' dropped non-string item")
            continue
        original = item
        item = normalize_path(item) if path_mode else item.strip()
        if not item:
            warnings.append(f"note {note_id} field '{field}' dropped empty item")
            continue
        if item != original:
            warnings.append(f"note {note_id} field '{field}' normalized '{original}' to '{item}'")
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized, warnings


def build_error_output(reason: str, errors: list[str], warnings: list[str], source: str) -> dict[str, Any]:
    return {
        **DEFAULT_OUTPUT,
        'status': 'error',
        'reason': reason,
        'errors': errors,
        'warnings': warnings,
        'meta': {'source': source},
    }


def prepare_notes(map_dir: str = '.nexus') -> dict[str, Any]:
    notes_path = Path(map_dir) / 'impact-notes.yaml'
    source = f'{map_dir}/impact-notes.yaml'
    if not notes_path.exists():
        return build_error_output('missing_notes_file', [f"notes file not found: {source}"], [], source)

    try:
        data = load_yaml(notes_path)
    except Exception as exc:
        return build_error_output('invalid_notes_file', [f'failed to load {source}: {exc}'], [], source)

    if not isinstance(data, dict):
        return build_error_output('invalid_notes_file', ['top-level notes file must be a mapping'], [], source)

    errors = []
    warnings = []
    pending = data.get('pending', [])
    transformed = data.get('transformed', [])

    if 'pending' in data and not isinstance(pending, list):
        errors.append("top-level field 'pending' must be a list")
    if 'transformed' in data and not isinstance(transformed, list):
        errors.append("top-level field 'transformed' must be a list")
    if errors:
        return build_error_output('invalid_notes_file', errors, warnings, source)

    notes = []
    for index, entry in enumerate(pending):
        if not isinstance(entry, dict):
            errors.append(f'pending entry at index {index} must be a mapping')
            continue

        note_id = entry.get('note_id')
        if not isinstance(note_id, str) or not note_id.strip():
            errors.append(f"pending entry at index {index} is missing required field 'note_id'")
            continue

        text = entry.get('text')
        if not isinstance(text, str) or not text.strip():
            errors.append(f"pending entry '{note_id}' is missing required field 'text'")
            continue

        route_hint = entry.get('route_hint', '')
        if route_hint is None:
            route_hint = ''
        elif isinstance(route_hint, str):
            stripped = route_hint.strip()
            if stripped != route_hint:
                warnings.append(f"note {note_id} field 'route_hint' normalized '{route_hint}' to '{stripped}'")
            route_hint = stripped
        else:
            warnings.append(f"note {note_id} field 'route_hint' must be a string; using empty string")
            route_hint = ''

        file_hints, field_warnings = normalize_string_list(note_id, 'file_hints', entry.get('file_hints'), path_mode=True)
        warnings.extend(field_warnings)
        symbol_hints, field_warnings = normalize_string_list(note_id, 'symbol_hints', entry.get('symbol_hints'))
        warnings.extend(field_warnings)
        tags, field_warnings = normalize_string_list(note_id, 'tags', entry.get('tags'))
        warnings.extend(field_warnings)

        notes.append(
            {
                'note_id': note_id,
                'text': normalize_text(text),
                'route_hint': route_hint,
                'file_hints': file_hints,
                'symbol_hints': symbol_hints,
                'tags': tags,
            }
        )

    if errors:
        return build_error_output('invalid_notes_file', errors, warnings, source)

    pending_count = len(notes)
    status = 'ready' if pending_count else 'skip'
    reason = 'pending_notes_found' if pending_count else 'no_pending_notes'
    return {
        'status': status,
        'reason': reason,
        'pending_count': pending_count,
        'notes': notes,
        'errors': [],
        'warnings': warnings,
        'meta': {
            'source': source,
            'transformed_count': len(transformed),
            'pending_raw_count': len(pending),
            'pending_usable_count': pending_count,
        },
    }


def main(map_dir: str = '.nexus') -> int:
    output = prepare_notes(map_dir)
    sys.stdout.write(dump_yaml(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
