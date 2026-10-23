import React from 'react';
import { Field, EvidenceSelect, RowActions } from './ReviewSectionEditor';
import { newEditorId } from '../../services/reviewDraftService';
export function ReviewCaseEditor({draft,onChange,permissions}) {
  const rows=draft.perspectiveCases;
  const set=cases=>onChange({...draft,perspectiveCases:cases});
  const update=(i,key,value)=>set(rows.map((row,j)=>i===j?{...row,[key]:value}:row));
  return <><p className="review-hint">회사·제품·운영 조건이 구별되는 실제 사례를 작성하세요. 자료에 없는 값이나 여유도를 만들지 마세요.</p>
    {rows.map((row,i)=>{
      const locked=row.isMasked&&!permissions.canEditConfidential;
      const spec=(index,key,value)=>update(i,'specifications',row.specifications.map((s,j)=>index===j?{...s,[key]:value}:s));
      return <details className="review-edit-card" key={row.editorId} open={i===0 || row.isNew}><summary>사례 {i+1} · {row.perspectiveTitle || '새 공개 사례'}</summary><header><strong>사례 {i+1}</strong><RowActions label={`사례 ${i+1}`} rows={rows} index={i} onChange={set} disabled={locked}/></header>
        <Field label={`사례 ${i+1} 제목`} value={row.perspectiveTitle} onChange={v=>update(i,'perspectiveTitle',v)}/><Field label={`사례 ${i+1} 구분`} value={row.perspectiveBadge} onChange={v=>update(i,'perspectiveBadge',v)}/>
        {locked&&<p>기밀이 포함된 사례 설명은 열람 승인 후 편집할 수 있습니다.</p>}
        <Field label={`사례 ${i+1} 설명`} value={row.narrative} multiline disabled={locked} onChange={v=>update(i,'narrative',v)}/><Field label={`사례 ${i+1} 주의사항`} value={row.caution} multiline disabled={locked} onChange={v=>update(i,'caution',v)}/>
        <EvidenceSelect single disabled={locked} label={`사례 ${i+1} 연결 출처`} sources={draft.evidences} value={row.evidenceId} onChange={v=>update(i,'evidenceId',v)}/>
        <h4>파라미터</h4>{row.specifications.map((s,j)=><details className="review-spec" key={s.editorId} open={s.isNew}><summary>{s.parameter || `새 파라미터 ${j+1}`} · {s.isConfidential?'기밀':'공개'}</summary>
          {s.readOnly?<p>열람 승인 필요 · 기존 값은 보존됩니다.</p>:<><RowActions label={`사례 ${i+1} 파라미터 ${j+1}`} rows={row.specifications} index={j} disabled={locked} onChange={v=>update(i,'specifications',v)}/>
            {Object.entries({parameter:'명칭',value:'값',unit:'단위',safetyMargin:'여유도',role:'역할',tradeoff:'트레이드오프',rationale:'이유'}).map(([key,label])=><Field key={key} label={`사례 ${i+1} 파라미터 ${j+1} ${label}`} value={s[key]} onChange={v=>spec(j,key,v || (key==='parameter'?'':null))}/>)}
            <label className="review-field"><span>공개 범위</span><select aria-label={`사례 ${i+1} 파라미터 ${j+1} 공개 범위`} disabled={s.isNew?!permissions.canEditConfidential:!permissions.canChangeConfidentiality} value={s.isConfidential?'private':'public'} onChange={e=>spec(j,'isConfidential',e.target.value==='private')}><option value="public">공개</option><option value="private">기밀</option></select></label>
            <EvidenceSelect label={`사례 ${i+1} 파라미터 ${j+1} 연결 출처`} sources={draft.evidences} value={s.evidenceIds || []} onChange={v=>spec(j,'evidenceIds',v)}/>
          </>}
        </details>)}<button type="button" onClick={()=>update(i,'specifications',[...row.specifications,{editorId:newEditorId(),parameter:'',value:null,unit:null,safetyMargin:null,role:null,tradeoff:null,rationale:null,isConfidential:false,isNew:true,evidenceIds:[]}])}>사례 {i+1} 공개 파라미터 추가</button>
      </details>;
    })}<button type="button" onClick={()=>set([...rows,{editorId:newEditorId(),isNew:true,perspectiveTitle:'',perspectiveBadge:'',narrative:'',caution:'',evidenceId:null,specifications:[]}])}>공개 사례 추가</button></>;
}
