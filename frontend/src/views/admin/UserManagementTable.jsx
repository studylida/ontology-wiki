/**
 * [계층 1] UserManagementTable View (Pure Dumb UI Component)
 * - 엔지니어 계정 목록 및 4단계 RBAC 권한 레벨(승격/강등) 관리 테이블
 */

import React from 'react';
import { UserCheck, UserX, Shield, Users } from 'lucide-react';

const LEVEL_NAMES = {
  1: 'Level 1 (게스트)',
  2: 'Level 2 (현장 엔지니어)',
  3: 'Level 3 (수석 검토관)',
  4: 'Level 4 (시스템 관리자)'
};

const LEVEL_COLORS = {
  1: { color: 'var(--text-muted)', bg: 'var(--bg-surface-2)' },
  2: { color: '#2563eb', bg: 'rgba(37, 99, 235, 0.1)' },
  3: { color: '#7c3aed', bg: 'rgba(124, 58, 237, 0.1)' },
  4: { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)' }
};

export function UserManagementTable({
  users = [],
  isActionLoading = false,
  onUpdateLevel,
  onToggleActive
}) {
  return (
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
            <th style={{ padding: '12px 16px', width: '16%' }}>사번 (ID)</th>
            <th style={{ padding: '12px 16px', width: '22%' }}>엔지니어 성명 / 계정명</th>
            <th style={{ padding: '12px 16px', width: '20%' }}>소속 부서</th>
            <th style={{ padding: '12px 16px', width: '22%' }}>권한 레벨 (RBAC 조정)</th>
            <th style={{ padding: '12px 16px', width: '20%', textAlign: 'center' }}>계정 상태</th>
          </tr>
        </thead>
        <tbody>
          {users.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                등록된 엔지니어 계정이 없습니다.
              </td>
            </tr>
          ) : (
            users.map((u) => {
              const lvlMeta = LEVEL_COLORS[u.level] || LEVEL_COLORS[2];

              return (
                <tr
                  key={u.id}
                  style={{ borderBottom: '1px solid var(--border-color)', opacity: u.isActive ? 1 : 0.6 }}
                >
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {u.id}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      {u.name}
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      @{u.username}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {u.department}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <select
                      value={u.level}
                      disabled={isActionLoading}
                      onChange={(e) => onUpdateLevel(u.id, parseInt(e.target.value, 10))}
                      style={{
                        padding: '5px 8px',
                        borderRadius: '6px',
                        border: '1px solid var(--border-color)',
                        background: lvlMeta.bg,
                        color: lvlMeta.color,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: isActionLoading ? 'not-allowed' : 'pointer'
                      }}
                    >
                      <option value={1}>Level 1 (게스트 · 열람)</option>
                      <option value={2}>Level 2 (현장 엔지니어 · 발의/편집)</option>
                      <option value={3}>Level 3 (수석 검토관 · 승인/거버넌스)</option>
                      <option value={4}>Level 4 (시스템 관리자 · 전권한)</option>
                    </select>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    <button
                      type="button"
                      disabled={isActionLoading}
                      onClick={() => onToggleActive(u.id, u.isActive, u.level)}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '4px',
                        border: '1px solid var(--border-color)',
                        background: u.isActive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: u.isActive ? '#059669' : '#dc2626',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: isActionLoading ? 'not-allowed' : 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      {u.isActive ? <UserCheck size={13} /> : <UserX size={13} />}
                      <span>{u.isActive ? '활성 계정' : '계정 차단'}</span>
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
