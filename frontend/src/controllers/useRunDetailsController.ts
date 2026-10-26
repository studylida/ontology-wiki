import { useEffect, useState } from "react";
import { conversationRepository } from "../repositories/api";
import { errorMessage, isAbort } from "../repositories/http";
import type { AnswerRun } from "../types/contracts";

/** Read a historical run on demand; opening metadata must never restart generation. */
export function useRunDetailsController(
  runId: string | undefined,
  open: boolean,
  hasCurrentSnapshot: boolean,
) {
  const [run, setRun] = useState<AnswerRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!open || !runId || hasCurrentSnapshot || run?.runId === runId) return;
    const controller = new AbortController();
    setError(null);
    conversationRepository
      .run(runId, controller.signal)
      .then(setRun)
      .catch((error) => {
        if (!isAbort(error)) setError(errorMessage(error));
      });
    return () => controller.abort();
  }, [hasCurrentSnapshot, open, run?.runId, runId]);
  return { run: run?.runId === runId ? run : null, error };
}
