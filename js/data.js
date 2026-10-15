/**
 * 반도체 산업 지식 위키 - 공용 데이터 및 상태 저장소 (Demo Data)
 * 공식 출처 기반 전수 반영: Samsung Semiconductor, SK hynix, ASML, Lam Research, Applied Materials, SEMI, IEEE/MDPI
 */

const WikiStore = {
  // ── 1. 반도체 다차원 도메인 패싯 (8대 공정 종속 탈피 & 4대 온톨로지 축) ──
  domainFacets: [
    { id: "facet-device", name: "소자·제품군 (Devices)", active: false },
    { id: "facet-process", name: "제조 단위 공정 (Unit Process)", active: true },
    { id: "facet-operations", name: "팹 지능화 & 운영 (Operations)", active: false },
    { id: "facet-materials", name: "소재·화학 & 팹 인프라 (Materials & Infra)", active: false }
  ],

  // 1-A. 소자 & 제품군 트리 (HBM, 3D NAND, 2nm GAA, DRAM)
  deviceTree: [
    {
      id: "dev-hbm",
      name: "1. AI 메모리: HBM 3D 적층 (HBM3E / HBM4)",
      summary: "DRAM 다이를 수직 적층하여 테라바이트급 대역폭을 구현하는 초고성능 메모리",
      concepts: ["mr-muf", "hybrid-bonding", "hbm-kgd-testing", "cowos-interposer-cuf"]
    },
    {
      id: "dev-nand",
      name: "2. 초고적층 메모리: 3D V-NAND & 4D Flash",
      summary: "300단 이상 수직 채널 홀과 전하 트랩으로 테라비트 용량을 구현하는 플래시 메모리",
      concepts: ["3d-nand-ctf-architecture", "4d-nand-puc", "3d-nand-mo-wordline", "cryogenic-etch", "bbp-defect-inspection"]
    },
    {
      id: "dev-logic",
      name: "3. 선단 로직: 3nm / 2nm GAA 나노시트",
      summary: "게이트가 채널 4면을 완전히 감싸 누설전류를 차단하는 차세대 초미세 트랜지스터",
      concepts: ["gaa-nanosheet-etch", "hkmg-transistor", "high-na-euv", "euv-lithography", "model-based-opc", "tddb-reliability-physics"]
    },
    {
      id: "dev-dram",
      name: "4. 초고밀도 메모리: 10nm급 DRAM",
      summary: "ZAZ 고유전체 커패시터와 비트라인 에어갭으로 리프레시와 기생용량을 극복한 D램",
      concepts: ["dram-zaz-capacitor", "dram-airgap-bitline", "ald-deposition", "cu-damascene-cmp"]
    }
  ],

  // 1-B. 제조 단위 공정 트리
  processes: [
    {
      id: "proc-wafer",
      name: "1. 웨이퍼 제조",
      engName: "Wafer Fabrication",
      summary: "규소(모래)에서 고순도 잉곳을 성장시키고 원판으로 가공",
      concepts: ["wafer-fabrication", "silicon-ingot"]
    },
    {
      id: "proc-oxidation",
      name: "2. 산화 공정",
      engName: "Oxidation",
      summary: "열산화 반응으로 고품질 절연막(SiO2) 형성",
      concepts: ["thermal-oxidation"]
    },
    {
      id: "proc-photo",
      name: "3. 포토 공정",
      engName: "Photolithography",
      summary: "빛과 마스크를 이용해 미세 회로 패턴을 전사",
      concepts: ["photolithography", "euv-lithography", "high-na-euv", "model-based-opc", "photo-resist"]
    },
    {
      id: "proc-etch",
      name: "4. 식각 공정",
      engName: "Etching",
      summary: "반응성 가스와 이온으로 불필요한 박막을 정밀 제거",
      active: true,
      concepts: ["dry-etch", "cryogenic-etch", "ale-etch", "gaa-nanosheet-etch", "plasma-discharge"]
    },
    {
      id: "proc-deposition",
      name: "5. 박막 증착 공정",
      engName: "Deposition & Ion Implant",
      summary: "원자/분자 단위의 절연막·전도막을 웨이퍼에 형성",
      concepts: ["ald-deposition", "hkmg-transistor", "dram-zaz-capacitor", "3d-nand-ctf-architecture", "4d-nand-puc"]
    },
    {
      id: "proc-metal",
      name: "6. 금속 배선 공정",
      engName: "Metal Interconnect",
      summary: "트랜지스터 간 전기 신호 연결을 위한 배선 형성",
      concepts: ["cu-damascene-cmp", "cmp-slurry-bta-passivation", "dram-airgap-bitline", "3d-nand-mo-wordline"]
    },
    {
      id: "proc-eds",
      name: "7. EDS & 검사 공정",
      engName: "Electrical Die Sorting & Metrology",
      summary: "웨이퍼 상태에서 프로브 카드로 칩의 전기적 동작 및 결함 광학 검사",
      concepts: ["hbm-kgd-testing", "bbp-defect-inspection"]
    },
    {
      id: "proc-packaging",
      name: "8. 첨단 패키징 공정",
      engName: "Advanced Packaging",
      summary: "칩을 보호하고 외부 단자와 연결하는 차세대 2.5D/3D 적층",
      concepts: ["mr-muf", "hybrid-bonding", "cowos-interposer-cuf", "fan-out-wafer-level-packaging"]
    }
  ],

  // 1-C. 생산 운영 & EES·FDC 트리
  operationsTree: [
    {
      id: "op-fdc",
      name: "FDC (고장 감지 및 분류 & 센서)",
      summary: "챔버 실시간 센서 데이터를 분석하여 공정 이상치와 결함 조기 탐지",
      concepts: ["fab-fdc-oes-realtime", "plasma-fdc-sensor", "spc-control-chart"]
    },
    {
      id: "op-apc",
      name: "APC & R2R (첨단 공정 제어)",
      summary: "이전 런 계측값을 바탕으로 다음 런 파라미터(시간/출력) 자동 보정",
      concepts: ["run-to-run"]
    },
    {
      id: "op-yield",
      name: "수율 통계 모델링 & 신뢰성 물리",
      summary: "결함 뭉침 보정 수율 예측(Negative Binomial) 및 10년 수명 보증(TDDB)",
      concepts: ["yield-negative-binomial-modeling", "tddb-reliability-physics"]
    },
    {
      id: "op-ees",
      name: "EES & RMS (장비 엔지니어링 시스템)",
      summary: "Fab 전 장비의 통신(SECS/GEM), 레시피 무결성 및 인터락 중앙 통제",
      concepts: ["ees-rms"]
    }
  ],

  // 1-D. 소재·화학 & 팹 인프라 트리
  materialsTree: [
    {
      id: "mat-infra",
      name: "팹 유틸리티 & 환경 인프라",
      summary: "초순수 연속 공급망 및 서브팹 온실가스 친환경 분해 설비",
      concepts: ["ultra-pure-water-upw", "fab-subfab-pfc-scrubber"]
    },
    {
      id: "mat-chemical",
      name: "첨단 슬러리 & 표면 화학",
      summary: "Low-k 보호를 위한 초저하중 CMP 슬러리 및 BTA 부식 방지제",
      concepts: ["cmp-slurry-bta-passivation", "photo-resist"]
    },
    {
      id: "mat-precursor",
      name: "차세대 메탈 & ALD 전구체",
      summary: "무불소 몰리브덴(Mo) 배선 및 초고유전체 ZAZ 박막 원자층 전구체",
      concepts: ["3d-nand-mo-wordline", "dram-zaz-capacitor"]
    }
  ],

  // ── 2. 개념 상세 온톨로지 데이터베이스 ──
  concepts: {
    // ----------------------------------------------------
    // 1. 플라즈마 건식 식각 (Dry Etch)
    // ----------------------------------------------------
    "dry-etch": {
      id: "dry-etch",
      facetId: "facet-process",
      processId: "proc-etch",
      processName: "식각 공정",
      title: "플라즈마 건식 식각 (Plasma Dry Etching)",
      engName: "Reactive Ion Etching (RIE)",
      aliases: ["RIE", "건식 식각", "드라이 에칭", "플라즈마 식각"],
      status: "채택됨",
      verificationLevel: "공식 출처 4건 검증",
      lastReviewed: "2026.10.12 (K팀장 검토 승인)",
      version: "v1.2",
      summary: "플라즈마 상태의 반응성 가스와 이온을 가속시켜 웨이퍼 표면의 불필요한 박막을 선택적으로 제거하는 공정이다.",
      purpose: "미세 선폭(Sub-10nm) 구현 시 습식 식각의 등방성(Isotropic) 언더컷 한계를 극복하고 수직 이방성(Anisotropic) 패턴을 확보하기 위함이다.",
      prerequisites: [
        { id: "plasma-discharge", name: "플라즈마 방전" },
        { id: "photo-resist", name: "포토레지스트 패터닝" }
      ],
      principles: [
        "물리적 충돌(Sputtering)과 화학적 반응(Radical)이 결합된 이온 보조 식각 메커니즘을 사용한다.",
        "RF 바이어스를 인가하여 양이온을 웨이퍼 표면에 수직으로 입사시켜 측면 식각을 억제하고 정밀한 수직 프로파일을 얻는다."
      ],
      limitations: [
        "고종횡비(HARC) 공정에서 종횡비가 20:1 이상으로 깊어질수록 비아 넥킹(Neck-down) 및 식각 정지(Etch Stop) 위험이 존재한다.",
        "하부 산화막에 대한 선택비가 낮을 경우 게이트 절연막 파괴 및 격자 결함(Plasma Damage)을 유발할 수 있다."
      ],
      // 다중 회사·프로젝트 관점
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "산업 표준 및 학술 문헌에서 합의된 일반적 물리 원리와 정의",
          appliedCase: null
        },
        "domain-memory": {
          label: "도메인: 첨단 메모리 제조",
          description: "초고단 3D NAND 및 초미세 DRAM 커패시터 공정에서의 적용 맥락",
          appliedCase: {
            title: "3D NAND 200단 이상 채널 홀 에칭 조건",
            conditions: "극저온(-60°C 이하) 환경에서 식각 가스를 주입하여 측벽 패시베이션을 극대화하는 Cryogenic Etching 기법 적용.",
            limitationNote: "극저온 유지에 따른 칠러 소비 전력 증가 및 챔버 세정 주기 단축이 양산 제약으로 작용함."
          }
        },
        "company-a-hbm": {
          label: "회사·프로젝트: A사 HBM3E P-Line",
          description: "A 고객사 HBM3E 수율 개선 과제(P-Line)에서 실측된 양산 레시피 및 대응 이력",
          appliedCase: {
            code: "ET-HARC-04",
            title: "HBM 8단 적층 TSV 형성 공정 중 바닥 보이드 대응",
            conditions: "Poly-Si 식각 대비 Oxide 선택비 > 30:1 필수 유지. Lam 2300 Kiyo 장비 기준 C4F8 가스 유량을 기존 40sccm에서 46sccm으로 15% 상향 조정.",
            evidenceId: "E-03",
            limitationNote: "주의: 본 조건은 특정 P-Line의 Lam 장비 챔버 전제이며 타사 라인의 전역 공통 규칙이 아님."
          }
        },
        "company-b-dram": {
          label: "회사·프로젝트: B사 1b nm DRAM 캐패시터 라인",
          description: "B사 첨단 DRAM 커패시터 전극 고종횡비 식각 최적화 사례",
          appliedCase: {
            code: "ET-CAP-1B",
            title: "High-k 유전체 보호를 위한 펄스 RF 바이어스 적용",
            conditions: "식각 손상을 방지하기 위해 100Hz 듀티비 펄스 플라즈마 제어를 도입하여 하부 누설전류 40% 차단.",
            evidenceId: "E-02",
            limitationNote: "펄스 식각 적용 시 전체 공정 시간(TAT)이 약 25% 증가함."
          }
        }
      },
      relations: {
        is_a: [{ id: "proc-etch", name: "식각 공정 (Etching)" }],
        part_of: [
          { id: "plasma-chamber", name: "플라즈마 반응 챔버" },
          { id: "rf-generator", name: "RF 바이어스 제너레이터" }
        ],
        next_step: [{ id: "ashing", name: "PR 스트립 및 애싱 (Ashing)" }]
      },
      evidences: {
        "E-01": {
          id: "E-01",
          sourceName: "Lam Research Technical Glossary",
          pubDate: "2024.01",
          type: "장비사 공식 기술 용어집",
          quote: "Plasma etch utilizes reactive gases energized into a plasma state to remove material selectively from wafer surfaces via chemical reactions and ion bombardment.",
          externalUrl: "https://www.lamresearch.com/technical-glossary/",
          urlLabel: "Lam Research 공식 용어집 웹사이트 바로가기"
        },
        "E-02": {
          id: "E-02",
          sourceName: "Applied Materials Process Handbook v3.2",
          pubDate: "2023.09",
          type: "장비사 공정 가이드",
          quote: "Anisotropic profile control in Sub-10nm nodes requires strict RF bias decoupling from ICP plasma source power to balance physical sputter with chemical passivation.",
          externalUrl: "https://www.appliedmaterials.com/us/en/glossary.html",
          urlLabel: "Applied Materials 공식 Glossary 바로가기"
        },
        "E-03": {
          id: "E-03",
          sourceName: "A사 HBM3E 수율 개선 완료 보고서 (v2.1)",
          pubDate: "2025.11.14",
          type: "사내 승인 기술 문서 (P-Line)",
          quote: "TSV HARC 공정에서 종횡비 12:1 초과 시 비아 하부 식각 정지 현상이 관측됨. 이에 폴리머 형성을 제어하기 위해 C4F8 가스 유량을 15% 증량 처방하여 보이드 결함률을 0.02%로 개선함.",
          externalUrl: "https://news.skhynix.com/en/details-defined-a-look-at-etch-technology/",
          urlLabel: "관련 공정 기술 보고서 원문 링크"
        }
      }
    },

    // ----------------------------------------------------
    // 2. 원자층 식각 (ALE)
    // ----------------------------------------------------
    "ale-etch": {
      id: "ale-etch",
      facetId: "facet-process",
      processId: "proc-etch",
      processName: "식각 공정",
      title: "원자층 식각 (Atomic Layer Etching - ALE)",
      engName: "Atomic Layer Etching",
      aliases: ["ALE", "원자단위 식각", "디지털 식각"],
      status: "채택됨",
      verificationLevel: "Lam Research 기술 백서 검증",
      lastReviewed: "2026.10.05",
      version: "v1.1",
      summary: "원자층 증착(ALD)의 역과정으로, 화학적 표면 개질과 물리적 이온 탈착 반응을 분리 순환시켜 원자 한 층(Angstrom) 두께로 표면을 균일하게 깎아내는 차세대 디지털 식각 기술이다.",
      purpose: "3nm 이하 극미세 게이트 공정에서 플라즈마 대미지 없이 원자 수준의 표면 평탄도와 극도의 선택비를 달성하기 위함이다.",
      prerequisites: [{ id: "dry-etch", name: "플라즈마 건식 식각" }],
      principles: [
        "1단계: 반응성 염소(Cl2) 가스를 주입하여 웨이퍼 표면 최상단 원자층에만 선택적으로 화학 흡착(Adsorption)시킨다.",
        "2단계: 퍼지 후 아르곤(Ar+) 저에너지 이온을 충돌시켜 흡착된 표면 층만을 선택적으로 스퍼터링 탈착(Desorption)시킨다."
      ],
      limitations: [
        "사이클당 식각 두께가 0.1~0.5nm에 불과하여 두꺼운 박막 식각 시 총 공정 시간(TAT)이 길어져 스루풋(Throughput)이 매우 낮다."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "Lam / Applied Materials 기술 백서에 따른 ALE 자기제한(Self-limiting) 반응 원리",
          appliedCase: null
        },
        "company-c-foundry": {
          label: "회사·프로젝트: C사 2nm GAA 파운드리 라인",
          description: "C사 2nm 공정 나노시트(Nanosheet) 게이트 형성 시 ALE 적용 사례",
          appliedCase: {
            code: "GAA-ALE-02",
            title: "Si/SiGe 초미세 선택 식각을 통한 나노시트 릴리스",
            conditions: "SiGe 층만을 선택적으로 ALE 처리하여 Si 나노시트의 두께 편차를 0.2nm 이내로 극저제어 성공.",
            evidenceId: "E-01",
            limitationNote: "전구체 퍼지 시간 최적화를 위한 초고진공 배기 밸브 유지보수 주기 단축."
          }
        }
      },
      evidences: {
        "E-01": {
          id: "E-01",
          sourceName: "Lam Research Technical Glossary (ALE)",
          pubDate: "2024.01",
          type: "장비사 공식 기술 용어집",
          quote: "ALE uses sequential self-limiting steps to remove atomic layers of material with Angstrom-level precision.",
          externalUrl: "https://www.lamresearch.com/technical-glossary/",
          urlLabel: "Lam Research ALE 공식 기술 설명 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 3. 포토레지스트 (Photoresist - 양성 vs 음성)
    // ----------------------------------------------------
    "photo-resist": {
      id: "photo-resist",
      facetId: "facet-process",
      processId: "proc-photo",
      processName: "포토 공정",
      title: "포토레지스트 패터닝 (양성 PR vs 음성 PR)",
      engName: "Photoresist (Positive vs Negative)",
      aliases: ["PR", "감광액", "Positive PR", "Negative PR"],
      status: "채택됨",
      verificationLevel: "삼성반도체 8대 공정 공식 교육 검증",
      lastReviewed: "2026.09.20",
      version: "v1.3",
      summary: "빛(자외선/EUV)에 노출되었을 때 화학적 구조가 변하는 유기 감광 고분자 물질로, 후속 식각 공정에서 하부 박막을 보호하는 마스크 역할을 수행한다.",
      purpose: "설계된 CAD 회로 패턴을 웨이퍼 표면에 정밀하게 전사하기 위함이다.",
      prerequisites: [{ id: "proc-oxidation", name: "산화 공정" }],
      principles: [
        "양성(Positive) PR: 빛을 받은 영역의 고분자 결합이 끊어져 현상액(Developer)에 용해되어 제거된다. 해상도가 우수하여 미세 공정에 주로 쓰인다.",
        "음성(Negative) PR: 빛을 받은 영역이 가교 반응(Cross-linking)을 일으켜 현상액에 녹지 않고 남는다. 접착력이 우수하나 팽윤(Swelling) 현상으로 초미세 선폭에 한계가 있다."
      ],
      limitations: [
        "EUV 초미세 노광 시 광자 무작위성(Photon Shot Noise)으로 인한 선폭 거칠기(LER/LWR) 결함 발생 위험.",
        "도포 후 웨이퍼 가장자리의 잔류 PR을 제거하기 위한 EBR(Edge Bead Removal) 솔벤트 정밀 제어 필수."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "삼성 용어집 및 교과서적 양성/음성 PR 광화학 반응 메커니즘",
          appliedCase: null
        },
        "company-a-hbm": {
          label: "회사·프로젝트: A사 초미세 패턴 라인",
          description: "EUV 노광 공정용 화학증폭형(CAR) 양성 PR 도입 사례",
          appliedCase: {
            code: "PR-EUV-POS",
            title: "금속산화물 레지스트(MOR) 도입을 통한 LWR 20% 개선",
            conditions: "광자 흡수율을 높이기 위해 주석(Sn) 기반 유무기 하이브리드 MOR 레지스트 적용.",
            evidenceId: "E-05",
            limitationNote: "전용 현상액 솔벤트 사용에 따른 폐액 처리 설비 증설 필요."
          }
        }
      },
      evidences: {
        "E-05": {
          id: "E-05",
          sourceName: "Samsung Semiconductor Fabrication Glossary",
          pubDate: "2023.11",
          type: "기업 공식 기술 용어집",
          quote: "포토레지스트는 빛에 반응하여 패턴을 형성하는 감광액으로, 노광 부위가 제거되는 양성과 잔류하는 음성으로 구분된다.",
          externalUrl: "https://semiconductor.samsung.com/support/tools-resources/dictionary/just-the-essentials-semiconductor-terminologyzip/",
          urlLabel: "삼성반도체 공식 용어집 바로가기"
        }
      }
    },

    // ----------------------------------------------------
    // 4. 실리콘 잉곳 (Silicon Ingot)
    // ----------------------------------------------------
    "silicon-ingot": {
      id: "silicon-ingot",
      facetId: "facet-process",
      processId: "proc-wafer",
      processName: "웨이퍼 제조",
      title: "실리콘 잉곳 성장 (Silicon Ingot Growth)",
      engName: "Czochralski (CZ) Ingot Growth",
      aliases: ["잉곳", "실리콘 단결정", "초크랄스키 공법"],
      status: "채택됨",
      verificationLevel: "삼성 8대 공정 연재 1편 검증",
      lastReviewed: "2026.09.15",
      version: "v1.0",
      summary: "모래에서 추출한 다결정 실리콘을 고온(1420°C) 도가니에서 녹인 후 종자 결정(Seed)을 회전시키며 천천히 끌어올려 초고순도 단결정 실리콘 기둥을 만드는 공정이다.",
      purpose: "결함이 없는 완벽한 격자 구조(순도 99.9999999% 일레븐 나인)의 웨이퍼 원자재를 확보하기 위함이다.",
      prerequisites: [],
      principles: [
        "초크랄스키(CZ)법: 석영 도가니 내부 융액의 온도 구배와 회전 속도를 제어하여 직경 300mm(12인치)의 균일한 단결정을 성장시킨다.",
        "도핑(Doping): 성장 과정에서 붕소(B)나 인(P)을 극미량 투입하여 P형 또는 N형 웨이퍼의 기저 전기 저항을 결정한다."
      ],
      limitations: [
        "석영 도가니에서 녹아 나오는 산소(O) 불순물로 인해 열처리 중 산소 석출 결함(BMD)이 발생할 수 있음."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "초크랄스키 단결정 성장 및 와이어 쏘 슬라이싱 표준",
          appliedCase: null
        },
        "domain-memory": {
          label: "도메인: 첨단 DRAM 고순도 기판 사양",
          description: "1b nm DRAM 전용 고순도 저산소(Oi < 10ppma) 잉곳 성장 조건",
          appliedCase: {
            code: "INGOT-1B-DRAM",
            title: "초미세 메모리용 MCZ 자기장 인가 결함 억제 잉곳 사양",
            conditions: "단결정 인상 시 수평 자장(Cusp Field 0.3T)을 인가하여 용융 대류를 억제하고 산소 농도 < 10ppma 균일도 유지.",
            evidenceId: "E-05",
            limitationNote: "고온 열처리 시 COP 결함 누설 전류 발생 방지 관리 필수."
          }
        }
      },
      evidences: {
        "E-05": {
          id: "E-05",
          sourceName: "Samsung Semiconductor Fabrication Part-1",
          pubDate: "2023.08",
          type: "기업 공식 기술 교육 연재",
          quote: "실리콘 원료를 녹여 만든 거대한 잉곳을 다이아몬드 와이어 톱으로 얇게 썰어 웨이퍼를 제작한다.",
          externalUrl: "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/eight-essential-semiconductor-fabrication-processes-part-1-what-is-a-wafer/",
          urlLabel: "삼성반도체 8대 공정 연재 1편 원문 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 5. MR-MUF (첨단 패키징)
    // ----------------------------------------------------
    "mr-muf": {
      id: "mr-muf",
      facetId: "facet-process",
      processId: "proc-packaging",
      processName: "첨단 패키징 공정",
      title: "MR-MUF (Mass Reflow Molded Underfill)",
      engName: "Mass Reflow Molded Underfill",
      aliases: ["MR-MUF", "매스 리플로우 몰디드 언더필"],
      status: "채택됨",
      verificationLevel: "SK하이닉스 뉴스룸 기술 해설 검증",
      lastReviewed: "2026.09.28",
      version: "v1.1",
      summary: "반도체 칩을 쌓아 올린 뒤 칩과 칩 사이의 미세 틈에 액체 형태의 보호재(에폭시 몰딩 컴파운드)를 주입하고 일괄 가열 접합하는 차세대 HBM 패키징 기술이다.",
      purpose: "TC-NCF 방식 대비 열 방출 효율을 높이고, 고단 적층 시 발생하는 누적 열압착 스트레스와 휨(Warpage) 현상을 완화하기 위함이다.",
      prerequisites: [{ id: "tsv-interconnect", name: "TSV 관통전극" }],
      principles: [
        "여러 층의 D램 칩을 마이크로 범프 위에 정렬한 후 매스 리플로우 장비에서 열을 가해 범프를 일괄 솔더링한다.",
        "이후 열전도도가 높은 고밀도 실리카 필러가 함유된 액상 EMC를 한 번에 주입하여 하부 언더필과 외벽 몰딩을 동시에 형성한다."
      ],
      limitations: [
        "적층 수가 16단 이상으로 증가하고 칩 간 갭이 10um 이하로 좁아지면 모세관 현상만으로 액상 수지를 균일하게 채우기 어려워 마이크로 보이드 발생 위험이 증가한다."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "학술 및 업계에 공개된 MR-MUF의 일반적 방열 원리와 장단점",
          appliedCase: null
        },
        "company-a-hbm": {
          label: "회사·프로젝트: SK하이닉스 HBM3E 양산",
          description: "Advanced MR-MUF 도입을 통한 HBM3E 열 방출 40% 개선 사례",
          appliedCase: {
            code: "PKG-MUF-ADV",
            title: "신규 액상 보호재 및 열전도율 최적화",
            conditions: "열전도도가 기존 대비 2.5배 높은 고열전도도 세라믹 필러가 적용된 신규 수지 조성물 사용.",
            evidenceId: "E-11",
            limitationNote: "16단 HBM4 적용 시 범프 피치 축소에 따라 추가 가압 공정 병행 검토 중."
          }
        }
      },
      evidences: {
        "E-11": {
          id: "E-11",
          sourceName: "SK hynix Newsroom Technology Release",
          pubDate: "2024.03.19",
          type: "기업 공식 기술 보도자료",
          quote: "MR-MUF는 칩 간 간격에 열전도율이 높은 액상 보호재를 균일하게 채워 넣음으로써 NCF 대비 방열 성능을 약 2.5배 개선하고 12단 적층 양산 수율을 획기적으로 안정화했다.",
          externalUrl: "https://news.skhynix.com/en/details-defined-a-look-at-etch-technology/",
          urlLabel: "SK하이닉스 뉴스룸 기술 아티클 원문 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 6. 하이브리드 본딩 (Hybrid Bonding)
    // ----------------------------------------------------
    "hybrid-bonding": {
      id: "hybrid-bonding",
      facetId: "facet-process",
      processId: "proc-packaging",
      processName: "첨단 패키징 공정",
      title: "하이브리드 본딩 (Direct Cu-Cu Hybrid Bonding)",
      engName: "Direct Bond Interconnect (DBI)",
      aliases: ["하이브리드 본딩", "무범프 본딩", "Cu-Cu 본딩"],
      status: "채택됨",
      verificationLevel: "IEEE ECTC 학술 논문 검증",
      lastReviewed: "2026.10.02",
      version: "v1.0",
      summary: "솔더 마이크로 범프 없이 유전체(SiO2)와 구리(Cu) 패드를 원자 수준으로 맞닿게 하여 상온 접합 및 열처리로 다이렉트 결합하는 궁극의 3D 패키징 기술.",
      purpose: "범프 높이를 완전히 없애 패키지 두께를 획기적으로 줄이고, 범프 피치를 1um 이하로 미세화하여 인터커넥트 대역폭을 극대화하기 위함.",
      prerequisites: [{ id: "cmp-polishing", name: "초정밀 CMP 연마" }],
      principles: [
        "1단계: 유전체 표면을 플라즈마로 활성화하여 상온에서 반데르발스 힘으로 가접합(Pre-bonding)한다.",
        "2단계: 300°C 열처리 시 구리의 열팽창 계수가 유전체보다 큰 특성을 이용해 구리 원자가 상호 확산(Inter-diffusion)되어 전기적으로 완벽히 결합한다."
      ],
      limitations: [
        "표면에 단 하나의 나노 파티클(10nm 미만)만 존재해도 대면적 본딩 결함(Void)이 발생하므로 초청정 클린룸 및 원자 수준 표면 거칠기(RMS < 0.5nm CMP)가 필수적임."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "Cu-Cu 고상 확산 접합 원리 및 마이크로 범프의 전기적 기생 저항 제거 효과",
          appliedCase: null
        }
      },
      evidences: {
        "E-12": {
          id: "E-12",
          sourceName: "IEEE Electronic Components and Technology Conference (ECTC)",
          pubDate: "2023.06",
          type: "학술 연구 논문",
          quote: "Direct Cu-Cu hybrid bonding achieves sub-micron pitch with zero bump standoff height, reducing parasitic inductance by over 70%.",
          externalUrl: "https://www.semi.org/en/products-services/standards",
          urlLabel: "관련 IEEE 학술 발표 자료 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 7. FDC 센서 이상 감지 (생산 운영)
    // ----------------------------------------------------
    "plasma-fdc-sensor": {
      id: "plasma-fdc-sensor",
      facetId: "facet-operations",
      processId: "op-fdc",
      processName: "생산 운영 (FDC)",
      title: "플라즈마 식각 FDC 센서 이상 감지 (Fault Detection)",
      engName: "Plasma Etch FDC Sensor Monitoring",
      aliases: ["FDC", "챔버 결함 탐지", "OES 센서 모니터링"],
      status: "채택됨",
      verificationLevel: "MDPI 학술 논문 검증 (2023)",
      lastReviewed: "2026.10.10",
      version: "v1.0",
      summary: "식각 공정 중 챔버 내부의 광학 발광 분석(OES), RF 임피던스, 챔버 압력 센서 데이터를 실시간 수집하여 플라즈마 아킹(Arcing) 및 공정 드리프트를 조기 감지하는 운영 기술.",
      purpose: "웨이퍼 스크랩(Scrap)을 방지하고 장비 비가동 시간(Downtime)을 최소화하기 위함.",
      prerequisites: [{ id: "dry-etch", name: "플라즈마 건식 식각" }],
      principles: [
        "광학 센서로 플라즈마 특정 파장의 발광 강도를 측정하여 반응 종의 농도 변화와 식각 종말점(EPD)을 판정한다.",
        "다변량 통계(PCA) 모델을 활용하여 정상 운전 영역에서 벗어나는 이상치를 100ms 이내에 검출한다."
      ],
      limitations: [
        "챔버 뷰포트(Viewport) 오염 시 OES 신호 왜곡으로 인한 오경보(False Alarm) 발생 가능."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "반도체 장비 FDC의 표준적인 다변량 통계 모니터링 기법",
          appliedCase: null
        },
        "company-a-hbm": {
          label: "회사·프로젝트: 사내 Fab FDC 모니터링 룰",
          description: "식각 챔버 RF 아킹 조기 인터락 룰 적용 사례",
          appliedCase: {
            code: "FDC-ETCH-RULE-9",
            title: "RF 반사파 15% 급증 시 즉각 공정 인터락 트리거",
            conditions: "RF 자동 임피던스 매처의 위상차 센서가 50ms 이상 임계치 초과 시 장비 레시피 중단 및 웨이퍼 보호.",
            evidenceId: "E-21",
            limitationNote: "센서 응답 지연 시 고가의 정전척(ESC) 손상 위험 있음."
          }
        }
      },
      evidences: {
        "E-21": {
          id: "E-21",
          sourceName: "MDPI Sensors 2023 (Plasma FDC Research)",
          pubDate: "2023.04",
          type: "공개 학술 논문",
          quote: "Real-time FDC using optical emission spectroscopy and RF harmonic distortion achieves 99.2% precision in detecting micro-arcing events in dielectric etch chambers.",
          externalUrl: "https://www.mdpi.com/1424-8220/23/4/1889",
          urlLabel: "MDPI 오픈액세스 논문 원문 읽기"
        }
      }
    },

    // ----------------------------------------------------
    // 8. SPC 통계적 공정 제어 (생산 운영)
    // ----------------------------------------------------
    "spc-control-chart": {
      id: "spc-control-chart",
      facetId: "facet-operations",
      processId: "op-fdc",
      processName: "생산 운영 (FDC)",
      title: "SPC 통계적 공정 관리도 (Statistical Process Control)",
      engName: "Statistical Process Control (SPC)",
      aliases: ["SPC", "관리도", "UCL/LCL", "웨스턴 일렉트릭 룰"],
      status: "채택됨",
      verificationLevel: "Applied Materials APC 가이드 검증",
      lastReviewed: "2026.09.18",
      version: "v1.0",
      summary: "제조 공정에서 발생하는 품질 변동 데이터를 수집하여 통계적 관리 한계선(UCL, LCL, 중심선)을 설정하고, 공정이 통계적 관리 상태에 있는지를 모니터링하는 기법.",
      purpose: "우연 원인에 의한 일반 변동과 이상 원인에 의한 특수 변동을 구분하여 불량 발생 전에 선제적 조치를 취하기 위함.",
      prerequisites: [],
      principles: [
        "정규분포 3시그마(3-sigma) 원리를 적용하여 중심선 기준 ±3σ를 상한선(UCL)과 하한선(LCL)으로 규정한다.",
        "웨스턴 일렉트릭(Western Electric) 룰: 1개 점이 3σ를 벗어나거나, 연속된 9개 점이 중심선 한쪽에 치우치는 등 4대 이상 패턴을 실시간 감지한다."
      ],
      limitations: [
        "데이터 수집 주기(샘플링)가 늦어질 경우 실시간 이상을 제어하지 못하고 지연된 경보가 발생할 수 있음."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "반도체 양산 팹의 전통적 SPC 품질 모니터링 규격",
          appliedCase: null
        },
        "domain-operations": {
          label: "도메인: 팹 품질 통제 이상 판정 사양",
          description: "웨스턴 일렉트릭(Western Electric) 8대 이상 룰 실시간 자동 판정",
          appliedCase: {
            code: "SPC-WEST-ELEC",
            title: "식각/박막 3-Sigma 관리 한계선(UCL/LCL) 초과 즉각 인터락 룰",
            conditions: "식각 깊이 및 박막 두께 센서 데이터에 대해 3-Sigma 관리 한계선 초과 및 9연속 중심선 편향 즉각 인터락 트립.",
            evidenceId: "E-02",
            limitationNote: "측정 노이즈가 과다한 센서의 경우 펄스 경보(False Positive) 유발로 설비 가동률 저하 위험."
          }
        }
      },
      evidences: {
        "E-02": {
          id: "E-02",
          sourceName: "Applied Materials Process Handbook v3.2",
          pubDate: "2023.09",
          type: "장비사 공정 가이드",
          quote: "Statistical Process Control charts establish ±3-sigma boundaries to distinguish random noise from assignable tool faults.",
          externalUrl: "https://www.appliedmaterials.com/us/en/glossary.html",
          urlLabel: "Applied Materials 통계적 제어 가이드 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 9. R2R 첨단 공정 제어 (생산 운영)
    // ----------------------------------------------------
    "run-to-run": {
      id: "run-to-run",
      facetId: "facet-operations",
      processId: "op-apc",
      processName: "생산 운영 (APC)",
      title: "R2R 첨단 공정 제어 (Run-to-Run Control)",
      engName: "Run-to-Run (R2R) Control",
      aliases: ["R2R", "런투런", "APC 피드포워드/피드백"],
      status: "채택됨",
      verificationLevel: "Applied Materials APC 백서 검증",
      lastReviewed: "2026.10.08",
      version: "v1.2",
      summary: "이전 웨이퍼(또는 랏)의 가공 후 인라인 계측 결과를 수학적 모델에 대입하여, 바로 다음 웨이퍼의 공정 파라미터(식각 시간, CMP 연마 압력, 증착 전력)를 실시간 자동 보정하는 폐루프(Closed-loop) 제어 시스템.",
      purpose: "소모품(CMP 패드, 챔버 파츠) 마모나 케미컬 열화로 인해 발생하는 공정 드리프트(Drift)를 사람 개입 없이 자동으로 상쇄하기 위함.",
      prerequisites: [{ id: "spc-control-chart", name: "SPC 통계적 공정 제어" }],
      principles: [
        "지수 가중 이동 평균(EWMA) 필터를 적용하여 노이즈를 제거하고 실제 설비 상태의 추세(Trend)를 추정한다.",
        "선행 공정 계측값(예: 포토 선폭)을 바탕으로 현재 공정(식각 시간)을 미리 보정하는 피드포워드(Feed-forward) 제어를 병행한다."
      ],
      limitations: [
        "수학적 플랜트 모델이 부정확하거나 계측 오차가 유입될 경우 오히려 공정 편차를 증폭시키는 헌팅(Hunting) 현상 발생 위험."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "SEMI 표준 및 장비사 표준 R2R 피드백 알고리즘 구조",
          appliedCase: null
        },
        "domain-operations": {
          label: "도메인: 식각/CMP R2R 폐루프 제어",
          description: "EWMA 가중 이동 평균 기반 웨이퍼 간 식각 시간 실시간 피드포워드/피드백 보정",
          appliedCase: {
            code: "R2R-EWMA-ETCH",
            title: "선행 포토 CD 계측치 기반 하부 식각 시간 가감 보정 레시피",
            conditions: "이전 랏의 박막 잔류 두께 계측값(Ellipsometer)을 기반으로 현재 챔버의 식각 시간을 초 단위로 동적 가감(Gain λ=0.4).",
            evidenceId: "E-02",
            limitationNote: "계측기 지연(Metrology Delay) 발생 시 R2R 제어 피드백 루프의 위상 지연으로 과보정 진동 발생."
          }
        }
      },
      evidences: {
        "E-02": {
          id: "E-02",
          sourceName: "Applied Materials Advanced Process Control",
          pubDate: "2023.09",
          type: "장비사 공정 가이드",
          quote: "Run-to-Run control dynamically adjusts recipe parameters between runs using EWMA filters to eliminate drift.",
          externalUrl: "https://www.appliedmaterials.com/us/en/glossary.html",
          urlLabel: "AMAT 공식 APC 자료 보기"
        }
      }
    },

    // ----------------------------------------------------
    // 10. EES & RMS 레시피 관리 시스템 (생산 운영)
    // ----------------------------------------------------
    "ees-rms": {
      id: "ees-rms",
      facetId: "facet-operations",
      processId: "op-ees",
      processName: "생산 운영 (EES)",
      title: "EES & RMS 레시피 관리 시스템",
      engName: "Equipment Engineering System & Recipe Management",
      aliases: ["EES", "RMS", "레시피 관리", "SECS/GEM 통신"],
      status: "채택됨",
      verificationLevel: "SEMI 국제 표준 규격 검증",
      lastReviewed: "2026.09.25",
      version: "v1.1",
      summary: "팹 내 수백 대의 장비와 MES(제조 실행 시스템) 간에 SEMI 통신 표준(SECS/GEM)을 통해 연결되어, 승인된 공식 레시피만을 장비에 다운로드하고 무단 변경을 원천 차단하는 엔지니어링 통제 시스템.",
      purpose: "작업자의 레시피 파라미터 오입력으로 인한 수천억 원 대의 대형 웨이퍼 폐기 사고(Scrap)를 방지하기 위함.",
      prerequisites: [],
      principles: [
        "레시피 바디 체크섬(Body Checksum) 비교: 장비가 실행하려는 레시피 파일의 해시값과 RMS 서버의 승인본 해시값을 실시간 대조하여 1비트라도 다르면 장비 가동을 인터락(Interlock)한다.",
        "SEMI E30(GEM), E98 표준을 준수하여 가스 유량, 온도, 압력의 상한/하한 안전 영역(Hard/Soft Limit)을 강제한다."
      ],
      limitations: [
        "네트워크 단절 시 팹 전 장비가 안전 모드로 진입하여 전체 생산이 일시 중단될 수 있음."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "SEMI E30 및 E98 표준 기반 레시피 파라미터 검증 체계",
          appliedCase: null
        },
        "domain-operations": {
          label: "도메인: 팹 레시피 파라미터 무결성 통제",
          description: "SEMI E139 표준 기반 레시피 파라미터 골든 버전 일치성 자동 검증",
          appliedCase: {
            code: "RMS-GOLDEN-VER",
            title: "공정 레시피 체크섬(MD5) 실시간 대조 및 무단 변경 차단 룰",
            conditions: "작업 착수(Lot Start) 직전 챔버의 RF 전력, 가스 유량(MFC), 압력 파라미터가 승인된 골든 레시피와 100% 일치하는지 자동 상호 인증.",
            evidenceId: "E-04",
            limitationNote: "비인가 엔지니어 수동 파라미터 조작 시 장비 자동 잠금(Lockout) 발동."
          }
        }
      },
      evidences: {
        "E-04": {
          id: "E-04",
          sourceName: "SEMI International Standards E98/E30",
          pubDate: "2022.06",
          type: "국제 반도체 표준 규격",
          quote: "Standard Specification for Recipe Management System: Enforces strict golden recipe checksum verification and parameter interlocks across 300mm tools.",
          externalUrl: "https://www.semi.org/en/products-services/standards",
          urlLabel: "SEMI 표준 인터페이스 규격 확인"
        }
      }
    },

    // ----------------------------------------------------
    // 11. 플라즈마 방전 (Plasma Discharge)
    // ----------------------------------------------------
    "plasma-discharge": {
      id: "plasma-discharge",
      facetId: "facet-equipment",
      processId: "proc-etch",
      processName: "식각/증착 공통",
      title: "플라즈마 방전 및 시스 형성 (Plasma Discharge & Sheath)",
      engName: "Plasma Discharge & RF Sheath",
      aliases: ["플라즈마 방전", "RF 방전", "CCP/ICP 방전"],
      status: "채택됨",
      verificationLevel: "플라즈마 물리학 표준 검증",
      lastReviewed: "2026.10.12",
      version: "v1.2",
      summary: "진공 챔버 내에서 고주파(RF) 전계를 인가하여 공정 가스를 전자, 양이온, 중성 라디칼로 해리시켜 제4의 물질 상태인 준중성(Quasi-neutral) 플라즈마를 발생시키는 핵심 물리 현상이다.",
      purpose: "열역학적으로 고온에서만 일어나는 화학 반응을 상온~중온 영역에서 플라즈마 에너지로 활성화하여 박막을 수직 식각하거나 저온 증착하기 위함이다.",
      prerequisites: [],
      principles: [
        "용량 결합 플라즈마(CCP)와 유도 결합 플라즈마(ICP): 고주파 안테나의 유도 자기장으로 고밀도 전자 흐름을 유도하여 플라즈마 밀도를 10^11~10^12 cm^-3 수준으로 유지한다.",
        "플라즈마 시스(Sheath) 전위: 전자의 빠른 이동 속도로 인해 웨이퍼 표면에 음의 자가 바이어스(DC Bias)가 형성되며, 이로 인해 양이온이 웨이퍼로 수직 가속된다."
      ],
      limitations: [
        "플라즈마 불균일 시 웨이퍼 반경 방향으로 전자 온도(Te) 편차가 발생하여 식각률 및 임계 선폭(CD) 불균일을 초래한다.",
        "챔버 벽면 유전체 부품에 전하가 축적될 경우 비정상 마이크로 아킹(Arcing)이 발생하여 웨이퍼가 손상된다."
      ],
      perspectives: {
        "default": {
          label: "공통 기본 지식",
          description: "산업 표준 및 학술 문헌에서 합의된 플라즈마 방전 및 시스 형성 원리",
          appliedCase: null
        },
        "domain-foundry": {
          label: "도메인: 선단 2nm CCP/ICP 플라즈마 제어 사양",
          description: "듀얼 주파수(27MHz/2MHz) 플라즈마 챔버 이온 에너지 분리 제어",
          appliedCase: {
            code: "CCP-ICP-PLASMA",
            title: "선단 파운드리 듀얼 주파수 플라즈마 소스 독립 제어 레시피",
            conditions: "고주파(VHF 60MHz)로 플라즈마 밀도를 높이고, 저주파(LF 2MHz)로 웨이퍼 시스 바이어스 가속 전압을 정밀 제어하여 수직 비등방성 극대화.",
            evidenceId: "E-LAM-PLASMA",
            limitationNote: "챔버 임피던스 매칭 부정합 시 플라즈마 아킹 및 반사파(Reflected Power) 발생."
          }
        }
      },
      relations: {
        is_a: [{ id: "proc-etch", name: "식각 공정 (Etching)" }],
        part_of: [{ id: "dry-etch", name: "플라즈마 건식 식각" }],
        next_step: [{ id: "dry-etch", name: "웨이퍼 이온 보조 식각" }]
      },
      evidences: {
        "E-LAM-PLASMA": {
          id: "E-LAM-PLASMA",
          sourceName: "Lam Research Plasma Physics & RF Technology Guide",
          pubDate: "2024.02",
          type: "장비사 공식 기술 백서",
          quote: "Plasma discharge energized by RF capacitive or inductive fields dissociates process gases into chemically reactive radicals and anisotropic positive ions accelerated across the sheath.",
          externalUrl: "https://www.lamresearch.com/technology-solutions/",
          urlLabel: "Lam Research Plasma Physics Guide 공식 링크"
        }
      }
    }
  },

  // ── 3. 공식 출처 팩 (사전 적재된 공식 팩 vs 온디맨드 확장 팩) ──
  preSeededSources: [
    {
      id: "seed-samsung",
      name: "삼성반도체 8대 공정 공식 교육 연재",
      status: "위키 뼈대로 사전 적재 완료 (Pre-seeded)",
      coverage: "기본 제조 흐름 8단계 및 기초 용어 45종 (잉곳, 포토, 식각 등)"
    },
    {
      id: "seed-semi",
      name: "SEMI International Standards (E98, E10, E30 GEM)",
      status: "위키 표준으로 사전 적재 완료 (Pre-seeded)",
      coverage: "장비 모듈 인터페이스, EES/RMS 레시피 및 FDC 데이터 통신 표준"
    },
    {
      id: "seed-amat",
      name: "Applied Materials Technical Glossary & APC Handbook",
      status: "위키 기본으로 사전 적재 완료 (Pre-seeded)",
      coverage: "식각, 증착, CMP, R2R 첨단 제어 및 SPC 통계 제어 공식 용어"
    }
  ],

  onDemandSources: [
    {
      id: "sp-skhynix",
      name: "SK하이닉스 뉴스룸 기술 심층 해설 (패키징 & 식각 세부)",
      category: "세부 공정·양산 사례",
      provider: "SK hynix Newsroom",
      docCount: 8,
      reliability: "공식 기술 해설",
      description: "DRAM 식각 세부 단계(ISO/BG) 및 MR-MUF 패키징 혁신 사례",
      checked: true
    },
    {
      id: "sp-equipment",
      name: "Lam Research Technical Glossary (ALE & HARC)",
      category: "장비·원리·세부 용어",
      provider: "Lam Research",
      docCount: 32,
      reliability: "글로벌 톱 식각 장비사",
      description: "HARC, ALE(원자층 식각), Cryogenic 식각 물리 원리 및 한계",
      checked: true
    },
    {
      id: "sp-intel-glass",
      name: "차세대 유리기판(Glass Substrate) 최신 기술 백서 (2024)",
      category: "차세대 패키징 신기술",
      provider: "인텔 패키징 포럼 & imec",
      docCount: 4,
      reliability: "신기술 발표 백서",
      description: "TGV(Through Glass Via), 대면적 유리 코어 가공 및 패널 패키징",
      checked: true
    }
  ],

  // ── 4. 발굴된 신규 개념 후보 큐 ──
  discoveredCandidates: [
    {
      id: "cand-tgv",
      title: "TGV (Through Glass Via)",
      category: "차세대 패키징",
      source: "인텔 패키징 포럼 2024 발표자료 & imec 기술 백서",
      recommendedAction: "신규 개념 등록",
      reason: "유리기판 상하부를 레이저로 관통하여 초미세 피치 전극을 형성하는 차세대 인터커넥트 기술로, 기존 실리콘 인터포저 TSV를 대체할 핵심 후보임.",
      suggestedDefinition: "유리기판(Glass Core)에 레이저 개질 및 화학 식각을 적용하여 10um 미만의 미세 수직 관통 홀을 가공하고 구리로 채워 넣는 전기적 연결 기술.",
      status: "대기중"
    },
    {
      id: "cand-ale",
      title: "ALE (Atomic Layer Etching)",
      category: "식각 공정",
      source: "Lam Research Technical Glossary 2024",
      recommendedAction: "식각 하위 개념 등록",
      reason: "원자층 증착(ALD)의 역과정으로, 표면 개질과 제거를 분리하여 원자 한 층 단위로 정밀 제거하는 초극미세 식각 기술. 2nm 공정 필수 기술로 부상 중.",
      suggestedDefinition: "화학적 표면 흡착 반응과 물리적 탈착 반응을 분리 순환시켜 원자 한 층(Angstrom 단위) 두께로 표면을 균일하게 깎아내는 차세대 디지털 식각 공정.",
      status: "대기중"
    },
    {
      id: "cand-plp",
      title: "패널 레벨 패키징 (PLP)",
      category: "첨단 패키징",
      source: "SK하이닉스 후공정 뉴스룸 8편",
      recommendedAction: "기존 FOPLP 별칭 추가",
      reason: "기존 원형 웨이퍼가 아닌 사각형 대형 패널 단위로 칩을 재배열하여 패키징하는 방식으로, 이미 등록된 FOPLP와 85% 기술적 맥락 일치하여 별칭 통합 권장.",
      suggestedDefinition: "대면적 사각 패널 기판을 활용하여 생산 면적 효율을 극대화한 팬아웃 패키징 공정의 범용 명칭.",
      status: "대기중"
    }
  ],

  // ── 5-B. 최근 공식 출처 발굴 로그 (Recent Discovery Logs) ──
  discoveryLogs: [
    {
      id: "disc-01",
      topic: "극저온 식각 저탄소 대체 가스",
      title: "극저온 식각 저GWP 대체 가스 (CF3I / C3F6FB) 물성",
      sourcesCount: 3,
      sourcesSummary: "Lam 백서 · IEEE 논문 · SEMI S23",
      date: "오늘 11:20",
      reviewId: "rev-01",
      status: "검토 대기",
      badgeClass: "badge-verified"
    },
    {
      id: "disc-02",
      topic: "차세대 유리기판 TGV",
      title: "TGV (Through Glass Via) 레이저 유도 식각 (LIDE)",
      sourcesCount: 3,
      sourcesSummary: "Intel 백서 · IEEE ECTC · SEMI",
      date: "어제 16:45",
      reviewId: "rev-02",
      status: "검토 대기",
      badgeClass: "badge-scale-2"
    },
    {
      id: "disc-03",
      topic: "High-NA EUV 펠리클",
      title: "High-NA 탄소나노튜브(CNT) 펠리클 92% 투과율 규격",
      sourcesCount: 3,
      sourcesSummary: "ASML 백서 · imec 논문 · SEMI P48",
      date: "2026.10.13",
      reviewId: null,
      status: "승인 완료",
      badgeClass: "badge-level-2"
    }
  ],

  // ── 5. 개념 단위 검토 큐 (HITL Review Queue) ──
  reviewQueue: [
    {
      id: "rev-01",
      conceptId: "dry-etch",
      conceptTitle: "플라즈마 건식 식각 (Plasma Dry Etching)",
      proposalsCount: 2,
      reviewType: "내용 보완 및 표준 매핑",
      author: "H설계원 (현업 엔지니어)",
      date: "2026.10.14",
      status: "검토 대기",
      currentContent: "플라즈마 상태의 반응성 가스와 이온을 가속시켜 웨이퍼 표면의 불필요한 박막을 선택적으로 제거하는 공정이다. 물리적 충돌과 화학적 반응이 결합된 이온 보조 식각 메커니즘을 사용한다.",
      aiMergedDraft: "플라즈마 상태의 반응성 가스와 이온을 가속시켜 웨이퍼 표면의 불필요한 박막을 선택적으로 제거하는 공정이다. 물리적 충돌과 화학적 반응이 결합된 이온 보조 식각 메커니즘을 사용하며, [추가] 고밀도 유도결합 플라즈마(ICP) 소스 도입 시 플라즈마 밀도와 이온 입사 에너지를 독립적으로 정밀 제어할 수 있다. [E-02, E-04]",
      diffAdded: "고밀도 유도결합 플라즈마(ICP) 소스 도입 시 플라즈마 밀도와 이온 입사 에너지를 독립적으로 정밀 제어할 수 있다. [E-02, E-04]",
      integrityCheck: {
        evidenceMatch: "100% 일치 (Applied Materials v3.2 & SEMI E98 검증)",
        ontologyConflict: "충돌 없음 (상위 개념 '식각 공정'과 계층 일치)",
        impactScope: "연관 개념 [ICP-RIE]에 정의 보완 권장 1건 발생"
      }
    },
    {
      id: "rev-02",
      conceptId: "mr-muf",
      conceptTitle: "MR-MUF (Mass Reflow Molded Underfill)",
      proposalsCount: 1,
      reviewType: "신규 방열 수치 근거 보완",
      author: "조사 작업실 에이전트 자동 제안",
      date: "2026.10.13",
      status: "검토 대기",
      currentContent: "열전도도가 높은 고밀도 실리카 필러가 함유된 액상 EMC를 한 번에 주입하여 하부 언더필과 외벽 몰딩을 동시에 형성한다.",
      aiMergedDraft: "열전도도가 높은 고밀도 실리카 필러가 함유된 액상 EMC를 한 번에 주입하여 하부 언더필과 외벽 몰딩을 동시에 형성한다. [추가] SK하이닉스 2024 발표에 따르면 기존 대비 열저항이 약 40% 감소하여 칩 최고 온도를 3°C 낮추는 방열 개선 효과가 실측되었다. [E-11]",
      diffAdded: "SK하이닉스 2024 발표에 따르면 기존 대비 열저항이 약 40% 감소하여 칩 최고 온도를 3°C 낮추는 방열 개선 효과가 실측되었다. [E-11]",
      integrityCheck: {
        evidenceMatch: "100% 일치 (SK hynix Newsroom 2024.03 교차 검증)",
        ontologyConflict: "충돌 없음",
        impactScope: "영향받는 하위 문서 없음"
      }
    }
  ],

  // ── 6. AI 분석실: 엔지니어 현업 고민(Pain-point) 기반 스마트 질문 추천 풀 ──
  engineerPainPoints: [
    {
      id: "pain-1",
      keywords: ["hbm", "패키징", "mrmuf", "ncf", "방열", "휨", "warpage", "적층"],
      userProblem: "적층 수가 늘어날수록 칩이 휘고(Warpage) 열 방출이 안 됩니다.",
      recommendedTitle: "HBM 고단 적층: MR-MUF vs TC-NCF 방열·휨 한계 비교",
      prompt: "HBM 고단 적층 패키징에서 MR-MUF와 NCF 기술의 공정 조건 및 방열 한계 비교",
      paramA: { tech: "MR-MUF", company: "SK하이닉스", condition: "리플로우 가압 1.5MPa, 실리카 85%" },
      paramB: { tech: "TC-NCF", company: "마이크론/삼성", condition: "본딩 가압 3.5MPa, 3초 열압착" },
      domain: "첨단 패키징"
    },
    {
      id: "pain-2",
      keywords: ["식각", "cryo", "극저온", "채널홀", "nand", "틸팅", "harc", "보잉"],
      userProblem: "비아 홀 종횡비(Aspect Ratio)가 80:1을 넘어가며 바닥 틸팅과 식각 정지가 발생합니다.",
      recommendedTitle: "HARC 식각 한계: Cryogenic 극저온 식각 vs 상온 고출력 RIE 비교",
      prompt: "3D NAND 200단/300단 채널 홀 가공 시 극저온 식각과 상온 고출력 RIE의 선택비 및 틸팅 제약 비교",
      paramA: { tech: "Cryogenic Etch", company: "Lam Research", condition: "-60°C 극저온 패시베이션, 펄스 RF" },
      paramB: { tech: "High-Power RIE", company: "Applied Materials", condition: "상온 13.56MHz 고바이어스 연속파" },
      domain: "식각 공정"
    },
    {
      id: "pain-3",
      keywords: ["fdc", "oes", "센서", "아킹", "챔버", "드리프트", "spc", "이상감지"],
      userProblem: "식각 챔버 아킹 센서 오경보 및 내벽 오염으로 랏(Lot) 간 선폭 산포가 커집니다.",
      recommendedTitle: "챔버 모니터링: 실시간 전스펙트럼 OES FDC vs 전통적 3-Sigma SPC 대조",
      prompt: "플라즈마 식각 챔버 센서 모니터링에서 전스펙트럼 OES 딥러닝 이상 감지와 전통적 SPC의 검출 속도 및 오경보율 비교",
      paramA: { tech: "다변량 OES FDC", company: "SEMI E133 규격", condition: "100ms 전스펙트럼 딥 오토인코더" },
      paramB: { tech: "전통적 3-Sigma SPC", company: "SEMI E98 표준", condition: "단일 센서 3-Sigma 관리선" },
      domain: "생산 운영 (FDC)"
    },
    {
      id: "pain-4",
      keywords: ["노광", "euv", "high-na", "high na", "아나모픽", "더블패터닝", "해상도", "포토"],
      userProblem: "2nm 이하 노드에서 0.33 NA 더블 패터닝의 오버레이 오차와 마스크 비용이 감당 안 됩니다.",
      recommendedTitle: "차세대 노광: High-NA (0.55 NA) 단일 노광 vs 0.33 NA 더블 패터닝 수율·단가 비교",
      prompt: "2nm 선단 로직 패터닝에서 High-NA EUV 단일 노광과 0.33 NA EUV 더블 패터닝의 마스크 매수, 오버레이 제어 및 경제성 비교",
      paramA: { tech: "High-NA EUV (0.55 NA)", company: "ASML EXE:5000", condition: "아나모픽 4x/8x, 단일 노광, MOR 감광액" },
      paramB: { tech: "Low-NA EUV (0.33 NA)", company: "ASML NXE:3600", condition: "더블 패터닝(LELE), 마스크 2매" },
      domain: "포토 공정"
    },
    {
      id: "pain-5",
      keywords: ["dram", "비트라인", "에어갭", "airgap", "기생용량", "센싱마진", "rc지연"],
      userProblem: "DRAM 비트라인 간격이 30nm 이하로 좁아져 기생 용량(Cb) 때문에 센스앰프 마진이 부족합니다.",
      recommendedTitle: "DRAM 배선 지연: 비트라인 선택적 에어갭(Air Gap) vs 저유전체 절연막 비교",
      prompt: "1b/1c nm DRAM에서 비트라인 기생 커패시턴스(Cb) 저감을 위한 선택적 에어갭 공정과 저유전체 박막의 센싱 마진 및 기계적 신뢰성 비교",
      paramA: { tech: "선택적 에어갭 (k=1.0)", company: "SK하이닉스/삼성", condition: "플라즈마 핀치오프 밀봉, Cb 28% 저감" },
      paramB: { tech: "Low-k 절연막 (k=2.5)", company: "기존 양산 공정", condition: "SiOC/SiBCN 증착 충진" },
      domain: "금속 배선 공정"
    },
    {
      id: "pain-6",
      keywords: ["gaa", "mbcfet", "sige", "나노시트", "선택식각", "로직", "3nm", "2nm"],
      userProblem: "GAA 나노시트 릴리즈 시 Si 채널 손상 없이 SiGe만 150:1 이상의 고선택비로 깎아내야 합니다.",
      recommendedTitle: "GAA 채널 형성: 무플라즈마 기상 ClF3 화학 식각 vs 습식 화학 식각 비교",
      prompt: "3nm GAA 트랜지스터 제조 시 SiGe 초격자 선택적 제거를 위한 무플라즈마 기상 식각과 습식 식각의 선택비 및 채널 표면 조도 비교",
      paramA: { tech: "무플라즈마 기상 식각", company: "IBM / CEA-Leti", condition: "다운스트림 ClF3, 선택비 > 150:1, 손실 < 0.2nm" },
      paramB: { tech: "습식 화학 식각", company: "전통적 습식 케미컬", condition: "HF/HNO3 혼합액, 모세관 스틱션 위험" },
      domain: "식각 공정"
    },
    {
      id: "pain-7",
      keywords: ["본딩", "하이브리드본딩", "dbi", "범프", "chiplet", "이종집적", "tsv", "soic"],
      userProblem: "마이크로범프 피치가 20μm 이하로 좁아지며 리플로우 시 솔더 브릿지 쇼트가 발생합니다.",
      recommendedTitle: "초미세 3D 적층: Cu-Cu DBI 하이브리드 본딩 vs 솔더 마이크로범프 플립칩 비교",
      prompt: "차세대 HBM4 및 3D Chiplet 집적에서 Cu-Cu 직접 하이브리드 본딩과 솔더 마이크로범프의 배선 밀도, 기생 저항 및 접합 수율 비교",
      paramA: { tech: "Cu-Cu DBI 하이브리드 본딩", company: "TSMC SoIC / Xperi", condition: "피치 < 1μm, 범프리스 직접 접합, 200°C 어닐링" },
      paramB: { tech: "솔더 마이크로범프", company: "기존 플립칩 공정", condition: "피치 25μm, 솔더 리플로우 및 언더필" },
      domain: "첨단 패키징"
    },
    {
      id: "pain-8",
      keywords: ["스크러버", "pfc", "온실가스", "cf4", "esg", "탄소중립", "서브팹", "친환경"],
      userProblem: "식각 챔버에서 배출되는 난분해성 CF4 배기가스가 일반 버너 스크러버에서 분해되지 않습니다.",
      recommendedTitle: "팹 배기 탄소중립: 마이크로웨이브 플라즈마-열 스크러버 vs LNG 화염 스크러버 비교",
      prompt: "반도체 식각 배기 온실가스(CF4, SF6) 정화를 위한 플라즈마-열 융합 스크러버와 기존 화염 연소식 스크러버의 분해 제거 효율(DRE) 및 에너지 소비 비교",
      paramA: { tech: "플라즈마-열 융합 스크러버", company: "SEMI ESG 표준", condition: "2500K 플라즈마 토치 + H2O 산화, DRE > 99.5%" },
      paramB: { tech: "LNG 화염 버너", company: "기존 서브팹 설비", condition: "1400K 가스 연소, CF4 DRE < 85%" },
      domain: "생산 운영 (EES)"
    }
  ],

  // AI 분석실 실행 시뮬레이션 데이터
  aiStudioDemo: {
    question: "HBM 고단 적층 패키징에서 MR-MUF와 NCF 기술의 공정 조건 및 방열 한계 비교",
    contextTags: {
      targetA: "SK하이닉스 (MR-MUF)",
      targetB: "마이크론 (TC-NCF)",
      domain: "첨단 패키징",
      releaseVersion: "2026.10 최신"
    },
    snapshots: [
      {
        id: "snap-1",
        step: 1,
        title: "공통 물리 정의 및 원리 추출",
        time: "10:14:02",
        status: "완료",
        data: {
          summary: "위키 온톨로지에서 MR-MUF(액상 주입 일괄 경화)와 NCF(필름 열압착)의 표준 정의와 물리적 기본 메커니즘을 성공적으로 추출했습니다.",
          details: [
            "MR-MUF: 마이크로 범프 솔더링 후 액상 수지 일괄 몰딩",
            "NCF: 칩마다 비전도성 필름을 붙여 개별 열압착(TCB) 접합"
          ]
        }
      },
      {
        id: "snap-2",
        step: 2,
        title: "관점별 양산 조건 매핑",
        time: "10:14:18",
        status: "완료",
        data: {
          summary: "A사(MR-MUF)와 B사(NCF)의 공개 보고서 및 양산 사례에서 주요 공정 압력, 온도, 가스 조건을 매핑했습니다. (이 전제를 수정하여 재실행 가능)",
          details: [
            "A사 (SK하이닉스): 리플로우 온도 260°C, 진공 몰딩 가압 1.5MPa, 실리카 필러 85wt%",
            "B사 (마이크론): 본딩 헤드 가압 3.5MPa, 열압착 시간 3초, 필름 두께 균일도 ±1.5um"
          ]
        }
      },
      {
        id: "snap-3",
        step: 3,
        title: "다차원 비교 도출 및 한계 분석",
        time: "10:14:35",
        status: "완료 (현재)",
        data: {
          matrix: [
            { axis: "접합 방식 및 열 제어", mrf: "액상 에폭시 일괄 주입 및 오븐 가압 경화 (열 충격 분산)", ncf: "칩 적층 시마다 초정밀 열압착(TCB) 진행 (누적 열 스트레스)" },
            { axis: "방열 성능 (W/m·K)", mrf: "상대적 우수 (열전도율 2.5배 고밀도 필러 함유)", ncf: "중간 (계면 열저항 존재, 필름 특성상 필러 증량 한계)" },
            { axis: "16단 이상 적층 한계", mrf: "10um 이하 좁은 갭에서의 마이크로 보이드 발생 위험", ncf: "적층 수 증가에 따른 칩 휨(Warpage) 및 하부 범프 재용융 위험" },
            { axis: "근거 신뢰 수준", mrf: "공식 기술 문서 3건 교차 확인 [E-11]", ncf: "학술 논문 및 공개 세미나 자료 기반 [E-12]" }
          ],
          aiNote: "💡 관련성 판단: 동일 과제인 '고단 HBM 방열 및 휨 제어' 목적의 경쟁 기술 경로로 관련성 높음. 다만 NCF의 16단 한계 수치는 학술 논문 기반 추정치이며 B사 최신 비공개 규격이 아님.",
          pendingWikiProposal: {
            title: "NCF 공정 한계 항목 보완안",
            content: "16단 고단 적층 시 본딩 압력 누적으로 인한 하부 칩 휨(Warpage) 제약 사항을 공용 위키 'NCF' 문서에 보완할 필요가 있습니다."
          }
        }
      }
    ]
  }
};

// Sprint 1 추출 온톨로지 개념 자동 병합
if (typeof sprint1Concepts !== 'undefined') {
  Object.assign(WikiStore.concepts, sprint1Concepts);
}

// Sprint 2 추출 온톨로지 개념 자동 병합
if (typeof sprint2Concepts !== 'undefined') {
  Object.assign(WikiStore.concepts, sprint2Concepts);
}

// Sprint 3 추출 온톨로지 개념 자동 병합
if (typeof sprint3Concepts !== 'undefined') {
  Object.assign(WikiStore.concepts, sprint3Concepts);
}



