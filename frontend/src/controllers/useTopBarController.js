/**
 * [계층 2] TopBar Controller Hook
 * 상단 글로벌 내비게이션, 슬라이딩 탭 스위처 및 스포트라이트 검색 단축키 제어
 */

import { useState, useEffect, useCallback } from 'react';

export const WORKSPACE_TABS = [
  { id: 'home', label: '대시보드', badge: null },
  { id: 'wiki', label: '지식 브라우저', badge: 'Tab 1' },
  { id: 'comparison', label: '인과 탐구실', badge: 'Tab 2' },
  { id: 'review', label: '검토 승인 센터', badge: 'Tab 3' },
  { id: 'research', label: '외부 문헌 조사실', badge: 'Tab 4' }
];

export function useTopBarController({ initialTab = 'wiki', onTabChange } = {}) {
  const [activeTab, setActiveTabState] = useState(initialTab);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const setActiveTab = useCallback(
    (tabId) => {
      setActiveTabState(tabId);
      if (onTabChange) {
        onTabChange(tabId);
      }
    },
    [onTabChange]
  );

  const openSearch = useCallback(() => {
    setIsSearchOpen(true);
  }, []);

  const closeSearch = useCallback(() => {
    setIsSearchOpen(false);
  }, []);

  const toggleSearch = useCallback(() => {
    setIsSearchOpen((prev) => !prev);
  }, []);

  // ⌘K / Ctrl+K 단축키 바인딩
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        toggleSearch();
      } else if (e.key === 'Escape' && isSearchOpen) {
        closeSearch();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [toggleSearch, closeSearch, isSearchOpen]);

  return {
    tabs: WORKSPACE_TABS,
    activeTab,
    setActiveTab,
    isSearchOpen,
    openSearch,
    closeSearch,
    toggleSearch
  };
}
