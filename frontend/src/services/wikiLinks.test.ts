import { describe, expect, it } from 'vitest';
import { wikiPageHref, wikiPageId } from './wikiLinks';
const id = 'wpg_' + 'a'.repeat(32);
it('uses stable page identity, not a mutable title', () => {
  expect(wikiPageId(wikiPageHref(id))).toBe(id);
  expect(() => wikiPageHref('RUL')).toThrow();
});
describe('reject noncanonical internal URLs', () => {
  it.each(['//evil.test/wiki/' + id, '/wiki/../auth', '/wiki/%2e%2e/auth', '/wiki/' + id + '?redirect=//evil.test',
    '/wiki/' + id + '/edit', '/wiki\\' + id, 'javascript:alert(1)', 'https://evil.test/wiki/' + id])('%s', value => {
    expect(wikiPageId(value)).toBeNull();
  });
});
