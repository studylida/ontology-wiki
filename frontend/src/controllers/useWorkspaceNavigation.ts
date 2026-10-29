import { useCallback, useEffect, useState } from 'react';
import { currentWorkspaceTab, onWikiNavigation, rememberWorkspaceTab } from '../repositories/wikiNavigation';
import type { WorkspaceTab } from '../types/workspace';

/** Keep tab state and reload/back-forward destinations together; do not remount wiki drafts. */
export function useWorkspaceNavigation() {
  const [tab, setTab] = useState<WorkspaceTab>(currentWorkspaceTab);
  const [wikiOpened, setWikiOpened] = useState(() => currentWorkspaceTab() === 'wiki');
  const show = useCallback((next: WorkspaceTab) => {
    setTab(next);
    if (next === 'wiki') setWikiOpened(true);
  }, []);
  useEffect(() => onWikiNavigation(() => show(currentWorkspaceTab())), [show]);
  const navigate = useCallback((next: WorkspaceTab) => {
    rememberWorkspaceTab(next);
    show(next);
  }, [show]);
  return {tab, wikiOpened, navigate};
}
