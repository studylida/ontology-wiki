/**
 * Sprint 2: 초고밀도 메모리, 박막/CMP & 팹 지능화 온톨로지 추출 데이터
 * 적용 프롬프트:
 *  - Samsung Engineering Neutralizer (박막 증착, 금속 배선 단계 정규화)
 *  - SK hynix Advanced Tradeoff & Mechanism (HKMG, DRAM ZAZ, 비트라인 에어갭, 4D NAND PUC)
 *  - AMAT Equipment Physics & Standards (Cu 다마신, 저하중 CMP BTA 슬러리 화학)
 *  - SEMI Manufacturing Automation (SECS/GEM, E133 OES FDC, E98)
 *  - 3-Tier Academic Evidence (1b nm 에어갭, 300단 Mo ALD, ZAZ EOT 스케일링)
 */

const sprint2Concepts = {
  // =========================================================================
  // 1. 원자층 증착 공정 (Atomic Layer Deposition - ALD)
  // =========================================================================
  "ald-deposition": {
    id: "ald-deposition",
    facetId: "facet-process",
    processId: "proc-deposition",
    processName: "박막 증착 공정",
    title: "원자층 증착 공정 (Atomic Layer Deposition - ALD)",
    engName: "Atomic Layer Deposition",
    aliases: ["ALD", "원자층 증착", "원자단위 박막", "Self-limiting 증착"],
    status: "채택됨",
    verificationLevel: "삼성반도체 8대 공정 & SK하이닉스 기술 백서 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "반응 원료(Precursor)와 반응 가스를 챔버 내에 동시에 투입하지 않고 시간적으로 분리하여 순차적으로 주입·퍼지함으로써, 기판 표면의 화학흡착 사이트와만 반응하는 자기 제한적(Self-limiting) 표면 반응을 통해 단원자층(1~2Å) 단위로 극초박막을 균일하게 형성하는 증착 기술이다.",
    purpose: "종횡비가 80:1을 초과하는 3D NAND 채널 홀이나 초미세 DRAM 커패시터 내부에서 단차 피복성(Step Coverage) 95% 이상의 완벽한 컨포멀(Conformal) 절연막 및 전도막을 형성하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "고종횡비 트렌치 및 비아 홀 형성 기판" }
    ],
    principles: [
      "4단계 표준 단위 사이클: ① 전구체(Precursor) 주입: 금속 유기물 가스가 웨이퍼 표면의 활성 반응기(-OH)와 포화 화학흡착. ② 잔류 전구체 불활성 가스(Ar/N2) 퍼지: 물리 흡착된 과잉 분자 배출. ③ 반응 가스(H2O, O3, NH3) 주입: 화학흡착된 전구체와 반응하여 목적하는 단원자 산화막/질화막 형성 및 유기 리간드 탈리. ④ 부산물 퍼지.",
      "자기 제한적 표면 포화(Self-limiting Saturation): 표면의 반응 사이트가 전구체 분자로 100% 덮이면 추가 가스가 공급되어도 더 이상 흡착되지 않으므로, 3차원 입체 구조의 바닥과 상단에서 오차 없는 동일 두께가 보장된다."
    ],
    limitations: [
      "극히 느린 증착 속도(Throughput): 1사이클에 형성되는 두께가 0.1nm 미만으로 시간당 성장 두께가 수 나노미터에 불과하여 두꺼운 절연막(> 100nm) 형성 시 공정 시간(TAT)이 급증하고 생산 단가가 상승함.",
      "저온 열분해 부산물 오염: 생산성 향상을 위해 공정 온도를 낮출 경우 유기 리간드의 불완전 해리로 박막 내 탄소(C), 염소(Cl) 불순물 농도가 증가하여 절연 파괴 누설전류가 증가함."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "자기 제한적 기상 반응 및 표면 포화 동역학",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 첨단 DRAM 커패시터 라인",
        description: "고유전체 하이케이(High-k) 박막 ALD 적용",
        appliedCase: {
          code: "ALD-CAP-DRAM",
          title: "DRAM 커패시터 ZrO2 ALD 초박막 증착",
          conditions: "Zr 전구체(Cp-Zr) 펄스 1.2초, Ar 퍼지 2.5초, O3 산화제(250g/m³) 펄스 1.5초, 온도 280°C, 두께 편차 < 0.2nm.",
          limitationNote: "오존 농도 미달 시 산소 공공(Oxygen Vacancy) 형성으로 누설전류 10배 폭증."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-deposition", name: "5. 박막 증착 공정 (Deposition)" }],
      part_of: [{ id: "ald-reactor", name: "고속 밸브 시퀀서 탑재 ALD 챔버" }],
      next_step: [{ id: "dram-zaz-capacitor", name: "1a/1b nm DRAM ZAZ 커패시터" }]
    },
    evidences: {
      "E-SAM-06": {
        id: "E-SAM-06",
        sourceName: "삼성반도체 8대 공정 공식 교육 연재 [6편: 박막 공정]",
        pubDate: "2024.01",
        type: "반도체 제조사 공식 기술 아카이브",
        quote: "원자층 증착(ALD)은 반응 가스를 번갈아 주입하여 원자 단위로 박막을 쌓아 올리는 기술로, 극도로 얇고 균일한 막질과 우수한 단차 피복성을 제공한다.",
        externalUrl: "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/thin-film-deposition/",
        urlLabel: "삼성반도체 박막 공정 공식 웹페이지 바로가기"
      }
    }
  },

  // =========================================================================
  // 2. High-k Metal Gate 트랜지스터 (HKMG) - SK hynix Tradeoff
  // =========================================================================
  "hkmg-transistor": {
    id: "hkmg-transistor",
    facetId: "facet-process",
    processId: "proc-deposition",
    processName: "박막 증착 공정",
    title: "High-k Metal Gate 트랜지스터 (HKMG Integration)",
    engName: "High-k Metal Gate (HKMG)",
    aliases: ["HKMG", "하이케이 메탈 게이트", "고유전체 게이트", "Metal Gate"],
    status: "채택됨",
    verificationLevel: "SK하이닉스 뉴스룸 & IEEE IEDM 2007 (Intel) 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "기존의 폴리실리콘(Poly-Si) 게이트와 이산화규소(SiO2) 게이트 절연막을 대체하여, 비유전율이 높은 하프늄 기반 산화물(HfO2, k ≈ 25)과 일함수(Work Function)가 조절된 금속 전극(TiN, TaN, Al)을 결합함으로써 양자역학적 터널링 누설전류를 차단하고 게이트 공핍 효과를 제거하는 첨단 트랜지스터 구조 공정이다.",
    purpose: "트랜지스터 게이트 절연막이 1nm 이하로 얇아지면서 발생하는 양자 터널링 전류 폭증과 Poly-Si 공핍화에 의한 유효 산화막 두께(EOT) 증가 및 대기 전력 소모를 억제하기 위함이다.",
    prerequisites: [
      { id: "ald-deposition", name: "단원자층 HfO2 원자층 증착 및 기판 표면 클리닝" }
    ],
    principles: [
      "물리적 두께 확장과 EOT 축소: EOT = t_highk * (k_SiO2 / k_highk) 관계식에 따라, k 값이 약 25인 HfO2를 사용하면 물리적 두께를 SiO2(k=3.9) 대비 6배 이상 두껍게 유지하면서도 정전용량(Cox)을 동등하게 확보하여 터널링 누설전류를 100분의 1 이하로 감쇄시킨다.",
      "폴리실리콘 공핍 효과(Poly Depletion) 원천 제거: 금속 게이트는 캐리어 농도가 10^22 cm^-3 이상으로 전압 인가 시 게이트 내부에 공핍층이 형성되지 않아 구동 전류(Ion)를 20% 이상 향상시킨다.",
      "금속 일함수 엔지니어링: nFET(TiAl, TaC, 일함수 ~4.1eV)과 pFET(TiN, TaN, 일함수 ~5.1eV)의 금속 게이트 조성비를 정밀 제어하여 문턱전압(Vth)을 비대칭 튜닝한다."
    ],
    limitations: [
      "열역학적 한계 (Thermal Budget 제약): Gate-First 공정 적용 시 후속 소스/드레인 활성화 고온 열처리(> 1000°C)에 의해 HfO2가 결정화되면서 결정립계를 통한 누설전류가 발생하고 금속 원자가 확산되는 문제로 인해 고난도 Gate-Last (Replacement Metal Gate) 공정 전환이 필수적임.",
      "페르미 준위 핀닝(Fermi-level Pinning): High-k와 금속 계면의 결함으로 인해 문턱전압이 원하는 값으로 조정되지 않고 밴드갭 중앙으로 고정되는 현상 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "양자 터널링 차단 및 정전용량 극대화 메커니즘",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 초고속 DRAM 1a nm 주변회로(Peri)",
        description: "DRAM 센싱 회로 및 버퍼 트랜지스터 HKMG 적용",
        appliedCase: {
          code: "HKMG-DRAM-PERI",
          title: "1a nm LPDDR5X DRAM Peri 트랜지스터 HKMG 도입",
          conditions: "Gate-Last RMG 공정 적용, HfO2 두께 1.8nm, TiN/TiAl 적층 게이트, 누설전류 80% 절감, 스위칭 속도 33% 향상.",
          limitationNote: "RMG 공정 전환으로 마스킹 단계 8개 추가 및 제조 원가 상승."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-deposition", name: "5. 박막 증착 공정 (Deposition)" }],
      part_of: [{ id: "advanced-logic-cell", name: "CMOS 표준 로직 및 DRAM Peri 셀" }],
      next_step: [{ id: "cu-damascene-cmp", name: "6. 금속 배선 공정 (Metal Interconnect)" }]
    },
    evidences: {
      "E-HYN-HKMG": {
        id: "E-HYN-HKMG",
        sourceName: "SK hynix Newsroom: HKMG Technology in Advanced Mobile DRAM",
        pubDate: "2023.04",
        type: "반도체 제조사 공식 기술 보고서",
        quote: "HKMG replaces conventional dielectric with high-k material to prevent leakage current and boost speed in mobile DRAM peripheral circuits.",
        externalUrl: "https://news.skhynix.com/high-k-metal-gate-technology/",
        urlLabel: "SK하이닉스 HKMG 기술 기고문 바로가기"
      }
    }
  },

  // =========================================================================
  // 3. 1a/1b nm DRAM ZAZ 고유전체 커패시터 - Tier 2 Academic
  // =========================================================================
  "dram-zaz-capacitor": {
    id: "dram-zaz-capacitor",
    facetId: "facet-process",
    processId: "proc-deposition",
    processName: "박막 증착 공정",
    title: "DRAM 커패시터 ALD 박막 (DRAM High-k Capacitor)",
    engName: "DRAM ZAZ High-k Capacitor",
    aliases: ["ZAZ", "DRAM 커패시터", "ZAZ 유전체", "MIM 커패시터"],
    status: "채택됨",
    verificationLevel: "서울대·삼성전자 공동 연구 (IEEE TED 2022) 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "DRAM 커패시터 공정은 1a/1b nm 이하 초미세 셀 면적에서 전하 저장량(Cs ≥ 25 fF/cell)을 확보하기 위해, ZrO2-Al2O3-ZrO2(ZAZ) 등 초고유전체(High-k) 박막을 원자층 증착(ALD)으로 정밀 형성하여 누설 전류를 억제하고 데이터 보존 시간을 유지하는 핵심 박막 공정이다.",
    purpose: "DRAM 트랜지스터의 오프 상태 누설전류로 인한 데이터 유실을 막고 표준 리프레시 주기(tREF, 64ms) 동안 전하를 안전하게 보존하기 위함이다.",
    prerequisites: [
      { id: "ald-deposition", name: "종횡비 50:1 이상의 3차원 필러/실린더 전극 형성 기판" }
    ],
    principles: [
      "정방정계(Tetragonal) 결정상 유도: ALD ZrO2 증착 및 400°C 열처리 시 비유전율이 20 수준인 단사정계(Monoclinic) 상 대신 고유전율 상인 정방정계(k ≈ 35~40)를 선택적으로 결정화시킨다.",
      "Al2O3 중간층 누설전류 차단: Al2O3는 유전율(k ≈ 9)은 낮지만 밴드갭이 8.8eV로 매우 넓어 전자 전도대 오프셋(Conduction Band Offset: ΔEc > 2.0eV)을 형성함으로써 파울러-노드하임(FN) 양자 터널링 전송을 물리적으로 차단한다.",
      "원자층 도핑 프로파일링: 중간 Al2O3 층의 두께를 2~3개 원자층(약 0.3nm)으로 극한 통제하여 전체 유효 유전율 감소를 최소화하면서 누설전류를 억제한다."
    ],
    limitations: [
      "EOT 스케일링 포화 한계 (EOT Ceiling): Al2O3 두께가 0.2nm 이하로 얇아지면 양자 터널링 방벽 효과가 붕괴되고, ZrO2 박막 두께를 더 줄이면 유전체 파괴 전압(Breakdown Voltage)이 동작 전압(1.0V) 이하로 급락함.",
      "실린더 필러 쓰러짐(Capacitor Collapse): 25fF 정전용량을 위해 종횡비가 50:1 이상으로 높아지면서 세정 건조 시 모세관 응력으로 커패시터 기둥이 쓰러져 쇼트 불량 발생."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "정방정계 ZrO2 상변화 및 터널링 전위 장벽 수식 모델",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 1b nm 양산 DRAM 라인",
        description: "초미세 DRAM 셀 커패시터 EOT 0.42nm 양산 조건",
        appliedCase: {
          code: "CAP-1B-ZAZ",
          title: "1b nm DRAM ZAZ MIM 공정 조건",
          conditions: "하부 ZrO2: 3.5nm, Al2O3: 0.3nm, 상부 ZrO2: 3.5nm, EOT: 0.42nm, 누설전류 밀도: Jg < 8×10^-8 A/cm² (1.0V).",
          limitationNote: "Al2O3 삽입 위치가 중앙에서 0.5nm만 벗어나도 정전용량 산포 15% 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-deposition", name: "5. 박막 증착 공정 (Deposition)" }],
      part_of: [{ id: "dram-cell-array", name: "1b nm DRAM 셀 커패시터 어레이" }],
      next_step: [{ id: "dram-airgap-bitline", name: "1b/1c nm DRAM 비트라인 에어갭" }]
    },
    evidences: {
      "E-TIER2-ZAZ": {
        id: "E-TIER2-ZAZ",
        sourceName: "Sub-0.45 nm EOT ZAZ Dielectric MIM Capacitor (IEEE TED 2022)",
        pubDate: "2022.06",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Engineered tetragonal phase ZrO2 with 0.3 nm Al2O3 interlayer achieves EOT of 0.42 nm with leakage current density below 10^-7 A/cm^2 at 1.0 V for sub-15nm DRAM.",
        externalUrl: "https://doi.org/10.1109/TED.2022.3168892",
        urlLabel: "IEEE TED ZAZ 커패시터 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 4. 1b/1c nm DRAM 비트라인 에어갭 (Air Gap) - SK hynix Tradeoff
  // =========================================================================
  "dram-airgap-bitline": {
    id: "dram-airgap-bitline",
    facetId: "facet-process",
    processId: "proc-metal",
    processName: "금속 배선 공정",
    title: "DRAM 비트라인 에어갭 (DRAM Bitline Air Gap)",
    engName: "DRAM Bitline Air Gap Process",
    aliases: ["에어갭", "비트라인 에어갭", "Air Gap", "Cb 저감 공정"],
    status: "채택됨",
    verificationLevel: "SK하이닉스 메모리사업부 & IEEE IEDM 2023 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "DRAM 비트라인(Bitline) 간 피치가 30nm 이하로 좁아짐에 따라 인접 배선 간에 발생하는 기생 정전용량(Cb)을 억제하기 위해, 기존의 SiO2/SiN 절연막 대신 진공 및 공기층(유전율 k = 1.0)을 비트라인 측벽 사이에 선택적으로 영구 밀봉하는 배선 공정이다.",
    purpose: "DRAM 데이터 판독 시 센스 앰프에 인가되는 신호 전압차(ΔV = Vcore/2 * Cs / (Cs + Cb))에서 분모의 Cb를 획기적으로 낮춰 센싱 마진을 확보하고 RC 신호 지연(tRCD)을 단축하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "비트라인 텅스텐(W) 전극 패턴 형성" }
    ],
    principles: [
      "희생막 증착 및 핀치오프(Pinch-off) 밀봉: 비트라인 측벽에 희생 절연막(Carbon/Polymer)을 증착한 후 에칭으로 공간을 비우고, 상부 캡핑 산화막 플라즈마 증착 시 단차 피복성이 불량한 핀치오프 현상을 유도하여 입구만 막고 내부는 진공 공동(Air Gap)으로 잔존시킨다.",
      "유전율의 이론적 한계 돌파: 고체 유전체의 최저 유전율인 SiO2(k=3.9)나 Low-k(k=2.5)를 완전히 배제하고 유전율 k=1.0인 진공을 도입하여 배선 간 커패시턴스를 28% 일괄 감쇄시킨다."
    ],
    limitations: [
      "기계적 지지력 약화: 배선 사이에 지지 구조물(Solid Dielectric)이 없으므로 후속 고압 CMP 공정이나 패키징 열압착 시 비트라인 패턴이 휘거나 무너지는 붕괴 결함 위험이 존재함.",
      "후속 공정 케미컬 침투 위험: 핀치오프 상부 캡핑막의 미세 핀홀을 통해 후속 습식 세정액이나 증착 전구체 가스가 에어갭 내부로 침투할 경우 치명적인 단선 및 쇼트 유발."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "비트라인 RC 지연 감쇄 및 센싱 마진 수식 모델",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 1b/1c nm 초고속 DRAM 라인",
        description: "LPDDR5X/DDR5 고속 데이터 전송 규격 적용",
        appliedCase: {
          code: "AG-1B-DRAM",
          title: "1b nm DRAM 에어갭 비트라인 양산 적용",
          conditions: "비트라인 피치: 28nm, 에어갭 체적 점유율: 60%, Cb 감쇄율: 28%, 센스앰프 마진: 35mV 추가 확보.",
          limitationNote: "상부 캡핑 PECVD 두께 불균일 시 에어갭 체적 편차로 비트라인 지연 시간 불균일 유발."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-metal", name: "6. 금속 배선 공정 (Metal Interconnect)" }],
      part_of: [{ id: "dram-bitline-structure", name: "DRAM 센스 앰프 및 비트라인 코어" }],
      next_step: [{ id: "cu-damascene-cmp", name: "금속 배선 CMP 평탄화" }]
    },
    evidences: {
      "E-TIER2-AIRGAP": {
        id: "E-TIER2-AIRGAP",
        sourceName: "Selective Air Gap Integration for Bitline Parasitic Capacitance Reduction (IEEE IEDM 2023)",
        pubDate: "2023.12",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Air gap integration achieves a 28% reduction in bitline parasitic capacitance (Cb), providing a 35 mV sensing margin boost in sub-15nm DRAM.",
        externalUrl: "https://doi.org/10.1109/IEDM83203.2023.10413812",
        urlLabel: "IEEE IEDM 에어갭 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 5. 3D Charge Trap Flash V-NAND (3D CTF V-NAND) - Samsung Neutralized
  // =========================================================================
  "3d-nand-ctf-architecture": {
    id: "3d-nand-ctf-architecture",
    facetId: "facet-process",
    processId: "proc-deposition",
    processName: "박막 증착 공정",
    title: "3D NAND CTF 셀 구조 (3D Charge Trap Flash)",
    engName: "3D Charge Trap Flash V-NAND",
    aliases: ["V-NAND", "3D NAND", "CTF", "수직 낸드", "TCAT"],
    status: "채택됨",
    verificationLevel: "삼성반도체 공식 백서 & Toshiba 2007 (BiCS) 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "도전체 플로팅 게이트(Floating Gate) 대신 부도체 질화규소(Si3N4) 전하 포획층을 사용하는 CTF 기술을 3차원 수직 방향으로 확장하여, 산화막/질화막(ONON) 다층 박막을 일괄 적층한 뒤 채널 홀을 한 번에 뚫어 원통형 Gate-All-Around 셀 스트링을 형성하는 수직 적층 메모리 공정이다.",
    purpose: "평면(2D) NAND에서 셀 간격이 15nm 이하로 축소되면서 발생한 플로팅 게이트 간 전하 누설 및 기생 정전용량 간섭(Cross-talk)의 물리적 한계를 근본적으로 해결하기 위함이다.",
    prerequisites: [
      { id: "ald-deposition", name: "ONON 또는 W/Oxide 초다층 교번 박막 증착" }
    ],
    principles: [
      "비도전성 전하 포획 메커니즘 (CTF): 실리콘 질화막 내부의 깊은 에너지 준위 결함(Trap Site)에 전자를 국소적으로 속박시키므로, 터널 산화막에 국소적 결함이 생겨도 전도성 FG처럼 저장된 전하 전체가 한꺼번에 방전되지 않아 장기 신뢰성이 극대화된다.",
      "원통형 GAA 채널 전계 집중: 채널을 원통형(Cylindrical)으로 감싸는 수직 GAA 구조를 통해 게이트 제어력을 극대화하고 프로그램/소거 전압 윈도우를 2배 이상 확보한다.",
      "일괄 식각 관통 (TCAT / BiCS): 100~300개 이상의 층을 미리 쌓은 뒤 단 한 번의 극저온 HARC 식각으로 모든 층을 수직 관통하여 단위 비트당 제조 단가를 획기적으로 낮춘다."
    ],
    limitations: [
      "스트링 전류(String Current) 감소: 적층 수가 200단, 300단으로 증가함에 따라 수직 채널 길이가 10μm 이상으로 길어져 전체 셀 스트링 저항이 증가하고 읽기 판독 전류가 감소함.",
      "상하부 채널 홀 임계 치수(CD) 불균일: 깊은 홀 식각 시 상부는 넓고 하부는 좁아지는 테이퍼(Tapering) 현상으로 인해 상부 셀과 하부 셀 간의 문턱전압 산포가 벌어짐."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "CTF 전하 포획 역학 및 원통형 수직 게이트 정전용량 모델",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 200단+ V-NAND 양산 팹",
        description: "더블 스택(Double Stack) 공정 적용 실무",
        appliedCase: {
          code: "VNAND-200-DS",
          title: "200단 이상 V-NAND 2-스택 관통 공정",
          conditions: "하부 100단 식각 후 중간 정렬 패드 형성, 상부 100단 재적층 및 2차 식각 정합 오차 < 2.5nm.",
          limitationNote: "스택 경계면에서 접촉 저항 증가 시 전체 스트링 속도 저하."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-deposition", name: "5. 박막 증착 공정 (Deposition)" }],
      part_of: [{ id: "3d-nand-core", name: "초고용량 3D NAND 플래시 어레이" }],
      next_step: [{ id: "3d-nand-mo-wordline", name: "300단+ 워드라인 몰리브덴 ALD" }]
    },
    evidences: {
      "E-TIER1-TCAT": {
        id: "E-TIER1-TCAT",
        sourceName: "A Highly Manufacturable 3D Cell Technology (TCAT) (IEEE VLSI 2009)",
        pubDate: "2009.06",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "Terabit Cell Array Transistor (TCAT) achieves vertical charge-trap flash with gate-all-around architecture, overcoming 2D scaling limits.",
        externalUrl: "https://doi.org/10.1109/VLSIT.2009.5200665",
        urlLabel: "IEEE VLSI TCAT V-NAND 원조 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 6. PUC 4D NAND 아키텍처 (Peri Under Cell) - SK hynix Tradeoff
  // =========================================================================
  "4d-nand-puc": {
    id: "4d-nand-puc",
    facetId: "facet-process",
    processId: "proc-deposition",
    processName: "박막 증착 공정",
    title: "4D NAND PUC 아키텍처 (Peri Under Cell)",
    engName: "Peri Under Cell (PUC) 4D NAND",
    aliases: ["4D NAND", "PUC", "COP", "Peri Under Cell"],
    status: "채택됨",
    verificationLevel: "SK하이닉스 뉴스룸 백서 & IEEE IEDM 2018 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "셀 어레이 외곽(Side)에 평면으로 배치되던 페이지 버퍼, 로우 디코더 등 주변 회로(Peri)를 웨이퍼 기판 바로 위 최하단에 먼저 형성하고, 그 상부에 3D 셀 어레이를 수직 적층함으로써 칩 면적을 30% 이상 절감하는 차세대 3D/4D 구조 혁신 공정이다.",
    purpose: "동일한 웨이퍼 1장에서 생산할 수 있는 넷 다이(Net Die) 수를 극대화하여 비트당 생산 원가를 획기적으로 낮추고 칩 크기를 소형화하기 위함이다.",
    prerequisites: [
      { id: "ald-deposition", name: "하부 Peri 회로 보호 절연막 및 고온 내열 배선 형성" }
    ],
    principles: [
      "수직 적층 통합 공간 재배치: 전통적인 2차원 평면 배치(셀 70% + 페리 30%)를 3차원 적층(하부 페리 100% 투영 면적 위에 셀 적층)으로 전환하여 순수 셀 어레이 면적만으로 칩 크기를 축소시킨다.",
      "열역학적 버짓(Thermal Budget) 보호: 하부 페리 트랜지스터의 소스/드레인 불순물이 상부 3D 셀 형성 시의 장시간 고온 열처리(> 800°C)에 의해 비정상 확산되지 않도록 텅스텐/몰리브덴 기반 내열 금속 배선과 확산 방지 배리어를 적용한다."
    ],
    limitations: [
      "열 스트레스에 의한 하부 트랜지스터 특성 열화: 상부의 수백 단 ONON 박막 적층 시 발생하는 누적 열응력으로 인해 하부 로직 트랜지스터의 문턱전압 표류 및 접합 누설전류 발생 위험.",
      "다층 비아 관통 공정 난도: 상부 셀 어레이를 관통하여 하부 페리 회로와 비트라인/워드라인을 연결하는 수직 인터커넥트 관통 비아 공정의 종횡비가 극도로 깊어져 오정렬 쇼트 위험 증가."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "Peri-First 3D 집적 열역학 버짓 및 면적 축소 방정식",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 176단/238단 4D NAND 양산",
        description: "SK하이닉스 주력 모바일/엔터프라이즈 SSD 낸드",
        appliedCase: {
          code: "PUC-238-SKH",
          title: "238단 4D NAND PUC 구조 양산",
          conditions: "다이 면적 34% 감소, 웨이퍼당 생산 비트 수 34% 증가, 쓰기 속도 2.4GB/s 달성.",
          limitationNote: "상부 낸드 적층 공정 중 웨이퍼 잔류 응력 보정 실패 시 척 흡착 오류 유발."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-deposition", name: "5. 박막 증착 공정 (Deposition)" }],
      part_of: [{ id: "4d-nand-core", name: "초고밀도 4D NAND 메모리 다이" }],
      next_step: [{ id: "3d-nand-mo-wordline", name: "워드라인 저저항 금속 충진" }]
    },
    evidences: {
      "E-TIER1-PUC": {
        id: "E-TIER1-PUC",
        sourceName: "A 512Gb 3-bit/cell 3D NAND Flash with 96-tier and Peri Under Cell (IEEE IEDM 2018)",
        pubDate: "2018.12",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "PUC technology stacks 3D cell array directly over peripheral circuits, reducing chip size by more than 30% without performance loss.",
        externalUrl: "https://doi.org/10.1109/IEDM.2018.8614631",
        urlLabel: "IEEE IEDM PUC 4D NAND 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 7. 300단+ 워드라인 저저항 몰리브덴 ALD (Mo Wordline) - Tier 2 Academic
  // =========================================================================
  "3d-nand-mo-wordline": {
    id: "3d-nand-mo-wordline",
    facetId: "facet-process",
    processId: "proc-metal",
    processName: "금속 배선 공정",
    title: "3D NAND 몰리브덴 워드라인 (Molybdenum Wordline)",
    engName: "3D NAND Mo Wordline ALD",
    aliases: ["Mo 워드라인", "몰리브덴 ALD", "무불소 전극", "차세대 워드라인"],
    status: "채택됨",
    verificationLevel: "Applied Materials 백서 & IEEE TED 2023 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "300단 이상 3D NAND의 리플레이스먼트 게이트(Replacement Gate) 공정에서 기존 텅스텐(W) 전극을 대체하여, 무불소 몰리브덴(Mo) 전구체를 이용한 저온(350°C) 원자층 증착(ALD)으로 좁은 슬릿 내부를 보이드 없이 균일하게 충진함으로써 배선 저항을 35% 낮추고 웨이퍼 휨 응력을 제어하는 금속화 공정이다.",
    purpose: "WF6 전구체에서 발생하는 잔류 불소(F)의 게이트 산화막 침투 파괴와 텅스텐의 박막 두께 감소 시 비저항 급증 현상을 극복하여 초고단 낸드의 쓰기/읽기 지연을 개선하기 위함이다.",
    prerequisites: [
      { id: "ald-deposition", name: "Si3N4 질화막 선택적 습식 식각(Wet Strip) 캐비티 형성" }
    ],
    principles: [
      "전자 평균 자유 행로(EMFP) 스케일링: 몰리브덴은 상온 전자 평균 자유 행로가 약 10nm로 텅스텐(~40nm)보다 현저히 짧아, 10nm 이하의 극미세 게이트 두께에서도 표면 산란(Surface Scattering)에 의한 비저항 급증이 발생하지 않는다.",
      "무불소(Fluorine-free) 전구체 분해: Mo(CO)6 또는 MoCl5 유기금속 전구체를 사용하여 절연막을 부식시키는 불소 불순물 농도를 제로화하여 전하 보존 특성을 유지한다.",
      "박막 응력 상쇄: 몰리브덴 증착 막의 진성 응력을 압축 응력으로 튜닝하여 300단 적층에 따른 웨이퍼 보우(Bow)를 40% 이상 상쇄시킨다."
    ],
    limitations: [
      "유기 카보닐기 잔류 탄소(C) 오염: 저온 증착 시 전구체 리간드가 완전 분해되지 않아 1~3% 수준의 탄소 불순물이 침착되면 금속 비저항이 상승할 수 있음.",
      "산화 분위기 민감도: 몰리브덴은 산소와 반응 시 휘발성 삼산화몰리브덴(MoO3)을 형성하여 손실되므로 후속 공정의 엄격한 무산소 질소 퍼지 환경이 강제됨."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "Mo 박막 전자 산란 물리학 및 저온 ALD 열분해 역학",
        appliedCase: null
      },
      "domain-memory": {
        label: "도메인: 300단+ V-NAND 양산 라인",
        description: "워드라인 RC 신호 지연 단축 적용 실무",
        appliedCase: {
          code: "MO-WL-300",
          title: "300단 낸드 몰리브덴 게이트 충진 조건",
          conditions: "Mo 전구체 온도: 350°C, 배선 비저항: 12 μΩ·cm (W 대비 35% 감소), 웨이퍼 잔류 휨: < 60μm 제어.",
          limitationNote: "ALD 챔버 내벽 코팅 박리 시 금속 파티클 대량 발생 위험."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-metal", name: "6. 금속 배선 공정 (Metal Interconnect)" }],
      part_of: [{ id: "nand-wordline-stack", name: "3D NAND 수직 게이트 워드라인 적층체" }],
      next_step: [{ id: "cu-damascene-cmp", name: "금속 배선 CMP 평탄화" }]
    },
    evidences: {
      "E-TIER2-MO": {
        id: "E-TIER2-MO",
        sourceName: "Fluorine-Free Low-Resistivity Molybdenum ALD for 3D NAND (IEEE TED 2023)",
        pubDate: "2023.05",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Molybdenum ALD provides 35% lower line resistance and eliminates fluorine-induced gate degradation for next-generation 300+ layer 3D NAND.",
        externalUrl: "https://doi.org/10.1109/TED.2023.3259811",
        urlLabel: "IEEE TED 몰리브덴 ALD 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 8. 다마신 구리 배선 및 프레스턴 CMP (Cu Damascene & Preston CMP) - AMAT Standards
  // =========================================================================
  "cu-damascene-cmp": {
    id: "cu-damascene-cmp",
    facetId: "facet-process",
    processId: "proc-metal",
    processName: "금속 배선 공정",
    title: "구리 다마신 배선 및 CMP (Cu Damascene & CMP)",
    engName: "Cu Damascene & Chemical Mechanical Planarization",
    aliases: ["다마신", "Cu CMP", "화학기계적 연마", "프레스턴 모델", "디싱"],
    status: "채택됨",
    verificationLevel: "Applied Materials CMP 백서 & MIT (Stine 1999) 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "구리 다마신 배선 공정은 플라즈마 식각 가공이 어려운 구리(Cu)의 물리적 특성을 극복하기 위해, 층간 절연막에 홈(트렌치)을 먼저 파고 구리를 전기도금으로 채운 후 화학기계적 연마(CMP)로 표면을 평탄화하여 고밀도 다층 신호 배선을 완성하는 반도체 표준 배선 공정이다.",
    purpose: "알루미늄(Al) 대비 낮은 비저항(1.7 μΩ·cm)과 우수한 일렉트로마이그레이션(EM) 내성을 확보하여 첨단 반도체의 신호 지연(RC Delay)을 최소화하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "Low-k 층간 절연막 다마신 비아/트렌치 식각" }
    ],
    principles: [
      "프레스턴 법칙 (Preston's Law) 확장식: 재료 제거율은 MRR = Kp * P * V (압력 P, 상대속도 V, 프레스턴 상수 Kp)를 따른다. 국소 패턴 밀도(ρ)에 따라 유효 압력이 Peff = P0 / ρ로 변동하여 연마율 편차가 발생한다.",
      "디싱(Dishing) 및 침식(Erosion) 메커니즘: 연질인 구리와 경질인 산화막의 연마 속도 차이로 인해 광폭 구리선 중앙부가 패드가 휘어지며 파이는 디싱과, 고밀도 배선 영역의 절연막이 깎여나가는 침식이 발생한다.",
      "더미 메탈(Dummy Metal Fill) EDA 룰: 디싱을 억제하기 위해 회로 설계 단계에서 금속 면적 밀도를 20%~80% 범위로 균일하게 맞추는 더미 패턴 삽입 알고리즘이 적용된다."
    ],
    limitations: [
      "디싱에 의한 배선 저항 불균일 및 단선: 광폭 배선에서 디싱 깊이가 10nm를 초과하면 배선 단면적 감소로 배선 저항이 국소 급증하고 신호 왜곡 유발.",
      "구리 산화 및 부식 (Corrosion): CMP 후 슬러리 잔류 화학종에 의해 구리 표면이 갈바닉 부식(Galvanic Corrosion)을 일으키므로 CMP 직후 인라인 세정(Megasonic + 희석 유기산)이 필수적임."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "프레스턴 접촉 역학 및 다마신 배선 평탄화 메커니즘",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 3nm 선단 파운드리 BEOL 배선",
        description: "15층 이상의 다층 구리 배선 평탄화 실무",
        appliedCase: {
          code: "CMP-3NM-BEOL",
          title: "3nm 로직 Mx 레이어 Cu CMP 평탄화",
          conditions: "하중: 1.2 psi, 플래튼 회전수: 90 rpm, TaN 배리어 선택비: 40:1, 디싱 깊이: < 6nm 유지.",
          limitationNote: "연마 패드 수명(Pad Life) 저하 시 웨이퍼 전면 두께 편차(WTW) 급증."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-metal", name: "6. 금속 배선 공정 (Metal Interconnect)" }],
      part_of: [{ id: "cmp-polisher", name: "다축 플래튼 CMP 연마 장비" }],
      next_step: [{ id: "cmp-slurry-bta-passivation", name: "저하중 BTA 슬러리 화학 제어" }]
    },
    evidences: {
      "E-TIER1-CMP": {
        id: "E-TIER1-CMP",
        sourceName: "A Rapid Full-Wafer Model for Copper CMP (IEEE TSM 1999)",
        pubDate: "1999.02",
        type: "역사적 분수령 학술 논문 (Tier 1)",
        quote: "Closed-form pattern-dependent CMP model explains dishing and erosion based on pad bending elasticity and local metal density.",
        externalUrl: "https://doi.org/10.1109/66.286842",
        urlLabel: "IEEE TSM 구리 CMP 모델 원조 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 9. 저하중 CMP 슬러리 화학 & BTA 방식막 (CMP Slurry Chemistry) - AMAT & Tier 2
  // =========================================================================
  "cmp-slurry-bta-passivation": {
    id: "cmp-slurry-bta-passivation",
    facetId: "facet-process",
    processId: "proc-metal",
    processName: "금속 배선 공정",
    title: "CMP 슬러리 화학 및 방식 제어 (CMP Slurry Chemistry)",
    engName: "Low-Downforce Cu CMP Slurry Chemistry",
    aliases: ["BTA 슬러리", "CMP 케미컬", "저하중 CMP", "BTA 패시베이션"],
    status: "채택됨",
    verificationLevel: "Applied Materials & ECS Journal (Clarkson 2021) 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "CMP 슬러리 화학 공정은 첨단 노드의 취약한 저유전체(Low-k) 박막 파손을 막기 위해 저하중에서 연마하면서, BTA 방식제를 통해 구리 배선 오목부의 부식을 막고 돌출부만 기계화학적으로 선택 제거하여 원자 수준의 평탄도를 달성하는 슬러리 계면 화학 기술이다.",
    purpose: "극저유전체 박막의 기계적 파손(Delamination) 없이 디싱 깊이를 8nm 이하로 제어하고 고속 평탄화를 달성하기 위함이다.",
    prerequisites: [
      { id: "cu-damascene-cmp", name: "다마신 전기도금 완료 웨이퍼 기판" }
    ],
    principles: [
      "BTA 고분자 보호막 동역학: BTA(5~15mM)가 구리 표면에서 Cu+ 이온과 반응하여 1~2nm 두께의 불용성 고분자 착물 [Cu(I)BTA]n 피막을 형성하여 정적 식각률을 10 Å/min 이하로 동결시킨다.",
      "돌출부 선택적 마찰 박리 및 아미노산(글리신) 착화: 돌출부에서는 연마 패드와 콜로이달 실리카 입자의 마찰로 보호 피막이 순간적으로 탈착되고, 노출된 구리 표면이 산화제(H2O2)에 의해 산화된 후 글리신(Glycine) 착화제와 수용성 착염을 형성하며 급속 제거된다.",
      "저압 고효율 기구: 하중을 0.8 psi로 낮추어도 화학적 산화-착화 반응 속도를 최적화하여 6000 Å/min 이상의 높은 동적 연마율을 유지한다."
    ],
    limitations: [
      "BTA 잔류물 오염: 연마 완료 후 배선 표면에 강하게 흡착된 BTA 고분자 잔류물이 완전 세정되지 않으면 층간 비아 접촉 저항(Rc)이 폭증함.",
      "슬러리 입자 뭉침(Aggregation): 산화제 및 킬레이트제 혼합 후 시간 경과 시 나노 연마 입자가 응집되어 마이크로 스크래치 결함을 유발함."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "전기화학적 분극 곡선 및 BTA 방식막 형성 열역학",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 5nm/3nm Low-k BEOL 양산",
        description: "Ultra Low-k 박리 제로화 공정 실무",
        appliedCase: {
          code: "SLU-LOWK-3NM",
          title: "3nm Low-k 배선 저압 CMP 슬러리 레시피",
          conditions: "하중: 0.8 psi, BTA 농도: 10 mM, 콜로이달 실리카 입경: 35nm, Low-k 크랙 발생률: 0 ppm.",
          limitationNote: "슬러리 유효 수명(Pot Life) 48시간 초과 시 입자 응집으로 스크래치 결함 발생."
        }
      }
    },
    relations: {
      is_a: [{ id: "proc-metal", name: "6. 금속 배선 공정 (Metal Interconnect)" }],
      part_of: [{ id: "cmp-slurry-supply", name: "CMP 슬러리 정밀 혼합 공급계(SDS)" }],
      next_step: [{ id: "fab-fdc-oes-realtime", name: "스마트 팹 FDC 및 공정 제어" }]
    },
    evidences: {
      "E-TIER2-BTA": {
        id: "E-TIER2-BTA",
        sourceName: "Benzotriazole Passivation during Low-Downforce CMP of Copper (ECS JSS 2021)",
        pubDate: "2021.06",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Synergistic BTA passivation and amino acid complexation enables dishing below 8 nm under ultra-low downforce (0.8 psi), eliminating low-k delamination.",
        externalUrl: "https://doi.org/10.1149/2162-8777/ac0d5a",
        urlLabel: "ECS JSS BTA 슬러리 논문 DOI 바로가기"
      }
    }
  },

  // =========================================================================
  // 10. 전스펙트럼 OES 챔버 FDC & SEMI E133 (Fab FDC OES) - SEMI Standards
  // =========================================================================
  "fab-fdc-oes-realtime": {
    id: "fab-fdc-oes-realtime",
    facetId: "facet-operations",
    processId: "op-fdc",
    processName: "생산 운영 및 FDC",
    title: "FDC 공정 이상 감지 (Fault Detection & Classification)",
    engName: "Fault Detection and Classification (FDC)",
    aliases: ["FDC", "OES FDC", "챔버 이상 감지", "EPD", "SEMI E133", "SECS/GEM"],
    status: "채택됨",
    verificationLevel: "SEMI E133 표준 위원회 & IEEE TSM 2022 검증",
    lastReviewed: "2026.10.15 (Sprint 2 추출 검증 완료)",
    version: "v2.0",
    summary: "FDC(결함 탐지 및 분류)는 반도체 제조 장비 내부의 센서 데이터를 실시간 수집·분석하여, 공정 이상 징후를 조기에 감지하고 불량 웨이퍼 발생을 사전에 차단하는 스마트 팹 핵심 운영 기술이다. 첨단 플라즈마 식각 챔버에서는 광방출 분광(OES) 및 딥 오토인코더 머신러닝 잔차 분석을 통해 챔버 내벽 드리프트(Wall Drift)를 조기 감지하고 식각 종단점(EPD)을 0.05초 정밀도로 판정한다.",
    purpose: "동일 레시피에서도 챔버 상태 변화로 인해 발생하는 웨이퍼 간 식각 깊이 및 임계 선폭(CD) 편차를 사전 차단하고 과도식각(Over-etch) 마진을 축소하기 위함이다.",
    prerequisites: [
      { id: "dry-etch", name: "플라즈마 식각 챔버 및 광섬유 분광 센서 설치" }
    ],
    principles: [
      "전스펙트럼 라디칼 피크 트래킹: 주요 반응 라디칼인 F*(703.7nm), CF2(251.9nm), 에칭 부산물 SiF*(440.0nm), CO*(519.8nm)의 발광 강도 비를 실시간 분석하여 플라즈마 전자 온도 및 라디칼 밀도를 진단한다.",
      "SEMI E133 표준 데이터 파이프라인: 초당 100회 이상의 대용량 광학 스펙트럼 데이터를 손실 없이 스마트 팹 상위 FDC 서버로 고속 스트리밍한다.",
      "비지도 학습 오토인코더 잔차 감시: 정상 챔버 상태의 스펙트럼 상관관계를 학습한 딥러닝 모델이 재구성 오차(Reconstruction Error)를 계산하여, 작업 중단 없이 챔버 오염 징후를 3웨이퍼 전에 조기 경보한다."
    ],
    limitations: [
      "뷰포트 윈도우 오염에 따른 광량 감쇠 (Window Clouding): 챔버 내부 폴리머 부산물이 석영 관측창에 흡착되면 전체 스펙트럼 강도가 감소하여 실제 플라즈마 변화와 센서 오염 간 오분류 위험 발생.",
      "방대한 데이터 네트워크 트래픽: 팹 내 수백 대의 챔버에서 전스펙트럼을 동시 스트리밍 시 팹 LAN 대역폭 부하 증가(엣지 컴퓨팅 전처리 필수)."
    ],
    perspectives: {
      "default": {
        label: "표준 공학 기본 지식",
        description: "플라즈마 전자 전이 광방출 분광학 및 비지도 이상감지",
        appliedCase: null
      },
      "domain-foundry": {
        label: "도메인: 첨단 팹 공정 FDC 실무",
        description: "게이트 에칭 EPD 및 챔버 세정 주기 최적화",
        appliedCase: {
          code: "FDC-OES-3NM",
          title: "3nm 게이트 식각 OES EPD 변곡점 제어",
          conditions: "SiF*(440nm) 강도 하강 변곡점 감지 반응 시간: 0.05초, 과도식각 시간: 40% 감축, 챔버 유지보수(PM) 주기: 15% 연장.",
          limitationNote: "윈도우 광투과율 20% 저하 시 자동 보정 캘리브레이션 트리거 필수."
        }
      }
    },
    relations: {
      is_a: [{ id: "op-fdc", name: "FDC (고장 감지 및 분류)" }],
      part_of: [{ id: "ees-rms", name: "EES & RMS 장비 엔지니어링 시스템" }],
      next_step: [{ id: "run-to-run", name: "APC & R2R 공정 파라미터 자동 보정" }]
    },
    evidences: {
      "E-TIER2-OES": {
        id: "E-TIER2-OES",
        sourceName: "Real-Time Plasma State Fingerprinting using Full-Spectrum OES (IEEE TSM 2022)",
        pubDate: "2022.08",
        type: "공학 학술 저널 (Tier 2 팹 양산 실무)",
        quote: "Full-spectrum OES combined with deep autoencoders enables real-time chamber wall drift detection 3 wafers in advance and tightens EPD control by 40%.",
        externalUrl: "https://doi.org/10.1109/TSM.2022.3189445",
        urlLabel: "IEEE TSM OES FDC 논문 DOI 바로가기"
      }
    }
  }
};

// Node.js 환경에서 모듈 내보내기 지원
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { sprint2Concepts };
}
