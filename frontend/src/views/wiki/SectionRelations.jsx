/**
 * [계층 1] SectionRelations View (Pure Dumb UI Component)
 * - 5번 섹션: 온톨로지 인과 관계망 및 규모별(Scale) 계층도
 * - 1~3번 섹션과 100% 동일한 24x24px 둥근 배지 헤더 디자인 준수
 * - 듀얼 모드 서브 탭:
 *   [Tab 1] 🔄 공정 인과 워크플로우 뷰 (M:N 다중 전·후 공정 파이프라인 + 1:N 대체 대안 + 소속 장비)
 *   [Tab 2] 🔬 등록 관계의 규모별 연결 뷰
 */

import React, { useState } from 'react';
import {
  Layers,
  ArrowRight,
  Plus,
  Sparkles,
  ExternalLink,
  Info,
  CheckCircle2,
  Workflow,
  GitBranch,
  Split
} from 'lucide-react';
import { relationService } from '../../services/relationService';

export function SectionRelations({
  conceptDetail,
  onSelectConcept,
  onOpenNewConceptModal,
  onNavigateComparison
}) {
  const [activeTab, setActiveTab] = useState('flow'); // 'flow' | 'ladder'
  const canNavigate = item => item.isRegistered === true && !!item.id && !!onSelectConcept;
  const navigate = (item, event) => {
    event.stopPropagation();
    if (canNavigate(item)) onSelectConcept(item.id);
  };
  const relationTitle = (item, style) => canNavigate(item) ? (
    <a href={`#concept/${encodeURIComponent(item.id)}`} onClick={event => {
      event.preventDefault();
      navigate(item, event);
    }} style={{...style, textDecoration: 'none'}} title={`${item.name} 문서로 이동`}>
      {item.name} <ArrowRight size={12} aria-hidden="true" style={{verticalAlign: 'middle'}} />
    </a>
  ) : <strong style={style}>{item.name}</strong>;
  const proposalButton = item => item.isRegistered !== true && onOpenNewConceptModal ? (
    <button type="button" onClick={event => {
      event.stopPropagation();
      onOpenNewConceptModal({
        title: item.name, parentConceptId: conceptDetail.id, parentTitle: conceptDetail.title,
        relationType: 'next_step',
        reason: item.reason || `[${conceptDetail.title}]의 인과 관계 개념으로 신규 발의합니다.`
      });
    }} style={{display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px',
      border: '1px solid var(--accent-primary)', borderRadius: '6px', padding: '6px 10px',
      background: 'var(--accent-primary-light)', color: 'var(--accent-primary)', cursor: 'pointer'}}>
      <Plus size={12} /> 신규 지식 발의하기
    </button>
  ) : null;

  if (!conceptDetail) return null;

  // Domain Service를 통한 관계망 데이터 정규 추출 (다중 전후공정 지원)
  const previousList = relationService.getRelationItems(conceptDetail, 'previousSteps');
  const nextList = relationService.getRelationItems(conceptDetail, 'nextSteps');
  const altList = relationService.getRelationItems(conceptDetail, 'alternatives');
  const partOfList = relationService.getRelationItems(conceptDetail, 'partOf');
  const isAList = relationService.getRelationItems(conceptDetail, 'isA');
  const scaleLadder = relationService.getScaleLadder(conceptDetail);

  return (
    <section
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 1. 섹션 헤더 (24x24 둥근 배지 + 듀얼 탭 스위처) ── */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          marginBottom: '16px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '6px',
              background: 'var(--accent-primary-light)',
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8125rem'
            }}
          >
            5
          </div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            온톨로지 인과 관계망 및 규모별(Scale) 계층도
          </h2>
        </div>

        {/* 서브 탭 스위처 (transitions.dev 규약 준수) */}
        <div
          style={{
            display: 'inline-flex',
            padding: '3px',
            borderRadius: '8px',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border-color)',
            fontSize: '0.75rem',
            fontWeight: 700
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('flow')}
            style={{
              padding: '5px 12px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              background: activeTab === 'flow' ? 'var(--accent-primary)' : 'transparent',
              color: activeTab === 'flow' ? '#ffffff' : 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease'
            }}
          >
            <Workflow size={13} />
            <span>지식 관계 뷰</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('ladder')}
            style={{
              padding: '5px 12px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              background: activeTab === 'ladder' ? 'var(--accent-primary)' : 'transparent',
              color: activeTab === 'ladder' ? '#ffffff' : 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease'
            }}
          >
            <Layers size={13} />
            <span>규모별 연결 뷰</span>
          </button>
        </div>
      </div>

      <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0 0 20px 0', lineHeight: 1.5 }}>
        등록된 지식의 소속·분류, 전후 공정과 기술적 대안 관계를 보여줍니다.
      </p>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* [TAB 1] 공정 인과 워크플로우 뷰 (Process & Causal Map)       */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'flow' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

          <div style={{padding: '12px 16px', border: '1px solid var(--accent-primary)', borderRadius: '8px', background: 'var(--accent-primary-light)'}}>
            <strong>{conceptDetail.title}</strong>
            <span style={{marginLeft: '10px', fontSize: '0.75rem'}}>{relationService.getScaleLabel(conceptDetail.scaleLevel)}</span>
          </div>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px'}}>
            {[
              ['상위 소속 대상', partOfList], ['구성 요소', relationService.getRelationItems(conceptDetail, 'hasParts')],
              ['상위 분류', isAList], ['하위 종류', relationService.getRelationItems(conceptDetail, 'subtypes')]
            ].filter(([, items]) => items.length > 0).map(([label, items]) => (
              <div key={label} style={{padding: '14px', borderRadius: '8px', background: 'var(--bg-surface-2)', border: '1px solid var(--border-color)'}}>
                <h3 style={{fontSize: '0.8125rem', margin: '0 0 8px'}}>{label} · {items.length}건</h3>
                {items.map(item => (
                  <div key={item.id} data-relation-block
                    onClick={canNavigate(item) ? event => navigate(item, event) : undefined}
                    style={{display: 'block', textAlign: 'left', padding: '10px', marginTop: '6px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-surface)', color: 'var(--text-primary)', cursor: canNavigate(item) ? 'pointer' : 'default'}}>
                    <span style={{display: 'block', fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '4px'}}>
                      {label === '상위 분류' || label === '상위 소속 대상' ? `${conceptDetail.title} → ${item.name}` : `${item.name} → ${conceptDetail.title}`}
                    </span>
                    {relationTitle(item, {fontWeight: 700, color: 'var(--text-primary)'})}
                    <span style={{display: 'block', fontSize: '0.6875rem', color: 'var(--text-muted)'}}>{item.isRegistered ? relationService.getScaleLabel(item.scaleLevel) : '미등록 대상'}</span>
                    {item.reason && <span style={{display: 'block', fontSize: '0.75rem', marginTop: '5px'}}>{item.reason}</span>}
                    {proposalButton(item)}
                  </div>
                ))}
              </div>
            ))}
          </div>
          {previousList.length + nextList.length + altList.length + partOfList.length + isAList.length + relationService.getRelationItems(conceptDetail, 'hasParts').length + relationService.getRelationItems(conceptDetail, 'subtypes').length === 0 && (
            <p>아직 등록된 관계가 없습니다. 원문에서 확인한 정의와 설명은 본문과 출처에서 볼 수 있습니다.</p>
          )}

          {(previousList.length > 0 || nextList.length > 0) && (<>
          {/* Zone 1: ⏩ 공정 전·후 파이프라인 (다중 선행 M개 ➔ 현재 ➔ 다중 후속 N개) */}
          <div
            style={{
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '18px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Workflow size={14} />
                <span>공정 전·후 연계 파이프라인 (Process Pipeline Stream)</span>
              </div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                등록된 카드를 클릭하면 해당 문서로 이동합니다
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(240px, 1fr) 40px minmax(260px, 1.2fr) 40px minmax(240px, 1fr)',
                gap: '8px',
                alignItems: 'center'
              }}
              className="pipeline-grid"
            >
              {/* 1. 선행 투입 공정 컬럼 (M:N 다중 카드 세로 스택) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>선행 투입 공정</span>
                  <span>{previousList.length}건</span>
                </div>

                {previousList.length > 0 ? (
                  previousList.map((item, idx) => {
                    const isReg = item.isRegistered === true;
                    return (
                      <div
                        key={item.id || idx}
                        data-relation-block
                        onClick={canNavigate(item) ? event => navigate(item, event) : undefined}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-color)',
                          cursor: canNavigate(item) ? 'pointer' : 'default',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          transition: 'border-color 0.15s ease'
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--accent-primary)'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span
                            style={{
                              fontSize: '0.625rem',
                              fontWeight: 700,
                              padding: '2px 5px',
                              borderRadius: '4px',
                              background: isReg ? 'rgba(16, 185, 129, 0.12)' : 'var(--bg-surface-3)',
                              color: isReg ? '#10b981' : 'var(--text-muted)'
                            }}
                          >
                            {isReg ? '🟢 등록 문서' : '⚪ 미등록'}
                          </span>
                        </div>
                        {relationTitle(item, {fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)'})}
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {item.reason || '연결 사유 미등록'}
                        </div>
                        {proposalButton(item)}
                      </div>
                    );
                  })
                ) : (
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      background: 'var(--bg-surface)',
                      border: '1px dashed var(--border-color)',
                      color: 'var(--text-muted)',
                      fontSize: '0.75rem',
                      textAlign: 'center'
                    }}
                  >
                    등록된 선행 공정이 없습니다.
                  </div>
                )}
              </div>

              {/* 연결 화살표 1 */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'var(--accent-primary-light)',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '0.75rem'
                  }}
                >
                  ➔
                </div>
                <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)', marginTop: '4px' }}>투입</span>
              </div>

              {/* 2. 현재 공정 (Scale 3 강조 카드) */}
              <div
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  background: 'var(--accent-primary-light)',
                  border: '2px solid var(--accent-primary)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.12)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 800,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: 'var(--accent-primary)',
                      color: '#ffffff'
                    }}
                  >
                    ● 현재 열람 개념
                  </span>
                  <span style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
                    Scale {conceptDetail.scaleLevel || 3}
                  </span>
                </div>
                <div style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {conceptDetail.title}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {conceptDetail.summary || '개요 미등록'}
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '0.6875rem',
                    color: 'var(--accent-primary)',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>🎯</span>
                  <span>{conceptDetail.processCategory || '표준 단위 기술'}</span>
                </div>
              </div>

              {/* 연결 화살표 2 */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#10b981',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '0.75rem'
                  }}
                >
                  ➔
                </div>
                <span style={{ fontSize: '0.625rem', color: '#10b981', marginTop: '4px', fontWeight: 700 }}>
                  연계
                </span>
              </div>

              {/* 3. 후속 연계 공정 컬럼 (M:N 다중 카드 세로 스택) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>후속 연계 공정</span>
                  <span>{nextList.length}건</span>
                </div>

                {nextList.length > 0 ? (
                  nextList.map((item, idx) => {
                    const isReg = item.isRegistered === true;
                    return (
                      <div
                        key={item.id || idx}
                        data-relation-block
                        onClick={canNavigate(item) ? event => navigate(item, event) : undefined}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-color)',
                          cursor: canNavigate(item) ? 'pointer' : 'default',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          transition: 'border-color 0.15s ease'
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#10b981'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span
                            style={{
                              fontSize: '0.625rem',
                              fontWeight: 700,
                              padding: '2px 5px',
                              borderRadius: '4px',
                              background: isReg ? 'rgba(16, 185, 129, 0.12)' : 'var(--bg-surface-3)',
                              color: isReg ? '#10b981' : 'var(--text-muted)'
                            }}
                          >
                            {isReg ? '🟢 등록 문서' : '⚪ 미등록'}
                          </span>
                        </div>
                        {relationTitle(item, {fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)'})}
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {item.reason || '연결 사유 미등록'}
                        </div>
                        {proposalButton(item)}
                      </div>
                    );
                  })
                ) : (
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      background: 'var(--bg-surface)',
                      border: '1px dashed var(--border-color)',
                      color: 'var(--text-muted)',
                      fontSize: '0.75rem',
                      textAlign: 'center'
                    }}
                  >
                    등록된 후속 공정이 없습니다.
                  </div>
                )}
              </div>
            </div>
          </div>

          </>)}

          {altList.length > 0 && (<>
          {/* Zone 2: ⚡ 기술적 대체 대안 비교 (Alternative Technologies - 1:N) */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Split size={14} style={{ color: '#f59e0b' }} />
                <span>기술적 대안 (Alternative Technologies)</span>
              </div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                {altList.length}건의 기술 대안 비교 가능
              </span>
            </div>

            {altList.length > 0 ? (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '12px'
                }}
              >
                {altList.map((alt, idx) => {
                  const isReg = alt.isRegistered === true;
                    return (
                    <div
                      key={alt.id || idx}
                      data-relation-block
                      onClick={canNavigate(alt) ? event => navigate(alt, event) : undefined}
                      style={{
                        padding: '14px',
                        borderRadius: '8px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-color)',
                        cursor: canNavigate(alt) ? 'pointer' : 'default',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                        transition: 'border-color 0.15s ease'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#f59e0b'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span
                          style={{
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: 'rgba(245, 158, 11, 0.12)',
                            color: '#f59e0b'
                          }}
                        >
                          대안 기술 {idx + 1}
                        </span>
                        <span
                          style={{
                            fontSize: '0.625rem',
                            fontWeight: 700,
                            color: isReg ? '#10b981' : 'var(--text-muted)'
                          }}
                        >
                          {isReg ? '🟢 등록 문서' : '⚪ 미등록'}
                        </span>
                      </div>

                      {relationTitle(alt, {fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)' })}

                      {proposalButton(alt)}
                      {alt.commonGoal && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          💡 <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>공통 목적:</span> {alt.commonGoal}
                        </div>
                      )}

                      {alt.tradeoff && (
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                          ⚖️ <span style={{ fontWeight: 600 }}>트레이드오프:</span> {alt.tradeoff}
                        </div>
                      )}

                      <div
                        style={{
                          marginTop: '4px',
                          paddingTop: '8px',
                          borderTop: '1px solid var(--border-color)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}
                      >
                        <span style={{ fontSize: '0.6875rem', color: '#f59e0b', fontWeight: 600 }}>
                          {isReg ? '위키 간 비교 가능' : '대상 위키 미등록'}
                        </span>
                        <button
                          type="button"
                          disabled={!isReg}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onNavigateComparison) {
                              onNavigateComparison(conceptDetail.id, alt.id);
                            } else {
                              window.location.hash = `#comparison?targetA=${conceptDetail.id}&targetB=${alt.id}`;
                            }
                          }}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '6px',
                            border: 'none',
                            background: 'var(--accent-primary)',
                            color: '#ffffff',
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="Tab 2 인과 비교 스튜디오로 이동하여 A/B 매트릭스를 확인합니다."
                        >
                          <span>⚡ A/B 비교 스튜디오</span>
                          <ArrowRight size={10} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem'
                }}
              >
                등록된 기술적 대안이 없습니다.
              </div>
            )}
          </div>

          </>)}

        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* [TAB 2] 규모별 연결 뷰 (Vertical Scale Ladder)       */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'ladder' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            현재 개념에서 두 단계 이내의 등록 관계를 규모별로 모았습니다. 구성·분류·공정 순서·대안은 서로 다른 관계이며 화살표에 종류와 방향을 표시합니다.
          </div>

          {scaleLadder.length === 0 && <p>현재 개념에 등록된 연결 정보가 없습니다.</p>}
          {scaleLadder.map((step) => {
            const isCur = step.isCurrent;
            return (
              <div data-relation-block
                key={step.entityId || step.scaleLevel}
                onClick={!isCur && canNavigate({id: step.entityId, isRegistered: true}) ? event => navigate({id: step.entityId, isRegistered: true}, event) : undefined}
                style={{textAlign: 'left', width: '100%', color: 'var(--text-primary)', font: 'inherit',
                  padding: '14px 18px',
                  borderRadius: '10px',
                  background: isCur ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)',
                  border: isCur ? '2px solid var(--accent-primary)' : '1px solid var(--border-color)',
                  cursor: !isCur && step.entityId && onSelectConcept ? 'pointer' : 'default',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease',
                  boxShadow: isCur ? '0 4px 12px rgba(37, 99, 235, 0.12)' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (!isCur) e.currentTarget.style.borderColor = 'var(--accent-primary)';
                }}
                onMouseLeave={(e) => {
                  if (!isCur) e.currentTarget.style.borderColor = 'var(--border-color)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '8px',
                      background: isCur ? 'var(--accent-primary)' : 'var(--bg-surface-3)',
                      color: isCur ? '#ffffff' : 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.8125rem'
                    }}
                  >
                    S{step.scaleLevel}
                  </div>
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 800, color: isCur ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                      {isCur ? step.title : relationTitle({id: step.entityId, name: step.title, isRegistered: !!step.entityId}, {color: 'inherit', fontWeight: 800})}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {step.description}
                    </div>
                    <div style={{fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '8px'}}>
                      {step.hops === 0 ? '현재 개념' : `현재 개념에서 ${step.hops}단계 연결`}
                    </div>
                    {relationService.getScaleConnections(step, scaleLadder).map(link => (
                      <div key={link.id} style={{marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem'}}>
                        <div><strong>{link.sourceName}</strong> → [{link.label}] → <strong>{link.targetName}</strong></div>
                        {link.mechanismLabel && <div style={{marginTop: '4px', color: 'var(--text-secondary)'}}>{link.mechanismLabel}</div>}
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isCur ? (
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        background: 'var(--accent-primary)',
                        color: '#ffffff',
                        fontSize: '0.6875rem',
                        fontWeight: 700
                      }}
                    >
                      ● 현재 위치
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}

    </section>
  );
}
