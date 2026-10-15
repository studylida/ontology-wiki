/**
 * 반도체 산업 지식 위키 - 애플리케이션 코어 로직
 * 공간 분리, 다차원 도메인 패싯, 스티키 플로팅 관점 바, 회사 드롭다운, 스마트 고민 추천기
 */

document.addEventListener("DOMContentLoaded", () => {
  // ── 전역 상태 (Global State) ──
  const state = {
    currentWorkspace: "wiki", // 'wiki' | 'ai' | 'investigation' | 'review'
    currentFacet: "facet-process", // 'facet-process' | 'facet-operations' | 'facet-equipment' | 'facet-materials'
    currentConceptId: "dry-etch",
    currentPerspective: "default", // 'default' | 'domain-memory' | 'company-a-hbm' | 'company-b-dram' | 'company-c-foundry'
    currentCompanyId: "company-a-hbm",
    currentSnapshotIndex: 2,
    selectedReviewId: "rev-01",
    readingDepth: "all", // 'all' | 'summary' | 'mech'
    sidebarNavMode: "domain" // 'domain' | 'scale'
  };

  // ── DOM 캐시 ──
  const dom = {
    // 워크스페이스 탭 & 뷰
    wsTabs: document.querySelectorAll(".ws-tab-btn"),
    viewSections: {
      wiki: document.getElementById("view-wiki"),
      ai: document.getElementById("view-ai"),
      investigation: document.getElementById("view-investigation"),
      review: document.getElementById("view-review")
    },
    // 사이드바 뷰들 (공간별 전용 사이드바)
    sidebarViews: {
      wiki: document.getElementById("sidebar-wiki-view"),
      ai: document.getElementById("sidebar-ai-view"),
      investigation: document.getElementById("sidebar-investigation-view"),
      review: document.getElementById("sidebar-review-view")
    },
    sidebarModeBtns: document.querySelectorAll(".sidebar-mode-btn"),
    sidebarDomainContainer: document.getElementById("sidebar-domain-container"),
    sidebarScaleContainer: document.getElementById("sidebar-scale-container"),
    sidebarScaleTree: document.getElementById("sidebar-scale-tree"),
    domainFacetTabs: document.getElementById("domain-facet-tabs"),
    facetSubnavTitle: document.getElementById("facet-subnav-title"),
    sidebarProcesses: document.getElementById("sidebar-processes"),
    sidebarReviewQueueList: document.getElementById("sidebar-review-queue-list"),
    // 팹 라이프사이클 스테이지 인디케이터
    fabStageStrip: document.getElementById("fab-stage-strip"),
    stageStripCategoryBadge: document.getElementById("stage-strip-category-badge"),
    stageStripTitle: document.getElementById("stage-strip-title"),
    stageStripMeta: document.getElementById("stage-strip-meta"),
    stageStripCloseBtn: document.getElementById("stage-strip-close-btn"),
    stageStripFlow: document.getElementById("stage-strip-flow"),
    stageStripReopenBar: document.getElementById("stage-strip-reopen-bar"),
    stageStripReopenBtn: document.getElementById("stage-strip-reopen-btn"),
    // 개념 헤더 Level 뱃지 및 열람 심도 컨트롤러
    conceptLevelBadge: document.getElementById("concept-level-badge"),
    conceptScaleBadge: document.getElementById("concept-scale-badge"),
    btnDepthAll: document.getElementById("btn-depth-all"),
    btnDepthSummary: document.getElementById("btn-depth-summary"),
    btnDepthMech: document.getElementById("btn-depth-mech"),
    principlesAccordionItem: document.getElementById("principles-accordion-item"),
    // 관점 바 (스티키 블록 & 동적 탭 컨테이너)
    perspectiveBarBlock: document.getElementById("perspective-bar-block"),
    perspectiveTabsContainer: document.getElementById("perspective-tabs-container"),
    perspectiveDesc: document.getElementById("perspective-desc"),
    appliedCardContainer: document.getElementById("applied-card-container"),
    // 우측 드로어 (근거 리더)
    evidenceDrawer: document.getElementById("evidence-drawer"),
    drawerBackdrop: document.getElementById("drawer-backdrop"),
    drawerCloseBtn: document.getElementById("drawer-close-btn"),
    drawerContent: document.getElementById("drawer-content"),
    // 인라인 팝오버
    conceptPopover: document.getElementById("concept-popover"),
    popoverTitle: document.getElementById("popover-title"),
    popoverSummary: document.getElementById("popover-summary"),
    popoverAiContext: document.getElementById("popover-ai-context"),
    // 모달들
    suggestModal: document.getElementById("suggest-modal"),
    suggestModalClose: document.getElementById("suggest-modal-close"),
    suggestForm: document.getElementById("suggest-form"),
    openSuggestModalBtn: document.getElementById("open-suggest-modal-btn"),
    editParamsModal: document.getElementById("edit-params-modal"),
    editParamsForm: document.getElementById("edit-params-form"),
    // 런타임 모드 세그먼트 스위처 (Transitions.dev sliding-tabs)
    runtimeModeSwitcher: document.getElementById("runtime-mode-switcher"),
    runtimeModeIndicator: document.getElementById("runtime-mode-indicator"),
    btnModeMock: document.getElementById("btn-mode-mock"),
    btnModeLive: document.getElementById("btn-mode-live"),
    // 타 프로젝트 백엔드 연동 & API Key 보안 허브 (Transitions.dev Modal)
    headlessApiModal: document.getElementById("headless-api-modal"),
    headlessModalClose: document.getElementById("headless-modal-close"),
    btnCloseHeadlessModal: document.getElementById("btn-close-headless-modal"),
    hubKeyStatusBadge: document.getElementById("hub-key-status-badge"),
    btnEditKeys: document.getElementById("btn-edit-keys"),
    btnDeleteKeys: document.getElementById("btn-delete-keys"),
    inputGoogleKey: document.getElementById("input-google-key"),
    labelGoogleMasked: document.getElementById("label-google-masked"),
    btnToggleGoogleMask: document.getElementById("btn-toggle-google-mask"),
    inputOpenAIKey: document.getElementById("input-openai-key"),
    labelOpenAIMasked: document.getElementById("label-openai-masked"),
    btnToggleOpenAIMask: document.getElementById("btn-toggle-openai-mask"),
    keySecurityNote: document.getElementById("key-security-note"),
    btnSaveKeysHub: document.getElementById("btn-save-keys-hub"),
    // 타 프로젝트 API 시뮬레이터 (Headless Simulator)
    headlessClientSelect: document.getElementById("headless-client-select"),
    headlessQueryInput: document.getElementById("headless-query-input"),
    headlessMultimodalCb: document.getElementById("headless-multimodal-cb"),
    btnRunHeadlessQuery: document.getElementById("btn-run-headless-query"),
    headlessGapBanner: document.getElementById("headless-gap-banner"),
    headlessGapDesc: document.getElementById("headless-gap-desc"),
    btnTransferToReview: document.getElementById("btn-transfer-to-review"),
    headlessResultsContainer: document.getElementById("headless-results-container"),
    headlessElapsedBadge: document.getElementById("headless-elapsed-badge"),
    codeHeadlessJson: document.getElementById("code-headless-json"),
    codeHeadlessCurl: document.getElementById("code-headless-curl"),
    listHeadlessTrace: document.getElementById("list-headless-trace"),
    btnCopyJson: document.getElementById("btn-copy-json"),
    btnCopyCurl: document.getElementById("btn-copy-curl"),
    // 위키 1번 탭 플로팅 챗봇
    floatingChatFab: document.getElementById("floating-chat-fab"),
    floatingChatWidget: document.getElementById("floating-chat-widget"),
    chatWidgetClose: document.getElementById("chat-widget-close"),
    chatEngineModeBadge: document.getElementById("chat-engine-mode-badge"),
    chatContextBadge: document.getElementById("chat-context-badge"),
    chatCurConceptName: document.getElementById("chat-cur-concept-name"),
    floatingChatMessages: document.getElementById("floating-chat-messages"),
    floatingChatInput: document.getElementById("floating-chat-input"),
    floatingChatSendBtn: document.getElementById("floating-chat-send-btn"),
    // 전역 검색 모달
    searchModal: document.getElementById("search-modal"),
    searchModalClose: document.getElementById("search-modal-close"),
    globalSearchTrigger: document.getElementById("global-search-trigger"),
    globalSearchInput: document.getElementById("global-search-input"),
    searchCounterBadge: document.getElementById("search-counter-badge"),
    // AI 분석실
    painpointCardList: document.getElementById("painpoint-card-list"),
    aiPromptInput: document.getElementById("ai-prompt-input"),
    aiClarifyBtn: document.getElementById("ai-clarify-btn"),
    aiDialogueArea: document.getElementById("ai-dialogue-area"),
    aiPainpointSection: document.getElementById("ai-painpoint-section"),
    aiRunBtn: document.getElementById("ai-run-btn"),
    aiSnapshotTimeline: document.getElementById("ai-snapshot-timeline"),
    aiResultCard: document.getElementById("ai-result-card"),
    tagTextA: document.getElementById("tag-text-a"),
    tagTextB: document.getElementById("tag-text-b"),
    tagTextDomain: document.getElementById("tag-text-domain"),
    // 조사 작업실
    preSeededList: document.getElementById("pre-seeded-sources-list"),
    sourcesPackList: document.getElementById("sources-pack-list"),
    runSeedingBtn: document.getElementById("run-seeding-btn"),
    seedingResultArea: document.getElementById("seeding-result-area"),
    investigationQueryInput: document.getElementById("investigation-query-input"),
    btnInvestigateClarify: document.getElementById("btn-investigate-clarify"),
    investigationDialogueArea: document.getElementById("investigation-dialogue-area"),
    // 검토 센터
    diffCurrentText: document.getElementById("diff-current-text"),
    diffDraftText: document.getElementById("diff-draft-text"),
    btnToggleEditor: document.getElementById("btn-toggle-editor"),
    diffDraftContainer: document.getElementById("diff-draft-container"),
    reviewEditorContainer: document.getElementById("review-editor-container"),
    reviewEditorInput: document.getElementById("review-editor-input"),
    btnSaveEdit: document.getElementById("btn-save-edit"),
    btnCancelEdit: document.getElementById("btn-cancel-edit"),
    agentDirectiveInput: document.getElementById("agent-directive-input"),
    btnSendDirective: document.getElementById("btn-send-directive"),
    directiveStatusArea: document.getElementById("directive-status-area"),
    integrityEvidence: document.getElementById("integrity-evidence"),
    integrityOntology: document.getElementById("integrity-ontology"),
    integrityImpact: document.getElementById("integrity-impact"),
    approveReviewBtn: document.getElementById("approve-review-btn"),
    gotoWikiBtn: document.getElementById("goto-wiki-btn"),
    // 위키 미리보기 모달 & 승인 완료 모달 (Transitions.dev)
    btnPreviewWiki: document.getElementById("btn-preview-wiki"),
    btnQuickPreviewDiff: document.getElementById("btn-quick-preview-diff"),
    modalWikiPreview: document.getElementById("modal-wiki-preview"),
    wikiPreviewContent: document.getElementById("wiki-preview-content"),
    closeWikiPreviewBtn: document.getElementById("close-wiki-preview-btn"),
    btnPreviewCancel: document.getElementById("btn-preview-cancel"),
    btnPreviewToEditor: document.getElementById("btn-preview-to-editor"),
    btnPreviewConfirmApprove: document.getElementById("btn-preview-confirm-approve"),
    togglePreviewDiffHighlight: document.getElementById("toggle-preview-diff-highlight"),
    approvalSuccessModal: document.getElementById("approval-success-modal"),
    approvalSuccessMsg: document.getElementById("approval-success-msg"),
    btnSuccessGotoWiki: document.getElementById("btn-success-goto-wiki"),
    btnSuccessStayReview: document.getElementById("btn-success-stay-review"),
    // 토스트
    toastContainer: document.getElementById("toast-container")
  };

  // ── 토스트 헬퍼 ──
  function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 6L9 17l-5-5"/>
      </svg>
      <span>${message}</span>
    `;
    dom.toastContainer.appendChild(toast);
    
    requestAnimationFrame(() => {
      toast.classList.add("show");
    });

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // ── 0. 전역 실시간 검색 엔진 (Spotlight Cmd+K Modal) ──
  let searchSelectedIndex = 0;
  let currentSearchResults = [];

  function openSearchModal() {
    if (!dom.searchModal) return;
    dom.searchModal.classList.add("open");
    dom.globalSearchInput.value = "";
    dom.globalSearchInput.focus();
    renderSearchResults("");
  }

  function closeSearchModal() {
    if (!dom.searchModal) return;
    dom.searchModal.classList.remove("open");
  }

  function renderSearchResults(query) {
    const q = query.trim().toLowerCase();
    const allConcepts = Object.values(WikiStore.concepts || {});
    
    if (dom.searchCounterBadge) {
      dom.searchCounterBadge.textContent = `${allConcepts.length}개 개념 인덱싱됨`;
    }

    if (!q) {
      // 초기 상태: 최근/대표 추천 개념 표시
      currentSearchResults = allConcepts.slice(0, 8);
    } else {
      // 매칭 검색
      currentSearchResults = allConcepts.filter(c => {
        const titleMatch = c.title?.toLowerCase().includes(q);
        const engMatch = c.engName?.toLowerCase().includes(q);
        const aliasMatch = c.aliases?.some(a => a.toLowerCase().includes(q));
        const procMatch = c.processName?.toLowerCase().includes(q);
        const summaryMatch = c.summary?.toLowerCase().includes(q);
        return titleMatch || engMatch || aliasMatch || procMatch || summaryMatch;
      }).slice(0, 10);
    }

    searchSelectedIndex = 0;

    if (currentSearchResults.length === 0) {
      dom.searchResultsList.innerHTML = `
        <div class="search-empty-state">
          <p><strong>'${query}'</strong>에 일치하는 온톨로지 개념을 찾지 못했습니다.</p>
          <span style="font-size:0.75rem; color:var(--text-muted); margin-top:4px; display:block;">
            💡 약어(EUV, ALE, ZAZ, KGD, TDDB 등) 또는 공정명(식각, 노광, 패키징)으로 검색해 보세요.
          </span>
        </div>
      `;
      return;
    }

    dom.searchResultsList.innerHTML = currentSearchResults.map((c, idx) => {
      const isSelected = idx === searchSelectedIndex;
      const aliasesText = c.aliases ? c.aliases.slice(0, 3).join(", ") : "";
      return `
        <div class="search-result-item ${isSelected ? 'selected' : ''}" data-index="${idx}" data-concept-id="${c.id}">
          <div class="search-result-top">
            <div class="search-result-title">
              <span>${c.title}</span>
              ${aliasesText ? `<span class="search-result-badge">${aliasesText}</span>` : ""}
            </div>
            <span style="font-size:0.75rem; color:var(--text-muted);">${c.processName || "공정 기술"}</span>
          </div>
          <div class="search-result-summary">${c.summary || ""}</div>
        </div>
      `;
    }).join("");

    // 클릭 이벤트 바인딩
    dom.searchResultsList.querySelectorAll(".search-result-item").forEach(item => {
      item.addEventListener("click", () => {
        const cid = item.dataset.conceptId;
        window.selectWikiConcept(cid);
        closeSearchModal();
      });
      item.addEventListener("mouseenter", () => {
        dom.searchResultsList.querySelectorAll(".search-result-item").forEach(el => el.classList.remove("selected"));
        item.classList.add("selected");
        searchSelectedIndex = parseInt(item.dataset.index, 10);
      });
    });
  }

  // 검색 인풋 이벤트
  dom.globalSearchInput?.addEventListener("input", (e) => {
    renderSearchResults(e.target.value);
  });

  // 키보드 네비게이션
  dom.globalSearchInput?.addEventListener("keydown", (e) => {
    const items = dom.searchResultsList.querySelectorAll(".search-result-item");
    if (items.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      searchSelectedIndex = (searchSelectedIndex + 1) % items.length;
      updateSearchSelection(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      searchSelectedIndex = (searchSelectedIndex - 1 + items.length) % items.length;
      updateSearchSelection(items);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (currentSearchResults[searchSelectedIndex]) {
        window.selectWikiConcept(currentSearchResults[searchSelectedIndex].id);
        closeSearchModal();
      }
    }
  });

  function updateSearchSelection(items) {
    items.forEach((item, idx) => {
      item.classList.toggle("selected", idx === searchSelectedIndex);
      if (idx === searchSelectedIndex) {
        item.scrollIntoView({ block: "nearest" });
      }
    });
  }

  // 검색 모달 열기/닫기 바인딩
  dom.globalSearchTrigger?.addEventListener("click", openSearchModal);
  dom.searchModalClose?.addEventListener("click", closeSearchModal);
  dom.searchModal?.addEventListener("click", (e) => {
    if (e.target === dom.searchModal) closeSearchModal();
  });

  // 전역 단축키 (Cmd+K / Ctrl+K / ESC)
  window.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (dom.searchModal?.classList.contains("open")) {
        closeSearchModal();
      } else {
        openSearchModal();
      }
    } else if (e.key === "Escape") {
      closeSearchModal();
    }
  });
  // ── 스티키 바 정밀 센티넬 감지 (Transitions.dev 무단차 감속 이징 & 0-Layout Shift) ──
  const stickySentinel = document.getElementById("perspective-sticky-sentinel");
  if (stickySentinel && dom.perspectiveBarBlock && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(([entry]) => {
      // 센티넬이 52px(탑바 높이) 위로 밀려나면 sticky가 시작된 것이므로 .is-stuck 활성화
      const isStuck = !entry.isIntersecting && entry.boundingClientRect.top <= 55;
      dom.perspectiveBarBlock.classList.toggle("is-stuck", isStuck);
    }, {
      rootMargin: "-52px 0px 0px 0px",
      threshold: [0, 1]
    });
    observer.observe(stickySentinel);
  } else {
    // 폴백: 히스테리시스 스크롤
    window.addEventListener("scroll", () => {
      const isStuck = window.scrollY > 200;
      dom.perspectiveBarBlock?.classList.toggle("is-stuck", isStuck);
    }, { passive: true });
  }

  // ── 1. 워크스페이스 공간 분리 ──
  function setWorkspace(wsName) {
    state.currentWorkspace = wsName;
    dom.wsTabs.forEach(tab => {
      tab.classList.toggle("active", tab.dataset.workspace === wsName);
    });

    Object.entries(dom.viewSections).forEach(([key, section]) => {
      const isTarget = (key === wsName);
      section.style.display = isTarget ? "block" : "none";
      if (isTarget) {
        section.classList.remove("fade-slide-up");
        void section.offsetWidth;
        section.classList.add("fade-slide-up");
      }
    });

    Object.entries(dom.sidebarViews).forEach(([key, view]) => {
      if (view) {
        const isTarget = (key === wsName);
        view.style.display = isTarget ? "block" : "none";
        if (isTarget) {
          view.classList.remove("fade-slide-up");
          void view.offsetWidth;
          view.classList.add("fade-slide-up");
        }
      }
    });

    if (wsName === "wiki") {
      renderConceptDetail(state.currentConceptId);
    } else if (wsName === "review") {
      renderReviewQueue();
    } else if (wsName === "ai") {
      renderPainPoints(dom.aiPromptInput?.value || "");
    } else if (wsName === "investigation") {
      renderDiscoveryLogs();
    }
  }

  dom.wsTabs.forEach(tab => {
    tab.addEventListener("click", () => setWorkspace(tab.dataset.workspace));
  });

  // ── 2. 팹 라이프사이클 파이프라인 (4대 온톨로지 축별 동적 플로우 & active 매칭) ──
  const fabPipelines = {
    "facet-device": {
      categoryName: "소자·제품군 (HBM · 3D NAND · GAA Logic · DRAM)",
      steps: [
        { label: "1. AI 메모리 HBM", conceptId: "mr-muf", matchConcepts: ["mr-muf", "hybrid-bonding", "hbm-kgd-testing", "cowos-interposer-cuf"] },
        { label: "2. 3D V-NAND", conceptId: "3d-nand-ctf-architecture", matchConcepts: ["3d-nand-ctf-architecture", "4d-nand-puc", "3d-nand-mo-wordline", "cryogenic-etch", "bbp-defect-inspection"] },
        { label: "3. 2nm GAA 로직", conceptId: "gaa-nanosheet-etch", matchConcepts: ["gaa-nanosheet-etch", "hkmg-transistor", "high-na-euv", "euv-lithography", "model-based-opc", "tddb-reliability-physics"] },
        { label: "4. 초고밀도 DRAM", conceptId: "dram-zaz-capacitor", matchConcepts: ["dram-zaz-capacitor", "dram-airgap-bitline", "ald-deposition", "cu-damascene-cmp"] }
      ]
    },
    "facet-process": {
      categoryName: "제조 단위 공정 (Unit Process Pipeline)",
      steps: [
        { label: "1. 웨이퍼", conceptId: "wafer-fabrication", matchConcepts: ["wafer-fabrication", "silicon-ingot"] },
        { label: "2. 산화", conceptId: "thermal-oxidation", matchConcepts: ["thermal-oxidation"] },
        { label: "3. 포토", conceptId: "photolithography", matchConcepts: ["photolithography", "euv-lithography", "high-na-euv", "model-based-opc", "photo-resist"] },
        { label: "4. 식각", conceptId: "dry-etch", matchConcepts: ["dry-etch", "cryogenic-etch", "ale-etch", "gaa-nanosheet-etch", "plasma-discharge"] },
        { label: "5. 박막/증착", conceptId: "ald-deposition", matchConcepts: ["ald-deposition", "hkmg-transistor", "dram-zaz-capacitor", "3d-nand-ctf-architecture", "4d-nand-puc"] },
        { label: "6. 배선/CMP", conceptId: "cu-damascene-cmp", matchConcepts: ["cu-damascene-cmp", "cmp-slurry-bta-passivation", "dram-airgap-bitline", "3d-nand-mo-wordline"] },
        { label: "7. EDS/검사", conceptId: "hbm-kgd-testing", matchConcepts: ["hbm-kgd-testing", "bbp-defect-inspection"] },
        { label: "8. 첨단 패키징", conceptId: "mr-muf", matchConcepts: ["mr-muf", "hybrid-bonding", "cowos-interposer-cuf", "fan-out-wafer-level-packaging"] }
      ]
    },
    "facet-operations": {
      categoryName: "팹 지능화 & 운영 (Operations & Quality Pipeline)",
      steps: [
        { label: "1. SECS/GEM 통신", conceptId: "ees-rms", matchConcepts: ["ees-rms"] },
        { label: "2. 실시간 OES 센싱", conceptId: "fab-fdc-oes-realtime", matchConcepts: ["fab-fdc-oes-realtime"] },
        { label: "3. FDC 아킹 감지", conceptId: "plasma-fdc-sensor", matchConcepts: ["plasma-fdc-sensor"] },
        { label: "4. 3-Sigma SPC 통계", conceptId: "spc-control-chart", matchConcepts: ["spc-control-chart"] },
        { label: "5. R2R 피드백 제어", conceptId: "run-to-run", matchConcepts: ["run-to-run"] },
        { label: "6. 수율 모델링", conceptId: "yield-negative-binomial-modeling", matchConcepts: ["yield-negative-binomial-modeling"] },
        { label: "7. TDDB 신뢰성 모델", conceptId: "tddb-reliability-physics", matchConcepts: ["tddb-reliability-physics"] }
      ]
    },
    "facet-materials": {
      categoryName: "소재·화학 & 팹 인프라 (Materials & Infra Pipeline)",
      steps: [
        { label: "1. 초순수 UPW 공급", conceptId: "ultra-pure-water-upw", matchConcepts: ["ultra-pure-water-upw"] },
        { label: "2. 친환경 PFC 스크러버", conceptId: "fab-subfab-pfc-scrubber", matchConcepts: ["fab-subfab-pfc-scrubber"] },
        { label: "3. 포토 감광제(PR/MOR)", conceptId: "photo-resist", matchConcepts: ["photo-resist"] },
        { label: "4. 저하중 CMP 슬러리", conceptId: "cmp-slurry-bta-passivation", matchConcepts: ["cmp-slurry-bta-passivation"] },
        { label: "5. High-k ZAZ 유전체", conceptId: "dram-zaz-capacitor", matchConcepts: ["dram-zaz-capacitor"] },
        { label: "6. 무불소 몰리브덴 ALD", conceptId: "3d-nand-mo-wordline", matchConcepts: ["3d-nand-mo-wordline"] },
        { label: "7. 액상 EMC 몰딩 수지", conceptId: "mr-muf", matchConcepts: ["mr-muf"] }
      ]
    }
  };

  // ── 37개 온톨로지 개념의 수준별 위계 정보 (Level 1 / 2 / 3 체계) ──
  const conceptLevels = {
    // Level 1: 산업 공통 기초 (9개)
    "wafer-fabrication": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "웨이퍼 기판 제조 및 잉곳 성장의 공통 표준 정의" },
    "silicon-ingot": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "단결정 규소 성장(CZ법)의 기초 물리 및 공통 정의" },
    "thermal-oxidation": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "실리콘 표면 열산화막(SiO2) 형성 기초 원리" },
    "photolithography": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "포토마스크 회로 패턴 전사 및 현상 기초 정의" },
    "photo-resist": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "감광제 고분자 폴리머 반응 및 포토 필수 소재 기초" },
    "dry-etch": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "플라즈마 반응성 이온 식각(RIE)의 기초 개념" },
    "plasma-discharge": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "RF 전기장에 의한 가스 이온화 및 플라즈마 기초 물리학" },
    "ald-deposition": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "원자층 증착(ALD) 자기제한 표면 반응의 기본 정의" },
    "cu-damascene-cmp": { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "구리 배선 형성(다마신) 및 표면 평탄화 기초" },

    // Level 2: 선단 공학 메커니즘 (13개)
    "euv-lithography": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "13.5nm 극자외선 노광 및 Rayleigh 해상도 한계 극복" },
    "high-na-euv": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "0.55NA 아나모픽 광학계 및 극초미세 패턴 DOF 제어" },
    "model-based-opc": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "회절 광학 수치 시뮬레이션 및 마스크 역보정 역산" },
    "ale-etch": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "원자층 단위 표면 흡착 및 저에너지 탈착 정밀 제어" },
    "cryogenic-etch": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "-60℃ 극저온 응축 패시베이션 및 고종횡비 채널 홀 식각" },
    "gaa-nanosheet-etch": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "2nm 로직 SiGe 선택 식각 및 나노시트 채널 릴리즈" },
    "hkmg-transistor": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "양자역학적 게이트 누설 차단 및 일함수 엔지니어링" },
    "dram-zaz-capacitor": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "ZrO2-Al2O3-ZrO2 다층 나노박막 및 유전율 극대화" },
    "dram-airgap-bitline": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "진공 유전율(k=1.0) 기반 기생 커패시턴스 억제 물리" },
    "3d-nand-ctf-architecture": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "부유게이트 간섭 제거 및 SiN 질화막 전하 트랩 물리" },
    "tddb-reliability-physics": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "절연막 열화 결함 전도 필라멘트 및 Weibull 수명 통계" },
    "yield-negative-binomial-modeling": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "결함 뭉침(Cluster Parameter) 보정 수율 예측 수식" },
    "fan-out-wafer-level-packaging": { level: 2, label: "Level 2 · 선단 공학 메커니즘", badgeClass: "badge-level-2", desc: "기판 없는 재배선(RDL) 및 칩 휨 제어 패키징 물리" },

    // Level 3: 현장 규격 & 팹 지능화 (15개)
    "mr-muf": { level: 3, label: "Level 3 · 현장 규격 & 첨단 패키징", badgeClass: "badge-level-3", desc: "HBM3E/HBM4 양산 플럭스 리플로우 및 액상 EMC 가압 몰딩 규격" },
    "hybrid-bonding": { level: 3, label: "Level 3 · 현장 규격 & 차세대 패키징", badgeClass: "badge-level-3", desc: "Cu-Cu 직접 원자 결합, 플라즈마 표면 활성화 및 무범프 인터커넥트" },
    "cowos-interposer-cuf": { level: 3, label: "Level 3 · 현장 규격 & 2.5D 패키징", badgeClass: "badge-level-3", desc: "TSV 실리콘 인터포저 결합 및 모세관 언더필 양산 제어 규격" },
    "hbm-kgd-testing": { level: 3, label: "Level 3 · 현장 검사 & 신뢰성 수율", badgeClass: "badge-level-3", desc: "웨이퍼 레벨 초고속 ATE 프로빙 및 Known Good Die 선별 기준" },
    "bbp-defect-inspection": { level: 3, label: "Level 3 · 팹 광학 검사 & 수율", badgeClass: "badge-level-3", desc: "광대역 단파장 플라즈마 레이저 및 1x nm 킬러 결함 인라인 검출" },
    "4d-nand-puc": { level: 3, label: "Level 3 · 초고집적 셀 아키텍처", badgeClass: "badge-level-3", desc: "주변부 회로(Peri)를 셀 하부에 배치하여 팹 다이 효율 극대화" },
    "3d-nand-mo-wordline": { level: 3, label: "Level 3 · 신소재 박막 & 공정", badgeClass: "badge-level-3", desc: "무불소 전구체 Mo ALD 증착 및 텅스텐 대체 초저저항 배선 레시피" },
    "fab-fdc-oes-realtime": { level: 3, label: "Level 3 · 팹 지능화 & 센서 FDC", badgeClass: "badge-level-3", desc: "2,048채널 전스펙트럼 실시간 OES 분광 분석 및 EPD 종말점 판정" },
    "plasma-fdc-sensor": { level: 3, label: "Level 3 · 팹 지능화 & 장비 FDC", badgeClass: "badge-level-3", desc: "RF VI-Probe 고주파 임피던스 센싱 및 마이크로 아킹 사전 인터락" },
    "spc-control-chart": { level: 3, label: "Level 3 · 팹 지능화 & SPC 통계", badgeClass: "badge-level-3", desc: "3-Sigma 관리 한계선 통계 제어 및 Western Electric 8대 룰 판정" },
    "run-to-run": { level: 3, label: "Level 3 · 팹 지능화 & APC 제어", badgeClass: "badge-level-3", desc: "EWMA 기반 런간 계측 오차 산출 및 식각/CMP 파라미터 피드백 통제" },
    "ees-rms": { level: 3, label: "Level 3 · 팹 지능화 & 장비 통신", badgeClass: "badge-level-3", desc: "SECS/GEM 장비 온라인 통신 및 양산 레시피 무단 변조 방지 RMS" },
    "ultra-pure-water-upw": { level: 3, label: "Level 3 · 팹 인프라 & 초순수", badgeClass: "badge-level-3", desc: "18.2MΩ·cm 연속 공급 루프 및 서브팹 유틸리티 TOC 한계 통제" },
    "fab-subfab-pfc-scrubber": { level: 3, label: "Level 3 · 팹 환경 & 서브팹 배기", badgeClass: "badge-level-3", desc: "고온 열분해 및 습식 세정 연계 친환경 온실가스 분해 설비" },
    "cmp-slurry-bta-passivation": { level: 3, label: "Level 3 · 첨단 화학 & 슬러리", badgeClass: "badge-level-3", desc: "초저하중 CMP 슬러리 입도 통제 및 BTA 부식 억제제 계면 화학" }
  };

  // ── 37개 온톨로지 개념의 물리적 규모(Scale) 위계 정보 (5단계 체계) ──
  const scaleDefinitions = [
    { scale: 1, name: "Scale 1: 원자·물성", icon: "🔬", range: "0.1nm ~ 1nm", desc: "원자 흡착, 격자 결함, 양자 물성" },
    { scale: 2, name: "Scale 2: 소자·패턴", icon: "📐", range: "10nm ~ 수 mm", desc: "3D 나노 패턴, 셀 어레이, 칩 다이" },
    { scale: 3, name: "Scale 3: 공정·레시피", icon: "⚙️", range: "1cm ~ 300mm", desc: "웨이퍼 단위 가공, 플라즈마 방전, 통계" },
    { scale: 4, name: "Scale 4: 설비·챔버", icon: "🏭", range: "1m ~ 10m", desc: "챔버 하드웨어, 센서 계측, 장비 통신" },
    { scale: 5, name: "Scale 5: 팹 인프라", icon: "🌐", range: "100m ~ 1km", desc: "클린룸 유틸리티, 서브팹 배기, 환경" }
  ];

  const conceptScales = {
    // ── Scale 5: 팹 인프라 & 환경 (100m ~ 1km) ──
    "ultra-pure-water-upw": {
      scale: 5,
      scaleLabel: "Scale 5 · 팹 인프라 & 환경",
      badgeClass: "badge-scale-5",
      scopeName: "100m ~ 1km 팹 단지 공급망",
      parents: [
        { id: null, scale: 5, title: "용인·평택 메가팹 중앙 수처리 원수 인프라", desc: "지하수/공업용수 취수 및 클린룸 전체 공급망 인프라" }
      ],
      children: [
        { id: "cu-damascene-cmp", scale: 3, title: "구리 다마신 배선 평탄화 (Cu CMP)", desc: "18.2MΩ·cm 초순수 기반 무결점 슬러리 세정 및 연마 공급" },
        { id: "wafer-fabrication", scale: 3, title: "웨이퍼 제조 단위 공정", desc: "베어 웨이퍼 연마 후 잔류 금속 파티클 초정밀 세정 유틸리티" },
        { id: "high-na-euv", scale: 4, title: "High-NA EUV 노광 장비 (0.55NA)", desc: "0.55NA 투과 광학 미러 및 고출력 광원 초정밀 냉각수 순환" }
      ]
    },
    "fab-subfab-pfc-scrubber": {
      scale: 5,
      scaleLabel: "Scale 5 · 팹 인프라 & 환경",
      badgeClass: "badge-scale-5",
      scopeName: "100m ~ 1km 서브팹 환경 설비",
      parents: [
        { id: null, scale: 5, title: "팹 통합 환경 모니터링 및 탄소중립 배기망", desc: "클린룸 지하 서브팹(Sub-Fab) 온실가스 통합 처리 및 전사 환경 규제 모니터링" }
      ],
      children: [
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "식각 챔버에서 배출되는 과불화화합물(PFCs) 고온 열분해 및 세정 처리 연동" },
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "챔버 배기 펌프 후단 과불화 가스(CF4, SF6) 99.9% 분해 처리" }
      ]
    },

    // ── Scale 4: 설비 & 베이 (1m ~ 10m) ──
    "euv-lithography": {
      scale: 4,
      scaleLabel: "Scale 4 · 설비 & 챔버",
      badgeClass: "badge-scale-4",
      scopeName: "1m ~ 10m 진공 노광 스캐너",
      parents: [
        { id: "ultra-pure-water-upw", scale: 5, title: "초순수 UPW 공급 인프라", desc: "ASML NXE 스캐너 고출력 CO2 레이저 플라즈마 틴(Sn) 집광 냉각 유틸리티" }
      ],
      children: [
        { id: "photolithography", scale: 3, title: "포토리소그래피 노광 공정", desc: "13.5nm 극자외선 기반 서브 10nm 임계 치수(CD) 회로 패터닝 레시피 집행" },
        { id: "photo-resist", scale: 1, title: "감광제 (Photoresist)", desc: "EUV 광자 흡수 및 산발생제(PAG) 화학 증폭형 고분자 반응 통제" },
        { id: "model-based-opc", scale: 2, title: "모델 기반 광학 근접 보정 (MB-OPC)", desc: "EUV 회절 한계 극복을 위한 마스크 보정 광학 시뮬레이션 데이터 수용" }
      ]
    },
    "high-na-euv": {
      scale: 4,
      scaleLabel: "Scale 4 · 설비 & 챔버",
      badgeClass: "badge-scale-4",
      scopeName: "1m ~ 10m 차세대 아나모픽 스캐너",
      parents: [
        { id: "ultra-pure-water-upw", scale: 5, title: "초순수 UPW 공급 인프라", desc: "0.55NA 아나모픽 투과 광학 미러 초고순도 냉각 및 진공 팹 인프라" },
        { id: "euv-lithography", scale: 4, title: "기존 0.33NA EUV 스캐너", desc: "0.33NA 광학계의 해상도 한계 극복을 위한 아나모픽 광학계 진화" }
      ],
      children: [
        { id: "model-based-opc", scale: 2, title: "모델 기반 광학 근접 보정 (MB-OPC)", desc: "아나모픽 8x/4x 비대칭 광학 수차 보정 마스크 역산 데이터 집행" },
        { id: "photo-resist", scale: 1, title: "감광제 (Photoresist)", desc: "초미세 패턴 DOF 감소에 대응하는 초박막 PR 도포 및 반응성 제어" }
      ]
    },
    "plasma-fdc-sensor": {
      scale: 4,
      scaleLabel: "Scale 4 · 설비 & 챔버",
      badgeClass: "badge-scale-4",
      scopeName: "1m ~ 10m 플라즈마 챔버 하드웨어",
      parents: [
        { id: "fab-subfab-pfc-scrubber", scale: 5, title: "친환경 PFC 배기 스크러버", desc: "식각 챔버 진공 펌프 배기 라인 및 유틸리티 하드웨어 연동" },
        { id: "ees-rms", scale: 4, title: "설비 엔지니어링 & RMS 통신", desc: "SECS/GEM 통신을 통한 실시간 고속 임피던스 센서 데이터 MES 보고" }
      ],
      children: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "식각 공정 중 챔버 내부 파티클 번(Burn) 발생 시 마이크로초 단위 플라즈마 차단" },
        { id: "plasma-discharge", scale: 3, title: "플라즈마 방전 기초 물리학", desc: "RF 13.56MHz 정합 임피던스 위상차 검출 및 챔버 마이크로 아킹 방전 감지" },
        { id: "fab-fdc-oes-realtime", scale: 3, title: "실시간 OES 분광 FDC 및 EPD", desc: "RF 센서와 광학 분광 센서의 다변량 융합 FDC 분석 연계" }
      ]
    },
    "ees-rms": {
      scale: 4,
      scaleLabel: "Scale 4 · 설비 & 챔버",
      badgeClass: "badge-scale-4",
      scopeName: "1m ~ 10m 장비 통신 & 레시피 서버",
      parents: [
        { id: null, scale: 5, title: "팹 중앙 MES & 호스트 통신망", desc: "팹 호스트 MES-장비 SECS/GEM 온라인 네트워크 및 중앙 통제 센터" }
      ],
      children: [
        { id: "run-to-run", scale: 3, title: "Run-to-Run 첨단 공정 제어 (APC)", desc: "엔지니어 레시피 무단 변경 차단 및 공정 파라미터 자동 다운로드 집행" },
        { id: "spc-control-chart", scale: 3, title: "SPC 통계적 공정 관리", desc: "장비 알람 및 관리 한계선 이탈 시 설비 자동 인터락(Interlock) 집행" },
        { id: "mr-muf", scale: 2, title: "HBM MR-MUF 액상 몰딩 패키징", desc: "HBM 오토클레이브 가압 챔버 1.5MPa 양산 레시피 무단 변조 차단 통제" }
      ]
    },

    // ── Scale 3: 단위 공정 & 런 (1cm ~ 300mm) ──
    "dry-etch": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm RIE 플라즈마 챔버",
      parents: [
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "식각 챔버 RF VI-Probe 임피던스 센싱 및 아킹 사전 인터락 통제" },
        { id: "run-to-run", scale: 3, title: "Run-to-Run 첨단 공정 제어 (APC)", desc: "직전 웨이퍼 식각 깊이 계측값 기반 챔버 RF 파워 및 시간 자동 보정" }
      ],
      children: [
        { id: "ale-etch", scale: 1, title: "원자층 식각 (ALE)", desc: "플라즈마 반응성 이온의 화학 흡착 및 원자층 단위 저에너지 탈착 정밀 제어" },
        { id: "cryogenic-etch", scale: 1, title: "극저온 식각 (Cryogenic Etch)", desc: "-60℃ 표면 분자 응축 패시베이션을 통한 수직 채널 홀 식각 물리" },
        { id: "gaa-nanosheet-etch", scale: 2, title: "2nm GAA 나노시트 선택 식각", desc: "Si 대 SiGe 격자 간 원자층 선택비 150:1 에칭 기반 채널 릴리즈 구조 형성" },
        { id: "dram-airgap-bitline", scale: 2, title: "DRAM 에어갭 비트라인 (Air-Gap)", desc: "희생 절연막 등방성 식각을 통해 진공 유전율(k=1.0) 에어갭 캐비티 형성" }
      ]
    },
    "wafer-fabrication": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "300mm 웨이퍼 기판 가공",
      parents: [
        { id: "silicon-ingot", scale: 3, title: "단결정 실리콘 잉곳 성장 (CZ)", desc: "단결정 잉곳 성장 및 와이어 쏘잉 슬라이싱을 거친 원소재 기판 가공" },
        { id: "ultra-pure-water-upw", scale: 5, title: "초순수 UPW 공급 인프라", desc: "웨이퍼 경면 연마(CMP) 후 표면 금속 불순물 제거 초순수 린스 세정" }
      ],
      children: [
        { id: "thermal-oxidation", scale: 3, title: "열산화막 형성 공정", desc: "경면 연마(CMP)가 완료된 베어 웨이퍼 표면 초기 절연 산화막(SiO2) 형성" },
        { id: "photolithography", scale: 3, title: "포토리소그래피 노광 공정", desc: "웨이퍼 기판 위 1차 정렬 키(Alignment Key) 및 회로 패턴 전사" }
      ]
    },
    "silicon-ingot": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 잉곳 성장 로(Furnace)",
      parents: [
        { id: "fab-subfab-pfc-scrubber", scale: 5, title: "서브팹 환경 및 고순도 가스 공급망", desc: "초고온 1420℃ 용융 실리콘 도가니 및 초고순도 Ar 아르곤 가스 챔버 분위기" }
      ],
      children: [
        { id: "wafer-fabrication", scale: 3, title: "웨이퍼 제조 단위 공정", desc: "원통형 잉곳 절삭, 에지 라운딩 및 CMP 경면 연마 공정 가공" },
        { id: null, scale: 1, title: "단결정 규소 다이아몬드 격자 물성 (Si <100>/<111>)", desc: "전위 없는 무결함 단결정 원자 배열 및 도펀트(B/P) 균일 확산 물리" }
      ]
    },
    "thermal-oxidation": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 퍼니스 챔버 가공",
      parents: [
        { id: "spc-control-chart", scale: 3, title: "SPC 통계적 공정 관리", desc: "산화로 퍼니스 온도 ±0.5℃ 3-Sigma 관리 한계선 통계 제어" },
        { id: "wafer-fabrication", scale: 3, title: "웨이퍼 제조 단위 공정", desc: "세정 완료된 베어 실리콘 표면에 건식/습식 열산화막 형성" }
      ],
      children: [
        { id: "ald-deposition", scale: 1, title: "원자층 증착 (ALD)", desc: "초박막 계면 산화막 위에 고유전율 나노박막을 형성하는 후속 공정 연계" },
        { id: "tddb-reliability-physics", scale: 1, title: "TDDB 절연 파괴 물리 & 신뢰성", desc: "열산화막 두께 균일도와 계면 결함 밀도에 따른 절연 파괴 수명 통제" }
      ]
    },
    "photolithography": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 노광 샷 패터닝",
      parents: [
        { id: "euv-lithography", scale: 4, title: "EUV 노광 시스템 (ASML NXE)", desc: "13.5nm 파장 EUV 노광 스캐너 광학계 및 샷별 스테이지 레벨링 통제" },
        { id: "high-na-euv", scale: 4, title: "High-NA EUV 노광 장비 (0.55NA)", desc: "차세대 0.55NA 아나모픽 노광 장비를 통한 2nm 이하 패턴 전사" }
      ],
      children: [
        { id: "photo-resist", scale: 1, title: "감광제 (Photoresist)", desc: "노광 광자에 반응하는 PAG 및 고분자 폴리머 광화학 수용 반응" },
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "현상된 포토레지스트 패턴을 마스크 삼아 하부 박막을 선택 식각" },
        { id: "model-based-opc", scale: 2, title: "모델 기반 광학 근접 보정 (MB-OPC)", desc: "광학 회절 왜곡을 역산 보정한 마스크 패턴을 웨이퍼에 전사" }
      ]
    },
    "plasma-discharge": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 챔버 플라즈마 체적",
      parents: [
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "RF 전원 매칭 네트워크 및 ICP 코일 인가 전압 통제" }
      ],
      children: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "공정 가스(CF4, Cl2)의 전자 충돌 이온화 및 웨이퍼 시스 전계 가속" },
        { id: "ale-etch", scale: 1, title: "원자층 식각 (ALE)", desc: "플라즈마 해리 이온의 저에너지 바이어스 충돌 탈착 물리" },
        { id: "fab-fdc-oes-realtime", scale: 3, title: "실시간 OES 분광 FDC 및 EPD", desc: "플라즈마 내부 여기된 라디칼의 고유 파장 광학 방출 스펙트럼 감지" }
      ]
    },
    "cu-damascene-cmp": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm CMP 플래튼 평탄화",
      parents: [
        { id: "run-to-run", scale: 3, title: "Run-to-Run 첨단 공정 제어 (APC)", desc: "CMP 연마 두께 계측 기반 헤드 하중 가압 R2R 피드백 제어" },
        { id: "ultra-pure-water-upw", scale: 5, title: "초순수 UPW 공급 인프라", desc: "연마 후 잔류 슬러리 세정 및 부식 방지 린스수 공급" }
      ],
      children: [
        { id: "cmp-slurry-bta-passivation", scale: 1, title: "CMP 슬러리 & BTA 방식막 화학", desc: "연마 슬러리 내 BTA 방식막 형성 및 디싱/에로전 결함 제어" },
        { id: "hybrid-bonding", scale: 2, title: "차세대 Cu-Cu 하이브리드 본딩", desc: "무범프 다이 접합을 위한 서브 나노미터 초평탄 Cu 표면 가공" },
        { id: "fan-out-wafer-level-packaging", scale: 2, title: "팬아웃 웨이퍼 레벨 패키징 (FOWLP)", desc: "미세 RDL(재배선) 구리 도금층 평탄화 공정 지원" }
      ]
    },
    "fab-fdc-oes-realtime": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 플라즈마 분광 센싱",
      parents: [
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "식각 챔버 뷰포트 장착 2,048채널 광학 분광계 및 고속 통신 버스" },
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "챔버 내부 공정 가스 방전 중 플라즈마 화학종 발광 상태 계측" }
      ],
      children: [
        { id: "dry-etch", scale: 3, title: "식각 종말점(EPD) 판정 집행", desc: "반응 부산물 파장 급변 감지 시 RF 전원 즉시 차단 및 과식각 방지" },
        { id: "bbp-defect-inspection", scale: 2, title: "광대역 플라즈마 결함 검사 (BBP)", desc: "챔버 드리프트 결함과 웨이퍼 인라인 결함 간 상관 분석 연계" }
      ]
    },
    "spc-control-chart": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 웨이퍼 로트 통계",
      parents: [
        { id: "ees-rms", scale: 4, title: "설비 엔지니어링 & RMS 통신", desc: "팹 MES와 연동된 Western Electric 8대 룰 위반 시 자동 장비 인터락(Interlock)" }
      ],
      children: [
        { id: "yield-negative-binomial-modeling", scale: 1, title: "음이항 결함 뭉침 수율 모델", desc: "3-Sigma 관리 한계선과 웨이퍼 다이 결함 밀도 상관성 통계 분석" },
        { id: "hbm-kgd-testing", scale: 2, title: "HBM 웨이퍼 KGD 양품 테스트", desc: "웨이퍼 프로빙 수율 관리도 및 불량 클러스터링 통계 통제" }
      ]
    },
    "run-to-run": {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 런간 파라미터 보정보간",
      parents: [
        { id: "ees-rms", scale: 4, title: "설비 엔지니어링 & RMS 통신", desc: "APC 피드백 엔진이 계산한 오프셋을 장비 RMS 레시피로 실시간 주입" }
      ],
      children: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "직전 웨이퍼 식각 깊이 계측값 기반 챔버 RF 파워 및 시간 자동 보정" },
        { id: "cu-damascene-cmp", scale: 3, title: "구리 다마신 배선 평탄화 (Cu CMP)", desc: "연마 패드 마모도에 따른 가압 헤드 영역별 압력 자동 보정" }
      ]
    },

    // ── Scale 2: 소자 구조 & 칩 패키지 (10nm ~ 수 mm) ──
    "gaa-nanosheet-etch": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "10nm ~ 수십 nm 3D 나노시트 채널",
      parents: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "ICP 식각 챔버 내 기상 에칭 가스 분사 및 런간 제어 공정" },
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "나노시트 박리 시 미세 아킹 손상 방지 플라즈마 모니터링" }
      ],
      children: [
        { id: "ale-etch", scale: 1, title: "원자층 식각 (ALE)", desc: "SiGe 층만 선택적으로 깎아내는 원자 수준 150:1 선택비 식각 물리" },
        { id: "hkmg-transistor", scale: 1, title: "HKMG 트랜지스터 게이트 스택", desc: "나노시트 4면을 감싸는 High-k 절연막 및 금속 게이트 전계 형성" }
      ]
    },
    "model-based-opc": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "10nm ~ 수백 nm 마스크 역산 패턴",
      parents: [
        { id: "high-na-euv", scale: 4, title: "High-NA EUV 노광 장비 (0.55NA)", desc: "EUV 스캐너 광학계 회절 수치 및 조명계 조건 입력" },
        { id: "euv-lithography", scale: 4, title: "EUV 노광 시스템 (ASML NXE)", desc: "0.33NA 노광 광학계 광학 근접 효과 시뮬레이션 모델링" }
      ],
      children: [
        { id: "photolithography", scale: 3, title: "포토리소그래피 노광 공정", desc: "웨이퍼 상 2nm 로직 핀치/브릿지 결함 방지 회로 마스크 패턴 전사" },
        { id: "photo-resist", scale: 1, title: "감광제 (Photoresist)", desc: "빛의 회절과 화학 증폭형 레지스트 블러(Blur) 수치 역보정" }
      ]
    },
    "dram-zaz-capacitor": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "10nm ~ 100nm 필러 커패시터",
      parents: [
        { id: "ald-deposition", scale: 1, title: "원자층 증착 (ALD)", desc: "ZrO2-Al2O3-ZrO2 다층 유전막 교번 원자층 증착 레시피" }
      ],
      children: [
        { id: "tddb-reliability-physics", scale: 1, title: "TDDB 절연 파괴 물리 & 신뢰성", desc: "고종횡비 필러 커패시터 산화막 결함 전도 및 TDDB 절연 파괴 물리" },
        { id: null, scale: 1, title: "ZrO2 정방정계(Tetragonal) 결정상 유전율 극대화", desc: "Al2O3 도핑 삽입을 통해 고유전율 유전체 결정 상변이를 안정화시키는 원자 물성" }
      ]
    },
    "dram-airgap-bitline": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "10nm ~ 수십 nm 에어갭 캐비티",
      parents: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "비트라인 스페이서 희생막 선택 식각 및 캐비티 형성 단위 공정" }
      ],
      children: [
        { id: null, scale: 1, title: "진공 유전율 (k=1.0) 기반 기생 커패시턴스 억제", desc: "인접 비트라인 간 신호 간섭 및 RC 신호 지연을 극한으로 낮추는 정전기학 원리" }
      ]
    },
    "3d-nand-ctf-architecture": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "수십 nm ~ 수 µm 수직 셀 스트링",
      parents: [
        { id: "cryogenic-etch", scale: 1, title: "극저온 식각 (Cryogenic Etch)", desc: "수백 단 적층 채널 홀을 수직 관통하는 극저온 식각 챔버 가공" },
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "초고종횡비(HARC) 계단식 슬릿 및 워드라인 분리 식각" }
      ],
      children: [
        { id: "3d-nand-mo-wordline", scale: 1, title: "3D NAND Mo 워드라인 금속화", desc: "SiN 질화막 전하 트랩 및 초저저항 몰리브덴(Mo) 배선 전도도" },
        { id: "4d-nand-puc", scale: 2, title: "4D NAND 주변부 회로 하부 적층 (PUC)", desc: "주변 회로(Peri)를 셀 어레이 하부에 배치하는 집적도 극대화 아키텍처" }
      ]
    },
    "4d-nand-puc": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패턴",
      badgeClass: "badge-scale-2",
      scopeName: "수 µm ~ 수 mm 칩 다이 면적 효율",
      parents: [
        { id: "3d-nand-ctf-architecture", scale: 2, title: "3D NAND 전하 트랩 (CTF) 셀 구조", desc: "주변 회로를 셀 하부에 매립하여 다이 크기를 줄이는 셀 아키텍처" }
      ],
      children: [
        { id: null, scale: 1, title: "하부 Peri 회로의 고온 어닐링 열 스트레스 저항성", desc: "상부 메모리 셀 적층 공정의 고온 열처리에도 하부 로직 배선이 열화되지 않는 재료 물성" }
      ]
    },
    "fan-out-wafer-level-packaging": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "수 mm ~ 수 cm 팬아웃 재배선 패키지",
      parents: [
        { id: "cu-damascene-cmp", scale: 3, title: "구리 다마신 배선 평탄화 (Cu CMP)", desc: "기판 없는 칩 패키징의 미세 RDL 구리 배선 도금 및 평탄화" }
      ],
      children: [
        { id: null, scale: 1, title: "실리콘-EMC 간 열팽창계수(CTE) 불일치 응력 물리", desc: "다이와 몰딩 수지 간의 CTE 차이로 인한 휨(Warpage) 현상을 억제하는 고분자 계면 물성" }
      ]
    },
    "mr-muf": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "수 mm ~ 수 cm HBM 적층 큐브",
      parents: [
        { id: "ees-rms", scale: 4, title: "설비 엔지니어링 & RMS 통신", desc: "HBM3E/HBM4 진공 가압 오토클레이브 챔버 및 SECS-GEM 레시피 통제" },
        { id: "hbm-kgd-testing", scale: 2, title: "HBM 웨이퍼 KGD 양품 테스트", desc: "1,024개 TSV 마이크로 범프 프로빙 검증 통과 다이만 선별 적층" }
      ],
      children: [
        { id: "cmp-slurry-bta-passivation", scale: 1, title: "CMP 슬러리 & BTA 방식막 화학", desc: "고밀도 실리카 필러 함유 액상 EMC 점도 및 15µm 미세 범프 갭 젖음성" },
        { id: "tddb-reliability-physics", scale: 1, title: "TDDB 절연 파괴 물리 & 신뢰성", desc: "적층 다이 간 마이크로 범프 고온 동작 번인 및 단락 신뢰성 보증" }
      ]
    },
    "hybrid-bonding": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "서브 µm 마이크로 피치 접합면",
      parents: [
        { id: "plasma-fdc-sensor", scale: 4, title: "플라즈마 RF 아킹 센서 (VI-Probe)", desc: "상온 직접 결합 전 SiCN/Cu 표면 플라즈마 활성화 챔버 파라미터 제어" },
        { id: "cu-damascene-cmp", scale: 3, title: "구리 다마신 배선 평탄화 (Cu CMP)", desc: "무범프 다이 접합을 위한 서브 나노미터 초평탄 Cu 표면 가공" }
      ],
      children: [
        { id: "ald-deposition", scale: 1, title: "원자층 증착 (ALD)", desc: "범프 없는 무가압 Cu-Cu 직접 원자간 고체 확산 접합 메커니즘" },
        { id: null, scale: 1, title: "Cu-Cu 원자간 열팽창 결합 확산 (Grain Growth)", desc: "200℃ 저온 어닐링 시 계면 구리 원자가 확산 이동하여 결정립 결합 형성" }
      ]
    },
    "cowos-interposer-cuf": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "수 cm 실리콘 인터포저 기판",
      parents: [
        { id: "hbm-kgd-testing", scale: 2, title: "HBM 웨이퍼 KGD 양품 테스트", desc: "로직 다이와 HBM 스택을 결합하기 전 2.5D 인터포저 수율 보증" },
        { id: "mr-muf", scale: 2, title: "HBM MR-MUF 액상 몰딩 패키징", desc: "인터포저 위에 HBM 큐브 실장 및 2.5D 시스템 패키지 패키징" }
      ],
      children: [
        { id: null, scale: 1, title: "TSV 전극 미세 피치 간 모세관 언더필 충진 유동학", desc: "수십 마이크론 미세 갭 사이에 기포 없이 언더필 수지를 완전 충진하는 계면 물리" }
      ]
    },
    "hbm-kgd-testing": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "300mm 웨이퍼 전면 다이 테스트",
      parents: [
        { id: "spc-control-chart", scale: 3, title: "SPC 통계적 공정 관리", desc: "고속 ATE 테스터 1,024개 I/O 접촉 저항 및 불량률 SPC 관리도" }
      ],
      children: [
        { id: "mr-muf", scale: 2, title: "HBM MR-MUF 액상 몰딩 패키징", desc: "KGD 검증을 통과한 양품 베어 다이만을 HBM 16단 적층 공정에 투입" },
        { id: "cowos-interposer-cuf", scale: 2, title: "TSV 실리콘 인터포저 & CoWoS", desc: "최종 HBM 스택 모듈의 기판 실장 전 KGD 수율 보증" },
        { id: "tddb-reliability-physics", scale: 1, title: "TDDB 절연 파괴 물리 & 신뢰성", desc: "적층 다이 TSV 마이크로 범프 고온 동작 번인(Burn-in) 및 신뢰성 한계" }
      ]
    },
    "bbp-defect-inspection": {
      scale: 2,
      scaleLabel: "Scale 2 · 소자 & 칩 패키지",
      badgeClass: "badge-scale-2",
      scopeName: "300mm 웨이퍼 다이 인라인 검사",
      parents: [
        { id: "fab-fdc-oes-realtime", scale: 3, title: "실시간 OES 분광 FDC 및 EPD", desc: "광학 챔버 레이저 발진 상태 및 팹 인라인 검사 장비 FDC 모니터링" }
      ],
      children: [
        { id: null, scale: 1, title: "초단파장 DUV 레이저 암시야 회절 산란 광학", desc: "1x nm 킬러 결함에서 산란되는 미약한 광학 신호를 검출하는 전자기파 산란 물리" }
      ]
    },

    // ── Scale 1: 원자·분자 & 계면 물성 (0.1nm ~ 1nm) ──
    "ald-deposition": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 단원자층 제어",
      parents: [
        { id: "dram-zaz-capacitor", scale: 2, title: "DRAM 고유전율 ZAZ 커패시터", desc: "초박막 유전체 적층을 통한 고용량 커패시터 소자 구현 단위" },
        { id: "3d-nand-mo-wordline", scale: 1, title: "3D NAND Mo 워드라인 금속화", desc: "수백 단 수직 채널 홀 내 균일한 몰리브덴 ALD 증착 레시피" },
        { id: "hkmg-transistor", scale: 1, title: "HKMG 트랜지스터 게이트 스택", desc: "서브 1nm HfO2 게이트 산화막 원자층 정밀 증착" }
      ],
      children: [
        { id: null, scale: 1, title: "자기제한 표면 화학흡착 (Self-Limiting Chemisorption)", desc: "전구체 분자가 표면 작용기와 1:1로 포화 결합 후 추가 반응이 정지되는 분자 역학" }
      ]
    },
    "ale-etch": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 0.5nm 단원자층 식각",
      parents: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "플라즈마 장비 내 반응 가스(Cl2)와 Ar 이온의 교번 펄스 제어" },
        { id: "gaa-nanosheet-etch", scale: 2, title: "2nm GAA 나노시트 선택 식각", desc: "2nm GAA 나노시트 Si/SiGe 무손상 채널 릴리즈 구조 가공" }
      ],
      children: [
        { id: null, scale: 1, title: "염소(Cl2) 화학 흡착 및 저에너지 Ar+ 탈착 원자 거동", desc: "하부 격자 손상(Defect) 없이 단원자층 결합 에너지만큼의 충돌 에너지 전달 물리" }
      ]
    },
    "cryogenic-etch": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 분자 응축 계면",
      parents: [
        { id: "dry-etch", scale: 3, title: "플라즈마 건식 식각 (RIE)", desc: "식각 챔버 정전척(ESC) 온도를 -60℃로 제어하는 챔버 레시피" },
        { id: "3d-nand-ctf-architecture", scale: 2, title: "3D NAND 전하 트랩 (CTF) 셀 구조", desc: "400단+ 3D NAND 초고종횡비(HAR) 채널 홀 관통 식각 소자 가공" }
      ],
      children: [
        { id: null, scale: 1, title: "-60℃ 극저온 표면 분자 응축 패시베이션 물리", desc: "측벽 반응 억제를 위해 화학종을 극저온으로 물리 응축시켜 수직 직진성을 유지하는 계면 물리" }
      ]
    },
    "hkmg-transistor": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 게이트 옥사이드 계면",
      parents: [
        { id: "gaa-nanosheet-etch", scale: 2, title: "2nm GAA 나노시트 선택 식각", desc: "서브 2nm 첨단 로직 트랜지스터 3D 채널 전계 효과 소자" },
        { id: "ald-deposition", scale: 1, title: "원자층 증착 (ALD)", desc: "HfO2 고유전체 나노박막 및 TiN 금속 게이트 ALD 원자층 적층" }
      ],
      children: [
        { id: null, scale: 1, title: "양자역학 터널링 차단 및 게이트 금속 일함수 밴드갭", desc: "HfO2 고유전율 격자 엔지니어링을 통해 1nm 미만 등가산화막(EOT) 두께 실현" }
      ]
    },
    "3d-nand-mo-wordline": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 금속 원자 결정립계",
      parents: [
        { id: "3d-nand-ctf-architecture", scale: 2, title: "3D NAND 전하 트랩 (CTF) 셀 구조", desc: "300단 이상 3D 낸드의 워드라인 저항 급증을 해결하는 게이트 금속 대체" },
        { id: "ald-deposition", scale: 1, title: "원자층 증착 (ALD)", desc: "무불소 전구체 Mo ALD 증착 박막 형성" }
      ],
      children: [
        { id: null, scale: 1, title: "무불소 몰리브덴(Mo) 박막의 낮은 전자 산란 전도 물리", desc: "텅스텐 대비 결정립계 전자 산란(Electron Scattering)이 적어 나노 스케일에서 비저항 급감" }
      ]
    },
    "photo-resist": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 고분자 사슬 & 광자 반응",
      parents: [
        { id: "photolithography", scale: 3, title: "포토리소그래피 노광 공정", desc: "웨이퍼 스핀 코팅 및 회로 패턴 전사 단위 공정" },
        { id: "euv-lithography", scale: 4, title: "EUV 노광 시스템 (ASML NXE)", desc: "13.5nm 극자외선 노광 광자 흡수 및 산발생 반응" }
      ],
      children: [
        { id: null, scale: 1, title: "극자외선 광자 흡수 및 산발생제(PAG) 연쇄 탈보호 화학 반응", desc: "EUV 광자 흡수 시 생성된 2차 전자가 고분자 결합을 끊어내는 용해도 전이 화학" }
      ]
    },
    "cmp-slurry-bta-passivation": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 분자 흡착 방식막",
      parents: [
        { id: "cu-damascene-cmp", scale: 3, title: "구리 다마신 배선 평탄화 (Cu CMP)", desc: "구리 다마신 화학기계적 연마(CMP) 공정 조건 및 헤드 압력 제어" },
        { id: "mr-muf", scale: 2, title: "HBM MR-MUF 액상 몰딩 패키징", desc: "HBM3E 액상 몰딩 수지의 고밀도 무기 필러 표면 계면 제어" }
      ],
      children: [
        { id: null, scale: 1, title: "Cu-BTA 배위 결합 단분자 보호 피막 계면 화학", desc: "벤조트리아졸 분자가 구리 원자와 킬레이트 착물을 형성하여 화학적 에칭을 물리 차단" }
      ]
    },
    "tddb-reliability-physics": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 절연막 결함 필라멘트",
      parents: [
        { id: "dram-zaz-capacitor", scale: 2, title: "DRAM 고유전율 ZAZ 커패시터", desc: "1b/1c nm DRAM 초박막 커패시터의 장기 절연 신뢰성 수명 판정" },
        { id: "hbm-kgd-testing", scale: 2, title: "HBM 웨이퍼 KGD 양품 테스트", desc: "적층 다이 간 마이크로 범프 고전계 동작 신뢰성 검증" }
      ],
      children: [
        { id: null, scale: 1, title: "산소 공공(Vo) 트랩 생성 및 퍼콜레이션 전도 경로 파괴", desc: "전기적 스트레스 하에서 유전체 격자 결함이 선형 연결되어 항복 전류가 급증하는 물리" }
      ]
    },
    "yield-negative-binomial-modeling": {
      scale: 1,
      scaleLabel: "Scale 1 · 원자 & 계면 물성",
      badgeClass: "badge-scale-1",
      scopeName: "0.1nm ~ 1nm 결함 군집 통계 수식",
      parents: [
        { id: "spc-control-chart", scale: 3, title: "SPC 통계적 공정 관리", desc: "팹 인라인 검사 파티클 밀도 및 결함 뭉침 인자(Alpha) 통계 피팅" }
      ],
      children: [
        { id: null, scale: 1, title: "Murphy & Seeds 음이항 결함 클러스터링 감마 분포 수식", desc: "포아송 통계의 결함 무작위 분포 가정을 극복하고 실제 팹 결함 뭉침을 설명하는 수학 모델" }
      ]
    }
  };

  function renderFabStageStrip() {
    if (!dom.fabStageStrip || !dom.stageStripFlow) return;

    const c = WikiStore.concepts[state.currentConceptId];
    const activeFacet = state.currentFacet || c?.facetId || "facet-process";
    const pipeline = fabPipelines[activeFacet] || fabPipelines["facet-process"];

    if (dom.stageStripCategoryBadge) {
      dom.stageStripCategoryBadge.textContent = pipeline.categoryName;
    }

    const flowHtml = pipeline.steps.map((step, idx) => {
      const isActive = (step.conceptId === state.currentConceptId) || (step.matchConcepts && step.matchConcepts.includes(state.currentConceptId));
      const arrow = (idx < pipeline.steps.length - 1) ? `<span class="stage-step-arrow">➔</span>` : "";
      return `
        <span class="stage-step-pill ${isActive ? 'active' : ''}" data-concept-id="${step.conceptId}" title="${step.label} 온톨로지 개념 바로보기">
          ${step.label}
        </span>
        ${arrow}
      `;
    }).join("");

    dom.stageStripFlow.innerHTML = flowHtml;

    dom.stageStripFlow.querySelectorAll(".stage-step-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const cid = pill.dataset.conceptId;
        window.selectWikiConcept(cid);
      });
    });
  }

  // 닫기 및 다시 열기 버튼 이벤트
  dom.stageStripCloseBtn?.addEventListener("click", () => {
    if (dom.fabStageStrip) dom.fabStageStrip.style.display = "none";
    if (dom.stageStripReopenBar) dom.stageStripReopenBar.style.display = "block";
    showToast("팹 라이프사이클 파이프라인 바가 접혔습니다.", "info");
  });

  dom.stageStripReopenBtn?.addEventListener("click", () => {
    if (dom.fabStageStrip) dom.fabStageStrip.style.display = "block";
    if (dom.stageStripReopenBar) dom.stageStripReopenBar.style.display = "none";
    renderFabStageStrip();
  });

  // ── 2. 도메인 패싯 (공정 / 운영 / 장비 / 소재) ──
  function renderDomainFacets() {
    dom.domainFacetTabs.innerHTML = WikiStore.domainFacets.map(f => `
      <button type="button" class="facet-chip ${f.id === state.currentFacet ? 'active' : ''}" data-facet="${f.id}">
        <span>${f.name}</span>
        <span style="font-size:0.6875rem; opacity:0.7;">➔</span>
      </button>
    `).join("");

    dom.domainFacetTabs.querySelectorAll(".facet-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        state.currentFacet = btn.dataset.facet;
        renderDomainFacets();
        renderSidebarNav();
        renderFabStageStrip();
        
        // 해당 패싯의 첫 번째 대표 개념으로 자동 열람
        const pipeline = fabPipelines[state.currentFacet];
        if (pipeline && pipeline.steps.length > 0) {
          window.selectWikiConcept(pipeline.steps[0].conceptId);
        }
      });
    });
  }

  // 패싯별 서브 트리 렌더링
  function renderSidebarNav() {
    dom.sidebarProcesses.innerHTML = "";

    let treeData = [];
    if (state.currentFacet === "facet-device") {
      dom.facetSubnavTitle.textContent = "소자·제품군 온톨로지 체계 (HBM/NAND/GAA)";
      treeData = WikiStore.deviceTree || [];
    } else if (state.currentFacet === "facet-process") {
      dom.facetSubnavTitle.textContent = "제조 단위 공정 체계 (Unit Processes)";
      treeData = WikiStore.processes;
    } else if (state.currentFacet === "facet-operations") {
      dom.facetSubnavTitle.textContent = "팹 지능화 & 운영 관리 체계 (Operations)";
      treeData = WikiStore.operationsTree;
    } else {
      dom.facetSubnavTitle.textContent = "소재·화학 & 팹 인프라 체계 (Materials & Infra)";
      treeData = WikiStore.materialsTree;
    }

    treeData.forEach(node => {
      const isCurrent = (node.id === WikiStore.concepts[state.currentConceptId]?.processId) ||
                        (node.concepts && node.concepts.includes(state.currentConceptId));
      const item = document.createElement("div");
      item.className = "process-nav-group";
      item.innerHTML = `
        <div class="process-nav-item ${isCurrent ? 'active' : ''}" data-proc-id="${node.id}">
          <span>${node.name}</span>
          ${node.concepts ? `
            <svg class="accordion-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          ` : ""}
        </div>
        ${node.concepts ? `
          <div class="process-concept-sublist" style="display: ${isCurrent ? 'flex' : 'none'};">
            ${node.concepts.map(cid => {
              const concept = WikiStore.concepts[cid];
              const title = concept ? concept.title.split("(")[0].trim() : cid;
              return `<div class="concept-sub-link ${cid === state.currentConceptId ? 'active' : ''}" data-concept-id="${cid}">• ${title}</div>`;
            }).join("")}
          </div>
        ` : ""}
      `;
      dom.sidebarProcesses.appendChild(item);
    });

    dom.sidebarProcesses.querySelectorAll(".process-nav-item").forEach(el => {
      el.addEventListener("click", () => {
        const sublist = el.nextElementSibling;
        if (sublist && sublist.classList.contains("process-concept-sublist")) {
          sublist.style.display = (sublist.style.display === "flex") ? "none" : "flex";
        }
      });
    });

    dom.sidebarProcesses.querySelectorAll(".concept-sub-link").forEach(el => {
      el.addEventListener("click", () => {
        const cid = el.dataset.conceptId;
        window.selectWikiConcept(cid);
      });
    });
  }

  // ── 물리적 규모(Scale) 위계 사이드바 트리 렌더링 (1안) ──
  function renderSidebarScaleTree() {
    if (!dom.sidebarScaleTree) return;
    dom.sidebarScaleTree.innerHTML = "";

    // Scale 5 (팹 인프라)부터 Scale 1 (원자 물성)까지 거시 ➔ 미시 내림차순 정렬
    const sortedScales = [...scaleDefinitions].sort((a, b) => b.scale - a.scale);
    const currConceptScale = conceptScales[state.currentConceptId]?.scale || 3;

    sortedScales.forEach(s => {
      // 해당 스케일에 속하는 37개 개념 추출
      const matchedConceptIds = Object.keys(conceptScales).filter(id => conceptScales[id].scale === s.scale);
      const isCurrentGroup = (s.scale === currConceptScale);

      const groupEl = document.createElement("div");
      groupEl.className = "scale-nav-group";
      groupEl.dataset.scale = s.scale;
      groupEl.innerHTML = `
        <div class="process-nav-item scale-nav-header ${isCurrentGroup ? 'active open' : ''}" data-scale="${s.scale}">
          <div style="display:flex; align-items:center; gap:6px; overflow:hidden;">
            <span style="font-size:0.9375rem; flex-shrink:0;">${s.icon}</span>
            <span style="font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              Scale ${s.scale} · ${s.name.split(':')[1]?.trim() || s.name}
            </span>
          </div>
          <div style="display:flex; align-items:center; gap:4px; flex-shrink:0;">
            <span class="scale-count-badge">${matchedConceptIds.length}</span>
            <span class="scale-nav-chevron">▼</span>
          </div>
        </div>
        <div class="scale-sublist-wrapper ${isCurrentGroup ? 'open' : ''}">
          <div class="scale-sublist-inner">
            <div class="scale-concept-sublist">
              ${matchedConceptIds.map(cid => {
                const c = WikiStore.concepts[cid];
                const title = c ? c.title.split('(')[0].trim() : cid;
                const isActive = (cid === state.currentConceptId);
                return `
                  <div class="concept-sub-link ${isActive ? 'active' : ''}" data-concept-id="${cid}" title="${c?.title || cid}">
                    <span>• ${title}</span>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        </div>
      `;
      dom.sidebarScaleTree.appendChild(groupEl);
    });

    // 스케일 아코디언 헤더 토글 이벤트 (Transitions.dev CSS Grid Rows 애니메이션)
    dom.sidebarScaleTree.querySelectorAll(".scale-nav-header").forEach(header => {
      header.addEventListener("click", () => {
        const wrapper = header.nextElementSibling;
        if (wrapper) {
          const isOpen = wrapper.classList.toggle("open");
          header.classList.toggle("open", isOpen);
        }
      });
    });

    // 개별 개념 링크 클릭 이벤트
    dom.sidebarScaleTree.querySelectorAll(".concept-sub-link").forEach(link => {
      link.addEventListener("click", () => {
        const cid = link.dataset.conceptId;
        window.selectWikiConcept(cid);
      });
    });
  }

  // ── 사이드바 내비게이션 모드 전환 헬퍼 ──
  function setSidebarNavMode(mode) {
    state.sidebarNavMode = mode;
    dom.sidebarModeBtns.forEach(btn => {
      const isActive = (btn.dataset.mode === mode);
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    if (mode === "scale") {
      if (dom.sidebarDomainContainer) dom.sidebarDomainContainer.style.display = "none";
      if (dom.sidebarScaleContainer) dom.sidebarScaleContainer.style.display = "block";
      renderSidebarScaleTree();
      showToast("📐 [물리 규모별 탐색] 팹 인프라(1km)부터 원자(0.1nm)까지 5단계 크기순으로 탐색합니다.", "info");
    } else {
      if (dom.sidebarDomainContainer) dom.sidebarDomainContainer.style.display = "block";
      if (dom.sidebarScaleContainer) dom.sidebarScaleContainer.style.display = "none";
      renderDomainFacets();
      renderSidebarNav();
      showToast("🏛️ [업무 분야별 탐색] 소자, 공정, 운영, 소재 4대 반도체 도메인별로 탐색합니다.", "info");
    }
  }

  // ── 패싯-개념 포함 여부 판별 헬퍼 ──
  function doesFacetContainConcept(facetId, conceptId) {
    if (facetId === "facet-device") {
      return (WikiStore.deviceTree || []).some(g => g.concepts && g.concepts.includes(conceptId));
    } else if (facetId === "facet-process") {
      return (WikiStore.processes || []).some(g => g.concepts && g.concepts.includes(conceptId));
    } else if (facetId === "facet-operations") {
      return (WikiStore.operationsTree || []).some(g => g.concepts && g.concepts.includes(conceptId));
    } else if (facetId === "facet-materials") {
      return (WikiStore.materialsTree || []).some(g => g.concepts && g.concepts.includes(conceptId));
    }
    return false;
  }

  function findFacetForConcept(conceptId) {
    if ((WikiStore.deviceTree || []).some(g => g.concepts && g.concepts.includes(conceptId))) return "facet-device";
    if ((WikiStore.operationsTree || []).some(g => g.concepts && g.concepts.includes(conceptId))) return "facet-operations";
    if ((WikiStore.materialsTree || []).some(g => g.concepts && g.concepts.includes(conceptId))) return "facet-materials";
    if ((WikiStore.processes || []).some(g => g.concepts && g.concepts.includes(conceptId))) return "facet-process";
    return "facet-process";
  }

  // ── 지식 열람 심도(Reading Depth: L1 / L2 / L3) 관리 ──
  function applyCurrentReadingDepth() {
    const canvas = document.querySelector(".main-canvas");
    const mode = state.readingDepth || "all";
    
    // 버튼 active 상태 동기화
    [dom.btnDepthAll, dom.btnDepthSummary, dom.btnDepthMech].forEach(btn => {
      if (btn) btn.classList.toggle("active", btn.dataset.depth === mode);
    });

    if (mode === "summary") {
      if (canvas) {
        canvas.classList.add("depth-mode-summary");
        canvas.classList.remove("depth-mode-mech");
      }
      dom.principlesAccordionItem?.classList.remove("open");
    } else if (mode === "mech") {
      if (canvas) {
        canvas.classList.add("depth-mode-mech");
        canvas.classList.remove("depth-mode-summary");
      }
      dom.principlesAccordionItem?.classList.add("open");
    } else {
      if (canvas) {
        canvas.classList.remove("depth-mode-summary", "depth-mode-mech");
      }
      dom.principlesAccordionItem?.classList.add("open");
    }
  }

  function setReadingDepth(mode) {
    state.readingDepth = mode;
    applyCurrentReadingDepth();

    if (mode === "summary") {
      showToast("🌱 [Level 1 입문 요약 뷰] 초심자를 위한 용어 표준 정의 및 목적 중심으로 요약되었습니다.", "info");
    } else if (mode === "mech") {
      document.getElementById("sec-principles")?.scrollIntoView({ behavior: "smooth", block: "start" });
      showToast("📘 [Level 2 공학 메커니즘 뷰] 물리·화학적 원리 수식과 공정 결함 한계점이 전개되었습니다.", "info");
    } else {
      showToast("🔬 [Level 1~3 전체 심층 뷰] 공통 기초부터 공학 메커니즘, 사내 실무 레시피까지 전수 열람합니다.", "info");
    }
  }

  // ── 전역 개념 선택 헬퍼 ──
  window.selectWikiConcept = function(conceptId) {
    if (WikiStore.concepts[conceptId]) {
      state.currentConceptId = conceptId;
      const c = WikiStore.concepts[conceptId];
      
      // 현재 열람 중인 패싯에 해당 개념이 이미 속해 있다면, 굳이 다른 패싯으로 튕기지 않고 현재 패싯 유지!
      // (예: 소자·제품군 허브에서 HBM MR-MUF를 선택했을 때 '제조 단위 공정'으로 강제 전환되는 현상 원천 해결)
      if (!doesFacetContainConcept(state.currentFacet, conceptId)) {
        state.currentFacet = c.facetId || findFacetForConcept(conceptId);
      }

      renderDomainFacets();
      renderSidebarNav();
      renderSidebarScaleTree();
      renderFabStageStrip();
      renderConceptDetail(conceptId);
      setWorkspace("wiki");
      window.dispatchEvent(new CustomEvent("conceptChanged"));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      showToast(`'${conceptId}' 문서는 조사 작업실에서 후보 발굴 대기 중입니다.`, "info");
    }
  };

  // ── 2-B. 온톨로지 개념 인텍스트 자동 하이퍼링크 헬퍼 ──
  function enrichTextWithConceptLinks(rawText, currentConceptId) {
    if (!rawText) return "";
    const allConcepts = Object.values(WikiStore.concepts || {});
    
    // 1. 키워드 목록 수집 (단어 길이 긴 순서)
    const keywords = [];
    allConcepts.forEach(c => {
      if (c.id === currentConceptId) return;
      const mainTitle = c.title ? c.title.split("(")[0].trim() : "";
      if (mainTitle && mainTitle.length >= 2) keywords.push({ term: mainTitle, id: c.id });
      if (c.aliases) {
        c.aliases.forEach(a => {
          if (a && a.length >= 2) keywords.push({ term: a.trim(), id: c.id });
        });
      }
    });

    // 중복 키워드 제거
    const uniqueKeywords = [];
    const seen = new Set();
    keywords.sort((a, b) => b.term.length - a.term.length).forEach(item => {
      const lower = item.term.toLowerCase();
      if (item.term.length < 2) return;
      if (!seen.has(lower)) {
        seen.add(lower);
        uniqueKeywords.push(item);
      }
    });

    // 2. 비중복 매칭 위치 탐색 (Non-overlapping ranges)
    const matches = [];
    const textLower = rawText.toLowerCase();

    uniqueKeywords.forEach(kw => {
      const termLower = kw.term.toLowerCase();
      const isAscii = /^[A-Za-z0-9\-]+$/.test(kw.term);
      
      let startIndex = 0;
      while ((startIndex = textLower.indexOf(termLower, startIndex)) !== -1) {
        const endIndex = startIndex + termLower.length;
        
        // 영문 약어의 경우 단어 경계(앞뒤에 알파벳/숫자가 없어야 함) 확인
        let validBoundary = true;
        if (isAscii) {
          const prevChar = startIndex > 0 ? rawText[startIndex - 1] : ' ';
          const nextChar = endIndex < rawText.length ? rawText[endIndex] : ' ';
          if (/[A-Za-z0-9]/.test(prevChar) || /[A-Za-z0-9]/.test(nextChar)) {
            validBoundary = false;
          }
        }

        if (validBoundary) {
          // 기존 매치와 겹치는지 검사
          const overlaps = matches.some(m => 
            (startIndex >= m.start && startIndex < m.end) || 
            (endIndex > m.start && endIndex <= m.end) ||
            (startIndex <= m.start && endIndex >= m.end)
          );

          if (!overlaps) {
            matches.push({
              start: startIndex,
              end: endIndex,
              original: rawText.substring(startIndex, endIndex),
              id: kw.id,
              term: kw.term
            });
            break; // 동일 키워드는 문단당 최초 1회만 하이퍼링크 부여
          }
        }
        startIndex += 1;
      }
    });

    if (matches.length === 0) return rawText;

    // 3. 인덱스 오름차순 정렬 후 문자열 치환 조립
    matches.sort((a, b) => a.start - b.start);
    let result = "";
    let lastIdx = 0;
    for (const m of matches) {
      result += rawText.substring(lastIdx, m.start);
      result += `<span class="concept-intext-link" data-concept-id="${m.id}" title="${m.term} 온톨로지 문서로 바로가기">${m.original}</span>`;
      lastIdx = m.end;
    }
    result += rawText.substring(lastIdx);

    return result;
  }

  // ── 3. 위키 개념 본문 렌더링 ──
  function renderConceptDetail(conceptId) {
    const c = WikiStore.concepts[conceptId];
    if (!c) return;

    let facetLabel = "제조 단위 공정";
    if (state.currentFacet === "facet-device") facetLabel = "소자·제품군 (Devices)";
    else if (state.currentFacet === "facet-operations") facetLabel = "팹 지능화 & 운영 (Operations)";
    else if (state.currentFacet === "facet-materials") facetLabel = "소재·화학 & 팹 인프라 (Materials & Infra)";

    let groupName = c.processName || "단위 공정";
    if (state.currentFacet === "facet-device") {
      const devNode = (WikiStore.deviceTree || []).find(g => g.concepts && g.concepts.includes(c.id));
      if (devNode) groupName = devNode.name.replace(/^\d+\.\s*/, '');
    } else if (state.currentFacet === "facet-operations") {
      const opNode = (WikiStore.operationsTree || []).find(g => g.concepts && g.concepts.includes(c.id));
      if (opNode) groupName = opNode.name.split('(')[0].trim();
    } else if (state.currentFacet === "facet-materials") {
      const matNode = (WikiStore.materialsTree || []).find(g => g.concepts && g.concepts.includes(c.id));
      if (matNode) groupName = matNode.name;
    }

    document.getElementById("concept-breadcrumb-facet").textContent = facetLabel;
    document.getElementById("concept-breadcrumb-proc").textContent = groupName;
    document.getElementById("concept-breadcrumb-title").textContent = c.title.split("(")[0].trim();
    document.getElementById("concept-title-text").textContent = c.title;
    document.getElementById("concept-aliases-text").textContent = c.aliases ? c.aliases.join(", ") : "-";
    document.getElementById("concept-version-text").textContent = `${c.version} (${c.verificationLevel})`;
    document.getElementById("concept-reviewed-text").textContent = c.lastReviewed;
    document.getElementById("footer-concept-id").textContent = `concept-${c.id}-001`;

    // ── 지식 Level 뱃지 갱신 ──
    const lvlInfo = conceptLevels[c.id] || { level: 1, label: "Level 1 · 산업 공통 기초", badgeClass: "badge-level-1", desc: "비전공자 및 신입을 위한 용어 표준 정의와 필수 기초 개념" };
    if (dom.conceptLevelBadge) {
      dom.conceptLevelBadge.className = `concept-badge ${lvlInfo.badgeClass}`;
      dom.conceptLevelBadge.textContent = lvlInfo.label;
      dom.conceptLevelBadge.title = lvlInfo.desc;
    }

    // ── 지식 Scale 뱃지 갱신 ──
    const scaleInfo = conceptScales[c.id] || {
      scale: 3,
      scaleLabel: "Scale 3 · 단위 공정 & 런",
      badgeClass: "badge-scale-3",
      scopeName: "1cm ~ 300mm 웨이퍼",
      parent: { id: null, title: "상위 설비 및 팹 인프라", desc: "상위 스케일 공정 및 설비 연계" },
      child: { id: null, title: "하위 물리 및 재료 물성", desc: "하위 스케일 원자 및 계면 물리" }
    };
    if (dom.conceptScaleBadge) {
      dom.conceptScaleBadge.className = `concept-badge ${scaleInfo.badgeClass}`;
      dom.conceptScaleBadge.textContent = scaleInfo.scaleLabel;
      dom.conceptScaleBadge.title = `[물리적 규모] ${scaleInfo.scaleLabel} (${scaleInfo.scopeName})\n클릭 시 하단 '4. 온톨로지 관계'의 규모 인과 계층도로 바로 이동`;
    }

    // 열람 모드 적용 (현재 설정된 readingDepth 유지 및 UI 동기화)
    applyCurrentReadingDepth();

    // 출처 키 목록 추출 (동적 바인딩)
    const evKeys = c.evidences ? Object.keys(c.evidences) : [];
    const ev1Key = evKeys[0] || null;
    const ev2Key = evKeys[1] || evKeys[0] || null;

    // 1. 기본 설명
    const summaryHtml = `
      <p class="doc-paragraph">
        ${enrichTextWithConceptLinks(c.summary, c.id)}
        ${ev1Key ? `<button type="button" class="evidence-pill-btn" data-evidence-id="${ev1Key}" aria-label="출처 ${ev1Key} 보기">[${ev1Key}: ${c.evidences[ev1Key].sourceName.split(' ')[0]} 공식 출처]</button>` : ""}
      </p>
      <ul class="doc-list">
        <li><strong>목적:</strong> ${enrichTextWithConceptLinks(c.purpose, c.id)} ${ev2Key ? `<button type="button" class="evidence-pill-btn" data-evidence-id="${ev2Key}" aria-label="출처 ${ev2Key} 보기">[${ev2Key}]</button>` : ""}</li>
        ${c.prerequisites && c.prerequisites.length > 0 ? `
          <li><strong>선행 이해 개념:</strong> 
            ${c.prerequisites.map(p => `<span class="inline-concept-tag" data-concept="${p.id}">${p.name}</span>`).join(", ")}
          </li>
        ` : ""}
      </ul>
    `;
    document.getElementById("section-summary-content").innerHTML = summaryHtml;

    // 2. 원리 및 한계
    const principlesHtml = `
      <h4 style="font-size:0.875rem; font-weight:700; margin-bottom:6px; color:var(--text-primary);">• 물리·기술적 메커니즘</h4>
      <ul class="doc-list" style="margin-bottom:12px;">
        ${(c.principles || []).map(p => `<li>${enrichTextWithConceptLinks(p, c.id)}</li>`).join("")}
      </ul>
      <h4 style="font-size:0.875rem; font-weight:700; margin-bottom:6px; color:var(--accent-danger);">• 공정 한계 및 관리 주의사항</h4>
      <ul class="doc-list">
        ${(c.limitations || []).map(l => `<li>${enrichTextWithConceptLinks(l, c.id)}</li>`).join("")}
      </ul>
    `;
    document.getElementById("principles-accordion-content").innerHTML = principlesHtml;

    // 팹 파이프라인 인디케이터 동기화
    renderFabStageStrip();

    // 3. 관점별 쓰임 렌더링
    updatePerspectiveView();

    // 4. 온톨로지 관계 및 물리적 규모(Scale) 계층
    const stepperHtml = scaleDefinitions.map((s, idx) => {
      const isActive = s.scale === scaleInfo.scale;
      const arrow = idx < scaleDefinitions.length - 1 ? `<span class="scale-step-connector">➔</span>` : "";
      return `
        <div class="scale-step-node ${isActive ? 'active' : ''}" title="${s.desc}">
          <span>${s.icon} ${s.name}</span>
          <small>${s.range}</small>
        </div>
        ${arrow}
      `;
    }).join("");

    const parents = scaleInfo.parents || (scaleInfo.parent ? [scaleInfo.parent] : []);
    const children = scaleInfo.children || (scaleInfo.child ? [scaleInfo.child] : []);

    const parentBoxHtml = `
      <div class="scale-relation-box scale-box-parent">
        <div class="scale-box-header">
          <span class="scale-direction-label">⬆️ 상위 스케일 인과 영향 (Upper Scale: ${parents.length}건)</span>
          ${parents.length === 0 ? `<span style="font-size:0.6875rem; color:var(--text-muted); font-weight:600;">최상위 스케일</span>` : ""}
        </div>
        ${parents.length === 0 ? `
          <div style="font-size:0.8125rem; color:var(--text-muted); padding:6px 0;">팹 단지 최상위 인프라로서 상위 공정 의존성이 없습니다.</div>
        ` : `
          <div class="scale-links-list">
            ${parents.map(p => `
              <div class="scale-link-card">
                <div class="scale-link-card-header">
                  <div class="scale-link-title-group">
                    ${p.scale ? `<span class="concept-badge badge-scale-${p.scale}" style="font-size:0.6875rem; padding:1px 5px; flex-shrink:0;">Scale ${p.scale}</span>` : ""}
                    <span class="scale-link-title" title="${p.title}">${p.title}</span>
                  </div>
                  ${p.id ? `<button type="button" class="scale-jump-btn" data-concept-id="${p.id}" title="${p.title} 문서로 이동">이동 ➔</button>` : `<span style="font-size:0.6875rem; color:var(--text-muted); font-weight:600; white-space:nowrap;">최상위</span>`}
                </div>
                <p class="scale-link-desc">${p.desc || ""}</p>
              </div>
            `).join("")}
          </div>
        `}
      </div>
    `;

    const childBoxHtml = `
      <div class="scale-relation-box scale-box-child">
        <div class="scale-box-header">
          <span class="scale-direction-label">⬇️ 하위 스케일 물리 메커니즘 & 파생 소자 (Lower Scale: ${children.length}건)</span>
          ${children.length === 0 ? `<span style="font-size:0.6875rem; color:var(--text-muted); font-weight:600;">기초 물리 한계</span>` : ""}
        </div>
        ${children.length === 0 ? `
          <div style="font-size:0.8125rem; color:var(--text-muted); padding:6px 0;">단원자층 및 양자역학 한계 계층으로 추가적인 하위 공정 분기가 없습니다.</div>
        ` : `
          <div class="scale-links-list">
            ${children.map(c => `
              <div class="scale-link-card">
                <div class="scale-link-card-header">
                  <div class="scale-link-title-group">
                    ${c.scale ? `<span class="concept-badge badge-scale-${c.scale}" style="font-size:0.6875rem; padding:1px 5px; flex-shrink:0;">Scale ${c.scale}</span>` : ""}
                    <span class="scale-link-title" title="${c.title}">${c.title}</span>
                  </div>
                  ${c.id ? `<button type="button" class="scale-jump-btn" data-concept-id="${c.id}" title="${c.title} 문서로 이동">이동 ➔</button>` : `<span style="font-size:0.6875rem; color:var(--text-muted); font-weight:600; white-space:nowrap;">물리 한계</span>`}
                </div>
                <p class="scale-link-desc">${c.desc || ""}</p>
              </div>
            `).join("")}
          </div>
        `}
      </div>
    `;

    const scaleNavigatorHtml = `
      <div class="scale-navigator-card" id="scale-hierarchy-card">
        <div class="scale-card-header">
          <div class="scale-card-title-group">
            <span class="scale-icon-tag">${scaleDefinitions.find(s => s.scale === scaleInfo.scale)?.icon || "📐"}</span>
            <div>
              <h3 class="scale-card-title">물리적 규모(Scale) 인과 계층도 (Multi-Scale Context)</h3>
              <p class="scale-card-subtitle">원자(Sub-nm)부터 팹 인프라(km)까지 5단계 물리·운영 범위 및 상하위 인과 추적</p>
            </div>
          </div>
          <span class="concept-badge ${scaleInfo.badgeClass}" style="font-size:0.75rem;">
            현재: ${scaleInfo.scaleLabel} (${scaleInfo.scopeName})
          </span>
        </div>

        <div class="scale-stepper-track">
          ${stepperHtml}
        </div>

        <div class="scale-cards-grid">
          ${parentBoxHtml}
          ${childBoxHtml}
        </div>
      </div>
    `;

    const relationsHtml = `
      ${scaleNavigatorHtml}
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-top:8px;">
        <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px;">
          <span style="font-size:0.6875rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">분류 체계 (is_a)</span>
          <div style="font-size:0.8125rem; font-weight:600; margin-top:4px;">${c.processName}</div>
        </div>
        <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px;">
          <span style="font-size:0.6875rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">핵심 구성 (part_of)</span>
          <div style="font-size:0.8125rem; margin-top:4px;">${c.relations?.part_of?.map(r => r.name).join(", ") || "공정 표준 모듈"}</div>
        </div>
        <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px;">
          <span style="font-size:0.6875rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">후속 연계 (next_step)</span>
          <div style="font-size:0.8125rem; margin-top:4px;">${c.relations?.next_step?.map(r => r.name).join(", ") || "품질 검사 및 세정"}</div>
        </div>
      </div>
    `;
    document.getElementById("section-relations-content").innerHTML = relationsHtml;

    // 5. 공식 검증 출처 원문 (Evidence References) 렌더링
    const evidencesContainer = document.getElementById("section-evidences-content");
    if (evidencesContainer) {
      if (evKeys.length === 0) {
        evidencesContainer.innerHTML = `<p style="font-size:0.8125rem; color:var(--text-muted); padding:12px; background:var(--bg-surface-2); border-radius:6px;">현재 등록된 공식 검증 출처가 없습니다.</p>`;
      } else {
        const evCardsHtml = evKeys.map(k => {
          const ev = c.evidences[k];
          return `
            <div class="evidence-source-card" style="background:var(--bg-surface-2); border:1px solid var(--border-color); border-radius:8px; padding:16px; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; gap:8px;">
                <div>
                  <span class="concept-badge badge-verified" style="font-size:0.6875rem;">${ev.type || "공식 검증"}</span>
                  <span style="font-weight:700; font-size:0.875rem; color:var(--text-primary); margin-left:6px;">[${ev.id || k}] ${ev.sourceName}</span>
                </div>
                <span style="font-size:0.75rem; color:var(--text-muted); white-space:nowrap;">발행: ${ev.pubDate || "-"}</span>
              </div>
              <blockquote style="font-size:0.8125rem; line-height:1.6; color:var(--text-secondary); background:var(--bg-surface-1); padding:10px 14px; border-left:3px solid var(--accent-primary); border-radius:4px; margin:8px 0 12px 0; font-style:italic;">
                "${ev.quote || ""}"
              </blockquote>
              <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                <button type="button" class="cand-action-btn cand-btn-primary evidence-pill-btn" data-evidence-id="${k}" style="font-size:0.75rem; padding:4px 10px; cursor:pointer;">
                  🔍 출처 검증 리더 열기
                </button>
                ${ev.externalUrl ? `
                  <a href="${ev.externalUrl}" target="_blank" rel="noopener noreferrer" style="font-size:0.75rem; color:var(--accent-primary); text-decoration:none; display:inline-flex; align-items:center; gap:4px; padding:4px 8px; border:1px solid var(--border-color); border-radius:4px; background:var(--bg-surface-1);">
                    <span>${ev.urlLabel || "공식 원문 출처 전문 보기"}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                  </a>
                ` : ""}
              </div>
            </div>
          `;
        }).join("");
        evidencesContainer.innerHTML = evCardsHtml;
      }
    }

    bindDynamicEvents();
  }

  // ── 4. 관점 바 (스티키 블록 & 동적 관점 렌더링) ──
  window.setPerspective = function(pKey) {
    state.currentPerspective = pKey;
    updatePerspectiveView();
    const c = WikiStore.concepts[state.currentConceptId];
    const pObj = c?.perspectives?.[pKey];
    if (pObj) {
      showToast(`'${pObj.label || pKey}' 관점으로 전환되었습니다.`, "info");
    }
  };

  function updatePerspectiveView() {
    const c = WikiStore.concepts[state.currentConceptId];
    if (!c || !c.perspectives) return;

    // 만약 현재 선택된 관점이 현재 문서에 없으면 'default'로 리셋
    if (!c.perspectives[state.currentPerspective]) {
      state.currentPerspective = "default";
    }

    // 1. 동적 탭 렌더링
    const pEntries = Object.entries(c.perspectives);
    if (dom.perspectiveTabsContainer) {
      dom.perspectiveTabsContainer.innerHTML = `
        <div class="sliding-tab-indicator" id="perspective-indicator"></div>
        ${pEntries.map(([key, p]) => {
          const isActive = (state.currentPerspective === key);
          let prefix = "○";
          if (key === "default") prefix = "●";
          else if (key.startsWith("company-")) prefix = "🏢";
          
          return `
            <button type="button" class="sliding-tab-item ${isActive ? 'active' : ''} perspective-tab-item" data-perspective="${key}">
              ${prefix} ${p.label || key}
            </button>
          `;
        }).join("")}
      `;

      // 탭 클릭 이벤트 바인딩
      dom.perspectiveTabsContainer.querySelectorAll(".perspective-tab-item").forEach(tab => {
        tab.addEventListener("click", () => {
          window.setPerspective(tab.dataset.perspective);
        });
      });
    }

    let currentP = c.perspectives[state.currentPerspective] || c.perspectives["default"];
    dom.perspectiveDesc.textContent = currentP.description;

    // 탭 슬라이딩 인디케이터 계산
    requestAnimationFrame(() => {
      const activeBtn = dom.perspectiveTabsContainer?.querySelector(".perspective-tab-item.active");
      const indicator = document.getElementById("perspective-indicator");
      if (activeBtn && indicator) {
        indicator.style.width = `${activeBtn.offsetWidth}px`;
        indicator.style.transform = `translateX(${activeBtn.offsetLeft}px)`;
      }
    });

    // 특화 적용 카드 렌더링
    if (currentP.appliedCase) {
      const ac = currentP.appliedCase;
      dom.appliedCardContainer.innerHTML = `
        <div class="perspective-applied-card">
          <div class="pac-header">
            <span class="pac-title">▼ ${ac.title}</span>
            ${ac.code ? `<span class="pac-code">사내 레시피: ${ac.code}</span>` : ""}
          </div>
          <div class="pac-body">
            <p><strong>• 특화 적용 조건:</strong> ${ac.conditions} 
              ${ac.evidenceId ? `<button class="evidence-pill-btn" data-evidence-id="${ac.evidenceId}">[${ac.evidenceId}]</button>` : ""}
            </p>
            <div class="pac-warning">
              ⚠️ ${ac.limitationNote}
            </div>
          </div>
        </div>
      `;
    } else {
      // default 상태일 때, 이 문서에서 선택 가능한 다른 관점들 추천
      const otherKeys = pEntries.filter(([k]) => k !== "default");
      dom.appliedCardContainer.innerHTML = `
        <div style="padding:16px; border:1px dashed var(--border-color); border-radius:8px; color:var(--text-secondary); font-size:0.8125rem; text-align:center; background:var(--bg-surface-2);">
          <div style="font-weight:700; color:var(--text-primary); margin-bottom:4px;">💡 현재 '공통 기본 지식' 렌즈로 열람 중입니다.</div>
          ${otherKeys.length > 0 ? `
            <div style="color:var(--text-muted); margin-bottom:12px; line-height:1.5;">
              상단 탭에서 아래의 세부 적용 관점을 선택하시면, 실제 팹 양산 라인의 구체적 레시피 규격과 결함 관리 기준이 즉시 본문에 반영됩니다.
            </div>
            <div style="display:flex; justify-content:center; gap:8px; flex-wrap:wrap;">
              ${otherKeys.map(([k, p]) => `
                <button type="button" class="cand-action-btn cand-btn-primary" onclick="window.setPerspective('${k}')" style="font-size:0.75rem; padding:5px 12px; cursor:pointer;">
                  ➔ ${p.label} 즉시 적용
                </button>
              `).join("")}
            </div>
          ` : `
            <div style="color:var(--text-muted);">
              현재 문서는 표준 기본 지식 체계로 충실히 열람 중입니다.
            </div>
          `}
        </div>
      `;
    }

    bindDynamicEvents();
  }

  // ── 5. 근거(Evidence) 리더 & 외부 원문 링크 ──
  function openEvidenceDrawer(evidenceId) {
    const c = WikiStore.concepts[state.currentConceptId];
    let ev = c?.evidences?.[evidenceId];
    if (!ev) {
      for (const concept of Object.values(WikiStore.concepts || {})) {
        if (concept.evidences && concept.evidences[evidenceId]) {
          ev = concept.evidences[evidenceId];
          break;
        }
      }
    }
    if (!ev) {
      showToast(`출처 '${evidenceId}' 상세 정보를 불러올 수 없습니다.`, "warning");
      return;
    }

    dom.drawerContent.innerHTML = `
      <div style="margin-bottom:16px;">
        <span class="concept-badge badge-verified" style="margin-bottom:8px;">${ev.type}</span>
        <h3 style="font-size:1.125rem; font-weight:700; margin-bottom:4px;">${ev.sourceName}</h3>
        <p style="font-size:0.8125rem; color:var(--text-muted);">발행/검증일: ${ev.pubDate} | 식별자: ${ev.id}</p>
      </div>

      <div style="background:var(--bg-surface-2); border-left:3px solid var(--accent-primary); padding:16px; border-radius:4px; margin-bottom:16px;">
        <span style="font-size:0.6875rem; font-weight:700; text-transform:uppercase; color:var(--accent-primary); display:block; margin-bottom:8px;">원문 발췌 인용구 (Verbatim Quote)</span>
        <blockquote style="font-size:0.875rem; line-height:1.6; color:var(--text-secondary); font-style:italic;">
          "${ev.quote}"
        </blockquote>
      </div>

      ${ev.externalUrl ? `
        <a href="${ev.externalUrl}" target="_blank" rel="noopener noreferrer" class="external-source-link-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
          <span>${ev.urlLabel || "공식 원문 출처 전문 보기"}</span>
        </a>
      ` : ""}

      <div style="font-size:0.8125rem; color:var(--text-muted); line-height:1.6; margin-top:20px;">
        <h4 style="font-size:0.8125rem; font-weight:700; color:var(--text-primary); margin-bottom:4px;">📌 원본 보존 및 접근 안내</h4>
        <p>본 위키는 외부 원문이 변경되더라도 승인 당시의 스냅샷 인용구를 불변 보존합니다. 전체 문서를 열람하려면 위 링크를 이용하세요.</p>
      </div>
    `;

    dom.evidenceDrawer.classList.add("open");
    dom.drawerBackdrop.classList.add("open");
  }

  function closeEvidenceDrawer() {
    dom.evidenceDrawer.classList.remove("open");
    dom.drawerBackdrop.classList.remove("open");
  }

  dom.drawerCloseBtn.addEventListener("click", closeEvidenceDrawer);
  dom.drawerBackdrop.addEventListener("click", closeEvidenceDrawer);

  // ── 6. 인라인 팝오버 ──
  function showConceptPopover(conceptKey, targetEl) {
    const term = WikiStore.concepts[conceptKey];
    if (!term) return;

    dom.popoverTitle.textContent = term.title;
    dom.popoverSummary.textContent = term.summary;
    dom.popoverAiContext.textContent = term.aiContextNote || "현재 본문 문맥에서 필수적인 선행 기초 개념입니다.";

    const rect = targetEl.getBoundingClientRect();
    dom.conceptPopover.style.top = `${rect.bottom + window.scrollY + 8}px`;
    dom.conceptPopover.style.left = `${Math.max(16, rect.left + window.scrollX - 40)}px`;
    dom.conceptPopover.classList.add("open");
  }

  function hideConceptPopover() {
    dom.conceptPopover.classList.remove("open");
  }

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".inline-concept-tag") && !e.target.closest(".concept-intext-link") && !e.target.closest("#concept-popover")) {
      hideConceptPopover();
    }
  });

  function bindDynamicEvents() {
    document.querySelectorAll(".evidence-pill-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        openEvidenceDrawer(btn.dataset.evidenceId);
      };
    });

    document.querySelectorAll(".inline-concept-tag").forEach(tag => {
      tag.onclick = (e) => {
        e.stopPropagation();
        showConceptPopover(tag.dataset.concept, tag);
      };
    });

    // 본문 인텍스트 상호 참조 하이퍼링크 이벤트
    document.querySelectorAll(".concept-intext-link").forEach(link => {
      link.addEventListener("mouseenter", () => {
        showConceptPopover(link.dataset.conceptId, link);
      });
      link.addEventListener("mouseleave", () => {
        hideConceptPopover();
      });
      link.addEventListener("click", (e) => {
        e.stopPropagation();
        hideConceptPopover();
        window.selectWikiConcept(link.dataset.conceptId);
      });
    });
    // 멀티스케일 인과 계층도 상하위 점프 버튼
    document.querySelectorAll(".scale-jump-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const cid = btn.dataset.conceptId;
        if (cid) {
          window.selectWikiConcept(cid);
        }
      };
    });
  }

  // 아코디언 토글
  document.querySelectorAll(".accordion-header").forEach(header => {
    header.addEventListener("click", () => {
      const item = header.closest(".accordion-item");
      item.classList.toggle("open");
    });
  });

  // ── 지식 열람 심도 (Reading Depth) 버튼 이벤트 ──
  dom.btnDepthAll?.addEventListener("click", () => setReadingDepth("all"));
  dom.btnDepthSummary?.addEventListener("click", () => setReadingDepth("summary"));
  dom.btnDepthMech?.addEventListener("click", () => setReadingDepth("mech"));

  // ── 지식 Scale 뱃지 클릭 시 하단 인과 계층도로 부드럽게 스크롤 ──
  dom.conceptScaleBadge?.addEventListener("click", () => {
    const sec = document.getElementById("sec-relations");
    if (sec) {
      sec.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  // ── 사이드바 탐색 모드 전환 버튼 이벤트 (1안) ──
  dom.sidebarModeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      setSidebarNavMode(btn.dataset.mode);
    });
  });

  // ── 7. 보완 제안 모달 ──
  dom.openSuggestModalBtn.addEventListener("click", () => {
    dom.suggestModal.classList.add("open");
  });

  dom.suggestModalClose.addEventListener("click", () => {
    dom.suggestModal.classList.remove("open");
  });

  dom.suggestForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const comment = document.getElementById("suggest-textarea").value;
    if (!comment.trim()) return;

    WikiStore.reviewQueue.unshift({
      id: `rev-${Date.now()}`,
      conceptId: state.currentConceptId,
      conceptTitle: WikiStore.concepts[state.currentConceptId].title,
      proposalsCount: 1,
      reviewType: "현업 엔지니어 보완 제안",
      author: "현업 사용자 (제안)",
      date: "방금 전",
      status: "검토 대기",
      currentContent: WikiStore.concepts[state.currentConceptId].summary,
      aiMergedDraft: `${WikiStore.concepts[state.currentConceptId].summary} [보완 제안: ${comment}]`,
      diffAdded: comment,
      integrityCheck: {
        evidenceMatch: "신규 제안 접수됨 (검토 필요)",
        ontologyConflict: "미확인",
        impactScope: "검토 대기중"
      }
    });

    dom.suggestModal.classList.remove("open");
    document.getElementById("suggest-textarea").value = "";
    showToast("보완 제안이 '검토 센터' 큐에 성공적으로 등록되었습니다!", "success");
  });

  // ── 8. AI 분석실 (현업 고민 온디맨드 검색형 추천기, 대화형 구체화 & 스냅샷) ──

  // 8-A. 대화형 온톨로지 질문 구체화 상담 (Conversational Query Clarifier)
  async function renderConversationalClarifier(userQuery = "") {
    const q = (userQuery || dom.aiPromptInput?.value || "").trim();
    if (!q) {
      showToast("구체화할 고민이나 키워드를 입력해 주세요 (예: HBM 방열, Cryo 식각, High-NA).", "info");
      dom.aiPromptInput?.focus();
      return;
    }

    if (!dom.aiDialogueArea) return;
    dom.aiDialogueArea.style.display = "block";

    dom.aiDialogueArea.innerHTML = `
      <div class="reasoning-stream-box">
        <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <span>온톨로지 인과 사슬 및 물리 스케일별 비교 분기 분석 중...</span>
      </div>
    `;

    try {
      const clarifyResult = await window.OntologyAgentCore.clarifyPainpoint(q);
      const clarifiedTitle = clarifyResult.clarifiedQuestion || `'${q}' 관련 인과 분기`;
      const branches = clarifyResult.branches || [];

      dom.aiDialogueArea.innerHTML = `
        <div class="ai-dialogue-stream" style="margin-top:0;">
          <div class="dialogue-bubble dialogue-user-bubble">
            <strong>🗣️ 엔지니어 질의:</strong> "${q}"
          </div>
          <div class="dialogue-bubble dialogue-agent-bubble">
            <div style="font-weight:700; color:var(--accent-primary); margin-bottom:4px;">🤖 온톨로지 에이전트 구체화 안내</div>
            <p style="margin-bottom:8px;">
              ${clarifiedTitle}. 온톨로지 지식 그래프 상에서 다음 <strong>${branches.length}가지 핵심 분기</strong>가 식별되었습니다:
            </p>
            <div class="clarifier-options-grid">
              ${branches.map((b, idx) => {
                const paramEntries = Object.entries(b.params || {});
                const paramsBadges = paramEntries.length > 0
                  ? paramEntries.map(([k, v]) => `<span style="background:var(--bg-surface-2); padding:2px 7px; border-radius:4px; border:1px solid var(--border-color); font-size:0.6875rem;">${k}: <strong>${v}</strong></span>`).join(" ")
                  : `<span style="font-size:0.6875rem; color:var(--text-muted);">표준 공정 물리 규칙</span>`;

                return `
                <div class="clarifier-option-card clarifier-card" data-idx="${idx}" style="--card-index: ${idx};">
                  <div class="clarifier-option-info">
                    <div class="clarifier-option-title">
                      <span class="concept-badge badge-scale-3" style="font-size:0.6875rem;">${b.domain || '온톨로지 인과'}</span>
                      <span>${b.title}</span>
                    </div>
                    <div class="clarifier-option-desc">${b.desc}</div>
                    <div style="margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                      <span style="font-size:0.6875rem; font-weight:700; color:var(--text-secondary);">⚙️ 핵심 공학 변수:</span>
                      ${paramsBadges}
                    </div>
                  </div>
                  <button type="button" class="cand-action-btn cand-btn-primary" style="white-space:nowrap; font-size:0.8125rem;">
                    이 조건으로 세팅 & 분석 ➔
                  </button>
                </div>
                `;
              }).join("")}
            </div>
          </div>
        </div>
      `;

      dom.aiDialogueArea.querySelectorAll(".clarifier-option-card").forEach(card => {
        card.addEventListener("click", () => {
          const idx = parseInt(card.dataset.idx, 10);
          const b = branches[idx];
          if (b) {
            dom.aiPromptInput.value = b.title;
            const titleParts = b.title.split(/[:—–-]/);
            dom.tagTextA.textContent = (titleParts[0] || b.title).trim();
            dom.tagTextB.textContent = (titleParts[1] || "업계 표준 대조군").trim();
            dom.tagTextDomain.textContent = b.domain || "반도체 핵심 공정";

            showToast(`'${b.title}' 조건으로 파라미터가 세팅되었습니다. 다차원 분석을 실행합니다!`, "info");
            dom.aiRunBtn.click();
          }
        });
      });
    } catch (err) {
      console.warn("Clarify error:", err);
      showToast("질문 구체화 처리 중 오류가 발생했습니다.", "warning");
    }
  }

  // 질문 구체화 버튼 클릭 이벤트
  dom.aiClarifyBtn?.addEventListener("click", () => {
    renderConversationalClarifier(dom.aiPromptInput?.value);
  });

  // 엔터 키 입력 시 질문 구체화 자동 호출
  dom.aiPromptInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      renderConversationalClarifier(dom.aiPromptInput.value);
    }
  });

  function renderPainPoints(query = "") {
    const q = (query || "").trim().toLowerCase();
    
    // 1. 검색어가 비어 있을 때 (초기 상태): 카드를 전부 늘어놓지 않고 정돈된 가이드와 탐색 칩 표시
    if (!q) {
      dom.painpointCardList.innerHTML = `
        <div class="painpoint-empty-guide">
          <div class="empty-guide-icon">💡</div>
          <div class="empty-guide-title">원하는 엔지니어링 주제나 기술 키워드를 검색해 보세요</div>
          <p class="empty-guide-desc">
            위 입력창에 키워드를 입력하시거나 상단 <strong>빠른 추천 탐색 칩</strong>을 클릭하시면, 양산 현장의 실무 고민 템플릿과 비교 파라미터 세트(A사 vs B사, 평가 도메인)를 실시간으로 추천해 드립니다.
          </p>
          <div class="empty-guide-chips">
            <span class="guide-chip" data-query="HBM">🔥 HBM 방열·MR-MUF</span>
            <span class="guide-chip" data-query="Cryo">❄️ Cryogenic 극저온 식각</span>
            <span class="guide-chip" data-query="High-NA">🔬 High-NA 0.55 노광</span>
            <span class="guide-chip" data-query="에어갭">⚡ DRAM 비트라인 에어갭</span>
            <span class="guide-chip" data-query="본딩">🔗 Cu-Cu 하이브리드 본딩</span>
            <span class="guide-chip" data-query="FDC">📊 챔버 실시간 OES FDC</span>
            <span class="guide-chip" data-query="GAA">⚙️ GAA 나노시트 선택식각</span>
            <span class="guide-chip" data-query="스크러버">🌱 팹 플라즈마 스크러버</span>
          </div>
        </div>
      `;

      dom.painpointCardList.querySelectorAll(".guide-chip").forEach(chip => {
        chip.addEventListener("click", () => {
          const kw = chip.dataset.query;
          dom.aiPromptInput.value = kw;
          renderConversationalClarifier(kw);
          dom.aiPromptInput.focus();
        });
      });
      return;
    }

    // 2. 검색어가 입력되었을 때: 매칭되는 고민 템플릿 실시간 필터링
    const matches = WikiStore.engineerPainPoints.filter(p => {
      const matchProblem = p.userProblem?.toLowerCase().includes(q);
      const matchRecom = p.recommendedTitle?.toLowerCase().includes(q);
      const matchPrompt = p.prompt?.toLowerCase().includes(q);
      const matchDomain = p.domain?.toLowerCase().includes(q);
      const matchTechA = p.paramA?.tech?.toLowerCase().includes(q);
      const matchCompA = p.paramA?.company?.toLowerCase().includes(q);
      const matchTechB = p.paramB?.tech?.toLowerCase().includes(q);
      const matchCompB = p.paramB?.company?.toLowerCase().includes(q);
      return matchProblem || matchRecom || matchPrompt || matchDomain || matchTechA || matchCompA || matchTechB || matchCompB;
    });

    if (matches.length === 0) {
      dom.painpointCardList.innerHTML = `
        <div class="painpoint-no-match">
          <p>💡 <strong>'${query}'</strong> 관련 사전 정의된 현업 템플릿 외에도, 에이전트와 대화하여 정밀 비교 쿼리를 도출할 수 있습니다.</p>
          <button type="button" class="cand-action-btn cand-btn-primary" id="btn-custom-clarify">
            '${query}' 대화형 질문 구체화 실행
          </button>
        </div>
      `;
      document.getElementById("btn-custom-clarify")?.addEventListener("click", () => {
        renderConversationalClarifier(query);
      });
      return;
    }

    dom.painpointCardList.innerHTML = `
      <div class="painpoint-match-header">
        <span>🎯 <strong>'${query}'</strong> 연관 현업 공학 고민 템플릿 (<strong>${matches.length}건</strong> 추천됨)</span>
        <button type="button" class="clear-filter-btn" id="btn-clear-painpoint-filter">전체 안내로 돌아가기</button>
      </div>
      ${matches.map(p => `
        <div class="painpoint-card" data-pain-id="${p.id}">
          <div>
            <div class="painpoint-problem-text">🔥 현업 고민: "${p.userProblem}"</div>
            <div class="painpoint-recom-title">➔ AI 추천 분석: ${p.recommendedTitle}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
              파라미터 세팅: [${p.paramA.company} (${p.paramA.tech})] vs [${p.paramB.company} (${p.paramB.tech})] | 평가: ${p.domain}
            </div>
          </div>
          <button type="button" class="cand-action-btn cand-btn-primary" style="white-space:nowrap;">
            이 분석 시작
          </button>
        </div>
      `).join("")}
    `;

    document.getElementById("btn-clear-painpoint-filter")?.addEventListener("click", () => {
      dom.aiPromptInput.value = "";
      renderPainPoints("");
      if (dom.aiDialogueArea) dom.aiDialogueArea.style.display = "none";
      dom.aiPromptInput.focus();
    });

    dom.painpointCardList.querySelectorAll(".painpoint-card").forEach(card => {
      card.addEventListener("click", () => {
        const p = WikiStore.engineerPainPoints.find(item => item.id === card.dataset.painId);
        if (p) {
          dom.aiPromptInput.value = p.prompt;
          dom.tagTextA.textContent = `${p.paramA.company} (${p.paramA.tech})`;
          dom.tagTextB.textContent = `${p.paramB.company} (${p.paramB.tech})`;
          dom.tagTextDomain.textContent = p.domain;

          showToast(`고민 해결을 위한 '${p.recommendedTitle}' 분석을 시작합니다.`, "info");
          dom.aiRunBtn.click();
        }
      });
    });
  }

  // 상단 빠른 추천 검색어 칩 클릭 바인딩
  document.querySelectorAll(".ai-suggest-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      dom.aiPromptInput.value = q;
      renderConversationalClarifier(q);
      dom.aiPromptInput.focus();
    });
  });

  // AI 프롬프트 입력창 실시간 추천 필터링 바인딩
  dom.aiPromptInput?.addEventListener("input", (e) => {
    renderPainPoints(e.target.value);
  });

  function renderAiStudioSnapshot(index) {
    state.currentSnapshotIndex = index;
    const demo = WikiStore.aiStudioDemo;
    const currentSnap = demo.snapshots[index];

    dom.aiSnapshotTimeline.innerHTML = demo.snapshots.map((snap, i) => `
      <div class="snapshot-step-chip ${i === index ? 'active' : ''} ${i < index ? 'done' : ''}" data-step-index="${i}">
        <span class="step-num">${i + 1}</span>
        <span>${snap.title}</span>
      </div>
    `).join("");

    dom.aiSnapshotTimeline.querySelectorAll(".snapshot-step-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        renderAiStudioSnapshot(parseInt(chip.dataset.stepIndex, 10));
      });
    });

    if (index === 0) {
      dom.aiResultCard.innerHTML = `
        <div style="padding:16px; background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px;">
          <h4 style="font-weight:700; margin-bottom:8px;">[1단계] ${currentSnap.title}</h4>
          <p style="font-size:0.875rem; color:var(--text-secondary); margin-bottom:12px;">${currentSnap.data.summary}</p>
          <ul class="doc-list">${currentSnap.data.details.map(d => `<li>${d}</li>`).join("")}</ul>
          <div style="font-size:0.8125rem; color:var(--text-muted); margin-top:12px;">⏳ 2단계에서 양사의 양산 레시피 전제를 매핑합니다.</div>
        </div>
      `;
    } else if (index === 1) {
      dom.aiResultCard.innerHTML = `
        <div style="padding:16px; background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px;">
          <h4 style="font-weight:700; margin-bottom:8px;">[2단계] ${currentSnap.title}</h4>
          <p style="font-size:0.875rem; color:var(--text-secondary); margin-bottom:12px;">${currentSnap.data.summary}</p>
          <ul class="doc-list">${currentSnap.data.details.map(d => `<li>${d}</li>`).join("")}</ul>
          
          <div style="margin-top:16px; padding:12px; background:var(--bg-surface-2); border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.8125rem; color:var(--text-secondary);">⚙️ 이 조건 수치가 실제 현장과 다른가요?</span>
            <button type="button" class="cand-action-btn cand-btn-primary" id="btn-open-edit-params">
              이 시점 전제를 수정하고 재실행
            </button>
          </div>
        </div>
      `;

      document.getElementById("btn-open-edit-params")?.addEventListener("click", () => {
        dom.editParamsModal.classList.add("open");
      });
    } else if (index === 2) {
      const snapData = currentSnap.data;
      dom.aiResultCard.innerHTML = `
        <table class="comparison-matrix-table">
          <thead>
            <tr>
              <th style="width:24%;">비교 분석 축</th>
              <th style="width:38%;">MR-MUF (SK하이닉스 적용 맥락)</th>
              <th style="width:38%;">TC-NCF (마이크론 적용 맥락)</th>
            </tr>
          </thead>
          <tbody>
            ${snapData.matrix.map(row => `
              <tr>
                <td><strong>${row.axis}</strong></td>
                <td>${row.mrf}</td>
                <td>${row.ncf}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>

        <div style="margin-top:16px; padding:12px 16px; background:var(--bg-surface-2); border-radius:8px; font-size:0.8125rem; line-height:1.6;">
          ${snapData.aiNote}
        </div>

        <!-- Step 2-2: A06 결정 반영 온톨로지 보완 제안 자동 도출 카드 -->
        <div class="ai-export-review-card">
          <div class="ai-export-review-content">
            <div class="ai-export-review-title">
              <span>💡</span>
              <span>온톨로지 보완 제안 자동 도출 (A06 결정 반영)</span>
            </div>
            <p class="ai-export-review-desc">
              비교 분석 결과, 현재 위키 온톨로지에 누락된 <strong>[MR-MUF 16단 적층 시 액상 에폭시 점도 제어 한계(120Pa·s)]</strong> 및 <strong>[TC-NCF 갭필 보이드 결함 대조 데이터]</strong>가 도출되었습니다.
            </p>
          </div>
          <button type="button" class="cand-action-btn cand-btn-primary" id="send-wiki-prop-btn" style="white-space:nowrap; padding:10px 18px; font-weight:700;">
            ✍️ 이 분석 결과를 검토 센터로 전송하여 온톨로지에 반영하기 ➔
          </button>
        </div>
      `;

      document.getElementById("send-wiki-prop-btn")?.addEventListener("click", () => {
        const newReviewItem = {
          id: `rev-ai-${Date.now()}`,
          conceptId: "mr-muf",
          conceptTitle: "MR-MUF 16단 점도 및 TC-NCF 보이드 한계 보완",
          proposalsCount: 2,
          reviewType: "AI 관점 분석실 도출 지식 반영",
          author: "AI Contextual Studio (A06)",
          date: "방금 전",
          status: "검토 대기",
          currentContent: "MR-MUF는 적층 칩 사이에 액상 에폭시 몰딩을 주입하여 경화하는 방식이다.",
          aiMergedDraft: "MR-MUF는 적층 칩 사이에 액상 에폭시 몰딩을 주입하여 경화하는 방식이다. [보완] 16단 고단 적층 시 마이크로범프 간격 협소화(15μm)로 인해 에폭시 점도를 120Pa·s 이하로 정밀 통제해야 하며, 반면 TC-NCF는 열압착 압력 누적으로 칩 휨(Warpage) 및 갭필 보이드 결함 위험이 상대적으로 2.3배 높음.",
          diffAdded: "16단 고단 적층 시 마이크로범프 간격 협소화(15μm)로 인해 에폭시 점도를 120Pa·s 이하로 정밀 통제해야 하며, 반면 TC-NCF는 열압착 압력 누적으로 칩 휨(Warpage) 및 갭필 보이드 결함 위험이 상대적으로 2.3배 높음.",
          integrityCheck: {
            evidenceMatch: "IEEE ECTC 2026 및 SK하이닉스 학술 비교 분석 기반 (100%)",
            ontologyConflict: "온톨로지 충돌 없음",
            impactScope: "HBM 메모리 및 패키징 공정 2건"
          }
        };

        WikiStore.reviewQueue.unshift(newReviewItem);
        state.selectedReviewId = newReviewItem.id;
        renderReviewQueue();
        showToast("AI 분석실에서 도출된 지식이 3번 검토 센터 큐에 등록되었습니다! 검토 센터 탭으로 이동합니다.", "success");
        setTimeout(() => {
          setWorkspace("review");
        }, 600);
      });
    }
  }

  // 전제 수정 폼 제출
  dom.editParamsForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const newPressure = document.getElementById("param-b-pressure")?.value || "1.8MPa";
    dom.editParamsModal.classList.remove("open");
    
    showToast(`B사 본딩 압력을 '${newPressure}'(으)로 보정하여 스냅샷 3을 재계산합니다.`, "info");
    
    dom.aiResultCard.innerHTML = `
      <div class="reasoning-stream-box">
        <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <span>수정된 전제(압력 ${newPressure})로 온톨로지 인과 매트릭스 실시간 재추론 중...</span>
      </div>
    `;

    try {
      const res = await window.OntologyAgentCore.runComparativeAnalysis({
        domain: dom.tagTextDomain?.textContent || "첨단 패키징",
        params: { pressure: newPressure, temp: "180℃" },
        snapshotIndex: 2
      });

      if (res.matrix && res.matrix.length) {
        WikiStore.aiStudioDemo.snapshots[2].data.matrix = res.matrix.map(m => ({
          axis: m.axis,
          muf: m.companyA,
          ncf: m.companyB,
          winner: m.winner || "muf"
        }));
      }
      if (res.recommendation) {
        WikiStore.aiStudioDemo.snapshots[2].data.recommendation = res.recommendation;
      }

      renderAiStudioSnapshot(2);
      showToast("수정된 전제를 기반으로 비교 분석 결과가 실시간 갱신되었습니다!", "success");
    } catch (err) {
      console.warn("Analysis error:", err);
      renderAiStudioSnapshot(2);
    }
  });

  dom.aiRunBtn.addEventListener("click", () => {
    dom.aiResultCard.innerHTML = `
      <div class="reasoning-stream-box">
        <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <span>공식 출처 지식 온톨로지 조회 및 조건 추출 중...</span>
      </div>
    `;

    setTimeout(() => {
      renderAiStudioSnapshot(2);
      showToast("다차원 비교 분석이 완료되었습니다. (스냅샷 3개 생성)", "info");
    }, 1200);
  });

  // ── 9. 검토 센터 (HITL 직접 편집 에디터 & 에이전트 수정 지시) ──
  function renderReviewQueue() {
    dom.sidebarReviewQueueList.innerHTML = WikiStore.reviewQueue.map(item => `
      <div class="review-queue-item ${item.id === state.selectedReviewId ? 'active' : ''}" data-review-id="${item.id}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <strong style="font-size:0.875rem;">${item.conceptTitle.split("(")[0]}</strong>
          <span class="concept-badge ${item.status === '게시 완료' ? 'badge-verified' : ''}" style="font-size:0.6875rem;">
            ${item.status}
          </span>
        </div>
        <div style="font-size:0.75rem; color:var(--text-muted);">${item.reviewType} • ${item.author}</div>
      </div>
    `).join("");

    dom.sidebarReviewQueueList.querySelectorAll(".review-queue-item").forEach(itemEl => {
      itemEl.addEventListener("click", () => {
        state.selectedReviewId = itemEl.dataset.reviewId;
        renderReviewQueue();
        renderReviewDetails();
      });
    });

    renderReviewDetails();
  }

  function renderReviewDetails() {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item) return;

    document.getElementById("review-detail-title").textContent = item.conceptTitle;
    document.getElementById("review-detail-meta").textContent = `제안 구분: ${item.reviewType} | 작성자: ${item.author} (${item.date})`;

    dom.diffCurrentText.textContent = item.currentContent;
    dom.diffDraftText.innerHTML = item.aiMergedDraft.replace(item.diffAdded, `<span class="diff-added-text">${item.diffAdded}</span>`);

    dom.integrityEvidence.textContent = item.integrityCheck.evidenceMatch;
    dom.integrityOntology.textContent = item.integrityCheck.ontologyConflict;
    dom.integrityImpact.textContent = item.integrityCheck.impactScope;

    dom.approveReviewBtn.disabled = (item.status === "게시 완료");
    dom.approveReviewBtn.textContent = (item.status === "게시 완료") ? "✔ 이미 승인 및 게시됨" : "승인 및 공용 위키에 즉시 게시";
    
    // 에디터 모드 초기화 (기본은 diff 뷰)
    if (dom.reviewEditorContainer && dom.diffDraftContainer) {
      dom.reviewEditorContainer.style.display = "none";
      dom.diffDraftContainer.style.display = "block";
      dom.btnToggleEditor.textContent = "✏️ 직접 편집 모드";
    }

    if (item.status === "게시 완료") {
      dom.gotoWikiBtn.style.display = "inline-flex";
      dom.gotoWikiBtn.onclick = () => {
        state.currentConceptId = (item.conceptId === "dry-etch") ? "dry-etch" : "mr-muf";
        setWorkspace("wiki");
        window.scrollTo({ top: 300, behavior: "smooth" });
        showToast("방금 승인 반영된 위키 문서 위치로 이동했습니다.", "info");
      };
    } else {
      dom.gotoWikiBtn.style.display = "none";
    }
  }

  // 직접 편집 모드 토글
  dom.btnToggleEditor?.addEventListener("click", () => {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item) return;

    const isEditing = dom.reviewEditorContainer.style.display === "flex" || dom.reviewEditorContainer.style.display === "block";
    if (isEditing) {
      dom.reviewEditorContainer.style.display = "none";
      dom.diffDraftContainer.style.display = "block";
      dom.diffDraftContainer.classList.remove("fade-slide-up");
      void dom.diffDraftContainer.offsetWidth; // 트리거 리플로우
      dom.diffDraftContainer.classList.add("fade-slide-up");
      dom.btnToggleEditor.textContent = "✏️ 직접 편집 모드";
    } else {
      dom.reviewEditorContainer.style.display = "flex";
      dom.reviewEditorContainer.classList.remove("fade-slide-up");
      void dom.reviewEditorContainer.offsetWidth; // 트리거 리플로우
      dom.reviewEditorContainer.classList.add("fade-slide-up");
      dom.diffDraftContainer.style.display = "none";
      dom.reviewEditorInput.value = item.aiMergedDraft;
      dom.btnToggleEditor.textContent = "👁️ 비교 뷰로 돌아가기";
      dom.reviewEditorInput.focus();
    }
  });

  // 직접 편집 저장
  dom.btnSaveEdit?.addEventListener("click", () => {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item) return;

    item.aiMergedDraft = dom.reviewEditorInput.value;
    item.status = "초안 수정됨 (인간 편집)";
    item.integrityCheck.evidenceMatch = "인간 전문가 직접 수정 검증 완료 (100%)";
    
    dom.reviewEditorContainer.style.display = "none";
    dom.diffDraftContainer.style.display = "block";
    dom.diffDraftContainer.classList.remove("fade-slide-up");
    void dom.diffDraftContainer.offsetWidth;
    dom.diffDraftContainer.classList.add("fade-slide-up");
    dom.btnToggleEditor.textContent = "✏️ 직접 편집 모드";

    renderReviewQueue();
    showToast("인간 전문가가 직접 편집한 내용이 초안에 저장되었습니다.", "success");
  });

  // 직접 편집 취소
  dom.btnCancelEdit?.addEventListener("click", () => {
    dom.reviewEditorContainer.style.display = "none";
    dom.diffDraftContainer.style.display = "block";
    dom.diffDraftContainer.classList.remove("fade-slide-up");
    void dom.diffDraftContainer.offsetWidth;
    dom.diffDraftContainer.classList.add("fade-slide-up");
    dom.btnToggleEditor.textContent = "✏️ 직접 편집 모드";
  });

  // 에이전트 수정 지시(Agent Revision Directive) 처리
  async function handleAgentDirective(directiveText) {
    const text = (directiveText || dom.agentDirectiveInput?.value || "").trim();
    if (!text) {
      showToast("에이전트에게 내릴 수정 지시사항을 입력해 주세요.", "info");
      dom.agentDirectiveInput?.focus();
      return;
    }

    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item) return;

    if (dom.directiveStatusArea) {
      dom.directiveStatusArea.innerHTML = `
        <div class="reasoning-stream-box" style="margin-top:4px; padding:10px 14px;">
          <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
          <span>에이전트가 지시사항('[${text}]')을 온톨로지 규칙에 맞추어 초안에 반영하는 중...</span>
        </div>
      `;
    }

    try {
      const result = await window.OntologyAgentCore.reviseReviewDraft({
        conceptId: item.conceptId || "dry-etch",
        currentDraft: item.aiMergedDraft,
        directive: text
      });

      item.aiMergedDraft = result.revisedDraft;
      item.diffAdded += `\n[지시 반영] ${text}`;
      if (result.integrityReport) {
        item.integrityCheck = {
          evidenceMatch: `공식 출처 전수 검증 (${result.integrityReport.evidence || '100%'})`,
          ontologyConflict: result.integrityReport.conflict || "없음",
          impactScope: result.integrityReport.impact || "1건"
        };
      }

      item.status = "초안 재작성됨 (지시 반영)";
      if (dom.agentDirectiveInput) dom.agentDirectiveInput.value = "";
      if (dom.directiveStatusArea) {
        dom.directiveStatusArea.innerHTML = `<span style="color:var(--accent-success); font-size:0.8125rem; font-weight:700;">✔ 에이전트 지시가 성공적으로 반영되어 초안이 갱신되었습니다.</span>`;
      }
      renderReviewQueue();
      showToast(result.changeSummary || "에이전트 수정 지시가 초안에 완벽히 반영되었습니다!", "success");
    } catch (err) {
      console.warn("Directive error:", err);
      showToast("수정 지시 처리 중 오류 발생: " + err.message, "warning");
    }
  }

  dom.btnSendDirective?.addEventListener("click", () => {
    handleAgentDirective();
  });

  dom.agentDirectiveInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAgentDirective();
    }
  });

  document.querySelectorAll(".directive-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const dirText = chip.dataset.directive;
      if (dirText) handleAgentDirective(dirText);
    });
  });

  // ── 검토 센터: 승인 시 위키 페이지 렌더링 미리보기 모달 (Transitions.dev) ──
  function openWikiPreviewModal() {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item || !dom.modalWikiPreview || !dom.wikiPreviewContent) return;

    const targetConceptId = item.conceptId || "dry-etch";
    const c = WikiStore.concepts[targetConceptId] || {
      id: targetConceptId,
      title: item.conceptTitle,
      engName: "Plasma Dry Etching",
      processName: "식각 공정",
      scaleId: "Scale 3",
      summary: item.currentContent,
      purpose: "웨이퍼 표면의 불필요한 박막을 선택적으로 제거하여 미세 반도체 패턴 형성",
      principles: [
        "플라즈마 방전으로 생성된 반응성 라디칼에 의한 등방성 화학 식각",
        "웨이퍼 바이어스 전압에 의해 가속된 이온 충돌에 의한 비등방성 물리 식각 (이온 보조 식각)"
      ],
      limitations: [
        "고종횡비 구조에서 마이크로 로딩 및 ARDE(종횡비 의존 식각) 현상으로 인한 식각율 저하",
        "플라즈마 유기 손상(PID) 및 게이트 절연막 전하 축적 파괴 위험"
      ]
    };

    // diff highlight 적용
    let highlightedDraft = item.aiMergedDraft;
    if (item.diffAdded && highlightedDraft.includes(item.diffAdded)) {
      highlightedDraft = highlightedDraft.replace(
        item.diffAdded,
        `<mark class="preview-diff-highlight">${item.diffAdded}</mark>`
      );
    } else {
      highlightedDraft = highlightedDraft.replace(
        /(\[추가\][^.\n]+(?:\.|\n)?)/g,
        `<mark class="preview-diff-highlight">$1</mark>`
      );
      highlightedDraft = highlightedDraft.replace(
        /(\[지시 반영\][^.\n]+(?:\.|\n)?)/g,
        `<mark class="preview-diff-highlight">$1</mark>`
      );
    }

    const scaleBadgeClass = c.scaleId === "Scale 1" ? "badge-scale-1" :
                            c.scaleId === "Scale 2" ? "badge-scale-2" :
                            c.scaleId === "Scale 4" ? "badge-scale-4" : "badge-scale-3";

    const previewHtml = `
      <!-- 승인 변경 안내 배너 -->
      <div class="wiki-preview-alert-banner">
        <span class="preview-banner-badge">✨ 승인 반영 시 변경 요약</span>
        <div class="preview-banner-text">
          <strong>제안 구분:</strong> ${item.reviewType} | <strong>제안자:</strong> ${item.author} (${item.date})<br>
          <strong>공식 출처 정합성:</strong> <span style="color:#15803d; font-weight:700;">${item.integrityCheck?.evidenceMatch || '100% 일치'}</span> | 
          <strong>온톨로지 충돌:</strong> <span style="color:#15803d; font-weight:700;">${item.integrityCheck?.ontologyConflict || '없음'}</span> | 
          <strong>영향 범위:</strong> ${item.integrityCheck?.impactScope || '1건'}
        </div>
      </div>

      <!-- 위키 문서 헤더 -->
      <div class="wiki-preview-header">
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:6px;">
          <span>제조 단위 공정</span> ➔ <span>${c.processName || '단위 공정'}</span> ➔ <strong style="color:var(--text-primary);">${c.title.split('(')[0].trim()}</strong>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
          <div>
            <h2 style="font-size:1.625rem; font-weight:800; margin:0 0 6px 0; color:var(--text-primary);">
              ${c.title}
            </h2>
            <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
              <span class="concept-badge badge-level-1">Level 1 · 산업 공통 기초</span>
              <span class="concept-badge ${scaleBadgeClass}">${c.scaleId || 'Scale 3'} · 단위 공정 & 런</span>
              <span class="concept-badge badge-verified" style="background:#dcfce7; color:#15803d; border:1px solid #86efac; font-weight:700;">
                v1.3 (신규 승인 반영 예정)
              </span>
              <span class="concept-badge" style="background:var(--bg-surface-2); border:1px solid var(--border-color); color:var(--text-secondary);">
                검토: 2026.10.15 (인간 전문가 HITL 승인 예정)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 1. 기본 설명 & AI 통합 초안 -->
      <div class="doc-section" style="margin-bottom:24px;">
        <h3 class="section-title" style="font-size:1.125rem; font-weight:700; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
          <span>1. 개요 및 정의</span>
          <span style="font-size:0.6875rem; color:#15803d; background:#dcfce7; padding:2px 6px; border-radius:4px; font-weight:600;">초안 병합 완료</span>
        </h3>
        <div style="line-height:1.75; font-size:0.9375rem; color:var(--text-primary); background:var(--bg-surface-2); padding:16px 18px; border-radius:8px; border:1px solid var(--border-color); margin-bottom:12px;">
          ${highlightedDraft}
        </div>
        <ul class="doc-list" style="font-size:0.875rem; margin-top:8px;">
          <li><strong>목적:</strong> ${c.purpose || '웨이퍼 표면의 불필요한 박막을 선택적으로 제거하여 초미세 나노 패턴 형성'}</li>
          ${c.prerequisites && c.prerequisites.length > 0 ? `
            <li><strong>선행 이해 개념:</strong> ${c.prerequisites.map(p => `<span class="inline-concept-tag">${p.name || p.id}</span>`).join(", ")}</li>
          ` : `<li><strong>선행 이해 개념:</strong> <span class="inline-concept-tag">플라즈마 방전 기초</span>, <span class="inline-concept-tag">반응성 이온 식각(RIE)</span></li>`}
        </ul>
      </div>

      <!-- 2. 핵심 원리 및 물리적 한계 -->
      <div class="doc-section" style="margin-bottom:24px;">
        <h3 class="section-title" style="font-size:1.125rem; font-weight:700; margin-bottom:10px;">2. 핵심 원리 및 물리적 한계</h3>
        <div style="background:var(--bg-surface-2); border:1px solid var(--border-color); border-radius:8px; padding:16px;">
          <h4 style="font-size:0.875rem; font-weight:700; margin-bottom:6px; color:var(--text-primary);">• 물리·기술적 메커니즘</h4>
          <ul class="doc-list" style="margin-bottom:12px; font-size:0.875rem;">
            ${(c.principles || [
              "플라즈마 방전으로 생성된 CFx 라디칼의 웨이퍼 표면 흡착 및 화학 반응",
              "RF 바이어스 전압에 가속된 이온의 수직 입사로 측벽 보호막 유지 및 수직 프로파일 구현"
            ]).map(p => `<li>${p}</li>`).join("")}
          </ul>
          <h4 style="font-size:0.875rem; font-weight:700; margin-bottom:6px; color:var(--accent-danger, #ef4444);">• 공정 한계 및 관리 주의사항</h4>
          <ul class="doc-list" style="font-size:0.875rem;">
            ${(c.limitations || [
              "초미세 패턴 종횡비(HARC) 증가 시 이온 수송 장애 및 에칭 정지(Etch Stop) 위험",
              "극저온(-60℃) 운전 시 불소계 부산물 배기 한계 및 챔버 오염 제어 주의"
            ]).map(l => `<li>${l}</li>`).join("")}
          </ul>
        </div>
      </div>

      <!-- 3. 다중 물리적 규모(Scale 1~4) 인과 연계 -->
      <div class="doc-section" style="margin-bottom:24px;">
        <h3 class="section-title" style="font-size:1.125rem; font-weight:700; margin-bottom:10px;">3. 다중 물리적 규모(Scale 1~4) 인과 연계</h3>
        <div class="wiki-preview-scale-stepper">
          <div class="wiki-preview-scale-node" title="Scale 1: 0.1nm ~ 10nm 원자·나노 물리">
            <span style="font-size:0.6875rem; color:var(--text-muted); display:block;">Scale 1 (나노/분자)</span>
            CFx 라디칼 흡착 & 이온 충돌
          </div>
          <span style="color:var(--text-muted);">➔</span>
          <div class="wiki-preview-scale-node" title="Scale 2: 10nm ~ 100nm 소자 셀 구조">
            <span style="font-size:0.6875rem; color:var(--text-muted); display:block;">Scale 2 (소자 셀)</span>
            GAA 나노시트 선택비 30:1 & 캐패시터
          </div>
          <span style="color:var(--text-muted);">➔</span>
          <div class="wiki-preview-scale-node current" title="Scale 3: 1cm ~ 300mm 웨이퍼 단위 공정">
            <span style="font-size:0.6875rem; color:#1d4ed8; display:block; font-weight:700;">Scale 3 (본 문서)</span>
            ICP-RIE 챔버 극저온 ESC 제어
          </div>
          <span style="color:var(--text-muted);">➔</span>
          <div class="wiki-preview-scale-node" title="Scale 4: Fab 전체 & 시스템 수율">
            <span style="font-size:0.6875rem; color:var(--text-muted); display:block;">Scale 4 (수율/팹)</span>
            2nm 선단 파운드리 누설전류 불량 통제
          </div>
        </div>
      </div>

      <!-- 4. 4대 도메인 관점 분석 요약 -->
      <div class="doc-section" style="margin-bottom:20px;">
        <h3 class="section-title" style="font-size:1.125rem; font-weight:700; margin-bottom:10px;">4. 4대 도메인 관점 분석 요약</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
          <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:0.8125rem;">
            <div style="font-weight:700; margin-bottom:4px; color:var(--accent-primary);">🛡️ 신뢰성 관점</div>
            <div style="color:var(--text-secondary); font-size:0.75rem;">과도 식각 방지를 통한 박막 손상 방지 및 절연 파괴 억제</div>
          </div>
          <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:0.8125rem;">
            <div style="font-weight:700; margin-bottom:4px; color:var(--accent-success);">⚙️ 양산 제조 관점</div>
            <div style="color:var(--text-secondary); font-size:0.75rem;">웨이퍼 런간(Run-to-Run) 산포 1.2nm 이하 균일도 제어</div>
          </div>
          <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:0.8125rem;">
            <div style="font-weight:700; margin-bottom:4px; color:#d97706;">🔬 공정 제어 관점</div>
            <div style="color:var(--text-secondary); font-size:0.75rem;">OES 발광 분광 기반 실시간 종말점(EPD) 판정 집행</div>
          </div>
          <div style="background:var(--bg-surface-2); padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:0.8125rem;">
            <div style="font-weight:700; margin-bottom:4px; color:#7c3aed;">📦 첨단 패키징 관점</div>
            <div style="color:var(--text-secondary); font-size:0.75rem;">고종횡비 관통전극(TSV) 식각 수직도 89.5° 이상 유지</div>
          </div>
        </div>
      </div>
    `;

    const conceptNameEl = document.getElementById("preview-modal-concept-name");
    if (conceptNameEl) conceptNameEl.textContent = item.conceptTitle.split("(")[0];
    dom.wikiPreviewContent.innerHTML = previewHtml;

    // 초기 하이라이트 상태 동기화
    if (dom.togglePreviewDiffHighlight) {
      if (dom.togglePreviewDiffHighlight.checked) {
        dom.wikiPreviewContent.classList.remove("preview-diff-plain");
      } else {
        dom.wikiPreviewContent.classList.add("preview-diff-plain");
      }
    }

    dom.modalWikiPreview.classList.add("open");
  }

  function closeWikiPreviewModal() {
    dom.modalWikiPreview?.classList.remove("open");
  }

  // 승인 집행 공통 함수
  function executeReviewApproval() {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    if (!item || item.status === "게시 완료") return;

    item.status = "게시 완료";

    const targetConceptId = item.conceptId || "dry-etch";
    if (WikiStore.concepts[targetConceptId]) {
      const c = WikiStore.concepts[targetConceptId];
      c.version = "v1.3 (신규 승인 반영)";
      c.summary = item.aiMergedDraft;
      c.definition = (item.aiMergedDraft.split("###")[1] || item.aiMergedDraft).slice(0, 300) + "...";
      c.lastReviewed = `2026.10.15 (인간 전문가 HITL 검토 승인 완료)`;
    }

    renderReviewQueue();
    closeWikiPreviewModal();

    // 1번 위키 탭 바로가기 버튼 노출 및 바인딩
    if (dom.gotoWikiBtn) {
      dom.gotoWikiBtn.style.display = "inline-flex";
      dom.gotoWikiBtn.innerHTML = `📖 1번 위키 탭에서 갱신된 v1.3 확인 ➔`;
      dom.gotoWikiBtn.onclick = () => {
        window.selectWikiConcept(targetConceptId);
        showToast(`'${item.conceptTitle}' 문서가 v1.3으로 갱신되었습니다! 본문을 확인하세요.`, "success");
        const headerEl = document.querySelector(".concept-header");
        if (headerEl) {
          headerEl.style.transition = "background 0.5s ease";
          headerEl.style.background = "rgba(16, 185, 129, 0.12)";
          setTimeout(() => { headerEl.style.background = ""; }, 2500);
        }
      };
    }

    // Transitions.dev 성취 체크마크 모달 표시
    if (dom.approvalSuccessModal) {
      if (dom.approvalSuccessMsg) {
        dom.approvalSuccessMsg.textContent = `'${item.conceptTitle.split("(")[0]}' 문서가 v1.3으로 성공적으로 승인되어 1번 공용 위키 및 온톨로지 코어에 정식 반영되었습니다.`;
      }
      dom.approvalSuccessModal.classList.add("open");
      const icon = dom.approvalSuccessModal.querySelector(".success-check-icon");
      if (icon) {
        icon.classList.remove("active");
        void icon.offsetWidth;
        icon.classList.add("active");
      }
    }

    showToast(`'${item.conceptTitle.split("(")[0]}' 문서가 v1.3으로 공용 위키 및 온톨로지 코어에 정식 반영되었습니다!`, "success");
  }

  // 미리보기 및 승인 이벤트 바인딩
  dom.btnPreviewWiki?.addEventListener("click", openWikiPreviewModal);
  dom.btnQuickPreviewDiff?.addEventListener("click", openWikiPreviewModal);
  dom.closeWikiPreviewBtn?.addEventListener("click", closeWikiPreviewModal);
  dom.btnPreviewCancel?.addEventListener("click", closeWikiPreviewModal);

  dom.btnPreviewToEditor?.addEventListener("click", () => {
    closeWikiPreviewModal();
    if (dom.reviewEditorContainer && dom.diffDraftContainer) {
      const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
      dom.reviewEditorContainer.style.display = "flex";
      dom.reviewEditorContainer.classList.remove("fade-slide-up");
      void dom.reviewEditorContainer.offsetWidth;
      dom.reviewEditorContainer.classList.add("fade-slide-up");
      dom.diffDraftContainer.style.display = "none";
      if (item && dom.reviewEditorInput) {
        dom.reviewEditorInput.value = item.aiMergedDraft;
        dom.reviewEditorInput.focus();
      }
      if (dom.btnToggleEditor) dom.btnToggleEditor.textContent = "👁️ 비교 뷰로 돌아가기";
    }
  });

  dom.btnPreviewConfirmApprove?.addEventListener("click", executeReviewApproval);
  dom.approveReviewBtn?.addEventListener("click", executeReviewApproval);

  dom.togglePreviewDiffHighlight?.addEventListener("change", (e) => {
    if (!dom.wikiPreviewContent) return;
    if (e.target.checked) {
      dom.wikiPreviewContent.classList.remove("preview-diff-plain");
    } else {
      dom.wikiPreviewContent.classList.add("preview-diff-plain");
    }
  });

  // 승인 완료 모달 내 버튼 핸들러
  dom.btnSuccessStayReview?.addEventListener("click", () => {
    dom.approvalSuccessModal?.classList.remove("open");
  });

  dom.btnSuccessGotoWiki?.addEventListener("click", () => {
    const item = WikiStore.reviewQueue.find(r => r.id === state.selectedReviewId);
    const targetConceptId = item ? (item.conceptId || "dry-etch") : "dry-etch";
    dom.approvalSuccessModal?.classList.remove("open");
    window.selectWikiConcept(targetConceptId);
    showToast(`'${item?.conceptTitle || ''}' 문서가 v1.3으로 갱신되었습니다! 본문을 확인하세요.`, "success");
    const headerEl = document.querySelector(".concept-header");
    if (headerEl) {
      headerEl.style.transition = "background 0.5s ease";
      headerEl.style.background = "rgba(16, 185, 129, 0.12)";
      setTimeout(() => { headerEl.style.background = ""; }, 2500);
    }
  });

  // 배경 클릭 및 ESC 키 닫기
  dom.modalWikiPreview?.addEventListener("click", (e) => {
    if (e.target === dom.modalWikiPreview) closeWikiPreviewModal();
  });
  dom.approvalSuccessModal?.addEventListener("click", (e) => {
    if (e.target === dom.approvalSuccessModal) dom.approvalSuccessModal.classList.remove("open");
  });

  // ── 조사 작업실 사이드바 최근 발굴 로그 렌더링 ──
  function renderDiscoveryLogs() {
    const listEl = document.getElementById("sidebar-discovery-log-list");
    const countBadge = document.getElementById("discovery-log-count-badge");
    if (!listEl) return;

    const logs = WikiStore.discoveryLogs || [];
    if (countBadge) countBadge.textContent = `${logs.length}건 기록`;

    if (logs.length === 0) {
      listEl.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted); padding:10px; text-align:center;">발굴 이력이 없습니다.</div>`;
      return;
    }

    listEl.innerHTML = logs.map(log => `
      <div class="discovery-log-item" data-log-id="${log.id}" data-review-id="${log.reviewId || ''}" title="클릭 시 검토 센터(HITL)로 이동하여 확인">
        <div class="discovery-log-title">${log.title}</div>
        <div style="font-size:0.6875rem; color:var(--accent-primary); margin-bottom:4px; font-weight:600;">
          📚 ${log.sourcesSummary}
        </div>
        <div class="discovery-log-meta">
          <span class="concept-badge ${log.status.includes('승인') ? 'badge-verified' : 'badge-level-1'}" style="font-size:0.625rem; padding:1px 5px;">
            ${log.status}
          </span>
          <span>${log.date}</span>
        </div>
      </div>
    `).join("");

    listEl.querySelectorAll(".discovery-log-item").forEach(item => {
      item.addEventListener("click", () => {
        const revId = item.dataset.reviewId;
        if (revId) {
          state.selectedReviewId = revId;
          setWorkspace("review");
          showToast(`'${item.querySelector(".discovery-log-title")?.textContent}' 검토 화면으로 이동했습니다.`, "info");
        } else {
          showToast("이미 온톨로지에 승인 반영 완료된 항목입니다.", "info");
        }
      });
    });
  }

  // ── 10. 조사 작업실 (간소화 및 대화형 신규 출처 발굴 & 검토 센터 즉시 이관) ──
  function renderInvestigationClarifier(query = "") {
    const q = (query || dom.investigationQueryInput?.value || "").trim();
    if (!q) {
      showToast("발굴할 공정 기술이나 표준 규격을 입력해 주세요 (예: 극저온 친환경 가스, 유리기판 TGV, High-NA 펠리클).", "info");
      dom.investigationQueryInput?.focus();
      return;
    }

    if (!dom.investigationDialogueArea) return;
    dom.investigationDialogueArea.style.display = "block";
    dom.seedingResultArea.innerHTML = "";

    // 검색어 키워드별 추천 공식 출처 팩 리스트
    let sourcesList = [];
    const lower = q.toLowerCase();

    if (lower.includes("가스") || lower.includes("친환경") || lower.includes("cryo") || lower.includes("극저온") || lower.includes("식각")) {
      sourcesList = [
        {
          id: "src-lam-cryo",
          name: "Lam Research 극저온 공정 백서 (2026)",
          type: "공식 기업 백서",
          badgeClass: "badge-verified",
          desc: "-60℃ 저GWP 대체 불소 가스(CF3I/C3F6FB) 플라즈마 해리 특성 및 Si/SiO2 고선택비 식각율 실측 데이터"
        },
        {
          id: "src-ieee-esg",
          name: "IEEE Transactions on Semicond. (Tier 3 학술)",
          type: "Tier 3 학술 논문",
          badgeClass: "badge-scale-1",
          desc: "온실가스 배출량 90% 저감형 차세대 식각 가스의 3D 낸드 300단 초고종횡비 채널홀 수직도 및 부산물 분석"
        },
        {
          id: "src-semi-s23",
          name: "SEMI S23 / ESG 국제 표준 규격 (2026)",
          type: "SEMI 국제 표준",
          badgeClass: "badge-scale-5",
          desc: "반도체 팹 Net-Zero 달성을 위한 대체 가스 배기 라인 히팅(120℃) 결로 방지 및 안전 운영 프로토콜"
        }
      ];
    } else if (lower.includes("유리기판") || lower.includes("tgv") || lower.includes("패키징")) {
      sourcesList = [
        {
          id: "src-intel-glass",
          name: "Intel 패키징 백서 (Whitepaper 2026)",
          type: "공식 기업 백서",
          badgeClass: "badge-verified",
          desc: "유리기판 로드맵, 열팽창계수(CTE) 매칭 및 TGV 비아 홀 피치 스펙 (실리콘 인터포저 대체)"
        },
        {
          id: "src-ieee-ectc",
          name: "IEEE ECTC 2026 초청 논문 (Tier 3 학술)",
          type: "Tier 3 학술 논문",
          badgeClass: "badge-scale-1",
          desc: "레이저 유도 화학 식각(LIDE) 크랙 최소화 및 10μm 미만 초미세 관통홀 구리 도금 갭필 물성"
        },
        {
          id: "src-semi-glass",
          name: "SEMI 국제 표준 규격 (Draft 2026)",
          type: "SEMI 국제 표준",
          badgeClass: "badge-scale-5",
          desc: "대면적(510×515mm) 패널 글래스 기판 자동 이송 및 진공 척 파티클 제어 표준 규격"
        }
      ];
    } else if (lower.includes("펠리클") || lower.includes("high-na") || lower.includes("euv") || lower.includes("노광")) {
      sourcesList = [
        {
          id: "src-asml-cnt",
          name: "ASML High-NA EUV 백서 (2026)",
          type: "공식 기업 백서",
          badgeClass: "badge-verified",
          desc: "탄소나노튜브(CNT) 펠리클 92% 투과율 및 500W+ 초고출력 EUV 광원 내열성/수명 검증 데이터"
        },
        {
          id: "src-imec-pattern",
          name: "imec Advanced Patterning 연구 논문 (Tier 3)",
          type: "Tier 3 학술 연구",
          badgeClass: "badge-scale-1",
          desc: "High-NA 아나모픽 노광 시 무펠리클 vs CNT 펠리클 결함 밀도 및 마스크 오염 제어 대조"
        },
        {
          id: "src-semi-p48",
          name: "SEMI P48 노광 마스크 표준 (2026)",
          type: "SEMI 국제 표준",
          badgeClass: "badge-scale-5",
          desc: "High-NA 0.55NA 아나모픽 마스크 보호 및 펠리클 자동 마운팅/디마운팅 챔버 규격"
        }
      ];
    } else {
      sourcesList = [
        {
          id: "src-global-wp",
          name: `글로벌 선도사 공식 기술 백서 (${q})`,
          type: "공식 기업 백서",
          badgeClass: "badge-verified",
          desc: `${q} 관련 단위 공정 양산 레시피 및 장비 챔버 운전 조건 공식 발표 자료`
        },
        {
          id: "src-ieee-trans",
          name: `IEEE / MDPI 반도체 제조 학술 논문 (Tier 3)`,
          type: "Tier 3 학술 논문",
          badgeClass: "badge-scale-1",
          desc: `${q} 관련 물리적 한계 메커니즘 및 차세대 소자 패턴 수율 평가 데이터`
        },
        {
          id: "src-semi-std",
          name: `SEMI 국제 산업 표준 규격 (2026)`,
          type: "SEMI 국제 표준",
          badgeClass: "badge-scale-5",
          desc: `${q} 관련 팹 인프라 규격 및 품질 관리 프로토콜`
        }
      ];
    }

    dom.investigationDialogueArea.innerHTML = `
      <div class="ai-dialogue-stream fade-slide-up" style="margin-top:0;">
        <div class="dialogue-bubble dialogue-user-bubble">
          <strong>🔍 발굴 요청:</strong> "${q}"
        </div>
        <div class="dialogue-bubble dialogue-agent-bubble">
          <div style="font-weight:700; color:var(--accent-primary); margin-bottom:4px;">🤖 온톨로지 에이전트 공식 출처 종합 안내</div>
          <p style="margin-bottom:10px;">
            <strong>'${q}'</strong> 관련 최신 기술 자료를 에이전트가 종합 교차 검증할 수 있도록 <strong>${sourcesList.length}대 공식/학술 출처 팩</strong>을 추천합니다. 탐색할 자료원을 선택해 주세요.
          </p>

          <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 2px; border-bottom:1px solid var(--border-color); margin-bottom:10px;">
            <label style="font-size:0.8125rem; font-weight:700; color:var(--text-primary); cursor:pointer; display:flex; align-items:center; gap:6px;">
              <input type="checkbox" id="inv-select-all-sources" checked style="cursor:pointer;" />
              전체 선택 (<span id="inv-selected-count">${sourcesList.length}</span>/${sourcesList.length}개 선택됨)
            </label>
            <span style="font-size:0.75rem; color:var(--text-muted);">복수 선택 시 에이전트가 교차 분석을 수행합니다</span>
          </div>

          <div class="clarifier-options-grid" id="inv-sources-grid">
            ${sourcesList.map((src, i) => `
              <label class="investigation-source-option" style="cursor:pointer; display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
                <div style="display:flex; align-items:flex-start; gap:10px;">
                  <input type="checkbox" class="inv-source-cb" data-source-name="${src.name}" checked style="margin-top:3px; cursor:pointer;" />
                  <div>
                    <div style="font-weight:700; font-size:0.875rem; color:var(--text-primary);">${i + 1}. ${src.name}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${src.desc}</div>
                  </div>
                </div>
                <span class="concept-badge ${src.badgeClass}" style="font-size:0.6875rem; flex-shrink:0;">${src.type}</span>
              </label>
            `).join("")}
          </div>

          <div style="margin-top:14px; display:flex; justify-content:flex-end;">
            <button type="button" class="cand-action-btn cand-btn-primary" id="btn-run-multi-sources" style="padding:10px 22px; font-weight:700;">
              🚀 선택한 자료원 (<span id="btn-selected-count-label">${sourcesList.length}</span>개) 종합 발굴 시작 ➔
            </button>
          </div>
        </div>
      </div>
    `;

    const selectAllCb = document.getElementById("inv-select-all-sources");
    const sourceCbs = dom.investigationDialogueArea.querySelectorAll(".inv-source-cb");
    const countSpan = document.getElementById("inv-selected-count");
    const btnCountSpan = document.getElementById("btn-selected-count-label");
    const runBtn = document.getElementById("btn-run-multi-sources");

    function updateCounts() {
      const checkedBoxes = Array.from(sourceCbs).filter(cb => cb.checked);
      const count = checkedBoxes.length;
      if (countSpan) countSpan.textContent = count;
      if (btnCountSpan) btnCountSpan.textContent = count;
      if (selectAllCb) selectAllCb.checked = (count === sourceCbs.length);
      if (runBtn) {
        runBtn.disabled = (count === 0);
        runBtn.style.opacity = (count === 0) ? "0.5" : "1";
      }
    }

    selectAllCb?.addEventListener("change", (e) => {
      sourceCbs.forEach(cb => { cb.checked = e.target.checked; });
      updateCounts();
    });

    sourceCbs.forEach(cb => {
      cb.addEventListener("change", updateCounts);
    });

    runBtn?.addEventListener("click", () => {
      const selectedSources = Array.from(sourceCbs).filter(cb => cb.checked).map(cb => cb.dataset.sourceName);
      if (selectedSources.length === 0) {
        showToast("탐색할 공식 출처를 1개 이상 선택해 주세요.", "warning");
        return;
      }
      triggerMultiSourceInvestigation(q, selectedSources);
    });
  }

  async function triggerMultiSourceInvestigation(topic, selectedSources) {
    if (!dom.seedingResultArea) return;

    dom.seedingResultArea.innerHTML = `
      <div class="reasoning-stream-box fade-slide-up" style="padding:16px;">
        <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <span>에이전트가 선택된 ${selectedSources.length}대 공식 출처 팩(${selectedSources.map(s => s.split('(')[0].trim()).join(', ')}) 전수 스캔 및 신규 온톨로지 초안 자동 합성 중...</span>
      </div>
    `;

    try {
      const draftResult = await window.OntologyAgentCore.synthesizeInvestigationDraft(topic, selectedSources);

      const cand1 = {
        id: `rev-cand-${Date.now()}-1`,
        conceptId: "dry-etch",
        conceptTitle: draftResult.conceptTitle || `${topic} 신규 규격 초안`,
        proposalsCount: selectedSources.length,
        reviewType: "조사 작업실 신규 발굴 (공식 출처 종합 합성)",
        author: `조사 에이전트 (${selectedSources.length}대 출처)`,
        date: "방금 전",
        status: "검토 대기",
        currentContent: "반도체 단위 공정 표준 규격 및 물성 기준선.",
        aiMergedDraft: draftResult.draftContent || `### ${topic}\n공식 출처 기반 신규 온톨로지 초안`,
        diffAdded: `[신규 발굴 초안] ${draftResult.draftContent?.slice(0, 150) || topic}...`,
        integrityCheck: {
          evidenceMatch: `${selectedSources[0]?.split('(')[0] || '공식 백서'} 교차 검증 (100%)`,
          ontologyConflict: "온톨로지 충돌 없음",
          impactScope: "식각 및 첨단 패키징 1건"
        }
      };

      const cand2 = {
        id: `rev-cand-${Date.now()}-2`,
        conceptId: "ees-rms",
        conceptTitle: `${topic} 팹 인프라 및 안전 통제 규격`,
        proposalsCount: 1,
        reviewType: "조사 작업실 신규 발굴 (SEMI 표준 연계)",
        author: `조사 에이전트 (${selectedSources.length}대 출처)`,
        date: "방금 전",
        status: "검토 대기",
        currentContent: "팹 운영 및 가스 배기 시스템 기준 규격.",
        aiMergedDraft: `팹 운영 규격: ${topic} 적용 라인에 대한 배기 온도 및 인터락 안전 관리 지침이 보강되었습니다.`,
        diffAdded: `${topic} 적용 라인에 대한 배기 온도 및 인터락 안전 관리 지침이 보강되었습니다.`,
        integrityCheck: {
          evidenceMatch: "SEMI 국제 표준 부합 (100%)",
          ontologyConflict: "온톨로지 충돌 없음",
          impactScope: "팹 인프라 1건"
        }
      };

      // 두 후보를 즉시 검토 센터 큐에 자동 등록!
      WikiStore.reviewQueue.unshift(cand2);
      WikiStore.reviewQueue.unshift(cand1);
      state.selectedReviewId = cand1.id;
      renderReviewQueue();

      // 사이드바 최근 발굴 로그에 즉시 반영
      WikiStore.discoveryLogs = WikiStore.discoveryLogs || [];
      WikiStore.discoveryLogs.unshift({
        id: `disc-${Date.now()}`,
        topic: topic,
        title: cand1.conceptTitle,
        sourcesCount: selectedSources.length,
        sourcesSummary: `${selectedSources[0]?.split('(')[0]?.trim()} 외 ${selectedSources.length - 1}건`,
        date: "방금 전",
        reviewId: cand1.id,
        status: "검토 대기",
        badgeClass: "badge-verified"
      });
      renderDiscoveryLogs();

      // 조사 작업실 결과 카드 렌더링
      dom.seedingResultArea.innerHTML = `
        <div class="investigation-complete-card">
          <div style="display:flex; align-items:center; gap:12px;">
            <svg class="success-check-icon active" viewBox="0 0 24 24" style="flex-shrink:0;">
              <path class="success-check-path" d="M5 13l4 4L19 7"></path>
            </svg>
            <div>
              <strong style="color:var(--accent-success); font-size:1.0625rem;">✔ 선택한 ${selectedSources.length}대 공식 출처 기반 신규 온톨로지 초안 합성 완료!</strong>
              <div style="font-size:0.8125rem; color:var(--text-secondary); margin-top:2px;">
                도출된 신규 지식 <strong>2건</strong>이 사람의 검토 및 온톨로지 승인을 위해 <strong>3번 개념 검토 센터(HITL) 큐에 자동 등록</strong>되었습니다.
              </div>
            </div>
          </div>

          <div style="margin-top:14px; padding:12px 16px; background:var(--bg-surface-2); border-radius:8px; font-size:0.8125rem; line-height:1.6;">
            <div>• <strong>[신규 지식 1]</strong> ${cand1.conceptTitle} <span class="concept-badge badge-scale-3" style="font-size:0.625rem;">검토 대기</span></div>
            <div style="margin-top:4px;">• <strong>[신규 지식 2]</strong> ${cand2.conceptTitle} <span class="concept-badge badge-scale-5" style="font-size:0.625rem;">검토 대기</span></div>
          </div>

          <div style="margin-top:14px; display:flex; justify-content:flex-end;">
            <button type="button" class="cand-action-btn cand-btn-primary" id="btn-goto-review-from-inv" style="padding:10px 20px; font-weight:700;">
              ✍️ 3번 개념 검토 센터로 이동하여 확인 및 편집하기 ➔
            </button>
          </div>
        </div>
      `;

      document.getElementById("btn-goto-review-from-inv")?.addEventListener("click", () => {
        setWorkspace("review");
        showToast("방금 발굴된 신규 개념 검토 항목으로 이동했습니다.", "info");
      });

      showToast(`선택한 출처에서 발굴된 2건의 지식이 3번 검토 센터 큐에 자동 등록되었습니다!`, "success");
    } catch (err) {
      console.warn("Investigation synthesis error:", err);
      showToast("초안 합성 중 오류가 발생했습니다.", "warning");
    }
  }

  dom.btnInvestigateClarify?.addEventListener("click", () => {
    renderInvestigationClarifier();
  });

  dom.investigationQueryInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      renderInvestigationClarifier();
    }
  });

  document.querySelectorAll(".inv-sample-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      if (dom.investigationQueryInput) dom.investigationQueryInput.value = q;
      renderInvestigationClarifier(q);
    });
  });

  // ── 0. 런타임 모드 세그먼트 스위처 & 타 프로젝트 API 허브 (Transitions.dev 표준 모달 & 비식별화) ──
  function initRuntimeModeAndApiHub() {
    let isGoogleMaskRevealed = false;
    let isOpenAIMaskRevealed = false;
    let isEditingKeys = false;

    // A. Transitions.dev 슬라이딩 세그먼트 스위처 인디케이터 동기화
    function updateModeSwitcherUI(mode) {
      if (!dom.runtimeModeSwitcher) return;
      const targetBtn = mode === "live" ? dom.btnModeLive : dom.btnModeMock;
      const otherBtn = mode === "live" ? dom.btnModeMock : dom.btnModeLive;
      if (!targetBtn || !otherBtn) return;

      targetBtn.classList.add("active");
      otherBtn.classList.remove("active");

      if (dom.runtimeModeIndicator) {
        requestAnimationFrame(() => {
          dom.runtimeModeIndicator.style.width = `${targetBtn.offsetWidth}px`;
          dom.runtimeModeIndicator.style.transform = `translateX(${targetBtn.offsetLeft}px)`;
        });
      }
    }

    // B. 비식별화 마스킹 헬퍼 (ontology-map-workspace 패턴)
    function maskKey(key) {
      if (!key) return "";
      const trimmed = key.trim();
      if (trimmed.length <= 10) return "••••••••••••";
      const prefix = trimmed.slice(0, 8);
      const suffix = trimmed.slice(-4);
      return `${prefix}••••••••••••••••${suffix}`;
    }

    // C. API Key 관리 섹션 UI 상태 렌더링
    function renderApiKeyBox() {
      if (!window.OntologyAgentCore) return;
      const keys = window.OntologyAgentCore.getKeys();

      // 1. Google Gemini Key
      if (keys.hasGoogle && !isEditingKeys) {
        if (dom.inputGoogleKey) dom.inputGoogleKey.style.display = "none";
        if (dom.labelGoogleMasked) {
          dom.labelGoogleMasked.style.display = "inline-flex";
          dom.labelGoogleMasked.textContent = isGoogleMaskRevealed ? keys.googleKey : maskKey(keys.googleKey);
        }
        if (dom.btnToggleGoogleMask) {
          dom.btnToggleGoogleMask.style.display = "inline-block";
          dom.btnToggleGoogleMask.textContent = isGoogleMaskRevealed ? "🙈 가리기" : "👁️ 보기";
        }
      } else {
        if (dom.inputGoogleKey) {
          dom.inputGoogleKey.style.display = "block";
          dom.inputGoogleKey.value = keys.googleKey || "";
        }
        if (dom.labelGoogleMasked) dom.labelGoogleMasked.style.display = "none";
        if (dom.btnToggleGoogleMask) dom.btnToggleGoogleMask.style.display = "none";
      }

      // 2. OpenAI Key
      if (keys.hasOpenAI && !isEditingKeys) {
        if (dom.inputOpenAIKey) dom.inputOpenAIKey.style.display = "none";
        if (dom.labelOpenAIMasked) {
          dom.labelOpenAIMasked.style.display = "inline-flex";
          dom.labelOpenAIMasked.textContent = isOpenAIMaskRevealed ? keys.openaiKey : maskKey(keys.openaiKey);
        }
        if (dom.btnToggleOpenAIMask) {
          dom.btnToggleOpenAIMask.style.display = "inline-block";
          dom.btnToggleOpenAIMask.textContent = isOpenAIMaskRevealed ? "🙈 가리기" : "👁️ 보기";
        }
      } else {
        if (dom.inputOpenAIKey) {
          dom.inputOpenAIKey.style.display = "block";
          dom.inputOpenAIKey.value = keys.openaiKey || "";
        }
        if (dom.labelOpenAIMasked) dom.labelOpenAIMasked.style.display = "none";
        if (dom.btnToggleOpenAIMask) dom.btnToggleOpenAIMask.style.display = "none";
      }

      // 3. 상태 뱃지 및 액션 버튼 제어
      const hasAnyKey = keys.hasGoogle || keys.hasOpenAI;
      if (hasAnyKey) {
        if (dom.hubKeyStatusBadge) {
          dom.hubKeyStatusBadge.className = "concept-badge badge-verified";
          dom.hubKeyStatusBadge.style.background = "#dcfce7";
          dom.hubKeyStatusBadge.style.color = "#15803d";
          dom.hubKeyStatusBadge.style.border = "1px solid #86efac";
          dom.hubKeyStatusBadge.textContent = "🟢 키 보관됨 (API 연동 가동)";
        }
        if (dom.btnEditKeys) dom.btnEditKeys.style.display = isEditingKeys ? "none" : "inline-block";
        if (dom.btnDeleteKeys) dom.btnDeleteKeys.style.display = "inline-block";
        if (dom.btnSaveKeysHub) dom.btnSaveKeysHub.style.display = isEditingKeys ? "inline-block" : "none";
        if (dom.keySecurityNote) {
          dom.keySecurityNote.innerHTML = isEditingKeys
            ? "✏️ 키 수정 후 [저장] 버튼을 누르면 비식별화가 즉시 재적용됩니다."
            : "🛡️ 브라우저 sessionStorage에 안전하게 비식별화 보관 중입니다. (외부 유출 절대 차단)";
        }
      } else {
        if (dom.hubKeyStatusBadge) {
          dom.hubKeyStatusBadge.className = "concept-badge";
          dom.hubKeyStatusBadge.style.background = "#fef3c7";
          dom.hubKeyStatusBadge.style.color = "#b45309";
          dom.hubKeyStatusBadge.style.border = "1px solid #fde68a";
          dom.hubKeyStatusBadge.textContent = "⚠️ 키 미등록 (MOCK 가동 중)";
        }
        if (dom.btnEditKeys) dom.btnEditKeys.style.display = "none";
        if (dom.btnDeleteKeys) dom.btnDeleteKeys.style.display = "none";
        if (dom.btnSaveKeysHub) dom.btnSaveKeysHub.style.display = "inline-block";
        if (dom.keySecurityNote) {
          dom.keySecurityNote.innerHTML = "🛡️ 키 저장 즉시 비식별화 마스킹 처리되며 타 프로젝트 API 연동이 활성화됩니다.";
        }
      }
    }

    // D. Transitions.dev 모달 제어 (.modal-overlay.open 표준 준수)
    function openHeadlessModal() {
      if (!dom.headlessApiModal) return;
      renderApiKeyBox();
      dom.headlessApiModal.classList.add("open");
    }

    function closeHeadlessModal() {
      if (!dom.headlessApiModal) return;
      dom.headlessApiModal.classList.remove("open");
      isEditingKeys = false;
      isGoogleMaskRevealed = false;
      isOpenAIMaskRevealed = false;

      // 닫힐 때 실제 저장된 키가 없으면 스위처 인디케이터를 안전하게 MOCK으로 복귀
      const keys = window.OntologyAgentCore?.getKeys();
      const curMode = window.OntologyAgentCore?.getMode();
      if (!keys?.hasGoogle && !keys?.hasOpenAI) {
        window.OntologyAgentCore?.setMode("mock");
        updateModeSwitcherUI("mock");
      } else {
        updateModeSwitcherUI(curMode);
      }
    }

    // E. 탑바 슬라이딩 스위처 이벤트 바인딩
    dom.btnModeMock?.addEventListener("click", () => {
      window.OntologyAgentCore?.setMode("mock");
      updateModeSwitcherUI("mock");
      if (dom.headlessApiModal?.classList.contains("open")) {
        closeHeadlessModal();
      }
      showToast("⚡ MOCK 모드가 유지됩니다. (37개 온톨로지 데모 데이터 보존, 초고속 인메모리)", "info");
    });

    dom.btnModeLive?.addEventListener("click", () => {
      openHeadlessModal();
      updateModeSwitcherUI("live");
      const keys = window.OntologyAgentCore?.getKeys();
      if (keys?.hasGoogle || keys?.hasOpenAI) {
        window.OntologyAgentCore?.setMode("live");
        showToast("🔌 타 프로젝트 API 연동 모드가 가동 중입니다. (키 비식별화 보관됨)", "success");
      } else {
        // 최초 클릭 시 키 입력 필드로 포커스 이동
        setTimeout(() => {
          if (dom.inputOpenAIKey && dom.inputOpenAIKey.style.display !== "none") {
            dom.inputOpenAIKey.focus();
          } else if (dom.inputGoogleKey && dom.inputGoogleKey.style.display !== "none") {
            dom.inputGoogleKey.focus();
          }
        }, 150);
        showToast("🔑 타 프로젝트 연동을 위해 상용 AI API Key를 등록하거나 아래 시뮬레이터를 테스트하세요.", "info");
      }
    });

    // F. 모달 닫기 이벤트들 (Transitions.dev 표준: X버튼, 닫기버튼, 배경클릭, Esc키)
    dom.headlessModalClose?.addEventListener("click", closeHeadlessModal);
    dom.btnCloseHeadlessModal?.addEventListener("click", closeHeadlessModal);
    dom.headlessApiModal?.addEventListener("click", (e) => {
      if (e.target === dom.headlessApiModal) closeHeadlessModal();
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && dom.headlessApiModal?.classList.contains("open")) {
        closeHeadlessModal();
      }
    });

    // G. API Key 비식별화/보기/수정/삭제 이벤트
    dom.btnToggleGoogleMask?.addEventListener("click", () => {
      isGoogleMaskRevealed = !isGoogleMaskRevealed;
      renderApiKeyBox();
    });

    dom.btnToggleOpenAIMask?.addEventListener("click", () => {
      isOpenAIMaskRevealed = !isOpenAIMaskRevealed;
      renderApiKeyBox();
    });

    dom.btnEditKeys?.addEventListener("click", () => {
      isEditingKeys = true;
      renderApiKeyBox();
      if (dom.inputOpenAIKey) dom.inputOpenAIKey.focus();
    });

    dom.btnDeleteKeys?.addEventListener("click", () => {
      if (confirm("세션에 저장된 모든 API Key를 삭제하고 ⚡ MOCK 모드로 복귀하시겠습니까?")) {
        window.OntologyAgentCore?.clearKeys();
        isEditingKeys = false;
        isGoogleMaskRevealed = false;
        isOpenAIMaskRevealed = false;
        renderApiKeyBox();
        updateModeSwitcherUI("mock");
        showToast("API Key가 브라우저 세션에서 안전하게 삭제되었으며 ⚡ MOCK 모드로 복귀했습니다.", "info");
      }
    });

    dom.btnSaveKeysHub?.addEventListener("click", () => {
      if (!window.OntologyAgentCore) return;
      const gKey = dom.inputGoogleKey?.value.trim() || "";
      const oKey = dom.inputOpenAIKey?.value.trim() || "";

      if (!gKey && !oKey) {
        showToast("Google 또는 OpenAI API Key를 하나 이상 입력해주세요.", "warning");
        return;
      }

      window.OntologyAgentCore.saveKeys(gKey, oKey, true);
      isEditingKeys = false;
      isGoogleMaskRevealed = false;
      isOpenAIMaskRevealed = false;
      renderApiKeyBox();
      updateModeSwitcherUI("live");
      showToast("🎉 API Key가 비식별화되어 안전하게 저장되었습니다! 타 프로젝트 API 연동이 활성화되었습니다.", "success");
    });

    // H. 외부 호출 시뮬레이터 로직 (Phase 2 연계)
    document.querySelectorAll(".headless-preset-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const client = chip.dataset.client;
        const query = chip.dataset.query;
        if (dom.headlessClientSelect && client) dom.headlessClientSelect.value = client;
        if (dom.headlessQueryInput && query) dom.headlessQueryInput.value = query;
      });
    });

    // 결과 탭 전환 (Transitions.dev)
    const tabBtns = document.querySelectorAll(".headless-tab-btn");
    const panes = {
      json: document.getElementById("pane-headless-json"),
      curl: document.getElementById("pane-headless-curl"),
      trace: document.getElementById("pane-headless-trace")
    };

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        tabBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const tab = btn.dataset.tab;
        Object.entries(panes).forEach(([k, p]) => {
          if (p) p.style.display = (k === tab) ? "block" : "none";
        });
      });
    });

    dom.btnCopyJson?.addEventListener("click", () => {
      if (dom.codeHeadlessJson?.textContent) {
        navigator.clipboard.writeText(dom.codeHeadlessJson.textContent);
        showToast("정형 JSON 응답이 클립보드에 복사되었습니다.", "info");
      }
    });

    dom.btnCopyCurl?.addEventListener("click", () => {
      if (dom.codeHeadlessCurl?.textContent) {
        navigator.clipboard.writeText(dom.codeHeadlessCurl.textContent);
        showToast("cURL 호출 명령어가 클립보드에 복사되었습니다.", "info");
      }
    });

    dom.btnRunHeadlessQuery?.addEventListener("click", async () => {
      const query = dom.headlessQueryInput?.value.trim();
      if (!query) {
        alert("기술 질의 내용을 입력하거나 상단 프리셋을 선택하세요.");
        return;
      }

      const callerSystem = dom.headlessClientSelect?.value || "custom-api";
      const scaleFilters = Array.from(document.querySelectorAll(".headless-scale-cb:checked")).map(cb => cb.value);
      const bypassMultimodal = !dom.headlessMultimodalCb?.checked;

      const originalText = dom.btnRunHeadlessQuery.textContent;
      dom.btnRunHeadlessQuery.textContent = "⏳ 온톨로지 하네스 추론 중...";
      dom.btnRunHeadlessQuery.disabled = true;

      try {
        const result = await window.OntologyAgentCore.queryHeadlessApi({
          query,
          callerSystem,
          scaleFilters,
          bypassMultimodal
        });

        if (dom.headlessResultsContainer) dom.headlessResultsContainer.style.display = "block";
        if (dom.codeHeadlessJson) dom.codeHeadlessJson.textContent = JSON.stringify(result.responseJson, null, 2);
        if (dom.codeHeadlessCurl) dom.codeHeadlessCurl.textContent = result.curlCommand;
        if (dom.headlessElapsedBadge) dom.headlessElapsedBadge.textContent = `소요: ${result.elapsed}ms`;

        if (dom.listHeadlessTrace) {
          dom.listHeadlessTrace.innerHTML = result.traceSteps.map(step => {
            const isWarning = step.includes("⚠️") || step.includes("공백");
            const color = isWarning ? "#b45309" : "var(--text-secondary)";
            return `<div style="padding:4px 8px; background:var(--bg-surface); border-left:3px solid ${isWarning ? '#f59e0b' : 'var(--accent-primary)'}; border-radius:3px; color:${color}; font-size:0.75rem;">${step}</div>`;
          }).join("");
        }

        if (result.isKnowledgeGap) {
          if (dom.headlessGapBanner) dom.headlessGapBanner.style.display = "block";
          if (dom.headlessGapDesc) dom.headlessGapDesc.textContent = result.responseJson.message;

          if (dom.btnTransferToReview) {
            dom.btnTransferToReview.onclick = () => {
              const newCand = {
                id: `gap-${Date.now()}`,
                conceptTitle: query.slice(0, 30) + (query.length > 30 ? "..." : ""),
                facetId: "facet-process",
                levelId: "level-1",
                sourceAuthor: `외부 호출 [${callerSystem}] 지식 공백 감지`,
                regDate: "방금 전 (자동 발굴)",
                currentVersionText: "신규 미등록 (v0.0)",
                draftVersionText: "v1.0 (에이전트 권고 초안)",
                draftSnippet: `### ${query}\n본 기술 항목은 외부 시스템(${callerSystem}) 연동 중 온톨로지 공백으로 포착되어 전문가 검토 큐로 긴급 이관되었습니다. 공식 백서(SEMI/장비사) 기반 정식 온톨로지 편입이 필요합니다.`,
                integrityCheck: {
                  evidenceMatch: "신규 발굴 대상 (검증 필요)",
                  ontologyConflict: "신규 독립 노드 (충돌 없음)",
                  impactScope: "외부 백엔드 연동 1건"
                }
              };

              WikiStore.reviewQueue.unshift(newCand);
              state.selectedReviewId = newCand.id;
              renderReviewQueue();
              closeHeadlessModal();
              setWorkspace("review");
              showToast("지식 공백 항목이 3번 개념 검토 센터(HITL) 큐 최상단에 등록되었습니다!", "success");
            };
          }
        } else {
          if (dom.headlessGapBanner) dom.headlessGapBanner.style.display = "none";
        }

        showToast(`[${callerSystem}] 온톨로지 하네스 정형 인과 응답 수신 성공!`, "success");
      } catch (err) {
        alert("API 호출 중 오류 발생: " + err.message);
      } finally {
        dom.btnRunHeadlessQuery.textContent = originalText;
        dom.btnRunHeadlessQuery.disabled = false;
      }
    });

    // I. 최초 초기화 동기화
    const initialMode = window.OntologyAgentCore?.getMode() || "mock";
    updateModeSwitcherUI(initialMode);
    renderApiKeyBox();

    // 윈도우 리사이즈 시 인디케이터 위치 재계산
    window.addEventListener("resize", () => {
      const curMode = window.OntologyAgentCore?.getMode() || "mock";
      updateModeSwitcherUI(curMode);
    });
  }

  // ── 0-C. 위키 1번 탭 우측 하단 플로팅 챗봇 컨트롤러 ──
  function initFloatingChatWidget() {
    function formatChatMarkdown(text) {
      if (!text) return "";
      return text
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`([^`]+)`/g, "<code style='background:var(--bg-surface-2); padding:1px 5px; border-radius:3px; font-family:var(--font-mono); font-size:0.75rem;'>$1</code>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n/g, "<br>");
    }

    function syncChatContext() {
      const cur = WikiStore.concepts[state.currentConceptId] || WikiStore.concepts["dry-etch"];
      if (!cur) return;
      const title = cur.title || cur.name || state.currentConceptId;
      if (dom.chatContextBadge) {
        dom.chatContextBadge.textContent = `📌 ${title} (${cur.scaleId || 'Scale 3'})`;
      }
      if (dom.chatCurConceptName) {
        dom.chatCurConceptName.textContent = title;
      }
      if (dom.chatEngineModeBadge && window.OntologyAgentCore) {
        const mode = window.OntologyAgentCore.getMode();
        const isLive = window.OntologyAgentCore.isLiveAvailable();
        if (mode === "live" && isLive) {
          dom.chatEngineModeBadge.className = "concept-badge badge-verified";
          dom.chatEngineModeBadge.style.background = "#dcfce7";
          dom.chatEngineModeBadge.style.color = "#15803d";
          dom.chatEngineModeBadge.textContent = "🟢 Live (GPT-4o)";
        } else {
          dom.chatEngineModeBadge.className = "concept-badge badge-level-1";
          dom.chatEngineModeBadge.style.background = "";
          dom.chatEngineModeBadge.style.color = "";
          dom.chatEngineModeBadge.textContent = "⚡ MOCK";
        }
      }
    }

    // Transitions.dev 부드러운 개폐 토글 (.open 클래스 기반)
    function toggleChatWidget(open) {
      if (!dom.floatingChatWidget) return;
      const shouldOpen = open !== undefined ? open : !dom.floatingChatWidget.classList.contains("open");
      if (shouldOpen) {
        syncChatContext();
        dom.floatingChatWidget.classList.add("open");
        if (dom.floatingChatFab) dom.floatingChatFab.style.transform = "scale(0.92) translateY(2px)";
        setTimeout(() => dom.floatingChatInput?.focus(), 120);
      } else {
        dom.floatingChatWidget.classList.remove("open");
        if (dom.floatingChatFab) dom.floatingChatFab.style.transform = "";
      }
    }

    dom.floatingChatFab?.addEventListener("click", () => toggleChatWidget());
    dom.chatWidgetClose?.addEventListener("click", () => toggleChatWidget(false));

    // 메시지 렌더링 헬퍼
    function appendChatMessage(role, text) {
      if (!dom.floatingChatMessages) return;
      const msgDiv = document.createElement("div");
      msgDiv.className = `chat-msg chat-msg-${role}`;
      msgDiv.innerHTML = `<div class="chat-msg-bubble">${formatChatMarkdown(text)}</div>`;
      dom.floatingChatMessages.appendChild(msgDiv);
      dom.floatingChatMessages.scrollTop = dom.floatingChatMessages.scrollHeight;
      return msgDiv;
    }

    // 질문 발송 처리
    async function sendChatMessage(userText) {
      const query = (userText || dom.floatingChatInput?.value || "").trim();
      if (!query) return;

      appendChatMessage("user", query);
      if (dom.floatingChatInput) dom.floatingChatInput.value = "";

      // Transitions.dev 추론 스트림 & 매트릭스 도트 스피너 적용
      const loadingMsg = appendChatMessage(
        "agent",
        `<div class="reasoning-stream-box" style="margin:2px 0; padding:6px 10px; background:transparent; border:none; color:inherit;">
          <div class="matrix-dot-spinner"><span></span><span></span><span></span><span></span><span></span><span></span></div>
          <span>현재 온톨로지 문서의 물리 인과 사슬을 분석 중입니다...</span>
        </div>`
      );

      try {
        const res = await window.OntologyAgentCore.askContextualChat({
          conceptId: state.currentConceptId,
          userMessage: query,
          currentPerspective: state.currentPerspective
        });

        if (loadingMsg) {
          const bubble = loadingMsg.querySelector(".chat-msg-bubble");
          if (bubble) {
            bubble.innerHTML = formatChatMarkdown(res.answer);
          }
        }
      } catch (err) {
        if (loadingMsg) {
          const bubble = loadingMsg.querySelector(".chat-msg-bubble");
          if (bubble) bubble.textContent = "답변 생성 실패: " + err.message;
        }
      }
      if (dom.floatingChatMessages) {
        dom.floatingChatMessages.scrollTop = dom.floatingChatMessages.scrollHeight;
      }
    }

    dom.floatingChatSendBtn?.addEventListener("click", () => sendChatMessage());
    dom.floatingChatInput?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendChatMessage();
      }
    });

    // 퀵 질문 칩 클릭
    document.querySelectorAll(".chat-quick-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const q = chip.dataset.q;
        if (q) sendChatMessage(q);
      });
    });

    // 전역 개념 변경 시 컨텍스트 실시간 동기화 등록
    window.addEventListener("conceptChanged", () => {
      syncChatContext();
    });

    syncChatContext();
  }

  // ── 초기화 실행 ──
  initRuntimeModeAndApiHub();
  initFloatingChatWidget();
  renderDomainFacets();
  renderSidebarNav();
  renderSidebarScaleTree();
  renderConceptDetail(state.currentConceptId);
  renderPainPoints();
  renderReviewQueue();
  renderDiscoveryLogs();
  renderAiStudioSnapshot(2);
});

