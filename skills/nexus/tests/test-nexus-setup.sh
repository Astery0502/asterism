#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$TESTS_DIR/lib/nexus-test-helpers.sh"

setup_nexus_test_repo

assert_nexus_scaffold_state "$NEXUS_PROJECT" fresh

mkdir -p "$NEXUS_PROJECT/.nexus"
printf 'unrelated\n' > "$NEXUS_PROJECT/.nexus/local-note.txt"
assert_nexus_scaffold_state "$NEXUS_PROJECT" partial
run_nexus_install "$NEXUS_PROJECT" >/dev/null
assert_nexus_scaffold_state "$NEXUS_PROJECT" partial
assert_file_contains "$NEXUS_PROJECT/.nexus/local-note.txt" "unrelated"
run_nexus_install "$NEXUS_PROJECT" --confirm >/dev/null
assert_nexus_scaffold_state "$NEXUS_PROJECT" complete
assert_file_contains "$NEXUS_PROJECT/.nexus/local-note.txt" "unrelated"
rm -rf "$NEXUS_PROJECT/.nexus"

run_nexus_install "$NEXUS_PROJECT" >/dev/null
assert_nexus_scaffold_state "$NEXUS_PROJECT" complete
assert_nexus_template_installed "$NEXUS_PROJECT"

printf 'preserve me\n' > "$NEXUS_PROJECT/.nexus/routes_rules.yaml"
rm "$NEXUS_PROJECT/.nexus/impact.yaml"

assert_nexus_scaffold_state "$NEXUS_PROJECT" partial

run_nexus_install "$NEXUS_PROJECT" >/dev/null
assert_nexus_scaffold_state "$NEXUS_PROJECT" partial
assert_file_missing "$NEXUS_PROJECT/.nexus/impact.yaml"
assert_file_contains "$NEXUS_PROJECT/.nexus/routes_rules.yaml" "preserve me"

run_nexus_install "$NEXUS_PROJECT" --confirm >/dev/null
assert_nexus_scaffold_state "$NEXUS_PROJECT" complete
assert_file_contains "$NEXUS_PROJECT/.nexus/routes_rules.yaml" "preserve me"
assert_yaml_file_expr "$NEXUS_PROJECT/.nexus/impact.yaml" 'data["version"] == 1 and data["graph_meta"]["route_index_ref"] == ".nexus/route-index.json" and data["nodes"] == [] and data["edges"] == []' "restored impact scaffold"
assert_file_contains "$NEXUS_PROJECT/.nexus/scripts/prepare_impact_notes.py" "#!/usr/bin/env python3"

touch "$TEST_REPO/skills/nexus/template/.nexus/.DS_Store"
assert_nexus_scaffold_state "$NEXUS_PROJECT" complete
rm "$TEST_REPO/skills/nexus/template/.nexus/.DS_Store"

echo "PASS: nexus setup behavior"
