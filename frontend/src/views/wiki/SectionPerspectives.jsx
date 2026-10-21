/**
 * [계층 1] SectionPerspectives View (Pure Dumb UI Component)
 * - 4번 섹션: 3단계 적응형 실무 사례 (Perspective Cases)
 * - 🌟 L3 극비 파라미터 4단계 열람 인가 라이프사이클 화면 표출
 *   ① 미신청 [열람 권한 신청 ➔]
 *   ② 심사 대기 중 [신청 취소]
 *   ③ 승인 완료 [🔓 인가된 지식]
 *   ④ 반려됨 [❌ 사유 확인]
 */

import React, { useState } from 'react';
import { ShieldCheck, Lock, Unlock, Clock, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

export function SectionPerspectives({
  perspectives = [],
  l3AccessStatus, // { hasAccess: boolean, requestStatus: 'none'|'pending'|'approved'|'rejected', request?: any }
  currentUser,
  onOpenAccessModal,
  onCancelAccessRequest
}) {
  const [activeTabIdx, setActiveTabIdx] = useState(0);

  if (!perspectives || perspectives.length === 0) return null;

  const currentPerspective = perspectives[activeTabIdx] || perspectives[0];

  return (
    <section
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
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
            4
          </div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            적응형 실무 사례 및 파라미터 (Adaptive Perspectives & L3 Specs)
          </h2>
        </div>

        {/* L3 열람 인가 상태 종합 배지 */}
        <div>
          {currentUser?.level >= 3 ? (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'var(--accent-primary-light)',
                color: 'var(--accent-primary)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <ShieldCheck size={13} />
              수석 검토관(Level {currentUser.level}) 자동 전면 인가
            </span>
          ) : l3AccessStatus.hasAccess ? (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'var(--accent-success-light)',
                color: 'var(--accent-success)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Unlock size={13} />
              🔓 인가된 지식 (L3 열람 승인됨)
            </span>
          ) : l3AccessStatus.requestStatus === 'pending' ? (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'var(--accent-warning-light)',
                color: 'var(--accent-warning)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Clock size={13} />
              ⏳ 열람 심사 대기 중
            </span>
          ) : (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-muted)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Lock size={13} />
              Tier 3 대외비 파라미터 포함
            </span>
          )}
        </div>
      </div>

      {/* 관점 선택 탭 스위처 */}
      {perspectives.length > 1 && (
        <div className="sliding-tabs-container" style={{ marginBottom: '16px', display: 'flex', gap: '4px' }}>
          {perspectives.map((p, idx) => (
            <button
              key={p.id || idx}
              type="button"
              className={`sliding-tab-item ${activeTabIdx === idx ? 'active' : ''}`}
              onClick={() => setActiveTabIdx(idx)}
            >
              {p.perspectiveTitle || `사례 ${idx + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* 활성 관점 상세 박스 */}
      <div
        style={{
          background: 'var(--bg-surface-2)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '20px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            {currentPerspective.perspectiveTitle}
          </h3>
          {currentPerspective.managementCode && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              관리코드: {currentPerspective.managementCode}
            </span>
          )}
        </div>

        {currentPerspective.contextNarrative && (
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
            {currentPerspective.contextNarrative}
          </p>
        )}

        {/* 핵심 파라미터 스펙 테이블 */}
        {currentPerspective.specifications && currentPerspective.specifications.length > 0 && (
          <div style={{ overflowX: 'auto', marginBottom: '14px' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.8125rem',
                textAlign: 'left'
              }}
            >
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>파라미터 항목</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>공정 기준값 (Value)</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>단위</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>물리 안전 마진</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>보안 등급 및 인가 상태</th>
                </tr>
              </thead>
              <tbody>
                {currentPerspective.specifications.map((spec, sIdx) => {
                  const isConf = spec.isConfidential || currentPerspective.isMasked || spec.value.includes('***');
                  return (
                    <tr
                      key={sIdx}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        background: isConf && !l3AccessStatus.hasAccess ? 'rgba(239, 68, 68, 0.02)' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '10px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {spec.parameter}
                      </td>
                      <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {/* 🌟 마스킹 여부에 따른 분기 */}
                        {isConf && !l3AccessStatus.hasAccess ? (
                          <span style={{ color: 'var(--accent-danger)', letterSpacing: '2px' }}>***</span>
                        ) : (
                          <span style={{ color: 'var(--accent-primary)' }}>{spec.value}</span>
                        )}
                      </td>
                      <td style={{ padding: '10px', color: 'var(--text-muted)' }}>{spec.unit}</td>
                      <td style={{ padding: '10px', color: 'var(--text-secondary)' }}>
                        {spec.safetyMargin || '-'}
                      </td>
                      <td style={{ padding: '10px' }}>
                        {isConf ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {l3AccessStatus.hasAccess ? (
                              <span
                                style={{
                                  fontSize: '0.6875rem',
                                  fontWeight: 700,
                                  color: 'var(--accent-success)',
                                  background: 'var(--accent-success-light)',
                                  padding: '2px 6px',
                                  borderRadius: '4px'
                                }}
                              >
                                🔓 인가됨
                              </span>
                            ) : l3AccessStatus.requestStatus === 'pending' ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span
                                  style={{
                                    fontSize: '0.6875rem',
                                    fontWeight: 700,
                                    color: 'var(--accent-warning)',
                                    background: 'var(--accent-warning-light)',
                                    padding: '2px 6px',
                                    borderRadius: '4px'
                                  }}
                                >
                                  ⏳ 심사 대기
                                </span>
                                {l3AccessStatus.request && (
                                  <button
                                    type="button"
                                    onClick={() => onCancelAccessRequest(l3AccessStatus.request.id)}
                                    style={{
                                      fontSize: '0.6875rem',
                                      padding: '2px 6px',
                                      borderRadius: '4px',
                                      border: '1px solid var(--border-color)',
                                      background: 'var(--bg-surface)',
                                      color: 'var(--text-muted)',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    취소
                                  </button>
                                )}
                              </div>
                            ) : l3AccessStatus.requestStatus === 'rejected' ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span
                                  style={{
                                    fontSize: '0.6875rem',
                                    fontWeight: 700,
                                    color: 'var(--accent-danger)',
                                    background: 'var(--accent-danger-light)',
                                    padding: '2px 6px',
                                    borderRadius: '4px'
                                  }}
                                >
                                  ❌ 반려됨
                                </span>
                                <button
                                  type="button"
                                  onClick={onOpenAccessModal}
                                  style={{
                                    fontSize: '0.6875rem',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    border: '1px solid var(--accent-primary)',
                                    background: 'var(--accent-primary)',
                                    color: '#fff',
                                    cursor: 'pointer'
                                  }}
                                >
                                  재신청
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={onOpenAccessModal}
                                style={{
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  padding: '3px 8px',
                                  borderRadius: '4px',
                                  border: '1px solid var(--accent-primary)',
                                  background: 'var(--accent-primary-light)',
                                  color: 'var(--accent-primary)',
                                  cursor: 'pointer'
                                }}
                              >
                                🔒 열람 권한 신청 ➔
                              </button>
                            )}
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>공개 파라미터</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 주의사항 (Caution) */}
        {currentPerspective.caution && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '6px',
              background: 'var(--accent-danger-light)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              fontSize: '0.8125rem',
              color: 'var(--accent-danger)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <AlertCircle size={15} />
            <span>{currentPerspective.caution}</span>
          </div>
        )}
      </div>
    </section>
  );
}
