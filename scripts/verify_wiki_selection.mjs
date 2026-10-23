// Use --matcher-only for pure checks; full browser checks need Playwright via NODE_PATH.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { performance } from 'node:perf_hooks';
import { createSelectionMatcher } from '../frontend/src/services/textSelectionService.js';

const match = createSelectionMatcher(['D램', 'DRAM', '본딩', '열압착 본딩', '전이', '차이', 'SiO₂', 'TC-NCF', 'A+B']);
for (const [text, offset, expected] of [
  ['D램을', 2, 'D램'], ['열압착 본딩에서는', 8, '열압착 본딩'], ['dram은', 4, 'dram'],
  ['전이', 1, '전이'], ['차이는', 2, '차이'], ['SiO₂에서', 5, 'SiO₂'],
  ['TC-NCF으로부터도', 9, 'TC-NCF'], ['A+B는', 3, 'A+B']
]) {
  const range = match(text, offset);
  assert.equal(text.slice(range.start, range.end), expected);
}
assert.equal(match('DRAMATIC', 2), null);
assert.equal(match('D램' + '이랑'.repeat(200) + 'XYZ', 1), null);
assert.equal(createSelectionMatcher([])('D램을', 1), null);
const vocabulary = Array.from({ length: 2000 }, (_, i) => `등록용어${i}`);
const benchmark = createSelectionMatcher([...vocabulary, 'D램']);
const started = performance.now();
for (let i = 0; i < 100; i++) assert.deepEqual(benchmark('D램을 설명한다.', 2), { start: 0, end: 2 });
console.log(`PASS selection matcher; 2001 terms, 100 lookups: ${(performance.now() - started).toFixed(1)} ms`);
if (process.argv.includes('--matcher-only')) process.exit(0);

const repo = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const { createServer } = await import(pathToFileURL(join(repo, 'frontend/node_modules/vite/dist/node/index.js')));
const summary = 'D램을 비교하고 열압착 본딩에서는 원리를 봅니다. dram은 별칭입니다. 일부러 엉뚱한 선택도 허용합니다. 기묘한표현을 읽습니다. 실패표현과 느린표현도 있습니다.';
const html = `<!doctype html><html lang="ko"><body><div id="root"></div><script type="module">
  import React from 'react';
  import { createRoot } from 'react-dom/client';
  import { WikiView } from '/src/views/wiki/WikiView.jsx';
  import { useWikiController } from '/src/controllers/useWikiController.js';
  function Check() {
    const wiki = useWikiController({ initialConceptId: location.search.includes('entry=default') ? null : 'memory-fixture', currentUser: null });
    window.selectionCheck = { navigate: wiki.selectConcept, close: wiki.closeExplainer, activeId: wiki.activeConceptId };
    return React.createElement(WikiView, { wiki, currentUser: null });
  }
  createRoot(document.getElementById('root')).render(React.createElement(Check));
</script></body></html>`;
const cacheDir = await mkdtemp(join(tmpdir(), 'wiki-selection-vite-'));
const server = await createServer({ root: join(repo, 'frontend'), cacheDir, logLevel: 'error',
  server: { host: '127.0.0.1', port: 0 }, plugins: [{ name: 'selection-check-page', configureServer(vite) {
    vite.middlewares.use(async (req, res, next) => {
      if (req.url !== '/__selection-check.html' && req.url !== '/__selection-check.html?entry=default') return next();
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.end(await vite.transformIndexHtml('/__selection-check.html', html));
    });
  } }]
});
let browser;
try {
  await server.listen();
  browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
  const calls = [];
  let failureStatus = 503;
  let slowFailure = false;
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/contextual-explainer')) {
      assert.equal(route.request().method(), 'POST');
      assert.equal(url.search, '');
      const { term_id: term, selection_context: context } = route.request().postDataJSON();
      calls.push({ term, context, path: url.pathname });
      if (term === '느린표현' || term === 'D램') await new Promise((resolve) => setTimeout(resolve, 350));
      if (term === '실패표현' && failureStatus === 0) return route.abort('failed');
      if (term === '실패표현' || term === '느린표현' && slowFailure) {
        return route.fulfill({ status: term === '실패표현' ? failureStatus : 503, json: { detail: 'PRIVATE-ERROR-CONTENT' } });
      }
      return route.fulfill({ status: 200, json: {
        title: term, definition: '검사 해설: ' + term, contextSentence: '문맥 검사: ' + context, childConceptId: term === 'D램' ? 'registered-dram' : null
      } });
    }
    if (url.pathname.endsWith('/concepts/tree')) return route.fulfill({ json: { tree: [{ id: 'memory-fixture', title: '메모리 검사', type: 'concept', status: 'adopted', children: [] }], totalNodes: 1, currentFacet: 'unit_process' } });
    if (/\/concepts\/[^/]+$/.test(url.pathname)) return route.fulfill({ json: {
      id: url.pathname.split('/').at(-1), title: '메모리 검사', engName: 'Memory fixture', aliases: [],
      summary, purpose: 'D램은 용량 비교의 대상입니다.', principles: [], limitations: [], relations: {}, enrichedRelations: { previousSteps: [{ id: 'registered-dram', name: 'D램', isRegistered: true }] }, scaleLadder: [],
      evidenceIds: [], domainFacet: 'device', scaleLevel: 3, scaleName: '검사', status: 'adopted',
      preloadedExplainers: { 'd램': { definition: '문맥 없는 이전 설명', childConceptId: 'registered-dram' } }, selectionTerms: ['D램', 'DRAM', '열압착 본딩', '본딩', '실패표현', '느린표현'],
      perspectives: [{ id: 'masked-case', perspectiveId: 'private', perspectiveTitle: '비공개 사례',
        perspectiveBadge: '비공개', isMasked: true, contextNarrative: '', caution: '',
        specifications: [{ parameter: '비공개 압력', value: '***', isConfidential: true }] }]
    } });
    throw new Error('Unexpected fixture API: ' + url.pathname);
  });
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/__selection-check.html`);
  const paragraph = page.getByText(summary, { exact: true }).first();
  await paragraph.waitFor();
  const originalParagraphHTML = await paragraph.innerHTML();
  await paragraph.evaluate((element) => {
    window.paragraphMutations = 0;
    new MutationObserver((records) => { window.paragraphMutations += records.length; })
      .observe(element, { subtree: true, childList: true, characterData: true });
    window.nativeMouseUps = [];
    element.addEventListener('mouseup', (event) => window.nativeMouseUps.push({
      selection: window.getSelection().toString(), detail: event.detail, trusted: event.isTrusted
    }), true);
    window.nativeDoubleClicks = [];
    element.addEventListener('dblclick', (event) => window.nativeDoubleClicks.push({ detail: event.detail, trusted: event.isTrusted }));
  });
  const point = async (index, edge = null) => paragraph.evaluate((element, { offset, edge }) => {
    const range = document.createRange();
    range.setStart(element.firstChild, offset);
    range.setEnd(element.firstChild, offset + 1);
    const rect = range.getBoundingClientRect();
    return { x: edge === 'start' ? rect.left + .1 : edge === 'end' ? rect.right - .1 : rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
  }, { offset: index, edge });
  const selected = () => page.evaluate(() => window.getSelection().toString());
  const waitCalls = async (count) => {
    await page.waitForFunction(() => !document.querySelector('.concept-popover')?.textContent.includes('불러오는 중'));
    assert.equal(calls.length, count);
  };
  const click = async (word, options = {}) => {
    const p = await point(summary.indexOf(word));
    await page.mouse.click(p.x, p.y, options);
  };

  // A fresh fixture has no preloaded explanation: the two presses must share one request.
  const micro = await point(summary.indexOf('D램을'));
  await page.mouse.click(micro.x, micro.y);
  await page.mouse.move(micro.x, micro.y);
  await page.mouse.down({ clickCount: 2 });
  await page.mouse.move(micro.x + 1, micro.y);
  await page.mouse.up({ clickCount: 2 });
  await page.waitForTimeout(450);
  const microResult = { selection: await selected(), popovers: await page.locator('.concept-popover').count(),
    terms: calls.map((call) => call.term), events: await page.evaluate(() => window.nativeDoubleClicks) };
  console.log('1px second-press double-click:', JSON.stringify(microResult));
  assert.deepEqual(microResult.events, [{ detail: 2, trusted: true }]);
  assert.equal(microResult.selection, 'D램');
  assert.equal(microResult.popovers, 1);
  assert.deepEqual(microResult.terms, ['D램']);
  assert.equal(calls.at(-1).context, summary);
  assert.ok((await page.locator('.concept-popover').innerText()).includes('뜻:'));
  assert.ok((await page.locator('.concept-popover').innerText()).includes('이 문장에서:'));
  assert.ok(!(await page.locator('.concept-popover').innerText()).includes('문맥 없는 이전 설명'));
  assert.ok((await page.locator('.concept-popover').innerText()).includes('검사 해설: D램'));
  await page.evaluate(() => window.selectionCheck.close());

  // Capture the browser's range before React handles mouseup, including a return to the exact origin.
  const returnDrags = [];
  for (const returnOffset of [1, 0]) {
    await page.evaluate(() => window.getSelection().removeAllRanges());
    const beforeReturn = calls.length;
    await page.mouse.click(micro.x, micro.y);
    await page.mouse.down({ clickCount: 2 });
    await page.mouse.move(micro.x + 113, micro.y, { steps: 12 });
    await page.mouse.move(micro.x + returnOffset, micro.y, { steps: 12 });
    await page.mouse.up({ clickCount: 2 });
    await page.waitForTimeout(450);
    returnDrags.push({ returnOffset, beforeView: await page.evaluate(() => window.nativeMouseUps.at(-1)),
      selection: await selected(), popovers: await page.locator('.concept-popover').count(),
      terms: calls.slice(beforeReturn).map((call) => call.term) });
    await page.evaluate(() => window.selectionCheck.close());
  }
  console.log('113px drag and return:', JSON.stringify(returnDrags));
  for (const result of returnDrags) {
    assert.equal(result.beforeView.detail, 2);
    assert.equal(result.beforeView.trusted, true);
    assert.equal(result.beforeView.selection, 'D');
    assert.equal(result.selection, result.beforeView.selection);
    assert.equal(result.popovers, 0);
    assert.deepEqual(result.terms, ['D램']); // Only the first press requests an explanation.
  }

  await click('D램을');
  await page.waitForFunction(() => document.querySelector('.concept-popover')?.textContent.includes('검사 해설'));
  assert.equal(await selected(), 'D램');
  assert.equal(calls.at(-1).term, 'D램');
  await page.evaluate(() => window.selectionCheck.close());
  const beforeDouble = calls.length;
  await click('D램을', { clickCount: 2, delay: 200 });
  await waitCalls(beforeDouble + 1);
  assert.equal(await selected(), 'D램');
  assert.equal(calls.at(-1).term, 'D램');
  await click('에서는');
  await waitCalls(beforeDouble + 2);
  assert.equal(await selected(), '열압착 본딩');
  assert.equal(calls.at(-1).term, '열압착 본딩');
  await click('dram은');
  await waitCalls(beforeDouble + 3);
  assert.equal(await selected(), 'dram');
  assert.equal(calls.at(-1).term, 'dram');

  await page.evaluate(() => window.selectionCheck.close());
  const beforeContextChange = calls.length;
  const purpose = page.getByText('D램은 용량 비교의 대상입니다.', { exact: true });
  const purposePoint = await purpose.evaluate((element) => {
    const range = document.createRange();
    range.setStart(element.firstChild, 0); range.setEnd(element.firstChild, 1);
    const rect = range.getBoundingClientRect();
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
  });
  await page.mouse.click(purposePoint.x, purposePoint.y);
  await click('D램을', { clickCount: 2 });
  await waitCalls(beforeContextChange + 2);
  assert.equal(await selected(), 'D램');
  assert.equal(calls.at(-1).term, 'D램');
  assert.equal(calls.at(-2).context, 'D램은 용량 비교의 대상입니다.');
  assert.equal(calls.at(-1).context, summary);
  assert.ok((await page.locator('.concept-popover').innerText()).includes('문맥 검사: ' + summary));

  const drag = async (start, end) => {
    // Start a fresh selection instead of the browser's drag-and-drop of selected text.
    await page.evaluate(() => window.getSelection().removeAllRanges());
    const count = calls.length;
    const a = await point(start, start < end ? 'start' : 'end');
    const b = await point(end, start < end ? 'end' : 'start');
    await page.mouse.move(a.x, a.y); await page.mouse.down();
    await page.mouse.move(b.x, b.y, { steps: 12 }); await page.mouse.up();
    await waitCalls(count + 1);
    assert.equal(calls.at(-1).term, await selected());
  };
  const dragCount = calls.length;
  await drag(0, 2);
  assert.equal(await selected(), 'D램을');
  assert.equal(calls.length, dragCount + 1);
  await drag(2, 0);
  assert.equal(await selected(), 'D램을');
  // A longer movement on the second press still keeps the browser's manual range.
  await page.evaluate(() => window.getSelection().removeAllRanges());
  const beforeDoubleDrag = calls.length;
  const doubleDragStart = await point(0);
  const doubleDragEnd = await point(2, 'end');
  await page.mouse.click(doubleDragStart.x, doubleDragStart.y);
  await page.mouse.down({ clickCount: 2 });
  await page.mouse.move(doubleDragEnd.x, doubleDragEnd.y, { steps: 12 });
  await page.mouse.up({ clickCount: 2 });
  await waitCalls(beforeDoubleDrag + 2);
  assert.equal(await selected(), 'D램을');
  assert.equal(calls.at(-1).term, 'D램을');
  const unusualStart = summary.indexOf('일부러');
  await drag(unusualStart, unusualStart + '일부러 엉뚱한 선택'.length - 1);
  assert.ok((await selected()).includes('엉뚱한'));
  await drag(unusualStart - 1, unusualStart + '일부러 엉뚱한 선택도'.length);
  assert.equal(calls.at(-1).term, await selected());
  assert.ok((await selected()).startsWith(' '));
  assert.ok((await selected()).endsWith(' '));
  const unknownCount = calls.length;
  await click('기묘한표현을', { clickCount: 2, delay: 60 });
  await waitCalls(unknownCount + 1);
  assert.equal(calls.at(-1).term, await selected());
  assert.equal(await page.locator('.concept-popover').getByRole('button', { name: '문서 이동' }).count(), 0);

  for (const [status, message] of [
    [0, '연결 상태를 확인'], [403, '비공개 내용'], [404, '문서를 다시 열어'],
    [405, '서버 버전을 확인'], [422, '범위를 다시 선택'], [503, '생성하지 못했습니다'],
    [500, '요청을 처리하지 못했습니다']
  ]) {
    failureStatus = status;
    const beforeFailure = calls.length;
    await click('실패표현');
    await page.locator('.concept-popover [role="alert"]').filter({ hasText: message }).waitFor();
    assert.equal(calls.length, beforeFailure + 1);
    assert.ok(!(await page.locator('.concept-popover').innerText()).includes('PRIVATE-ERROR'));
  }
  slowFailure = true;
  await click('느린표현');
  await page.waitForFunction(() => document.querySelector('.concept-popover')?.textContent.includes('불러오는 중'));
  await page.evaluate(() => window.selectionCheck.close());
  await page.waitForTimeout(450);
  assert.equal(await page.locator('.concept-popover').count(), 0);
  slowFailure = false;
  const beforeNextSelection = calls.length;
  await click('느린표현');
  await page.waitForFunction(() => document.querySelector('.concept-popover')?.textContent.includes('불러오는 중'));
  await click('dram은');
  await waitCalls(beforeNextSelection + 2);
  await page.waitForTimeout(450);
  assert.ok((await page.locator('.concept-popover').innerText()).includes('검사 해설: dram'));
  assert.ok(!(await page.locator('.concept-popover').innerText()).includes('검사 해설: 느린표현'));
  await click('느린표현');
  await page.waitForFunction(() => document.querySelector('.concept-popover')?.textContent.includes('불러오는 중'));
  await page.evaluate(() => window.selectionCheck.navigate('other-fixture'));
  await page.waitForTimeout(450);
  assert.equal(await page.locator('.concept-popover').count(), 0);
  const beforeCard = calls.length;
  await page.getByText('D램', { exact: true }).first().click();
  // Shared UI versions open a relation dialog or navigate to its registered document.
  await page.waitForFunction(() => window.selectionCheck.activeId === 'registered-dram'
    || document.querySelector('[style*="backdrop-filter"]'));
  await page.waitForTimeout(100);
  assert.equal(calls.length, beforeCard);
  assert.ok(!(await page.locator('body').innerText()).includes('987654'));
  assert.ok(calls.every((call) => !call.term.includes('987654') && !call.context.includes('987654')));
  assert.equal(await paragraph.innerHTML(), originalParagraphHTML);
  assert.equal(await page.evaluate(() => window.paragraphMutations), 0);
  assert.deepEqual(errors, []);
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/__selection-check.html?entry=default`);
  await page.waitForFunction(() => window.selectionCheck?.activeId === 'memory-fixture');
  await page.getByText(summary, { exact: true }).first().waitFor();
  assert.ok(!(await page.locator('body').innerText()).includes('개념 로드 오류'));
  assert.deepEqual(errors, []);
  console.log('PASS default wiki entry selects a registered server tree node without a fixed concept ID');
  console.log('PASS Chromium native click/double-click, 1px jitter and out-and-back drag selection, suffix click, literal lowercase alias, unchanged registered/unusual drag, unknown native selection, one request per gesture, API error and stale response, existing relation-card click, masked fixture');
} finally {
  await browser?.close();
  await server.close();
}
