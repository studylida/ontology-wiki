/**
 * [계층 2] Dashboard Controller Hook
 * 대시보드 화면(온톨로지 통계, 4대 서브시스템 헬스, WORM 머클 체인 무결성) 상태 제어
 */

import { useState, useEffect, useCallback } from 'react';
import { systemRepo } from '../repositories/systemRepo';

export function useDashboardController({ currentUser } = {}) {
  const [healthData, setHealthData] = useState(null);
  const [versionData, setVersionData] = useState(null);
  const [auditData, setAuditData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [health, version] = await Promise.all([
        systemRepo.getHealth().catch(() => null),
        systemRepo.getVersion().catch(() => null)
      ]);
      setHealthData(health);
      setVersionData(version);

      // Level 3 이상일 때만 암호학적 머클 체인 무결성 검증
      if (currentUser && currentUser.level >= 3) {
        const audit = await systemRepo.verifyAuditIntegrity().catch(() => null);
        setAuditData(audit);
      }
    } catch (err) {
      setError(err.message || '대시보드 통계를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    healthData,
    versionData,
    auditData,
    isLoading,
    error,
    refreshDashboard: loadDashboard
  };
}
