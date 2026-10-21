/**
 * [계층 1] AdminConsoleView (Pure Dumb UI Component)
 * - [Admin] 수석 검토관 거버넌스 콘솔 메인 뷰
 * - L3 비인가 열람 신청 심사 큐 & 엔지니어 계정 관리 탭 조율
 */

import React from 'react';
import { ShieldAlert, ShieldCheck, Users, CheckCircle2, AlertTriangle, X } from 'lucide-react';
import { AccessRequestQueue } from './AccessRequestQueue';
import { UserManagementTable } from './UserManagementTable';

export function AdminConsoleView({
  activeSubTab = 'requests',
  accessRequests = [],
  totalRequestsCount = 0,
  users = [],
  filterStatus = 'all',
  isLoading = false,
  isActionLoading = false,
  notification = null,
  currentUser = null,

  setActiveSubTab,
  setFilterStatus,
  handleApproveRequest,
  handleRejectRequest,
  handleUpdateUserLevel,
  handleToggleUserActive,
  clearNotification
}) {
  return (
    <div className="tab-pane active" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── 글로벌 토스트 알림 ── */}
      {notification && (
        <div
          className="toast-notification show"
          style={{
            position: 'fixed',
            top: '80px',
            right: '24px',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            borderRadius: '8px',
            fontSize: '0.8125rem',
            fontWeight: 600,
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
            background: notification.type === 'error' ? '#ef4444' : notification.type === 'warning' ? '#f59e0b' : '#10b981',
            color: '#fff'
          }}
        >
          {notification.type === 'error' || notification.type === 'warning' ? (
            <AlertTriangle size={18} />
          ) : (
            <CheckCircle2 size={18} />
          )}
          <span>{notification.message}</span>
          <button
            type="button"
            onClick={clearNotification}
            style={{
              background: 'none',
              border: 'none',
              color: '#fff',
              cursor: 'pointer',
              marginLeft: '8px',
              padding: '2px'
            }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* ── 상단 헤더 및 서브탭 바 ── */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px 24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <ShieldAlert size={20} style={{ color: 'var(--accent-danger)' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              수석 검토관 거버넌스 콘솔 (Governance Console)
            </h2>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
            L3 극비 공정 데이터 열람 심사 및 엔지니어 4단계 RBAC 권한을 통합 관리합니다.
          </p>
        </div>

        {/* 서브탭 */}
        <div className="sliding-tabs-container">
          <button
            type="button"
            className={`sliding-tab-item ${activeSubTab === 'requests' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('requests')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <ShieldCheck size={14} />
            <span>L3 열람 신청 심사 ({totalRequestsCount})</span>
          </button>
          <button
            type="button"
            className={`sliding-tab-item ${activeSubTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('users')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Users size={14} />
            <span>엔지니어 계정 및 권한 관리 ({users.length})</span>
          </button>
        </div>
      </div>

      {/* ── 서브 화면 ── */}
      {activeSubTab === 'requests' && (
        <AccessRequestQueue
          accessRequests={accessRequests}
          filterStatus={filterStatus}
          isActionLoading={isActionLoading}
          onSelectFilter={setFilterStatus}
          onApprove={handleApproveRequest}
          onReject={handleRejectRequest}
        />
      )}

      {activeSubTab === 'users' && (
        <UserManagementTable
          users={users}
          isActionLoading={isActionLoading}
          onUpdateLevel={handleUpdateUserLevel}
          onToggleActive={handleToggleUserActive}
        />
      )}
    </div>
  );
}
