import { http } from './http';
import type { Proposal, ProposalSummary, ProposalCommand } from '../types/wikiProposal';
import type { WikiMutation } from '../types/wiki';
export const proposalRepository = {
  list: (pageId?: string, signal?: AbortSignal) => http<{items: ProposalSummary[]}>(`/wiki/proposals${pageId ? '?pageId=' + encodeURIComponent(pageId) : ''}`, {signal}),
  get: (id: string, signal?: AbortSignal) => http<Proposal>(`/wiki/proposals/${encodeURIComponent(id)}`, {signal}),
  execute: (command: ProposalCommand) => command.kind === 'submit' ? http<ProposalSummary>('/wiki/proposals', {method: 'POST', body: command.body}) :
    http<WikiMutation>(`/wiki/proposals/${encodeURIComponent(command.id)}/apply`, {method: 'POST', body: command.body}),
  dismiss: (id: string) => http<ProposalSummary>(`/wiki/proposals/${encodeURIComponent(id)}/dismiss`, {method: 'POST'}),
};
