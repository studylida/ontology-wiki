import { useCallback, useEffect, useState } from "react";
import { identityRepository, wikiRepository } from "../repositories/api";
import { errorMessage } from "../repositories/http";
import type { WikiSettings } from "../types/contracts";
export function useSettingsController(open: boolean) {
  const [wiki, setWiki] = useState<WikiSettings | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!open) return;
    let current = true;
    setError(null);
    Promise.allSettled([
      wikiRepository.settings(),
      identityRepository.health(),
    ]).then((results) => {
      if (!current) return;
      if (results[0].status === "fulfilled") setWiki(results[0].value);
      else setError(errorMessage(results[0].reason));
      if (results[1].status === "fulfilled") setHealth(results[1].value);
      else setError(errorMessage(results[1].reason));
    });
    return () => {
      current = false;
    };
  }, [open]);
  const setAutoOrganize = useCallback(async (enabled: boolean) => {
    setBusy(true);
    setError(null);
    try {
      setWiki(await wikiRepository.updateSettings(enabled));
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, []);
  return { wiki, health, busy, error, setAutoOrganize };
}
export function useEnvironmentController() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    identityRepository
      .health(controller.signal)
      .then(setHealth)
      .catch(() => {
        /* An unavailable health response never means configured or successful. */
      });
    return () => controller.abort();
  }, []);
  return health;
}
