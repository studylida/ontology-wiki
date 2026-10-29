import { useState } from 'react';
import { wikiRepository } from '../repositories/wikiRepository';
import { errorMessage } from '../repositories/http';
import type { WikiPage, WikiDetail } from '../types/wiki';
export function useWikiProposalTarget() {
  const [query,setQuery]=useState(''), [items,setItems]=useState<WikiPage[]>([]), [page,setPage]=useState<WikiDetail|null>(null);
  const [error,setError]=useState(''), [busy,setBusy]=useState(false);
  async function search() {setBusy(true);setError('');try{setItems((await wikiRepository.list(query,0)).items);}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  async function select(id:string) {setBusy(true);setError('');try{setPage(await wikiRepository.detail(id));}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  return {query,setQuery,items,page,error,busy,search,select,newPage:()=>setPage(null)};
}
