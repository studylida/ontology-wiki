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
  const [contextData, setContextData] = useState({
    conceptTitle: '반도체 인과 온톨로지 전역 어시스턴트',
    scaleBadge: '전역 탐색 모드',
    engineModeLabel: '🟢 Live (온톨로지 인과 추론 엔진)',
    quickQuestionChips: [
      '💡 HBM 방열 대안: MR-MUF vs TC-NCF 비교',
      '💡 Cryo 극저온 식각 반응 메커니즘',
      '💡 차세대 유리기판 TGV 공정 및 물성 표준'
    ]
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
        conceptTitle: res.conceptTitle || '반도체 인과 온톨로지 어시스턴트',
        scaleBadge: res.scaleBadge || '전역 탐색',
        engineModeLabel: res.engineModeLabel || '🟢 Live',
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
      followUpChips: []
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setIsThinking(true);

    try {
      await chatbotRepo.streamMessage(
        {
          message: text,
          conceptId: currentConceptId
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
                last.text = doneData.answerMarkdown || last.text;
                last.pathType = doneData.pathType || last.pathType;
                last.citations = doneData.citations || [];
                last.followUpChips = doneData.followUpChips || [];
                last.actionPayload = doneData.actionPayload || null;
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
  }, [inputText, isStreaming, currentConceptId]);

  /**
   * 대화 이력 초기화
   */
  const handleReset = useCallback(async () => {
    try {
      const res = await chatbotRepo.resetMessages({ conceptId: currentConceptId });
      setMessages([
        {
          sender: 'assistant',
          text: res.welcomeMessage || '대화가 초기화되었습니다. 질문해 주세요.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          pathType: 'factoid'
        }
      ]);
    } catch (err) {
      console.warn('Failed to reset chatbot messages:', err);
    }
  }, [currentConceptId]);

  /**
   * 액션 카드 클릭 ➔ 탭 이동 또는 개념 이동
   */
  const handleActionClick = useCallback((actionPayload) => {
    if (!actionPayload) return;
    const { actionType, targetTab, conceptId, query } = actionPayload;

    if (actionType === 'navigate_tab' && onNavigateToTab && targetTab) {
      onNavigateToTab(targetTab, { query });
    } else if (actionType === 'select_concept' && onSelectConcept && conceptId) {
      onSelectConcept(conceptId);
    }
  }, [onNavigateToTab, onSelectConcept]);

  return {
    isOpen,
    contextData,
    messages,
    inputText,
    isStreaming,
    isThinking,
    setIsOpen,
    setInputText,
    handleSendMessage,
    handleReset,
    handleActionClick,
    toggleOpen: () => setIsOpen((prev) => !prev),
    openChatbot: () => setIsOpen(true),
    closeChatbot: () => setIsOpen(false)
  };
}
