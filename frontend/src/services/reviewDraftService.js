export const reviewSections = [
  ['summary', '개요·목적'], ['principles', '작동 원리'], ['limitations', '한계·트레이드오프'],
  ['perspectiveCases', '사례·파라미터'], ['relations', '관계·계층'], ['evidences', '출처']
];
export const relationFields = { previousSteps:'이전 공정', nextSteps:'다음 공정', alternatives:'대안 기술', partOf:'구성 소속', isA:'종류·상위 개념' };
const fields = {
  principles:['title','content','formula','evidenceIds'], limitations:['title','description','evidenceIds'],
  perspectiveCases:['perspectiveTitle','perspectiveBadge','narrative','caution','evidenceId'],
  specifications:['parameter','value','unit','safetyMargin','role','tradeoff','rationale','isConfidential','evidenceIds'],
  evidences:['sourceName','publisher','quote','externalUrl'],
  relations:['id','name','targetId','targetName','reason','commonGoal','tradeoff','evidenceIds']
};
export const newEditorId = () => crypto.randomUUID();
export function equal(a,b) {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false;
  const keys = Object.keys(a);
  return keys.length === Object.keys(b).length && keys.every(k => Object.hasOwn(b,k) && equal(a[k],b[k]));
}
function rows(before=[],after=[],field) {
  const upsert=[];
  for (const row of after) {
    const old=before.find(r=>r.editorId===row.editorId);
    const patch={editorId:row.editorId};
    if(field==='evidences' && !old && row.existingId) {upsert.push({...patch,existingId:row.existingId});continue;}
    for(const key of fields[field] || fields.relations) {
      if(Object.hasOwn(row,key) && (!old || !equal(old[key],row[key]))) patch[key]=row[key];
    }
    if(field==='perspectiveCases') {
      const specs=rows(old?.specifications,row.specifications,'specifications');
      if(Object.keys(specs).length) patch.specifications=specs;
    }
    if(Object.keys(patch).length>1) upsert.push(patch);
  }
  const remove=before.filter(r=>!after.some(a=>a.editorId===r.editorId)).map(r=>r.editorId);
  const order=after.map(r=>r.editorId), oldOrder=before.map(r=>r.editorId).filter(id=>!remove.includes(id));
  const appended=[...oldOrder,...after.filter(r=>!before.some(b=>b.editorId===r.editorId)).map(r=>r.editorId)];
  return {...(upsert.length?{upsert}:{}),...(remove.length?{remove}:{}),...(!equal(order,appended)?{order}: {})};
}
export function draftChanges(saved,working) {
  if(!saved || !working) return {};
  const changes={};
  for(const key of ['summary','purpose']) if(saved[key]!==working[key]) changes[key]=working[key];
  for(const key of ['principles','limitations','perspectiveCases',...Object.keys(relationFields),'evidences']) {
    const changed=rows(saved[key],working[key],key);
    if(Object.keys(changed).length) changes[key]=changed;
  }
  return changes;
}

export function removedCitations(before,after) {
  const tags=value=>new Set((`${value?.summary || ''}\n${value?.purpose || ''}`.match(/\[E-[A-Za-z0-9_.:/-]+\]/gi)||[]).map(v=>v.slice(1,-1)));
  const previous=tags(before), current=tags(after);
  for(const e of before?.evidences || []) if(/^E-/i.test(e.id) && !after.evidences.some(v=>v.id===e.id)) previous.add(e.id);
  return [...previous].filter(id=>!current.has(id));
}
