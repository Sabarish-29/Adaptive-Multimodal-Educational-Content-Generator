#!/usr/bin/env node
import { spawn } from 'node:child_process';
const args = process.argv.slice(2);
const runner = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const child = spawn(runner, ['playwright','test','--reporter=list', ...args], { stdio: 'inherit' });
child.on('exit', code => process.exit(code ?? 1));
