import type { ProposalSummary } from './wikiProposal';
export type DocumentWikiNotice = {documentId: string; revisionId: string; enabled: boolean; status: string;
  result: {reason?: string; warnings?: string[]; model?: string}; error: {code: string; message: string} | null;
  items: ProposalSummary[]};
