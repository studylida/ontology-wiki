import { describe, expect, it, vi } from 'vitest';
import { executeProposal, proposalDraft, proposalSource } from './wikiProposalService';
import { proposalRepository } from '../repositories/wikiProposalRepository';
import type { Proposal, ProposalPending } from '../types/wikiProposal';
vi.mock('../repositories/wikiProposalRepository',()=>({proposalRepository:{execute:vi.fn(),get:vi.fn()}}));
const p={id:'p1',status:'ready',base:{title:'original'},result:{markdown:'proposed'}} as Proposal;
describe('proposal review contracts',()=>{
 it('keeps shared metadata and draft text separate from the request',()=>{expect(proposalDraft(p)).toMatchObject({title:'original',markdown:'proposed',sourceNote:''});});
 it('retries only GET when a write receipt is already known',async()=>{
  vi.mocked(proposalRepository.get).mockResolvedValue(p);
  const value={command:{kind:'submit',body:{requestId:'request-123',mode:'create',instruction:'do it'}},receipt:{id:'p1'}} as ProposalPending;
  await executeProposal(value,()=>{});expect(proposalRepository.execute).not.toHaveBeenCalled();
  expect(proposalRepository.get).toHaveBeenCalledWith('p1');
 });
 it('acknowledges before readback so a failed read cannot cause another write',async()=>{
  vi.mocked(proposalRepository.execute).mockResolvedValue({id:'p1'} as never);
  vi.mocked(proposalRepository.get).mockRejectedValue(new Error('unavailable'));
  const saved=vi.fn();
  await expect(executeProposal({command:{kind:'submit',body:{requestId:'request-124',mode:'create',instruction:'do it'}},receipt:null},saved)).rejects.toThrow();
  expect(saved).toHaveBeenCalledWith({id:'p1'});
 });
 it('never invents a document identity for a wiki source',()=>{
  expect(proposalSource({sourceKind:'wiki',pageId:'wp1',sourceRevisionId:'wr1',passageId:'ps',title:'t',locator:'l',text:'x'})).toEqual({sourceKind:'wiki',pageId:'wp1',revisionId:'wr1',title:'t'});
 });
});
