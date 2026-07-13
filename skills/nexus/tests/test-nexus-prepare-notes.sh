#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$TESTS_DIR/lib/nexus-test-helpers.sh"

setup_nexus_test_repo
run_nexus_install "$NEXUS_PROJECT" >/dev/null

prepare_skip_output="$(run_prepare_impact_notes "$NEXUS_PROJECT")"
PREPARE_OUTPUT="$prepare_skip_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['PREPARE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['PREPARE_OUTPUT']) or {}
assert data['status'] == 'skip'
assert data['reason'] == 'no_pending_notes'
assert data['pending_count'] == 0
assert data['notes'] == []
PY

cat > "$NEXUS_PROJECT/.nexus/impact-notes.yaml" <<'YAML'
version: 1
pending:
  - note_id: "N-001"
    text: "  config/settings.yaml   controls   src/app.py main  "
    route_hint: " src.app_py "
    file_hints:
      - "./config/settings.yaml"
      - "config/settings.yaml"
      - ""
    symbol_hints:
      - "main"
      - 42
    tags:
      - "control"
      - "control"
transformed:
  - note_id: "N-000"
    hint_ids:
      - "H-001"
    date: "2026-04-23"
YAML

prepare_ready_output="$(run_prepare_impact_notes "$NEXUS_PROJECT")"
PREPARE_OUTPUT="$prepare_ready_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['PREPARE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['PREPARE_OUTPUT']) or {}
assert data['status'] == 'ready'
assert data['reason'] == 'pending_notes_found'
assert data['pending_count'] == 1
note = data['notes'][0]
assert note['note_id'] == 'N-001'
assert note['text'] == 'config/settings.yaml controls src/app.py main'
assert note['route_hint'] == 'src.app_py'
assert note['file_hints'] == ['config/settings.yaml']
assert note['symbol_hints'] == ['main']
assert note['tags'] == ['control']
assert data['meta']['transformed_count'] == 1
assert data['warnings']
PY

cat > "$NEXUS_PROJECT/.nexus/impact-notes.yaml" <<'YAML'
version: 1
pending:
  - note_id: "N-002"
    file_hints:
      - "src/app.py"
transformed: []
YAML

prepare_error_output="$(run_prepare_impact_notes "$NEXUS_PROJECT")"
PREPARE_OUTPUT="$prepare_error_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['PREPARE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['PREPARE_OUTPUT']) or {}
assert data['status'] == 'error'
assert data['reason'] == 'invalid_notes_file'
assert any("missing required field 'text'" in error for error in data['errors'])
PY

echo "PASS: nexus prepare impact notes behavior"
