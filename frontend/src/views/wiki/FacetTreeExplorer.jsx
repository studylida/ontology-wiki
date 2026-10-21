/**
 * [계층 1] FacetTreeExplorer View (Pure Dumb UI Component)
 * - 2-Way 관점 전환 토글: [🏛️ 실무분야별] vs [🔬 물리규모별]
 * - 실무분야별: 4축 패싯 스위처 (소자, 공정, 운영, 인프라) & 카테고리 트리
 * - 물리규모별: 5단계 물리적 규모 체계 (Scale 5 팹 인프라 ~ Scale 1 원자 계면)
 * - 검색창 & [+ 새 문서 추가 발의하기 ➔] 버튼 탑재
 */

import React, { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronRight, PlusCircle, Layers, Cpu, Activity, Box } from 'lucide-react';
import { formatService } from '../../services/formatService';

const FACETS = [
  { id: 'unit_process', label: '단위공정', icon: Layers },
  { id: 'device', label: '소자', icon: Cpu },
  { id: 'operations', label: 'Fab운영', icon: Activity },
  { id: 'materials_infra', label: '인프라', icon: Box }
];

const SCALE_DEFINITIONS = [
  { scale: 5, name: 'Scale 5: 팹 인프라 & 환경', icon: '🌐', range: '100m ~ 1km', desc: '클린룸 유틸리티, 서브팹 배기, 환경' },
  { scale: 4, name: 'Scale 4: 장비 & 챔버', icon: '🏭', range: '1m ~ 10m', desc: '챔버 하드웨어, 센서 계측, 장비 통신' },
  { scale: 3, name: 'Scale 3: 공정 & 단위 레시피', icon: '⚙️', range: '1cm ~ 300mm', desc: '웨이퍼 단위 가열, 플라즈마 방전, 워피지' },
  { scale: 2, name: 'Scale 2: 박막 & 소자 셀', icon: '🔬', range: '1nm ~ 1μm', desc: '단위 셀(GAA, 3D NAND, HBM TSV/Microbump), 박막 균일도' },
  { scale: 1, name: 'Scale 1: 원자 물성 & 계면', icon: '⚛️', range: '0.1nm ~ 1nm', desc: '원자간 결합, 격자 부정합, 계면 결함, 전하 포획' }
];

export function FacetTreeExplorer({
  activeFacet,
  activeConceptId,
  treeData,
  isLoading,
  onSelectFacet,
  onSelectConcept,
  onOpenNewConceptModal
}) {
  const [navMode, setNavMode] = useState('domain'); // 'domain' | 'scale'
  const [searchFilter, setSearchFilter] = useState('');
  const [collapsedCategories, setCollapsedCategories] = useState({});
  const [collapsedScales, setCollapsedScales] = useState({ 1: true });

  const toggleCategory = (catId) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [catId]: !prev[catId]
    }));
  };

  const toggleScale = (scaleNum) => {
    setCollapsedScales((prev) => ({
      ...prev,
      [scaleNum]: !prev[scaleNum]
    }));
  };

  // 모든 개념 목록 평탄화 (스케일별 그룹핑용)
  const allConcepts = useMemo(() => {
    if (!treeData?.tree) return [];
    const list = [];
    treeData.tree.forEach((cat) => {
      (cat.children || []).forEach((c) => {
        list.push({ ...c, categoryName: cat.title });
      });
    });
    return list;
  }, [treeData]);

  // 도메인 모드 필터링 트리
  const filteredDomainTree = useMemo(() => {
    if (!treeData?.tree) return [];
    if (!searchFilter.trim()) return treeData.tree;

    const term = searchFilter.toLowerCase();
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

  // 스케일 모드 필터링 그룹
  const filteredScaleGroups = useMemo(() => {
    const term = searchFilter.toLowerCase().trim();

    return SCALE_DEFINITIONS.map((def) => {
      let matched = allConcepts.filter((c) => (c.scaleLevel || 3) === def.scale);
      if (term) {
        matched = matched.filter(
          (c) =>
            c.title.toLowerCase().includes(term) ||
            (c.engName && c.engName.toLowerCase().includes(term)) ||
            (c.aliases && c.aliases.some((a) => a.toLowerCase().includes(term)))
        );
      }
      return {
        ...def,
        concepts: matched
      };
    });
  }, [allConcepts, searchFilter]);

  return (
    <aside
      className="wiki-sidebar"
      style={{
        width: '320px',
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
      {/* ── 2-Way 관점 전환 토글 바 ── */}
      <div
        className="sidebar-nav-mode-toggle"
        style={{
          margin: '8px 8px 4px 8px',
          padding: '3px',
          display: 'flex',
          background: 'var(--bg-surface-2)',
          borderRadius: '8px',
          border: '1px solid var(--border-color)',
          gap: '2px'
        }}
      >
        <button
          type="button"
          className={`sidebar-mode-btn ${navMode === 'domain' ? 'active' : ''}`}
          onClick={() => setNavMode('domain')}
          style={{
            flex: 1,
            padding: '6px 8px',
            borderRadius: '6px',
            border: 'none',
            background: navMode === 'domain' ? 'var(--bg-surface)' : 'transparent',
            color: navMode === 'domain' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            fontSize: '0.75rem',
            fontWeight: navMode === 'domain' ? 800 : 500,
            cursor: 'pointer',
            boxShadow: navMode === 'domain' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <span>🏛️ 실무분야별</span>
        </button>
        <button
          type="button"
          className={`sidebar-mode-btn ${navMode === 'scale' ? 'active' : ''}`}
          onClick={() => setNavMode('scale')}
          style={{
            flex: 1,
            padding: '6px 8px',
            borderRadius: '6px',
            border: 'none',
            background: navMode === 'scale' ? 'var(--bg-surface)' : 'transparent',
            color: navMode === 'scale' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            fontSize: '0.75rem',
            fontWeight: navMode === 'scale' ? 800 : 500,
            cursor: 'pointer',
            boxShadow: navMode === 'scale' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <span>🔬 물리규모별</span>
        </button>
      </div>

      {/* ── 실무분야별 모드일 때: 4축 패싯 스위처 ── */}
      {navMode === 'domain' && (
        <div
          className="sliding-tabs-container"
          style={{
            padding: '3px',
            margin: '4px 8px 8px 8px',
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '2px'
          }}
        >
          {FACETS.map((f) => {
            const Icon = f.icon;
            const isActive = activeFacet === f.id;
            return (
              <button
                key={f.id}
                type="button"
                className={`sliding-tab-item ${isActive ? 'active' : ''}`}
                style={{
                  padding: '6px 2px',
                  fontSize: '0.75rem',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '2px'
                }}
                onClick={() => onSelectFacet(f.id)}
                title={`${f.label} 패싯으로 전환`}
              >
                <Icon size={14} />
                <span>{f.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* ── 물리규모별 모드일 때: 스케일 안내 헤더 ── */}
      {navMode === 'scale' && (
        <div style={{ padding: '6px 12px 8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            물리적 규모(Scale) 체계
          </span>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
            거시(팹) ➔ 미시(원자)
          </span>
        </div>
      )}

      {/* 검색 입력창 & 신규 발의 버튼 */}
      <div style={{ padding: '0 8px 8px 8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ position: 'relative' }}>
          <Search
            size={14}
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
            placeholder={navMode === 'domain' ? "개념명 또는 동의어 검색..." : "규모별 온톨로지 개념 검색..."}
            style={{
              width: '100%',
              padding: '6px 8px 6px 30px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              fontSize: '0.75rem'
            }}
          />
        </div>

        <button
          type="button"
          onClick={onOpenNewConceptModal}
          style={{
            padding: '6px 10px',
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
        >
          <PlusCircle size={14} />
          <span>+ 새 문서 추가 발의하기 ➔</span>
        </button>
      </div>

      {/* ── 트리 노드 목록 영역 ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 12px 8px' }}>
        {isLoading ? (
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="skeleton-line" style={{ width: '60%' }} />
            <div className="skeleton-line" style={{ width: '80%' }} />
            <div className="skeleton-line" style={{ width: '70%' }} />
          </div>
        ) : navMode === 'domain' ? (
          /* [도메인 모드] 카테고리 트리 */
          filteredDomainTree.length === 0 ? (
            <div style={{ padding: '24px 12px', textAlign: 'center', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              일치하는 온톨로지 개념이 없습니다.
            </div>
          ) : (
            filteredDomainTree.map((cat) => {
              const isCollapsed = Boolean(collapsedCategories[cat.id]);
              return (
                <div key={cat.id} style={{ marginBottom: '6px' }}>
                  {/* 카테고리 헤더 */}
                  <div
                    onClick={() => toggleCategory(cat.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '6px 8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: 'var(--text-secondary)',
                      userSelect: 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
                      <span>{cat.title}</span>
                    </div>
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
                  </div>

                  {/* 개념 노드 목록 */}
                  {!isCollapsed && (
                    <div style={{ paddingLeft: '8px', display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '2px' }}>
                      {cat.children?.map((concept) => {
                        const isSelected = activeConceptId === concept.id;
                        const scale = formatService.getScaleInfo(concept.scaleLevel);
                        return (
                          <div
                            key={concept.id}
                            onClick={() => onSelectConcept(concept.id)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '6px 8px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              background: isSelected ? 'var(--accent-primary-light)' : 'transparent',
                              color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                              fontWeight: isSelected ? 600 : 400,
                              fontSize: '0.8125rem',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                              {concept.title}
                            </span>
                            <span
                              style={{
                                fontSize: '0.6875rem',
                                padding: '1px 5px',
                                borderRadius: '4px',
                                background: scale.bg,
                                color: scale.color,
                                fontWeight: 600,
                                marginLeft: '6px',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              L{concept.scaleLevel}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )
        ) : (
          /* [스케일 모드] 5단계 물리적 규모 트리 (Scale 5 ➔ Scale 1) */
          filteredScaleGroups.map((group) => {
            const isCollapsed = Boolean(collapsedScales[group.scale]);
            return (
              <div key={group.scale} style={{ marginBottom: '8px' }}>
                {/* 스케일 헤더 */}
                <div
                  onClick={() => toggleScale(group.scale)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    userSelect: 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{group.icon}</span>
                    <span style={{ color: 'var(--text-primary)' }}>{group.name}</span>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>({group.range})</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span
                      style={{
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: '10px',
                        background: 'var(--bg-surface)',
                        color: 'var(--text-muted)',
                        border: '1px solid var(--border-color)'
                      }}
                    >
                      {group.concepts.length}
                    </span>
                    {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
                  </div>
                </div>

                {/* 해당 스케일 개념 목록 */}
                {!isCollapsed && (
                  <div style={{ paddingLeft: '8px', display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
                    {group.concepts.length === 0 ? (
                      <div style={{ padding: '6px 8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        해당 규모의 개념이 없습니다.
                      </div>
                    ) : (
                      group.concepts.map((concept) => {
                        const isSelected = activeConceptId === concept.id;
                        return (
                          <div
                            key={concept.id}
                            onClick={() => onSelectConcept(concept.id)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '6px 8px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              background: isSelected ? 'var(--accent-primary-light)' : 'transparent',
                              color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                              fontWeight: isSelected ? 700 : 400,
                              fontSize: '0.8125rem',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                              {concept.title}
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                              {concept.categoryName || '공정'}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
