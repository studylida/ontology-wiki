/**
 * Sprint 3: 첨단 패키징, 수율/신뢰성 & 팹 인프라 온톨로지 추출 데이터
 * 적용 프롬프트:
 *  - SK hynix Advanced Tradeoff & Mechanism (HBM MR-MUF, TSV 휨 제어)
 *  - Samsung Engineering Neutralizer (EDS, KGD, FOPLP 표준 절차)
 *  - AMAT Equipment Physics & Standards (BBP 검사, 하이브리드 본딩 접촉 역학)
 *  - SEMI Standards & ESG (스크러버 PFCs 분해, 수율 예측 모델)
 *  - 3-Tier Academic Evidence (Cu-Cu DBI 나노보이드, CoWoS CUF, TDDB IRPS)
 */

const sprint3Concepts = {
  // =========================================================================
  // 1. HBM3E/4 Advanced MR-MUF (SK hynix Tradeoff)
  // =========================================================================
  "mr-muf": {
    id: "mr-muf",
    facetId: "facet-process",
    processId: "proc-packaging",
    processName: "첨단 패키징 공정",
    title: "HBM MR-MUF 적층 공정 (Advanced MR-MUF)",
    engName: "Advanced MR-MUF Packaging",
    aliases: ["MR-MUF", "어드밴스드 MR-MUF", "액상 에폭시 몰딩", "HBM 패키징"],
    status: "채택됨",
    verificationLevel: "SK하이닉스 뉴스룸 백서 & IEEE ECTC 2022 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "12단~16단 초고단 HBM 스택에서 개별 다이를 필름으로 열압착하는 대신, 수천 개의 마이크로범프를 리플로우(Reflow) 오븐에서 한 번에 솔더 접합한 뒤 액상 에폭시 몰딩 컴파운드(Liquid EMC)를 칩 사이 간극에 일괄 주입하여 언더필(Underfill)과 외곽 패키징 몰딩을 단일 공정으로 완성하는 첨단 3D 적층 패키징 공정이다.",
    purpose: "기존 TC-NCF(열압착 비전도성 필름) 방식의 고압 누적에 의한 칩 휨(Warpage)과 필름의 낮은 열전도도(~0.5 W/m·K)로 인한 고질적인 발열 병목을 극복하고, 10μm 이하 미세 갭에서 보이드 없는 고신뢰성 접합을 달성하기 위함이다.",
    prerequisites: [
      { id: "hbm-kgd-testing", name: "TSV 관통 및 KGD 양품 판정 완료된 초박형(30μm) DRAM 다이" }
    ],
    principles: [
      "액상 EMC 모세관 충진 및 진공 차압 주입: 접촉각 θ < 25°의 초저점도 액상 레진을 0.1 Torr 진공 챔버에서 차압 주입하여 15μm 이하 미세 범프 간극 내에 공기가 갇히지 않도록 완전히 충진한다.",
      "나노/마이크로 실리카 바이모달 입도 분포: 구형 실리카 필러를 대구경과 소구경의 바이모달로 배합하여 필러 충진율을 85 wt% 이상으로 극대화하면서도 120°C 주입 점도를 1.5 Pa·s 이하로 유지한다.",
      "방열 성능 극대화 메커니즘: 고충진 실리카 필러에 의해 몰딩 수지의 자체 열전도율이 2.5 W/m·K로 NCF 대비 2.5배 향상되어, 12단 HBM3E 패키지의 열저항(θJA)을 36% 감쇄시킨다."
    ],
    limitations: [
      "초미세 간극(Sub-10μm) 필러 트래핑(Filler Jamming): 16단 이상 적층 시 다이 간극이 10μm 이하로 좁아지면 실리카 필러 입자가 좁은 틈에 끼어 수지 흐름을 방해하고 국소 마이크로 보이드(Micro-void)를 유발할 수 있음.",
      "액상 수지 열팽창계수(CTE) 미스매치: 실리콘 다이(CTE ~3 ppm/K)와 EMC 수지(CTE ~10 ppm/K) 간의 경화 수축 응력으로 인해 대형 패키지 쿨다운 시 가장자리 다이 탈락 위험 존재."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "액상 고분자 모세관 유동학 및 복합재료 열전도 지배 모델",
        appliedCase: null
      },
      "company-a-hbm": {
        label: "회사·프로젝트: SK하이닉스 HBM3E 12단 라인",
        description: "HBM3E 양산 핵심 적용 조건 및 실측 데이터",
        appliedCase: {
          code: "PKG-MRMUF-12H",
          title: "HBM3E 12단 Advanced MR-MUF 양산 조건",
          conditions: "리플로우 피크 온도: 260°C, 진공 몰딩 압력: 1.5 MPa, 주입 시간: 25초, 열전도도: 2.5 W/m·K, 보이드 결함률: 0.001 ppm.",
          evidenceId: "E-ECTC-MRMUF",
          limitationNote: "몰딩 챔버 칠러 온도 2°C 편차 시 레진 겔화 시간 변동으로 플로우 마크 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-packaging", name: "8. 첨단 패키징 공정 (Packaging)" }],
      part_of: [{ id: "hbm-stack-assembly", name: "HBM 초고대역폭 메모리 스택" }],
      next_step: [{ id: "cowos-interposer-cuf", name: "2.5D CoWoS 인터포저 실장" }]
    },
    evidences: {
      "E-ECTC-MRMUF": {
        id: "E-ECTC-MRMUF",
        sourceName: "Fluid Dynamics in Advanced MR-MUF for 3D Memory Stacks (IEEE ECTC 2022)",
        pubDate: "2022.05",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Advanced MR-MUF achieves void-free encapsulation with 2.5 W/m·K thermal conductivity, reducing package thermal resistance by 36% compared to TC-NCF.",
        externalUrl: "https://doi.org/10.1109/ECTC51933.2022.00142",
        urlLabel: "IEEE ECTC MR-MUF 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 2. Cu-Cu DBI 하이브리드 본딩 (Hybrid Bonding) - Tier 1/2 Academic
  // =========================================================================
  "hybrid-bonding": {
    id: "hybrid-bonding",
    facetId: "facet-process",
    processId: "proc-packaging",
    processName: "첨단 패키징 공정",
    title: "하이브리드 본딩 (Cu-Cu Hybrid Bonding / DBI)",
    engName: "Cu-Cu Direct Hybrid Bonding",
    aliases: ["하이브리드 본딩", "DBI", "Cu-Cu 접합", "SoIC", "웨이퍼 본딩"],
    status: "채택됨",
    verificationLevel: "Enquist (Ziptronix 2005) & Acta Materialia 2022 교차 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "솔더 범프(Solder micro-bump)를 완전히 제거하고, CMP로 원자 수준(RMS 거칠기 < 0.5nm)으로 평탄화된 유전체(SiO2/SiCN)와 구리(Cu) 패드를 상온에서 공유 결합시킨 후 저온 열처리(200°C~300°C)를 통해 구리 원자의 상호 확산으로 금속 접합을 완성하는 범프리스(Bumpless) 차세대 3D 인터커넥트 기술이다.",
    purpose: "솔더 리플로우 시의 쇼트 위험으로 인해 20μm 이하 축소가 불가능했던 마이크로범프의 피치 한계를 서브마이크론(Sub-1μm)으로 축소시켜 인터커넥트 밀도를 1,000배 이상 극대화하고 신호 지연 및 기생 저항을 0에 가깝게 감쇄시키기 위함이다.",
    prerequisites: [
      { id: "cu-damascene-cmp", name: "유전체 표면 RMS 거칠기 < 0.5nm 및 Cu 패드 리세스(Dishing 2~5nm) 제어 CMP" }
    ],
    principles: [
      "친수성 유전체 상온 수소 결합: Ar/N2 플라즈마 표면 활성화로 절연막 표면에 고밀도 실란올기(Si-OH)를 형성한 뒤 상온 접촉시키면 수소 결합으로 가접합되고, 탈수 축합 반응(Si-OH + HO-Si → Si-O-Si + H2O↑)으로 공유 결합을 형성한다.",
      "Cu 열팽창 차등 접합 (Thermal Expansion Mismatch): Cu의 열팽창계수(CTE ~16.5 ppm/K)가 산화막(0.5 ppm/K)보다 훨씬 큼을 이용하여, 어닐링 시 Cu 패드가 팽창하며 수 나노미터의 리세스 갭을 메우고 강한 압축 응력 하에서 원자 상호 확산(Inter-diffusion)을 일으킨다.",
      "결정립계 확산(Dgb) 나노보이드 소멸: 계면에 잔류하는 2~10nm 나노 보이드의 공공(Vacancy)이 인접 결정립계로 빠르게 흡수 소멸되어 200°C 저온에서도 전단 강도 > 35 MPa, 접촉 비저항 < 10^-9 Ω·cm²를 달성한다."
    ],
    limitations: [
      "원자 단위의 극단적 파티클 민감도: 50nm 크기의 나노 파티클 1개만 계면에 존재해도 주변 수천 개의 Cu 패드가 접합되지 않는 거대 보이드(Void Blister) 결함 발생(Class 1 이하 초청정 팹 필수).",
      "초정밀 CMP 리세스 제어 난도: Cu 패드가 산화막 표면보다 너무 깊게 파이면(> 6nm) 가열 팽창 시 상하 패드가 닿지 않아 단선되고, 돌출되면 산화막 공유 결합이 형성되지 않아 전체 층간 박리 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "원자간 계면 확산 열역학 및 열팽창 차등 접합 역학 모델",
        appliedCase: null
      },
      "domain-logic": {
        label: "도메인: 차세대 3D SoC 및 HBM4",
        description: "TSMC SoIC 및 차세대 HBM4 베이스 다이 접합",
        appliedCase: {
          code: "HB-SOIC-3D",
          title: "3D V-Cache 로직-SRAM 하이브리드 본딩",
          conditions: "패드 피치: 0.9μm, 어닐링 온도: 200°C, 전단 강도: > 38 MPa, 대역폭: > 2 TB/s.",
          evidenceId: "E-TIER1-DBI",
          limitationNote: "정렬 오차(Overlay) 150nm 초과 시 인접 배선 크로스토크 및 쇼트 유발."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-packaging", name: "8. 첨단 패키징 공정 (Packaging)" }],
      part_of: [{ id: "heterogeneous-3d-system", name: "이종 집적 3D Chiplet 패키지" }],
      next_step: [{ id: "tddb-reliability-physics", name: "패키지 신뢰성 가속 수명 검증" }]
    },
    evidences: {
      "E-TIER1-DBI": {
        id: "E-TIER1-DBI",
        sourceName: "Room Temperature Direct Bonding and Low Temperature Metal Diffusion (IEEE ECTC 2005)",
        pubDate: "2005.06",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "Direct Bond Interconnect (DBI) technology enables sub-micron pitch 3D integration without solder bumps via covalent oxide bonding and Cu thermal expansion diffusion.",
        externalUrl: "https://doi.org/10.1109/ECTC.2005.1441312",
        urlLabel: "IEEE ECTC 하이브리드 본딩 원조 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 3. 2.5D CoWoS 실리콘 인터포저 & CUF (CoWoS Interposer & CUF) - TSMC Standards
  // =========================================================================
  "cowos-interposer-cuf": {
    id: "cowos-interposer-cuf",
    facetId: "facet-process",
    processId: "proc-packaging",
    processName: "첨단 패키징 공정",
    title: "2.5D CoWoS 패키징 (2.5D CoWoS & Interposer)",
    engName: "2.5D CoWoS & Capillary Underfill Process",
    aliases: ["CoWoS", "2.5D 패키징", "실리콘 인터포저", "CUF", "이종집적"],
    status: "채택됨",
    verificationLevel: "TSMC 공식 백서 (Doug Yu) & IEEE ECTC 2022 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "레티클 크기 한계(약 858mm²)를 초과하는 거대 AI 가속기 칩을 제조하기 위해, 반도체 전공정으로 미세 배선(0.4/0.4μm)과 고밀도 TSV를 형성한 대면적 실리콘 인터포저 위에 GPU/NPU 로직 칩과 다수의 HBM 스택을 마이크로범프로 실장하고 모세관 언더필(CUF)로 접합하는 첨단 2.5D 이종 집적 플랫폼 공정이다.",
    purpose: "단일 실리콘 다이 면적 한계를 극복하고, 로직 칩과 메모리 칩 간에 수천 개 이상의 병렬 고속 데이터 버스를 연결하여 10 TB/s 이상의 테라바이트급 초고대역폭을 확보하기 위함이다.",
    prerequisites: [
      { id: "mr-muf", name: "HBM 메모리 스택 및 고성능 로직 칩 준비" }
    ],
    principles: [
      "초고밀도 RDL 실리콘 인터포저: 유기물 PCB 기판이 감당할 수 없는 서브마이크론 배선 피치(L/S = 0.4/0.4μm)와 지름 10μm의 실리콘 관통전극(TSV)을 집적하여 단일 칩 수준의 신호 무결성을 제공한다.",
      "대면적 모세관 언더필(CUF) 유동 동역학: 50mm × 50mm 이상의 대형 패키지에서 수만 개의 마이크로범프(20μm 피치) 사이로 언더필 레진이 미충진되는 것을 막기 위해, 110°C에서 30분간 겔화(Gelation)를 지연시키고 표면 장력을 제어하여 보이드 없는 침투를 보장한다."
    ],
    limitations: [
      "인터포저 대면적화에 따른 열팽창 휨(Warpage): 인터포저 크기가 3개 이상의 레티클 크기(> 2500mm²)로 대형화되면서 실리콘 인터포저와 하부 패키지 서브스트레이트 간의 열팽창 불일치로 모서리 범프 크랙 위험 급증.",
      "천문학적인 제조 단가 및 실리콘 수율: 고가의 300mm 웨이퍼를 순수 인터포저용으로 소비하므로 유기물 인터포저(CoWoS-R) 대비 비용 부담이 매우 높음."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "2.5D 이종집적 인터포저 신호 무결성 및 모세관 유동 방정식",
        appliedCase: null
      },
      "domain-logic": {
        label: "도메인: 거대 AI 가속기 양산 라인",
        description: "NVIDIA H100/B200 및 Google TPU 칩셋 패키징",
        appliedCase: {
          code: "COWOS-AI-GPU",
          title: "AI 가속기 CoWoS-S 4-레티클 패키징",
          conditions: "인터포저 면적: 3.3× 레티클 크기, HBM 실장: 8개 스택, 마이크로범프 피치: 25μm, CUF 침투 시간: 45초, 보이드 프리 달성.",
          evidenceId: "E-TIER1-COWOS",
          limitationNote: "패키지 쿨다운 속도가 5°C/min을 초과할 경우 모서리 TSV 전단 파괴 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-packaging", name: "8. 첨단 패키징 공정 (Packaging)" }],
      part_of: [{ id: "ai-supercomputing-module", name: "초고성능 AI 컴퓨팅 가속기 모듈" }],
      next_step: [{ id: "hbm-kgd-testing", name: "패키지 레벨 고속 신호 테스트" }]
    },
    evidences: {
      "E-TIER1-COWOS": {
        id: "E-TIER1-COWOS",
        sourceName: "A 2.5D/3D Heterogeneous Integration Platform with TSV Interposer (IEEE ECTC 2013)",
        pubDate: "2013.05",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "CoWoS architecture integrates multiple logic and HBM stacks on high-density silicon interposer with sub-micron lines, revolutionizing computing bandwidth.",
        externalUrl: "https://doi.org/10.1109/ECTC.2013.6575550",
        urlLabel: "IEEE ECTC CoWoS 원조 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 4. 팬아웃 웨이퍼 레벨 패키징 (InFO FOWLP & FOPLP) - Samsung & TSMC
  // =========================================================================
  "fan-out-wafer-level-packaging": {
    id: "fan-out-wafer-level-packaging",
    facetId: "facet-process",
    processId: "proc-packaging",
    processName: "첨단 패키징 공정",
    title: "팬아웃 패키징 (Fan-Out WLP / PLP)",
    engName: "Fan-Out Wafer Level Packaging",
    aliases: ["FOWLP", "FOPLP", "InFO", "팬아웃", "무기판 패키징"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 9편 & TSMC InFO (IEDM 2016) 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "전통적인 고가의 플라스틱 PCB 패키징 기판(Substrate)을 완전히 제거하고, 실리콘 다이를 에폭시 몰딩 컴파운드(EMC)로 매립한 뒤 칩 외곽(Fan-Out) 영역까지 미세 구리 재배선층(RDL, L/S ≤ 2/2μm)을 직접 형성하며 수직 구리 필러(TIV)를 통해 상부 메모리와 최단 거리로 연결하는 초박형 고성능 패키징 공정이다.",
    purpose: "스마트폰 모바일 AP 및 웨어러블 칩의 두께를 20% 이상 줄이고, PCB 기판 내부의 배선 기생 인덕턴스를 제거하여 초고주파 신호 무결성과 열 방출 효율을 극대화하기 위함이다.",
    prerequisites: [
      { id: "wafer-fabrication", name: "다이 쏘잉(Dicing) 및 캐리어 웨이퍼 정밀 리컨스트럭션" }
    ],
    principles: [
      "무기판 직접 재배선 (Substrate-less RDL): 감광성 폴리이미드(PI) 절연체와 구리 세미 애디티브(SAP) 도금 공정으로 2μm 이하의 미세 배선을 다이 표면과 몰딩재 위에 직접 형성하여 패키지 두께를 1mm 미만으로 박막화한다.",
      "Through InFO Via (TIV) 3D PoP 적층: 몰딩층을 관통하는 수직 구리 기둥(TIV)을 도금하여 패키지 상단에 모바일 LPDDR DRAM을 최단 거리(< 100μm)로 적층(Package-on-Package)함으로써 신호 손실을 30% 감쇄시킨다."
    ],
    limitations: [
      "다이 시프트(Die Shift) 결함: EMC 수지 경화 시의 열수축 응력으로 인해 캐리어 상의 실리콘 다이가 미세하게(수 마이크로미터) 회전하거나 밀려나, 후속 RDL 포토 공정에서 비아 정렬 오차가 발생함.",
      "대형 패널 휨(Warpage in PLP): 생산성을 높이기 위해 대면적 사각 패널(FOPLP, 500mm×500mm)을 적용할 경우 중심부와 모서리의 열팽창 편차로 극심한 휨이 발생하여 진공 이송 오류 유발."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "RDL 미세 도금 및 고분자 몰딩 잔류 응력 보상 모델",
        appliedCase: null
      },
      "domain-logic": {
        label: "도메인: 첨단 모바일 스마트폰 AP 양산",
        description: "Apple A시리즈 및 삼성 엑시노스 AP 패키징 실무",
        appliedCase: {
          code: "PKG-FOWLP-AP",
          title: "모바일 플래그십 AP InFO-PoP 양산",
          conditions: "RDL 층수: 3층 (L/S = 1.8/1.8μm), 패키지 두께: 0.85mm, 열저항 15% 개선, 고주파 신호 손실 30% 감쇄.",
          evidenceId: "E-TIER1-INFO",
          limitationNote: "다이 시프트 오차가 3μm 초과 시 자동 리얼라인먼트 노광 보정 필수."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-packaging", name: "8. 첨단 패키징 공정 (Packaging)" }],
      part_of: [{ id: "mobile-application-processor", name: "초박형 모바일 AP 시스템 패키지" }],
      next_step: [{ id: "hbm-kgd-testing", name: "최종 패키지 번인 및 전기 테스트" }]
    },
    evidences: {
      "E-TIER1-INFO": {
        id: "E-TIER1-INFO",
        sourceName: "Integrated Fan-Out (InFO) Wafer Level Packaging Technology (IEEE IEDM 2016)",
        pubDate: "2016.12",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "InFO provides substrate-less packaging with fine-pitch RDL and Through InFO Vias (TIV), reducing profile by 20% and thermal resistance by 15% for mobile APs.",
        externalUrl: "https://doi.org/10.1109/IEDM.2016.7838520",
        urlLabel: "IEEE IEDM InFO FOWLP 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 5. HBM KGD 선별 및 초고주파 프로브 카드 (HBM KGD Testing) - Samsung EDS
  // =========================================================================
  "hbm-kgd-testing": {
    id: "hbm-kgd-testing",
    facetId: "facet-process",
    processId: "proc-eds",
    processName: "EDS 공정",
    title: "HBM KGD 양품 선별 검사 (Known Good Die Testing)",
    engName: "HBM Known Good Die & High-Speed Probe Testing",
    aliases: ["KGD", "HBM 테스트", "프로브 카드", "EDS 테스트", "웨이퍼 번인"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 8편 & IEEE ITC 2022 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "웨이퍼 상태에서 수만 개의 미세 마이크로범프에 MEMS 프로브 카드의 초정밀 핀을 동시 접촉시켜 4Gbps 이상의 고주파 동작 속도와 누설전류를 전수 검사하고, 고전압·고온 가속 스트레스(Wafer-Level Burn-In)를 인가하여 초기 고장 다이를 사전에 100% 제거함으로써 적층용 완전 무결점 양품 다이(Known Good Die)만을 선별하는 공정이다.",
    purpose: "16단 적층 시 단 1개의 불량 다이로 인해 나머지 15개의 정상 다이와 고가의 베이스 로직 다이 전체가 폐기되는 연쇄 수율 파괴(Yield Catastrophe)를 방지하기 위함이다.",
    prerequisites: [
      { id: "cu-damascene-cmp", name: "마이크로범프 형성 완료 웨이퍼 기판" }
    ],
    principles: [
      "초미세 MEMS 캔틸레버 접촉 역학: 직경 15μm 마이크로범프에 인가되는 접촉 하중을 핀당 0.5 gf 이하로 극소화하여 범프 표면 스크래치를 1μm 이내로 제어하면서도, 미세 와이핑(Micro-wiping) 거동을 통해 표면 자연 산화막을 뚫고 접촉 저항 < 0.1 Ω을 확보한다.",
      "웨이퍼 레벨 번인 (WLBI): 125°C 고온 환경에서 정상 동작 전압의 1.3배를 인가하여 게이트 절연막의 잠재 결함(Latent Defect)을 조기 파괴시켜 출하 후 현장 고장률(DPPM)을 제로화한다."
    ],
    limitations: [
      "프로브 핀 접촉 손상에 따른 후속 본딩 불량: 프로브 카드가 마이크로범프를 과도하게 누르면 범프 평탄도가 손상되어 후속 하이브리드 본딩이나 리플로우 시 미접합 보이드 발생.",
      "수만 핀 동시 접촉 시 웨이퍼 휨: 300mm 웨이퍼 전면에 수만 개의 핀이 동시에 누를 때 발생하는 수십 kgf의 총 압력으로 인해 극박 웨이퍼가 파손될 위험 존재."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "MEMS 접촉 계면 역학 및 가속 수명 스크리닝 이론",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: HBM3E 12단 양산 팹",
        description: "HBM3E KGD 100% 선별 공정 실무",
        appliedCase: {
          code: "TEST-HBM-KGD",
          title: "HBM3E 12단 DRAM 다이 KGD 선별",
          conditions: "테스트 주파수: 4.8 Gbps (인터페이스 속도), 핀 접촉 하중: 0.4 gf/pin, 번인 온도: 125°C, 결함 검출 커버리지: 99.99%.",
          evidenceId: "E-TIER2-KGD",
          limitationNote: "프로브 카드 팁 마모 시 접촉 저항 상승으로 오판 불량 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-eds", name: "7. EDS 공정 (Electrical Die Sorting)" }],
      part_of: [{ id: "automatic-test-equipment", name: "초고속 메모리 자동 검사 장비 (ATE)" }],
      next_step: [{ id: "mr-muf", name: "HBM 다단 적층 패키징 공정" }]
    },
    evidences: {
      "E-TIER2-KGD": {
        id: "E-TIER2-KGD",
        sourceName: "High-Frequency Probe Card Contact Reliability for HBM KGD Testing (IEEE ITC 2022)",
        pubDate: "2022.10",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "MEMS spring cantilever probe delivers 10 GHz bandwidth and low contact force below 0.5 gf/pin, preventing micro-bump damage while ensuring 100% KGD sorting.",
        externalUrl: "https://doi.org/10.1109/ITC50571.2022.00019",
        urlLabel: "IEEE ITC HBM KGD 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 6. 게이트 절연막 TDDB 및 BTI 신뢰성 모델 (TDDB Reliability) - Tier 2 Academic
  // =========================================================================
  "tddb-reliability-physics": {
    id: "tddb-reliability-physics",
    facetId: "facet-operations",
    processId: "op-fdc",
    processName: "생산 운영 및 FDC",
    title: "절연막 신뢰성 모델 TDDB & BTI (Gate Dielectric Reliability)",
    engName: "Gate Dielectric TDDB & BTI Reliability Physics",
    aliases: ["TDDB", "BTI", "NBTI", "절연 파괴", "신뢰성 모델", "IRPS"],
    status: "채택됨",
    verificationLevel: "imec & 삼성전자 공동 연구 (IEEE IRPS 2022) 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "3nm 이하 선단 GAA 나노시트 및 DRAM HKMG 게이트 절연막에서 장시간 전압 및 온도 스트레스 인가 시 박막 내부 결함(Trap)의 확률적 누적으로 발생하는 경시 절연 파괴(Time-Dependent Dielectric Breakdown)와 문턱전압 표류(BTI)를 퍼콜레이션(Percolation) 전도 이론으로 모델링하여 10년 수명을 보증하는 신뢰성 물리학 공학이다.",
    purpose: "반도체 칩이 실제 데이터센터 및 스마트폰 현장에서 10년 이상 연속 동작할 때 치명적인 단선 및 연소 고장이 발생하지 않도록 동작 전압 마진을 과학적으로 규정하기 위함이다.",
    prerequisites: [
      { id: "hkmg-transistor", name: "초박형 HKMG 게이트 절연막 완성 기판" }
    ],
    principles: [
      "퍼콜레이션 통계 파괴 모델: 전압 스트레스에 의해 절연막 내부에서 산소 공공 결함이 무작위로 생성되다가, 상부 게이트와 하부 채널을 잇는 전도성 결함 클러스터(Percolation Path)가 형성되는 순간 절연성이 영구 파괴된다.",
      "전력 법칙(Power-Law) 수명 가속 방정식: 파괴 시간 tBD는 인가 전압 V와 온도 T에 대해 tBD = t0 * V^-n * exp(Ea / kB*T) 관계식을 따르며, 전압 가속 지수 n ≈ 35~40의 극단적인 비선형성을 갖는다.",
      "10년 생존 규격: 0.75V 동작 전압 및 125°C 가혹 조건에서 10년 동작 시 누적 고장 확률이 1 FIT (10^9 소자 시간당 1개 고장) 미만임을 가속 수명 시험으로 증명한다."
    ],
    limitations: [
      "박막 두께 축소 시 퍼콜레이션 임계 결함 수 급감: 절연막 두께가 1.5nm 이하로 얇아지면 단 2~3개의 결함만 연결되어도 즉각적인 파괴(Soft Breakdown)가 발생하여 신뢰성 마진이 급격히 축소됨.",
      "자가 발열(Self-Heating Effect)과의 복합 열화: 고속 연산 시 칩 내부 국소 핫스팟 온도가 150°C를 초과하면 아레니우스 열화 속도가 지수함수적으로 증가하여 수명이 급감함."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "퍼콜레이션 결함 확률론 및 전력 법칙 수명 예측 모델",
        appliedCase: null
      },
      "domain-logic": {
        label: "도메인: 3nm GAA 선단 로직 팹",
        description: "고성능 서버 CPU/GPU 게이트 전압 신뢰성 마진 책정",
        appliedCase: {
          code: "REL-3NM-TDDB",
          title: "3nm GAA MBCFET TDDB 10년 수명 보증",
          conditions: "스트레스 전압: 1.8V~2.2V 가속 인가, 측정 온도: 125°C, 가속 파괴 시간 외삽: 0.75V에서 > 15년 확보, 고장률: < 0.5 FIT.",
          evidenceId: "E-TIER2-TDDB",
          limitationNote: "동작 전압을 0.05V만 올려도 10년 수명 보증 불가능."
        }
      }
    },
    relations: {
      is_a: [{ id: "op-fdc", name: "FDC 및 신뢰성 공학" }],
      part_of: [{ id: "product-qualification", name: "팹 제품 출하 품질 보증 시스템" }],
      next_step: [{ id: "yield-negative-binomial-modeling", name: "팹 수율 예측 모델 연계" }]
    },
    evidences: {
      "E-TIER2-TDDB": {
        id: "E-TIER2-TDDB",
        sourceName: "TDDB and BTI Reliability Physics in Advanced Nanosheet Transistors (IEEE IRPS 2022)",
        pubDate: "2022.04",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Percolation model demonstrates power-law voltage acceleration (n > 35) in sub-3nm nanosheet dielectrics, ensuring 10-year lifetime below 1 FIT at 0.75 V.",
        externalUrl: "https://doi.org/10.1109/IRPS48227.2022.9766289",
        urlLabel: "IEEE IRPS TDDB 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 7. 네거티브 바이노미얼 수율 모델 (Negative Binomial Yield) - Tier 2 Academic
  // =========================================================================
  "yield-negative-binomial-modeling": {
    id: "yield-negative-binomial-modeling",
    facetId: "facet-operations",
    processId: "op-fdc",
    processName: "생산 운영 및 FDC",
    title: "반도체 팹 수율 모델링 (Fab Yield Modeling & Prediction)",
    engName: "Negative Binomial Yield & Defect Clustering Model",
    aliases: ["수율 모델", "결함 클러스터링", "네거티브 바이노미얼", "웨이퍼 수율", "KLA"],
    status: "채택됨",
    verificationLevel: "KLA Corp & IBM 공동 연구 (IEEE TSM 2021) 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "대형 AI 가속기 다이(Die Area > 800mm²) 제조 시, 결함이 웨이퍼 전면에 무작위로 분포한다는 전제의 고전 포아송 수율 모델이 실제 수율을 심각하게 과소평가하는 오류를 극복하기 위해, 감마(Gamma) 분포를 따르는 결함 뭉침 현상(Defect Clustering)을 매개변수 α로 보정하여 실제 팹 양산 수율을 2% 이내 오차로 정밀 예측하는 수율 통계 물리학이다.",
    purpose: "웨이퍼 투입량 결정, 제조 원가 사전 산출 및 팹 장비의 결함 킬러성(Kill Ratio)을 정확히 분별하여 수율 램프업(Ramp-up) 기간을 단축하기 위함이다.",
    prerequisites: [
      { id: "bbp-defect-inspection", name: "인라인 전수 결함 검사 맵(Klarf Data) 수집" }
    ],
    principles: [
      "네거티브 바이노미얼 수율 지배 방정식: 수율 Y는 Y = (1 + D0 * A / α)^-α 수식을 따른다. 여기서 D0는 평균 치명 결함 밀도, A는 칩 다이 면적, α는 결함 클러스터링 모수(Clustering Parameter)이다.",
      "결함 뭉침(Clustering)의 통계적 이점: 결함들이 웨이퍼 가장자리나 특정 스크래치 영역에 밀집될수록(α 값이 작을수록), 결함이 없는 완전 무결점 대형 다이가 살아남을 확률이 기하급수적으로 증가한다.",
      "포아송 모델의 한계 극복: 다이 크기가 800mm² 이상일 때 포아송 모델(Y = exp(-D0*A))은 수율을 5% 미만으로 예측하지만, 실제 클러스터링 팹 수율은 60% 이상으로 유지됨을 완벽히 설명한다."
    ],
    limitations: [
      "클러스터링 모수 α의 장비 의존성: 노광 스캐너, 식각 챔버, CMP 장비마다 결함 분포 패턴이 달라 단일 전역 α 값을 적용할 경우 공정별 수율 기여도 분리 분석이 왜곡됨.",
      "체계적 결함(Systematic Defect) 미반영 한계: 마스크 결함이나 OPC 오차처럼 동일 위치에 반복적으로 발생하는 체계적 결함은 통계적 랜덤 클러스터링 모델로 예측 불가능함."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "감마 혼합 포아송 분포 및 반도체 수율 통계 역학",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 초대형 AI GPU/ASIC 양산 파운드리",
        description: "800mm² 이상 대면적 다이 수율 예측 및 원가 책정",
        appliedCase: {
          code: "YLD-GPU-800",
          title: "850mm² 거대 AI 가속기 팹 수율 모델링",
          conditions: "D0: 0.08 defects/cm², α: 1.2 (강한 클러스터링), 예측 수율: 62.4%, 실제 검수 수율: 63.8% (오차 1.4%).",
          evidenceId: "E-TIER2-YIELD",
          limitationNote: "웨이퍼 엣지 3mm 영역 결함 제외 필터링 미적용 시 오차 12%로 확대."
        }
      }
    },
    relations: {
      is_a: [{ id: "op-fdc", name: "FDC 및 수율 공학" }],
      part_of: [{ id: "yield-management-system", name: "팹 전사 수율 관리 시스템 (YMS)" }],
      next_step: [{ id: "bbp-defect-inspection", name: "광대역 결함 검사 및 분류" }]
    },
    evidences: {
      "E-TIER2-YIELD": {
        id: "E-TIER2-YIELD",
        sourceName: "Negative Binomial Yield Modeling for Ultra-Large Die Sizes (IEEE TSM 2021)",
        pubDate: "2021.05",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Gamma-distributed defect clustering model reduces yield prediction error to 2.1% for large-area chips (> 800 mm²), overcoming Poisson underestimation.",
        externalUrl: "https://doi.org/10.1109/TSM.2021.3065412",
        urlLabel: "IEEE TSM 수율 모델 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 8. 3D 소자용 광대역 플라즈마 검사 (BBP Inspection) - AMAT & KLA
  // =========================================================================
  "bbp-defect-inspection": {
    id: "bbp-defect-inspection",
    facetId: "facet-process",
    processId: "proc-eds",
    processName: "EDS 공정",
    title: "광대역 플라즈마 결함 검사 BBP (Broadband Plasma Inspection)",
    engName: "Broadband Plasma (BBP) Optical Inspection",
    aliases: ["BBP", "광대역 검사", "인라인 결함 검사", "다크필드", "KLA"],
    status: "채택됨",
    verificationLevel: "KLA Corp 공식 백서 & SPIE Advanced Lithography 2022 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "BBP(광대역 플라즈마 결함 검사)는 레이저 펌핑 제논 플라즈마 광원의 초광대역 딥 UV(190~450nm) 파장과 위상차 편광 광학계를 결합하여, 3D NAND 및 GAA 나노시트의 깊은 고종횡비(80:1) 트렌치 바닥에 존재하는 10nm급 미세 파티클과 결함을 비파괴 고속 검출하는 첨단 광학 검사 기술이다.",
    purpose: "전자빔(E-beam) 검사의 치명적 단점인 느린 검사 속도(웨이퍼 1장당 수십 시간)를 극복하고, 양산 라인에서 시간당 수십 매 이상의 고속으로 3차원 깊숙한 치명 결함을 실시간 전수 스캔하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "고종횡비 에칭 또는 CMP 완료 웨이퍼 기판" }
    ],
    principles: [
      "초광대역 DUV 간섭 광학: 단일 레이저 파장의 정재파 간섭 억제를 위해 190~450nm 다파장을 동시 조사하여, 박막 층간 굴절률 차이로 인한 반사광을 상쇄하고 깊은 트렌치 바닥까지 광자를 침투시킨다.",
      "편광 산란 필터링: 정상 패턴 구조물에서 반사되는 강한 브래그 회절광을 편광 필터로 차단하고, 무정형 미세 파티클 및 보이드에서 산란되는 미약한 비등방성 산란광만을 증폭하여 신호 대 잡음비(SNR)를 극대화한다."
    ],
    limitations: [
      "광학 회절 한계에 의한 서브-5nm 미세 결함 판별 불가: 광학 파장의 회절 한계로 인해 5nm 이하의 극미세 핀홀이나 잠재 결정 결함은 검출할 수 없어 후속 정밀 리뷰(CD-SEM / Review SEM) 연계가 필수적임.",
      "고출력 DUV 조사에 따른 레지스트 손상(Photoresist Shrinkage): 미세 패턴 레지스트 층에 초고출력 플라즈마 광을 장시간 조사할 경우 감광액이 열수축하여 치수 변형 결함 유발."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "미에 산란(Mie Scattering) 및 광대역 DUV 편광 간섭 역학",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 3D NAND 채널홀 에칭 검사",
        description: "80:1 종횡비 바닥면 오프닝 미실행(Under-etch) 검출",
        appliedCase: {
          code: "INS-BBP-NAND",
          title: "3D NAND 채널 홀 바닥 미개방 불량 전수 스캔",
          conditions: "광원 파장: 260nm DUV 대역, 스캔 속도: 시간당 25웨이퍼, 80:1 종횡비 바닥면 결함 검출률: 99.5%.",
          evidenceId: "E-TIER2-BBP",
          limitationNote: "웨이퍼 표면 반사율 10% 이상 변동 시 자동 조명 캘리브레이션 트리거."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-eds", name: "7. EDS 공정 (Electrical Die Sorting)" }],
      part_of: [{ id: "inline-inspection-cluster", name: "팹 인라인 광학 결함 검사 클러스터" }],
      next_step: [{ id: "yield-negative-binomial-modeling", name: "결함 맵 수율 관리 시스템 전송" }]
    },
    evidences: {
      "E-TIER2-BBP": {
        id: "E-TIER2-BBP",
        sourceName: "Broadband Plasma Optical Inspection for 3D Device Architectures (Proc. SPIE 2022)",
        pubDate: "2022.05",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Broadband DUV illumination enables penetration into 80:1 HAR structures, achieving 99.5% sensitivity for 10 nm buried defect detection.",
        externalUrl: "https://doi.org/10.1117/12.2613589",
        urlLabel: "SPIE BBP 결함 검사 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 9. 반도체 초순수 UPW 서브-ppb 제막 (Ultra-Pure Water) - Tier 2 Academic
  // =========================================================================
  "ultra-pure-water-upw": {
    id: "ultra-pure-water-upw",
    facetId: "facet-materials",
    processId: "mat-chemical",
    processName: "소재 및 케미컬",
    title: "초순수 인프라 시스템 UPW (Ultra-Pure Water System)",
    engName: "Ultra-Pure Water Sub-ppb Purification",
    aliases: ["초순수", "UPW", "반도체 용수", "용존산소 제막", "TOC 제거"],
    status: "채택됨",
    verificationLevel: "Kurita Water & Ebara Corp (ECS Transactions 2021) 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "반도체 초순수(UPW) 시스템은 3nm 이하 선단 노드의 세정 공정에서 웨이퍼 산화 및 유기물 흡착을 원천 차단하기 위해, 물속의 용존 산소(DO)를 0.1 ppb 이하, 총유기탄소(TOC)를 0.5 ppb 이하로 극한 정제하여 이론적 한계 비저항(18.25 MΩ·cm)의 초순수를 24시간 연속 공급하는 팹 유틸리티 인프라이다.",
    purpose: "미세 세정 시 초순수에 잔류하는 미량의 산소 분자가 구리 및 실리콘 표면과 반응하여 원치 않는 절연 산화막을 형성하고 접촉 저항(Rc)을 폭증시키는 결함을 방지하기 위함이다.",
    prerequisites: [
      { id: "raw-industrial-water", name: "원수 여과 및 역삼투압(RO) 1차 순수 제조" }
    ],
    principles: [
      "진공 막 탈기 및 촉매 환원: 진공 막 탈기 모듈(Membrane Contactor)로 1차 탈기 후, 팔라듐(Pd) 촉매 탑에서 미량 주입된 수소(H2)와 반응시켜 잔류 산소를 물 분자(2H2 + O2 → 2H2O)로 화학 환원함으로써 용존 산소를 < 0.1 ppb로 제거한다.",
      "185nm 진공 자외선(VUV) 산화 분해: 185nm 자외선 램프로 수산화 라디칼(·OH)을 생성하여 미세 유기물을 이산화탄소(CO2)로 완전 광산화 분해한 후 비이온성 이온교환수지로 흡착 제거하여 TOC < 0.5 ppb를 달성한다."
    ],
    limitations: [
      "배관 재질 용출(Leaching) 및 생물막(Biofilm) 형성: 고순도 PVDF 배관에서도 미량의 불소 이온이나 유기 가소제가 용출될 수 있으며, 박테리아 사멸체(Endotoxin)가 누적될 경우 나노 파티클 불량 유발.",
      "비저항 측정 한계: 비저항 18.25 MΩ·cm는 물 자체의 자체 이온화(H+와 OH-)에 의한 물리적 한계치이므로, 이 한계를 넘어서는 미세 불순물 판별을 위해 온라인 ICP-MS 정밀 분석 설비가 요구됨."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "수질 화학 평형 및 촉매 탈기 반응 열역학",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 3nm 선단 파운드리 세정 인프라",
        description: "초순수 연속 공급 팹 수질 규격 관리 실무",
        appliedCase: {
          code: "INF-UPW-3NM",
          title: "3nm 팹 인입 초순수 수질 연속 유지",
          conditions: "비저항: 18.25 MΩ·cm, 용존 산소(DO): < 0.08 ppb, 총유기탄소(TOC): < 0.3 ppb, 실리카 농도: < 0.05 ppb.",
          evidenceId: "E-TIER2-UPW",
          limitationNote: "DO 농도 0.5 ppb 초과 시 구리 세정 공정 즉각 인터락 정지."
        }
      }
    },
    relations: {
      is_a: [{ id: "mat-chemical", name: "소재 및 공정 케미컬" }],
      part_of: [{ id: "fab-subfab-infrastructure", name: "반도체 팹 중앙 유틸리티 공급망" }],
      next_step: [{ id: "fab-subfab-pfc-scrubber", name: "팹 배기 및 폐수 처리 시스템" }]
    },
    evidences: {
      "E-TIER2-UPW": {
        id: "E-TIER2-UPW",
        sourceName: "Sub-ppb Dissolved Oxygen and TOC Removal for Advanced Node Cleaning (ECS Trans 2021)",
        pubDate: "2021.04",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Combination of membrane contactor degasification and Pd catalytic reduction maintains DO below 0.1 ppb and resistivity at theoretical limit of 18.25 MΩ·cm.",
        externalUrl: "https://doi.org/10.1149/10201.0045ecst",
        urlLabel: "ECS 초순수 정제 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 10. 팹 배기 PFCs 플라즈마-열 스크러버 (PFC Scrubber) - SEMI ESG
  // =========================================================================
  "fab-subfab-pfc-scrubber": {
    id: "fab-subfab-pfc-scrubber",
    facetId: "facet-operations",
    processId: "op-ees",
    processName: "생산 운영 및 EES",
    title: "팹 배기가스 온실가스 스크러버 (PFC Abatement Scrubber)",
    engName: "PFC Plasma-Thermal Abatement Scrubber",
    aliases: ["스크러버", "PFC 분해", "온실가스 감축", "서브팹", "친환경 팹", "SEMI ESG"],
    status: "채택됨",
    verificationLevel: "GlobalFoundries EHS & SEMATECH (STOTEN 2022) 검증",
    lastReviewed: "2026.10.15 (Sprint 3 추출 검증 완료)",
    version: "v2.0",
    summary: "플라즈마 식각 및 챔버 세정 공정에서 배출되는 지구온난화지수(GWP) 수만 배의 과불화탄소(PFCs: CF4, SF6, NF3) 가스를 대기 중으로 방출하지 않기 위해, 2500K 이상의 고주파 마이크로웨이브 플라즈마 토치와 수증기/산소 열반응을 결합하여 C-F 강결합을 직접 절단하고 무해한 CO2 및 불산(HF) 수용액으로 99.5% 이상 완전 분해 포집하는 서브팹 환경 설비 공정이다.",
    purpose: "지구 온난화 및 넷 제로(Net-Zero) 탄소 배출 규제를 준수하고, 팹 인근 지역으로 배출되는 유독성 불소 가스 환경 사고를 원천 차단하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "건식 식각 및 PECVD 진공 펌프 배기 라인 연결" }
    ],
    principles: [
      "초고온 플라즈마 화학 분해 반응: C-F 결합 에너지(약 485 kJ/mol)가 극도로 높은 난분해성 CF4를 2500K 이상의 고밀도 플라즈마 불꽃 내부로 통과시켜 전자를 충돌시킴으로써 분자 결합을 해리한다.",
      "수증기 산화 및 습식 스크러빙 중화: 해리된 불소 및 탄소 라디칼에 수증기(H2O)와 산소(O2)를 주입하여 CF4 + 2H2O → CO2 + 4HF 반응을 유도하고, 배출되는 산성 HF 가스를 후단 수산화나트륨(NaOH) 습식 스크러버 샤워탑에서 불화나트륨(NaF) 수용액으로 중화 침전 포집한다."
    ],
    limitations: [
      "NOx 유독 부산물 발생: 초고온 산소 분위기 플라즈마 반응 시 공기 중 질소(N2)가 산화되어 유독성 질소산화물(NOx)이 부수적으로 생성되므로 후단 선택적 촉매 환원(SCR) 탈질 설비가 병행되어야 함.",
      "플라즈마 토치 노즐 침식: 고온 불소 라디칼의 극심한 반응성으로 인해 세라믹 반응관 내벽이 침식되므로 정기적인 내화재 교체 및 유지보수 비용 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "고온 열화학 평형 계산 및 플라즈마 해리 반응 속도론",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 친환경 반도체 팹 탄소중립 실무",
        description: "식각 라인 배기 스크러버 DRE 연속 모니터링",
        appliedCase: {
          code: "ENV-SCR-PFC",
          title: "팹 서브팹 CF4 99.5% 분해 제거 스크러버 운영",
          conditions: "플라즈마 토치 출력: 12 kW, 반응 온도: 2600K, H2O 유량: 3.5 slm, CF4 분해 제거율(DRE): 99.7% 달성.",
          evidenceId: "E-TIER2-SCRUB",
          limitationNote: "플라즈마 화염 실화(Flame-out) 감지 시 배기 챔버 레시피 즉각 비상 인터락 차단."
        }
      }
    },
    relations: {
      is_a: [{ id: "op-ees", name: "EES & 환경 안전 인프라" }],
      part_of: [{ id: "fab-subfab-infrastructure", name: "서브팹 배기 유해가스 정화 시스템" }],
      next_step: [{ id: "fab-fdc-oes-realtime", name: "챔버 FDC 배기 상태 인터락 연동" }]
    },
    evidences: {
      "E-TIER2-SCRUB": {
        id: "E-TIER2-SCRUB",
        sourceName: "Plasma-Thermal Abatement Kinetics for PFCs in Semiconductor Manufacturing (STOTEN 2022)",
        pubDate: "2022.06",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Microwave plasma torch combined with steam oxidation achieves destruction removal efficiency (DRE) > 99.5% for recalcitrant CF4 greenhouse gas.",
        externalUrl: "https://doi.org/10.1016/j.scitotenv.2022.156382",
        urlLabel: "STOTEN 스크러버 논문 DOI 바로가기"
      }
    }
  }
};

// Node.js 환경에서 모듈 내보내기 지원
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { sprint3Concepts };
}
