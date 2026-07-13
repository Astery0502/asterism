#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from graph_helpers import dump_yaml, load_yaml, load_yaml_text, save_yaml


DEFAULT_OUTPUT = {
    'status': 'error',
    'reason': '',
    'appended_node_count': 0,
    'appended_edge_count': 0,
    'transformed_note_ids': [],
    'generated_hint_ids': [],
    'remaining_pending_note_ids': [],
    'errors': [],
    'warnings': [],
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
            'intent_source': f'{map_dir}/impact.intent.yaml',
            'notes_source': f'{map_dir}/impact-notes.yaml',
        },
    }


def load_validated_payload(stdin_text: str) -> dict[str, Any]:
    text = stdin_text.strip()
    if not text:
        return {}
    return load_yaml_text(text)


def highest_hint_number(existing_transformed: list[dict[str, Any]]) -> int:
    highest = 0
    for entry in existing_transformed:
        if not isinstance(entry, dict):
            continue
        for hint_id in entry.get('hint_ids', []) or []:
            if not isinstance(hint_id, str):
                continue
            if not hint_id.startswith('H-'):
                continue
            suffix = hint_id[2:]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return highest


def strip_note_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    persisted = dict(entry)
    persisted.pop('note_id', None)
    return persisted


def collect_note_ids(entries: list[Any]) -> list[str]:
    note_ids = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        note_id = entry.get('note_id')
        if not isinstance(note_id, str) or not note_id.strip():
            continue
        normalized_note_id = note_id.strip()
        if normalized_note_id in seen:
            continue
        seen.add(normalized_note_id)
        note_ids.append(normalized_note_id)
    return note_ids


def build_hint_ids_by_note_id(entries: list[Any], pending_note_ids: set[str], starting_hint_number: int) -> tuple[dict[str, list[str]], list[str], list[str]]:
    hint_ids_by_note_id: dict[str, list[str]] = {}
    generated_hint_ids: list[str] = []
    missing_note_ids: list[str] = []
    seen_missing = set()
    next_hint_number = starting_hint_number
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        note_id = entry.get('note_id')
        if not isinstance(note_id, str) or not note_id.strip():
            continue
        normalized_note_id = note_id.strip()
        if normalized_note_id not in pending_note_ids:
            if normalized_note_id not in seen_missing:
                seen_missing.add(normalized_note_id)
                missing_note_ids.append(normalized_note_id)
            continue
        next_hint_number += 1
        hint_id = f'H-{next_hint_number:03d}'
        generated_hint_ids.append(hint_id)
        hint_ids_by_note_id.setdefault(normalized_note_id, []).append(hint_id)
    return hint_ids_by_note_id, generated_hint_ids, missing_note_ids


def apply_validated_intents(map_dir: str = '.nexus', stdin_text: str = '') -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    map_path = Path(map_dir)
    intent_path = map_path / 'impact.intent.yaml'
    notes_path = map_path / 'impact-notes.yaml'

    missing = [str(path) for path in (intent_path, notes_path) if not path.exists()]
    if missing:
        missing_errors = [f'missing required file: {path}' for path in missing]
        return build_error_output('invalid_validated_intents', missing_errors, warnings, map_dir)

    try:
        payload = load_validated_payload(stdin_text)
    except Exception as exc:
        return build_error_output('invalid_validated_intents', [f'failed to load validated payload: {exc}'], warnings, map_dir)
    if not isinstance(payload, dict):
        return build_error_output('invalid_validated_intents', ['top-level validated payload must be a mapping'], warnings, map_dir)

    node_intents = payload.get('node_intents', [])
    edge_intents = payload.get('edge_intents', [])
    status = payload.get('status')
    reason = payload.get('reason')
    if 'node_intents' in payload and not isinstance(node_intents, list):
        errors.append("top-level field 'node_intents' must be a list")
    if 'edge_intents' in payload and not isinstance(edge_intents, list):
        errors.append("top-level field 'edge_intents' must be a list")
    if status is not None and not isinstance(status, str):
        errors.append("top-level field 'status' must be a string when present")
    if reason is not None and not isinstance(reason, str):
        errors.append("top-level field 'reason' must be a string when present")
    if errors:
        return build_error_output('invalid_validated_intents', errors, warnings, map_dir)

    if status == 'error':
        forwarded_errors = payload.get('errors', [])
        if isinstance(forwarded_errors, list) and forwarded_errors:
            errors.extend(str(item) for item in forwarded_errors)
        else:
            errors.append('validated payload reported status=error')
        return build_error_output('invalid_validated_intents', errors, warnings, map_dir)

    try:
        intent_data = load_yaml(intent_path)
        notes_data = load_yaml(notes_path)
    except Exception as exc:
        return build_error_output('invalid_validated_intents', [f'failed to load nexus sources: {exc}'], warnings, map_dir)

    if not isinstance(intent_data, dict):
        return build_error_output('invalid_validated_intents', [f'{map_dir}/impact.intent.yaml must be a mapping'], warnings, map_dir)
    if not isinstance(notes_data, dict):
        return build_error_output('invalid_validated_intents', [f'{map_dir}/impact-notes.yaml must be a mapping'], warnings, map_dir)

    existing_node_intents = intent_data.get('node_intents', []) or []
    existing_edge_intents = intent_data.get('edge_intents', []) or []
    aliases = intent_data.get('aliases', {}) or {}
    pending_notes = notes_data.get('pending', []) or []
    transformed_notes = notes_data.get('transformed', []) or []
    if not isinstance(existing_node_intents, list):
        return build_error_output('invalid_validated_intents', [f"{map_dir}/impact.intent.yaml field 'node_intents' must be a list"], warnings, map_dir)
    if not isinstance(existing_edge_intents, list):
        return build_error_output('invalid_validated_intents', [f"{map_dir}/impact.intent.yaml field 'edge_intents' must be a list"], warnings, map_dir)
    if not isinstance(aliases, dict):
        return build_error_output('invalid_validated_intents', [f"{map_dir}/impact.intent.yaml field 'aliases' must be a mapping"], warnings, map_dir)
    if not isinstance(pending_notes, list):
        return build_error_output('invalid_validated_intents', [f"{map_dir}/impact-notes.yaml field 'pending' must be a list"], warnings, map_dir)
    if not isinstance(transformed_notes, list):
        return build_error_output('invalid_validated_intents', [f"{map_dir}/impact-notes.yaml field 'transformed' must be a list"], warnings, map_dir)

    apply_ready = status == 'ready'
    appended_node_intents = [strip_note_metadata(entry) for entry in node_intents if apply_ready and isinstance(entry, dict)]
    appended_edge_intents = [strip_note_metadata(entry) for entry in edge_intents if apply_ready and isinstance(entry, dict)]

    existing_hint_highest = highest_hint_number(transformed_notes)
    pending_note_ids = {entry.get('note_id') for entry in pending_notes if isinstance(entry, dict) and isinstance(entry.get('note_id'), str)}
    hint_ids_by_note_id, generated_hint_ids, missing_note_ids = build_hint_ids_by_note_id(
        list(node_intents) + list(edge_intents) if apply_ready else [],
        pending_note_ids,
        existing_hint_highest,
    )
    transformed_note_ids = [note_id for note_id in collect_note_ids(list(node_intents) + list(edge_intents)) if note_id in hint_ids_by_note_id]
    today = date.today().isoformat()

    remaining_pending = []
    newly_transformed = []
    for entry in pending_notes:
        if not isinstance(entry, dict):
            remaining_pending.append(entry)
            continue
        note_id = entry.get('note_id')
        if isinstance(note_id, str) and note_id in hint_ids_by_note_id:
            newly_transformed.append({'note_id': note_id, 'hint_ids': hint_ids_by_note_id[note_id], 'date': today})
            continue
        remaining_pending.append(entry)

    if missing_note_ids:
        warnings.extend(f"accepted intent note_id '{note_id}' not found in pending notes" for note_id in missing_note_ids)


    if appended_node_intents or appended_edge_intents:
        save_yaml(
            intent_path,
            {
                'version': intent_data.get('version', 1),
                'node_intents': existing_node_intents + appended_node_intents,
                'edge_intents': existing_edge_intents + appended_edge_intents,
                'aliases': aliases,
            },
        )
        save_yaml(
            notes_path,
            {
                'version': notes_data.get('version', 1),
                'pending': remaining_pending,
                'transformed': transformed_notes + newly_transformed,
            },
        )

    if not appended_node_intents and not appended_edge_intents:
        output_status = 'skip'
        output_reason = 'no_validated_intents_to_apply'
    else:
        output_status = 'ready'
        output_reason = 'validated_intents_applied'

    remaining_pending_note_ids = []
    for entry in remaining_pending:
        if isinstance(entry, dict):
            note_id = entry.get('note_id')
            if isinstance(note_id, str) and note_id.strip():
                remaining_pending_note_ids.append(note_id)

    return {
        'status': output_status,
        'reason': output_reason,
        'appended_node_count': len(appended_node_intents),
        'appended_edge_count': len(appended_edge_intents),
        'transformed_note_ids': transformed_note_ids,
        'generated_hint_ids': generated_hint_ids,
        'remaining_pending_note_ids': remaining_pending_note_ids,
        'errors': [],
        'warnings': warnings,
        'meta': {
            'source': 'stdin',
            'intent_source': f'{map_dir}/impact.intent.yaml',
            'notes_source': f'{map_dir}/impact-notes.yaml',
            'validated_status': status or '',
            'validated_reason': reason or '',
        },
    }


def main(map_dir: str = '.nexus') -> int:
    output = apply_validated_intents(map_dir=map_dir, stdin_text=sys.stdin.read())
    sys.stdout.write(dump_yaml(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
