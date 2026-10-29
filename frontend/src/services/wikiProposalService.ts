import type { SourceSelection } from '../types/contracts';
import type { Proposal, ProposalCommand, ProposalEvidence, ProposalPending, ProposalSummary } from '../types/wikiProposal';
import type { WikiMutation, WikiWrite } from '../types/wiki';
import { newRequestId } from '../repositories/workspaceStorage';
import { proposalRepository } from '../repositories/wikiProposalRepository';
export const proposalLabel = (status: string) => ({pending: '생성 대기', running: '제안 작성 중', ready: '직원 확인 필요',
  applied: '반영 완료', dismissed: '무시함', failed: '생성 실패'}[status] || status);
export const proposalDraft = (p: Proposal): WikiWrite => ({title: p.result.title || p.base.title || '',
  markdown: p.result.markdown || '', sourceNote: p.result.sourceNote || '', changeSummary: 'AI 제안 검토 후 반영',
  aliases: p.result.aliases || p.base.aliases || [], meaning: p.result.meaning || p.base.meaning || ''});
export const applyProposalCommand = (p: Proposal, draft: WikiWrite): ProposalCommand => ({kind: 'apply', id: p.id,
  body: {...draft, requestId: newRequestId()}});
export async function executeProposal(pending: ProposalPending, acknowledge: (r: ProposalSummary | WikiMutation) => void) {
  const receipt = pending.receipt || await proposalRepository.execute(pending.command);
  acknowledge(receipt);
  const id = pending.command.kind === 'submit' ? (receipt as ProposalSummary).id : pending.command.id;
  return proposalRepository.get(id); // Confirmed POST must never repeat because this GET failed.
}
export function proposalSource(e: ProposalEvidence): SourceSelection {
  if (e.sourceKind === 'wiki' && e.pageId) return {sourceKind: 'wiki', pageId: e.pageId, revisionId: e.sourceRevisionId, title: e.title};
  if (e.sourceKind === 'document' && e.documentId) return {sourceKind: 'document', documentId: e.documentId, revisionId: e.sourceRevisionId, title: e.title};
  throw new Error('출처 식별자가 올바르지 않습니다.');
}
