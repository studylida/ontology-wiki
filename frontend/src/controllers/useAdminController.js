/**
 * [계층 2] AdminController Hook
 * [Admin] 수석 검토관 거버넌스 콘솔의 반응형 상태 및 심사/계정 관리 조율기
 */

import { useState, useEffect, useCallback } from 'react';
import { adminRepo } from '../repositories/adminRepo';

export function useAdminController({ currentUser } = {}) {
  const [activeSubTab, setActiveSubTab] = useState('requests'); // 'requests' | 'users'
  const [accessRequests, setAccessRequests] = useState([]);
  const [users, setUsers] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');

  const [isLoading, setIsLoading] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  /**
   * L3 열람 신청 큐 로드
   */
  const loadAccessRequests = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminRepo.listAccessRequests();
      setAccessRequests(Array.isArray(res) ? res : []);
    } catch (err) {
      console.warn('Failed to load access requests:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 엔지니어 계정 목록 로드
   */
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminRepo.listUsers({ limit: 50 });
      setUsers(Array.isArray(res) ? res : []);
    } catch (err) {
      console.warn('Failed to load users:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentUser?.level >= 3) {
      loadAccessRequests();
      loadUsers();
    }
  }, [currentUser, loadAccessRequests, loadUsers]);

  /**
   * L3 열람 신청 승인
   */
  const handleApproveRequest = useCallback(async (requestId) => {
    setIsActionLoading(true);
    try {
      await adminRepo.approveAccessRequest(requestId);
      setNotification({ type: 'success', message: 'L3 보안 문서 열람 신청이 승인되었습니다.' });
      loadAccessRequests();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '승인 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadAccessRequests]);

  /**
   * L3 열람 신청 반려
   */
  const handleRejectRequest = useCallback(async (requestId, reason = '') => {
    setIsActionLoading(true);
    try {
      await adminRepo.rejectAccessRequest(requestId, { reason });
      setNotification({ type: 'success', message: 'L3 보안 문서 열람 신청이 반려되었습니다.' });
      loadAccessRequests();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '반려 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadAccessRequests]);

  /**
   * 권한 레벨 변경 (승격/강등)
   */
  const handleUpdateUserLevel = useCallback(async (userId, newLevel) => {
    setIsActionLoading(true);
    try {
      await adminRepo.updateUserLevel(userId, { level: newLevel });
      setNotification({ type: 'success', message: `엔지니어 권한 레벨이 Level ${newLevel}로 변경되었습니다.` });
      loadUsers();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '권한 변경에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadUsers]);

  /**
   * 계정 활성/비활성 토글
   */
  const handleToggleUserActive = useCallback(async (userId, currentActive, userLevel) => {
    setIsActionLoading(true);
    try {
      await adminRepo.updateUserLevel(userId, { level: userLevel, isActive: !currentActive });
      setNotification({
        type: 'success',
        message: !currentActive ? '계정이 활성화되었습니다.' : '계정이 비활성화되었습니다.'
      });
      loadUsers();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '계정 상태 변경에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadUsers]);

  // 필터링된 열람 신청 목록
  const filteredRequests = accessRequests.filter((r) => {
    if (filterStatus === 'all') return true;
    return r.status === filterStatus;
  });

  return {
    activeSubTab,
    accessRequests: filteredRequests,
    totalRequestsCount: accessRequests.length,
    users,
    filterStatus,
    isLoading,
    isActionLoading,
    notification,

    setActiveSubTab,
    setFilterStatus,
    loadAccessRequests,
    loadUsers,
    handleApproveRequest,
    handleRejectRequest,
    handleUpdateUserLevel,
    handleToggleUserActive,
    clearNotification: () => setNotification(null)
  };
}
