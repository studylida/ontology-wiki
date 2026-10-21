/**
 * [계층 1] FacetTreeExplorer View (Pure Dumb UI Component)
 * - 4축 패싯 스위처 (소자, 공정, 운영, 인프라)
 * - 공정 카테고리별 아코디언 트리 & 스케일 레벨 배지
 * - 검색창 하단 [+ 새 문서 추가 발의하기 ➔] 버튼 탑재
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

export function FacetTreeExplorer({
  activeFacet,
  activeConceptId,
  treeData,
  isLoading,
  onSelectFacet,
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

  // 클라이언트 사이드 검색 필터링
  const filteredTree = useMemo(() => {
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

  return (
    <aside
      className="wiki-sidebar"
      style={{
        width: '300px',
        borderRight: '1px solid var(--border-color)',
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--topbar-height) - 40px)',
        position: 'sticky',
        top: 'calc(var(--topbar-height) + 20px)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        overflow: 'hidden'
      }}
    >
      {/* 4축 패싯 스위처 탭 */}
      <div
        className="sliding-tabs-container"
        style={{
          padding: '4px',
          margin: '8px',
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
            >
              <Icon size={13} />
              <span>{f.label}</span>
            </button>
          );
        })}
      </div>

      {/* 탐색기 검색창 & 새 문서 발의 진입로 */}
      <div style={{ padding: '0 8px 8px 8px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '9px', color: 'var(--text-muted)' }} />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="온톨로지 트리 필터링..."
            style={{
              width: '100%',
              padding: '7px 10px 7px 32px',
              fontSize: '0.8125rem',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)'
            }}
          />
        </div>

        {/* 🌟 명세서 필수: 검색창 하단 [+ 새 문서 추가 발의하기 ➔] 버튼 */}
        <button
          type="button"
          onClick={onOpenNewConceptModal}
          style={{
            width: '100%',
            marginTop: '6px',
            padding: '7px 10px',
            borderRadius: '6px',
            border: '1px dashed var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.75rem',
            fontWeight: 600,
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

      {/* 계층형 트리 노드 목록 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 12px 8px' }}>
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
          filteredTree.map((cat) => {
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
        )}
      </div>
    </aside>
  );
}
