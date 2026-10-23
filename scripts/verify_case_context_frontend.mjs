import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const requireFrontend = createRequire(resolve(root, 'frontend/package.json'));
const {transformSync} = requireFrontend('esbuild');
const React = requireFrontend('react');
const {renderToStaticMarkup} = requireFrontend('react-dom/server');
const compile = name => transformSync(readFileSync(resolve(root, name), 'utf8'), {format: 'cjs', loader: name.endsWith('.jsx') ? 'jsx' : 'js'}).code;
function load(name, dependencies, timers = {}) {
  const module = {exports: {}};
  vm.runInNewContext(compile(name), {module, exports: module.exports, console, ...timers, require: key => {
    assert.ok(key in dependencies, `Unexpected dependency: ${key}`);
    return dependencies[key];
  }});
  return module.exports;
}
const {CaseContextExplanation} = load('frontend/src/views/wiki/CaseContextExplanation.jsx', {react: React});
const saved = {basisHash: 'h1', content: {explanation: '<script>원문 수치를 풀어 쓴 설명</script>', background: '별도 배경 설명'}};
const html = (state, options = {}) => renderToStaticMarkup(React.createElement(CaseContextExplanation, {perspective: {contextExplanationState: state, contextExplanation: saved}, ...options}));
assert.match(html('ready'), /&lt;script&gt;/);
assert.doesNotMatch(html('ready'), /<script>/);
assert.match(html('ready'), /용어·배경 설명/);
assert.doesNotMatch(html('stale'), /원문 수치를 풀어/);
assert.equal(html('restricted'), '');
assert.match(html('missing'), /아직 준비되지/);
assert.doesNotMatch(html('missing'), /<button/);
assert.match(html('missing', {canGenerate: true}), /<button/);
assert.doesNotMatch(html('missing', {canGenerate: true, isPreview: true}), /<button/);
assert.match(html('missing', {isPreview: true}), /적용 후 해설이 생성/);
assert.match(html('generating', {canGenerate: true}), /disabled/);

const flush = async () => { for (let index = 0; index < 8; index += 1) await Promise.resolve(); };
const deferred = () => { let resolve; let reject; const promise = new Promise((yes, no) => {resolve = yes; reject = no;}); return {promise, resolve, reject}; };
const detail = (id, state = 'missing', hash = 'h1') => ({id, title: id, perspectives: [{id: `${id}-case`, contextExplanationBasisHash: hash, contextExplanationState: state}]});
function harness() {
  const slots = [];
  const effects = [];
  const timers = new Map();
  let cursor = 0;
  let timerId = 0;
  let output;
  let get = async id => detail(id);
  let post = async () => ({});
  let getCalls = 0;
  let postCalls = 0;
  const hooks = {
    useState(initial) { const index = cursor++; if (!(index in slots)) slots[index] = typeof initial === 'function' ? initial() : initial; return [slots[index], value => {slots[index] = typeof value === 'function' ? value(slots[index]) : value;}]; },
    useRef(initial) { const index = cursor++; return slots[index] ||= {current: initial}; },
    useCallback(callback) { return callback; },
    useMemo(callback) { return callback(); },
    useEffect(effect, deps) { const index = cursor++; const old = slots[index]; if (!old || deps.some((value, dep) => !Object.is(value, old.deps[dep]))) {effects.push(() => {old?.cleanup?.(); slots[index] = {deps, cleanup: effect()};});} }
  };
  const {useWikiController} = load('frontend/src/controllers/useWikiController.js', {
    react: hooks,
    '../repositories/conceptRepo': {conceptRepo: {getTree: async () => ({}), getConceptDetail: (...args) => {getCalls += 1; return get(...args);}, generateCaseContextExplanation: (...args) => {postCalls += 1; return post(...args);}}},
    '../repositories/authRepo': {authRepo: {}}, '../repositories/reviewRepo': {reviewRepo: {}}, '../services/authService': {authService: {checkL3Access: () => ({hasAccess: false})}},
    '../services/textSelectionService': {createSelectionMatcher: () => () => null}
  }, {setTimeout: callback => {timers.set(++timerId, callback); return timerId;}, clearTimeout: id => timers.delete(id)});
  return {
    render() {cursor = 0; output = useWikiController({initialConceptId: 'a', currentUser: {id: 'reviewer', level: 3}}); while (effects.length) effects.shift()(); return output;},
    get output() { return output; }, get timers() {return timers.size;}, get getCalls() {return getCalls;}, get postCalls() {return postCalls;},
    setGet(value) {get = value;}, setPost(value) {post = value;},
    async tick() {const entry = timers.entries().next().value; assert.ok(entry, 'Expected a polling timer'); timers.delete(entry[0]); await entry[1](); await flush(); this.render();},
    unmount() { for (const slot of slots) slot?.cleanup?.(); }
  };
}
async function mounted(state = 'missing') {const app = harness(); app.setGet(async id => detail(id, state)); app.render(); await flush(); app.render(); return app;}

const navigation = await mounted();
assert.equal(navigation.postCalls, 0, 'Page GET must not generate');
const pending = deferred();
navigation.setPost(() => pending.promise);
const generation = navigation.output.generateCaseContextExplanation('a-case');
await navigation.output.generateCaseContextExplanation('a-case');
assert.equal(navigation.postCalls, 1, 'Duplicate clicks must coalesce');
navigation.output.selectConcept('b'); await flush(); navigation.render();
pending.resolve({}); await generation; navigation.render();
assert.equal(navigation.output.conceptDetail.id, 'b', 'Late generation must not replace the new page');
assert.deepEqual(Object.keys(navigation.output.caseExplanationRequests), []);
navigation.unmount();

const revision = await mounted();
const old = deferred(); revision.setPost(() => old.promise);
const oldGeneration = revision.output.generateCaseContextExplanation('a-case');
revision.setGet(async id => detail(id, 'stale', 'h2'));
revision.output.refreshWiki(); await flush(); revision.render();
old.reject(new Error('old model failure')); await oldGeneration; revision.render();
assert.equal(revision.output.conceptDetail.perspectives[0].contextExplanationBasisHash, 'h2');
assert.deepEqual(Object.keys(revision.output.caseExplanationRequests), [], 'Old errors must not reach the new revision');
revision.unmount();

const failure = await mounted();
failure.setPost(async () => {throw new Error('model unavailable');});
await failure.output.generateCaseContextExplanation('a-case'); failure.render();
assert.equal(failure.output.conceptDetail.id, 'a');
assert.match(failure.output.caseExplanationRequests['a-case'].error, /잠시 후 다시/);
failure.unmount();

const polling = await mounted('generating');
assert.equal(polling.timers, 1);
polling.setGet(async id => detail(id, 'ready'));
await polling.tick();
assert.equal(polling.output.conceptDetail.perspectives[0].contextExplanationState, 'ready');
assert.equal(polling.timers, 0, 'Polling must stop after ready');
assert.equal(polling.postCalls, 0, 'Polling must only GET');
polling.unmount();

const bounded = await mounted('generating');
const initialCalls = bounded.getCalls;
for (let attempt = 0; attempt < 20; attempt += 1) await bounded.tick();
assert.equal(bounded.getCalls - initialCalls, 20);
assert.equal(bounded.timers, 0, 'Polling must have a finite budget');
bounded.unmount();
console.log('PASS: saved explanation rendering, escaped text, preview/restricted states, duplicate clicks, late responses, failure preservation, GET-only bounded polling');

const {relationService} = load('frontend/src/services/relationService.js', {});
function relationMarkup(tab, concept) {
  let state = 0;
  const react = {...React, useState: () => [state++ === 0 ? tab : null, () => {}]};
  const {SectionRelations} = load('frontend/src/views/wiki/SectionRelations.jsx', {react,
    'lucide-react': requireFrontend('lucide-react'), '../../services/relationService': {relationService}});
  return renderToStaticMarkup(React.createElement(SectionRelations, {conceptDetail: concept}));
}
const item = (id, name) => ({id, name, reason: name+'의 원문 사유', isRegistered: true, scaleLevel: 3});
const relationDetail = {id: 'center', title: '중심', enrichedRelations: {partOf: [item('parent-a','소속 A'),item('parent-b','소속 B')],
  isA: [item('kind-a','분류 A'),item('kind-b','분류 B')], hasParts: [item('child','구성 요소 C')],subtypes: [item('type','하위 종류 D')]},
  scaleLadder: [{entityId:'center',title:'중심',scaleLevel:3,hops:0,isCurrent:true,description:'정의',connections:[{id:'e',source:'child',target:'center',relationType:'part_of',mechanismLabel:'실제 소속 사유'}]},
    {entityId:'child',title:'구성 요소 C',scaleLevel:2,hops:1,description:'하위 설명',connections:[]}]};
const relationHtml = relationMarkup('flow',relationDetail);
for (const text of ['소속 A','소속 B','분류 A','분류 B','구성 요소 C','하위 종류 D']) assert.ok(relationHtml.includes(text),text);
const ladderHtml=relationMarkup('ladder',relationDetail);
assert.match(ladderHtml,/실제 소속 사유/);
assert.match(ladderHtml,/1단계 연결/);
assert.match(ladderHtml,/구성 요소 → 소속 대상/);
assert.doesNotMatch(ladderHtml,/5단 수직/);
console.log('PASS: all parent/type/component/subtype relations rendered; typed directed scale connections and hop counts');

// A relation-bearing concept must not be dominated by empty process/alternative panels.
assert.doesNotMatch(relationHtml,/등록된 선행 공정이 없습니다|등록된 후속 공정이 없습니다|등록된 기술적 대안이 없습니다/);
assert.ok(relationHtml.indexOf('상위 소속 대상') < relationHtml.indexOf('하위 종류'));
assert.match(relationHtml,/중심 → 소속 A/);
assert.match(relationHtml,/구성 요소 C → 중심/);
const emptyRelations=relationMarkup('flow',{id:'empty',title:'정의만 있는 개념',scaleLevel:1});
assert.match(emptyRelations,/아직 등록된 관계가 없습니다/);
assert.doesNotMatch(emptyRelations,/공정 전·후 연계 파이프라인/);
console.log('PASS: existing semantic relations prioritized; empty pipeline panels omitted; true empty state and directions retained');

// Local source step numbers are provenance, not a shared chronology across merged principles.
const {SectionPrinciples} = load('frontend/src/views/wiki/SectionPrinciples.jsx', {react: React,
  '../../services/formulaService': {formulaService: {renderFormula: formula => `<math>${formula}</math>`}}});
const principles = [
  {step: 1, title: '소자 집적', content: '정의와 연결'},
  {step: 1, title: '웨이퍼 위 형성', content: '다른 문헌의 원리'},
  {step: 1, title: '다층 미세 패턴', content: '<script>보존할 설명</script>', formula: 'a=b'},
  {step: 2, title: '집적의 효과', content: '공정 다음 단계가 아닌 효과 설명'}
];
const savedPrinciples=JSON.stringify(principles);
const principlesHtml=renderToStaticMarkup(React.createElement(SectionPrinciples,{principles}));
for (const entry of principles) assert.ok(principlesHtml.includes(entry.title),entry.title);
assert.doesNotMatch(principlesHtml,/Step \d/);
assert.match(principlesHtml,/&lt;script&gt;보존할 설명&lt;\/script&gt;/);
assert.match(principlesHtml,/<math>a=b<\/math>/);
assert.equal(JSON.stringify(principles),savedPrinciples);
assert.equal(renderToStaticMarkup(React.createElement(SectionPrinciples,{principles:[]})),'');

const {FacetTreeExplorer}=load('frontend/src/views/wiki/FacetTreeExplorer.jsx',{react:React,
  'lucide-react':requireFrontend('lucide-react'),'../../services/relationService':{relationService}});
const scaleTabsHtml=renderToStaticMarkup(React.createElement(FacetTreeExplorer,{navMode:'scale',activeScale:2}));
for (const scale of [1,2,3,4,5]) assert.ok(scaleTabsHtml.includes(relationService.getScaleLabel(scale)));
assert.doesNotMatch(scaleTabsHtml,/1nm|1μm|100m|1km|300mm/);
assert.match(relationService.getScaleLabel(2),/회로·패키지/);
assert.match(relationService.getScaleLabel(4),/설비·시스템·모듈/);
console.log('PASS: merged independent principles keep text/formulas without false Step chronology; scale navigation uses shared labels without invented length limits');
