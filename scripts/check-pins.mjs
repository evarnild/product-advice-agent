#!/usr/bin/env node
// Hand-run check of the Langfuse stack's image pins (needs Docker and network;
// not part of `npm run verify`). Read-only: `docker buildx imagetools inspect`
// only reads registry manifests; it never pulls, runs or tags an image.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const compose = new URL('../infra/langfuse/docker-compose.yml', import.meta.url);
const refs = [...readFileSync(compose, 'utf8').matchAll(/^\s*image:\s*(\S+)/gm)].map((m) => m[1]);

function inspect(ref) {
  try {
    return { out: execFileSync('docker', ['buildx', 'imagetools', 'inspect', ref], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }) };
  } catch (e) {
    if (e.code === 'ENOENT') {
      console.error('docker is not available: install Docker (with buildx) and put it on PATH');
      process.exit(2);
    }
    return { err: String(e.stderr || e.message).trim().split('\n').pop().slice(0, 120) };
  }
}
const digestOf = (out) => /^Digest:\s*(\S+)/m.exec(out)?.[1];

let failed = 0;
for (const ref of refs) {
  const r = inspect(ref);
  if (r.err) {
    failed++;
    console.log(`UNRESOLVED  ${ref}  ${r.err}`);
    continue;
  }
  console.log(`ok  ${ref}`);
  const [name, pin] = ref.split('@');
  if (!pin) continue;
  const latest = inspect(`${name}:latest`);
  const digest = latest.out && digestOf(latest.out);
  if (!digest) console.log(`    latest: could not resolve ${name}:latest (${latest.err ?? 'no digest'})`);
  else if (digest === pin) console.log(`    pin is current (${name}:latest)`);
  else console.log(`    pin is BEHIND ${name}:latest (not a failure); to update paste: ${name}@${digest}`);
}
if (failed) console.log(`${failed} pin(s) failed to resolve`);
process.exit(failed ? 1 : 0);
