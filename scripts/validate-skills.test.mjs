import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const validator = path.resolve('scripts/validate-skills.mjs');

async function fixture(files) {
  const root = await mkdtemp(path.join(tmpdir(), 'asterism-validator-'));
  for (const [relativePath, contents] of Object.entries(files)) {
    const target = path.join(root, relativePath);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, contents);
  }
  return root;
}

function skill(name, description = `${name} description`) {
  return `---\nname: ${name}\ndescription: >\n  ${description}\n---\n\n# ${name}\n`;
}

function validate(root) {
  return spawnSync(process.execPath, [validator, root], { encoding: 'utf8' });
}

test('accepts valid direct-child skills and existing local links', async (t) => {
  const root = await fixture({
    'skills/alpha/SKILL.md': `${skill('alpha')}\n[Guide](references/guide.md)\n`,
    'skills/alpha/references/guide.md': '# Guide\n',
    'skills/beta/SKILL.md': skill('beta'),
  });
  t.after(() => rm(root, { recursive: true, force: true }));
  const result = validate(root);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Validated 2 skills: alpha, beta/);
});

for (const scenario of [
  {
    name: 'rejects a direct child without SKILL.md',
    files: { 'skills/alpha/readme.md': '# missing\n' },
    error: 'skills/alpha/SKILL.md: missing SKILL.md',
  },
  {
    name: 'rejects a missing name',
    files: { 'skills/alpha/SKILL.md': '---\ndescription: present\n---\n' },
    error: 'skills/alpha/SKILL.md: frontmatter name must be a non-empty string',
  },
  {
    name: 'rejects a missing description',
    files: { 'skills/alpha/SKILL.md': '---\nname: alpha\n---\n' },
    error: 'skills/alpha/SKILL.md: frontmatter description must be a non-empty string',
  },
  {
    name: 'rejects a directory-name mismatch',
    files: { 'skills/alpha/SKILL.md': skill('other') },
    error: 'skills/alpha/SKILL.md: declared name "other" differs from directory "alpha"',
  },
  {
    name: 'rejects duplicate declared names',
    files: {
      'skills/alpha/SKILL.md': skill('same'),
      'skills/beta/SKILL.md': skill('same'),
    },
    error: 'skills/beta/SKILL.md: duplicate declared name "same"',
  },
  {
    name: 'rejects a missing local Markdown target',
    files: { 'skills/alpha/SKILL.md': `${skill('alpha')}\n[Missing](references/missing.md)\n` },
    error: 'skills/alpha/SKILL.md: local reference does not exist: references/missing.md',
  },
  {
    name: 'rejects an ambiguous nested SKILL.md',
    files: {
      'skills/alpha/SKILL.md': skill('alpha'),
      'skills/alpha/nested/SKILL.md': skill('nested'),
    },
    error: 'skills/alpha/nested/SKILL.md: unexpected nested SKILL.md',
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
