/**
 * [계층 1] SectionEvidences View (Pure Dumb UI Component)
 * - 5번 섹션: 공식 검증 출처 원문 (Evidence References)
 * - 본 개념에 귀속된 공인 출처([E-01], [E-02] 등)의 발행처, 원문 인용구, 위치 및 DOI 링크 카드 렌더러
 */

import React, { useState, useEffect } from 'react';
import { BookCheck, ExternalLink, Quote, ShieldCheck } from 'lucide-react';
import { httpClient } from '../../repositories/httpClient';

export function SectionEvidences({ conceptDetail }) {
  const [evidences, setEvidences] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setEvidences([]);
    if (!conceptDetail) {
      setIsLoading(false);
      return;
    }

    // 본문 전반(한계점, 실무 사례 등)에서 참조된 모든 공인 출처 ID 수집
    const ids = new Set(conceptDetail.evidenceIds || []);

    (conceptDetail.principles || []).forEach((p) => {
      (p.evidenceIds || []).forEach((eid) => ids.add(eid));
    });

    (conceptDetail.limitations || []).forEach((l) => {
      (l.evidenceIds || []).forEach((eid) => ids.add(eid));
    });

    (conceptDetail.perspectives || []).forEach((p) => {
      if (p.evidenceId) ids.add(p.evidenceId);
      (p.specifications || []).forEach((spec) => (spec.evidenceIds || []).forEach((id) => ids.add(id)));
    });

    Object.values(conceptDetail.enrichedRelations || {}).forEach((items) => {
      (items || []).forEach((item) => (item.evidenceIds || []).forEach((eid) => ids.add(eid)));
    });

    const fetchEvidences = async () => {
      setIsLoading(true);
      try {
        const idList = Array.from(ids);
        const results = await Promise.allSettled(
          idList.map((id) => httpClient.get(`/evidences/${id}`))
        );
        const successful = results
          .filter((r) => r.status === 'fulfilled')
          .map((r) => r.value);
        if (active) setEvidences(successful);
      } catch (err) {
        if (active) console.warn('Failed to load evidence details:', err);
      } finally {
        if (active) setIsLoading(false);
      }
    };

    fetchEvidences();
    return () => { active = false; };
  }, [conceptDetail]);

  if (!conceptDetail) return null;

  return (
    <article
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '6px',
              background: 'var(--accent-primary-light)',
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8125rem'
            }}
          >
            6
          </div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            공식 검증 출처 원문 (Evidence References)
          </h2>
        </div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '12px',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)'
          }}
        >
          공인 출처 {evidences.length}건 귀속
        </span>
      </div>

      {isLoading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
          공인 출처 원문 데이터를 불러오는 중...
        </div>
      ) : evidences.length === 0 ? (
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: 0, padding: '12px', background: 'var(--bg-surface-2)', borderRadius: '6px' }}>
          현재 본 문서에 귀속된 공인 출처가 없습니다.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {evidences.map((ev) => (
            <div
              key={ev.id}
              style={{
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '16px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}
            >
              {/* 상단 메타 바 */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      color: 'var(--accent-primary)',
                      background: 'var(--bg-surface)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)'
                    }}
                  >
                    [{ev.id}]
                  </span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {ev.sourceName}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  발행: <strong>{ev.publisher || '발행처 정보 없음'}</strong> {ev.publishedDate && `(${ev.publishedDate})`}
                </div>
              </div>

              {/* 직접 인용구 박스 */}
              {ev.quote && (
                <div
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    padding: '12px 14px',
                    fontSize: '0.8125rem',
                    lineHeight: 1.6,
                    color: 'var(--text-primary)',
                    display: 'flex',
                    gap: '8px'
                  }}
                >
                  <Quote size={16} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontStyle: 'italic' }}>"{ev.quote}"</div>
                    {ev.sectionContext && (
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        📍 {ev.sectionContext}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 원문 링크 */}
              {ev.externalUrl && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <a
                    href={ev.externalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: 'var(--accent-primary)',
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span>공인 원문 보기 (DOI / 외부 표준)</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
