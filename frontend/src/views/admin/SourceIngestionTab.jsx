/**
 * [계층 1] SourceIngestionTab (Pure UI View Component)
 * - 관리자 전용 sources/ 원천 기술 백서 목록 및 지식 추출 스튜디오
 * - 체크박스(전체선택 포함), 기추출 포함 선택, 날짜(-) 표기, 실행 전 재추출 여부 확인
 */

import React, { useState, useMemo } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
  Play,
  Search,
  Filter,
  Eye,
  Layers,
  Database,
  ArrowRight,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export function SourceIngestionTab({
  documents = [],
  summary = { totalCount: 0, succeededCount: 0, pendingCount: 0, modifiedCount: 0 },
  selectedDocIds = new Set(),
  isLoading = false,
  isExtracting = false,
  hasExtractionResult = false,
  extractionRecovery = null,
  onResumeExtraction,
  onOpenProgress,
  onToggleSelect,
  onSelectAll,
  onClearSelection,
  onRunExtraction,
  onRunReextraction,
  onOpenPreview
}) {
  const [publisherFilter, setPublisherFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // 1. 고유 출처사 목록 도출
  const publishers = useMemo(() => {
    const set = new Set(documents.map((d) => d.publisher).filter(Boolean));
    return ['all', ...Array.from(set)];
  }, [documents]);

  // 2. 필터링된 문서 목록
  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      if (publisherFilter !== 'all' && doc.publisher !== publisherFilter) return false;
      if (statusFilter === 'pending' && doc.lastSucceededAt) return false;
      if (statusFilter === 'success' && !doc.lastSucceededAt) return false;
      if (statusFilter === 'modified' && !doc.isModified) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const tMatch = (doc.title || '').toLowerCase().includes(q);
        const fMatch = (doc.filePath || '').toLowerCase().includes(q);
        if (!tMatch && !fMatch) return false;
      }
      return true;
    });
  }, [documents, publisherFilter, statusFilter, searchQuery]);

  // 3. 선택 통계 및 스마트 실행 대상 판별
  const selectionStats = useMemo(() => {
    const selectedList = filteredDocs.filter((d) => selectedDocIds.has(d.docId) && d.attemptStatus !== 'running');
    const pendingList = selectedList.filter((d) => !d.lastSucceededAt && d.attemptStatus !== 'running');
    const succeededList = selectedList.filter((d) => d.lastSucceededAt);
    const modifiedList = selectedList.filter((d) => d.isModified);

    return {
      totalSelected: selectedList.length,
      pendingCount: pendingList.length,
      succeededCount: succeededList.length,
      modifiedCount: modifiedList.length,
      runnableIds: pendingList.map((d) => d.docId),
      allSelectedIds: selectedList.map((d) => d.docId)
    };
  }, [filteredDocs, selectedDocIds]);

  const allFilteredSelected = useMemo(() => {
    const runnable = filteredDocs.filter((d) => d.attemptStatus !== 'running');
    return runnable.length > 0 && runnable.every((d) => selectedDocIds.has(d.docId));
  }, [filteredDocs, selectedDocIds]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── 요약 메트릭 카드 ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}
      >
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(59, 130, 246, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-primary)'
            }}
          >
            <FileText size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>총 원천 기술 백서</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary.totalCount}건
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10b981'
            }}
          >
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>추출 성공 문서</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981' }}>
              {summary.succeededCount}건
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#f59e0b'
            }}
          >
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>미추출 대기 문서</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f59e0b' }}>
              {summary.pendingCount}건
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(139, 92, 246, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#8b5cf6'
            }}
          >
            <RefreshCw size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>원문 변경 감지</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#8b5cf6' }}>
              {summary.modifiedCount}건
            </div>
          </div>
        </div>
      </div>

      {extractionRecovery && (
        <div role="status" style={{ padding: '16px', border: '1px solid #f59e0b', borderRadius: '10px', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}>
          <strong>이전 추출이 중단되었습니다.</strong>
          {extractionRecovery.docIds.length > 0 ? <>
            <p>전체 목록 {extractionRecovery.docIds.length}건 중 앞서 완료된 {extractionRecovery.preservedCount}건은 유지하고, 중단된 문서부터 나머지 {extractionRecovery.docIds.length - extractionRecovery.preservedCount}건을 다시 추출합니다. 위키 적용은 별도입니다.</p>
            <button type="button" disabled={isExtracting} onClick={onResumeExtraction} style={{ padding: '8px 14px', background: 'var(--accent-primary)', border: 'none', borderRadius: '6px', color: '#fff', cursor: 'pointer' }}>완료 결과 유지하고 이어하기</button>
          </> : <p>문서별 완료 이력이 섞여 있어 자동으로 이어갈 범위를 정할 수 없습니다. 문서를 확인하고 선택해주세요.</p>}
        </div>
      )}

      {/* ── 툴바 & 스마트 액션 바 ── */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* 필터 그룹 */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={15} style={{ color: 'var(--text-muted)' }} />
              <select
                value={publisherFilter}
                onChange={(e) => setPublisherFilter(e.target.value)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-page)',
                  color: 'var(--text-primary)',
                  fontSize: '0.8125rem'
                }}
              >
                {publishers.map((p) => (
                  <option key={p} value={p}>
                    {p === 'all' ? '출처사: 전체' : p}
                  </option>
                ))}
              </select>
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-page)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            >
              <option value="all">추출 상태: 전체</option>
              <option value="pending">미추출 대기만 보기</option>
              <option value="success">추출 완료만 보기</option>
              <option value="modified">원문 변경 감지만 보기</option>
            </select>

            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '9px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="파일명 또는 제목 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '6px 10px 6px 30px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-page)',
                  color: 'var(--text-primary)',
                  fontSize: '0.8125rem',
                  width: '200px'
                }}
              />
            </div>
          </div>

          {/* 액션 버튼 그룹 */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {(isExtracting || hasExtractionResult) && (
              <button type="button" onClick={onOpenProgress} style={{ padding: '8px 14px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-page)', color: 'var(--text-primary)', cursor: 'pointer' }}>
                {isExtracting ? '추출 진행 상황 보기' : '최근 추출 결과 보기'}
              </button>
            )}
            {/* 기추출 문서가 포함되면 Controller가 실행 범위를 확인한다. */}
            <button
              type="button"
              disabled={isExtracting || selectionStats.totalSelected === 0}
              onClick={() => onRunExtraction(selectionStats.allSelectedIds)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: selectionStats.totalSelected > 0 ? 'var(--accent-primary)' : 'var(--border-color)',
                color: '#fff',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: selectionStats.totalSelected > 0 ? 'pointer' : 'not-allowed',
                opacity: isExtracting ? 0.7 : 1
              }}
            >
              <Play size={15} />
              <span>선택 추출 실행 ({selectionStats.totalSelected}건)</span>
            </button>

          </div>
        </div>

        {/* ── 선택 상태 안내 바 ── */}
        <div
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '8px',
            borderTop: '1px solid var(--border-color)'
          }}
        >
          <div>
            현재 목록: <strong style={{ color: 'var(--text-primary)' }}>{filteredDocs.length}건</strong>
            {selectionStats.totalSelected > 0 && (
              <span>
                {' '}➔ 선택: <strong>{selectionStats.totalSelected}건</strong> (미추출: {selectionStats.pendingCount}건 / 기추출: {selectionStats.succeededCount}건)
              </span>
            )}
          </div>

          {selectionStats.totalSelected > 0 && (
            <button
              type="button"
              onClick={onClearSelection}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--accent-primary)',
                fontSize: '0.75rem',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              선택 해제
            </button>
          )}
        </div>
      </div>

      {/* ── 문서 목록 테이블 ── */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          overflow: 'hidden'
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-page)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 14px', width: '40px', textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={allFilteredSelected}
                    aria-label="현재 목록 전체 선택"
                    disabled={isExtracting || !filteredDocs.some((doc) => doc.attemptStatus !== 'running')}
                    onChange={(e) => onSelectAll(filteredDocs.filter((d) => d.attemptStatus !== 'running').map((d) => d.docId), e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                </th>
                <th style={{ padding: '12px 14px', width: '130px' }}>출처사</th>
                <th style={{ padding: '12px 14px' }}>백서 제목 및 파일 경로</th>
                <th style={{ padding: '12px 14px', width: '110px' }}>추출 상태</th>
                <th style={{ padding: '12px 14px', width: '150px' }}>마지막 성공 일시</th>
                <th style={{ padding: '12px 14px', width: '110px' }}>추출 지식</th>
                <th style={{ padding: '12px 14px', width: '130px', textAlign: 'center' }}>작업</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    조건에 부합하는 기술 백서가 없습니다.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => {
                  const isChecked = selectedDocIds.has(doc.docId);
                  const isSuccess = doc.attemptStatus === 'success' && !!doc.lastSucceededAt;

                  return (
                    <tr
                      key={doc.docId}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        background: isChecked ? 'rgba(59, 130, 246, 0.04)' : 'transparent',
                        transition: 'background 0.15s ease'
                      }}
                    >
                      {/* 체크박스 */}
                      <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          aria-label={`${doc.title} 선택`}
                          disabled={isExtracting || doc.attemptStatus === 'running'}
                          onChange={() => onToggleSelect(doc.docId)}
                          style={{ cursor: 'pointer' }}
                        />
                      </td>

                      {/* 출처사 배지 */}
                      <td style={{ padding: '12px 14px' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.6875rem',
                            fontWeight: 600,
                            background:
                              doc.publisher.includes('Samsung') ? 'rgba(24, 119, 242, 0.1)' :
                              doc.publisher.includes('SK') ? 'rgba(239, 68, 68, 0.1)' :
                              doc.publisher.includes('ASML') ? 'rgba(16, 185, 129, 0.1)' :
                              doc.publisher.includes('Lam') ? 'rgba(139, 92, 246, 0.1)' :
                              'rgba(107, 114, 128, 0.1)',
                            color:
                              doc.publisher.includes('Samsung') ? '#1877f2' :
                              doc.publisher.includes('SK') ? '#ef4444' :
                              doc.publisher.includes('ASML') ? '#10b981' :
                              doc.publisher.includes('Lam') ? '#8b5cf6' :
                              'var(--text-secondary)'
                          }}
                        >
                          {doc.publisher}
                        </span>
                      </td>

                      {/* 제목 및 파일 경로 */}
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                          {doc.title}
                        </div>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                          sources/{doc.filePath}
                        </div>
                        {doc.lastErrorMessage && doc.attemptStatus === 'failed' && (
                          <div style={{ fontSize: '0.6875rem', color: '#ef4444', marginTop: '4px' }}>
                            ⚠ 실패 사유: {doc.lastErrorMessage}
                          </div>
                        )}
                      </td>

                      {/* 추출 상태 */}
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', alignItems: 'flex-start' }}>
                          {isSuccess ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#10b981', fontWeight: 600, fontSize: '0.75rem' }}>
                              <CheckCircle2 size={13} /> 추출 완료
                            </span>
                          ) : doc.attemptStatus === 'failed' ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#ef4444', fontWeight: 600, fontSize: '0.75rem' }}>
                              <AlertCircle size={13} /> 추출 실패
                            </span>
                          ) : doc.attemptStatus === 'interrupted' ? (
                            <span style={{ color: '#f59e0b', fontWeight: 600 }}>추출 중단</span>
                          ) : doc.attemptStatus === 'running' ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.75rem' }}>
                              <RefreshCw size={13} className="spin" /> 실행 중
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                              미추출 대기
                            </span>
                          )}

                          {doc.isModified && (
                            <span
                              style={{
                                padding: '1px 5px',
                                borderRadius: '3px',
                                fontSize: '0.625rem',
                                fontWeight: 700,
                                background: 'rgba(139, 92, 246, 0.1)',
                                color: '#8b5cf6'
                              }}
                            >
                              원문 변경
                            </span>
                          )}
                        </div>
                      </td>

                      {/* 마지막 성공 일시 (미추출 시 '-' 표기) */}
                      <td style={{ padding: '12px 14px', color: doc.lastSucceededAt ? 'var(--text-secondary)' : 'var(--text-muted)' }}>
                        {doc.lastSucceededAt ? (
                          <span style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                            {doc.lastSucceededAt}
                          </span>
                        ) : (
                          <span style={{ fontWeight: 700 }}>-</span>
                        )}
                      </td>

                      {/* 추출 지식 요약 */}
                      <td style={{ padding: '12px 14px' }}>
                        {doc.extractedConceptsCount > 0 ? (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                            개념 {doc.extractedConceptsCount}개
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>-</span>
                        )}
                      </td>

                      {/* 개별 작업 버튼 */}
                      <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', gap: '6px' }}>
                          {doc.lastSucceededAt && !doc.isApplied && (
                            <button
                              type="button"
                              onClick={() => onOpenPreview(doc.docId)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '3px',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                border: '1px solid var(--border-color)',
                                background: 'var(--bg-page)',
                                color: 'var(--text-primary)',
                                fontSize: '0.6875rem',
                                cursor: 'pointer'
                              }}
                              title="추출된 지식 미리보기"
                            >
                              <Eye size={12} /> 미리보기
                            </button>
                          )}

                          <button
                            type="button"
                            disabled={isExtracting || doc.attemptStatus === 'running'}
                            onClick={() => doc.lastSucceededAt ? onRunReextraction([doc.docId]) : onRunExtraction([doc.docId])}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '3px',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: 'none',
                              background: 'var(--accent-primary)',
                              color: '#fff',
                              fontSize: '0.6875rem',
                              cursor: 'pointer'
                            }}
                          >
                            <Play size={10} /> {doc.lastSucceededAt ? '재추출' : '추출'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
