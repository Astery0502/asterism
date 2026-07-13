#!/usr/bin/env node
import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(process.argv[2] ?? '.');
const skillsRoot = path.join(root, 'skills');
const errors = [];

function relative(file) {
  return path.relative(root, file).split(path.sep).join('/');
}

async function exists(target) {
  try {
    await stat(target);
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

function scalar(frontmatter, key) {
  const lines = frontmatter.split(/\r?\n/);
  const index = lines.findIndex((line) => line.startsWith(`${key}:`));
  if (index === -1) return null;
  const raw = lines[index].slice(key.length + 1).trim();
  if (raw === '>' || raw === '|') {
    const value = [];
    for (const line of lines.slice(index + 1)) {
      if (!/^\s+/.test(line)) break;
      value.push(line.trim());
    }
    return value.join(raw === '>' ? ' ' : '\n').trim() || null;
  }
  if (!raw || /^(null|true|false|[0-9]+|\[|\{)/i.test(raw)) return null;
  if ((raw.startsWith('"') && raw.endsWith('"')) ||
      (raw.startsWith("'") && raw.endsWith("'"))) {
    return raw.slice(1, -1).trim() || null;
  }
  return raw;
}

function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) return { name: null, description: null };
  return {
    name: scalar(match[1], 'name'),
    description: scalar(match[1], 'description'),
  };
}

async function filesUnder(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await filesUnder(target));
    if (entry.isFile()) found.push(target);
  }
  return found;
}

async function validateLinks(markdownFile) {
  const text = await readFile(markdownFile, 'utf8');
  const links = text.matchAll(/!?\[[^\]]*\]\(([^)\s]+)(?:\s+["'][^"']*["'])?\)/g);
  for (const match of links) {
    const href = match[1];
    if (/^(?:[a-z]+:|#|\/)/i.test(href)) continue;
    const cleanHref = decodeURIComponent(href.split(/[?#]/, 1)[0]);
    const target = path.resolve(path.dirname(markdownFile), cleanHref);
    if (!await exists(target)) {
      errors.push(`${relative(markdownFile)}: local reference does not exist: ${href}`);
    }
  }
}

let children;
try {
  children = (await readdir(skillsRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .sort((left, right) => left.name.localeCompare(right.name));
} catch (error) {
  if (error.code === 'ENOENT') {
    console.error('skills: directory does not exist');
    process.exit(1);
  }
  throw error;
}

const declaredNames = new Map();
for (const child of children) {
  const skillDirectory = path.join(skillsRoot, child.name);
  const skillFile = path.join(skillDirectory, 'SKILL.md');
  if (!await exists(skillFile)) {
    errors.push(`${relative(skillFile)}: missing SKILL.md`);
    continue;
  }

  const files = await filesUnder(skillDirectory);
  for (const file of files) {
    if (path.basename(file) === 'SKILL.md' && file !== skillFile) {
      errors.push(`${relative(file)}: unexpected nested SKILL.md`);
    }
    if (path.extname(file).toLowerCase() === '.md') await validateLinks(file);
  }

  const frontmatter = parseFrontmatter(await readFile(skillFile, 'utf8'));
  if (!frontmatter.name) {
    errors.push(`${relative(skillFile)}: frontmatter name must be a non-empty string`);
  } else {
    if (frontmatter.name !== child.name) {
      errors.push(`${relative(skillFile)}: declared name "${frontmatter.name}" differs from directory "${child.name}"`);
    }
    if (declaredNames.has(frontmatter.name)) {
      errors.push(`${relative(skillFile)}: duplicate declared name "${frontmatter.name}"`);
    } else {
      declaredNames.set(frontmatter.name, skillFile);
    }
  }
  if (!frontmatter.description) {
    errors.push(`${relative(skillFile)}: frontmatter description must be a non-empty string`);
  }
}

if (errors.length > 0) {
  for (const error of errors) console.error(error);
  process.exit(1);
}

console.log(`Validated ${children.length} skills: ${children.map((entry) => entry.name).join(', ')}`);
