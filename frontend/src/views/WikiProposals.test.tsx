// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { WikiProposals } from './WikiProposals';
import { useWikiProposals } from '../controllers/useWikiProposals';
vi.mock('../controllers/useWikiProposals', () => ({useWikiProposals: vi.fn()}));
vi.mock('./WikiDiscovery', () => ({WikiSearchPanel: () => null}));
afterEach(cleanup);
it('keeps populated review labels separate from document contents', () => {
  vi.mocked(useWikiProposals).mockReturnValue({items: [], selected: {id: 'p1', status: 'ready',
    instruction: 'make a draft', employeeText: 'selected text', base: {}, result: {}, canApply: true},
    draft: {title: 'RUL', markdown: '# RUL\n\nEmployee experience', sourceNote: 'Staff input'},
    instruction: '', context: '', busy: false, pending: null, change: vi.fn(), refresh: vi.fn(),
    apply: vi.fn(), dismiss: vi.fn()} as unknown as ReturnType<typeof useWikiProposals>);
  render(<WikiProposals userId="alice" page={null}/>);
  const field = screen.getByRole('textbox', {name: '반영할 Markdown', exact: true}) as HTMLTextAreaElement;
  expect(field.value).toContain('Employee experience');
  expect(field.labels?.[0].textContent).toBe('반영할 Markdown');
  const note = screen.getByRole('textbox', {name: '반영할 근거·업무 맥락', exact: true}) as HTMLTextAreaElement;
  expect(note.labels?.[0].textContent).toBe('반영할 근거·업무 맥락');
});
