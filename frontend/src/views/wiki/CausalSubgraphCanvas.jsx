/**
 * [계층 1] CausalSubgraphCanvas View (Pure Dumb UI Component)
 * - 0.65ms Recursive CTE 기반 1~2 hop 인과 네트워크 시각화
 * - 보상 파라미터(Compensating Parameters) 인라인 표출
 * - 홉(1~2 hop) 및 인과 방향(양방향/원인/결과) 실시간 토글
 */

import React, { useState, useMemo } from 'react';
import { GitFork, ArrowUpRight, ArrowDownLeft, Network, Cpu, Sliders, RefreshCw } from 'lucide-react';
import { formatService } from '../../services/formatService';

export function CausalSubgraphCanvas({
  subgraphData,
  centralConceptId,
  depth,
  direction,
  isLoading,
  onChangeDepth,
  onChangeDirection,
  onSelectConcept
}) {
  const [selectedEdge, setSelectedEdge] = useState(null);

  // SVG 원형 방사형 노드 좌표 계산
  const { layoutNodes, layoutEdges, centerNode } = useMemo(() => {
    if (!subgraphData?.graph) {
      return { layoutNodes: [], layoutEdges: [], centerNode: null };
    }

    const { nodes = [], edges = [] } = subgraphData.graph;
    const width = 360;
    const height = 300;
    const centerX = width / 2;
    const centerY = height / 2;

    const center = nodes.find((n) => n.id === centralConceptId || n.isCenter);
    const others = nodes.filter((n) => n !== center);

    const positioned = [];
    const radius = 100;
    const count = others.length;

    others.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / (count || 1) - Math.PI / 2;
      positioned.push({
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      });
    });

    if (center) {
      positioned.push({
        ...center,
        x: centerX,
        y: centerY
      });
    }

    const nodeCoordMap = new Map(positioned.map((n) => [n.id, n]));

    const computedEdges = edges.map((e) => {
      const s = nodeCoordMap.get(e.source);
      const t = nodeCoordMap.get(e.target);
      return {
        ...e,
        sourceNode: s,
        targetNode: t
      };
    });

    return {
      layoutNodes: positioned,
      layoutEdges: computedEdges,
      centerNode: center
    };
  }, [subgraphData, centralConceptId]);

  // 보상 파라미터를 가진 대표 엣지 탐색
  const activeCompParamEdge = selectedEdge || layoutEdges.find((e) => e.compensatingParams);

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '18px',
        display: 'flex',
        flexDirection: 'column',
        marginBottom: '20px'
      }}
    >
      {/* 헤더 & 컨트롤 바 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Network size={16} style={{ color: 'var(--accent-primary)' }} />
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            2-Hop 인과 서브그래프 (Causal Subgraph)
          </h3>
        </div>

        {/* 홉 깊이 토글 (1-Hop / 2-Hop) */}
        <div className="sliding-tabs-container" style={{ padding: '2px' }}>
          <button
            type="button"
            className={`sliding-tab-item ${depth === 1 ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.6875rem' }}
            onClick={() => onChangeDepth(1)}
          >
            1-Hop
          </button>
          <button
            type="button"
            className={`sliding-tab-item ${depth === 2 ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.6875rem' }}
            onClick={() => onChangeDepth(2)}
          >
            2-Hop
          </button>
        </div>
      </div>

      {/* 방향 제어 바 */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '10px' }}>
        {[
          { id: 'both', label: '양방향' },
          { id: 'out', label: '결과(Out)' },
          { id: 'in', label: '원인(In)' }
        ].map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => onChangeDirection(d.id)}
            style={{
              padding: '3px 8px',
              fontSize: '0.6875rem',
              borderRadius: '4px',
              border: '1px solid var(--border-color)',
              background: direction === d.id ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)',
              color: direction === d.id ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: direction === d.id ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            {d.label}
          </button>
        ))}
      </div>

      {/* SVG 그래프 캔버스 */}
      <div
        style={{
          width: '100%',
          height: '280px',
          background: 'var(--bg-surface-2)',
          borderRadius: '8px',
          border: '1px solid var(--border-color)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {isLoading ? (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.8125rem',
              color: 'var(--text-muted)'
            }}
          >
            <RefreshCw size={16} className="spin" style={{ marginRight: '6px' }} />
            인과 네트워크 추론 중...
          </div>
        ) : (
          <svg width="100%" height="100%" viewBox="0 0 360 280">
            <defs>
              <marker id="arrow-plus" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent-primary)" />
              </marker>
              <marker id="arrow-minus" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent-danger)" />
              </marker>
            </defs>

            {/* 엣지 라인 */}
            {layoutEdges.map((e, idx) => {
              if (!e.sourceNode || !e.targetNode) return null;
              const isSelected = selectedEdge?.id === e.id;
              const isMinus = e.polarity === '-';
              return (
                <g key={e.id || idx} onClick={() => setSelectedEdge(e)} style={{ cursor: 'pointer' }}>
                  <line
                    x1={e.sourceNode.x}
                    y1={e.sourceNode.y}
                    x2={e.targetNode.x}
                    y2={e.targetNode.y}
                    stroke={isSelected ? 'var(--text-primary)' : isMinus ? 'var(--accent-danger)' : 'var(--accent-primary)'}
                    strokeWidth={isSelected ? 3 : 1.5}
                    strokeDasharray={isMinus ? '4,3' : 'none'}
                    markerEnd={isMinus ? 'url(#arrow-minus)' : 'url(#arrow-plus)'}
                    opacity={0.8}
                  />
                  {/* 메커니즘 라벨 */}
                  {e.mechanismLabel && (
                    <text
                      x={(e.sourceNode.x + e.targetNode.x) / 2}
                      y={(e.sourceNode.y + e.targetNode.y) / 2 - 4}
                      fill="var(--text-muted)"
                      fontSize="9"
                      textAnchor="middle"
                      style={{ pointerEvents: 'none', background: 'var(--bg-surface)' }}
                    >
                      {e.polarity}{e.mechanismLabel.slice(0, 10)}
                    </text>
                  )}
                </g>
              );
            })}

            {/* 노드 서클 */}
            {layoutNodes.map((n) => {
              const isCenter = n.id === centralConceptId || n.isCenter;
              return (
                <g
                  key={n.id}
                  transform={`translate(${n.x}, ${n.y})`}
                  onClick={() => onSelectConcept(n.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    r={isCenter ? 18 : 12}
                    fill={isCenter ? 'var(--accent-primary)' : 'var(--bg-surface)'}
                    stroke={isCenter ? '#ffffff' : 'var(--accent-primary)'}
                    strokeWidth={isCenter ? 3 : 2}
                    filter={isCenter ? 'drop-shadow(0 2px 6px rgba(37, 99, 235, 0.4))' : 'none'}
                  />
                  <text
                    y={isCenter ? 30 : 22}
                    textAnchor="middle"
                    fill="var(--text-primary)"
                    fontSize={isCenter ? '10' : '9'}
                    fontWeight={isCenter ? '700' : '500'}
                  >
                    {n.label ? n.label.slice(0, 10) : n.id}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      {/* 🌟 도메인 필수: 보상 파라미터(Compensating Parameters) 인라인 박스 */}
      {activeCompParamEdge?.compensatingParams && (
        <div
          style={{
            marginTop: '12px',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--accent-primary)',
            borderRadius: '6px',
            padding: '10px 12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <Sliders size={13} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
              보상 파라미터: {activeCompParamEdge.compensatingParams.parameter}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            <div><strong>보상 수식:</strong> {activeCompParamEdge.compensatingParams.compensationFormula}</div>
            {activeCompParamEdge.compensatingParams.tradeoffCost && (
              <div style={{ color: 'var(--accent-warning)', marginTop: '2px' }}>
                ⚠️ 트레이드오프: {activeCompParamEdge.compensatingParams.tradeoffCost}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
