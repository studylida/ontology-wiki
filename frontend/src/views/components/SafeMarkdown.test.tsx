// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { SafeMarkdown } from './SafeMarkdown';
import type { Citation } from '../../types/contracts';
afterEach(cleanup);
const c: Citation = {id: 'p1', passageId: 'p1', sourceRevisionId: 'r1', documentId: 'd1', title: '실제 문헌', locator: '조건', excerpt: '원문', number: 7};
it('uses the server footnote number, including in a table', () => {
  const click = vi.fn();
  render(<SafeMarkdown content={'| 근거 |\n| --- |\n| 본문 [[p1]] |'} citations={[c]} onCitation={click} />);
  const button = screen.getByRole('button', {name: '출처 7: 실제 문헌'});
  expect(button.textContent).toBe('7'); fireEvent.click(button); expect(click).toHaveBeenCalledWith(c);
});
it('never executes HTML, remote images or unsafe links', () => {
  const {container} = render(<SafeMarkdown content={'<script>alert(1)</script>\n\n<img src="https://example.org/tracker">\n\n![track](https://example.org/image)\n\n[unsafe](javascript:alert(1))'} />);
  expect(container.querySelector('script, img, iframe')).toBeNull(); expect(container.querySelector('a')).toBeNull();
});
it('keeps unknown markers and code inert', () => {
  render(<SafeMarkdown content={'[[unknown]] `[[p1]]`\n\n```text\n[[p1]]\n```'} citations={[c]} onCitation={vi.fn()} />);
  expect(screen.queryByRole('button')).toBeNull(); expect(screen.getByText('[[unknown]]')).toBeTruthy();
});
it('does not produce a link for an incomplete streaming marker', () => {
  const view = render(<SafeMarkdown content={'문장 [[p'} citations={[c]} onCitation={vi.fn()} />);
  expect(screen.queryByRole('button')).toBeNull();
  view.rerender(<SafeMarkdown content={'문장 [[p1]]'} citations={[c]} onCitation={vi.fn()} />);
  expect(screen.getByRole('button').textContent).toBe('7');
});
it('renders only canonical stored wiki hyperlinks and delegates navigation', () => {
  const id = 'wpg_' + 'a'.repeat(32), click = vi.fn();
  const view = render(<SafeMarkdown content={`[예지보전](/wiki/${id}) [기타](/settings) [잘못](/wiki/%2e%2e/auth)`} onWikiNavigate={click} />);
  const links = view.container.querySelectorAll('a'); expect(links.length).toBe(1);
  expect(links[0].getAttribute('href')).toBe(`/wiki/${id}`);
  fireEvent.click(links[0]); expect(click).toHaveBeenCalledWith(id);
});
it('internal link handling never changes the supplied markdown or its label', () => {
  const content = `[상태 모니터링](/wiki/wpg_${'b'.repeat(32)})`;
  render(<SafeMarkdown content={content} />);
  expect(screen.getByRole('link').textContent).toBe('상태 모니터링');
});
