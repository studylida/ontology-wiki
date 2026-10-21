/**
 * [계층 1] WikiView Orchestrator (Pure Dumb UI Component)
 * - Tab 1 위키 브라우저 3단 레이아웃 (좌측 트리, 중앙 본문, 우측 서브그래프)
 * - 비즈니스 로직 0줄: 모든 상태는 useWikiController에서 주입받음
 */

import React, { useState } from 'react';
import { FacetTreeExplorer } from './FacetTreeExplorer';
import { ConceptHeader } from './ConceptHeader';
import { SectionOverview } from './SectionOverview';
import { SectionPrinciples } from './SectionPrinciples';
import { SectionLimitations } from './SectionLimitations';
import { SectionPerspectives } from './SectionPerspectives';
import { SectionRelations } from './SectionRelations';
import { SectionEvidences } from './SectionEvidences';
import { CausalSubgraphCanvas } from './CausalSubgraphCanvas';
import { ContextualExplainerCard } from './ContextualExplainerCard';
import { ContextualPopover } from './ContextualPopover';
import { AccessRequestModal } from './AccessRequestModal';
import { RevisionModal } from './RevisionModal';
import { NewConceptModal } from './NewConceptModal';
import { CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export function WikiView({ wiki, currentUser, onAskChatbot }) {
  const [popoverState, setPopoverState] = useState({
    isOpen: false,
    position: null,
    data: null
  });
  const {
    navMode,
    activeScale,
    activeFacet,
    activeConceptId,
    treeData,
    conceptDetail,
    subgraphData,
    subgraphDepth,
    subgraphDirection,
    explainerCard,
    isTreeLoading,
    isConceptLoading,
    isSubgraphLoading,
    error,
    notification,
    l3AccessStatus,
    isAccessModalOpen,
    isRevisionModalOpen,
    isNewConceptModalOpen,
    newConceptInitialData,
    isRecommendingPlacement,
    placementRecommendation,
    changeFacet,
    changeScale,
    changeNavMode,
    selectConcept,
    changeSubgraphDepth,
    changeSubgraphDirection,
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

  // 마우스 드래그 텍스트 선택 시 플로팅 문맥 해설 팝오버 트리거
  const handleArticleMouseUp = (e) => {
    if (e.target.closest('.concept-popover, button, a, input, textarea, modal')) return;

    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const text = selection.toString().trim();
    if (text.length < 2 || text.length > 60) return;

    try {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      const x = Math.min(window.innerWidth - 340, Math.max(16, rect.left));
      const y = Math.min(window.innerHeight - 240, rect.bottom + 8);

      const pre = conceptDetail?.preloadedExplainers?.[text.toLowerCase()];

      setPopoverState({
        isOpen: true,
        position: { x, y },
        data: {
          title: text,
          term: text,
          definition: pre?.definition || `${text}에 대한 반도체 온톨로지 핵심 도메인 개념입니다.`,
          contextSentence: pre?.contextSentence || `현재 보고 있는 [${conceptDetail?.title || '공정'}] 문서와 밀접한 인과 연관성을 지닙니다.`,
          conceptId: pre?.targetConceptId || null
        }
      });
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
      <div style={{ flex: 1, minWidth: 0 }} onMouseUp={handleArticleMouseUp}>
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
              preloadedExplainers={conceptDetail.preloadedExplainers}
              onOpenExplainer={openExplainer}
            />

            {/* 2번 섹션: 작동 및 물리 원리 (KaTeX 수식) */}
            <SectionPrinciples principles={conceptDetail.principles} />

            {/* 3번 섹션: 물리적 한계 및 트레이드오프 ([E-01] 출처 배지) */}
            <SectionLimitations limitations={conceptDetail.limitations} />

            {/* 3번 섹션: 적응형 실무 사례 & L3 파라미터 (4단계 인가 배지) */}
            <SectionPerspectives
              perspectives={conceptDetail.perspectives}
              l3AccessStatus={l3AccessStatus}
              currentUser={currentUser}
              onOpenAccessModal={openAccessModal}
              onCancelAccessRequest={cancelAccessRequest}
            />

            {/* 4번 섹션: 온톨로지 인과 관계망 (전·후 공정 및 인과 연결) */}
            <SectionRelations
              conceptDetail={conceptDetail}
              treeData={treeData}
              onSelectConcept={selectConcept}
              onOpenNewConceptModal={openNewConceptModal}
            />

            {/* 5번 섹션: 공식 검증 출처 원문 (Evidence References) */}
            <SectionEvidences
              conceptDetail={conceptDetail}
            />
          </>
        ) : null}
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
        onClose={closeNewConceptModal}
        onRequestRecommendation={requestPlacementRecommendation}
        onSubmit={submitNewConceptTicket}
      />

      {/* ── 텍스트 드래그 및 인라인 용어 문맥 해설 팝오버 ── */}
      <ContextualPopover
        isOpen={popoverState.isOpen}
        position={popoverState.position}
        data={popoverState.data}
        onClose={() => setPopoverState((prev) => ({ ...prev, isOpen: false }))}
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
