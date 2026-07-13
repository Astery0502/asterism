# .nexus/

Route and impact tracking scaffold for this repository.

## Files

### Hand-authored

| File | Role |
|---|---|
| `routes_rules.yaml` | Controls which files become route nodes (exclude globs, promoted file patterns). Edit before first sync if the defaults don't fit the project. |
| `impact-notes.yaml` | Free-form authoring surface. Write plain-language descriptions of nodes and relationships in `pending`. |
| `impact-rules.yaml` | Rule catalog mapping intent kinds to scopes. Extend when adding new impact categories. |

### Script-generated

These files are fully overwritten on each sync. Do not edit manually.

**`routes.yaml`** — route tree built from git-visible files.

```bash
python .nexus/scripts/sync_routes.py
```

**`impact.yaml`** — compiled impact graph built from `impact.intent.yaml`.

```bash
python .nexus/scripts/sync_impact_graph.py
```

**`route-index.json`** — cache joining routes and impact. Always run last.

```bash
python .nexus/scripts/sync_route_index.py
```

### Agent-written

| File | Role |
|---|---|
| `impact.intent.yaml` | Resolved entries from `impact-notes.yaml`. Written by the agent during sync; do not edit manually. |

## Typical sync order

Invoke `/nexus` via the agent for the full workflow. The agent will run route
sync, prepare pending notes, translate exact notes into candidate intents,
validate/apply accepted intents, compile the impact graph, and build the route
index.

If you are only refreshing generated artifacts manually after intents already
exist, run:

```bash
python .nexus/scripts/sync_routes.py
python .nexus/scripts/sync_impact_graph.py
python .nexus/scripts/sync_route_index.py
```

Do not append directly to `impact.intent.yaml`; use `/nexus` so candidates pass
through validation and note bookkeeping.
