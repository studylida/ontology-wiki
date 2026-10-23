/**
 * [계층 1] ExtractionProgressModal (Pure Dumb UI Component)
 * - 단일 순차 실행 및 SSE 실시간 스트림 진행 상태를 정직하게 보여주는 모달
 * - 가짜 연출 배제: 단계별 진행률, 완료/전체 건수, 문서별 성공/실패 사유 표시
 */

import React from 'react';
import { RefreshCw, CheckCircle2, AlertCircle, X, ArrowRight } from 'lucide-react';

export function ExtractionProgressModal({
  isOpen = false,
  progress = { current: 0, total: 0, currentTitle: '', currentPublisher: '', step: '대기 중' },
  logs = [],
  isFinished = false,
  error = null,
  onClose,
  onOpenPreview
}) {
  if (!isOpen) return null;

  const pct = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;

  return (
    <div
      className="modal-backdrop"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
    >
      <div
        className="modal-box"
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '600px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
          overflow: 'hidden'
        }}
      >
        {/* ── 헤더 ── */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: isFinished ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isFinished ? '#10b981' : 'var(--accent-primary)'
              }}
            >
              {error ? <AlertCircle size={18} /> : isFinished ? <CheckCircle2 size={18} /> : <RefreshCw size={18} className="spin" />}
            </div>
            <div>
              <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {error ? '추출 상태 확인 필요' : isFinished ? '원천 백서 지식 추출 종료' : '원천 백서 순차 지식 추출 진행 중'}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                {error ? error : isFinished
                  ? progress.step
                  : `진행률: ${progress.current} / ${progress.total}건 (${pct}%)`}
              </div>
            </div>
          </div>

            <button
              type="button"
              onClick={onClose}
              aria-label="진행 창 닫기 (추출은 계속 진행됩니다)"
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
            >
              <X size={18} />
            </button>
        </div>

        {/* ── 본문: 진행률 바 & 현재 작업 문서 ── */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          {/* 프로그레스 바 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {error ? '연결 오류 또는 추출 중단' : isFinished ? '전체 작업 종료' : progress.step}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>
                {progress.current} / {progress.total} 건
              </span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'var(--bg-page)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: isFinished ? '#10b981' : 'var(--accent-primary)',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
          </div>

          {/* 현재 처리 중인 문서 안내 카드 */}
          {!isFinished && !error && progress.currentTitle && (
            <div
              style={{
                padding: '12px 14px',
                borderRadius: '8px',
                background: 'var(--bg-page)',
                border: '1px solid var(--border-color)',
                fontSize: '0.8125rem'
              }}
            >
              <div style={{ fontSize: '0.6875rem', color: 'var(--accent-primary)', fontWeight: 600, marginBottom: '2px' }}>
                [{progress.currentPublisher}] 현재 분석 문서
              </div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {progress.currentTitle}
              </div>
            </div>
          )}

          {/* 문서별 처리 결과 목록 */}
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              문서별 처리 이력
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
              {logs.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: item.type === 'error' ? 'rgba(239, 68, 68, 0.06)' : 'var(--bg-page)',
                    border: `1px solid ${item.type === 'error' ? 'rgba(239, 68, 68, 0.2)' : 'var(--border-color)'}`,
                    fontSize: '0.75rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {item.type === 'success' ? (
                      <CheckCircle2 size={14} style={{ color: '#10b981', flexShrink: 0 }} />
                    ) : item.type === 'error' ? (
                      <AlertCircle size={14} style={{ color: '#ef4444', flexShrink: 0 }} />
                    ) : item.type === 'skipped' ? (
                      <CheckCircle2 size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    ) : (
                      <RefreshCw size={14} className="spin" style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
                    )}
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {item.title || item.docId}
                    </span>
                  </div>

                  <span style={{ color: item.type === 'error' ? '#ef4444' : 'var(--text-muted)', fontSize: '0.6875rem' }}>
                    {item.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── 하단 액션 바 ── */}
        <div
          style={{
            padding: '14px 20px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px'
          }}
        >
          <button type="button" onClick={onClose} style={{ color: 'var(--text-primary)', background: 'var(--bg-page)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}>
            {isFinished || error ? '닫기' : '닫고 다른 작업하기'}
          </button>
          {isFinished ? (
            <>
              <button
                type="button"
                onClick={onOpenPreview}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 18px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent-primary)',
                  color: '#fff',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <span>추출 결과 미리보기 및 위키 적용</span>
                <ArrowRight size={15} />
              </button>
            </>
          ) : !error && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              순차적으로 LLM 구조화 추출을 진행 중입니다...
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
