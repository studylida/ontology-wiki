import { useCallback, useEffect, useState } from "react";
import { identityRepository } from "../repositories/api";
import { authStorage, errorMessage, isAbort } from "../repositories/http";
import type { User } from "../types/contracts";

export function useAuthController() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!authStorage.getToken());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!authStorage.getToken()) return;
    const controller = new AbortController();
    identityRepository
      .me(controller.signal)
      .then(setUser)
      .catch((error) => {
        if (!isAbort(error)) {
          setError(errorMessage(error));
          if (error.status === 401) authStorage.clear();
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);
  const login = useCallback(async (username: string, password: string) => {
    if (!username.trim() || !password) {
      setError("사용자 이름과 비밀번호를 입력해 주세요.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await identityRepository.login(username.trim(), password);
      authStorage.setToken(result.accessToken);
      setUser(result.user);
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, []);
  const logout = useCallback(() => {
    authStorage.clear();
    setUser(null);
    setError(null);
  }, []);
  return { user, loading, busy, error, login, logout };
}
