#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$TESTS_DIR/lib/nexus-test-helpers.sh"

setup_nexus_test_repo
run_nexus_install "$NEXUS_PROJECT" >/dev/null

run_sync_routes "$NEXUS_PROJECT" >/dev/null
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/routes.yaml" 'data["version"] == 1 and any(node["path"] == "src/app.py" and node["id"] == "src.app_py" and node["kind"] == "file" for node in data["nodes"]) and any(node["path"] == "config/settings.yaml" and node["id"] == "config.settings_yaml" for node in data["nodes"]) and any(node["path"] == "docs/notes.md" and node["id"] == "docs.notes_md" for node in data["nodes"])' "synced route nodes"

validator_apply_fixture=$(cat <<'EOF'
version: 1
pending:
  - note_id: "N-001"
    text: "bind app entrypoint"
  - note_id: "N-002"
    text: "promote config file"
  - note_id: "N-003"
    text: "duplicate-only note stays pending"
transformed:
  - note_id: "N-000"
    hint_ids:
      - "H-001"
    date: "2026-04-23"
EOF
)
printf '%s\n' "$validator_apply_fixture" > "$NEXUS_PROJECT/.nexus/impact-notes.yaml"

validator_apply_intent_fixture=$(cat <<'EOF'
version: 1
node_intents:
  - target: "docs/notes.md"
    kind: file_as_node
    route_ref: docs.notes_md
    role: reference_doc
edge_intents:
  - from: "docs/notes.md"
    to: "src/app.py:main"
    type: parameter_propagation
    when: "docs enabled"
aliases:
  existing_alias:
    - alias_one
EOF
)
printf '%s\n' "$validator_apply_intent_fixture" > "$NEXUS_PROJECT/.nexus/impact.intent.yaml"

validator_apply_payload=$(cat <<'EOF'
status: ready
reason: validated_intents_ready
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
EOF
)
run_apply_validated_intents "$NEXUS_PROJECT" "$validator_apply_payload" >/dev/null
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact.intent.yaml" 'data["version"] == 1 and len(data["node_intents"]) == 3 and any(item["target"] == "docs/notes.md" and item["kind"] == "file_as_node" and item["route_ref"] == "docs.notes_md" and item["role"] == "reference_doc" for item in data["node_intents"]) and any(item["target"] == "src/app.py:main" and item["kind"] == "route_binding" and item["route_ref"] == "src.app_py" and "note_id" not in item for item in data["node_intents"]) and any(item["target"] == "config/settings.yaml" and item["kind"] == "file_as_node" and item["route_ref"] == "config.settings_yaml" and item["role"] == "config_file" and "note_id" not in item for item in data["node_intents"]) and len(data["edge_intents"]) == 2 and any(item["from"] == "config/settings.yaml" and item["to"] == "src/app.py:main" and item["type"] == "control_flow_gate" and item["when"] == "enabled == true" and "note_id" not in item for item in data["edge_intents"]) and data["aliases"] == {"existing_alias": ["alias_one"]}' "applied impact intent file"
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact-notes.yaml" 'data["version"] == 1 and [entry["note_id"] for entry in data["pending"]] == ["N-002", "N-003"] and len(data["transformed"]) == 2 and data["transformed"][0]["note_id"] == "N-000" and data["transformed"][1]["note_id"] == "N-001" and data["transformed"][1]["hint_ids"] == ["H-002", "H-003", "H-004"]' "applied impact notes file"

impact_intent_hash_before_skip="$(capture_file_hash "$NEXUS_PROJECT/.nexus/impact.intent.yaml")"
impact_notes_hash_before_skip="$(capture_file_hash "$NEXUS_PROJECT/.nexus/impact-notes.yaml")"

validator_apply_skip_payload=$(cat <<'EOF'
status: skip
reason: no_new_intents
node_intents: []
edge_intents: []
EOF
)
run_apply_validated_intents "$NEXUS_PROJECT" "$validator_apply_skip_payload" >/dev/null
assert_file_hash_matches "$NEXUS_PROJECT/.nexus/impact.intent.yaml" "$impact_intent_hash_before_skip"
assert_file_hash_matches "$NEXUS_PROJECT/.nexus/impact-notes.yaml" "$impact_notes_hash_before_skip"

run_sync_impact_graph "$NEXUS_PROJECT" >/dev/null
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact.yaml" 'data["version"] == 1 and data["graph_meta"]["compiler"] == "scripts/sync_impact_graph.py" and data["graph_meta"]["route_index_ref"] == ".nexus/route-index.json" and len(data["nodes"]) == 3 and any(node["id"] == "src/app.py:main" and node["route_ref"] == "src.app_py" and node["kind"] == "route_binding" and node["symbol"] == "main" and node["source"] == "manual" and node["confidence"] == "curated" for node in data["nodes"]) and any(node["id"] == "config/settings.yaml" and node["route_ref"] == "config.settings_yaml" and node["kind"] == "file_as_node" and node["role"] == "config_file" for node in data["nodes"]) and any(node["id"] == "docs/notes.md" and node["route_ref"] == "docs.notes_md" and node["kind"] == "file_as_node" and node["role"] == "reference_doc" for node in data["nodes"]) and len(data["edges"]) == 2 and any(edge["from"] == "config/settings.yaml" and edge["to"] == "src/app.py:main" and edge["type"] == "control_flow_gate" and edge["source"] == "merged" and edge["confidence"] == "curated" for edge in data["edges"]) and any(edge["from"] == "docs/notes.md" and edge["to"] == "src/app.py:main" and edge["type"] == "parameter_propagation" and edge["when"] == "docs enabled" for edge in data["edges"]) and any(item["route_ref"] == "src.app_py" and item["graph_nodes"] == ["src/app.py:main"] for item in data["route_index"]) and any(item["route_ref"] == "config.settings_yaml" and item["graph_nodes"] == ["config/settings.yaml"] for item in data["route_index"]) and any(item["route_ref"] == "docs.notes_md" and item["graph_nodes"] == ["docs/notes.md"] for item in data["route_index"])' "synced impact graph"

run_sync_route_index "$NEXUS_PROJECT" >/dev/null
assert_json_expr "$NEXUS_PROJECT/.nexus/route-index.json" '.version == 1 and .routes_ref == ".nexus/routes.yaml" and .impact_ref == ".nexus/impact.yaml" and .by_route_id["src.app_py"].path == "src/app.py" and .by_route_id["src.app_py"].graph_nodes == ["src/app.py:main"] and .by_route_id["config.settings_yaml"].graph_nodes == ["config/settings.yaml"] and .by_route_id["docs.notes_md"].graph_nodes == ["docs/notes.md"] and .path_to_route_id["src/app.py"] == "src.app_py" and .graph_node_to_route_id["src/app.py:main"] == "src.app_py" and .graph_node_to_route_id["config/settings.yaml"] == "config.settings_yaml"'

echo "PASS: nexus sync behavior"
