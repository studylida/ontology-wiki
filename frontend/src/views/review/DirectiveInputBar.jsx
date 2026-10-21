/**
 * [계층 1] DirectiveInputBar View (Pure Dumb UI Component)
 * - 전문가 자연어 보완 지시문 입력 바 & 3대 무결성 진단 지표 표출
 */

import React, { useState } from 'react';
import { Send, Sparkles, ShieldCheck, CheckCircle2, AlertTriangle, BookCheck } from 'lucide-react';

export function DirectiveInputBar({
  integrityReport,
  directiveHistory = [],
  isActionLoading,
  isEditorDisabled,
  onApplyDirective
}) {
  const [directiveText, setDirectiveText] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverrideInput, setShowOverrideInput] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!directiveText.trim()) return;
    onApplyDirective(directiveText.trim(), overrideReason.trim());
    setDirectiveText('');
    setOverrideReason('');
    setShowOverrideInput(false);
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '16px 20px',
        marginBottom: '16px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 3대 무결성 진단 지표 대시보드 ── */}
      {integrityReport && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '14px', flexWrap: 'wrap' }}>
          {/* AI 신뢰도 점수 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>AI 신뢰도:</span>
            <span
              style={{
                fontWeight: 700,
                color: integrityReport.confidenceScore >= 80 ? 'var(--accent-success)' : 'var(--accent-warning)',
                padding: '2px 6px',
                borderRadius: '4px',
                background: integrityReport.confidenceScore >= 80 ? 'var(--accent-success-light)' : 'var(--accent-warning-light)'
              }}
            >
              {integrityReport.confidenceScore}점
            </span>
          </div>

          {/* 물리 안전 마진 상태 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>물리 마진 검증:</span>
            <span
              style={{
                fontWeight: 700,
                color: integrityReport.physicalMarginValid ? 'var(--accent-success)' : 'var(--accent-danger)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px'
              }}
            >
              {integrityReport.physicalMarginValid ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
              {integrityReport.physicalMarginValid ? '마진 준수' : '마진 초과 (사유 필요)'}
            </span>
          </div>

          {/* 인용된 공인 출처 */}
          {integrityReport.citedEvidenceIds && integrityReport.citedEvidenceIds.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>보존된 출처:</span>
              <div style={{ display: 'flex', gap: '4px' }}>
                {integrityReport.citedEvidenceIds.map((cid) => (
                  <span
                    key={cid}
                    style={{
                      padding: '1px 5px',
                      borderRadius: '4px',
                      background: 'var(--accent-primary-light)',
                      color: 'var(--accent-primary)',
                      fontWeight: 600
                    }}
                  >
                    {cid}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 전문가 자연어 보완 지시문 입력 폼 ── */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Sparkles size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--accent-primary)' }} />
            <input
              type="text"
              value={directiveText}
              onChange={(e) => setDirectiveText(e.target.value)}
              disabled={isEditorDisabled || isActionLoading}
              placeholder="전문가 보완 지시문 입력 (예: IEEE 2024 실측 보이드 억제 압력 조건을 수식 원리에 보정 반영하세요)..."
              style={{
                width: '100%',
                padding: '9px 12px 9px 36px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={!directiveText.trim() || isEditorDisabled || isActionLoading}
            style={{
              padding: '9px 18px',
              borderRadius: '8px',
              border: 'none',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: !directiveText.trim() || isEditorDisabled ? 'not-allowed' : 'pointer',
              opacity: !directiveText.trim() || isEditorDisabled ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Send size={14} />
            <span>지시문 머지</span>
          </button>
        </div>

        {/* 물리 마진 예외 사유 입력 토글 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
          <button
            type="button"
            onClick={() => setShowOverrideInput(!showOverrideInput)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
          >
            {showOverrideInput ? '▲ 물리 마진 예외 사유 닫기' : '+ 물리 안전 마진 예외 사유 입력'}
          </button>
          <span style={{ color: 'var(--text-muted)' }}>
            지시문 적용 시 4-Tier AI가 백서 초안에 지시 사항을 안전하게 병합합니다.
          </span>
        </div>

        {showOverrideInput && (
          <input
            type="text"
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            placeholder="물리 안전 마진(140N 등) 초과 허용 사유를 입력하세요 (선택)"
            style={{
              width: '100%',
              padding: '7px 10px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              fontSize: '0.75rem',
              color: 'var(--text-primary)'
            }}
          />
        )}
      </form>
    </div>
  );
}
