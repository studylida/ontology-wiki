import assert from 'node:assert/strict';
import {readFileSync, mkdtempSync, rmSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname, resolve, join, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import vm from 'node:vm';

const root=resolve(dirname(fileURLToPath(import.meta.url)), '..');
const requireFrontend=createRequire(resolve(root,'frontend/package.json'));
const {transformSync,build}=requireFrontend('esbuild');
const React=requireFrontend('react');
const {renderToStaticMarkup}=requireFrontend('react-dom/server');
function load(path, dependencies) {
  const module={exports:{}};
  const code=transformSync(readFileSync(resolve(root,path),'utf8'),{format:'cjs',loader:path.endsWith('jsx')?'jsx':'js'}).code;
  vm.runInNewContext(code,{module,exports:module.exports,console,require:name=>{assert.ok(name in dependencies,name);return dependencies[name];}});
  return module.exports;
}
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const deferred=()=>{let resolve;const promise=new Promise(yes=>resolve=yes);return {promise,resolve};};
const axis=label=>({axisId:label,label,category:'purpose',categoryLabel:'목적별 평가',terms:[label]});
const draft={targetAName:'MR-MUF',targetBName:'TC-NCF',purpose:'열 영향과 휨 비교',applicationContext:'HBM 적층',axes:[axis('열 영향'),axis('휨')]};
const plan={recognizedIntent:'original',targetA:'a',targetB:null,draft,dynamicAxesPool:draft.axes,clarificationQuestions:[],branches:[]};
function harness() {
  const slots=[],effects=[];let cursor=0,output;
  let clarify=async()=>plan,start=async body=>({id:'cmp',query:body.query,contextParams:{...body},snapshots:[{},{},{matrix:body.axes.map(a=>({axis:a.label,axisCategory:'purpose'}))}]});
  const calls=[],navigation=[];
  const hooks={useState(initial){const i=cursor++;if(!(i in slots))slots[i]=initial;return [slots[i],value=>slots[i]=typeof value==='function'?value(slots[i]):value];},useRef(value){const i=cursor++;return slots[i]||=({current:value});},useCallback(value){return value;},useMemo(fn){return fn();},useEffect(effect,deps){const i=cursor++;const old=slots[i];if(!old||deps.some((value,n)=>!Object.is(value,old.deps[n])))effects.push(()=>{old?.cleanup?.();slots[i]={deps,cleanup:effect()};});}};
  const {useComparisonController}=load('frontend/src/controllers/useComparisonController.js',{
    react:hooks,'../repositories/comparisonRepo':{comparisonRepo:{listConcepts:async()=>[{id:'a',title:'MR-MUF'},{id:'b',title:'TCB'}],clarify:body=>{calls.push(body);return clarify(body);}}},
    '../services/comparisonService':{comparisonService:{start:body=>{calls.push(body);return start(body);},sessionView:session=>({matrix:session.snapshots[2].matrix||[],history:[],evidences:[]})}}
  });
  return {render(){cursor=0;output=useComparisonController({onNavigateToTab:(...args)=>navigation.push(args)});while(effects.length)effects.shift()();return output;},get output(){return output;},calls,navigation,setClarify(fn){clarify=fn;},setStart(fn){start=fn;}};
}
const app=harness();app.render();await tick();app.render();
await app.output.handleClarifyQuery('original');app.render();
assert.equal(app.output.targetA,'a');assert.equal(app.output.targetB,'');assert.equal(app.output.draft.targetBName,'TC-NCF');assert.equal(app.output.domain,'HBM 적층');
app.output.handleApplyDraft();app.render();assert.equal(app.output.trackMode,'track2');assert.equal(app.output.draft.purpose,draft.purpose);
app.output.setAnswer('constraint','same thickness');app.render();
await app.output.handleConfirmTargets();app.render();
assert.equal(app.calls.at(-1).query,'original');assert.equal(app.calls.at(-1).answers.constraint,'same thickness');
assert.equal(app.calls.at(-1).draft.targetBName,'TC-NCF');assert.equal(app.calls.at(-1).draft.applicationContext,'HBM 적층');
app.output.setTargetB('b');app.render();assert.equal(app.output.draft.targetBName,'TC-NCF','An explicit wiki link must not rewrite the original target expression');
app.output.setDraftField('targetBName','새 기술');app.render();assert.equal(app.output.targetB,'');
app.output.setDraftField('purpose','edited purpose');app.render();assert.equal(app.output.selectedAxes.length,0,'Changing the purpose invalidates prior suggested axes');
app.output.setCustomAxisText('사용자 축');app.render();
app.output.handleNavigateToResearch();assert.equal(app.navigation.at(-1)[0],'research');assert.match(app.navigation.at(-1)[1].query,/새 기술/);assert.ok(!app.navigation.at(-1)[1].comparisonContext,'Draft research must not invent a comparison session ID');
app.setClarify(async()=>{throw new Error('synthetic offline');});await app.output.handleConfirmTargets();app.render();
assert.equal(app.output.draft.purpose,'edited purpose');assert.equal(app.output.customAxisText,'사용자 축');assert.equal(app.output.query,'original');assert.equal(app.output.isClarifying,false);
app.setClarify(async body=>({...plan,draft:body.draft,dynamicAxesPool:body.draft.axes,generationStatus:'model_unavailable'}));
await app.output.handleConfirmTargets();app.render();assert.equal(app.output.draft.targetBName,'새 기술');assert.equal(app.output.selectedAxes[0].label,'사용자 축');
const late=deferred();app.setClarify(()=>late.promise);
const pending=app.output.handleConfirmTargets();app.render();app.output.setDraftField('purpose','new purpose');app.render();assert.equal(app.output.isClarifying,false);
late.resolve(plan);await pending;app.render();assert.equal(app.output.draft.purpose,'new purpose');
app.setClarify(async()=>plan);await app.output.handleClarifyQuery('original');app.render();app.output.setTargetB('b');app.render();
const creation=deferred();app.setStart(()=>creation.promise);
const starting=app.output.handleStartDirectComparison();await tick();app.render();assert.equal(app.output.isMatrixLoading,true);
app.output.setDraftField('purpose','replacement purpose');app.render();assert.equal(app.output.isMatrixLoading,false);
creation.resolve({query:'old',contextParams:{targetA:'a',targetB:'b',axes:[]},snapshots:[{},{},{matrix:[]}]});await starting;app.render();assert.equal(app.output.activeStep,'setup');
app.output.setTrackMode('track1');app.render();app.output.setQuery('different question');app.render();assert.equal(app.output.clarifyResult,null);assert.equal(app.output.targetA,'');assert.equal(app.output.draft.targetBName,'');
const direct=harness();direct.render();await tick();direct.render();
direct.setClarify(async()=>({...plan,draft:{...draft,purpose:'자동 구체화한 목적'},targetB:'b'}));
await direct.output.handleDirectCompare('a','b','원래 질문');direct.render();
assert.equal(direct.calls.at(-1).draft.purpose,'자동 구체화한 목적');assert.equal(direct.output.domain,'HBM 적층');
direct.setStart(async()=>({query:'legacy original',contextParams:{targetA:'a',targetB:'b',targetAName:'MR-MUF',targetBName:'TCB',draft:{purpose:''},axes:[],clarificationAnswers:{constraint:'restored'}},snapshots:[{},{},{matrix:[]}]}));
await direct.output.handleDirectCompare('a','b','legacy original');direct.render();
assert.equal(direct.output.draft.purpose,'legacy original');assert.equal(direct.output.answers.constraint,'restored');

const {ConceptSearch}=load('frontend/src/views/comparison/ConceptSearch.jsx',{react:React});
const icon=()=>null;
const {ComparisonHeaderBar}=load('frontend/src/views/comparison/ComparisonHeaderBar.jsx',{react:React,'lucide-react':{ArrowLeft:icon,RotateCcw:icon,GitCompare:icon,Tag:icon}});
const header=renderToStaticMarkup(React.createElement(ComparisonHeaderBar,{currentSession:{query:'원래 열 영향 질문',contextParams:{draft:{purpose:'수정한 수율 목적'}}}}));
assert.match(header,/비교 목적: 수정한 수율 목적/);assert.match(header,/원래 질문: 원래 열 영향 질문/);
const {SetupTrackSelector}=load('frontend/src/views/comparison/SetupTrackSelector.jsx',{react:React,'./ConceptSearch':{ConceptSearch}});
const noop=()=>{};
const setup=renderToStaticMarkup(React.createElement(SetupTrackSelector,{trackMode:'track2',query:'original',draft,domain:'HBM 적층',targetA:'a',targetB:'',concepts:[{id:'a',title:'MR-MUF'}],axisCandidates:draft.axes,selectedAxes:draft.axes,onDraftFieldChange:noop,onResearch:noop,onConfirmTargets:noop}));
assert.match(setup,/value="TC-NCF"/);assert.match(setup,/HBM 적층/);assert.match(setup,/열 영향과 휨 비교/);
assert.match(setup,/<button type="button">이 초안으로 문헌 조사<\/button>/);
assert.match(setup,/<button[^>]*disabled=""[^>]*>위키 근거로 비교 시작<\/button>/);

const temp=mkdtempSync(join(tmpdir(),'comparison-markdown-'));
try {
  await build({entryPoints:[resolve(root,'frontend/src/views/comparison/ComparisonMarkdown.jsx')],outfile:join(temp,'markdown.cjs'),bundle:true,platform:'node',format:'cjs',plugins:[{name:'shared-react',setup(build){build.onResolve({filter:/^react$/},()=>({path:requireFrontend.resolve('react'),external:true}));}}]});
  const {ComparisonMarkdown,evidenceHref,evidenceAnchor,openEvidence}=requireFrontend(join(temp,'markdown.cjs'));
  let prevented=false,scrolled=false;
  const details={open:false};
  globalThis.document={getElementById(id){assert.equal(id,evidenceAnchor('E-한글/QA'));return {closest:()=>details,scrollIntoView(){scrolled=true;}};}};
  openEvidence({preventDefault(){prevented=true;}},'E-한글/QA');
  assert.ok(prevented && scrolled && details.open,'Citation navigation must open its source without changing the application hash');
  delete globalThis.document;
  const markdown='## 비교 목적\n\n**강조**\n\n- 목록\n\n| 항목 | 상태 |\n| --- | --- |\n| 휨 | 확인 필요 |\n\n[E-QA] [unknown]\n\n`[E-QA]`\n\n<script>alert(1)</script>\n\n[unsafe](javascript:alert%281%29) ![pixel](https://example.invalid/pixel)';
  const html=renderToStaticMarkup(React.createElement(ComparisonMarkdown,{evidences:[{id:'E-QA'}]},markdown));
  assert.match(html,/<h2>비교 목적<\/h2>/);assert.match(html,/<strong>강조<\/strong>/);assert.match(html,/<table>/);assert.match(html,/<li>목록<\/li>/);
  assert.ok(html.includes('href="'+evidenceHref('E-QA')+'"'));assert.match(html,/<code>\[E-QA\]<\/code>/);assert.ok(html.includes('[unknown]'));
  assert.doesNotMatch(html,/<script|javascript:|<img/);
  const {ConceptSearch}=load('frontend/src/views/comparison/ConceptSearch.jsx',{react:React});
  const selected=renderToStaticMarkup(React.createElement(ConceptSearch,{label:'비교 대상 A',value:'mr-muf',concepts:[{id:'mr-muf',title:'매스 리플로우',engName:'Mass Reflow',aliases:[]}],onChange(){}}));
  assert.match(selected,/role="combobox"/);assert.match(selected,/aria-autocomplete="list"/);assert.match(selected,/매스 리플로우/);
} finally {assert.ok(resolve(temp).startsWith(resolve(tmpdir())+sep));rmSync(temp,{recursive:true,force:true});}
console.log('PASS Agent draft fields, unknown targets, direct form/research transfer, user edits, missing-only answers, stale responses/loading and existing Markdown/search safety');
