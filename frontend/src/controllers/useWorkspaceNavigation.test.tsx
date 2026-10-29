// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it } from 'vitest';
import { useWorkspaceNavigation } from './useWorkspaceNavigation';
import { currentWorkspaceTab, rememberWikiPage } from '../repositories/wikiNavigation';
const id = 'wpg_' + 'a'.repeat(32);
beforeEach(() => window.history.replaceState(null, '', '/'));
afterEach(() => {cleanup(); window.history.replaceState(null, '', '/');});
it('leaves a wiki URL when returning to chat and restores the chat tab on remount', () => {
  rememberWikiPage(id);
  const hook = renderHook(() => useWorkspaceNavigation());
  expect(hook.result.current.tab).toBe('wiki');
  act(() => hook.result.current.navigate('chat'));
  expect(window.location.pathname).toBe('/');
  expect(hook.result.current.wikiOpened).toBe(true);
  hook.unmount();
  const restored = renderHook(() => useWorkspaceNavigation());
  expect(restored.result.current.tab).toBe('chat');
});
it('keeps documents and the wiki index reloadable without overwriting a current permalink', () => {
  const hook = renderHook(() => useWorkspaceNavigation());
  act(() => hook.result.current.navigate('documents'));
  expect(window.location.pathname).toBe('/documents');
  expect(currentWorkspaceTab()).toBe('documents');
  act(() => hook.result.current.navigate('wiki'));
  expect(window.location.pathname).toBe('/wiki');
  rememberWikiPage(id);
  act(() => hook.result.current.navigate('wiki'));
  expect(window.location.pathname).toBe('/wiki/' + id);
});
it('follows history destinations in both directions without dropping mounted wiki drafts', () => {
  const hook = renderHook(() => useWorkspaceNavigation());
  act(() => {rememberWikiPage(id); window.dispatchEvent(new PopStateEvent('popstate'));});
  expect(hook.result.current.tab).toBe('wiki');
  act(() => {window.history.replaceState(null, '', '/'); window.dispatchEvent(new PopStateEvent('popstate'));});
  expect(hook.result.current.tab).toBe('chat');
  expect(hook.result.current.wikiOpened).toBe(true);
  act(() => {window.history.replaceState(null, '', '/documents'); window.dispatchEvent(new PopStateEvent('popstate'));});
  expect(hook.result.current.tab).toBe('documents');
});
