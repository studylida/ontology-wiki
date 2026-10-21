/**
 * [계층 1] SetupTrackSelector View (Pure Dumb UI Component)
 * - 화면 2-A (조건 설정 단계)
 * - Track 1: 자연어 탐색창 (회색 placeholder + 미니멀 단어 칩) & 3대 공학 분기 카드
 * - Track 2: 대상 A/B 지능형 직접 지정
 */

import React, { useState } from 'react';
import { Sparkles, Search, GitCompare, ArrowRight, Layers, Cpu, CheckCircle2 } from 'lucide-react';

const SUGGESTED_CHIPS = [
  'MR-MUF vs TC-NCF',
  '하이브리드 본딩 방열',
  'Cryo 극저온 식각'
];

export function SetupTrackSelector({
  trackMode,
  query,
  isClarifying,
  clarifyResult,
  targetA,
  targetB,
  domain,
  onSelectTrackMode,
  onQueryChange,
  onClarifyQuery,
  onSelectBranch,
  onTargetAChange,
  onTargetBChange,
  onDomainChange,
  onStartDirectComparison
}) {
  const [localQuery, setLocalQuery] = useState(query);

  const handleSubmitTrack1 = (e) => {
    e.preventDefault();
    if (!localQuery.trim()) return;
    onClarifyQuery(localQuery.trim());
  };

  const handleChipClick = (chipText) => {
    setLocalQuery(chipText);
    onClarifyQuery(chipText);
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '28px 32px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 2-Track 탭 스위처 (Transitions.dev sliding-tabs) ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            기술 대안 비교 분석 전제 설정
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            목적에 따라 자연어 탐색(Track 1) 또는 대상 직접 지정(Track 2)을 선택하세요.
          </p>
        </div>

        <div className="sliding-tabs-container">
          <button
            type="button"
            className={`sliding-tab-item ${trackMode === 'track1' ? 'active' : ''}`}
            onClick={() => onSelectTrackMode('track1')}
          >
            Track 1: 자연어 질의 구체화
          </button>
          <button
            type="button"
            className={`sliding-tab-item ${trackMode === 'track2' ? 'active' : ''}`}
            onClick={() => onSelectTrackMode('track2')}
          >
            Track 2: 대상 A/B 직접 지정
          </button>
        </div>
      </div>

      {/* ── Track 1: 자연어 탐색창 ── */}
      {trackMode === 'track1' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <form onSubmit={handleSubmitTrack1}>
            <div style={{ position: 'relative', marginBottom: '8px' }}>
              <Search size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={localQuery}
                onChange={(e) => {
                  setLocalQuery(e.target.value);
                  onQueryChange(e.target.value);
                }}
                placeholder="예: HBM3E 16단 적층에서 MR-MUF와 TC-NCF의 열저항 및 휨(Warpage) 특성 비교해줘"
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  fontSize: '0.875rem',
                  color: 'var(--text-primary)',
                  outline: 'none'
                }}
              />
              <button
                type="submit"
                disabled={isClarifying || !localQuery.trim()}
                style={{
                  position: 'absolute',
                  right: '8px',
                  top: '7px',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent-primary)',
                  color: '#ffffff',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: isClarifying ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Sparkles size={13} />
                <span>{isClarifying ? '분석 중...' : '구체화'}</span>
              </button>
            </div>

            {/* 💡 추천 단어 키워드 칩 (한 줄 안내) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>💡 추천 키워드:</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                {SUGGESTED_CHIPS.map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => handleChipClick(chip)}
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-surface-2)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      cursor: 'pointer'
                    }}
                  >
                    [{chip}]
                  </button>
                ))}
              </div>
            </div>
          </form>

          {/* 3대 공학 분기 카드 (Clarification Branch Cards) */}
          {clarifyResult?.branches && clarifyResult.branches.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px' }}>
                분석 의도에 적합한 공학 비교 분기를 선택하세요:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                {clarifyResult.branches.map((b) => (
                  <div
                    key={b.branchId}
                    onClick={() => onSelectBranch(b)}
                    style={{
                      background: 'var(--bg-surface-2)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--accent-primary)';
                      e.currentTarget.style.background = 'var(--accent-primary-light)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-color)';
                      e.currentTarget.style.background = 'var(--bg-surface-2)';
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '4px' }}>
                        {b.targetA} vs {b.targetB}
                      </div>
                      <h4 style={{ fontSize: '0.875rem', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                        {b.title}
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                        {b.description}
                      </p>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginTop: '12px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                      <span>비교 시작</span>
                      <ArrowRight size={13} style={{ marginLeft: '4px' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Track 2: 대상 A/B 직접 지정 ── */}
      {trackMode === 'track2' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '16px', alignItems: 'center' }}>
            {/* 대상 A */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                비교 대상 A (Target A)
              </label>
              <select
                value={targetA}
                onChange={(e) => onTargetAChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  fontSize: '0.875rem',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="concept-mrmuf">MR-MUF (매스리플로우 몰디드 언더필)</option>
                <option value="concept-tcb">TC-NCF / TCB (열압착 비도전성 필름)</option>
                <option value="concept-hybrid-bonding">하이브리드 다이렉트 Cu-Cu 본딩</option>
                <option value="concept-cryo-etch">극저온 원자층 식각 (Cryo-ALE)</option>
              </select>
            </div>

            {/* VS 아이콘 */}
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '0.75rem',
                color: 'var(--accent-primary)',
                marginTop: '20px'
              }}
            >
              VS
            </div>

            {/* 대상 B */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                비교 대상 B (Target B)
              </label>
              <select
                value={targetB}
                onChange={(e) => onTargetBChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  fontSize: '0.875rem',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="concept-tcb">TC-NCF / TCB (열압착 비도전성 필름)</option>
                <option value="concept-mrmuf">MR-MUF (매스리플로우 몰디드 언더필)</option>
                <option value="concept-hybrid-bonding">하이브리드 다이렉트 Cu-Cu 본딩</option>
                <option value="concept-cryo-etch">극저온 원자층 식각 (Cryo-ALE)</option>
              </select>
            </div>
          </div>

          {/* 적용 도메인 판본 */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              적용 공정 도메인
            </label>
            <select
              value={domain}
              onChange={(e) => onDomainChange(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                fontSize: '0.8125rem'
              }}
            >
              <option value="hbm3e_advanced">HBM3E 12단/16단 첨단 적층 패키징</option>
              <option value="foundry_sub2nm">파운드리 Sub-2nm GAAFET</option>
              <option value="dram_process">DRAM 초미세 커패시터 공정</option>
              <option value="nand_high_stack">3D V-NAND 초고단 식각</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onStartDirectComparison}
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                border: 'none',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                fontSize: '0.875rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <GitCompare size={15} />
              <span>다차원 인과 비교 분석 실행 ➔</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
