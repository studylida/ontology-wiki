import React from 'react';
import { newEditorId } from '../../services/reviewDraftService';
import { ReviewCaseEditor } from './ReviewCaseEditor';
import { ReviewRelationEditor } from './ReviewRelationEditor';
import { ReviewEvidenceEditor } from './ReviewEvidenceEditor';

export function Field({label,value,onChange,multiline=false,disabled=false}) {
  const props={value:value ?? '',onChange:e=>onChange(e.target.value),disabled,'aria-label':label};
  return <label className="review-field"><span>{label}</span>{multiline?<textarea {...props} rows={4}/>:<input {...props}/>}</label>;
}
export function EvidenceSelect({sources=[],value=[],onChange,label='연결 출처',disabled=false,single=false}) {
  return <label className="review-field"><span>{label}</span><select aria-label={label} disabled={disabled} multiple={!single} value={single?(value || ''):value} onChange={e=>onChange(single?(e.target.value||null):Array.from(e.target.selectedOptions).map(o=>o.value))}>
    {single&&<option value="">근거 미연결</option>}{sources.map(s=><option key={s.editorId} value={s.id}>{s.sourceName} · {s.id}</option>)}
  </select><small>연결한 자료가 내용을 지지하는지 미리보기에서 확인하세요.</small></label>;
}
export function RowActions({index,rows,onChange,disabled=false,label='항목'}) {
  const move=delta=>{const next=[...rows];[next[index],next[index+delta]]=[next[index+delta],next[index]];onChange(next);};
  return <div className="review-row-actions"><button type="button" disabled={disabled||index===0} aria-label={`${label} 위로`} onClick={()=>move(-1)}>위로</button><button type="button" disabled={disabled||index===rows.length-1} aria-label={`${label} 아래로`} onClick={()=>move(1)}>아래로</button><button type="button" disabled={disabled} aria-label={`${label} 삭제`} onClick={()=>onChange(rows.filter((_,i)=>i!==index))}>삭제</button></div>;
}
export function ReviewSectionEditor({section,draft,onChange,permissions}) {
  const set=(key,value)=>onChange({...draft,[key]:value});
  if(section==='summary') return <><Field label="개요 및 기술 정의" value={draft.summary} onChange={v=>set('summary',v)} multiline/><Field label="도입 목적" value={draft.purpose} onChange={v=>set('purpose',v)} multiline/><p className="review-hint">직접 수정한 내용은 자동으로 근거 검증된 내용이 되지 않습니다.</p></>;
  if(section==='perspectiveCases') return <ReviewCaseEditor draft={draft} onChange={onChange} permissions={permissions}/>;
  if(section==='relations') return <ReviewRelationEditor draft={draft} onChange={onChange}/>;
  if(section==='evidences') return <ReviewEvidenceEditor draft={draft} onChange={onChange}/>;
  const principle=section==='principles', rows=draft[section] || [];
  const label=principle?'원리':'한계';
  const update=(i,key,v)=>set(section,rows.map((r,j)=>j===i?{...r,[key]:v}:r));
  return <><p className="review-hint">{principle?'현재 대상 자체의 작동 원리를 작성하세요. 인접 공정 설명과 구분합니다.':'발생 조건과 물리적 한계, 상충하는 특성을 자료 범위 안에서 작성하세요.'}</p>
    {rows.map((row,i)=><article className="review-edit-card" key={row.editorId}><header><strong>{label} {i+1}</strong><RowActions index={i} rows={rows} onChange={v=>set(section,v)} label={`${label} ${i+1}`}/></header>
      <Field label={`${label} ${i+1} 제목`} value={row.title} onChange={v=>update(i,'title',v)}/><Field label={`${label} ${i+1} 설명`} value={principle?row.content:row.description} multiline onChange={v=>update(i,principle?'content':'description',v)}/>
      {principle&&<Field label={`원리 ${i+1} 수식`} value={row.formula} onChange={v=>update(i,'formula',v||null)}/>}
      <EvidenceSelect label={`${label} ${i+1} 연결 출처`} sources={draft.evidences} value={row.evidenceIds || []} onChange={v=>update(i,'evidenceIds',v)}/>
    </article>)}<button type="button" onClick={()=>set(section,[...rows,{editorId:newEditorId(),title:'',...(principle?{content:'',formula:null}:{description:''}),evidenceIds:[]}])}>{label} 추가</button></>;
}
