# asterism

A small, content-first collection of agent skills installed with the [`skills`](https://skills.sh/) CLI.

## Included skills

- **scientific-investigation-injector** - Creates durable, prototype-first infrastructure for consequential scientific investigations.
- **simplify** - Reviews changed code for reuse, quality, and efficiency, then fixes issues found.

## Install

Choose skills and installation targets interactively:

```bash
npx skills@latest add Astery0502/asterism
```

To install every skill globally for Codex and Claude Code without prompts:

```bash
npx skills@latest add Astery0502/asterism \
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

Each public skill is one direct child of `skills/` and must contain a `SKILL.md`. Keep a skill's scripts, references, assets, fixtures, and tests inside that skill directory.

Run local validation from the repository root:

```bash
npm ci
npm test
npm run validate
```
