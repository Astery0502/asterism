#!/usr/bin/env bash
set -euo pipefail

NEXUS_TEST_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEXUS_TESTS_DIR="$(cd "$NEXUS_TEST_HELPERS_DIR/.." && pwd)"
REPO_ROOT="$(cd "$NEXUS_TESTS_DIR/../../.." && pwd)"

export LC_ALL=C
export LANG=C

TMP_DIR=""
TEST_REPO=""

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

test_cleanup() {
  [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]] && rm -rf "$TMP_DIR"
}

test_setup_repo() {
  TMP_DIR="$(mktemp -d)"
  TEST_REPO="$TMP_DIR/repo"
  trap test_cleanup EXIT

  mkdir -p "$TEST_REPO"
  (
    cd "$REPO_ROOT"
    tar --exclude='./.git' -cf - .
  ) | (
    cd "$TEST_REPO"
    tar -xf -
  )

  cd "$TEST_REPO"
}

assert_file_missing() {
  local path="$1"
  [[ ! -e "$path" ]] || fail "expected path to be absent: $path"
}

assert_file_contains() {
  local path="$1"
  local needle="$2"
  [[ -f "$path" ]] || fail "expected file to exist before checking contents: $path"
  grep -Fq "$needle" "$path" || fail "expected $path to contain: $needle"
}

assert_json_expr() {
  local file="$1"
  local expr="$2"
  jq -e "$expr" "$file" >/dev/null || fail "json assertion failed: $file :: $expr"
}

NEXUS_FIXTURE_SOURCE=""
NEXUS_SCRIPT_DIR=""
NEXUS_TEMPLATE_ROOT=""
NEXUS_PROJECT=""

setup_nexus_test_repo() {
  test_setup_repo
  NEXUS_FIXTURE_SOURCE="$TEST_REPO/skills/nexus/tests/fixtures/project"
  NEXUS_SCRIPT_DIR="$TEST_REPO/skills/nexus/scripts"
  NEXUS_TEMPLATE_ROOT="$TEST_REPO/skills/nexus/template/.nexus"
  NEXUS_PROJECT="$TMP_DIR/nexus-project"

  mkdir -p "$NEXUS_PROJECT"
  cp -R "$NEXUS_FIXTURE_SOURCE"/. "$NEXUS_PROJECT"/
  (
    cd "$NEXUS_PROJECT"
    git init -q
  )
}

capture_file_hash() {
  local path="$1"
  local digest

  [[ -f "$path" ]] || fail "expected file to exist before hashing: $path"
  digest="$(shasum -a 256 "$path")"
  printf '%s\n' "${digest%% *}"
}

assert_file_hash_matches() {
  local path="$1"
  local expected_hash="$2"
  local actual_hash

  actual_hash="$(capture_file_hash "$path")"
  [[ "$actual_hash" == "$expected_hash" ]] || fail "expected file hash to match for $path"
}


assert_yaml_file_expr() {
  local path="$1"
  local expr="$2"
  local label="${3:-$expr}"

  [[ -f "$path" ]] || fail "expected YAML file to exist before checking contents: $path"

  if ! ASSERT_YAML_PATH="$path" ASSERT_EXPR="$expr" ASSERT_LABEL="$label" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path


def load_yaml_path(path: Path):
    text = path.read_text(encoding='utf-8')
    try:
        from ruamel.yaml import YAML  # type: ignore

        yaml = YAML(typ='safe')
        return yaml.load(text) or {}
    except Exception:
        pass
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except Exception as exc:
        raise RuntimeError('Need ruamel.yaml or PyYAML to load YAML file.') from exc


path = Path(os.environ['ASSERT_YAML_PATH'])
expr = os.environ['ASSERT_EXPR']
label = os.environ['ASSERT_LABEL']
data = load_yaml_path(path)
namespace = {
    'data': data,
    'len': len,
    'any': any,
    'all': all,
    'sum': sum,
    'sorted': sorted,
    'set': set,
}
result = eval(expr, {'__builtins__': {}}, namespace)
if not result:
    print(f'YAML file assertion failed: {label}', file=sys.stderr)
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)
PY
  then
    fail "yaml file assertion failed: $label"
  fi
}

assert_nexus_template_installed() {
  local target_root="$1"

  if ! TEMPLATE_ROOT="$NEXUS_TEMPLATE_ROOT" TARGET_ROOT="$target_root" python3 - <<'PY'
import os
from pathlib import Path


def expected_text(template_path: Path) -> str:
    text = template_path.read_text(encoding='utf-8')
    if template_path.suffix == '.py' and not text.startswith('#!'):
        return '#!/usr/bin/env python3\n' + text
    return text


template_root = Path(os.environ['TEMPLATE_ROOT'])
target_root = Path(os.environ['TARGET_ROOT'])
problems = []
for template_path in sorted(template_root.rglob('*')):
    if not template_path.is_file() or template_path.name == '.DS_Store':
        continue
    rel = template_path.relative_to(template_root.parent)
    installed_path = target_root / rel
    if not installed_path.is_file():
        problems.append(f'missing file: {rel.as_posix()}')
        continue
    actual = installed_path.read_text(encoding='utf-8')
    expected = expected_text(template_path)
    if actual != expected:
        problems.append(f'content mismatch: {rel.as_posix()}')
if problems:
    for problem in problems:
        print(problem)
    raise SystemExit(1)
PY
  then
    fail "expected installed .nexus scaffold to match template contents"
  fi
}

assert_nexus_scaffold_state() {
  local target_root="$1"
  local expected_state="$2"

  if ! TEMPLATE_ROOT="$NEXUS_TEMPLATE_ROOT" TARGET_ROOT="$target_root" EXPECTED_STATE="$expected_state" python3 - <<'PY'
import os
from pathlib import Path


def collect_template_files(template_dir: Path) -> list[Path]:
    return sorted(path for path in template_dir.rglob('*') if path.is_file() and path.name != '.DS_Store')


def classify(template_root: Path, target_root: Path) -> str:
    existing = []
    missing = []
    for template_path in collect_template_files(template_root):
        rel = template_path.relative_to(template_root.parent)
        dest = target_root / rel
        (existing if dest.exists() else missing).append(template_path)
    if not existing and not (target_root / '.nexus').is_dir():
        return 'fresh'
    if not missing:
        return 'complete'
    return 'partial'


template_root = Path(os.environ['TEMPLATE_ROOT'])
target_root = Path(os.environ['TARGET_ROOT'])
expected_state = os.environ['EXPECTED_STATE']
actual_state = classify(template_root, target_root)
if actual_state != expected_state:
    raise SystemExit(f'expected nexus scaffold state {expected_state}, got {actual_state}')
PY
  then
    fail "nexus scaffold state mismatch for $target_root"
  fi
}

run_nexus_install() {
  local target="$1"
  shift
  python3 "$NEXUS_SCRIPT_DIR/nexus_install.py" --target "$target" "$@"
}

run_prepare_impact_notes() {
  (
    cd "$1"
    python3 .nexus/scripts/prepare_impact_notes.py
  )
}

run_validate_impact_intents() {
  local target="$1"
  local payload="$2"
  (
    cd "$target"
    printf '%s' "$payload" | python3 .nexus/scripts/validate_impact_intents.py
  )
}

run_apply_validated_intents() {
  local target="$1"
  local payload="$2"
  (
    cd "$target"
    printf '%s' "$payload" | python3 .nexus/scripts/apply_validated_intents.py
  )
}

run_sync_routes() {
  (
    cd "$1"
    python3 .nexus/scripts/sync_routes.py
  )
}

run_sync_impact_graph() {
  (
    cd "$1"
    python3 .nexus/scripts/sync_impact_graph.py
  )
}

run_sync_route_index() {
  (
    cd "$1"
    python3 .nexus/scripts/sync_route_index.py
  )
}
