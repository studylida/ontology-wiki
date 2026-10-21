/**
 * [계층 2] Auth Controller Hook
 * 화면별 반응형 인증 상태 및 사용자 액션 조율기
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { authRepo } from '../repositories/authRepo';
import { tokenService } from '../services/tokenService';
import { authService } from '../services/authService';
import { validateLoginDTO, validateRegisterDTO } from '../types/auth.dto';

export function useAuthController() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [myAccessRequests, setMyAccessRequests] = useState([]);

  /**
   * 내 열람 신청 목록 갱신
   */
  const loadMyAccessRequests = useCallback(async () => {
    try {
      const requests = await authRepo.getMyAccessRequests();
      setMyAccessRequests(requests || []);
    } catch {
      // 비로그인 상태이거나 실패 시 빈 배열
      setMyAccessRequests([]);
    }
  }, []);

  /**
   * 세션 복원 및 현재 사용자 프로필 로드
   */
  const restoreSession = useCallback(async () => {
    setIsLoading(true);
    const token = tokenService.getToken();
    if (!token) {
      setCurrentUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      return;
    }

    const inspection = tokenService.inspectToken(token);
    if (!inspection.valid) {
      tokenService.removeToken();
      setCurrentUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      return;
    }

    try {
      const user = await authRepo.getMe();
      setCurrentUser(user);
      setIsAuthenticated(true);
      await loadMyAccessRequests();
    } catch {
      tokenService.removeToken();
      setCurrentUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, [loadMyAccessRequests]);

  // 마운트 시 세션 복원 및 만료 이벤트 바인딩
  useEffect(() => {
    restoreSession();

    const handleAuthExpired = () => {
      setCurrentUser(null);
      setIsAuthenticated(false);
      setError('인증 세션이 만료되었습니다. 다시 로그인해 주세요.');
      setIsAuthModalOpen(true);
      setAuthMode('login');
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, [restoreSession]);

  /**
   * 로그인 액션
   */
  const login = useCallback(
    async (credentials) => {
      setError(null);
      setFieldErrors({});

      const validation = validateLoginDTO(credentials);
      if (!validation.isValid) {
        setFieldErrors(validation.errors);
        return false;
      }

      setIsLoading(true);
      try {
        const response = await authRepo.login(credentials);
        tokenService.setToken(response.accessToken);
        setCurrentUser(response.user);
        setIsAuthenticated(true);
        setIsAuthModalOpen(false);
        await loadMyAccessRequests();
        return true;
      } catch (err) {
        setError(err.message || '로그인에 실패했습니다.');
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [loadMyAccessRequests]
  );

  /**
   * 회원가입 액션
   */
  const register = useCallback(
    async (formData) => {
      setError(null);
      setFieldErrors({});

      const validation = validateRegisterDTO(formData);
      if (!validation.isValid) {
        setFieldErrors(validation.errors);
        return false;
      }

      setIsLoading(true);
      try {
        const response = await authRepo.register(formData);
        tokenService.setToken(response.accessToken);
        setCurrentUser(response.user);
        setIsAuthenticated(true);
        setIsAuthModalOpen(false);
        await loadMyAccessRequests();
        return true;
      } catch (err) {
        setError(err.message || '회원가입에 실패했습니다.');
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [loadMyAccessRequests]
  );

  /**
   * 로그아웃 액션
   */
  const logout = useCallback(() => {
    tokenService.removeToken();
    setCurrentUser(null);
    setIsAuthenticated(false);
    setMyAccessRequests([]);
    setError(null);
  }, []);

  /**
   * 모달 제어 핸들러
   */
  const openLoginModal = useCallback(() => {
    setError(null);
    setFieldErrors({});
    setAuthMode('login');
    setIsAuthModalOpen(true);
  }, []);

  const openRegisterModal = useCallback(() => {
    setError(null);
    setFieldErrors({});
    setAuthMode('register');
    setIsAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
    setError(null);
    setFieldErrors({});
  }, []);

  const switchAuthMode = useCallback((mode) => {
    setAuthMode(mode);
    setError(null);
    setFieldErrors({});
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setFieldErrors({});
  }, []);

  // 도메인 계산 속성
  const roleBadge = useMemo(() => {
    return authService.getRoleBadge(currentUser?.level || 1);
  }, [currentUser]);

  const canAccessAdmin = useMemo(() => {
    return authService.canAccessAdmin(currentUser);
  }, [currentUser]);

  const canManageUsers = useMemo(() => {
    return authService.canManageUsers(currentUser);
  }, [currentUser]);

  return {
    currentUser,
    isAuthenticated,
    isLoading,
    error,
    fieldErrors,
    isAuthModalOpen,
    authMode,
    myAccessRequests,
    roleBadge,
    canAccessAdmin,
    canManageUsers,
    login,
    register,
    logout,
    openLoginModal,
    openRegisterModal,
    closeAuthModal,
    switchAuthMode,
    clearError,
    refreshSession: restoreSession
  };
}
