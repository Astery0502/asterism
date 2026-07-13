#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$TESTS_DIR/lib/nexus-test-helpers.sh"

setup_nexus_test_repo
run_nexus_install "$NEXUS_PROJECT" >/dev/null
run_sync_routes "$NEXUS_PROJECT" >/dev/null

cat > "$NEXUS_PROJECT/.nexus/impact.intent.yaml" <<'YAML'
version: 1
node_intents:
  - target: "docs/notes.md"
    kind: file_as_node
    route_ref: docs.notes_md
edge_intents:
  - from: "docs/notes.md"
    to: "src/app.py:main"
    type: parameter_propagation
    when: "docs enabled"
aliases: {}
YAML

valid_payload=$(cat <<'YAML'
node_intents:
  - note_id: N-001
    target: "./src/app.py:main"
    kind: route_binding
    route_ref: src.app_py
edge_intents:
  - note_id: N-001
    from: "config/settings.yaml"
    to: "src/app.py:main"
    type: control_flow_gate
    when: "enabled == true"
YAML
)
valid_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "$valid_payload")"
VALIDATE_OUTPUT="$valid_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'ready'
assert data['reason'] == 'validated_intents_ready'
assert data['node_count'] == 1
assert data['edge_count'] == 1
assert data['node_intents'][0]['target'] == 'src/app.py:main'
assert data['node_intents'][0]['note_id'] == 'N-001'
assert data['warnings']
PY

invalid_rule_payload=$(cat <<'YAML'
node_intents:
  - target: "src/app.py:main"
    kind: not_a_rule
edge_intents: []
YAML
)
invalid_rule_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "$invalid_rule_payload")"
VALIDATE_OUTPUT="$invalid_rule_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'error'
assert data['reason'] == 'invalid_candidate_intents'
assert any("invalid rule id 'not_a_rule'" in error for error in data['errors'])
PY

invalid_route_payload=$(cat <<'YAML'
node_intents:
  - target: "src/app.py:main"
    kind: route_binding
    route_ref: missing.route
edge_intents: []
YAML
)
invalid_route_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "$invalid_route_payload")"
VALIDATE_OUTPUT="$invalid_route_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'error'
assert any("route_ref 'missing.route' not found" in error for error in data['errors'])
PY

duplicate_payload=$(cat <<'YAML'
node_intents:
  - target: "docs/notes.md"
    kind: file_as_node
    route_ref: docs.notes_md
  - target: "src/app.py:main"
    kind: route_binding
    route_ref: src.app_py
  - target: "src/app.py:main"
    kind: route_binding
    route_ref: src.app_py
edge_intents:
  - from: "docs/notes.md"
    to: "src/app.py:main"
    type: parameter_propagation
    when: "docs enabled"
  - from: "config/settings.yaml"
    to: "src/app.py:main"
    type: control_flow_gate
    when: "enabled == true"
  - from: "config/settings.yaml"
    to: "src/app.py:main"
    type: control_flow_gate
    when: "enabled == true"
YAML
)
duplicate_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "$duplicate_payload")"
VALIDATE_OUTPUT="$duplicate_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'ready'
assert data['node_count'] == 1
assert data['edge_count'] == 1
assert data['meta']['duplicate_existing_node_count'] == 1
assert data['meta']['duplicate_existing_edge_count'] == 1
assert data['meta']['duplicate_batch_node_count'] == 1
assert data['meta']['duplicate_batch_edge_count'] == 1
assert len(data['duplicates']['existing']) == 2
assert len(data['duplicates']['batch']) == 2
PY

empty_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "")"
VALIDATE_OUTPUT="$empty_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'skip'
assert data['reason'] == 'no_candidate_intents'
assert data['node_intents'] == []
assert data['edge_intents'] == []
PY

echo "PASS: nexus validate impact intents behavior"
