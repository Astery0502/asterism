# asterism

A small, content-first collection of agent skills installed with the [`skills`](https://skills.sh/) CLI.

## Included skills

- **brainstorming** - Explores user intent, requirements, and design before implementation.
- **intake** - Refines an explicitly submitted rough or under-structured request before downstream work.
- **nexus** - Scaffolds or synchronizes a repository's `.nexus/` route-and-impact system.
- **phase-frames** - Turns an approved specification into fixed, ordered implementation phase frames.
- **simplify** - Reviews changed code for reuse, quality, and efficiency, then fixes issues found.
- **writing-plans** - Produces a comprehensive, task-by-task implementation plan from an approved specification.
- **writing-skills** - Creates, edits, and verifies reusable agent skills with a test-driven workflow.

## Install

Choose skills and installation targets interactively:

```bash
npx skills@latest add astery/asterism
```

To install every skill globally for Codex and Claude Code without prompts:

```bash
npx skills@latest add astery/asterism \
  --global \
  --skill '*' \
  --agent codex claude-code \
  --yes
```

Update globally installed skills through the CLI:

```bash
npx skills@latest update --global
```

## Contributing

Each public skill is one direct child of `skills/` and must contain a `SKILL.md`. Keep a skill's scripts, references, templates, fixtures, and tests inside that skill directory.

Run local validation from the repository root:

```bash
node --test scripts/validate-skills.test.mjs
node scripts/validate-skills.mjs
for test_file in skills/nexus/tests/test-*.sh; do bash "$test_file"; done
```
