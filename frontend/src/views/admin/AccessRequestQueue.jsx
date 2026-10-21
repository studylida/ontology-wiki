/**
 * [계층 1] AccessRequestQueue View (Pure Dumb UI Component)
 * - L3 극비 보안 파라미터 비인가 열람 신청 심사 큐 테이블
 */

import React from 'react';
import { ShieldCheck, ShieldAlert, Check, X, Clock } from 'lucide-react';

const STATUS_BADGES = {
  pending: { label: '심사 대기', color: '#d97706', bg: 'rgba(217, 119, 6, 0.1)' },
  approved: { label: '열람 승인', color: '#059669', bg: 'rgba(5, 150, 105, 0.1)' },
  rejected: { label: '신청 반려', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)' }
};

export function AccessRequestQueue({
  accessRequests = [],
  filterStatus = 'all',
  isActionLoading = false,
  onSelectFilter,
  onApprove,
  onReject
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* 필터 탭 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="sliding-tabs-container">
          {['all', 'pending', 'approved', 'rejected'].map((s) => (
            <button
              key={s}
              type="button"
              className={`sliding-tab-item ${filterStatus === s ? 'active' : ''}`}
              onClick={() => onSelectFilter(s)}
            >
              {s === 'all' ? '전체' : STATUS_BADGES[s]?.label}
            </button>
          ))}
        </div>
      </div>

      {/* 테이블 */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border-color)', background: 'var(--bg-surface-2)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '12px 16px', width: '12%' }}>신청 ID</th>
              <th style={{ padding: '12px 16px', width: '16%' }}>신청 엔지니어</th>
              <th style={{ padding: '12px 16px', width: '16%' }}>대상 개념 ID</th>
              <th style={{ padding: '12px 16px', width: '28%' }}>열람 신청 사유</th>
              <th style={{ padding: '12px 16px', width: '12%' }}>심사 상태</th>
              <th style={{ padding: '12px 16px', width: '16%', textAlign: 'center' }}>거버넌스 심사</th>
            </tr>
          </thead>
          <tbody>
            {accessRequests.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  해당 조건의 L3 열람 신청 내역이 없습니다.
                </td>
              </tr>
            ) : (
              accessRequests.map((req) => {
                const badge = STATUS_BADGES[req.status] || STATUS_BADGES.pending;
                const isPending = req.status === 'pending';

                return (
                  <tr
                    key={req.id}
                    style={{ borderBottom: '1px solid var(--border-color)' }}
                  >
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {req.id}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {req.userName || req.userId}
                      </div>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                        {req.userDepartment || '미지정'}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)', fontWeight: 600 }}>
                      {req.targetConceptId}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {req.reason}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '4px',
                          color: badge.color,
                          background: badge.bg
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      {isPending ? (
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                          <button
                            type="button"
                            disabled={isActionLoading}
                            onClick={() => onApprove(req.id)}
                            style={{
                              padding: '5px 10px',
                              borderRadius: '4px',
                              border: 'none',
                              background: '#059669',
                              color: '#fff',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              cursor: isActionLoading ? 'not-allowed' : 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <Check size={12} />
                            <span>승인</span>
                          </button>
                          <button
                            type="button"
                            disabled={isActionLoading}
                            onClick={() => onReject(req.id)}
                            style={{
                              padding: '5px 10px',
                              borderRadius: '4px',
                              border: '1px solid var(--border-color)',
                              background: 'var(--bg-surface)',
                              color: '#dc2626',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: isActionLoading ? 'not-allowed' : 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <X size={12} />
                            <span>반려</span>
                          </button>
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          처리 완료
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
