/**
 * [계층 1] NewConceptModal View (Pure Dumb UI Component)
 * - 완전 신규 온톨로지 개념 발의 전역 모달
 * - 🌟 [🤖 AI 에이전트 위치 추천 받기] 원클릭 자동완성 탑재
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect, useState } from 'react';
import { PlusCircle, Sparkles, X, Send, Bot, RefreshCw } from 'lucide-react';

export function NewConceptModal({
  isOpen,
  currentUser,
  isRecommending,
  placementRecommendation,
  initialData,
  onClose,
  onRequestRecommendation,
  onSubmit
}) {
  const dialogRef = useRef(null);

  const [form, setForm] = useState({
    title: '',
    engName: '',
    summary: '',
    purpose: '',
    domainFacet: 'unit_process',
    scaleLevel: 5,
    processCategory: '첨단 패키징',
    parentConceptId: 'concept-tcb',
    reason: ''
  });

  // 미등록 개념에서 [+ 발의하기] 클릭 시 초기값 자동 주입
  useEffect(() => {
    if (isOpen && initialData) {
      setForm((prev) => ({
        ...prev,
        title: initialData.title || prev.title,
        parentConceptId: initialData.parentConceptId || prev.parentConceptId,
        reason: initialData.reason || `[${initialData.parentTitle || initialData.parentConceptId || '단위 공정'}]의 연계 개념으로 참조되었으나 아직 지식 위키에 상세 문서가 부재하여 신규 작성을 발의합니다.`
      }));
    }
  }, [isOpen, initialData]);

  // 추천 결과가 들어오면 폼 자동 채우기(Auto-fill)
  useEffect(() => {
    if (placementRecommendation) {
      setForm((prev) => ({
        ...prev,
        domainFacet: placementRecommendation.suggestedFacet || prev.domainFacet,
        scaleLevel: placementRecommendation.suggestedScaleLevel || prev.scaleLevel,
        processCategory: placementRecommendation.suggestedProcessCategory || prev.processCategory,
        parentConceptId: placementRecommendation.suggestedParentConceptId || prev.parentConceptId
      }));
    }
  }, [placementRecommendation]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) dialog.showModal();
    } else {
      if (dialog.open) dialog.close();
      setForm({
        title: '',
        engName: '',
        summary: '',
        purpose: '',
        domainFacet: 'unit_process',
        scaleLevel: 5,
        processCategory: '첨단 패키징',
        parentConceptId: 'concept-tcb',
        reason: ''
      });
    }

    const handleBackdrop = (e) => {
      if (e.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const inBox =
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width;
      if (!inBox) onClose();
    };

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      dialog.addEventListener('click', handleBackdrop);
      return () => dialog.removeEventListener('click', handleBackdrop);
    }
  }, [isOpen, onClose]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRecommendClick = () => {
    if (!form.title.trim()) {
      alert('기술/개념명을 먼저 입력해 주세요.');
      return;
    }
    onRequestRecommendation(form.title.trim(), form.summary.trim() || form.title.trim());
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.summary.trim()) return;

    onSubmit({
      title: form.title.trim(),
      engName: form.engName.trim(),
      author: currentUser?.name || '현장 엔지니어',
      department: currentUser?.department || '공정기술팀',
      reviewType: 'new_concept',
      originType: 'human_engineer',
      domainFacet: form.domainFacet,
      scaleLevel: Number(form.scaleLevel),
      scaleName: Number(form.scaleLevel) === 5 ? '첨단 패키징' : '단위 공정',
      processCategory: form.processCategory,
      parentConceptId: form.parentConceptId,
      userNote: `[신규 개념 발의] ${form.summary}\n\n도입 목적: ${form.purpose}`,
      evidencePayload: {
        summary: form.summary,
        purpose: form.purpose
      }
    });
  };

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '640px' }} onClose={onClose}>
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PlusCircle size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              신규 온톨로지 개념·문서 추가 발의
            </h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* 개념명 & 영문명 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                신규 기술/개념명 (국문) *
              </label>
              <input
                type="text"
                name="title"
                value={form.title}
                onChange={handleChange}
                placeholder="예: 플라즈마 활성화 Cu-Cu 직접 접합"
                required
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', color: 'var(--text-primary)', fontSize: '0.8125rem' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                표준 영문 명칭
              </label>
              <input
                type="text"
                name="engName"
                value={form.engName}
                onChange={handleChange}
                placeholder="예: Plasma Direct Bonding"
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', color: 'var(--text-primary)', fontSize: '0.8125rem' }}
              />
            </div>
          </div>

          {/* 핵심 기술 정의 & 도입 목적 */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              핵심 기술 정의 및 개요 *
            </label>
            <textarea
              rows={2}
              name="summary"
              value={form.summary}
              onChange={handleChange}
              placeholder="예: 웨이퍼 표면을 플라즈마로 친수화하여 200°C 저온에서 구리-구리 계면을 직접 접합하는 초고밀도 적층 기술."
              required
              style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', color: 'var(--text-primary)', fontSize: '0.8125rem', resize: 'none' }}
            />
          </div>

          {/* 🌟 AI 에이전트 온톨로지 편입 위치 추천 원클릭 버튼 */}
          <div
            style={{
              background: 'var(--accent-primary-light)',
              border: '1px solid rgba(37, 99, 235, 0.25)',
              borderRadius: '8px',
              padding: '12px 14px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Bot size={16} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                  온톨로지 트리 편입 위치 자동 추천
                </span>
              </div>
              <button
                type="button"
                onClick={handleRecommendClick}
                disabled={isRecommending}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent-primary)',
                  color: '#ffffff',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: isRecommending ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                {isRecommending ? <RefreshCw size={12} className="spin" /> : <Sparkles size={12} />}
                <span>AI 위치 추천 받기</span>
              </button>
            </div>

            {placementRecommendation && (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5, background: 'var(--bg-surface)', padding: '8px', borderRadius: '6px' }}>
                💡 <strong>추론 근거:</strong> {placementRecommendation.reasoning}
              </div>
            )}
          </div>

          {/* 온톨로지 위치 지정 드롭다운 행 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                소속 패싯 (Domain Facet)
              </label>
              <select
                name="domainFacet"
                value={form.domainFacet}
                onChange={handleChange}
                style={{ width: '100%', padding: '7px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', fontSize: '0.75rem' }}
              >
                <option value="unit_process">단위 공정 (Unit Process)</option>
                <option value="device">반도체 소자 (Device)</option>
                <option value="operations">Fab 운영/수율 (Operations)</option>
                <option value="materials_infra">소재/인프라 (Infra)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                공정 스케일 (Scale Level)
              </label>
              <select
                name="scaleLevel"
                value={form.scaleLevel}
                onChange={handleChange}
                style={{ width: '100%', padding: '7px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', fontSize: '0.75rem' }}
              >
                <option value={1}>L1 원자/물성</option>
                <option value={2}>L2 박막/식각</option>
                <option value={3}>L3 소자 트랜지스터</option>
                <option value={4}>L4 웨이퍼/다이</option>
                <option value={5}>L5 첨단 패키징/모듈</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                세부 공정군
              </label>
              <input
                type="text"
                name="processCategory"
                value={form.processCategory}
                onChange={handleChange}
                style={{ width: '100%', padding: '7px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', fontSize: '0.75rem' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{ padding: '8px 14px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface-2)', fontSize: '0.8125rem', cursor: 'pointer' }}
            >
              취소
            </button>
            <button
              type="submit"
              style={{
                padding: '8px 18px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Send size={13} />
              <span>신규 개념 발의 티켓 등록 ➔</span>
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}
