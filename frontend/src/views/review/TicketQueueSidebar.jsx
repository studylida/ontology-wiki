/**
 * [계층 1] TicketQueueSidebar View (Pure Dumb UI Component)
 * - 좌측 거버넌스 티켓 큐 사이드바 (상태 필터링 & 티켓 선택)
 */

import React from 'react';
import { CheckCircle2, Clock, XCircle, FileText, User } from 'lucide-react';
import { formatService } from '../../services/formatService';

const STATUS_FILTERS = [
  { id: 'all', label: '전체' },
  { id: 'pending', label: '대기 중' },
  { id: 'approved', label: '승인됨' },
  { id: 'rejected', label: '반려됨' }
];

export function TicketQueueSidebar({
  ticketList = [],
  selectedTicketId,
  statusFilter,
  isLoading,
  onSelectStatus,
  onSelectTicket
}) {
  return (
    <aside
      style={{
        width: '320px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--topbar-height) - 40px)',
        position: 'sticky',
        top: 'calc(var(--topbar-height) + 20px)',
        overflow: 'hidden'
      }}
    >
      {/* 큐 헤더 & 상태 탭 */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            거버넌스 검토 큐
          </h3>
          <span
            style={{
              fontSize: '0.6875rem',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'var(--accent-primary-light)',
              color: 'var(--accent-primary)'
            }}
          >
            {ticketList.length}건
          </span>
        </div>

        {/* 상태 필터 탭 (Transitions.dev sliding-tabs) */}
        <div className="sliding-tabs-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', padding: '2px' }}>
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              className={`sliding-tab-item ${statusFilter === f.id ? 'active' : ''}`}
              style={{ padding: '4px 2px', fontSize: '0.75rem', textAlign: 'center' }}
              onClick={() => onSelectStatus(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 티켓 목록 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {isLoading ? (
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="skeleton-line" style={{ width: '80%' }} />
            <div className="skeleton-line" style={{ width: '60%' }} />
            <div className="skeleton-line" style={{ width: '90%' }} />
          </div>
        ) : ticketList.length === 0 ? (
          <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
            검토 대기 중인 티켓이 없습니다.
          </div>
        ) : (
          ticketList.map((ticket) => {
            const isSelected = selectedTicketId === ticket.id;
            const isApproved = ticket.status === 'approved';
            const isRejected = ticket.status === 'rejected';

            return (
              <div
                key={ticket.id}
                onClick={() => onSelectTicket(ticket.id)}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                  background: isSelected ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {/* 상단 티켓 ID & 상태 배지 */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {ticket.id}
                  </span>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: isApproved
                        ? 'var(--accent-success-light)'
                        : isRejected
                        ? 'var(--accent-danger-light)'
                        : 'var(--accent-warning-light)',
                      color: isApproved
                        ? 'var(--accent-success)'
                        : isRejected
                        ? 'var(--accent-danger)'
                        : 'var(--accent-warning)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '3px'
                    }}
                  >
                    {isApproved ? <CheckCircle2 size={11} /> : isRejected ? <XCircle size={11} /> : <Clock size={11} />}
                    {isApproved ? '승인됨' : isRejected ? '반려됨' : '심사 대기'}
                  </span>
                </div>

                {/* 티켓 제목 */}
                <h4
                  style={{
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    margin: '0 0 6px 0',
                    color: 'var(--text-primary)',
                    lineHeight: 1.4,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical'
                  }}
                >
                  {ticket.title}
                </h4>

                {/* 대상 개념 및 발의자 메타데이터 */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>
                    {ticket.conceptTitle || ticket.conceptId}
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                    <User size={11} />
                    {ticket.author || '엔지니어'}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
