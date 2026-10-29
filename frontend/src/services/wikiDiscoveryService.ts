import { wikiDiscoveryRepository as repository } from '../repositories/wikiDiscoveryRepository';
import type { WikiDraft } from '../types/wiki';
export const indexLabels: Record<string, string> = {not_indexed: '검색 색인 대기', queued: '색인 대기',
  processing: '색인 처리 중', ready: '검색 사용 가능', partial: '일부 구간 검색 가능', failed: '색인 실패',
  profile_mismatch: '현재 임베딩 설정으로 재색인 필요', superseded: '이전 판본 작업'};
export const isIndexPending = (state?: string) => state === 'queued' || state === 'processing';
export const wikiDiscoveryService = {
  index: repository.index, alternatives: repository.alternatives, retryIndex: repository.retryIndex,
  search(query: string, signal?: AbortSignal) {return repository.search(query.trim(), signal);},
  similar(draft: WikiDraft, exclude?: string, signal?: AbortSignal) {
    return repository.similar(draft.title.trim(), draft.markdown, exclude, signal);
  },
};
