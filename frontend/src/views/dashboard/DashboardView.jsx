/**
 * [계층 1] DashboardView (Pure Dumb UI Component)
 * - [Home] 대시보드 화면
 * - 온톨로지 전체 통계, 4대 서브시스템 헬스, 4-Facet 퀵 네비게이션
 * - WORM 머클 체인 무결성 상태 표출 (Level >= 3)
 */

import React from 'react';
import {
  LayoutDashboard,
  Server,
  Database,
  Cpu,
  Layers,
  Activity,
  Box,
  ShieldCheck,
  Hash,
  ArrowRight,
  BookOpen,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { formatService } from '../../services/formatService';

export function DashboardView({
  dashboard,
  currentUser,
  onNavigateWiki
}) {
  const { healthData, versionData, auditData, isLoading, refreshDashboard } = dashboard;

  const FACET_CARDS = [
    {
      id: 'unit_process',
      title: '단위 공정 (Unit Process)',
      description: 'TCB, 하이브리드 본딩, 극저온 식각(Cryo-ALE), CMP, 화학기상증착(CVD)',
      icon: Layers,
      color: '#0ea5e9',
      bg: '#f0f9ff'
    },
    {
      id: 'device',
      title: '반도체 소자 (Device)',
      description: 'GAAFET, FinFET, 3D V-NAND 적층 셀, HBM 코어 다이 구조',
      icon: Cpu,
      color: '#6366f1',
      bg: '#eef2ff'
    },
    {
      id: 'operations',
      title: 'Fab 운영/수율 (Operations)',
      description: 'APC 실시간 피드포워드, FDC 이상 감지, 인과 결함 계측 거버넌스',
      icon: Activity,
      color: '#10b981',
      bg: '#ecfdf5'
    },
    {
      id: 'materials_infra',
      title: '소재 및 클린룸 인프라 (Infra)',
      description: 'NCF/MUF 언더필, EUV 포토레지스트, 초순수(UPW) 및 배기 정밀 제어',
      icon: Box,
      color: '#f59e0b',
      bg: '#fffbeb'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* ── 1. 대시보드 환영 및 통계 그리드 ── */}
      <section
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '24px 28px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <LayoutDashboard size={20} style={{ color: 'var(--accent-primary)' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                반도체 인과 온톨로지 통합 거버넌스 대시보드
              </h2>
            </div>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
              반도체 공정 및 소자의 물리적 인과 관계망, 안전 마진 수식 및 산업 실무 지식 베이스
            </p>
          </div>

          <button
            type="button"
            onClick={refreshDashboard}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
            <span>새로고침</span>
          </button>
        </div>

        {/* 4대 핵심 지표 카드 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <div style={{ background: 'var(--bg-surface-2)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>온톨로지 공정 개념</span>
            <div style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--accent-primary)', marginTop: '4px' }}>
              {versionData?.totalConcepts || 61}
              <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '4px' }}>개</span>
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>공인 출처/증거(Evidence)</span>
            <div style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--accent-success)', marginTop: '4px' }}>
              {versionData?.totalEvidences || 104}
              <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '4px' }}>건</span>
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>활성 온톨로지 버전</span>
            <div style={{ fontSize: '1.625rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
              {versionData?.activeVersion || 'v1.2'}
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-success)', marginLeft: '6px' }}>최신</span>
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>시스템 상태</span>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-success)', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-success)' }} />
              <span>{healthData?.status === 'healthy' ? '정상 가동 중' : '안전 모드 가동'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. 4축 온톨로지 작업 공간 바로가기 ── */}
      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            온톨로지 4대 업무 분류 탐색
          </h3>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            카드를 클릭하면 [Tab 1] 위키 브라우저의 해당 분류로 즉시 이동합니다.
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {FACET_CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.id}
                onClick={() => onNavigateWiki(card.id)}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '16px'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = card.color;
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '8px',
                    background: card.bg,
                    color: card.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  <Icon size={22} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                      {card.title}
                    </h4>
                    <ArrowRight size={15} style={{ color: 'var(--text-muted)' }} />
                  </div>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {card.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── 3. 코어 서브엔진 연결 상태 및 WORM 머클 체인 ── */}
      <section
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px 24px'
        }}
      >
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-primary)' }}>
          온톨로지 코어 인프라 연동 상태 (4-Tier Gateway)
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          <div style={{ background: 'var(--bg-surface-2)', padding: '12px 14px', borderRadius: '6px', fontSize: '0.8125rem' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>RDBMS 물리 데이터베이스</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-success)' }}>
              ● {healthData?.services?.database === 'connected' ? '정상 연결 (SQLite/PostgreSQL)' : '연결 대기'}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '12px 14px', borderRadius: '6px', fontSize: '0.8125rem' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>인메모리 캐시 & 서킷브레이커</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-success)' }}>
              ● {healthData?.services?.redisCache || '정상 가동 (Memory Cache)'}
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-2)', padding: '12px 14px', borderRadius: '6px', fontSize: '0.8125rem' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>AI 추론 게이트웨이 (Tier 1~2)</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
              ● {healthData?.services?.llmGateway === 'ready' ? 'Ready (GPT-4o / Gemini Flash)' : 'Fallback Safe Mode'}
            </div>
          </div>
        </div>

        {/* Level 3 이상 수석검토관 전용 WORM 머클 감사 체인 상태 */}
        {currentUser?.level >= 3 && auditData && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              borderRadius: '8px',
              background: auditData.valid ? 'var(--accent-success-light)' : 'var(--accent-danger-light)',
              border: `1px solid ${auditData.valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.8125rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} style={{ color: auditData.valid ? 'var(--accent-success)' : 'var(--accent-danger)' }} />
              <span>
                <strong>WORM 머클 감사로그 무결성 검증:</strong>{' '}
                {auditData.valid ? '암호학적 해시체인 변조 없음 (무결성 100% 입증)' : '해시 체인 불일치 감지'}
              </span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Merkle Root: {auditData.merkleRootHash?.slice(0, 16)}...
            </span>
          </div>
        )}
      </section>
    </div>
  );
}
