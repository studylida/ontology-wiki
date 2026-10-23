import React, { useState } from 'react';
import { ReviewWikiSections } from './ReviewWikiSections';
import { ReviewSectionEditor } from './ReviewSectionEditor';
import { reviewSections } from '../../services/reviewDraftService';
import './review.css';

export function TwoSegmentEditor({currentTicket,reviewContent,isContentLoading,contentError,onRetryContent,currentUser,workingDraft,
  activeSection,onSectionChange,isDirty,isEditorDisabled,isActionLoading,onDraftChange,onSaveDraft,onOpenWikiPreview,onOpenApproveModal,onOpenRejectModal}) {
  const [showBaseline,setShowBaseline]=useState(true);
  if(!currentTicket) return <div className="review-empty">{contentError || '왼쪽 검토 큐에서 티켓을 선택하세요.'}</div>;
  const permissions=currentTicket.workingDraft?.permissions || {};
  const disabled=isEditorDisabled||isActionLoading||!permissions.canEdit;
  return <div className="review-workspace">
    <header className="review-workspace-header"><div><p className="review-eyebrow">검토 작업본 · {currentTicket.conceptTitle || currentTicket.conceptId}</p><h2>{currentTicket.title}</h2><p className="review-hint">티켓 판본 {currentTicket.ticketVersion} · <span role="status">{isActionLoading?'처리 중…':isDirty?'저장하지 않은 변경':'저장된 작업본'}</span></p></div>
      <div className="review-toolbar"><button type="button" disabled={disabled} onClick={onSaveDraft}>작업본 저장</button><button type="button" disabled={isActionLoading||!workingDraft} onClick={()=>onOpenWikiPreview(activeSection)}>위키 미리보기</button>
        {currentTicket.status==='pending'&&<><button type="button" disabled={isActionLoading} onClick={onOpenRejectModal}>반려</button><button className="review-primary" type="button" disabled={isActionLoading||!workingDraft||currentUser?.level<3} onClick={onOpenApproveModal}>승인</button></>}
      </div>
    </header>
    <p className="review-hint">모든 목차를 직접 편집할 수 있습니다. 저장과 지시문 실행은 작업본만 바꾸며, 승인할 때 위키에 반영됩니다.</p>
    <nav className="review-section-nav" aria-label="편집 목차">{reviewSections.map(([key,label])=><button type="button" key={key} aria-current={activeSection===key?'page':undefined} onClick={()=>onSectionChange(key)}>{label}</button>)}</nav>
    {contentError&&<div role="alert" className="review-content-error">{contentError}<button type="button" disabled={isActionLoading} onClick={onRetryContent}>다시 불러오기</button></div>}
    {isContentLoading&&<p role="status">현재 위키를 불러오는 중입니다…</p>}
    <button className="review-baseline-toggle" type="button" aria-expanded={showBaseline} onClick={()=>setShowBaseline(v=>!v)}>{showBaseline?'현재 위키 접기':'현재 위키 보기'}</button>
    <div className={`review-editor-panes ${showBaseline?'':'review-baseline-hidden'}`}>
      {showBaseline&&<section aria-label="현재 공용 위키" className="review-baseline"><header><h3>현재 위키</h3><span>읽기 전용</span></header><ReviewWikiSections section={activeSection} concept={reviewContent?.baselineConcept?.isRegistered===false?null:reviewContent?.baselineConcept} currentUser={currentUser} emptyMessage="현재 위키에 등록된 내용이 없습니다."/></section>}
      <section aria-label="승인할 작업본" className="review-authoring"><header><h3>{reviewSections.find(([key])=>key===activeSection)?.[1]} 편집</h3><span>{disabled?'읽기 전용':'직접 편집'}</span></header>
        {workingDraft&&<fieldset disabled={disabled}><ReviewSectionEditor section={activeSection} draft={workingDraft} onChange={onDraftChange} permissions={permissions}/></fieldset>}
      </section>
    </div>
  </div>;
}
