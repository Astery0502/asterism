#!/usr/bin/env node
import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { parseDocument } from 'yaml';

const root = path.resolve(process.argv[2] ?? '.');
const skillsRoot = path.join(root, 'skills');
const errors = [];
const ignoredDirectories = new Set(['.git', 'node_modules']);
const validName = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const retiredTriggerWording = /LOAD ONLY|Do not auto-load/i;
const machinePath = /(?:\/Users\/[^/\s]+\/|\/home\/[^/\s]+\/|[A-Za-z]:\\Users\\[^\\\s]+\\)/;

function relative(file) {
  return path.relative(root, file).split(path.sep).join('/');
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

const contentCache = new Map();

async function readContent(file) {
  if (!contentCache.has(file)) contentCache.set(file, await readFile(file));
  return contentCache.get(file);
}

async function readText(file) {
  return (await readContent(file)).toString('utf8');
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

async function filesUnder(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await filesUnder(target));
    if (entry.isFile()) found.push(target);
  }
  return found;
}

function parseYaml(text, file) {
  const document = parseDocument(text, { uniqueKeys: true });
  if (document.errors.length > 0) {
    for (const error of document.errors) {
      errors.push(`${relative(file)}: invalid YAML: ${error.message.split('\n')[0]}`);
    }
    return null;
  }
  return document.toJS();
}

function parseFrontmatter(text, file) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) {
    errors.push(`${relative(file)}: missing or malformed YAML frontmatter`);
    return null;
  }
  return parseYaml(match[1], file);
}

function localTargets(markdown) {
  const targets = [];
  const inline = markdown.matchAll(/!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+["'][^"']*["'])?\s*\)/g);
  for (const match of inline) targets.push(match[1] ?? match[2]);

  const references = markdown.matchAll(/^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|([^\s]+))/gm);
  for (const match of references) targets.push(match[1] ?? match[2]);
  return targets;
}

function isExternalTarget(target) {
  return /^(?:[a-z][a-z0-9+.-]*:|#|\/)/i.test(target);
}

async function validateLocalTarget(sourceFile, skillDirectory, target) {
  if (isExternalTarget(target)) return;
  const cleanTarget = decodeURIComponent(target.split(/[?#]/, 1)[0]);
  const resolved = path.resolve(path.dirname(sourceFile), cleanTarget);
  const insideSkill = resolved === skillDirectory || resolved.startsWith(`${skillDirectory}${path.sep}`);
  if (!insideSkill) {
    errors.push(`${relative(sourceFile)}: local reference escapes skill directory: ${target}`);
    return;
  }
  if (!await exists(resolved)) {
    errors.push(`${relative(sourceFile)}: local reference does not exist: ${target}`);
  }
}

function validateString(file, field, value) {
  if (typeof value !== 'string' || value.trim() === '') {
    errors.push(`${relative(file)}: ${field} must be a non-empty string`);
    return null;
  }
  return value.trim();
}

function isOneSentence(value) {
  const trimmed = value.trim();
  return /^[\s\S]*[.!?]$/.test(trimmed) && !/[.!?]/.test(trimmed.slice(0, -1));
}

function sameArray(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
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

const allFiles = await filesUnder(root);
const allFileSet = new Set(allFiles);
const canonicalSkillFiles = new Set(children.map((child) => path.join(skillsRoot, child.name, 'SKILL.md')));
const canonicalMetadataFiles = new Set(children.map((child) => path.join(skillsRoot, child.name, 'agents', 'openai.yaml')));
const filesBySkill = new Map(children.map((child) => [child.name, []]));

for (const file of allFiles) {
  if (path.basename(file) === 'SKILL.md' && !canonicalSkillFiles.has(file)) {
    errors.push(`${relative(file)}: unexpected off-catalog SKILL.md`);
  }
  if (path.basename(file) === 'openai.yaml' && !canonicalMetadataFiles.has(file)) {
    errors.push(`${relative(file)}: unexpected off-catalog agents/openai.yaml`);
  }
  const skillPath = path.relative(skillsRoot, file);
  if (!skillPath.startsWith(`..${path.sep}`) && !path.isAbsolute(skillPath)) {
    filesBySkill.get(skillPath.split(path.sep, 1)[0])?.push(file);
  }
}

const declaredNames = new Set();
for (const child of children) {
  const skillDirectory = path.join(skillsRoot, child.name);
  const skillFile = path.join(skillDirectory, 'SKILL.md');
  const metadataFile = path.join(skillDirectory, 'agents', 'openai.yaml');

  if (!allFileSet.has(skillFile)) {
    errors.push(`${relative(skillFile)}: missing SKILL.md`);
    continue;
  }

  const skillText = await readText(skillFile);
  const frontmatter = parseFrontmatter(skillText, skillFile);
  if (frontmatter !== null && !isObject(frontmatter)) {
    errors.push(`${relative(skillFile)}: frontmatter must be a mapping`);
  } else if (isObject(frontmatter)) {
    const name = validateString(skillFile, 'frontmatter name', frontmatter.name);
    const description = validateString(skillFile, 'frontmatter description', frontmatter.description);
    if (name) {
      if (name.length > 64 || !validName.test(name)) {
        errors.push(`${relative(skillFile)}: invalid skill name "${name}"`);
      }
      if (name !== child.name) {
        errors.push(`${relative(skillFile)}: declared name "${name}" differs from directory "${child.name}"`);
      }
      if (declaredNames.has(name)) {
        errors.push(`${relative(skillFile)}: duplicate declared name "${name}"`);
      }
      declaredNames.add(name);
    }
    if (description && retiredTriggerWording.test(description)) {
      errors.push(`${relative(skillFile)}: description contains retired trigger-policy wording`);
    }
    if (frontmatter['disable-model-invocation'] !== true) {
      errors.push(`${relative(skillFile)}: disable-model-invocation must be true`);
    }
  }

  if (!allFileSet.has(metadataFile)) {
    errors.push(`${relative(metadataFile)}: missing agents/openai.yaml`);
  } else {
    const metadata = parseYaml(await readText(metadataFile), metadataFile);
    if (metadata !== null && !isObject(metadata)) {
      errors.push(`${relative(metadataFile)}: metadata must be a mapping`);
    } else if (isObject(metadata)) {
      validateString(metadataFile, 'interface.display_name', metadata.interface?.display_name);
      const shortDescription = validateString(metadataFile, 'interface.short_description', metadata.interface?.short_description);
      const defaultPrompt = validateString(metadataFile, 'interface.default_prompt', metadata.interface?.default_prompt);
      if (shortDescription && (shortDescription.length < 25 || shortDescription.length > 64)) {
        errors.push(`${relative(metadataFile)}: interface.short_description must be 25-64 characters`);
      }
      if (defaultPrompt) {
        if (!defaultPrompt.includes(`$${child.name}`)) {
          errors.push(`${relative(metadataFile)}: interface.default_prompt must contain $${child.name}`);
        }
        if (!isOneSentence(defaultPrompt)) {
          errors.push(`${relative(metadataFile)}: interface.default_prompt must be one sentence`);
        }
      }
      if (metadata.policy?.allow_implicit_invocation !== false) {
        errors.push(`${relative(metadataFile)}: policy.allow_implicit_invocation must be false`);
      }
      for (const assetField of ['icon_small', 'icon_large']) {
        const asset = metadata.interface?.[assetField];
        if (asset !== undefined) {
          if (typeof asset !== 'string' || asset.trim() === '') {
            errors.push(`${relative(metadataFile)}: interface.${assetField} must be a non-empty string`);
          } else {
            await validateLocalTarget(metadataFile, skillDirectory, asset);
          }
        }
      }
    }
  }

  for (const file of filesBySkill.get(child.name)) {
    const content = await readContent(file);
    if (content.includes(0)) continue;
    const text = content.toString('utf8');
    const pathMatch = text.match(machinePath);
    if (pathMatch) {
      errors.push(`${relative(file)}: machine-specific absolute path: ${pathMatch[0]}`);
    }
    if (path.extname(file).toLowerCase() === '.md') {
      for (const target of localTargets(text)) {
        await validateLocalTarget(file, skillDirectory, target);
      }
    }
  }
}

const expectedNames = children.map((entry) => entry.name);
const readmeFile = path.join(root, 'README.md');
if (!await exists(readmeFile)) {
  errors.push('README.md: file does not exist');
} else {
  const readme = await readText(readmeFile);
  const section = readme.match(/^## Included skills\s*$([\s\S]*?)^## Install\s*$/m);
  if (!section) {
    errors.push('README.md: cannot find Included skills catalog');
  } else {
    const readmeNames = [...section[1].matchAll(/^- \*\*([a-z0-9-]+)\*\* - /gm)]
      .map((match) => match[1])
      .sort();
    if (!sameArray(expectedNames, readmeNames)) {
      errors.push(`README.md: skill catalog differs; expected [${expectedNames.join(', ')}], found [${readmeNames.join(', ')}]`);
    }
  }
}

if (errors.length > 0) {
  for (const error of errors) console.error(error);
  process.exit(1);
}

console.log(`Validated ${children.length} skills: ${expectedNames.join(', ')}`);
