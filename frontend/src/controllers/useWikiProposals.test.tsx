// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach,beforeEach,expect,it,vi } from 'vitest';
import { useWikiProposals } from './useWikiProposals';
import { proposalRepository } from '../repositories/wikiProposalRepository';
import { ApiError } from '../repositories/http';
import { clearWorkspace } from '../repositories/workspaceStorage';
import type { Proposal } from '../types/wikiProposal';
vi.mock('../repositories/wikiProposalRepository',()=>({proposalRepository:{list:vi.fn(),execute:vi.fn(),get:vi.fn(),dismiss:vi.fn()}}));
vi.mock('../repositories/wikiRepository',()=>({guardWikiUnload:()=>()=>{}}));
const ready={id:'proposal-1',status:'ready',mode:'create',base:{},canApply:true,result:{title:'RUL',markdown:'draft'},error:null} as Proposal;
beforeEach(()=>{sessionStorage.clear();vi.clearAllMocks();vi.mocked(proposalRepository.list).mockResolvedValue({items:[]});vi.mocked(proposalRepository.get).mockResolvedValue(ready);});
afterEach(cleanup);
it('unknown submission is recovered without automatic POST and resends the exact command',async()=>{
 const hook=renderHook(()=>useWikiProposals('alice',null));
 act(()=>hook.result.current.setInstruction('Make RUL'));
 vi.mocked(proposalRepository.execute).mockRejectedValueOnce(new ApiError(0,'NETWORK_UNAVAILABLE','unknown'));
 act(()=>hook.result.current.submit());await waitFor(()=>expect(hook.result.current.busy).toBe(false));
 expect(hook.result.current.pending).not.toBeNull();const command=vi.mocked(proposalRepository.execute).mock.calls[0][0];hook.unmount();
 const recovered=renderHook(()=>useWikiProposals('alice',null));
 expect(proposalRepository.execute).toHaveBeenCalledTimes(1);
 vi.mocked(proposalRepository.execute).mockResolvedValueOnce(ready);
 act(()=>recovered.result.current.resend());await waitFor(()=>expect(recovered.result.current.pending).toBeNull());
 expect(vi.mocked(proposalRepository.execute).mock.calls[1][0]).toEqual(command);
 clearWorkspace('alice');expect(sessionStorage.length).toBe(0);
});
it('conflict keeps the edited review text and blocks apply until a new proposal',async()=>{
 const hook=renderHook(()=>useWikiProposals('alice',null));await act(()=>hook.result.current.open('proposal-1'));
 act(()=>hook.result.current.change('markdown','employee-reviewed text'));
 vi.mocked(proposalRepository.execute).mockRejectedValueOnce(new ApiError(409,'wiki_version_conflict','changed'));
 vi.mocked(proposalRepository.get).mockResolvedValue({...ready,stale:true,canApply:false});
 act(()=>hook.result.current.apply());await waitFor(()=>expect(hook.result.current.busy).toBe(false));
 expect(hook.result.current.draft?.markdown).toBe('employee-reviewed text');expect(hook.result.current.selected?.canApply).toBe(false);
 expect(hook.result.current.pending).toBeNull();
});
it('does not restore another employees pending data',async()=>{
 const hook=renderHook(()=>useWikiProposals('alice',null));act(()=>hook.result.current.setInstruction('private'));
 vi.mocked(proposalRepository.execute).mockRejectedValueOnce(new ApiError(0,'NETWORK_UNAVAILABLE','unknown'));
 act(()=>hook.result.current.submit());await waitFor(()=>expect(hook.result.current.pending).not.toBeNull());
 const other=renderHook(()=>useWikiProposals('bob',null));expect(other.result.current.pending).toBeNull();
});
