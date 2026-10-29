// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { DocumentWikiSuggestions } from './DocumentWikiSuggestions';
import { useDocumentWikiNotice } from '../controllers/useDocumentWikiNotice';
vi.mock('../controllers/useDocumentWikiNotice', () => ({useDocumentWikiNotice:vi.fn()}));
vi.mock('./WikiProposals', () => ({WikiProposals:({documentId}:{documentId:string})=><p>shared review {documentId}</p>}));
afterEach(() => {cleanup(); vi.clearAllMocks();});
it('keeps the existing review UI folded until the employee chooses it', () => {
  vi.mocked(useDocumentWikiNotice).mockReturnValue({error:'',value:{documentId:'d1',revisionId:'r1',enabled:true,status:'succeeded',result:{},error:null,
    items:[{id:'p1',pageId:null,mode:'create',status:'ready',createdAt:'2026-10-29',updatedAt:'2026-10-29'}]}});
  render(<DocumentWikiSuggestions userId="alice" documentId="d1" revisionId="r1"/>);
  expect(screen.queryByText('shared review d1')).toBeNull();
  expect(screen.getByRole('status').textContent).toContain('확인할 제안 1건');
  fireEvent.click(screen.getByRole('button',{name:'위키 보강 제안 확인'}));
  expect(screen.getByText('shared review d1')).toBeTruthy();
});
it('shows optional failure without claiming that the document failed', () => {
  vi.mocked(useDocumentWikiNotice).mockReturnValue({error:'',value:{documentId:'d1',revisionId:'r1',enabled:true,status:'failed',result:{},items:[],error:{code:'failed',message:'자동 검토 실패'}}});
  render(<DocumentWikiSuggestions userId="alice" documentId="d1" revisionId="r1"/>);
  expect(screen.getByText(/확인하지 않아도 문헌 검색과 채팅/)).toBeTruthy();
  expect(screen.queryByRole('button',{name:'위키 보강 제안 확인'})).toBeNull();
});
