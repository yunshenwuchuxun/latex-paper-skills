#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { constants } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const skillName = 'latex-paper-skills';
const packageRoot = fileURLToPath(new URL('../', import.meta.url));
const bundlePath = resolve(packageRoot, 'skills', skillName);
const args = process.argv.slice(2);

function printHelp() {
  console.log(`Usage: latex-paper-skills [install] [skills options]
       latex-paper-skills list [skills options]

Install the bundled LaTeX paper workflows in the current project.
Use --global explicitly to install at user level.

Options:
  -a, --agent <agents>  Choose supported agents, such as codex
  -g, --global          Install at user level
  -y, --yes             Skip confirmation prompts
  --copy                Copy files instead of creating symlinks
  -h, --help            Show this help
  -v, --version         Show the package version

Other skills installation options are forwarded unchanged.
The source and skill selection are fixed to this package's local bundle.`);
}

function runSkills(forwardedArgs, listOnly) {
  const require = createRequire(import.meta.url);
  const manifestPath = require.resolve('skills/package.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const bin = typeof manifest.bin === 'string' ? manifest.bin : manifest.bin?.skills;
  if (typeof bin !== 'string') {
    throw new Error('The installed skills dependency has no skills CLI entry point.');
  }
  const cliPath = resolve(dirname(manifestPath), bin);
  const childArgs = ['add', bundlePath, '--skill', skillName];
  if (listOnly) childArgs.push('--list');
  childArgs.push(...forwardedArgs);

  const child = spawn(process.execPath, [cliPath, ...childArgs], { stdio: 'inherit' });
  const signalHandlers = new Map();
  for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
    const handler = () => child.kill(signal);
    signalHandlers.set(signal, handler);
    process.on(signal, handler);
  }
  const removeSignalHandlers = () => {
    for (const [signal, handler] of signalHandlers) process.off(signal, handler);
  };

  child.once('error', (error) => {
    removeSignalHandlers();
    console.error(`Unable to start skills: ${error.message}`);
    process.exitCode = 1;
  });
  child.once('exit', (code, signal) => {
    removeSignalHandlers();
    if (signal) {
      try {
        process.kill(process.pid, signal);
      } catch {
        process.exitCode = 128 + (constants.signals[signal] ?? 1);
      }
    } else {
      process.exitCode = code ?? 1;
    }
  });
}

try {
  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
  } else if (args.includes('--version') || args.includes('-v')) {
    const manifest = JSON.parse(readFileSync(resolve(packageRoot, 'package.json'), 'utf8'));
    console.log(manifest.version);
  } else {
    const command = args[0];
    const listOnly = command === 'list';
    const forwardedArgs = command === 'install' || listOnly ? args.slice(1) : args;
    if (command && !command.startsWith('-') && command !== 'install' && !listOnly) {
      throw new Error(`Unknown command: ${command}. Use install, list, or --help.`);
    }
    if (forwardedArgs.some((arg) => ['--skill', '-s'].includes(arg) || arg.startsWith('--skill=') || arg.startsWith('-s='))) {
      throw new Error('Skill selection is fixed to latex-paper-skills; omit --skill or -s.');
    }
    runSkills(forwardedArgs, listOnly);
  }
} catch (error) {
  console.error(`latex-paper-skills: ${error.message}`);
  process.exitCode = 1;
}
