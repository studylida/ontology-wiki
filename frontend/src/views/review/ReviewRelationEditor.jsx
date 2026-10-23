import React from 'react';
import { Field, EvidenceSelect, RowActions } from './ReviewSectionEditor';
import { newEditorId, relationFields } from '../../services/reviewDraftService';
export function ReviewRelationEditor({draft,onChange}) {
  return <><p className="review-hint">직접 관계를 편집하면 관계망과 규모별 계층에 반영됩니다. 대상은 등록 개념 ID를 사용하세요. 상위 노드와 외부 연결은 파생 표시입니다.</p>
    {Object.entries(relationFields).map(([field,label])=>{
      const rows=draft[field], set=value=>onChange({...draft,[field]:value});
      const update=(i,key,v)=>set(rows.map((r,j)=>i===j?{...r,[key]:v}:r));
      return <section className="review-relation-group" key={field}><h4>{label}</h4>{rows.map((r,i)=><article className="review-edit-card" key={r.editorId}><header><strong>{label} {i+1}</strong><RowActions label={`${label} ${i+1}`} rows={rows} index={i} onChange={set}/></header>
        <label className="review-field"><span>등록 대상 개념</span><input aria-label={`${label} ${i+1} 대상 ID`} list="review-concept-options" value={(field==='alternatives'?r.targetId:r.id)||''} onChange={e=>update(i,field==='alternatives'?'targetId':'id',e.target.value)}/></label><p className="review-hint">{draft.conceptOptions?.find(c=>c.id===(field==='alternatives'?r.targetId:r.id))?.title || r.name || r.targetName || '등록 개념을 선택하세요.'}</p>
        {field==='alternatives'?<><Field label={`대안 기술 ${i+1} 공통 목적`} value={r.commonGoal} onChange={v=>update(i,'commonGoal',v)}/><Field label={`대안 기술 ${i+1} 트레이드오프`} value={r.tradeoff} multiline onChange={v=>update(i,'tradeoff',v)}/></>:<Field label={`${label} ${i+1} 관계 설명`} value={r.reason} multiline onChange={v=>update(i,'reason',v)}/>}
        <EvidenceSelect label={`${label} ${i+1} 연결 출처`} sources={draft.evidences} value={r.evidenceIds || []} onChange={v=>update(i,'evidenceIds',v)}/>
      </article>)}<button type="button" onClick={()=>set([...rows,{editorId:newEditorId(),...(field==='alternatives'?{targetId:'',targetName:'',commonGoal:'',tradeoff:''}:{id:'',name:'',reason:''}),evidenceIds:[]}])}>{label} 추가</button></section>;
    })}<datalist id="review-concept-options">{(draft.conceptOptions || []).map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</datalist></>;
}
