// The handful of `expect` matchers the kit's tests use, on top of node:assert,
// so `node --test` runs them with no dependency whatever stack the project
// picks. Add a matcher here when a test needs one; keep the names Vitest's.
// `expect(x).not.<matcher>` negates any of them.
import assert from 'node:assert/strict';
import { isDeepStrictEqual, inspect } from 'node:util';

const show = (v) => inspect(v, { depth: 6, breakLength: Infinity });

/**
 * Vitest's toMatchObject: every key of `expected` is in `actual` and matches,
 * recursively for plain objects; arrays must have the same length and match
 * element by element; anything else must be deeply equal.
 */
function matchesObject(actual, expected) {
  if (Array.isArray(expected)) {
    return Array.isArray(actual) && actual.length === expected.length && expected.every((x, i) => matchesObject(actual[i], x));
  }
  if (expected && typeof expected === 'object' && !(expected instanceof RegExp) && !(expected instanceof Date)) {
    if (!actual || typeof actual !== 'object') return false;
    return Object.entries(expected).every(([k, x]) => k in Object(actual) && matchesObject(actual[k], x));
  }
  return isDeepStrictEqual(actual, expected);
}

/** Vitest's toThrow argument: nothing, a RegExp or a substring of the message, or an Error class. */
function threwMatching(fn, expected) {
  try {
    fn();
  } catch (e) {
    if (expected === undefined) return { threw: true, ok: true, error: e };
    const message = e?.message ?? String(e);
    if (expected instanceof RegExp) return { threw: true, ok: expected.test(message), error: e };
    if (typeof expected === 'string') return { threw: true, ok: message.includes(expected), error: e };
    if (typeof expected === 'function') return { threw: true, ok: e instanceof expected, error: e };
    return { threw: true, ok: isDeepStrictEqual(e, expected), error: e };
  }
  return { threw: false, ok: false };
}

/** Each matcher returns [pass, failure message when it should have passed, failure message when negated]. */
const MATCHERS = {
  toBe: (a, v) => [Object.is(a, v), `expected ${show(a)} to be ${show(v)}`, `expected ${show(a)} not to be ${show(v)}`],
  toEqual: (a, v) => [isDeepStrictEqual(a, v), `expected ${show(a)} to equal ${show(v)}`, `expected ${show(a)} not to equal ${show(v)}`],
  toStrictEqual: (a, v) => [isDeepStrictEqual(a, v), `expected ${show(a)} to strictly equal ${show(v)}`, `expected ${show(a)} not to strictly equal ${show(v)}`],
  toMatchObject: (a, v) => [matchesObject(a, v), `expected ${show(a)} to match object ${show(v)}`, `expected ${show(a)} not to match object ${show(v)}`],
  toBeNull: (a) => [a === null, `expected ${show(a)} to be null`, 'expected value not to be null'],
  toBeUndefined: (a) => [a === undefined, `expected ${show(a)} to be undefined`, 'expected value not to be undefined'],
  toBeDefined: (a) => [a !== undefined, 'expected value to be defined', `expected ${show(a)} to be undefined`],
  toBeTruthy: (a) => [Boolean(a), `expected ${show(a)} to be truthy`, `expected ${show(a)} to be falsy`],
  toBeFalsy: (a) => [!a, `expected ${show(a)} to be falsy`, `expected ${show(a)} to be truthy`],
  toContain: (a, v) => [a.includes(v), `expected ${show(a)} to contain ${show(v)}`, `expected ${show(a)} not to contain ${show(v)}`],
  toMatch: (a, re) => {
    const pass = typeof re === 'string' ? String(a).includes(re) : re.test(a);
    return [pass, `expected ${show(a)} to match ${re}`, `expected ${show(a)} not to match ${re}`];
  },
  toHaveLength: (a, n) => [a?.length === n, `expected length ${n}, got ${show(a)}`, `expected length not to be ${n}`],
  toHaveProperty: (a, key, ...value) => {
    const path = Array.isArray(key) ? key : String(key).split('.');
    let cur = a;
    let has = true;
    for (const k of path) {
      if (cur == null || !(k in Object(cur))) {
        has = false;
        break;
      }
      cur = cur[k];
    }
    const pass = has && (value.length === 0 || isDeepStrictEqual(cur, value[0]));
    const what = value.length ? `property ${show(key)} = ${show(value[0])}` : `property ${show(key)}`;
    return [pass, `expected ${show(a)} to have ${what}`, `expected ${show(a)} not to have ${what}`];
  },
  toBeLessThan: (a, n) => [a < n, `expected ${show(a)} to be less than ${show(n)}`, `expected ${show(a)} not to be less than ${show(n)}`],
  toBeLessThanOrEqual: (a, n) => [a <= n, `expected ${show(a)} to be <= ${show(n)}`, `expected ${show(a)} not to be <= ${show(n)}`],
  toBeGreaterThan: (a, n) => [a > n, `expected ${show(a)} to be greater than ${show(n)}`, `expected ${show(a)} not to be greater than ${show(n)}`],
  toBeGreaterThanOrEqual: (a, n) => [a >= n, `expected ${show(a)} to be >= ${show(n)}`, `expected ${show(a)} not to be >= ${show(n)}`],
  toThrow: (fn, expected) => {
    const r = threwMatching(fn, expected);
    const want = expected === undefined ? 'to throw' : `to throw ${show(expected)}`;
    const got = r.threw ? `it threw ${show(r.error?.message ?? r.error)}` : 'it did not throw';
    return [r.ok, `expected function ${want}, but ${got}`, `expected function not ${want}, but ${got}`];
  },
};

function build(actual, message, negated) {
  const out = {};
  for (const [name, check] of Object.entries(MATCHERS)) {
    out[name] = (...args) => {
      const [pass, failMsg, notMsg] = check(actual, ...args);
      if (pass === negated) assert.fail(message ? `${message}\n${negated ? notMsg : failMsg}` : negated ? notMsg : failMsg);
    };
  }
  return out;
}

export function expect(actual, message) {
  const matchers = build(actual, message, false);
  matchers.not = build(actual, message, true);
  return matchers;
}
