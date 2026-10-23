import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(resolve(root,'frontend/package.json'));
const {transformSync}=require('esbuild');
const React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');
function load(name,deps,globals={}) {
  const module={exports:{}};
  const code=transformSync(readFileSync(resolve(root,name),'utf8'),{format:'cjs',loader:name.endsWith('.jsx')?'jsx':'js'}).code;
  vm.runInNewContext(code,{module,exports:module.exports,console,URLSearchParams,...globals,require:key=>{assert.ok(key in deps,key);return deps[key];}});
  return module.exports;
}
let requested;
const {conceptRepo}=load('frontend/src/repositories/conceptRepo.js',{'./httpClient':{httpClient:{get:url=>{requested=url;}}}});
await conceptRepo.search('MR-MUF & 본딩');
assert.equal(new URL('http://local'+requested).searchParams.get('q'),'MR-MUF & 본딩');
const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};};
const slots=[],effects=[],timers=new Map();let cursor=0,nextTimer=0,search,output,calls=[];
const hooks={
  useState(value){const index=cursor++;if(!(index in slots))slots[index]=value;return[slots[index],next=>{slots[index]=typeof next==='function'?next(slots[index]):next;}];},
  useCallback(fn){return fn;},
  useEffect(fn,deps){const index=cursor++;const previous=slots[index];if(!previous||deps.some((v,i)=>!Object.is(v,previous.deps[i])))effects.push(()=>{previous?.cleanup?.();slots[index]={deps,cleanup:fn()};});}
};
const {useTopBarController}=load('frontend/src/controllers/useTopBarController.js',{react:hooks,'../repositories/conceptRepo':{conceptRepo:{search:q=>{calls.push(q);return search(q);}}}},
 {window:{addEventListener(){},removeEventListener(){}},setTimeout:fn=>{timers.set(++nextTimer,fn);return nextTimer;},clearTimeout:id=>timers.delete(id)});
function render(){cursor=0;output=useTopBarController();while(effects.length)effects.shift()();return output;}
async function tick(){const [id,fn]=timers.entries().next().value;timers.delete(id);const running=fn();await flush();return running;}
render();assert.equal(calls.length,0);
const suggestion=deferred();search=()=>suggestion.promise;
output.openSearch();render();const first=tick();
suggestion.resolve({results:[{id:'registered-a',title:'공개 A'}],totalIndexed:494});await first;render();
assert.equal(output.searchResults[0].id,'registered-a');assert.equal(output.totalIndexed,494);
const old=deferred();search=()=>old.promise;
output.setSearchTerm('old');render();const oldRun=tick();
output.setSearchTerm('new');render();assert.equal(output.searchResults.length,0);
search=async()=>({results:[{id:'registered-new'}],totalIndexed:494});await tick();render();
old.resolve({results:[{id:'wrong-old'}],totalIndexed:494});await oldRun;render();
assert.equal(output.searchResults[0].id,'registered-new');
const closed=deferred();search=()=>closed.promise;
output.setSearchTerm('closed');render();const pending=tick();output.closeSearch();render();
closed.resolve({results:[{id:'wrong-closed'}],totalIndexed:494});await pending;render();
assert.equal(output.searchResults.length,0);assert.equal(output.searchTerm,'');
output.openSearch();render();search=async()=>{throw new Error('unavailable');};await tick();render();
assert.ok(output.searchError);assert.equal(output.searchResults.length,0);
const {DOMAIN_FACET_LABELS}=load('frontend/src/types/concept.dto.js',{});
const {relationService}=load('frontend/src/services/relationService.js',{});
const {SpotlightModal}=load('frontend/src/views/SpotlightModal.jsx',{react:React,'lucide-react':require('lucide-react'),'../types/concept.dto':{DOMAIN_FACET_LABELS},'../services/relationService':{relationService}});
const markup=props=>renderToStaticMarkup(React.createElement(SpotlightModal,{isOpen:true,...props}));
const html=markup({results:[{id:'registered-a',title:'<공개 A>',domainFacet:'device',scaleLevel:2}],totalIndexed:494});
assert.match(html,/&lt;공개 A&gt;/);assert.doesNotMatch(html,/concept-cryo-etch|concept-tcb|Cryo-ALE/);
assert.match(html,/등록 개념 494개/);assert.match(html,/<button/);
assert.match(markup({error:'조회 실패'}),/role="alert"/);
assert.doesNotMatch(markup({isLoading:true,results:[{id:'stale',title:'오래된 결과'}]}),/오래된 결과/);
console.log('PASS: real registered suggestions/search, query encoding, debounce/late/closed/error isolation, accessible escaped result buttons, no sample links');
