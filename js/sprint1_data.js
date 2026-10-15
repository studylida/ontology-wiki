/**
 * Sprint 1: 전공정 핵심 (패터닝, 식각, 트랜지스터 형성) 온톨로지 추출 데이터
 * 적용 프롬프트:
 *  - Samsung Engineering Neutralizer (비유 제거, 순차 절차)
 *  - ASML Optical Physics & Holistic Lithography Rule (Rayleigh, LPP, High-NA)
 *  - Lam Equipment Physics & Chamber Control Rule (플라즈마 임피던스, ALE, 극저온)
 *  - 3-Tier Academic Evidence Rule (GAA SiGe 선택식각, Inner Spacer, MOR)
 */

const sprint1Concepts = {
  // =========================================================================
  // 1. 웨이퍼 제조 공정 (Wafer Fabrication) - Samsung Neutralized
  // =========================================================================
  "wafer-fabrication": {
    id: "wafer-fabrication",
    facetId: "facet-process",
    processId: "proc-wafer",
    processName: "웨이퍼 제조 공정",
    title: "웨이퍼 제조 공정 (Wafer Fabrication)",
    engName: "Silicon Wafer Fabrication",
    aliases: ["웨이퍼 제조", "잉곳 성장", "CZ 공정", "웨이퍼 기판"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 & SEMI M1 표준 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "규소(SiO2)를 순도 99.999999999%(11N)의 전자급 다결정 실리콘(EG-Si)으로 정련한 후, 초크랄스키(CZ)법으로 무결함 단결정 잉곳을 성장시켜 슬라이싱, 엣지 프로파일링, 래핑, CMP 연마를 거쳐 원자 수준의 평탄 기판을 제조하는 단위 공정이다.",
    purpose: "반도체 집적회로 소자 형성의 물리적 베이스 플레이트(Substrate)를 제공하고, 격자 결함(Dislocation) 및 금속 오염을 억제하여 트랜지스터의 전기적 특성과 수율을 보장하기 위함이다.",
    prerequisites: [
      { id: "raw-silica", name: "고순도 규석 정련 및 전자급 실리콘(EG-Si) 제조" }
    ],
    principles: [
      "초크랄스키(Czochralski, CZ) 잉곳 성장: 석영 도가니에서 1420°C로 용융된 실리콘에 종자 결정(Seed Crystal)을 접촉시켜 회전 인상(Pulling)하며 대구경(300mm) 무결함 단결정 잉곳을 제조한다.",
      "결정 결함 제어: 인상 속도(V)와 고-액 계면의 축방향 온도 구배(G)의 비(V/G)를 임계값 근방으로 제어하여 공공(Vacancy, COP)과 격자간 실리콘(Interstitial Si) 응집 결함을 동시에 차단한다.",
      "표면 평탄화 및 결함 제거: 다이아몬드 와이어 절단으로 절단된 웨이퍼의 미세 크랙을 화학 에칭으로 제거하고, 양면 래핑(Lapping)과 화학기계적 연마(CMP)를 통해 표면 RMS 거칠기를 0.1nm 이하로 가공한다."
    ],
    limitations: [
      "300mm 대구경 웨이퍼 인상 시 열응력(Thermal Stress)으로 인한 슬립(Slip) 전위 발생 위험이 존재한다.",
      "석영 도가니 용해에 의해 잉곳 내부로 침투하는 침입형 산소 농도(Oi: 10~20 ppma)를 엄격히 제어하지 못할 경우 고온 열처리 시 산소 석출 결함이 활성 소자 영역에 형성되어 누설전류를 유발한다."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "CZ법 단결정 성장 및 기계화학적 표면 가공의 지배 메커니즘",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 선단 로직 파운드리 (3nm/2nm)",
        description: "원자 평탄도 및 극저 결함 밀도가 요구되는 첨단 파운드리 웨이퍼 사양",
        appliedCase: {
          code: "WF-300-LOGIC",
          title: "선단 FinFET/GAA 로직용 극초평탄 웨이퍼(Ultra-flat Wafer) 사양",
          conditions: "나노 토폴로지(Nanotopology) 편차 < 10nm (2mm×2mm 윈도우 기준), 표면 금속 불순물 농도 < 1×10^9 atoms/cm² 유지.",
          limitationNote: "과도한 화학 연마 시 웨이퍼 엣지 롤오프(Edge Roll-Off) 현상으로 엣지 다이 수율 손실 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-wafer", name: "1. 웨이퍼 제조 (Wafer Fabrication)" }],
      part_of: [{ id: "ingot-puller", name: "CZ 잉곳 성장로" }],
      next_step: [{ id: "thermal-oxidation", name: "2. 산화 공정 (Oxidation)" }]
    },
    evidences: {
      "E-SAM-01": {
        id: "E-SAM-01",
        sourceName: "삼성반도체 8대 공정 공식 교육 연재 [1편: 웨이퍼 제조]",
        pubDate: "2024.01",
        type: "반도체 제조사 공식 기술 아카이브",
        quote: "모래에서 추출한 실리콘을 고순도로 정련하여 잉곳을 만들고, 이를 얇게 썰어 연마하는 과정을 통해 반도체의 바탕이 되는 300mm 실리콘 웨이퍼가 완성된다.",
        externalUrl: "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/wafer/",
        urlLabel: "삼성반도체 8대 공정 공식 웹페이지 바로가기"
      }
    }
  },

  // =========================================================================
  // 2. 열산화 공정 (Thermal Oxidation) - Samsung Neutralized
  // =========================================================================
  "thermal-oxidation": {
    id: "thermal-oxidation",
    facetId: "facet-process",
    processId: "proc-oxidation",
    processName: "산화 공정",
    title: "열산화 공정 (Thermal Oxidation)",
    engName: "Thermal Oxidation",
    aliases: ["열산화", "산화막 형성", "Dry Oxidation", "Wet Oxidation"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 & Deal-Grove 물리 모델 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "800°C~1200°C의 고온 전기로에서 실리콘 웨이퍼를 산소(O2) 또는 수증기(H2O)와 화학 반응시켜 웨이퍼 표면에 균일하고 절연성이 뛰어난 이산화규소(SiO2) 박막을 직접 성장시키는 공정이다.",
    purpose: "금속 배선 간의 전기적 절연, 이온 주입 시 하부 실리콘 영역 차폐(Screen Oxide), 패터닝 시 하드마스크 및 소자 분리막(STI 라이너)을 형성하기 위함이다.",
    prerequisites: [
      { id: "wafer-fabrication", name: "웨이퍼 세정(RCA Clean) 및 표면 파티클 제거" }
    ],
    principles: [
      "딜-그로브(Deal-Grove) 산화 모델: 산화막 두께 x와 시간 t는 수식 x² + Ax = B(t + τ)를 따른다. 박막 초기에는 표면 반응 제한 영역(Linear regime: x ∝ t)을 따르고, 막이 두꺼워지면 산화종의 산화막 내부 확산 제한 영역(Parabolic regime: x² ∝ t)을 따른다.",
      "건식 산화 (Dry Oxidation): Si + O2 → SiO2 반응을 이용하며, 성장 속도는 느리지만 산화막의 밀도가 높고 계면 결함 밀도(Dit)가 낮아 고품질 게이트 절연막 및 얇은 패시베이션 산화막에 적용된다.",
      "습식 산화 (Wet Oxidation): Si + 2H2O → SiO2 + 2H2 반응을 이용하며, 물 분자의 높은 용해도와 빠른 확산 속도로 건식 대비 성장 속도가 5~10배 빠르지만 수소 부산물로 인해 막질 밀도가 상대적으로 낮아 두꺼운 필드 산화막 및 마스킹층에 적용된다."
    ],
    limitations: [
      "실리콘 소모 현상: 산화막이 성장할 때 최종 SiO2 두께의 약 44%에 해당하는 하부 벌크 실리콘이 반응하여 소모되므로 단차 및 치수 설계 시 사전 보정이 필수적이다.",
      "부피 팽창에 따른 진성 응력(Intrinsic Stress): Si와 SiO2의 몰 부피 차이(약 2.2배)로 인해 계면에 강한 압축 응력(Compressive Stress)이 축적되어 웨이퍼 휨을 유발한다."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "Deal-Grove 모델에 기반한 열역학적 산화 메커니즘",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 첨단 낸드/DRAM 제조",
        description: "고종횡비 소자 분리 및 터널 산화막 품질 관리",
        appliedCase: {
          code: "OX-STI-01",
          title: "3D NAND 페리 영역 STI 라이너 건식 산화막 형성",
          conditions: "온도 950°C 건식 산화, 순수 산소 유량 5 slm, 두께 5nm 정밀 제어, Dit < 1×10^10 cm^-2eV^-1 유지.",
          limitationNote: "산화 시간 과다 시 활성 영역 임계 치수(CD) 축소 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-oxidation", name: "2. 산화 공정 (Oxidation)" }],
      part_of: [{ id: "oxidation-furnace", name: "수직형 열산화 확산로(Vertical Diffusion Furnace)" }],
      next_step: [{ id: "photolithography", name: "3. 포토 공정 (Photolithography)" }]
    },
    evidences: {
      "E-SAM-02": {
        id: "E-SAM-02",
        sourceName: "삼성반도체 8대 공정 공식 교육 연재 [2편: 산화 공정]",
        pubDate: "2024.01",
        type: "반도체 제조사 공식 기술 아카이브",
        quote: "산화 공정은 고온에서 산소나 수증기를 웨이퍼 표면에 반응시켜 실리콘 산화막을 형성하는 과정으로, 건식 산화와 습식 산화로 구분되어 용도에 따라 선택적으로 적용된다.",
        externalUrl: "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/oxidation/",
        urlLabel: "삼성반도체 산화 공정 공식 웹페이지 바로가기"
      }
    }
  },

  // =========================================================================
  // 3. 포토리소그래피 공정 (Photolithography Standard Pipeline) - Samsung Neutralized
  // =========================================================================
  "photolithography": {
    id: "photolithography",
    facetId: "facet-process",
    processId: "proc-photo",
    processName: "포토 공정",
    title: "포토리소그래피 공정 (Photolithography)",
    engName: "Photolithography Process",
    aliases: ["포토 공정", "노광 공정", "리소그래피", "패터닝 공정"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 & SEMI E10 표준 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "웨이퍼 표면에 감광액(Photoresist)을 도포하고, 포토마스크에 형성된 회로 패턴에 단파장 빛을 투과·노광한 뒤 현상액을 통해 특정 영역을 선택적으로 용해·제거하여 나노스케일 2차원 회로 형상을 전사하는 8단계 정밀 화학·광학 공정이다.",
    purpose: "후속 식각 및 이온 주입 공정에서 웨이퍼의 특정 타깃 영역만을 물리·화학적으로 개질할 수 있도록 보호 마스크 패턴을 정의하기 위함이다.",
    prerequisites: [
      { id: "thermal-oxidation", name: "산화막 또는 증착 박막 기판 준비" }
    ],
    principles: [
      "표준 8단계 시퀀스: ① 표면 처리(HMDS 기상 프라이밍으로 친수성 웨이퍼를 소수성으로 개질) → ② 감광액 스핀 코팅(Spin Coating, 두께 균일도 ±1nm) → ③ 소프트 베이크(Soft Bake, 솔벤트 90% 휘발) → ④ 정렬 및 노광(Alignment & Exposure) → ⑤ 노광 후 가열(PEB: Post-Exposure Bake, 정재파 효과 제거 및 화학증폭 활성화) → ⑥ 현상(Development: TMAH 2.38% 용액 현상) → ⑦ 하드 베이크(Hard Bake, 잔류 수분 제거 및 에칭 내성 강화) → ⑧ 비파괴 광학 검사(CD 및 오버레이 측정).",
      "광화학 반응 원리: 양성 감광액(Positive PR)은 노광 영역의 광산발생제(PAG)가 산(H+)을 발생시키고 PEB 열에 의해 고분자 보호기가 탈리되어 알칼리 현상액에 가용성으로 전환된다. 음성 감광액(Negative PR)은 노광 영역이 광가교 결합을 형성하여 불용성으로 남는다."
    ],
    limitations: [
      "정재파 효과(Standing Wave Effect): 기판 반사광과 입사광의 간섭으로 인해 레지스트 측벽에 리플(Ripple) 줄무늬 단차가 형성되어 선폭 제어가 왜곡될 수 있음(하부 반사방지막 BARC 적용 필수).",
      "초점 심도(Depth of Focus, DOF) 제약: 해상도를 높이기 위해 개구수(NA)를 키우거나 파장을 줄이면 DOF = k2 * (λ / NA²) 수식에 의해 초점 마진이 급감하여 웨이퍼 토폴로지 단차에서 패턴 디포커스 결함 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "클린룸 트랙-스캐너 인라인 연동 8단계 리소그래피 파이프라인",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 선단 로직 ArFi 액침 리소그래피 사양",
        description: "선단 7nm/5nm 파운드리 DUV 액침(Immersion) 트랙-스캐너 인라인 레시피",
        appliedCase: {
          code: "LITHO-DUV-IMMER",
          title: "선단 파운드리 ArFi 193nm 액침 리소그래피 공정 사양",
          conditions: "NA 1.35 렌즈계와 초순수(DI Water, n=1.44) 매질 결합, 액침 워터마크 결함 < 0.05 defects/cm² 관리.",
          evidenceId: "E-SAM-04",
          limitationNote: "스캔 속도 > 600mm/s 초과 시 미세 기포(Micro-bubble) 형성으로 패턴 브릿지 불량 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-photo", name: "3. 포토 공정 (Photolithography)" }],
      part_of: [{ id: "track-scanner-cluster", name: "인라인 트랙 & 스캐너 클러스터 시스템" }],
      next_step: [{ id: "plasma-dry-etch", name: "4. 식각 공정 (Etching)" }]
    },
    evidences: {
      "E-SAM-04": {
        id: "E-SAM-04",
        sourceName: "삼성반도체 8대 공정 공식 교육 연재 [4편: 포토 공정]",
        pubDate: "2024.01",
        type: "반도체 제조사 공식 기술 아카이브",
        quote: "포토 공정은 마스크 상의 회로 패턴을 감광액이 도포된 웨이퍼 위에 빛을 투과시켜 전사하는 핵심 공정으로, 감광액 도포, 노광, 현상의 일련의 화학·광학적 단계로 구성된다.",
        externalUrl: "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/photolithography/",
        urlLabel: "삼성반도체 포토 공정 공식 웹페이지 바로가기"
      }
    }
  },

  // =========================================================================
  // 4. 극자외선 노광 (EUV Lithography & LPP Optics) - ASML Physics
  // =========================================================================
  "euv-lithography": {
    id: "euv-lithography",
    facetId: "facet-process",
    processId: "proc-photo",
    processName: "포토 공정",
    title: "EUV 극자외선 노광 시스템 (EUV Lithography)",
    engName: "EUV Lithography",
    aliases: ["EUV", "극자외선 노광", "0.33 NA EUV", "LPP 광원"],
    status: "채택됨",
    verificationLevel: "ASML 공식 백서 & SPIE JM3 학술 교차 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "파장 13.5nm의 극자외선(EUV) 광원을 사용하여 레일리 해상도 한계(CD = k1 * λ / NA)를 획기적으로 낮춤으로써 서브-7nm 선단 로직 및 10nm급 DRAM 셀을 단일 노광(Single Exposure)으로 패터닝하는 전반사 진공 노광 시스템이다.",
    purpose: "ArF 액침(193nm) 리소그래피의 다중 패터닝(SADP, SAQP) 복잡도와 마스크 매수 증가로 인한 수율 저하 및 생산 단가 폭증을 극복하기 위함이다.",
    prerequisites: [
      { id: "photolithography", name: "초고진공(10^-7 mbar) 챔버 환경 및 주석(Sn) 드롭릿 공급계" }
    ],
    principles: [
      "레이저 생성 플라즈마 (LPP) 광원: 진공 챔버 내에서 직경 25μm의 고순도 액체 주석(Sn) 드롭릿을 초당 50,000회 고속 분사하고, 30kW CO2 펄스 레이저를 2회 타격(프리펄스로 납작하게 만든 후 메인펄스 방전)하여 주석 원자를 수십만 도의 고밀도 플라즈마 상태(Sn8+~Sn14+)로 여기시켜 13.5nm EUV 광자를 방출한다.",
      "브래그 반사 광학계 (Bragg Reflective Optics): 13.5nm 파장은 모든 물질(공기, 유리)에 흡수되므로 렌즈 투과가 불가능하여 진공 환경에서 Mo/Si 40~50쌍 다층막 거울을 사용한다. 거울 1매당 이론 반사율은 약 70%이며, 11회 전반사를 거쳐 웨이퍼에 도달하는 유효 광량은 입사광의 약 2% 수준으로 감소한다.",
      "광투과형 펠리클(Pellicle) 보호 및 수소 세정: 마스크 오염을 막기 위해 400W 고출력 레이저 조사 시 800°C 고열을 견디고 투과율 > 90%를 유지하는 Ru/MoSi2 캡핑 탄소나노튜브(CNT) 펠리클을 적용하며, 챔버 내 수소 플라즈마를 주입하여 잔류 주석 오염물을 가스(SnH4↑) 상태로 배출한다."
    ],
    limitations: [
      "광자 샷 노이즈(Photon Shot Noise)와 확률론적 결함: EUV 광자 1개의 에너지가 91.8eV로 매우 높아 동일 노광량(Dose)에서 도달하는 광자 수가 ArF의 1/14에 불과하여, 광자 수의 통계적 요동으로 인한 마이크로 브릿지(Micro-bridge) 및 라인 단선 결함 위험이 존재한다.",
      "광원 전력 대비 극히 낮은 총 효율: 30kW급 CO2 레이저를 투입하여 수백 W의 극자외선을 생성하고 다층막 반사 후 웨이퍼에 도달하는 빛은 수 W에 불과하여 대형 칠러 설비 및 천문학적 소비 전력이 요구된다."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "ASML NXE 시리즈 0.33 NA EUV 스캐너의 물리 원리",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 첨단 DRAM 1a/1b nm 양산",
        description: "DRAM 비트라인 및 커패시터 콘택 홀 레이어 적용",
        appliedCase: {
          code: "EUV-DRAM-1B",
          title: "1b nm DRAM 비트라인 패터닝 EUV 단일 노광 적용",
          conditions: "Dose: 45 mJ/cm², 스캐너 출력: 350W, 오버레이 정렬 오차: < 1.5nm (ASML NXE:3600D 기준).",
          limitationNote: "도즈를 과도하게 낮출 경우 스토캐스틱 라인 에지 러프니스(LER) 열화 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-photo", name: "3. 포토 공정 (Photolithography)" }],
      part_of: [{ id: "euv-scanner", name: "ASML NXE 0.33 NA 스캐너" }],
      next_step: [{ id: "plasma-dry-etch", name: "4. 식각 공정 (Etching)" }]
    },
    evidences: {
      "E-ASML-01": {
        id: "E-ASML-01",
        sourceName: "ASML Technology Whitepaper: The Power of EUV",
        pubDate: "2023.10",
        type: "노광 장비사 공식 기술 백서",
        quote: "EUV lithography uses light with a wavelength of 13.5 nm, which enables chipmakers to print smaller features using a simpler process than optical lithography with deep UV light.",
        externalUrl: "https://www.asml.com/en/technology/lithography-principles",
        urlLabel: "ASML 극자외선 노광 공식 기술 백서 바로가기"
      }
    }
  },

  // =========================================================================
  // 5. High-NA EUV 노광 (High-NA 0.55 Anamorphic Optics) - ASML Physics
  // =========================================================================
  "high-na-euv": {
    id: "high-na-euv",
    facetId: "facet-process",
    processId: "proc-photo",
    processName: "포토 공정",
    title: "High-NA EUV 노광 시스템 (High-NA EUV Lithography)",
    engName: "High-NA EUV Lithography",
    aliases: ["High-NA", "0.55 NA EUV", "EXE:5000", "아나모픽 노광"],
    status: "채택됨",
    verificationLevel: "ASML 공식 백서 & imec 공동 연구 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "투영 광학계의 개구수(NA)를 기존 0.33에서 0.55로 대폭 끌어올려 단일 노광 해상도를 8nm까지 축소시키며, 3D 마스크 섀도잉 효과를 극복하기 위해 가로/세로 배율이 다른 아나모픽(Anamorphic) 광학계(X축 4배, Y축 8배 축소)를 적용한 2nm 이하 초미세 노드용 차세대 리소그래피 시스템이다.",
    purpose: "0.33 NA EUV에서도 불가피해진 2nm 이하 로직의 더블 패터닝(EUV double patterning)을 단일 노광으로 단순화하여 공정 결함 감소 및 수율 극대화를 달성하기 위함이다.",
    prerequisites: [
      { id: "euv-lithography", name: "0.33 NA EUV 인프라 및 차세대 금속 산화물 레지스트(MOR)" }
    ],
    principles: [
      "아나모픽 비대칭 배율 투영 (Anamorphic Optics): NA가 0.55로 증가함에 따라 마스크에 입사하는 빛의 각도가 커져 마스크 흡수체 패턴 뒷면에 그림자가 지는 3D 섀도잉(Mask 3D Effect)이 발생한다. 이를 방지하기 위해 마스크 상에서 각도 마진을 확보하고자 입사면 방향(Y축)만 8배로 축소하고 수평면(X축)은 기존 4배 축소를 유지하는 비대칭 배율 렌즈계를 채택한다.",
      "하프 필드 스캔 (Half-Field Scanning): Y축 8배 축소로 인해 웨이퍼 상의 노광 노출 면적(Field Size)이 기존 표준(26mm × 33mm)의 절반인 26mm × 16.5mm로 줄어든다. 거대 다이(Large AI Chip) 노광 시 두 개의 하프 필드를 나노미터 오차 없이 이어 붙이는 스티칭(Stitching) 알고리즘이 적용된다.",
      "주석 옥소 케이지 금속 산화물 레지스트(MOR): 유기 CAR의 산 확산(Acid Diffusion Blur) 한계를 극복하기 위해 Sn-Oxide 코어 기반의 무기 MOR을 적용하여 피치 20nm 이하에서 LER < 1.8nm를 달성한다."
    ],
    limitations: [
      "극단적인 초점 심도 축소 (DOF < 20nm): DOF = k2 * λ / NA² 수식에 의해 NA 0.55에서 초점 허용 마진이 20nm 이하로 급감하므로, 웨이퍼의 미세 휨과 두께 불균일을 실시간으로 보정하는 초정밀 압전 척 액추에이터 제어가 필수적이다.",
      "하프 필드 스티칭 오버레이 결함: 스티칭 경계면에서 수 나노미터의 정렬 오차 발생 시 초대형 AI 가속기 칩의 내부 버스 배선이 단선되거나 저항이 폭증할 위험이 존재한다."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "ASML EXE:5000/5200 시리즈 0.55 NA 아나모픽 광학 사양",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 2nm/A14 이하 선단 파운드리",
        description: "차세대 GAA 로직 표준 셀 및 BSPDN 나노 비아 패터닝",
        appliedCase: {
          code: "HNA-A14-LOGIC",
          title: "A14 노드 금속 배선 피치 20nm 단일 노광 형성",
          conditions: "Dose: 65 mJ/cm² (MOR 감광액), 스캐너 스테이지 가속도: 8g, 스티칭 오버레이: < 1.1nm.",
          limitationNote: "레지스트 도즈 증가로 시간당 웨이퍼 처리량(WPH)이 0.33 NA 대비 약 20% 감소."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-photo", name: "3. 포토 공정 (Photolithography)" }],
      part_of: [{ id: "high-na-scanner", name: "ASML EXE:5000/5200 High-NA 스캐너" }],
      next_step: [{ id: "ale-etch", name: "원자층 식각 공정 (ALE)" }]
    },
    evidences: {
      "E-ASML-02": {
        id: "E-ASML-02",
        sourceName: "ASML & imec High-NA Joint Roadmap Briefing",
        pubDate: "2024.02",
        type: "노광 장비사 공식 로드맵",
        quote: "High-NA EUV introduces 0.55 NA anamorphic optics (4x/8x magnification) to print features down to 8 nm, enabling 2nm and sub-2nm semiconductor production with single exposure.",
        externalUrl: "https://www.asml.com/en/technology/lithography-principles/high-na-euv",
        urlLabel: "ASML High-NA 공식 기술 로드맵 바로가기"
      }
    }
  },

  // =========================================================================
  // 6. 모델 기반 광학 근접 효과 보정 (Model-based OPC) - Optical Physics
  // =========================================================================
  "model-based-opc": {
    id: "model-based-opc",
    facetId: "facet-process",
    processId: "proc-photo",
    processName: "포토 공정",
    title: "광학 근접 효과 보정 OPC (Optical Proximity Correction)",
    engName: "Model-based Optical Proximity Correction",
    aliases: ["OPC", "모델 기반 OPC", "마스크 보정", "역보정"],
    status: "채택됨",
    verificationLevel: "SPIE 1994 분수령 논문 & ASML YieldStar 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "빛의 회절 한계와 레지스트 현상 공정에서 발생하는 미세 패턴 왜곡(모서리 둥글림, 라인 끝단 수축, 선폭 편차)을 광학 모델로 시뮬레이션하여 마스크 상에 역보정 형상(Serif, Hammerhead, SRAF)을 자동 생성하고, 계측 데이터(YieldStar)와 연동하여 실시간 피드백하는 폐루프 리소그래피 최적화 기술이다.",
    purpose: "설계된 CAD 레이아웃의 정확한 직사각형 프로파일이 실제 웨이퍼 상에 전사되도록 마스크 왜곡을 물리적으로 선반영 보상하기 위함이다.",
    prerequisites: [
      { id: "photolithography", name: "스캐너 조명계(Illumination) 모델 및 레지스트 화학 모델" }
    ],
    principles: [
      "호프킨스 부분 결맞음 회절 모델: 광학계의 수차와 회절을 컨볼루션 연산으로 모델링하여 광학상(Aerial Image) 강도 분포를 계산하고, 레지스트 임계 강도(Threshold)와의 교차점을 역산한다.",
      "역보정 형상 배치: 라인 모서리 둥글림을 방지하기 위한 세리프(Serif), 라인 끝단 수축(Line-end shortening)을 보상하는 해머헤드(Hammerhead), 비해상 보조 패턴(SRAF: Sub-Resolution Assist Feature)을 마스크에 자동 삽입하여 초점 심도(DOF)를 확장한다.",
      "홀리스틱 리소그래피 폐루프(R2R): 스캐너 노광 후 YieldStar 회절 산란계가 실시간 측정한 오버레이 및 초점 오차를 스캐너 소프트웨어와 OPC 엔진에 전달하여 다음 랏(Lot) 마스크 보정 파라미터를 자동 튜닝한다."
    ],
    limitations: [
      "마스크 데이터 파일 크기 및 연산 폭증: 서브-3nm 노드에서 역보정 파형이 복잡해짐에 따라 마스크 데이터(OASIS) 용량이 테라바이트급으로 증가하고 마스크 전자빔 묘화 시간(Write Time)이 수십 시간으로 급증함.",
      "SRAF 프린팅 불량(SRAF Print-out): 보조 패턴이 공정 마진 범위를 벗어나 실제 웨이퍼 위에 잔류 패턴으로 인쇄되어 브릿지 쇼트 결함을 유발할 수 있음."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "EDA 마스크 합성 엔진과 스캐너 광학 모델 간 인터페이스",
        appliedCase: null
      },
      "domain-logic": {
        label: "도메인: 3nm 로직 ILT 역보정 사양",
        description: "3nm GAA 로직 다이 풀칩 SRAF(Sub-resolution Assist Feature) 최적화",
        appliedCase: {
          code: "OPC-3NM-GAA",
          title: "3nm 선단 파운드리 ILT(Inverse Lithography) 풀칩 보정 사양",
          conditions: "광학 역산 연산 가속기를 통해 코너 라운딩 및 라인 엔드 풀백 오차 < 0.5nm 보정, EPE 마진 15% 확보.",
          evidenceId: "E-TIER1-OPC",
          limitationNote: "마스크 데이터 볼륨 급증으로 마스크 묘화 시간(Write Time) 24시간 초과 리스크."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-photo", name: "3. 포토 공정 (Photolithography)" }],
      part_of: [{ id: "eda-mask-synthesis", name: "EDA 마스크 합성 소프트웨어 플랫폼" }],
      next_step: [{ id: "euv-lithography", name: "극자외선 노광 공정 (EUV)" }]
    },
    evidences: {
      "E-TIER1-OPC": {
        id: "E-TIER1-OPC",
        sourceName: "Automated Optical Proximity Correction (SPIE 1994)",
        pubDate: "1994.05",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "Model-based approach simulates diffraction and resist development to automatically pre-distort mask patterns, eliminating corner rounding and line-end shortening.",
        externalUrl: "https://doi.org/10.1117/12.175444",
        urlLabel: "SPIE OPC 원조 논문 DOI 링크 바로가기"
      }
    }
  },

  // =========================================================================
  // 7. 플라즈마 반응성 이온 식각 (Plasma Dry Etch / RIE) - Lam Physics
  // =========================================================================
  "dry-etch": {
    id: "dry-etch",
    facetId: "facet-process",
    processId: "proc-etch",
    processName: "식각 공정",
    title: "플라즈마 건식 식각 (Reactive Ion Etching - RIE)",
    engName: "Reactive Ion Etching",
    aliases: ["RIE", "건식 식각", "드라이 에칭", "플라즈마 식각"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 & Lam Research 공정 매뉴얼 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "진공 챔버 내에서 고주파(RF) 전력으로 에칭 가스를 플라즈마 상태로 해리시켜 화학적 반응성을 지닌 중성 라디칼과 방향성을 지닌 양이온을 생성하고, 하부 바이어스로 가속된 이온의 물리적 충돌과 라디칼의 화학 반응을 결합하여 박막을 수직 이방성으로 선택 제거하는 공정이다.",
    purpose: "등방성(Isotropic) 언더컷이 발생하는 습식 식각의 물리적 한계를 극복하고 나노스케일(Sub-10nm) 수직 프로파일을 정밀하게 형성하기 위함이다.",
    prerequisites: [
      { id: "photolithography", name: "포토레지스트 또는 하드마스크 패터닝 기판" }
    ],
    principles: [
      "이온 보조 식각 메커니즘 (Ion-assisted Etching): 중성 불화탄소 라디칼(CFx)이 표면에 흡착되어 휘발성 반응 생성물(SiF4↑)을 형성하기 전, 수직으로 입사하는 고에너지 Ar+/CFx+ 이온이 결합을 끊어 반응 활성화 에너지를 대폭 낮춘다.",
      "플라즈마 소스-바이어스 디커플링 (ICP/CCP): 소스 RF(13.56MHz~60MHz)로 플라즈마 밀도(이온/라디칼 플럭스)를 독립 제어하고, 기판 척 바이어스 RF(400kHz~2MHz)로 입사 이온의 가속 에너지(Ion Energy)를 분리 제어하여 이방성과 마스크 선택비를 동시 확보한다.",
      "측벽 보호막(Passivation) 동역학: 에칭 부산물과 플라즈마 중합체가 패턴 측벽에 폴리머(CF2)n 박막을 형성하여 횡방향 침식을 차단하고 완벽한 수직 트렌치를 구현한다."
    ],
    limitations: [
      "플라즈마 유도 손상 (Plasma Induced Damage, PID): 고에너지 충돌 이온이 실리콘 기판 내부 격자를 붕괴(Amorphization)시키거나 게이트 절연막에 충전 전하(Charging Damage)를 축적시켜 절연 파괴(TDDB)를 유발함.",
      "마이크로 로딩 및 종횡비 의존 식각 (ARDE): 패턴 밀도가 높은 영역이나 종횡비가 깊은 비아 홀에서 반응 가스 유입 및 부산물 배출 지연으로 식각 속도가 느려지는 에칭 지연 현상 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "RIE 단위 공정의 물리적 스퍼터링과 화학적 식각 균형",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 첨단 3D NAND 제조",
        description: "옥사이드/나이트라이드 교번 적층 박막 식각",
        appliedCase: {
          code: "ET-NAND-ON",
          title: "3D NAND ONON 적층 박막 고선택비 식각",
          conditions: "C4F8/CH2F2/O2 가스 혼합, 소스 2500W, 듀얼 바이어스 5000W 인가, 카본 하드마스크 선택비 > 15:1 유지.",
          limitationNote: "과도한 폴리머 형성 시 홀 입구가 막히는 클로깅(Clogging) 결함 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-etch", name: "4. 식각 공정 (Etching)" }],
      part_of: [{ id: "plasma-chamber", name: "ICP/CCP 플라즈마 식각 챔버" }],
      next_step: [{ id: "ashing-clean", name: "포토레지스트 애싱 및 세정 공정" }]
    },
    evidences: {
      "E-LAM-01": {
        id: "E-LAM-01",
        sourceName: "Lam Research Technical Glossary: Dry Etch Fundamentals",
        pubDate: "2024.01",
        type: "장비사 공식 기술 용어집",
        quote: "Plasma etch utilizes reactive gases energized into a plasma state to remove material selectively from wafer surfaces via chemical reactions and ion bombardment.",
        externalUrl: "https://www.lamresearch.com/technical-glossary/",
        urlLabel: "Lam Research 기술 용어집 원문 바로가기"
      }
    }
  },

  // =========================================================================
  // 8. 극저온 고종횡비 식각 (Cryogenic Etching) - Tier 1/2 Physics
  // =========================================================================
  "cryogenic-etch": {
    id: "cryogenic-etch",
    facetId: "facet-process",
    processId: "proc-etch",
    processName: "식각 공정",
    title: "극저온 HARC 식각 (Cryogenic Etching)",
    engName: "Cryogenic Etching",
    aliases: ["극저온 식각", "Cryo Etch", "HARC 식각", "극저온 플라즈마"],
    status: "채택됨",
    verificationLevel: "Applied Physics Letters 1988 & AVS JVST 2023 교차 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "웨이퍼 기판 온도를 -60°C~-130°C의 극저온으로 급랭하여 측벽에서의 자발적 화학 반응을 동결(Arrhenius 반응 속도 차단)시킴으로써, 무거운 유기 폴리머 보호막 증착 없이도 순수 이온 충돌만으로 종횡비 80:1 이상의 깊은 수직 채널홀을 비틀림 없이 깎아내는 차세대 식각 기술이다.",
    purpose: "300단 이상 3D NAND의 초고종횡비 채널홀 공정에서 기존 상온 식각의 마스크 과소모, 홀 틸팅/보잉 결함 및 식각 정지(Etch Stop)를 원천 차단하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "극저온 헬륨 칠러 ESC 정전척 챔버 및 고밀도 하드마스크" }
    ],
    principles: [
      "아레니우스 반응 속도 동결: k = A * exp(-Ea / kB*T) 수식에 따라 기판 온도가 상온(300K)에서 극저온(180K~150K)으로 냉각되면 측면 자발 에칭 반응 속도 k가 4자리수 이상 급감하여 언더컷이 발생하지 않는다.",
      "무폴리머 초고속 식각: SF6/O2 또는 순수 할로겐 가스만으로 측벽을 자연 패시베이션하므로 폴리머 침적에 의한 홀 막힘(Clogging) 없이 식각 속도를 상온 대비 2.5배 이상 가속한다.",
      "동기화 펄스 바이어스 전하 중화: 10~50kHz 펄스 RF의 Off 구간 동안 열전자가 10μm 이상 깊은 홀 바닥으로 유입되어 양이온 축적 전하를 중화함으로써 이온 궤적 굴절에 의한 홀 틸팅(Tilting)을 3nm 이내로 방지한다."
    ],
    limitations: [
      "초저온 유지에 따른 설비 전력 소비 및 칠러 발열: 대구경 300mm 웨이퍼를 연속으로 -60°C 이하로 유지하기 위한 액체 질소/특수 헬륨 칠러의 팹 전력 소모와 탄소 배출이 증가함.",
      "식각 후 승온 과정의 수분 응결 결함: 에칭 완료 후 진공 챔버에서 상온으로 복귀할 때 결로 현상으로 인한 웨이퍼 파티클 오염 위험이 있어 질소 퍼지 로드락 진공 승온 시퀀스가 필수적임."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "극저온 표면 흡착 및 무폴리머 이방성 RIE 물리학",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 300단+ 3D NAND 양산 팹",
        description: "종횡비 80:1 이상의 채널 홀 일괄 식각 적용",
        appliedCase: {
          code: "CRYO-NAND-300",
          title: "300단 V-NAND 12μm 채널 홀 관통 공정",
          conditions: "정전척 온도: -60°C, RF 펄스 주파수: 20kHz, 듀티비: 25%, 식각 깊이: 11.5μm, 바닥 편차: < 2.8nm.",
          limitationNote: "정전척 헬륨 가스 누설 발생 시 웨이퍼 엣지 영역 급격한 온도 상승 및 보잉 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-etch", name: "4. 식각 공정 (Etching)" }],
      part_of: [{ id: "cryo-etch-chamber", name: "극저온 칠러 장착 플라즈마 챔버" }],
      next_step: [{ id: "ald-deposition", name: "5. 박막 증착 공정 (ALD)" }]
    },
    evidences: {
      "E-TIER1-CRYO": {
        id: "E-TIER1-CRYO",
        sourceName: "Low-temperature reactive ion etching (Appl. Phys. Lett. 1988)",
        pubDate: "1988.04",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "Freezing spontaneous reaction at cryogenic temperatures enables purely ion-driven vertical anisotropy without thick polymer sidewalls.",
        externalUrl: "https://doi.org/10.1063/1.99382",
        urlLabel: "APL 극저온 RIE 원조 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 9. 원자층 식각 (Atomic Layer Etching - ALE) - Lam Equipment Physics
  // =========================================================================
  "ale-etch": {
    id: "ale-etch",
    facetId: "facet-process",
    processId: "proc-etch",
    processName: "식각 공정",
    title: "원자층 식각 (Atomic Layer Etching - ALE)",
    engName: "Atomic Layer Etching",
    aliases: ["ALE", "원자층 식각", "디지털 식각", "원자단위 식각"],
    status: "채택됨",
    verificationLevel: "Lam Research 기술 백서 & ECS Journal 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "원자층 증착(ALD)의 역과정으로, 화학적 표면 흡착(개질) 단계와 물리적 이온 탈착 단계를 공간적·시간적으로 엄격히 분리 순환시킴으로써 자기 제한적(Self-limiting) 반응을 통해 1사이클당 단원자층(1~1.5Å) 단위로 박막을 제거하는 극미세 디지털 식각 기술이다.",
    purpose: "3nm 이하 선단 트랜지스터(GAA)의 극미세 게이트 및 콘택 형성 시 하부 박막의 플라즈마 대미지 없이 원자 수준의 표면 평탄도와 무한대에 가까운 극한 선택비를 달성하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "초고속 가스 스위칭 밸브 및 저에너지 이온 빔 제어 시스템" }
    ],
    principles: [
      "2단계 자기 제한적 시퀀스: ① 표면 개질(Modification): 염소(Cl2) 또는 불소 가스를 주입하여 타깃 표면 단원자층과 반응시켜 화학 결합력이 약화된 염화물(SiClx) 층을 자발 형성하고 잔류 가스를 퍼지한다. ② 원자 탈착(Removal): 벌크 실리콘의 스퍼터링 문턱 에너지(약 50eV) 이하인 저에너지 Ar+ 이온(20~30eV)을 입사시켜 개질된 SiClx 층만을 선택적으로 튕겨내고 반응을 자동 중단한 뒤 퍼지한다.",
      "두께 디지털 제어성: 사이클 횟수(Cycle count)에 의해 최종 제거 두께가 선형적으로 결정되므로 로딩 효과(Loading Effect)가 전혀 발생하지 않는다."
    ],
    limitations: [
      "극히 느린 공정 속도(Throughput / TAT): 1사이클에 제거되는 두께가 약 0.1nm 수준으로, 사이클당 퍼지 시간이 소요되어 수십 나노미터 이상의 깊은 패턴 식각에는 생산성이 현저히 떨어짐.",
      "초정밀 저에너지 RF 제어 난도: 이온 에너지가 50eV를 1eV라도 초과할 경우 하부 벌크 실리콘의 물리적 스퍼터링이 발생하여 ALE의 자기 제한성 특성이 상실됨."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "자기 제한적 표면 흡착 및 저에너지 탈착 순환 동역학",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 3nm/2nm GAA 파운드리 라인",
        description: "나노시트 게이트 리세스 및 콘택 에어리어 원자 클리닝",
        appliedCase: {
          code: "ALE-GAA-RECESS",
          title: "3nm GAA 트랜지스터 콘택 계면 ALE 처리",
          conditions: "Cl2 흡착 시간: 0.8초, Ar 퍼지: 1.2초, Ar+ 탈착 RF: 25W (25eV), 총 40사이클 적용(4nm 정밀 제거).",
          limitationNote: "Ar+ 이온 각도 산란 시 트렌치 측벽 모서리 라운딩 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-etch", name: "4. 식각 공정 (Etching)" }],
      part_of: [{ id: "ale-reactor", name: "고속 밸브 탑재 ALE 전용 플라즈마 챔버" }],
      next_step: [{ id: "ald-deposition", name: "5. 박막 증착 공정 (ALD)" }]
    },
    evidences: {
      "E-LAM-02": {
        id: "E-LAM-02",
        sourceName: "Lam Research: Atomic Layer Etch Fundamentals and Applications",
        pubDate: "2023.08",
        type: "장비사 공식 기술 백서",
        quote: "Atomic layer etching (ALE) removes thin layers of material using sequential reaction steps that are self-limiting, delivering atomic-scale control on sub-3nm architectures.",
        externalUrl: "https://www.lamresearch.com/technology/atomic-layer-etching/",
        urlLabel: "Lam Research ALE 공식 기술 백서 바로가기"
      }
    }
  },

  // =========================================================================
  // 10. GAA SiGe 초격자 선택식각 & Inner Spacer (GAA Nanosheet Release) - Tier 1/2 Academic
  // =========================================================================
  "gaa-nanosheet-etch": {
    id: "gaa-nanosheet-etch",
    facetId: "facet-process",
    processId: "proc-etch",
    processName: "식각 공정",
    title: "GAA 나노시트 선택 식각 (GAA Selective Etch)",
    engName: "GAA Nanosheet SiGe Release & Inner Spacer",
    aliases: ["GAA 식각", "나노시트 릴리즈", "SiGe 선택식각", "Inner Spacer"],
    status: "채택됨",
    verificationLevel: "IBM IEDM 2017 & IEEE TED 2021 학술 교차 검증",
    lastReviewed: "2026.10.15 (Sprint 1 추출 검증 완료)",
    version: "v2.0",
    summary: "GAA(Gate-All-Around) 나노시트 선택 식각은 3nm/2nm 이하 선단 로직 트랜지스터에서 채널을 형성하기 위해, 교대로 적층된 Si/SiGe 초격자 층 중 SiGe만을 손상 없이 선택적으로 제거하여 실리콘 나노시트 채널을 공중에 띄우는(Sheet Release) 핵심 식각 공정이다. 이후 게이트와 소스/드레인 간 기생 용량을 차단하기 위해 SiBCN/SiOCN 저유전체 Inner Spacer를 공동 내에 정밀 형성한다.",
    purpose: "게이트 금속이 실리콘 나노시트 채널 4면을 완전히 감싸 전류 구동력을 극대화하고, 나노시트 사이의 미세 갭에서 발생하는 기생 정전용량(Cgs, Cgd)을 차단하여 스위칭 속도를 확보하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "Si/SiGe 다층 에피택시 및 수직 핀 식각 기판" }
    ],
    principles: [
      "무플라즈마 기상 열 화학 반응: ClF3 또는 CF4/O2 다운스트림 라디칼 가스를 인가하여 Ge 원자의 자발 산화/불화 촉매 반응을 유도한다. SiGe 층의 화학 반응 활성화 에너지가 Si보다 현저히 낮음을 활용하여 플라즈마 물리 충격 없이 순수 화학 반응만으로 수평 등방성 선택 제거를 달성한다.",
      "초고선택비 및 표면 거칠기 보존: SiGe:Si 선택비를 > 150:1로 유지하여 상하 실리콘 나노시트의 두께 손실을 0.2nm 이하로 억제하고, 채널 표면 RMS 거칠기를 0.15nm 이하로 제어하여 전자 이동도 저하를 방지한다.",
      "저유전체 Inner Spacer 형성: SiGe 제거 후 형성된 나노시트 사이의 리세스 캐비티에 원자층 증착(ALD)으로 k ≈ 4.2 수준의 SiBCN 박막을 채운 뒤, 채널 외부 박막만 선택적으로 제거하는 고정밀 등방성 ALE를 수행하여 게이트 기생 커패시턴스를 44% 감쇄시킨다."
    ],
    limitations: [
      "나노시트 융합(Stiction) 결함: SiGe 층을 제거하고 남은 수 나노미터 두께의 얇은 Si 나노시트들이 세정액 건조 시 모세관력에 의해 상하 시트끼리 달라붙는 스틱션(Stiction) 현상이 발생할 수 있음(초임계 CO2 건조 필수).",
      "게르마늄 잔류물(Ge Residue) 오염: SiGe 식각 잔류물이 나노시트 하부에 미량 남아 있을 경우 차세대 HKMG 게이트 절연막 증착 시 계면 트랩을 형성하여 문턱전압 산포를 유발함."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "GAA 나노시트 채널 릴리즈 및 내부 스페이서 화학 역학",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 3nm/2nm 파운드리 양산 팹",
        description: "MBCFET 나노시트 3단/4단 적층 채널 형성 실무",
        appliedCase: {
          code: "GAA-REL-3NM",
          title: "3nm 파운드리 나노시트 릴리즈 공정",
          conditions: "ClF3 가스 유량 80 sccm, 챔버 압력 1.5 Torr, 온도 85°C 무플라즈마 반응, SiGe 선택비 180:1 유지, 시트 손실 0.15nm.",
          limitationNote: "온도가 100°C를 초과하면 Si 채널 에칭이 시작되어 선택비 급감."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-etch", name: "4. 식각 공정 (Etching)" }],
      part_of: [{ id: "gaa-transistor-cell", name: "3nm GAA MBCFET 로직 표준 셀" }],
      next_step: [{ id: "ald-gate-dielectric", name: "HKMG 게이트 절연막 ALD 증착" }]
    },
    evidences: {
      "E-TIER2-GAA": {
        id: "E-TIER2-GAA",
        sourceName: "Ultra-High Selective Dry Etching of SiGe Superlattices (IEEE TED 2021)",
        pubDate: "2021.08",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Gas-phase downstream chemical dry etching achieves SiGe:Si selectivity > 150:1 with Si sheet thickness loss < 0.2 nm and RMS roughness < 0.15 nm for nanosheet architectures.",
        externalUrl: "https://doi.org/10.1109/TED.2021.3099120",
        urlLabel: "IEEE TED GAA SiGe 선택식각 논문 DOI 바로가기"
      }
    }
  }
};

// Node.js 환경에서 모듈 내보내기 지원
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { sprint1Concepts };
}
