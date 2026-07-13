import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { stringify } from 'yaml';

const validator = path.resolve('scripts/validate-skills.mjs');

async function fixture(files) {
  const root = await mkdtemp(path.join(tmpdir(), 'asterism-validator-'));
  for (const [relativePath, contents] of Object.entries(files)) {
    if (contents === null) continue;
    const target = path.join(root, relativePath);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, contents);
  }
  return root;
}

function skill(name, description = `${name} workflow summary`) {
  return `---\nname: ${name}\ndescription: ${description}\ndisable-model-invocation: true\n---\n\n# ${name}\n`;
}

function metadata(name, overrides = {}) {
  const values = {
    displayName: name,
    shortDescription: `Perform the ${name} workflow with clear results`,
    defaultPrompt: `Use $${name} to perform this requested workflow.`,
    allowImplicitInvocation: false,
    ...overrides,
  };
  const interfaceFields = {
    display_name: values.displayName,
    short_description: values.shortDescription,
    default_prompt: values.defaultPrompt,
  };
  if (values.iconSmall !== undefined) interfaceFields.icon_small = values.iconSmall;
  if (values.iconLarge !== undefined) interfaceFields.icon_large = values.iconLarge;
  return stringify({
    interface: interfaceFields,
    policy: { allow_implicit_invocation: values.allowImplicitInvocation },
  });
}

function readme(names) {
  const skills = names.map((name) => `- **${name}** - ${name} workflow`).join('\n');
  return `# Fixture\n\n## Included skills\n\n${skills}\n\n## Install\n`;
}

function validFiles(names = ['alpha']) {
  return Object.fromEntries([
    ['README.md', readme(names)],
    ...names.flatMap((name) => [
      [`skills/${name}/SKILL.md`, skill(name)],
      [`skills/${name}/agents/openai.yaml`, metadata(name)],
    ]),
  ]);
}

function validate(root) {
  return spawnSync(process.execPath, [validator, root], { encoding: 'utf8' });
}

test('accepts valid skills, metadata, links, images, and reference links', async (t) => {
  const root = await fixture({
    ...validFiles(['alpha', 'beta']),
    'skills/alpha/SKILL.md': `${skill('alpha')}\n[Guide](references/guide.md)\n![Icon](assets/icon.png)\n[Details][details]\n[details]: references/details.md\n`,
    'skills/alpha/references/guide.md': '# Guide\n',
    'skills/alpha/references/details.md': '# Details\n',
    'skills/alpha/assets/icon.png': 'not a real image',
  });
  t.after(() => rm(root, { recursive: true, force: true }));
  const result = validate(root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Validated 2 skills: alpha, beta/);
});

for (const scenario of [
  {
    name: 'rejects a direct child without SKILL.md',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': null },
    error: 'skills/alpha/SKILL.md: missing SKILL.md',
  },
  {
    name: 'rejects malformed frontmatter YAML',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': '---\nname: [alpha\n---\n' },
    error: 'skills/alpha/SKILL.md: invalid YAML',
  },
  {
    name: 'rejects duplicate frontmatter keys',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': '---\nname: alpha\nname: beta\ndescription: Workflow\ndisable-model-invocation: true\n---\n' },
    error: 'skills/alpha/SKILL.md: invalid YAML',
  },
  {
    name: 'rejects non-mapping frontmatter',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': '---\nalpha\n---\n' },
    error: 'skills/alpha/SKILL.md: frontmatter must be a mapping',
  },
  {
    name: 'rejects invalid names',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': skill('bad--name') },
    error: 'skills/alpha/SKILL.md: invalid skill name "bad--name"',
  },
  {
    name: 'rejects directory-name mismatch',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': skill('other') },
    error: 'declared name "other" differs from directory "alpha"',
  },
  {
    name: 'rejects duplicate declared names',
    files: {
      ...validFiles(['alpha', 'beta']),
      'skills/beta/SKILL.md': skill('alpha'),
    },
    error: 'duplicate declared name "alpha"',
  },
  {
    name: 'rejects missing Claude invocation policy',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': '---\nname: alpha\ndescription: Alpha workflow\n---\n' },
    error: 'disable-model-invocation must be true',
  },
  {
    name: 'rejects retired trigger wording',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': skill('alpha', 'LOAD ONLY when asked') },
    error: 'description contains retired trigger-policy wording',
  },
  {
    name: 'rejects missing OpenAI metadata',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': null },
    error: 'skills/alpha/agents/openai.yaml: missing agents/openai.yaml',
  },
  {
    name: 'rejects malformed OpenAI metadata YAML',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': 'interface: [\n' },
    error: 'skills/alpha/agents/openai.yaml: invalid YAML',
  },
  {
    name: 'rejects duplicate OpenAI metadata keys',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': 'interface:\n  display_name: alpha\n  display_name: duplicate\n' },
    error: 'skills/alpha/agents/openai.yaml: invalid YAML',
  },
  {
    name: 'rejects non-mapping OpenAI metadata',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': 'alpha\n' },
    error: 'skills/alpha/agents/openai.yaml: metadata must be a mapping',
  },
  {
    name: 'rejects missing interface fields',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': 'interface: {}\npolicy:\n  allow_implicit_invocation: false\n' },
    error: 'interface.display_name must be a non-empty string',
  },
  {
    name: 'rejects non-string interface fields',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { displayName: ['alpha'] }) },
    error: 'interface.display_name must be a non-empty string',
  },
  {
    name: 'rejects short descriptions outside length bounds',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { shortDescription: 'Too short' }) },
    error: 'interface.short_description must be 25-64 characters',
  },
  {
    name: 'rejects short descriptions above the upper bound',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { shortDescription: 'A'.repeat(65) }) },
    error: 'interface.short_description must be 25-64 characters',
  },
  {
    name: 'rejects incorrect prompt token',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { defaultPrompt: 'Use $beta to perform this requested workflow.' }) },
    error: 'interface.default_prompt must contain $alpha',
  },
  {
    name: 'rejects multi-sentence default prompts',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { defaultPrompt: 'Use $alpha for this workflow. Then stop.' }) },
    error: 'interface.default_prompt must be one sentence',
  },
  {
    name: 'rejects implicit Codex invocation',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { allowImplicitInvocation: true }) },
    error: 'policy.allow_implicit_invocation must be false',
  },
  {
    name: 'rejects off-catalog SKILL.md',
    files: { ...validFiles(), 'drafts/SKILL.md': skill('draft') },
    error: 'drafts/SKILL.md: unexpected off-catalog SKILL.md',
  },
  {
    name: 'rejects off-catalog OpenAI metadata',
    files: { ...validFiles(), 'drafts/agents/openai.yaml': metadata('draft') },
    error: 'drafts/agents/openai.yaml: unexpected off-catalog agents/openai.yaml',
  },
  {
    name: 'rejects misplaced OpenAI metadata inside a skill',
    files: { ...validFiles(), 'skills/alpha/references/agents/openai.yaml': metadata('alpha') },
    error: 'skills/alpha/references/agents/openai.yaml: unexpected off-catalog agents/openai.yaml',
  },
  {
    name: 'rejects README catalog drift',
    files: { ...validFiles(), 'README.md': readme(['other']) },
    error: 'README.md: skill catalog differs',
  },
  {
    name: 'rejects a missing local link',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': `${skill('alpha')}\n[Missing](references/missing.md)\n` },
    error: 'local reference does not exist: references/missing.md',
  },
  {
    name: 'rejects a missing image target',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': `${skill('alpha')}\n![Missing](assets/missing.png)\n` },
    error: 'local reference does not exist: assets/missing.png',
  },
  {
    name: 'rejects a missing reference-style target',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': `${skill('alpha')}\n[Guide][guide]\n[guide]: references/missing.md\n` },
    error: 'local reference does not exist: references/missing.md',
  },
  {
    name: 'rejects a local link escaping its skill',
    files: { ...validFiles(), 'skills/alpha/SKILL.md': `${skill('alpha')}\n[README](../../README.md)\n` },
    error: 'local reference escapes skill directory: ../../README.md',
  },
  {
    name: 'rejects a missing metadata asset',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { iconSmall: './assets/missing.svg' }) },
    error: 'local reference does not exist: ./assets/missing.svg',
  },
  {
    name: 'rejects a metadata asset escaping its skill',
    files: { ...validFiles(), 'skills/alpha/agents/openai.yaml': metadata('alpha', { iconSmall: '../../../README.md' }) },
    error: 'local reference escapes skill directory: ../../../README.md',
  },
  {
    name: 'rejects machine-specific absolute paths',
    files: { ...validFiles(), 'skills/alpha/script.py': 'ROOT = "/Users/example/project"\n' },
    error: 'machine-specific absolute path: /Users/example/',
  },
  {
    name: 'rejects Linux user-home paths',
    files: { ...validFiles(), 'skills/alpha/script.py': 'ROOT = "/home/example/project"\n' },
    error: 'machine-specific absolute path: /home/example/',
  },
  {
    name: 'rejects Windows user-home paths',
    files: { ...validFiles(), 'skills/alpha/script.py': 'ROOT = "C:\\Users\\example\\project"\n' },
    error: 'machine-specific absolute path: C:',
  },
]) {
  test(scenario.name, async (t) => {
    const root = await fixture(scenario.files);
    t.after(() => rm(root, { recursive: true, force: true }));
    const result = validate(root);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, new RegExp(scenario.error.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  });
}
