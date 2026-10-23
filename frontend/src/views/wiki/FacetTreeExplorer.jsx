/**
 * [계층 1] FacetTreeExplorer View (Pure Dumb UI Component)
 * - 2-Way 관점 전환: [🏛️ 실무분야별 (4대 분야)] vs [🔬 물리규모별 (5단계 Scale)]
 * - css/style.css 표준 클래스(.domain-facet-tabs, .facet-chip, .process-tree-nav, .process-nav-item, .concept-sub-link) 100% 준수
 * - 백엔드에서 쿼리된 정규화된 트리 데이터를 깨끗하고 직관적으로 렌더링
 */

import React, { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronRight, PlusCircle, Layers, Cpu, Activity, Box, Sparkles } from 'lucide-react';
import { relationService } from '../../services/relationService';

const DOMAIN_FACETS = [
  { id: 'unit_process', label: '단위공정', icon: Layers },
  { id: 'device', label: '소자 구조', icon: Cpu },
  { id: 'operations', label: 'Fab운영 & FDC', icon: Activity },
  { id: 'materials_infra', label: '소재 & 인프라', icon: Box }
];

const SCALE_TABS = [5, 4, 3, 2, 1].map(scale => ({
  scale,
  label: relationService.getScaleLabel(scale),
  shortLabel: relationService.getScaleLabel(scale)
}));

export function FacetTreeExplorer({
  navMode = 'domain',
  activeScale = 3,
  activeFacet = 'unit_process',
  activeConceptId,
  treeData,
  isLoading,
  onChangeNavMode,
  onSelectFacet,
  onSelectScale,
  onSelectConcept,
  onOpenNewConceptModal
}) {
  const [searchFilter, setSearchFilter] = useState('');
  const [collapsedCategories, setCollapsedCategories] = useState({});

  const toggleCategory = (catId) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [catId]: !prev[catId]
    }));
  };

  // 검색어에 따른 트리 필터링
  const filteredTree = useMemo(() => {
    if (!treeData?.tree) return [];
    if (!searchFilter.trim()) return treeData.tree;

    const term = searchFilter.toLowerCase().trim();
    return treeData.tree
      .map((cat) => {
        const matchingChildren = (cat.children || []).filter(
          (c) =>
            c.title.toLowerCase().includes(term) ||
            (c.engName && c.engName.toLowerCase().includes(term)) ||
            (c.aliases && c.aliases.some((a) => a.toLowerCase().includes(term)))
        );
        if (matchingChildren.length > 0) {
          return { ...cat, children: matchingChildren };
        }
        return null;
      })
      .filter(Boolean);
  }, [treeData, searchFilter]);

  return (
    <aside
      className="wiki-sidebar"
      style={{
        width: '300px',
        flexShrink: 0,
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--topbar-height) - 40px)',
        position: 'sticky',
        top: 'calc(var(--topbar-height) + 20px)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 1. 상단 2-Way 관점 전환 토글 바 ── */}
      <div style={{ padding: '10px 10px 4px 10px' }}>
        <div className="sidebar-nav-mode-toggle" role="tablist" style={{ margin: 0 }}>
          <button
            type="button"
            className={`sidebar-mode-btn ${navMode === 'domain' ? 'active' : ''}`}
            onClick={() => onChangeNavMode && onChangeNavMode('domain')}
            role="tab"
            aria-selected={navMode === 'domain'}
            title="실무 분야별 4대 범주로 온톨로지 탐색"
          >
            <span>🏛️ 실무분야별</span>
          </button>
          <button
            type="button"
            className={`sidebar-mode-btn ${navMode === 'scale' ? 'active' : ''}`}
            onClick={() => onChangeNavMode && onChangeNavMode('scale')}
            role="tab"
            aria-selected={navMode === 'scale'}
            title="물리적 규모(Scale 1~5)별로 온톨로지 탐색"
          >
            <span>🔬 물리규모별</span>
          </button>
        </div>
      </div>

      {/* ── 2. 분야 또는 규모 선택 탭 바 (레거시 .domain-facet-tabs & .facet-chip 규약) ── */}
      <div style={{ padding: '4px 10px 8px 10px' }}>
        {navMode === 'domain' ? (
          <div className="domain-facet-tabs">
            {DOMAIN_FACETS.map((f) => {
              const isActive = activeFacet === f.id;
              return (
                <button
                  key={f.id}
                  type="button"
                  className={`facet-chip ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectFacet && onSelectFacet(f.id)}
                >
                  <span>{f.label}</span>
                  <span style={{ fontSize: '0.6875rem', opacity: 0.6 }}>➔</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="domain-facet-tabs">
            {SCALE_TABS.map((s) => {
              const isActive = activeScale === s.scale;
              return (
                <button
                  key={s.scale}
                  type="button"
                  className={`facet-chip ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectScale && onSelectScale(s.scale)}
                  title={s.label}
                >
                  <span>{s.shortLabel}</span>
                  <span style={{ fontSize: '0.6875rem', opacity: 0.6 }}>➔</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── 3. 검색 입력창 & 신규 발의 버튼 ── */}
      <div style={{ padding: '0 10px 10px 10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ position: 'relative' }}>
          <Search
            size={13}
            style={{
              position: 'absolute',
              left: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)'
            }}
          />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder={navMode === 'domain' ? '단위 공정명 또는 약어 검색...' : '선택된 규모의 개념 검색...'}
            style={{
              width: '100%',
              padding: '6px 8px 6px 28px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              fontSize: '0.75rem',
              outline: 'none'
            }}
          />
        </div>

        <button
          type="button"
          onClick={() => onOpenNewConceptModal && onOpenNewConceptModal()}
          style={{
            padding: '5px 8px',
            borderRadius: '6px',
            border: '1px dashed var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.75rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            transition: 'background 0.15s ease'
          }}
          title="온톨로지에 아직 등록되지 않은 신규 개념 추가를 발의합니다."
        >
          <PlusCircle size={13} />
          <span>+ 새 문서 추가 발의하기 ➔</span>
        </button>
      </div>

      {/* ── 4. 계층형 공정 트리 네비게이션 (.process-tree-nav) ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 10px 12px 10px' }}>
        {isLoading ? (
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="skeleton-line" style={{ width: '60%' }} />
            <div className="skeleton-line" style={{ width: '80%' }} />
            <div className="skeleton-line" style={{ width: '70%' }} />
          </div>
        ) : filteredTree.length === 0 ? (
          <div style={{ padding: '24px 12px', textAlign: 'center', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            일치하는 온톨로지 개념이 없습니다.
          </div>
        ) : (
          <nav className="process-tree-nav">
            {filteredTree.map((cat) => {
              const isCollapsed = Boolean(collapsedCategories[cat.id]);
              return (
                <div key={cat.id} className="process-nav-group" style={{ marginBottom: '4px' }}>
                  {/* 대분류/카테고리 헤더 */}
                  <div
                    className="process-nav-item"
                    onClick={() => toggleCategory(cat.id)}
                    style={{ fontSize: '0.78125rem', padding: '6px 8px' }}
                  >
                    <span style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>{cat.title}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          padding: '1px 5px',
                          borderRadius: '4px',
                          background: 'var(--bg-surface-3)',
                          color: 'var(--text-muted)'
                        }}
                      >
                        {cat.children?.length || 0}
                      </span>
                      {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
                    </div>
                  </div>

                  {/* 세부 단위 개념 목록 */}
                  {!isCollapsed && (
                    <div className="process-concept-sublist" style={{ display: 'flex', paddingLeft: '14px' }}>
                      {cat.children?.map((concept) => {
                        const isSelected = activeConceptId === concept.id;
                        return (
                          <div
                            key={concept.id}
                            className={`concept-sub-link ${isSelected ? 'active' : ''}`}
                            onClick={() => onSelectConcept && onSelectConcept(concept.id)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '6px'
                            }}
                          >
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                              • {concept.title}
                            </span>
                            {concept.scaleLevel && (
                              <span
                                style={{
                                  fontSize: '0.625rem',
                                  padding: '1px 4px',
                                  borderRadius: '3px',
                                  background: isSelected ? 'var(--accent-primary)' : 'var(--bg-surface-3)',
                                  color: isSelected ? '#fff' : 'var(--text-muted)',
                                  fontWeight: 600
                                }}
                              >
                                L{concept.scaleLevel}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        )}
      </div>
    </aside>
  );
}
