/**
 * [계층 2] ChatbotController Hook
 * [F-01] 플로팅 실시간 챗봇의 반응형 상태 및 SSE 스트리밍 토큰 타이핑 조율기
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { chatbotRepo } from '../repositories/chatbotRepo';

export function useChatbotController({
  currentConceptId = null,
  activeTab = 'wiki',
  onNavigateToTab,
  onSelectConcept
} = {}) {
  const [isOpen, setIsOpen] = useState(false);
  const [knowledgeScope, setKnowledgeScope] = useState('local');
  const [contextData, setContextData] = useState({
    conceptTitle: '온톨로지 챗',
    scaleBadge: '전역 탐색 모드',
    engineModeLabel: '위키 등록 지식 기반',
    quickQuestionChips: []
  });

  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: '안녕하세요! 현재 열람 중인 온톨로지 지식 및 공정 인과 메커니즘에 대해 무엇이든 질문하세요.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      pathType: 'factoid'
    }
  ]);

  const [inputText, setInputText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isThinking, setIsThinking] = useState(false);

  // 컨텍스트 변경 시 퀵 질문 칩 및 헤더 갱신
  const loadContext = useCallback(async (cid) => {
    try {
      const res = await chatbotRepo.getContext({ conceptId: cid });
      setContextData({
        conceptTitle: res.conceptTitle || '온톨로지 챗',
        scaleBadge: res.scaleBadge || '전역 탐색',
        engineModeLabel: res.engineModeLabel || '위키 등록 지식 기반',
        quickQuestionChips: res.quickQuestionChips || []
      });
    } catch (err) {
      console.warn('Failed to load chatbot context:', err);
    }
  }, []);

  useEffect(() => {
    loadContext(currentConceptId);
  }, [currentConceptId, loadContext]);

  /**
   * 메시지 전송 및 SSE 실시간 스트리밍
   */
  const handleSendMessage = useCallback(async (textToSend) => {
    const text = (textToSend || inputText).trim();
    if (!text || isStreaming) return;

    setInputText('');
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. 사용자 메시지 추가
    const userMsg = {
      sender: 'user',
      text,
      timestamp: timeStr
    };

    // 2. 어시스턴트 스트리밍 메시지 플레이스홀더 추가
    const assistantMsg = {
      sender: 'assistant',
      text: '',
      timestamp: timeStr,
      isStreaming: true,
      pathType: null,
      citations: [],
      followUpChips: [],
      knowledgeScope
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setIsThinking(true);

    try {
      await chatbotRepo.streamMessage(
        {
          message: text,
          conceptId: knowledgeScope === 'local' ? currentConceptId : null,
          knowledgeScope
        },
        {
          onRouting: (routingData) => {
            setIsThinking(false);
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.sender === 'assistant') {
                last.pathType = routingData.pathType || routingData.intent;
              }
              return next;
            });
          },
          onDelta: (deltaChunk) => {
            setIsThinking(false);
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.sender === 'assistant') {
                last.text += deltaChunk;
              }
              return next;
            });
          },
          onDone: (doneData) => {
            setIsStreaming(false);
            setIsThinking(false);
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.sender === 'assistant') {
                const payload = doneData.actionCard || doneData.actionPayload || null;
                last.text = doneData.answerMarkdown || last.text;
                last.pathType = doneData.pathType || last.pathType;
                last.knowledgeScope = doneData.knowledgeScope || knowledgeScope;
                last.citations = doneData.citations || (doneData.sourceEvidences || []).map((source) => source.id);
                last.followUpChips = doneData.followUpChips || doneData.suggestedChips || [];
                last.actionPayload = payload;
                last.actionCard = payload;
                last.isStreaming = false;
              }
              return next;
            });
          },
          onError: (err) => {
            setIsStreaming(false);
            setIsThinking(false);
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.sender === 'assistant') {
                last.text = `⚠️ 오류: ${err.message || '답변을 생성하지 못했습니다.'}`;
                last.isStreaming = false;
              }
              return next;
            });
          }
        }
      );
    } catch (err) {
      setIsStreaming(false);
      setIsThinking(false);
    }
  }, [inputText, isStreaming, currentConceptId, knowledgeScope]);

  /**
   * 대화 이력 초기화
   */
  const handleReset = useCallback(async () => {
    try {
      const res = await chatbotRepo.resetMessages({ conceptId: knowledgeScope === 'local' ? currentConceptId : null });
      setMessages([
        {
          sender: 'assistant',
          text: knowledgeScope === 'global' ? '반도체 관련 일반 지식을 질문해주세요. 웹 검색 결과와는 구분해서 설명합니다.' : (res.welcomeMessage || '대화가 초기화되었습니다. 질문해 주세요.'),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          pathType: 'factoid'
        }
      ]);
    } catch (err) {
      console.warn('Failed to reset chatbot messages:', err);
    }
  }, [currentConceptId, knowledgeScope]);

  /**
   * 액션 카드 클릭 ➔ 탭 이동 또는 개념 이동
   */
  const handleActionClick = useCallback((actionPayload) => {
    if (!actionPayload) return;
    const { actionType, targetTab, conceptId, query, targetUrl } = actionPayload;

    if (actionType === 'navigate_research' || (targetUrl && targetUrl.includes('research'))) {
      const topicMatch = targetUrl ? targetUrl.match(/topic=([^&]+)/) : null;
      const topic = topicMatch ? decodeURIComponent(topicMatch[1]) : query;
      if (onNavigateToTab) onNavigateToTab('research', { query: topic });
    } else if (actionType === 'navigate_comparison' || (targetUrl && targetUrl.includes('comparison'))) {
      const tAMatch = targetUrl ? targetUrl.match(/targetA=([^&]+)/) : null;
      const tBMatch = targetUrl ? targetUrl.match(/targetB=([^&]+)/) : null;
      const targetA = tAMatch ? decodeURIComponent(tAMatch[1]) : null;
      const targetB = tBMatch ? decodeURIComponent(tBMatch[1]) : null;
      if (onNavigateToTab) onNavigateToTab('comparison', { targetA, targetB });
    } else if (actionType === 'navigate_tab' && onNavigateToTab && targetTab) {
      onNavigateToTab(targetTab, { query });
    } else if (actionType === 'select_concept' && onSelectConcept && conceptId) {
      onSelectConcept(conceptId);
    }
  }, [onNavigateToTab, onSelectConcept]);

  return {
    isOpen,
    contextData: knowledgeScope === 'global' ? {
      conceptTitle: '반도체 Global 챗', scaleBadge: '반도체 일반 지식',
      engineModeLabel: '모델 지식 · 웹 검색 아님', quickQuestionChips: []
    } : contextData,
    knowledgeScope,
    onChangeKnowledgeScope: (scope) => {
      if (!isStreaming && ['local', 'global'].includes(scope)) {
        setKnowledgeScope(scope);
        setMessages((prev) => prev.length === 1 ? [{ ...prev[0], text: scope === 'global'
          ? '반도체 관련 일반 지식을 질문해주세요. 웹 검색 결과와는 구분해서 설명합니다.'
          : '등록된 위키 지식을 질문해주세요. 현재 문서를 가리킬 때는 이 공정 또는 이 문서라고 입력해주세요.' }] : prev);
      }
    },
    messages,
    inputText,
    isStreaming,
    isThinking,
    setIsOpen,
    setInputText,
    handleSendMessage,
    handleReset,
    handleActionClick,
    onChangeInput: setInputText,
    onSendMessage: handleSendMessage,
    onReset: handleReset,
    onActionClick: handleActionClick,
    sendWithText: (text) => {
      setIsOpen(true);
      handleSendMessage(text);
    },
    toggleOpen: () => setIsOpen((prev) => !prev),
    openChatbot: () => setIsOpen(true),
    closeChatbot: () => setIsOpen(false)
  };
}
