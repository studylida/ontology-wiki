/**
 * [계층 1] WikiView Orchestrator (Pure Dumb UI Component)
 * - Tab 1 위키 브라우저 레이아웃 (좌측 트리, 중앙 본문)
 * - 비즈니스 로직 0줄: 모든 상태는 useWikiController에서 주입받음
 */

import React, { useRef } from 'react';
import { FacetTreeExplorer } from './FacetTreeExplorer';
import { ConceptHeader } from './ConceptHeader';
import { SectionOverview } from './SectionOverview';
import { SectionPrinciples } from './SectionPrinciples';
import { SectionLimitations } from './SectionLimitations';
import { SectionPerspectives } from './SectionPerspectives';
import { SectionRelations } from './SectionRelations';
import { SectionEvidences } from './SectionEvidences';
import { ContextualPopover } from './ContextualPopover';
import { AccessRequestModal } from './AccessRequestModal';
import { RevisionModal } from './RevisionModal';
import { NewConceptModal } from './NewConceptModal';
import { CheckCircle2, AlertCircle, RefreshCw, BookOpen } from 'lucide-react';

export function WikiView({ wiki, currentUser, onAskChatbot, onNavigateComparison }) {
  const {
    navMode,
    activeScale,
    activeFacet,
    activeConceptId,
    treeData,
    conceptDetail,
    explainerPopover,
    findSelectionRange,
    caseExplanationRequests,
    generateCaseContextExplanation,
    isTreeLoading,
    isConceptLoading,
    error,
    notification,
    l3AccessStatus,
    isAccessModalOpen,
    isRevisionModalOpen,
    isNewConceptModalOpen,
    newConceptInitialData,
    isRecommendingPlacement,
    placementRecommendation,
    placementRecommendationError,
    changeFacet,
    changeScale,
    changeNavMode,
    selectConcept,
    openExplainer,
    closeExplainer,
    openAccessModal,
    closeAccessModal,
    openRevisionModal,
    closeRevisionModal,
    openNewConceptModal,
    closeNewConceptModal,
    submitAccessRequest,
    cancelAccessRequest,
    submitRevisionTicket,
    requestPlacementRecommendation,
    submitNewConceptTicket,
    clearNotification
  } = wiki;

  const pointerStart = useRef(null);
  const excluded = '.concept-popover, button, a, input, textarea, select, [role="button"], [role="dialog"], [contenteditable], .modal, .katex, svg, math';

  const handleArticleMouseMove = (e) => {
    const start = pointerStart.current;
    if (start && (e.buttons & 1) && Math.hypot(start.x - e.clientX, start.y - e.clientY) > 2) {
      start.dragged = true;
    }
  };

  const handleArticleMouseUp = (e) => {
    const start = pointerStart.current;
    pointerStart.current = null;
    if (e.button !== 0 || !start || !conceptDetail || isConceptLoading) return;
    if (e.target.closest(excluded)) { closeExplainer(); return; }
    try {
      const selection = window.getSelection();
      if (!selection || !selection.rangeCount) return;
      const article = e.currentTarget;
      // Allow slight jitter only on the browser's second click; keep manual drags intact.
      const doubleClickJitter = e.detail === 2 && Math.hypot(start.x - e.clientX, start.y - e.clientY) <= 2;
      const dragged = start.dragged || (!selection.isCollapsed && !doubleClickJitter && (start.x !== e.clientX || start.y !== e.clientY));

      // Keep manual selections intact, including suffixes and intentionally unusual text.
      if (!dragged && !e.shiftKey) {
        if (getComputedStyle(e.target).cursor === 'pointer') { closeExplainer(); return; }
        const caret = document.caretPositionFromPoint?.(e.clientX, e.clientY);
        const fallback = !caret && document.caretRangeFromPoint?.(e.clientX, e.clientY);
        const node = caret?.offsetNode || fallback?.startContainer;
        const offset = caret?.offset ?? fallback?.startOffset;
        if (node?.nodeType === Node.TEXT_NODE && article.contains(node) && !node.parentElement.closest(excluded)) {
          const hit = document.createRange();
          hit.setStart(node, Math.max(0, offset - 1));
          hit.setEnd(node, Math.min(node.length, offset + 1));
          const onText = [...hit.getClientRects()].some((rect) => e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom);
          if (onText) {
            const block = node.parentElement.closest('p, div, li, td, th, h1, h2, h3, h4, h5, h6') || node.parentElement;
            const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
            const nodes = [];
            let text = '';
            let clickOffset;
            let part;
            while ((part = walker.nextNode())) {
              const visible = document.createRange();
              visible.selectNodeContents(part);
              if (part.parentElement.closest(excluded) || !visible.getClientRects().length || getComputedStyle(part.parentElement).visibility !== 'visible') {
                text += '\n';
                continue;
              }
              if (part === node) clickOffset = text.length + offset;
              nodes.push({ node: part, start: text.length, end: text.length + part.length });
              text += part.textContent;
            }
            const bounds = clickOffset === undefined ? null : findSelectionRange(text, clickOffset);
            if (bounds) {
              const first = nodes.find((item) => item.start <= bounds.start && item.end > bounds.start);
              const last = nodes.find((item) => item.start < bounds.end && item.end >= bounds.end);
              if (first && last) {
                const range = document.createRange();
                range.setStart(first.node, bounds.start - first.start);
                range.setEnd(last.node, bounds.end - last.start);
                selection.removeAllRanges();
                selection.addRange(range);
              }
            }
          }
        }
      }

      if (selection.isCollapsed) {
        closeExplainer();
        return;
      }
      const range = selection.getRangeAt(0);
      if (!article.contains(range.startContainer) || !article.contains(range.endContainer)) return;
      const text = selection.toString();
      if (text.trim().length < 2 || text.length > 60) { closeExplainer(); return; }
      const rect = range.getBoundingClientRect();
      const origin = range.startContainer.nodeType === Node.TEXT_NODE ? range.startContainer.parentElement : range.startContainer;
      const block = origin.closest('p, li, td, th, h1, h2, h3, h4, h5, h6') || origin;
      const before = document.createRange();
      before.selectNodeContents(block);
      before.setEnd(range.startContainer, range.startOffset);
      const offset = before.toString().length;
      const context = block.innerText.slice(Math.max(0, offset - 240), offset + text.length + 240);
      openExplainer(text, {
        x: Math.min(window.innerWidth - 340, Math.max(16, rect.left)),
        y: Math.min(window.innerHeight - 240, rect.bottom + 8)
      }, !dragged && e.detail > 1, context);
    } catch (err) {
      console.warn('Selection parse error:', err);
    }
  };

  return (
    <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
      {/* ── 좌측 패널: 2-Way (실무분야별 vs 물리규모별) 계층 트리 탐색기 ── */}
      <FacetTreeExplorer
        navMode={navMode}
        activeScale={activeScale}
        activeFacet={activeFacet}
        activeConceptId={activeConceptId}
        treeData={treeData}
        isLoading={isTreeLoading}
        onChangeNavMode={changeNavMode}
        onSelectFacet={changeFacet}
        onSelectScale={changeScale}
        onSelectConcept={selectConcept}
        onOpenNewConceptModal={openNewConceptModal}
      />

      {/* ── 중앙 패널: 위키 본문 5대 섹션 ── */}
      <div style={{ flex: 1, minWidth: 0 }} data-wiki-article
        onMouseDown={(e) => { pointerStart.current = e.button === 0 ? { x: e.clientX, y: e.clientY, dragged: false } : null; }}
        onMouseMove={handleArticleMouseMove}
        onMouseUp={handleArticleMouseUp}>
        {/* 알림 토스트 / 피드백 배너 */}
        {notification && (
          <div
            style={{
              padding: '12px 18px',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.8125rem',
              fontWeight: 500,
              background: notification.type === 'error' ? 'var(--accent-danger-light)' : 'var(--accent-success-light)',
              color: notification.type === 'error' ? 'var(--accent-danger)' : 'var(--accent-success)',
              border: `1px solid ${notification.type === 'error' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {notification.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
              <span>{notification.message}</span>
            </div>
            <button
              type="button"
              onClick={clearNotification}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>
        )}

        {isConceptLoading ? (
          <div
            style={{
              padding: '60px 40px',
              background: 'var(--bg-surface)',
              borderRadius: '12px',
              border: '1px solid var(--border-color)',
              textAlign: 'center',
              color: 'var(--text-muted)'
            }}
          >
            <RefreshCw size={24} className="spin" style={{ margin: '0 auto 12px auto', display: 'block' }} />
            <span>지식 온톨로지 상세 본문을 불러오는 중입니다...</span>
          </div>
        ) : error ? (
          <div
            style={{
              padding: '40px',
              background: 'var(--accent-danger-light)',
              borderRadius: '12px',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              color: 'var(--accent-danger)',
              textAlign: 'center'
            }}
          >
            <AlertCircle size={28} style={{ margin: '0 auto 12px auto', display: 'block' }} />
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.125rem' }}>개념 로드 오류</h3>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>{error}</p>
          </div>
        ) : conceptDetail ? (
          <>
            {/* 개념 헤더 */}
            <ConceptHeader
              conceptDetail={conceptDetail}
              onOpenRevisionModal={openRevisionModal}
              onOpenNewConceptModal={openNewConceptModal}
            />

            {/* 1번 섹션: 개요 및 도입 목적 */}
            <SectionOverview
              summary={conceptDetail.summary}
              purpose={conceptDetail.purpose}
            />

            {/* 2번 섹션: 작동 및 물리 원리 (KaTeX 수식) */}
            <SectionPrinciples principles={conceptDetail.principles} />

            {/* 3번 섹션: 물리적 한계 및 트레이드오프 ([E-01] 출처 배지) */}
            <SectionLimitations limitations={conceptDetail.limitations} />

            {/* 4번 섹션: 적응형 실무 사례 & L3 파라미터 (4단계 인가 배지) */}
            <SectionPerspectives
              perspectives={conceptDetail.perspectives}
              l3AccessStatus={l3AccessStatus}
              currentUser={currentUser}
              onOpenAccessModal={openAccessModal}
              onCancelAccessRequest={cancelAccessRequest}
              explanationRequests={caseExplanationRequests}
              onGenerateExplanation={generateCaseContextExplanation}
            />

            {/* 5번 섹션: 온톨로지 인과 관계망 및 규모별 계층도 */}
            <SectionRelations
              conceptDetail={conceptDetail}
              onSelectConcept={selectConcept}
              onOpenNewConceptModal={openNewConceptModal}
              onNavigateComparison={onNavigateComparison}
            />

            {/* 6번 섹션: 공식 검증 출처 원문 (Evidence References) */}
            <SectionEvidences
              conceptDetail={conceptDetail}
            />
          </>
        ) : (
          <div
            style={{
              padding: '64px 24px',
              textAlign: 'center',
              background: 'var(--surface-card, #ffffff)',
              borderRadius: '16px',
              border: '1px dashed var(--border-light, #e2e8f0)',
              margin: '24px 0'
            }}
          >
            <BookOpen size={48} style={{ margin: '0 auto 16px auto', display: 'block', color: 'var(--primary-color, #2563eb)', opacity: 0.6 }} />
            <h3 style={{ margin: '0 0 8px 0', fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary, #0f172a)' }}>
              현재 등록된 온톨로지 지식 개념이 없습니다
            </h3>
            <p style={{ margin: '0 auto 20px auto', maxWidth: '500px', fontSize: '0.9rem', color: 'var(--text-muted, #64748b)', lineHeight: 1.6 }}>
              새로운 데이터베이스로 초기화되었습니다.<br />
              상단 <strong>[거버넌스 콘솔] ➔ [원천 백서 지식 추출]</strong>에서 준비된 공식 기술 백서를 선택하여 위키의 첫 지식을 구축해보세요.
            </p>
          </div>
        )}
      </div>

      {/* ── 전역 모달 팝업들 ── */}
      <AccessRequestModal
        isOpen={isAccessModalOpen}
        conceptTitle={conceptDetail?.title || activeConceptId}
        onClose={closeAccessModal}
        onSubmit={submitAccessRequest}
      />

      <RevisionModal
        isOpen={isRevisionModalOpen}
        conceptDetail={conceptDetail}
        currentUser={currentUser}
        onClose={closeRevisionModal}
        onSubmit={submitRevisionTicket}
      />

      <NewConceptModal
        isOpen={isNewConceptModalOpen}
        currentUser={currentUser}
        initialData={newConceptInitialData}
        isRecommending={isRecommendingPlacement}
        placementRecommendation={placementRecommendation}
        recommendationError={placementRecommendationError}
        onClose={closeNewConceptModal}
        onRequestRecommendation={requestPlacementRecommendation}
        onSubmit={submitNewConceptTicket}
      />

      {/* ── 텍스트 드래그 및 인라인 용어 문맥 해설 팝오버 ── */}
      <ContextualPopover
        isOpen={explainerPopover.isOpen}
        position={explainerPopover.position}
        data={explainerPopover.data}
        onClose={closeExplainer}
        onAskChatbot={(term) => {
          if (onAskChatbot) {
            onAskChatbot(term);
          }
        }}
        onNavigateConcept={(targetId) => {
          selectConcept(targetId);
        }}
      />
    </div>
  );
}
