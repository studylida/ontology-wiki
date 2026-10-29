import { afterEach, expect, it, vi } from 'vitest';
import { isCitation, type Citation, type WikiSource } from '../types/contracts';
import { citationIndex } from './citationService';
import { readSource, sourceKey, sourceSelection } from './sourceService';
import { sourceRepository } from '../repositories/sourceRepository';
vi.mock('../repositories/sourceRepository', () => ({sourceRepository: {read: vi.fn(), download: vi.fn()}}));
afterEach(() => vi.clearAllMocks());
const common = {id: 'wpsg_real', passageId: 'wpsg_real', sourceRevisionId: 'wrv_old', title: '개념', locator: '조건', excerpt: '본문', number: 1};
const wiki: Citation = {...common, sourceKind: 'wiki', pageId: 'wpg_page', revisionNumber: 1};
const doc: Citation = {...common, id: 'psg_doc', passageId: 'psg_doc', sourceRevisionId: 'rev_doc', number: 2, documentId: 'doc_ref'};
it('keeps one citation numbering map for actual wiki and original document identities', () => {
  expect(isCitation(wiki)).toBe(true); expect(isCitation(doc)).toBe(true);
  expect(isCitation({...wiki, documentId: 'fake-pdf'})).toBe(false);
  expect(isCitation({...common, sourceKind: 'unknown', documentId: 'doc'})).toBe(false);
  expect(isCitation({...common, sourceKind: 'wiki'})).toBe(false);
  expect([...citationIndex([wiki, doc]).values()].map(c => c.number)).toEqual([1, 2]);
  expect(sourceSelection(wiki)).toMatchObject({sourceKind: 'wiki', pageId: 'wpg_page', revisionId: 'wrv_old'});
  expect(sourceSelection(doc)).toMatchObject({documentId: 'doc_ref', revisionId: 'rev_doc'});
  expect(sourceKey(sourceSelection(wiki))).not.toBe(sourceKey(sourceSelection(doc)));
});
const original: WikiSource = {sourceKind: 'wiki', pageId: 'wpg_page', revisionId: 'wrv_old', revisionNumber: 1,
  active: false, title: '개념', content: '본문', sourceNote: '직원 경험', editor: {id: 'u', username: 'author'}, createdAt: '2026-10-29T00:00:00Z',
  passages: [{id: 'wpsg_real', ordinal: 0, text: '본문', locator: '조건', startOffset: 0, endOffset: 2, excluded: false, exclusionReason: null}]};
it('reads the cited historical revision and does not replace it with the latest page', async () => {
  vi.mocked(sourceRepository.read).mockResolvedValue(original);
  expect(await readSource(sourceSelection(wiki))).toEqual(original);
  expect(sourceRepository.read).toHaveBeenCalledWith(sourceSelection(wiki), undefined);
});
it('rejects mismatched revision, page and held evidence instead of inventing a source', async () => {
  for (const data of [{...original, revisionId: 'wrv_new'}, {...original, pageId: 'another'},
      {...original, passages: [{...original.passages[0], excluded: true}]}]) {
    vi.mocked(sourceRepository.read).mockResolvedValue(data);
    await expect(readSource(sourceSelection(wiki))).rejects.toThrow();
  }
});
