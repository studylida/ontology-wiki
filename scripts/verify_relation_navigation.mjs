import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(resolve(root,'frontend/package.json'));
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),{transformSync}=require('esbuild');
function load(name,deps) {
  const module={exports:{}};
  const code=transformSync(readFileSync(resolve(root,name),'utf8'),{loader:name.endsWith('.jsx')?'jsx':'js',format:'cjs'}).code;
  vm.runInNewContext(code,{module,exports:module.exports,require:key=>{assert.ok(key in deps,key);return deps[key];}});
  return module.exports;
}
const {relationService}=load('frontend/src/services/relationService.js',{});
let tab='flow';
const {SectionRelations}=load('frontend/src/views/wiki/SectionRelations.jsx',{
  react:{...React,useState:()=>[tab,value=>tab=value]},
  'lucide-react':require('lucide-react'),'../../services/relationService':{relationService}
});
const keys=['isA','partOf','hasParts','subtypes','previousSteps','nextSteps','alternatives'];
const item=(key,registered)=>({id:key+(registered?'-registered':'-unregistered'),name:key+(registered?' 등록':' 미등록'),
  isRegistered:registered,reason:key+' 설명 <script>',scaleLevel:2,commonGoal:'공통 목적',tradeoff:'기존 한계'});
const concept={id:'center',title:'중심',enrichedRelations:Object.fromEntries(keys.map(key=>[key,[item(key,true),item(key,false)]])),
  scaleLadder:[{entityId:'center',title:'현재 개념',scaleLevel:2,isCurrent:true,hops:0,description:'현재 설명'},
    {entityId:'neighbor',title:'이웃',scaleLevel:2,hops:1,description:'규모 설명',connections:[]}]};
let chosen=[],drafts=[],compared=[];
const props={conceptDetail:concept,onSelectConcept:id=>chosen.push(id),onOpenNewConceptModal:value=>drafts.push(value),
  onNavigateComparison:(a,b)=>compared.push([a,b])};
const nodes=node=>node&&typeof node==='object'?[node,...React.Children.toArray(node.props?.children).flatMap(nodes)]:[];
const text=node=>typeof node==='string'?node:React.Children.toArray(node?.props?.children).map(text).join('');
const click=node=>{let stopped=false,prevented=false;node.props.onClick({stopPropagation(){stopped=true;},preventDefault(){prevented=true;}});return {stopped,prevented};};
let tree=SectionRelations(props),all=nodes(tree);
for(const key of keys) {
  const link=all.find(n=>n.type==='a'&&n.props.href===`#concept/${key}-registered`);
  assert.ok(link,key);assert.equal(click(link).stopped,true);assert.equal(chosen.at(-1),key+'-registered');
  assert.equal(all.some(n=>n.type==='a'&&n.props.href.includes(key+'-unregistered')),false);
  const card=all.find(n=>n.props['data-relation-block']!==undefined&&nodes(n).some(child=>child.type==='a'&&child.props.href===link.props.href));
  assert.ok(card.props.onClick);click(card);assert.equal(chosen.at(-1),key+'-registered');
}
const proposals=all.filter(n=>n.type==='button'&&text(n).includes('신규 지식 발의하기'));
assert.equal(proposals.length,keys.length);
for(const button of proposals) assert.equal(click(button).stopped,true);
assert.deepEqual(drafts.map(d=>d.title).sort(),keys.map(key=>key+' 미등록').sort());
assert.ok(drafts.every(d=>d.parentConceptId==='center'&&d.parentTitle==='중심'&&d.relationType==='next_step'&&d.reason.includes('설명')));
click(all.find(n=>n.type==='button'&&!n.props.disabled&&text(n).includes('A/B 비교')));
assert.deepEqual(compared,[['center','alternatives-registered']]);
const markup=renderToStaticMarkup(tree);
for(const key of keys.filter(key=>key!=='alternatives'))assert.ok(markup.includes(key+' 설명 &lt;script&gt;'));
assert.ok(markup.includes('공통 목적')&&markup.includes('기존 한계'));
assert.doesNotMatch(markup,/aria-haspopup|role="dialog"|popover=|상세 사유를 확인/);
click(all.find(n=>n.type==='button'&&text(n)==='규모별 연결 뷰'));
assert.equal(tab,'ladder');tree=SectionRelations(props);all=nodes(tree);
const neighbor=all.find(n=>n.type==='a'&&n.props.href==='#concept/neighbor');assert.ok(neighbor);click(neighbor);assert.equal(chosen.at(-1),'neighbor');
const current=all.find(n=>n.props['data-relation-block']!==undefined&&text(n).includes('현재 설명'));assert.equal(current.props.onClick,undefined);
assert.ok(renderToStaticMarkup(tree).includes('규모 설명'));
assert.equal(all.some(n=>n.type==='a'&&n.props.href==='#concept/center'),false);
for(const mode of ['flow','ladder']) {
  tab=mode;all=nodes(SectionRelations({conceptDetail:concept}));
  assert.equal(all.filter(n=>n.type==='a').length,0,'Preview has no inactive navigation links');
  assert.ok(all.filter(n=>n.props['data-relation-block']!==undefined).every(n=>!n.props.onClick));
  assert.equal(all.filter(n=>n.type==='button'&&text(n).includes('신규 지식 발의하기')).length,0);
}
tab='flow';const unchanged=JSON.stringify(concept);SectionRelations(props);assert.equal(JSON.stringify(concept),unchanged);
console.log('PASS: both relation views navigate directly; block descriptions remain; unregistered proposals and comparison remain; current card and read-only preview have no navigation; no duplicate popup');
