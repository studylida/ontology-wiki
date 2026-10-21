/**
 * [계층 1] TailQuestionAdvisor View (Pure Dumb UI Component)
 * - 화면 2-B 하단: 실시간 꼬리질문 & 조건 튜닝 상담 인터페이스
 * - 물리 안전 마진(140N, 280°C 등) 실시간 가드레일 경고 및 Tab 3 티켓 내보내기 트리거
 */

import React, { useState } from 'react';
import { Sparkles, Send, ShieldAlert, ArrowRight, MessageSquare, AlertCircle } from 'lucide-react';
import { physicalSafetyGuardService } from '../../services/physicalSafetyGuardService';

const QUICK_TAIL_QUESTIONS = [
  '본딩 가압력 140N으로 낮출 때 워피지 영향은?',
  '큐어링 온도를 175°C에서 185°C로 상향 시 보이드 변화',
  '칩 갭 15μm 이하로 축소 시 언더필 충진 시간 변화'
];

export function TailQuestionAdvisor({
  chatHistory = [],
  isAdvising = false,
  onSendTailQuestion,
  onOpenExportModal
}) {
  const [inputQuestion, setInputQuestion] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverrideInput, setShowOverrideInput] = useState(false);

  // 실시간 물리 안전 마진 가드 체크
  const guard = physicalSafetyGuardService.validateSafetyMargins(inputQuestion, overrideReason);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isAdvising) return;

    if (!guard.isSafe && !overrideReason.trim()) {
      setShowOverrideInput(true);
      return;
    }

    const success = await onSendTailQuestion(inputQuestion.trim(), overrideReason.trim());
    if (success) {
      setInputQuestion('');
      setOverrideReason('');
      setShowOverrideInput(false);
    }
  };

  const handleQuickClick = (q) => {
    setInputQuestion(q);
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* 헤더 및 거버넌스 내보내기 버튼 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          paddingBottom: '14px',
          borderBottom: '1px solid var(--border-color)',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={20} style={{ color: 'var(--accent-primary)' }} />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              대화형 꼬리질문 & 조건 튜닝 상담 (Tail-Question Advisor)
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              공정 파라미터 변경 시의 인과 연쇄 반응과 물리 안전 마진(140N, 280°C 등)을 실시간 검증합니다.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenExportModal}
          style={{
            padding: '8px 14px',
            borderRadius: '6px',
            border: '1px solid var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.8125rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
          }}
          title="현재 비교 매트릭스와 튜닝 상담 결과를 검토 센터(Tab 3)의 공식 개정안 티켓으로 등록합니다."
        >
          <span>거버넌스 검토(Tab 3)로 티켓 내보내기</span>
          <ArrowRight size={14} />
        </button>
      </div>

      {/* 추천 질문 칩 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          추천 튜닝 질문:
        </span>
        {QUICK_TAIL_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleQuickClick(q)}
            style={{
              padding: '4px 10px',
              borderRadius: '20px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
              e.currentTarget.style.color = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-color)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* 상담 대화 목록 */}
      {chatHistory.length > 0 ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            maxHeight: '340px',
            overflowY: 'auto',
            padding: '12px',
            background: 'var(--bg-surface-2)',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            marginBottom: '16px'
          }}
        >
          {chatHistory.map((item, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* 사용자 질문 */}
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '10px 14px',
                    borderRadius: '12px 12px 0 12px',
                    background: 'var(--accent-primary)',
                    color: '#fff',
                    fontSize: '0.8125rem',
                    lineHeight: 1.5
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{item.question}</div>
                  <div style={{ fontSize: '0.6875rem', opacity: 0.8, marginTop: '4px', textAlign: 'right' }}>
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>

              {/* 시스템 답변 */}
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '12px 16px',
                    borderRadius: '12px 12px 12px 0',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                    fontSize: '0.8125rem',
                    lineHeight: 1.6
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
                    <span style={{ fontWeight: 700, fontSize: '0.75rem', color: 'var(--accent-primary)' }}>
                      인과 추론 및 튜닝 조언
                    </span>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{item.answer}</div>

                  {item.warnings && item.warnings.length > 0 && (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        background: 'var(--accent-warning-light)',
                        border: '1px solid var(--accent-warning)',
                        color: 'var(--accent-warning)',
                        fontSize: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <ShieldAlert size={14} />
                      <span>{item.warnings.join(' ')}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div
          style={{
            padding: '24px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.8125rem',
            background: 'var(--bg-surface-2)',
            borderRadius: '8px',
            border: '1px dashed var(--border-color)',
            marginBottom: '16px'
          }}
        >
          <MessageSquare size={24} style={{ opacity: 0.4, margin: '0 auto 8px auto', display: 'block' }} />
          비교 대상에 대해 추가적인 공정 조건(압력, 온도, 갭 등) 변경 시의 영향도를 질의해 보세요.
        </div>
      )}

      {/* 물리 안전 가드 실시간 경고 배너 */}
      {!guard.isSafe && (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'var(--accent-warning-light)',
            border: '1px solid var(--accent-warning)',
            color: 'var(--accent-warning)',
            fontSize: '0.8125rem',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px'
          }}
        >
          <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700 }}>물리 안전 마진 초과 감지:</div>
            <div>{guard.warningMessage}</div>
            {guard.requiresOverride && (
              <div style={{ marginTop: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                엔지니어링 승인 절차를 거치기 위해 아래 [물리 예외 사유]를 반드시 입력해야 상담이 진행됩니다.
              </div>
            )}
          </div>
        </div>
      )}

      {/* 질문 입력 폼 */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {/* 예외 사유 입력란 (안전 가드 경고 발생 시 노출) */}
        {(showOverrideInput || !guard.isSafe) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-warning)' }}>
              물리 예외 사유 (Override Reason) *
            </label>
            <input
              type="text"
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="예: 실리콘 관통전극(TSV) 접촉 저항 개선 및 Cu-Cu 직접 결합을 위한 한시적 가압력 허용"
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--accent-warning)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            />
          </div>
        )}

        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="공정 조건 튜닝 질문을 입력하세요 (예: 본딩 가압력 140N으로 낮출 때 워피지 영향은?)"
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem'
            }}
          />
          <button
            type="submit"
            disabled={isAdvising || !inputQuestion.trim()}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              border: 'none',
              background: isAdvising || !inputQuestion.trim() ? 'var(--text-muted)' : 'var(--accent-primary)',
              color: '#fff',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: isAdvising || !inputQuestion.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              whiteSpace: 'nowrap'
            }}
          >
            {isAdvising ? (
              <span>추론 중...</span>
            ) : (
              <>
                <Send size={14} />
                <span>조언 요청</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
