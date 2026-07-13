# Asterism Explicit Invocation And Validation Design

## Purpose

Strengthen Asterism's existing skill package controls without replacing its
content-first layout, `skills` CLI distribution, structural validator, Nexus
behavioral tests, CI, licensing, or third-party notices.

This change makes every maintained skill explicitly user-invoked in both Codex
and Claude Code, adds Codex-facing skill metadata, removes redundant trigger
language from human-facing descriptions, and expands repository validation.

## Current Repository State

Asterism currently maintains these six public skills:

- `brainstorming`
- `intake`
- `nexus`
- `phase-frames`
- `simplify`
- `writing-plans`

The canonical public catalog is the dynamic set of direct children under
`skills/` that contain `SKILL.md`. The repository must not restore or retain a
fixed seven-skill assertion. `writing-skills` was intentionally removed and is
not part of this design.

Existing controls remain in place:

- direct-child skill packaging
- local structural validator and validator tests
- local Markdown link validation
- `skills` CLI discovery comparison in CI
- Nexus behavioral tests
- MIT licensing and third-party notices
- reviewed, manually maintained adaptations of upstream skills

## Distribution Boundaries

Asterism remains a skill repository installed through the external `skills`
CLI. It continues to support installation for Codex and Claude Code through
that CLI.

The repository does not become a Claude plugin and must not add
`.claude-plugin/plugin.json`. It also does not add a Codex plugin manifest as
part of this change. Plugin packaging can be designed later if Asterism adopts
a plugin marketplace as a separate distribution channel.

Every distributable skill remains at:

```text
skills/<name>/SKILL.md
```

Drafts, experiments, deprecated skills, examples, and fixtures must not use a
discoverable `SKILL.md` filename anywhere else in the repository. Such work
belongs on another branch, in another repository, or under a non-discoverable
filename.

## Explicit Invocation Contract

Every public `SKILL.md` must include this Claude Code frontmatter field:

```yaml
disable-model-invocation: true
```

Every public skill must also contain `agents/openai.yaml` with this structure:

```yaml
interface:
  display_name: "Human-facing skill name"
  short_description: "Concise description between 25 and 64 characters"
  default_prompt: "Use $skill-name to perform the skill's workflow."

policy:
  allow_implicit_invocation: false
```

The `short_description` length is an Asterism interface convention, not a
claim about a mandatory Codex platform limit.

The default prompt must be one sentence and contain the exact invocation token
for its directory, such as `$brainstorming` or `$phase-frames`. The Codex and
Claude policies must agree: implicit/model invocation is disabled in both.

Once these machine-readable policies exist, each frontmatter `description`
must become a concise human-facing summary. It must not repeat `LOAD ONLY`,
`Do not auto-load`, or equivalent trigger-policy wording. A skill body may
still describe explicit invocation where that fact is part of its workflow or
authorization boundary.

## Skill Interface Metadata

Use these initial interface values:

| Skill | `display_name` | `short_description` | `default_prompt` |
| --- | --- | --- | --- |
| `brainstorming` | `Brainstorming` | `Explore intent and shape an approved design` | `Use $brainstorming to explore this idea and produce an approved design.` |
| `intake` | `Intake` | `Turn a rough request into a stronger prompt` | `Use $intake to refine this request into a clear downstream prompt.` |
| `nexus` | `Nexus` | `Maintain repository routes and impact mappings` | `Use $nexus to scaffold or synchronize this repository's route and impact map.` |
| `phase-frames` | `Phase Frames` | `Frame an approved spec into ordered phases` | `Use $phase-frames to add ordered implementation phases to this approved specification.` |
| `simplify` | `Simplify` | `Review changed code and fix quality issues` | `Use $simplify to review the changed code and fix justified quality issues.` |
| `writing-plans` | `Writing Plans` | `Turn an approved spec into an execution plan` | `Use $writing-plans to turn this approved specification into an implementation plan.` |

These values are maintained beside each skill rather than in a central
generated catalog.

## Documentation And Authorization Neutrality

The `superpowers` intermediate directory remains part of Asterism's document
convention. Do not flatten it away.

Default artifact paths are:

```text
docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md
```

User-specified output paths continue to override these defaults.

Skills may inspect Git history when it helps understand a repository, but they
must not create commits merely because a workflow reached a milestone. Any
commit, amend, tag, push, release, or other repository mutation requires
explicit user authorization. Update `brainstorming` and `writing-plans` so
their required terminal states are saved artifacts and successful validation,
not automatic commits.

Claude-specific installation assumptions must not leak into cross-agent skill
procedures. In particular, the helper at
`skills/simplify/references/extract-builtin-prompt.py` must not hard-code
`/usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js`. If retained,
the helper must accept the bundle path as an argument or discover it from an
explicit environment/tool lookup and fail with an actionable message.

## Validator Architecture

Replace the hand-written frontmatter scalar parser with the maintained `yaml`
package. Add a minimal `package.json` and lockfile so local and CI parsing is
reproducible. The validator remains read-only and must not repair files,
generate catalogs, or call network services.

The canonical catalog is computed from direct `skills/*/SKILL.md` entries. The
validator must dynamically verify the following.

### Skill Placement And Identity

- Every direct child directory of `skills/` contains `SKILL.md`.
- Every repository `SKILL.md`, excluding `.git/` and dependency directories,
  is exactly one canonical `skills/<name>/SKILL.md`.
- No nested, draft, deprecated, experimental, or off-catalog `SKILL.md` exists.
- Frontmatter is valid YAML.
- `name` and `description` are non-empty strings.
- `name` uses the supported skill-name format.
- The declared name equals the directory name.
- Declared names are unique.
- `disable-model-invocation` is exactly `true`.
- Descriptions do not contain the retired trigger-policy wording.

### Codex Metadata

- Every skill contains exactly one `agents/openai.yaml`.
- The metadata file is valid YAML.
- `interface.display_name` is a non-empty string.
- `interface.short_description` is a string between 25 and 64 characters.
- `interface.default_prompt` is a non-empty, one-sentence string.
- The default prompt contains the exact `$<directory-name>` token.
- `policy.allow_implicit_invocation` is exactly `false`.
- No unknown placement of `agents/openai.yaml` creates ambiguous metadata.

### Catalog Agreement

- The canonical direct-child set equals the skill list in `README.md`.
- The validator does not hard-code the six current names.
- The validator does not call `npx skills` or any other network-dependent
  command.
- CI continues to compare `npx skills@latest add . --list` with the canonical
  direct-child set as an external integration check.
- No plugin-manifest comparison is required because this design adds no plugin
  distribution channel.

### References And Published Paths

- Every relative Markdown link and image target resolves to an existing path.
- Reference-style Markdown links are validated in addition to inline links.
- Local asset paths declared in `agents/openai.yaml` resolve relative to that
  metadata file.
- Referenced companion scripts, templates, and documents exist inside the
  owning skill directory.
- Published skill files must not contain machine-specific absolute paths such
  as `/Users/<name>/...`, `/home/<name>/...`, or Windows drive-rooted user
  paths.
- Generic runtime paths such as `/tmp/...`, documented repository-root
  placeholders, URLs, and shebangs are not treated as machine-specific paths.

## README Contract

Keep `README.md` focused on using and contributing skills. Its included-skill
list must contain exactly one entry for each canonical direct-child skill and
no other skill.

The README continues to document:

- interactive `skills` CLI installation
- optional global installation for Codex and Claude Code
- the CLI update command
- the direct-child public-skill convention
- local structural and behavioral validation commands

The README must not claim that Asterism is distributed as a Claude plugin.

## Tests And CI

Extend `scripts/validate-skills.test.mjs` with focused fixtures for every new
validator contract. At minimum, cover:

- valid explicit-invocation metadata
- malformed frontmatter YAML
- invalid skill names and directory/name mismatch
- duplicate names
- missing or duplicate `agents/openai.yaml`
- missing interface fields
- short descriptions below and above the allowed bounds
- incorrect or missing `$skill-name` token
- inconsistent invocation policies
- unexpected `SKILL.md` outside the direct-child catalog
- README/catalog mismatch
- broken inline, reference-style, image, and declared-asset paths
- machine-specific absolute paths

Update CI to run:

1. `npm ci`
2. validator unit tests
3. repository structural validation
4. `skills` CLI discovery comparison
5. the transported Nexus behavioral test suite

All validation must pass before publishing a tag.

## Release And Update Policy

Asterism continues to use reviewed changes rather than unattended
synchronization from mutable upstream branches. The existing third-party notice
remains authoritative for locally adapted upstream skills.

Adopt annotated semantic-version tags for reviewed Asterism releases. The first
tagged release after this work is `v0.1.0`. Tagging is manual and requires
explicit user authorization after:

- all local structural and behavioral tests pass
- the accepted commit is pushed to `main`
- CI succeeds for that exact commit
- the public skill catalog is reviewed

Tags improve reproducibility and auditability; they do not replace the current
`skills` CLI update behavior or create unattended release automation.

## Files Expected To Change

- Create: `package.json`
- Create: `package-lock.json`
- Create: `skills/brainstorming/agents/openai.yaml`
- Create: `skills/intake/agents/openai.yaml`
- Create: `skills/nexus/agents/openai.yaml`
- Create: `skills/phase-frames/agents/openai.yaml`
- Create: `skills/simplify/agents/openai.yaml`
- Create: `skills/writing-plans/agents/openai.yaml`
- Modify: all six `skills/*/SKILL.md` files
- Modify: `skills/simplify/references/extract-builtin-prompt.py`
- Modify: `scripts/validate-skills.mjs`
- Modify: `scripts/validate-skills.test.mjs`
- Modify: `.github/workflows/validate.yml`
- Modify: `README.md` only where its catalog or validation commands require it

Do not create `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, a
generated skill index, an install map, a custom installer, or synchronization
automation.

## Acceptance Criteria

The change is complete when:

- exactly six public direct-child skills remain discoverable
- all six skills require explicit invocation in Codex and Claude Code metadata
- all six descriptions are concise and free of redundant trigger-policy text
- each skill has valid, matching `agents/openai.yaml`
- the validator uses the real YAML parser and covers every new contract
- direct children, README, and `skills` CLI discovery agree exactly
- no off-catalog `SKILL.md` exists
- all referenced local files and assets exist
- no published skill contains a machine-specific absolute path
- `docs/superpowers/specs/` and `docs/superpowers/plans/` remain the defaults
- no skill automatically commits, tags, pushes, or publishes
- validator tests, repository validation, CLI discovery, and Nexus tests pass
- CI succeeds for the accepted commit
- an annotated `v0.1.0` tag is created only with explicit authorization
- no Claude or Codex plugin manifest is added

## Non-Goals

This change does not:

- restore `writing-skills`
- increase the catalog back to seven skills
- distribute Asterism through the Claude plugin system
- distribute Asterism through the Codex plugin system
- remove the `superpowers` intermediate documentation directory
- flatten specs to `docs/specs/` or plans to `docs/plans/`
- add automatic upstream synchronization
- add unattended tagging or release automation
- change Nexus route-and-impact behavior
- redesign interactions among the six skills
