import { useEffect, useRef, useState } from 'react';
import type { User } from '../types/contracts';
import { api } from '../repositories/api';
import { errorMessage } from '../repositories/http';
import { authStorage, AUTH_CHANGED, clearWorkspace } from '../repositories/workspaceStorage';

export function useAuthController() {
  const [user, setUser] = useState<User | null>(null), [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const locked = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try { if (authStorage.getToken()) { const value = await api.me(controller.signal); if (!controller.signal.aborted) setUser(value); } }
      catch (e) { if (!controller.signal.aborted) setError(errorMessage(e)); }
      finally { if (!controller.signal.aborted) setChecking(false); }
    })();
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const expired = () => {
      try { authStorage.clear(); if (user) clearWorkspace(user.id); } catch { /* No private view survives logout. */ }
      setUser(null); setError('로그인이 만료되었거나 권한이 변경되었습니다. 다시 로그인해 주세요.');
    };
    window.addEventListener(AUTH_CHANGED, expired);
    return () => window.removeEventListener(AUTH_CHANGED, expired);
  }, [user]);
  async function login(username: string, password: string) {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError('');
    try { const response = await api.login(username, password); authStorage.setToken(response.accessToken); setUser(response.user); }
    catch (e) { setError(errorMessage(e)); }
    finally { locked.current = false; setBusy(false); }
  }
  function logout() {
    try { if (user) clearWorkspace(user.id); authStorage.clear(); }
    finally { setUser(null); setError(''); }
  }
  return {user, checking, busy, error, login, logout};
}
