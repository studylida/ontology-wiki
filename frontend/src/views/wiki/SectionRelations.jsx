/**
 * [계층 1] SectionRelations View (Pure Dumb UI Component)
 * - 4번 섹션: 온톨로지 인과 관계망 (전·후 공정 및 시스템 연결)
 * - 도메인 의미 명확화: 상위 조립 계통(part_of), 다음 연계 공정(next_step), 기술 대안(alternative_to), 분류 체계(is_a)
 * - DB 실재 문서: 파란색 원클릭 이동 링크
 * - DB 미등록 개념: 안전한 안내용 배지(Badge) + [+ 발의하기] 원클릭 신규 발의 연동
 */

import React, { useMemo } from 'react';
import { GitBranch, Layers, ArrowRight, ArrowUpRight, Plus, Sparkles, ExternalLink } from 'lucide-react';
import { formatService } from '../../services/formatService';

export function SectionRelations({
  conceptDetail,
  treeData,
  onSelectConcept,
  onOpenNewConceptModal
}) {
  if (!conceptDetail) return null;

  const relations = conceptDetail.relations || {};
  const currentScale = conceptDetail.scaleLevel || 3;

  const isAList = relations.is_a || [];
  const partOfList = relations.part_of || [];
  const nextStepList = relations.next_step || [];
  const altList = relations.alternative_to || [];

  // DB에 실재하는 개념 ID 목록 (404 에러 방지용)
  const registeredIds = useMemo(() => {
    const ids = new Set([
      'concept-tcb', 'concept-mrmuf', 'mr-muf', 'concept-dry-etch', 'dry-etch',
      'concept-cryo-etch', 'cryogenic-etch', 'cowos-interposer-cuf', 'fan-out-wafer-level-packaging',
      'hybrid-bonding', 'hbm-kgd-testing', 'euv-lithography', 'high-na-euv', 'concept-high-na-euv',
      'ald-deposition', 'ale-etch', 'cu-damascene-cmp', 'dram-zaz-capacitor', '3d-nand-ctf-architecture',
      'gaa-nanosheet-etch', 'concept-gaa-nanosheet', 'fab-fdc-oes-realtime', 'concept-fdc-apc',
      'spc-control-chart', 'run-to-run', 'ultra-pure-water-upw', 'fab-subfab-pfc-scrubber'
    ]);

    if (treeData?.tree) {
      treeData.tree.forEach((cat) => {
        (cat.children || []).forEach((c) => {
          if (c.id) ids.add(c.id);
        });
      });
    }
    return ids;
  }, [treeData]);

  // 관계 칩 렌더러 (실재 문서 ➔ 이동 버튼 / 미등록 개념 ➔ 안내 배지 + 발의 버튼)
  const renderRelationItem = (item, relationTypeLabel, relationKey) => {
    const rawId = item.id || item.targetId;
    const name = item.name || item.targetName || item.title || rawId;
    const isRegistered = rawId && registeredIds.has(rawId);

    if (isRegistered) {
      return (
        <button
          key={rawId}
          type="button"
          onClick={() => onSelectConcept && onSelectConcept(rawId)}
          style={{
            padding: '5px 10px',
            borderRadius: '6px',
            border: '1px solid var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.8125rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            transition: 'transform 0.15s ease'
          }}
          title={`'${name}' 지식 문서로 바로 이동합니다.`}
        >
          <span>{name}</span>
          <ArrowRight size={12} />
        </button>
      );
    }

    // 미등록 개념 ➔ 안전한 안내용 배지 + [+ 발의하기]
    return (
      <div
        key={name}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          borderRadius: '6px',
          border: '1px dashed var(--border-color)',
          background: 'var(--bg-surface-2)',
          fontSize: '0.8125rem'
        }}
      >
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{name}</span>
        <span
          style={{
            fontSize: '0.625rem',
            padding: '1px 5px',
            borderRadius: '4px',
            background: 'var(--bg-surface-3)',
            color: 'var(--text-muted)'
          }}
        >
          미등록 문서
        </span>
        <button
          type="button"
          onClick={() =>
            onOpenNewConceptModal &&
            onOpenNewConceptModal({
              title: name,
              parentConceptId: conceptDetail.id,
              parentTitle: conceptDetail.title,
              relationType: relationKey,
              reason: `[${conceptDetail.title}] 문서의 '${relationTypeLabel}'(${name})로 참조되었으나 아직 지식 위키에 상세 문서가 부재하여 신규 작성을 발의합니다.`
            })
          }
          style={{
            background: 'var(--accent-primary)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            padding: '2px 6px',
            fontSize: '0.625rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '2px'
          }}
          title={`'${name}' 개념의 신규 작성을 거버넌스 센터에 발의합니다.`}
        >
          <Plus size={10} />
          <span>발의하기</span>
        </button>
      </div>
    );
  };

  return (
    <article
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <GitBranch size={20} style={{ color: 'var(--accent-primary)' }} />
        <h2 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
          4. 온톨로지 인과 관계망 (전·후 공정 및 인과 연결)
        </h2>
      </div>
      <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0 0 18px 0', lineHeight: 1.5 }}>
        본 단위 공정이 반도체 제조 라인과 완제품 조립 흐름 상에서 맺고 있는 상위 계통, 후속 공정 및 대체 기술 대안 관계망입니다.
      </p>

      {/* ── 4분할 온톨로지 관계망 그리드 ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '14px'
        }}
      >
        {/* 1. 상위 구성 모듈 (part_of) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              🏛️ 상위 조립 계통 (part_of)
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              현재 단위 공정이 일부분으로 종속되는 상위 패키징/설비 인프라 모듈입니다.
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {partOfList.length > 0 ? (
              partOfList.map((item) => renderRelationItem(item, '상위 조립 계통', 'part_of'))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>기본 제조 라인 조립 계통</span>
            )}
          </div>
        </div>

        {/* 2. 다음 연계 공정 (next_step) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              ⏩ 다음 연계 공정 (next_step)
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              본 공정 완료 후 웨이퍼/칩이 팹 라인 상에서 즉시 투입되는 후속 공정입니다.
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {nextStepList.length > 0 ? (
              nextStepList.map((item) => renderRelationItem(item, '다음 연계 공정', 'next_step'))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>품질 검사 및 신뢰성 평가</span>
            )}
          </div>
        </div>

        {/* 3. 기술 대안 및 경쟁 기술 (alternative_to) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              🔀 기술적 대체 대안 (alternative_to)
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              동일 제조 목표(예: 방열/수율 확보)를 달성하기 위한 직접 경쟁 공정입니다.
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {altList.length > 0 ? (
              altList.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {renderRelationItem(item, '기술 대안', 'alternative_to')}
                  {item.commonGoal && (
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', paddingLeft: '2px' }}>
                      💡 공통 목표: {item.commonGoal}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>등록된 직접 대체 기술 없음</span>
            )}
          </div>
        </div>

        {/* 4. 분류 체계 (is_a) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              📂 표준 분류 체계 (is_a)
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              반도체 공정 표준 아키텍처 상의 소속 분야 분류입니다.
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {isAList.length > 0 ? (
              isAList.map((item) => renderRelationItem(item, '표준 분류 체계', 'is_a'))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                {conceptDetail.processCategory || '표준 단위 공정'}
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
