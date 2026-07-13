#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$TESTS_DIR/lib/nexus-test-helpers.sh"

setup_nexus_test_repo
run_nexus_install "$NEXUS_PROJECT" >/dev/null
run_sync_routes "$NEXUS_PROJECT" >/dev/null

cat > "$NEXUS_PROJECT/.nexus/impact-notes.yaml" <<'YAML'
version: 1
pending:
  - note_id: "N-001"
    text: >
      config/settings.yaml controls whether src/app.py main runs when enabled is true.
    route_hint: src.app_py
    file_hints:
      - config/settings.yaml
      - src/app.py
    symbol_hints:
      - main
    tags:
      - control
transformed:
  - note_id: "N-000"
    hint_ids:
      - H-001
    date: "2026-04-23"
YAML

prepared_output="$(run_prepare_impact_notes "$NEXUS_PROJECT")"
PREPARE_OUTPUT="$prepared_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['PREPARE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['PREPARE_OUTPUT']) or {}
assert data['status'] == 'ready'
assert data['notes'][0]['note_id'] == 'N-001'
assert data['notes'][0]['file_hints'] == ['config/settings.yaml', 'src/app.py']
assert data['notes'][0]['symbol_hints'] == ['main']
PY

candidate_payload=$(cat <<'YAML'
node_intents:
  - note_id: N-001
    target: src/app.py:main
    kind: route_binding
    route_ref: src.app_py
  - note_id: N-001
    target: config/settings.yaml
    kind: file_as_node
    route_ref: config.settings_yaml
    role: config_file
edge_intents:
  - note_id: N-001
    from: config/settings.yaml
    to: src/app.py:main
    type: control_flow_gate
    when: enabled == true
YAML
)

validated_output="$(run_validate_impact_intents "$NEXUS_PROJECT" "$candidate_payload")"
VALIDATE_OUTPUT="$validated_output" python3 - <<'PY'
import os
try:
    from ruamel.yaml import YAML  # type: ignore
    data = YAML(typ='safe').load(os.environ['VALIDATE_OUTPUT']) or {}
except Exception:
    import yaml  # type: ignore
    data = yaml.safe_load(os.environ['VALIDATE_OUTPUT']) or {}
assert data['status'] == 'ready'
assert data['node_count'] == 2
assert data['edge_count'] == 1
assert data['node_intents'][0]['note_id'] == 'N-001'
PY

run_apply_validated_intents "$NEXUS_PROJECT" "$validated_output" >/dev/null
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact.intent.yaml" 'data["version"] == 1 and len(data["node_intents"]) == 2 and len(data["edge_intents"]) == 1 and all("note_id" not in item for item in data["node_intents"] + data["edge_intents"]) and any(item["target"] == "src/app.py:main" and item["kind"] == "route_binding" for item in data["node_intents"]) and any(item["target"] == "config/settings.yaml" and item["role"] == "config_file" for item in data["node_intents"]) and data["edge_intents"][0]["when"] == "enabled == true"' "step b applied validated intents"
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact-notes.yaml" 'data["version"] == 1 and data["pending"] == [] and len(data["transformed"]) == 2 and data["transformed"][1]["note_id"] == "N-001" and data["transformed"][1]["hint_ids"] == ["H-002", "H-003", "H-004"]' "step b transformed note bookkeeping"

run_sync_impact_graph "$NEXUS_PROJECT" >/dev/null
run_sync_route_index "$NEXUS_PROJECT" >/dev/null
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact.yaml" 'len(data["nodes"]) == 2 and len(data["edges"]) == 1 and any(node["id"] == "src/app.py:main" and node["route_ref"] == "src.app_py" for node in data["nodes"]) and any(node["id"] == "config/settings.yaml" and node["route_ref"] == "config.settings_yaml" for node in data["nodes"]) and data["edges"][0]["from"] == "config/settings.yaml" and data["edges"][0]["to"] == "src/app.py:main"' "step b compiled graph"
assert_json_expr "$NEXUS_PROJECT/.nexus/route-index.json" '.graph_node_to_route_id["src/app.py:main"] == "src.app_py" and .graph_node_to_route_id["config/settings.yaml"] == "config.settings_yaml"'

echo "PASS: nexus step b envelope behavior"
