/**
 * [계층 2] TopBar Controller Hook
 * 상단 글로벌 내비게이션, 슬라이딩 탭 스위처 및 스포트라이트 검색 단축키 제어
 */

import { useState, useEffect, useCallback } from 'react';
import { conceptRepo } from '../repositories/conceptRepo';

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
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [totalIndexed, setTotalIndexed] = useState(0);

  useEffect(() => {
    let current = true;
    setSearchResults([]);
    setSearchError(null);
    setIsSearchLoading(isSearchOpen);
    if (!isSearchOpen) return;
    const timer = setTimeout(async () => {
      try {
        const response = await conceptRepo.search(searchTerm.trim());
        if (current) {
          setSearchResults(response.results);
          setTotalIndexed(response.totalIndexed);
        }
      } catch (error) {
        if (current) setSearchError('등록된 지식을 검색하지 못했습니다. 검색창을 다시 열어 시도해 주세요.');
      } finally {
        if (current) setIsSearchLoading(false);
      }
    }, searchTerm.trim() ? 200 : 0);
    return () => { current = false; clearTimeout(timer); };
  }, [isSearchOpen, searchTerm]);

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
    setSearchTerm('');
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
    searchTerm, setSearchTerm, searchResults, isSearchLoading, searchError, totalIndexed,
    openSearch,
    closeSearch,
    toggleSearch
  };
}
