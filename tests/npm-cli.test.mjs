import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { copyFile, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const wrapperSource = fileURLToPath(new URL('../bin/latex-paper-skills.mjs', import.meta.url));

async function fixture(t, { dependency = true } = {}) {
  const root = await realpath(await mkdtemp(join(tmpdir(), 'latex-paper-npm-cli-')));
  t.after(() => rm(root, { recursive: true, force: true }));
  const packageRoot = join(root, "npm package's directory");
  const project = join(root, "user project's directory");
  const bin = join(packageRoot, 'bin', 'latex-paper-skills.mjs');
  const bundle = join(packageRoot, 'skills', 'latex-paper-skills');
  const capture = join(root, 'capture.json');
  await mkdir(join(packageRoot, 'bin'), { recursive: true });
  await mkdir(project);
  await mkdir(bundle, { recursive: true });
  await copyFile(wrapperSource, bin);
  await writeFile(join(packageRoot, 'package.json'), JSON.stringify({ name: 'latex-paper-skills', version: '3.2.1', type: 'module' }));
  await writeFile(join(bundle, 'SKILL.md'), '---\nname: latex-paper-skills\ndescription: Fixture bundle\n---\n');
  if (dependency) {
    const dependencyRoot = join(packageRoot, 'node_modules', 'skills');
    await mkdir(join(dependencyRoot, 'bin'), { recursive: true });
    await writeFile(join(dependencyRoot, 'package.json'), JSON.stringify({ name: 'skills', type: 'module', bin: { skills: './bin/cli.mjs' } }));
    await writeFile(join(dependencyRoot, 'bin', 'cli.mjs'), `
import { writeFile } from 'node:fs/promises';
await writeFile(process.env.WRAPPER_TEST_CAPTURE, JSON.stringify({ args: process.argv.slice(2), cwd: process.cwd() }));
if (process.env.WRAPPER_TEST_SIGNAL) process.kill(process.pid, process.env.WRAPPER_TEST_SIGNAL);
else process.exit(Number(process.env.WRAPPER_TEST_EXIT ?? 0));
`);
  }
  return { root, packageRoot, project, bin, bundle, capture };
}

function execute(f, args = [], extraEnv = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [f.bin, ...args], {
      cwd: f.project,
      env: { ...process.env, DISABLE_TELEMETRY: '1', DO_NOT_TRACK: '1', WRAPPER_TEST_CAPTURE: f.capture, ...extraEnv },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    const timeout = setTimeout(() => child.kill('SIGKILL'), 10000);
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.once('error', (error) => { clearTimeout(timeout); reject(error); });
    child.once('close', (code, signal) => {
      clearTimeout(timeout);
      resolve({ code, signal, stdout, stderr });
    });
  });
}

async function captured(f) {
  return JSON.parse(await readFile(f.capture, 'utf8'));
}

test('default installation uses only the absolute local bundle and preserves the project cwd', async (t) => {
  const f = await fixture(t);
  const result = await execute(f);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual(await captured(f), { args: ['add', f.bundle, '--skill', 'latex-paper-skills'], cwd: f.project });
});

test('install alias forwards official options and explicit global selection unchanged', async (t) => {
  const f = await fixture(t);
  const options = ['--agent', 'codex', 'cursor', '--global', '--copy', '--yes'];
  const result = await execute(f, ['install', ...options]);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual((await captured(f)).args, ['add', f.bundle, '--skill', 'latex-paper-skills', ...options]);
});

test('list selects the bundled skill through the upstream list option', async (t) => {
  const f = await fixture(t);
  const result = await execute(f, ['list', '--agent', 'codex']);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual((await captured(f)).args, ['add', f.bundle, '--skill', 'latex-paper-skills', '--list', '--agent', 'codex']);
});

test('help and package version work without loading the skills dependency', async (t) => {
  const f = await fixture(t, { dependency: false });
  for (const flag of ['--help', '-h']) {
    const result = await execute(f, [flag]);
    assert.equal(result.code, 0, result.stderr);
    assert.ok(result.stdout.length > 0);
  }
  for (const flag of ['--version', '-v']) {
    const result = await execute(f, [flag]);
    assert.equal(result.code, 0, result.stderr);
    assert.equal(result.stdout.trim(), '3.2.1');
  }
  await assert.rejects(readFile(f.capture), { code: 'ENOENT' });
});

test('callers cannot replace the fixed skill selector', async (t) => {
  const f = await fixture(t);
  for (const args of [['--skill', 'other-skill'], ['install', '-s', 'other-skill'], ['--skill=other-skill']]) {
    const result = await execute(f, args);
    assert.equal(result.code, 1);
    await assert.rejects(readFile(f.capture), { code: 'ENOENT' });
  }
});

test('the upstream process exit code is returned unchanged', async (t) => {
  const f = await fixture(t);
  const result = await execute(f, ['--agent', 'codex'], { WRAPPER_TEST_EXIT: '27' });
  assert.equal(result.code, 27);
});

test('the upstream termination signal is returned unchanged', { skip: process.platform === 'win32' }, async (t) => {
  const f = await fixture(t);
  const result = await execute(f, [], { WRAPPER_TEST_SIGNAL: 'SIGTERM' });
  assert.equal(result.code, null);
  assert.equal(result.signal, 'SIGTERM');
});

test('missing skills dependency reports failure without installing anything', async (t) => {
  const f = await fixture(t, { dependency: false });
  const result = await execute(f, ['--agent', 'codex']);
  assert.equal(result.code, 1);
  await assert.rejects(readFile(f.capture), { code: 'ENOENT' });
});
