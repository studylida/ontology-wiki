/**
 * [계층 1] WikiView Orchestrator (Pure Dumb UI Component)
 * - Tab 1 위키 브라우저 3단 레이아웃 (좌측 트리, 중앙 본문, 우측 서브그래프)
 * - 비즈니스 로직 0줄: 모든 상태는 useWikiController에서 주입받음
 */

import React from 'react';
import { FacetTreeExplorer } from './FacetTreeExplorer';
import { ConceptHeader } from './ConceptHeader';
import { SectionOverview } from './SectionOverview';
import { SectionPrinciples } from './SectionPrinciples';
import { SectionLimitations } from './SectionLimitations';
import { SectionPerspectives } from './SectionPerspectives';
import { CausalSubgraphCanvas } from './CausalSubgraphCanvas';
import { ContextualExplainerCard } from './ContextualExplainerCard';
import { AccessRequestModal } from './AccessRequestModal';
import { RevisionModal } from './RevisionModal';
import { NewConceptModal } from './NewConceptModal';
import { CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export function WikiView({ wiki, currentUser }) {
  const {
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
    isRecommendingPlacement,
    placementRecommendation,
    changeFacet,
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

  return (
    <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
      {/* ── 좌측 패널: 4축 패싯 트리 탐색기 ── */}
      <FacetTreeExplorer
        activeFacet={activeFacet}
        activeConceptId={activeConceptId}
        treeData={treeData}
        isLoading={isTreeLoading}
        onSelectFacet={changeFacet}
        onSelectConcept={selectConcept}
        onOpenNewConceptModal={openNewConceptModal}
      />

      {/* ── 중앙 패널: 위키 본문 4대 섹션 ── */}
      <div style={{ flex: 1, minWidth: 0 }}>
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

            {/* 4번 섹션: 적응형 실무 사례 & L3 파라미터 (4단계 인가 배지) */}
            <SectionPerspectives
              perspectives={conceptDetail.perspectives}
              l3AccessStatus={l3AccessStatus}
              currentUser={currentUser}
              onOpenAccessModal={openAccessModal}
              onCancelAccessRequest={cancelAccessRequest}
            />
          </>
        ) : null}
      </div>

      {/* ── 우측 패널: 2-Hop 인과 서브그래프 & 문맥 해설 ── */}
      <aside style={{ width: '360px', flexShrink: 0 }}>
        {/* 문맥 해설 카드 (활성화 시 표출) */}
        <ContextualExplainerCard
          explainerData={explainerCard}
          onClose={closeExplainer}
          onNavigate={(targetId) => selectConcept(targetId)}
        />

        {/* 2-Hop 인과 서브그래프 캔버스 */}
        <CausalSubgraphCanvas
          subgraphData={subgraphData}
          centralConceptId={activeConceptId}
          depth={subgraphDepth}
          direction={subgraphDirection}
          isLoading={isSubgraphLoading}
          onChangeDepth={changeSubgraphDepth}
          onChangeDirection={changeSubgraphDirection}
          onSelectConcept={selectConcept}
        />
      </aside>

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
        isRecommending={isRecommendingPlacement}
        placementRecommendation={placementRecommendation}
        onClose={closeNewConceptModal}
        onRequestRecommendation={requestPlacementRecommendation}
        onSubmit={submitNewConceptTicket}
      />
    </div>
  );
}
