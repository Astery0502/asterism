---
name: nexus
description: >
  Scaffold or sync the .nexus/ route-and-impact system.
  LOAD ONLY when the user explicitly invokes /nexus. Do not auto-load for any other reason.
---

# Nexus

## Goal

Nexus maintains a local `.nexus/` route-and-impact map for a repository. It can scaffold the map, sync route discovery from the current file tree, transform human-authored impact notes into validated structured intents, and compile the final impact graph and route index.

The central idea is evidence-preserving translation: user notes stay free-form, while the sync workflow admits only exact, validated structure into `.nexus/impact.intent.yaml`. If a note is not specific enough to translate without guessing, leave it pending and ask one clarifying question after the apply step.

## Terms

- Route: a file node discovered into `.nexus/routes.yaml` according to `.nexus/routes_rules.yaml`.
- Route id: the exact `id` field for a route in `.nexus/routes.yaml`.
- Impact note: a pending entry in `.nexus/impact-notes.yaml` written by the user in plain language.
- Candidate intent: a temporary YAML proposal derived from prepared notes. It exists only long enough to pass through `validate_impact_intents.py`.
- Validated intent: a candidate returned by the validator as accepted. Only these may be applied.
- Compiled graph: `.nexus/impact.yaml`, generated from `.nexus/impact.intent.yaml`; never edit it manually.

## Exactness rule

Treat Step B as a precise translation task, not a summarization task.

Use only evidence from:

- the prepared note fields returned by `prepare_impact_notes.py`
- `.nexus/routes.yaml`
- `.nexus/impact-rules.yaml`
- existing `.nexus/impact.intent.yaml`
- repository files that you read to confirm a named symbol or file path

An intent is exact enough only when every required field can be tied to explicit evidence:

- `target`, `from`, and `to` must be canonical repo-relative file paths, optionally with `:symbol` only when the note or `symbol_hints` names that symbol and the symbol spelling is confirmed from the file.
- `kind` and `type` must be exact rule ids from `.nexus/impact-rules.yaml`.
- `route_ref` must be an exact route id from `.nexus/routes.yaml`; otherwise omit it.
- `role` and `when` must preserve the user's meaning in the note without broadening it.

When exactness is missing, produce no candidate for that note. Leaving a note in `pending` is correct; inventing structure is not.

Run the status check first:

```bash
python <skill_dir>/scripts/nexus_status.py --target <repo_root>
```

Read the `STATE` line and branch:

- `STATE: fresh` — `.nexus/` does not exist → go to **Mode 1 — Setup**
- `STATE: partial` — `.nexus/` exists but some scaffold files are missing → go to **Mode 1 — Setup**
- `STATE: complete` — all scaffold files present → go to **Mode 2 — Sync**

## Scaffold contents

- `.nexus/routes.yaml`
- `.nexus/routes_rules.yaml`
- `.nexus/impact-notes.yaml`
- `.nexus/impact.intent.yaml`
- `.nexus/impact.yaml`
- `.nexus/impact-rules.yaml`
- `.nexus/route-index.json`
- `.nexus/scripts/graph_helpers.py`
- `.nexus/scripts/prepare_impact_notes.py`
- `.nexus/scripts/validate_impact_intents.py`
- `.nexus/scripts/apply_validated_intents.py`
- `.nexus/scripts/sync_routes.py`
- `.nexus/scripts/sync_route_index.py`
- `.nexus/scripts/sync_impact_graph.py`

## Mode 1 — Setup

If `STATE: partial`, the status script already printed `WILL_CREATE` /
`WILL_SKIP` lines — show these to the user and ask for confirmation before
proceeding.

Run:

```bash
python <skill_dir>/scripts/nexus_install.py --target <repo_root>
# add --confirm if STATE was partial and user confirmed
```

`nexus_install.py` outputs `CREATED:` / `SKIPPED:` per file, then `DONE`.

Tell the user the scaffold is ready. No further action required at setup time;
they can configure `.nexus/routes_rules.yaml` and write into
`.nexus/impact-notes.yaml` at their own pace, then invoke the skill again to
sync.

## Mode 2 — Sync

All commands run from `<repo_root>`. Run unconditionally in this order:

### A — Sync route tree

```bash
python .nexus/scripts/sync_routes.py
```

### B — Transform notes into intents

First run:

```bash
python .nexus/scripts/prepare_impact_notes.py
```

Read the YAML result and branch:

- `status: error` — stop Step B and report `errors`
- `status: skip` — skip Step B and continue to Step C
- `status: ready` — continue Step B using only the returned `notes`

When `status: ready`, derive candidate `node_intents` and `edge_intents` from the returned notes. Derive each candidate from one note at a time; do not merge two notes to manufacture a stronger claim. A single note may produce multiple intents only when each intent is directly supported by that note's `text`, `route_hint`, `file_hints`, `symbol_hints`, or `tags`.

Translation checklist for each note:

1. Identify explicit file or symbol references from the prepared note.
2. Confirm referenced files against `.nexus/routes.yaml` or by reading the repository file when a symbol must be checked.
3. Select the narrowest matching rule id from `.nexus/impact-rules.yaml`.
4. Build only candidates whose required fields pass the exactness rule above.
5. If multiple interpretations remain plausible, leave the note unresolved instead of choosing one.

Candidate payload shape:

```yaml
node_intents:
  - note_id: N-001
    target: src/app.py:main
    kind: route_binding
    route_ref: src.app_py
    role: optional_role
edge_intents:
  - note_id: N-001
    from: config/settings.yaml
    to: src/app.py:main
    type: control_flow_gate
    when: enabled == true
```

Omit optional fields when they are not clearly supported by the note. If no candidate intents can be derived, use empty lists for both top-level fields. The validator accepts only `node_intents` and `edge_intents`; unresolved notes are represented by omission, not by a third YAML field.

The agent is responsible for semantic interpretation only:
- classify each note as node intent, edge intent, or unresolved
- resolve canonical repo-relative ids for `target`, `from`, and `to`
- choose valid rule ids from `.nexus/impact-rules.yaml`
- attach the originating `note_id` to every candidate intent derived from a note
- optionally set `route_ref` only when it exactly matches an existing route id
- optionally set `role` or `when` only when the note clearly supplies that meaning

Do not:
- infer targets, rules, routes, or conditions from project conventions alone
- use a symbol name in `target` or `to` until the spelling has been confirmed
- rewrite `.nexus/impact-notes.yaml` during candidate derivation
- append raw candidate intents directly to `.nexus/impact.intent.yaml`

Before any append, pass the candidate batch to the validator through stdin:

```bash
python .nexus/scripts/validate_impact_intents.py < /tmp/nexus-candidate-intents.yaml
```

`/tmp/nexus-candidate-intents.yaml` is a temporary file containing the candidate payload above. Do not write candidate intents into `.nexus/impact.intent.yaml` directly.

This helper is the intent admission gate. It validates candidate intents against:
- `.nexus/impact-rules.yaml`
- `.nexus/routes.yaml`
- existing `.nexus/impact.intent.yaml`

Read the YAML result and branch:

- `status: error` — stop Step B and report `errors`
- `status: skip` — continue to the apply helper so unresolved notes stay pending and no append occurs
- `status: ready` — continue to the apply helper with the returned validated `node_intents` and `edge_intents`

Validation constraints:

1. Required fields must exist:
   - node intent: `target`, `kind`
   - edge intent: `from`, `to`, `type`

2. Canonical normalization is allowed only for light cleanup:
   - trim strings
   - strip leading `./`
   - normalize path separators
   - drop malformed optional fields with warnings

3. Rule validation:
   - `node_intents.kind` must use a rule id with scope `node` or `node_edge`
   - `edge_intents.type` must use a rule id with scope `edge` or `node_edge`

4. Route validation:
   - if `route_ref` is present, it must exist in `.nexus/routes.yaml`
   - if `route_ref` is absent, leave it absent and let later compilation infer it when possible

5. Duplicate policy:
   - existing node duplicate: same `target`, `kind`, and `route_ref`
   - existing edge duplicate: same `from`, `to`, `type`, and `when`
   - batch duplicates use the same keys
   - duplicates are filtered, not appended, and not treated as fatal errors
   - `note_id` is Step B provenance only and is not part of duplicate keys or persisted intents

Then pass the full validator output to the apply helper through stdin, even when validation returned `status: skip`:

```bash
python .nexus/scripts/apply_validated_intents.py < /tmp/nexus-validated-intents.yaml
```

`/tmp/nexus-validated-intents.yaml` is a temporary file containing the complete YAML output from `validate_impact_intents.py`. The apply helper uses that status and payload to append validated intents and update note bookkeeping safely.

Apply behavior:

- append only the helper-returned validated node intents into `.nexus/impact.intent.yaml` `node_intents`
- append only the helper-returned validated edge intents into `.nexus/impact.intent.yaml` `edge_intents`
- preserve existing `node_intents`, `edge_intents`, and `aliases`
- strip `note_id` before persisting to `.nexus/impact.intent.yaml`
- do not append rejected or duplicate candidates

Notes bookkeeping:

- move a note from `.nexus/impact-notes.yaml` `pending` to `transformed` only if at least one validated intent derived from that note was appended
- record:
  - `hint_ids`
  - `date`
- generate `hint_ids` deterministically as the next `H-###` values in append order
- leave unresolved notes in `pending`
- leave duplicate-only notes in `pending`

After apply, if any notes remain unresolved in `pending`, report them all at once with a single clarifying question. Do not interrupt per entry.


### C — Compile impact graph

```bash
python .nexus/scripts/sync_impact_graph.py
```

### D — Build route index

```bash
python .nexus/scripts/sync_route_index.py
```

D joins routes and impact; always run it last. On the very first sync,
`route-index.json` is still the empty template when C runs — C will emit
`confidence: low` warnings for unresolved route refs. This is expected;
subsequent syncs use the index built by the previous D.

## Notes

- `routes_rules.yaml` controls what files become route nodes; edit before
  first sync if the defaults don't fit the project.
- `impact-notes.yaml` is the user's free-form authoring surface.
- `impact.intent.yaml` is agent-written from notes; never edit manually.
- `impact.yaml` is compiled output; never edit manually.
- `route-index.json` is a cache built from routes + impact.
