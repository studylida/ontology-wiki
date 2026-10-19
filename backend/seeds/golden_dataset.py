"""Golden Seed Dataset for Semiconductor Causal Ontology Wiki.

Contains verified golden records for 5 core domain processes:
1. HBM3E Packaging: TCB (Thermal Compression Bonding) vs MR-MUF
2. Etch Scaling: Plasma Dry Etch vs Cryogenic Etch
3. Photolithography Optics: 0.33NA EUV vs 0.55NA High-NA EUV
4. Transistor Device: 2nm GAA (MBCFET) vs FinFET
5. Fab Operations: FDC (Fault Detection & Classification) Real-time APC

Strictly adheres to:
- 보상 파라미터 (Compensating Parameters)
- 꼬리질문 (Tail-Questions / deep_dive_history)
- 사유 / overrideReason (금지어: '전문가 사유' 엄격 배제)
"""
from typing import Dict, List, Any

# ==============================================================================
# 1. 공인 출처 엔티티 (EvidenceSource)
# ==============================================================================
EVIDENCE_SOURCES: List[Dict[str, Any]] = [
    {
        "id": "E-01",
        "source_name": "SK hynix Advanced MR-MUF Technology Whitepaper",
        "source_type": "official_whitepaper",
        "publisher": "SK hynix",
        "published_date": "2026.01",
        "quote": "Advanced MR-MUF utilizes liquid epoxy molding compound to achieve 2.5x higher thermal dissipation and zero-void gap filling compared to conventional NCF in 16-high HBM3E stacks.",
        "section_context": "Section 3.2 Packaging Reliability, p.8 Table 1",
        "relevance_score": 0.98,
        "external_url": "https://news.skhynix.com/technology/advanced-mr-muf",
        "url_label": "SK하이닉스 백서 원문 ➔",
        "credibility_tier": "Tier 1 (공식 제조사)",
        "referenced_concepts": [
            {"conceptId": "concept-mrmuf", "name": "MR-MUF"},
            {"conceptId": "concept-tcb", "name": "열압착 본딩 (TCB)"}
        ]
    },
    {
        "id": "E-02",
        "source_name": "Samsung Electronics Semiconductor Packaging Reliability Report",
        "source_type": "official_whitepaper",
        "publisher": "Samsung",
        "published_date": "2026.02",
        "quote": "TC-NCF requires strict bonding force control (140N~160N) to avoid micro-crack formation in ultra-thin micro bumps while applying non-conductive film.",
        "section_context": "Section 4.1 Thermo-Compression Dynamics, p.15",
        "relevance_score": 0.95,
        "external_url": "https://semiconductor.samsung.com/newsroom/tech-blog/packaging-ncf",
        "url_label": "삼성전자 기술 블로그 원문 ➔",
        "credibility_tier": "Tier 1 (공식 제조사)",
        "referenced_concepts": [
            {"conceptId": "concept-tcb", "name": "열압착 본딩 (TCB)"}
        ]
    },
    {
        "id": "E-03",
        "source_name": "Lam Research Cryogenic Etch for 3D NAND Whitepaper",
        "source_type": "official_whitepaper",
        "publisher": "Lam",
        "published_date": "2026.01",
        "quote": "Operating at wafer chuck temperatures of -60℃ enables extreme chemical passivating layer freezing, doubling etch rates while maintaining 99.8% vertical profile selectivity in 300+ layer HARC channels.",
        "section_context": "Section 2.4 Cryo Chamber Thermodynamics, p.12",
        "relevance_score": 0.97,
        "external_url": "https://www.lamresearch.com/technology/cryo-dielectric-etch",
        "url_label": "Lam Research 솔루션 원문 ➔",
        "credibility_tier": "Tier 1 (공식 제조사)",
        "referenced_concepts": [
            {"conceptId": "concept-cryo-etch", "name": "극저온 식각"},
            {"conceptId": "concept-dry-etch", "name": "플라즈마 건식 식각"}
        ]
    },
    {
        "id": "E-04",
        "source_name": "ASML High-NA EUV Lithography Optics & System Architecture",
        "source_type": "official_whitepaper",
        "publisher": "ASML",
        "published_date": "2025.11",
        "quote": "High-NA EUV with 0.55 numerical aperture achieves 8nm half-pitch printing resolution using anamorphic magnification optics (4x in X, 8x in Y), eliminating mask shadowing.",
        "section_context": "Section 3.1 Optical Physics & Anamorphic Projection, p.6",
        "relevance_score": 0.99,
        "external_url": "https://www.asml.com/en/technology/high-na-euv",
        "url_label": "ASML High-NA 공식 기술 문서 ➔",
        "credibility_tier": "Tier 1 (공식 제조사)",
        "referenced_concepts": [
            {"conceptId": "concept-high-na-euv", "name": "High-NA EUV 노광"}
        ]
    },
    {
        "id": "E-05",
        "source_name": "Samsung Electronics MBCFET (Multi-Bridge-Channel FET) 2nm Architecture",
        "source_type": "official_whitepaper",
        "publisher": "Samsung",
        "published_date": "2026.02",
        "quote": "MBCFET with horizontal nanosheets allows custom channel width tuning per standard cell, providing 30% higher performance and 50% power reduction over 3nm FinFET.",
        "section_context": "Section 1.2 Device Scaling & Short Channel Control, p.4",
        "relevance_score": 0.96,
        "external_url": "https://semiconductor.samsung.com/foundry/process-technology/gaa",
        "url_label": "삼성전자 파운드리 GAA 원문 ➔",
        "credibility_tier": "Tier 1 (공식 제조사)",
        "referenced_concepts": [
            {"conceptId": "concept-gaa-nanosheet", "name": "2nm GAA 나노시트"}
        ]
    },
    {
        "id": "E-06",
        "source_name": "SEMI E98 Standard for Advanced Process Control (APC) and FDC",
        "source_type": "international_standard",
        "publisher": "SEMI",
        "published_date": "2025.08",
        "quote": "SEMI E98 specifies fault detection and classification models, requiring sub-100ms multi-sensor anomaly detection to prevent catastrophic yield excursion across 300mm wafer runs.",
        "section_context": "Standard Specification Clause 5.3 Real-Time Streaming",
        "relevance_score": 0.94,
        "external_url": "https://www.semi.org/standards/e98",
        "url_label": "SEMI E98 표준 전문 ➔",
        "credibility_tier": "Tier 2 (국제 표준)",
        "referenced_concepts": [
            {"conceptId": "concept-fdc-apc", "name": "FDC 실시간 결함 감지 및 이상 진단"}
        ]
    }
]

# ==============================================================================
# 2. 온톨로지 핵심 개념 엔티티 (Concept)
# ==============================================================================
CONCEPTS: List[Dict[str, Any]] = [
    {
        "id": "concept-tcb",
        "title": "열압착 본딩",
        "eng_name": "Thermal Compression Bonding (TCB)",
        "aliases": ["TCB", "열압착", "TC-NCF", "열압착 접합"],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징",
        "scale_level": 3,
        "scale_name": "Scale 3: 모듈·패키징 공정 (100㎛~10mm)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 김수석 (첨단패키징연구팀)",
        "summary": "다이(Die)와 기판 사이에 고체 비전도성 필름(NCF)을 개재한 후 정밀한 온도와 압력을 가해 마이크로 범프를 용융 접합하는 첨단 패키징 공정.",
        "purpose": "HBM 및 3D IC 적층 시 인접 다이 간의 전기적 연결 신뢰성을 확보하고 마이크로 범프 간 단락을 방지함.",
        "principles": [
            {
                "step": 1,
                "title": "다이 정렬 및 NCF 가압 (Die Alignment & Pre-Force)",
                "content": "하부 다이 위에 마이크로 범프가 형성된 상부 다이를 0.5㎛ 정밀도로 광학 정렬 후 100~150N 하중을 인가함.",
                "formula": "F_{\\text{bonding}} = P_{\\text{tool}} \\times A_{\\text{die}}"
            },
            {
                "step": 2,
                "title": "급속 승온 및 솔더 용융 (Thermal Ramp & Reflow)",
                "content": "가압 상태에서 260~300℃로 급속 승온하여 Sn-Ag 마이크로 범프를 용융시키고 금속간 화합물(IMC)을 형성함.",
                "formula": "T(t) = T_0 + \\beta t \\quad (\\beta \\approx 100^\\circ\\text{C/s})"
            },
            {
                "step": 3,
                "title": "냉각 및 수지 경화 (Cooling & Resin Curing)",
                "content": "압력을 유지한 채 급속 냉각하여 솔더 조인트를 고화시키고 NCF 수지를 경화하여 접합을 완료함."
            }
        ],
        "limitations": [
            {
                "title": "16단 고적층 시 누적 열팽창(CTE) 미스매치 및 휨 (Warpage)",
                "description": "적층 단수가 높아질수록 반복적인 열압착 사이클에 의해 실리콘과 NCF 간의 CTE 불일치 응력이 누적되어 칩 가장자리 휨 발생.",
                "evidenceIds": ["E-02"]
            },
            {
                "title": "생산성(TAT) 및 기포(Void) 잔류 리스크",
                "description": "칩을 1장씩 순차 가압·가열(Pick-and-Place)하므로 스택당 공정 시간이 길며, 필름 사이 공기 배출이 어려워 미세 보이드 발생 위험 존재.",
                "evidenceIds": ["E-01", "E-02"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-packaging", "name": "첨단 패키징 공정"}],
            "part_of": [{"id": "concept-hbm-assembly", "name": "HBM 적층 조립 모듈"}],
            "next_step": [{"id": "concept-pkg-inspection", "name": "패키지 신뢰성 X-ray 검사"}],
            "alternative_to": [
                {
                    "targetId": "concept-mrmuf",
                    "targetName": "MR-MUF 공정",
                    "commonGoal": "16단 초고단 HBM 방열 극대화 및 수율 확보"
                }
            ]
        }
    },
    {
        "id": "concept-mrmuf",
        "title": "MR-MUF",
        "eng_name": "Mass Reflow Molded Underfill (MR-MUF)",
        "aliases": ["MR-MUF", "매스 리플로우 몰디드 언더필", "어드밴스드 MR-MUF"],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징",
        "scale_level": 3,
        "scale_name": "Scale 3: 모듈·패키징 공정 (100㎛~10mm)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 김수석 (첨단패키징연구팀)",
        "summary": "다단 적층된 다이를 오븐에서 일괄 리플로우(Mass Reflow) 접합한 후, 액상 에폭시 몰딩 컴파운드(EMC)를 고압 주입하여 다이 간 틈새와 외곽을 동시에 충진·방열하는 차세대 패키징 공정.",
        "purpose": "HBM 다단 적층 시 공정 시간(TAT)을 획기적으로 줄이고, 고열전도성 액상 에폭시를 통해 휨 방지 및 방열 특성을 극대화함.",
        "principles": [
            {
                "step": 1,
                "title": "일괄 솔더 리플로우 (Mass Reflow)",
                "content": "가압 툴 없이 12~16단 다이를 정렬하여 리플로우 오븐에서 전체 솔더 범프를 동시에 일괄 접합함."
            },
            {
                "step": 2,
                "title": "액상 EMC 진공 고압 주입 (Molded Underfill Injection)",
                "content": "마이크로 간극 사이에 고열전도성 필러가 함유된 액상 에폭시를 진공 상태에서 고압으로 밀어 넣어 보이드 없이 완벽 충진함.",
                "formula": "Q = \\frac{\\pi r^4 \\Delta P}{8 \\eta L}"
            }
        ],
        "limitations": [
            {
                "title": "마이크로 간극 사이 필러 트래핑 (Filler Jamming)",
                "description": "범프 피치가 10㎛ 이하로 극미세화될 경우 액상 EMC 내부의 실리카 필러 입자가 간극에 걸려 미충진 결함 유발 가능.",
                "evidenceIds": ["E-01"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-packaging", "name": "첨단 패키징 공정"}],
            "part_of": [{"id": "concept-hbm-assembly", "name": "HBM 적층 조립 모듈"}],
            "next_step": [{"id": "concept-pkg-inspection", "name": "패키지 신뢰성 X-ray 검사"}],
            "alternative_to": [
                {
                    "targetId": "concept-tcb",
                    "targetName": "열압착 본딩 (TCB)",
                    "commonGoal": "16단 초고단 HBM 방열 극대화 및 수율 확보"
                }
            ]
        }
    },
    {
        "id": "concept-dry-etch",
        "title": "플라즈마 건식 식각",
        "eng_name": "Plasma Dry Etching",
        "aliases": ["RIE", "건식 식각", "플라즈마 에칭"],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정 (1㎛~100㎛)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 박수석 (식각공정개발팀)",
        "summary": "진공 챔버에 공정 가스를 주입하고 고주파(RF) 전력을 인가하여 생성된 반응성 라디칼과 가속된 이온의 물리·화학적 시너지 반응으로 박막을 수직 패턴화하는 핵심 제조 공정.",
        "purpose": "미세 반도체 패턴에서 수평 언더컷 없이 높은 이방성(Anisotropy)과 수직 프로파일을 달성함.",
        "principles": [
            {
                "step": 1,
                "title": "플라즈마 방전 및 라디칼 생성 (Discharge & Dissociation)",
                "content": "RF 전력으로 가스 분자(CF4, CHF3 등)를 해리시켜 반응성 중성 라디칼과 양이온 플라즈마 생성.",
                "formula": "e^- + CF_4 \\rightarrow CF_3^+ + F^* + 2e^-"
            },
            {
                "step": 2,
                "title": "이온 가속 및 바이어스 충돌 (Ion Bombardment)",
                "content": "웨이퍼 척에 인가된 음의 셀프 바이어스 전압에 의해 양이온이 수직 가속되어 박막 표면의 결합을 끊고 활성화함."
            }
        ],
        "limitations": [
            {
                "title": "300단 초고종횡비(HARC) 홀에서의 보잉(Bowing) 및 틸팅(Tilting)",
                "description": "깊은 트렌치 내부로 들어갈수록 이온 산란과 측벽 충돌로 인해 홀 중간이 볼록해지는 보잉 결함 발생.",
                "evidenceIds": ["E-03"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-etch", "name": "식각 공정"}],
            "part_of": [{"id": "concept-etch-chamber", "name": "플라즈마 챔버 모듈"}],
            "next_step": [{"id": "concept-pr-ash", "name": "PR 애싱 및 세정"}],
            "alternative_to": [
                {
                    "targetId": "concept-cryo-etch",
                    "targetName": "극저온 식각 (Cryo Etch)",
                    "commonGoal": "300단 낸드 채널 홀 수직도 및 식각 속도 극대화"
                }
            ]
        }
    },
    {
        "id": "concept-cryo-etch",
        "title": "극저온 건식 식각",
        "eng_name": "Cryogenic Dry Etching",
        "aliases": ["Cryo Etch", "극저온 에칭", "램리서치 극저온 공정"],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정 (1㎛~100㎛)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 박수석 (식각공정개발팀)",
        "summary": "웨이퍼 척 온도를 -60℃~-80℃의 극저온으로 냉각하여 식각 측벽에 보호 반응막을 물리적으로 동결시킴으로써 홀 보잉을 차단하고 초고속 수직 식각을 구현하는 기술.",
        "purpose": "3D 낸드 300단 이상의 초고종횡비(Aspect Ratio 100:1) 채널 홀을 상온 식각 대비 2배 이상의 속도로 무결성 수직 가공함.",
        "principles": [
            {
                "step": 1,
                "title": "측벽 부동태막 동결 (Sidewall Freezing)",
                "content": "극저온 상태에서 화학 반응물이 측벽에 즉시 응축·동결되어 라디칼에 의한 측면 식각을 원천 차단함.",
                "formula": "k_{\\text{desorption}} \\propto \\exp\\left(-\\frac{E_a}{k_B T}\\right)"
            }
        ],
        "limitations": [
            {
                "title": "극저온 냉각 척 신뢰성 및 전력 소비",
                "description": "챔버 내부를 상시 극저온으로 유지하기 위한 칠러 설비 전력 소모 및 결로 방지 공정 제어 복잡도 증가.",
                "evidenceIds": ["E-03"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-etch", "name": "식각 공정"}],
            "part_of": [{"id": "concept-etch-chamber", "name": "극저온 칠러 챔버"}],
            "next_step": [{"id": "concept-pr-ash", "name": "PR 애싱 및 세정"}],
            "alternative_to": [
                {
                    "targetId": "concept-dry-etch",
                    "targetName": "플라즈마 건식 식각",
                    "commonGoal": "300단 낸드 채널 홀 수직도 및 식각 속도 극대화"
                }
            ]
        }
    },
    {
        "id": "concept-high-na-euv",
        "title": "High-NA EUV 노광",
        "eng_name": "High-NA EUV Lithography (0.55NA)",
        "aliases": ["High-NA", "0.55NA EUV", "ASML EXE Platform"],
        "domain_facet": "unit_process",
        "process_category": "노광 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정 (13.5nm~1㎛)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 정수석 (광학물리연구팀)",
        "summary": "13.5nm EUV 광원에 개구수(NA)를 기존 0.33에서 0.55로 확대한 아나모픽(Anamorphic) 반사 광학계를 적용하여 8nm 이하의 단일 노광 해상도를 달성하는 첨단 리소그래피 시스템.",
        "purpose": "2nm 이하 초미세 반도체 회로를 멀티 패터닝 없이 단일 노광(Single Exposure)으로 인쇄하여 공정 복잡도와 원가를 절감함.",
        "principles": [
            {
                "step": 1,
                "title": "레일리 해상도 한계 확장 (Rayleigh Scaling)",
                "content": "개구수 NA를 0.55로 확대하여 회로 인쇄 한계 선폭(CD)을 8nm 수준으로 미세화함.",
                "formula": "\\text{CD} = k_1 \\frac{\\lambda}{\\text{NA}} = 0.35 \\times \\frac{13.5}{0.55} \\approx 8.59\\text{nm}"
            },
            {
                "step": 2,
                "title": "아나모픽 비대칭 광학계 (Anamorphic Magnification)",
                "content": "마스크 섀도잉 방지를 위해 X축 4배, Y축 8배로 비대칭 축소 투영하여 포토마스크 패턴 각도를 완화함."
            }
        ],
        "limitations": [
            {
                "title": "초점 심도(DOF) 급감 및 스캔 필드 반토막",
                "description": "NA 증가로 인해 초점 심도(DOF)가 제곱으로 감소하여 펠리클 평탄도 및 극초박막 레지스트 제약 발생. Y축 8배 확대로 필드 크기가 절반으로 감소.",
                "evidenceIds": ["E-04"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-lithography", "name": "노광 공정"}],
            "part_of": [{"id": "concept-asml-scanner", "name": "ASML EXE 스캐너"}],
            "next_step": [{"id": "concept-dry-etch", "name": "플라즈마 건식 식각"}],
            "alternative_to": [
                {
                    "targetId": "concept-euv-standard",
                    "targetName": "표준 0.33NA EUV",
                    "commonGoal": "2nm 로직 회로 패턴 인쇄"
                }
            ]
        }
    },
    {
        "id": "concept-gaa-nanosheet",
        "title": "2nm GAA 나노시트",
        "eng_name": "Gate-All-Around Nanosheet FET (MBCFET)",
        "aliases": ["GAA", "나노시트", "MBCFET", "2nm 트랜지스터"],
        "domain_facet": "device",
        "process_category": "소자 구조",
        "scale_level": 2,
        "scale_name": "Scale 2: 소자 물성 구조 (1nm~100nm)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 이수석 (소자물리팀)",
        "summary": "게이트가 나노시트 채널 4면을 완전히 둘러싸 누설 전류를 완벽히 통제하고, 나노시트 폭을 가변 조절하여 성능과 전력 효율을 극대화한 3차원 트랜지스터 구조.",
        "purpose": "FinFET의 3면 게이트 정전 제어 한계를 극복하고 2nm 이하 초미세 노드에서 단채널 효과(Short Channel Effect)를 차단함.",
        "principles": [
            {
                "step": 1,
                "title": "4면 풀 서라운드 게이트 정전 제어 (All-Around Electrostatic Control)",
                "content": "나노시트 상하좌우 전체에 산화막과 메탈 게이트를 형성하여 드레인 전압에 의한 소스 전위 장벽 강하(DIBL)를 억제함."
            }
        ],
        "limitations": [
            {
                "title": "내부 스페이서(Inner Spacer) 형성 및 기생 커패시턴스",
                "description": "나노시트 사이의 SiGe 희생층 선택 식각 정밀도 저하 시 게이트와 소스/드레인 간 기생 용량 증가로 고주파 특성 저하 위험.",
                "evidenceIds": ["E-05"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-transistor", "name": "전계효과 트랜지스터 (FET)"}],
            "part_of": [{"id": "concept-logic-cell", "name": "표준 로직 셀"}],
            "next_step": [{"id": "concept-bspdn", "name": "후면 전력 공급망 (BSPDN)"}]
        }
    },
    {
        "id": "concept-fdc-apc",
        "title": "FDC 실시간 결함 감지 및 이상 진단",
        "eng_name": "Fault Detection and Classification (FDC / APC)",
        "aliases": ["FDC", "APC", "이상감지", "고장 진단 및 분류"],
        "domain_facet": "operations",
        "process_category": "팹 운영 및 수율",
        "scale_level": 4,
        "scale_name": "Scale 4: 장비 및 라인 시스템 (1m~100m)",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "Dr. 최수석 (수율분석운영팀)",
        "summary": "반도체 장비 내부의 수백 개 센서 시계열 데이터를 100ms 단위로 실시간 수집하여 공정 드리프트 및 부품 이상을 사전 감지·분류하고 레시피를 자동 보정하는 스마트 팹 핵심 시스템.",
        "purpose": "웨이퍼 배치 손실(Scrap)을 원천 방지하고 설비 가동률(OEE)과 수율 안정성을 극대화함.",
        "principles": [
            {
                "step": 1,
                "title": "다변량 통계 이상 감지 (Multivariate Statistical Monitoring)",
                "content": "PCA 및 오토인코더 모델을 통해 RF 파워, 압력, 가스 유량 간의 상관관계 붕괴(T^2, SPE 통계량)를 0.1초 내 감지함.",
                "formula": "T^2 = \\mathbf{x}^T \\mathbf{S}^{-1} \\mathbf{x} > T^2_{\\alpha}"
            }
        ],
        "limitations": [
            {
                "title": "정상 변동과 결함 이상 간의 오경보(False Alarm)",
                "description": "타겟 챔버의 주기적 클리닝 직후 베이스라인 이동 시 정상 공정을 결함으로 오판하여 불필요한 라인 인터록 발생 가능.",
                "evidenceIds": ["E-06"]
            }
        ],
        "relations": {
            "is_a": [{"id": "concept-smart-fab", "name": "스마트 팹 운영 제어"}],
            "part_of": [{"id": "concept-mes-system", "name": "팹 통합 MES 시스템"}],
            "next_step": [{"id": "concept-auto-recipe-patch", "name": "레시피 자동 보상 파라미터 패치"}]
        }
    },
    # 그래프 시각화 및 캔버스 연결용 보조 노드들
    {
        "id": "param-bonding-pressure",
        "title": "본딩 인가 압력/하중",
        "eng_name": "Bonding Force / Tool Pressure",
        "aliases": ["가압력", "본딩 하중", "Tool Pressure"],
        "domain_facet": "unit_process",
        "process_category": "공정 파라미터",
        "scale_level": 3,
        "scale_name": "Scale 3: 공정 제어 수치",
        "version": "v1.2",
        "status": "adopted",
        "summary": "열압착 본딩 툴이 다이에 인가하는 기계적 수직 하중 (단위: N 또는 MPa).",
        "purpose": "범프 간 긴밀한 접촉 및 NCF 필름 수지의 유동 배출 제어.",
        "principles": [],
        "limitations": [],
        "relations": {}
    },
    {
        "id": "defect-micro-bridging",
        "title": "마이크로 범프 단락 (Short)",
        "eng_name": "Micro-Bump Solder Bridging Defect",
        "aliases": ["범프 단락", "솔더 브릿징", "NCF 누출 단락"],
        "domain_facet": "device",
        "process_category": "패키징 결함 모드",
        "scale_level": 2,
        "scale_name": "Scale 2: 미세 결함 물성",
        "version": "v1.2",
        "status": "adopted",
        "summary": "용융된 솔더가 인접 범프로 흘러넘쳐 인접 전기 회로를 전기적으로 쇼트시키는 치명적 패키징 불량.",
        "purpose": "원인 규명 및 방지 기준 확립.",
        "principles": [],
        "limitations": [],
        "relations": {}
    }
]

# ==============================================================================
# 3. 온톨로지 인과 엣지 물리 테이블 (CausalEdge)
#    (Neo4j 단일화 및 보상 파라미터 Compensating Parameters 완비)
# ==============================================================================
CAUSAL_EDGES: List[Dict[str, Any]] = [
    {
        "source_concept_id": "param-bonding-pressure",
        "target_concept_id": "defect-micro-bridging",
        "relation_type": "causes_defect",
        "polarity": "+",
        "weight": 0.92,
        "mechanism_label": "180N 초과 가압 시 NCF 수지 측방 유출 및 용융 솔더 압출 단락 유발",
        "compensating_params": {
            "parameter": "초음파 인가 시간 (Ultrasonic Scrubbing Time)",
            "compensation_formula": "Δt = +120ms / -15N",
            "tradeoff_cost": "택트타임(TAT) 8.5% 증가"
        },
        "evidence_id": "E-02"
    },
    {
        "source_concept_id": "concept-tcb",
        "target_concept_id": "concept-mrmuf",
        "relation_type": "alternative_to",
        "polarity": "tradeoff",
        "weight": 0.88,
        "mechanism_label": "16단 고적층 생산성(TAT) 및 방열 한계로 인한 공정 대안 관계",
        "compensating_params": {
            "parameter": "몰딩 온도 및 진공 압력",
            "compensation_formula": "T_mold = 175℃ ± 2℃, P_disp = 0.45MPa",
            "tradeoff_cost": "액상 언더필 주입 시간 12초 소요"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "concept-dry-etch",
        "target_concept_id": "concept-cryo-etch",
        "relation_type": "alternative_to",
        "polarity": "tradeoff",
        "weight": 0.95,
        "mechanism_label": "300단 이상 초고종횡비 낸드 채널 홀 보잉 결함 해소를 위한 극저온 공정 대체",
        "compensating_params": {
            "parameter": "웨이퍼 척 극저온 헬륨 냉각 압력",
            "compensation_formula": "T_chuck = -60℃, P_He = 2.4kPa",
            "tradeoff_cost": "칠러 전력 소비량 35% 증가 및 챔버 웜업 주기 단축"
        },
        "evidence_id": "E-03"
    },
    {
        "source_concept_id": "concept-high-na-euv",
        "target_concept_id": "concept-gaa-nanosheet",
        "relation_type": "causes",
        "polarity": "+",
        "weight": 0.90,
        "mechanism_label": "8nm 단일 노광 해상도 달성을 통해 2nm GAA 나노시트 게이트 패턴 직접 패터닝 가능",
        "compensating_params": {
            "parameter": "초점 심도(DOF) 감소에 따른 레지스트 박막화",
            "compensation_formula": "t_PR = 20nm ± 1nm",
            "tradeoff_cost": "하드마스크 식각 선택비 확보 요구 조건 심화"
        },
        "evidence_id": "E-04"
    },
    {
        "source_concept_id": "concept-fdc-apc",
        "target_concept_id": "concept-dry-etch",
        "relation_type": "part_of",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "플라즈마 임피던스 및 가스 유량 실시간 모니터링을 통한 챔버 이상 방어",
        "compensating_params": {
            "parameter": "RF 바이어스 전력 자동 보정",
            "compensation_formula": "ΔP_RF = +5W per 0.1s drift",
            "tradeoff_cost": "플라즈마 안정화 지연시간 2초 발생"
        },
        "evidence_id": "E-06"
    }
]

# ==============================================================================
# 4. 적응형 Level 3 실무 사례 엔티티 (PerspectiveCase)
# ==============================================================================
PERSPECTIVE_CASES: List[Dict[str, Any]] = [
    {
        "id": "case-tcb-hbm3e",
        "concept_id": "concept-tcb",
        "perspective_id": "hbm3e_advanced",
        "perspective_title": "A사 HBM3E 16단 TCB 본딩 양산 기준",
        "perspective_badge": "양산 적용 관점",
        "management_code": "RCP-TCB-HBM3E-16H",
        "context_narrative": "16단 적층 HBM3E 라인에서 다이 두께 30㎛ 미세화에 따른 휨(Warpage)을 제어하고 범프 크랙을 차단하기 위한 현장 전용 열압착 가압 프로파일입니다.",
        "specifications": [
            {"label": "피크 본딩 온도", "value": "285", "unit": "℃", "criteria": "±3℃", "role": "peak_temp", "evidenceId": "E-02"},
            {"label": "인가 본딩 압력", "value": "145", "unit": "N", "criteria": "140N ~ 150N", "role": "bonding_force", "evidenceId": "E-02"},
            {"label": "초음파 인가 시간", "value": "350", "unit": "ms", "criteria": "330ms ~ 370ms", "role": "ultrasonic_time", "evidenceId": "E-02"},
            {"label": "NCF 필름 두께", "value": "25", "unit": "㎛", "criteria": "24㎛ ~ 26㎛", "role": "film_thickness", "evidenceId": "E-02"}
        ],
        "caution": "⚠️ 본딩 압력이 160N을 초과할 경우 NCF 수지 측방 유출로 인해 솔더 쇼트가 급증하므로 가압력 보상 상한선(150N)을 엄격히 준수할 것.",
        "evidence_id": "E-02"
    },
    {
        "id": "case-mrmuf-hbm3e",
        "concept_id": "concept-mrmuf",
        "perspective_id": "hbm3e_advanced",
        "perspective_title": "SK하이닉스 16단 HBM3E 어드밴스드 MR-MUF 기준",
        "perspective_badge": "방열 극대화 관점",
        "management_code": "SKH-MRMUF-HBM3E-16H",
        "context_narrative": "16단 고적층 HBM3E의 발열을 해소하고 접합 보이드 제로를 달성하기 위해 고열전도성 액상 에폭시와 일괄 리플로우를 적용한 공정 기준입니다.",
        "specifications": [
            {"label": "리플로우 피크 온도", "value": "260", "unit": "℃", "criteria": "255℃ ~ 265℃", "role": "reflow_temp", "evidenceId": "E-01"},
            {"label": "액상 몰딩 주입 압력", "value": "0.45", "unit": "MPa", "criteria": "0.40 ~ 0.50MPa", "role": "injection_pressure", "evidenceId": "E-01"},
            {"label": "방열 열전도도", "value": "2.5", "unit": "W/m·K", "criteria": "≥ 2.2 W/m·K", "role": "thermal_conductivity", "evidenceId": "E-01"}
        ],
        "caution": "⚠️ 다이 간격이 10㎛ 이하로 협소하므로 실리카 필러 뭉침에 의한 미충진(Void) 발생 여부를 음향현미경(C-SAM)으로 상시 전수 검사할 것.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-cryo-harc",
        "concept_id": "concept-cryo-etch",
        "perspective_id": "nand_high_stack",
        "perspective_title": "3D 낸드 300단 이상 채널 홀 초고속 극저온 가공 기준",
        "perspective_badge": "수율 극대화 관점",
        "management_code": "HARC-CRYO-300L",
        "context_narrative": "300단 초고층 낸드에서 홀 깊이 10㎛ 이상의 고종횡비 채널을 보잉 없이 수직 식각하기 위한 극저온 챔버 세팅 기준입니다.",
        "specifications": [
            {"label": "척 냉각 온도", "value": "-60", "unit": "℃", "criteria": "±2℃", "role": "chuck_temp", "evidenceId": "E-03"},
            {"label": "식각 속도", "value": "2.4", "unit": "㎛/min", "criteria": "≥ 2.0 ㎛/min", "role": "etch_rate", "evidenceId": "E-03"},
            {"label": "상하 프로파일 수직도", "value": "99.8", "unit": "%", "criteria": "≥ 99.5%", "role": "profile_verticality", "evidenceId": "E-03"}
        ],
        "caution": "⚠️ 챔버 진공 파괴 후 대기 노출 시 척 표면 결로 위험이 있으므로 질소 퍼지 및 승온 프로토콜(Warm-up)을 필수 이행할 것.",
        "evidence_id": "E-03"
    }
]

# ==============================================================================
# 5. 기술 대안 비교 세션 엔티티 (ComparisonSession)
#    (3-Step 스냅샷, 꼬리질문 이력 deep_dive_history, 보상 파라미터 튜닝 이력)
# ==============================================================================
COMPARISON_SESSIONS: List[Dict[str, Any]] = [
    {
        "id": "sess-20261016-001",
        "user_id": "EMP-91823",
        "title": "HBM3E 방열 및 조립성 대안: SK하이닉스 MR-MUF vs 마이크론 TC-NCF",
        "is_pinned": True,
        "folder_id": "folder-hbm-packaging",
        "query": "HBM 16단 고적층 시 방열과 휨 제어를 위해 MR-MUF와 TC-NCF 중 어느 쪽이 적합한가?",
        "context_params": {
            "targetA": "SK하이닉스 (MR-MUF)",
            "targetB": "마이크론 (TC-NCF)",
            "domain": "첨단 패키징",
            "releaseVersion": "v1.2",
            "constraints": [
                {"param": "본딩 가압력", "operator": "<=", "limitValue": "150N", "source": "fab_profile"}
            ]
        },
        "snapshots": [
            {
                "step": 1,
                "title": "공학 질문 확정",
                "branchData": {
                    "question": "16단 HBM3E 열 분산 및 다이 휨 방지 대안",
                    "branches": [
                        {"id": "b1", "label": "방열 우선: 액상 에폭시 일괄 주입 (MR-MUF)"},
                        {"id": "b2", "label": "정밀 정렬 우선: 필름 개재 개별 열압착 (TC-NCF)"},
                        {"id": "b3", "label": "하이브리드 본딩 (Cu-Cu 직접 접합)"}
                    ]
                }
            },
            {
                "step": 2,
                "title": "양산 조건 매핑",
                "conditions": {
                    "dieCount": 16,
                    "targetThickness": "720㎛",
                    "maxPressureLimit": "150N"
                },
                "constraintGaps": [
                    {
                        "param": "본딩 가압력",
                        "standardValue": "180N (기존 NCF 기준)",
                        "constraintValue": "150N (현장 장비 한계)",
                        "riskNote": "접촉 계면 압력 부족으로 솔더 젖음성 불량 및 보이드 잔류 위험"
                    }
                ],
                "tuningHistory": [
                    {
                        "userPrompt": "장비 한계로 가압력을 150N 이상 못 줄 때 어떻게 보상해야 하지?",
                        "advisorRecommendation": {
                            "compensationA": {
                                "param": "초음파 인가 시간",
                                "value": "350ms (+120ms)",
                                "tradeoff": "택트타임(TAT) 8.5% 증가하지만 보이드 제로 달성"
                            },
                            "compensationB": {
                                "param": "본딩 피크 온도",
                                "value": "295℃ (+10℃)",
                                "tradeoff": "열충격 위험 있으나 NCF 점도 급감으로 유동성 확보"
                            }
                        }
                    }
                ]
            },
            {
                "step": 3,
                "title": "다차원 비교 분석 완료",
                "matrix": [
                    {
                        "axis": "열전도도 및 방열 특성",
                        "axisCategory": "thermal",
                        "categoryLabel": "🔬 열·물성 특성",
                        "valA": "2.5 W/m·K (액상 에폭시 방열 우수)",
                        "valB": "1.0 W/m·K (고체 NCF 필름 열 저항)",
                        "evidenceA": "E-01",
                        "evidenceB": "E-02",
                        "isGap": False
                    },
                    {
                        "axis": "16단 적층 시 휨(Warpage) 및 보이드",
                        "axisCategory": "defects",
                        "categoryLabel": "⚠️ 결함·신뢰성 리스크",
                        "valA": "보이드 제로, 휨 응력 분산 우수",
                        "valB": "필름 공기 포집 보이드 잔류 위험 (3.2%)",
                        "evidenceA": "E-01",
                        "evidenceB": "E-02",
                        "isGap": False
                    },
                    {
                        "axis": "조립 생산성 (TAT / Throughput)",
                        "axisCategory": "fab",
                        "categoryLabel": "🏭 팹 양산성 & TAT",
                        "valA": "일괄 리플로우로 16단 1회 동시 접합 (고생산성)",
                        "valB": "16단 개별 순차 열압착 (공정 시간 3배)",
                        "evidenceA": "E-01",
                        "evidenceB": "E-02",
                        "isGap": False
                    }
                ],
                "aiCausalNote": "16단 고적층 환경에서는 액상 몰딩을 통해 방열 성능과 일괄 리플로우 생산성을 확보한 MR-MUF가 공학적으로 우세함.",
                "deepDiveHistory": [
                    {
                        "query": "TC-NCF에서 가압력 누적 시 휨이 발생하는 물리적 인과 메커니즘은 무엇인가?",
                        "causalPath": ["가압력 누적", "CTE 미스매치", "전단응력", "다이 휨"],
                        "explanation": "NCF의 열팽창계수(CTE, 약 30ppm/K)와 실리콘 다이(2.6ppm/K) 간의 10배 이상 물성 차이로 인해, 냉각 시 계면 전단응력이 중심부로 집중되면서 칩 최외곽이 위로 들리는 Warpage 현상이 유발됩니다.",
                        "timestamp": "2026-10-16T10:15:00Z"
                    }
                ]
            }
        ],
        "exported_review_id": "rev-20261016-001"
    }
]

# ==============================================================================
# 6. 지식 거버넌스 및 검토·승인 티켓 엔티티 (ReviewTicket)
#    (2-Segment, 도메인 필수 override_reason 사유 반영)
# ==============================================================================
REVIEW_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "rev-20261016-001",
        "concept_id": "concept-tcb",
        "concept_title": "열압착 본딩 (TCB)",
        "title": "TCB 16단 적층 시 145N 가압 조건 및 시간 보상 파라미터 추가",
        "review_type": "파라미터 수정",
        "author": "Dr. 김수석 (수율분석팀)",
        "department": "수율분석팀",
        "submitted_at": "2026-10-16T11:30:00Z",
        "status": "pending",  # 🌟 pending ➔ [Tab 3] 대기 중 탭
        "source_session_id": "sess-20261016-001",
        "origin_type": "comparison_studio",
        "current_version": "v1.2",
        "target_version": "v1.3",
        "current_content": "### 인가 본딩 압력\n- 기준값: 180N (초기 8단 규격)",
        "ai_merged_draft": "### 인가 본딩 압력\n- 16단 고적층 개정값: 145N (허용범위 140N ~ 150N)\n- 보상 파라미터: 초음파 인가 시간 350ms (+120ms 보상 연동)",
        "human_edits": None,
        "structured_patches": {
            "specsPatch": [
                {"label": "인가 본딩 압력", "oldValue": "180N", "newValue": "145N", "role": "bonding_force"},
                {"label": "초음파 인가 시간", "oldValue": "230ms", "newValue": "350ms", "role": "ultrasonic_time"}
            ]
        },
        "integrity_report": {
            "evidenceMatchRate": 1.0,
            "hasOntologyConflict": False,
            "impactScopeCount": 2,
            "validationDetails": "삼성전자 신뢰성 보고서(E-02) 인용문과 100% 일치하며 인과 충돌 없음."
        },
        "directive_history": [],
        # 🌟 도메인 필수 용어: 사유 / overrideReason (금지어 '전문가 사유' 엄격 배제)
        "override_reason": "파일럿 팹 라인 16단 실측 결과 145N에서 솔더 쇼트율이 0.02% 이하로 급감함을 공인 검증하여 개정 상신함.",
        "ticket_version": 1
    },
    {
        "id": "rev-20261015-002",
        "concept_id": "concept-cryo-etch",
        "concept_title": "극저온 식각 (Cryo Etch)",
        "title": "극저온 식각 하드웨어 척 온도 사양 v1.2 공식 채택",
        "review_type": "신규 개념",
        "author": "Dr. 박수석 (식각공정개발팀)",
        "department": "식각공정개발팀",
        "submitted_at": "2026-10-15T09:00:00Z",
        "status": "approved",  # 🌟 approved ➔ [Tab 3] 승인 완료 이력 탭
        "source_session_id": None,
        "origin_type": "literature_search",
        "current_version": "v1.1",
        "target_version": "v1.2",
        "current_content": "신규 등록 개념 초안",
        "ai_merged_draft": "척 온도 -60℃ 조건 및 HARC 채널 식각 속도 2.4㎛/min 공식 반영본",
        "human_edits": "척 온도 -60℃ 조건 및 HARC 채널 식각 속도 2.4㎛/min 공식 반영본",
        "integrity_report": {
            "evidenceMatchRate": 0.98,
            "hasOntologyConflict": False,
            "impactScopeCount": 1,
            "validationDetails": "Lam Research 백서(E-03) 대조 검증 완료."
        },
        "directive_history": [],
        # 🌟 도메인 필수 용어: 사유 / overrideReason (금지어 '전문가 사유' 엄격 배제)
        "override_reason": "Lam Research 공인 백서 실측 수치와 100% 일치 확인 및 300단 낸드 개발 라인 적용 승인.",
        "approved_at": "2026-10-15T18:00:00Z",
        "approved_by": "Dr. 최수석 (총괄수석연구원)",
        "applied_concept_version": "v1.2",
        "ticket_version": 2
    }
]

# ==============================================================================
# 7. 프론트엔드 전체 개념 및 실무 사례 전수 동기화 병합 (Extended Concepts)
# ==============================================================================
try:
    from backend.seeds.extended_concepts import (
        EXTENDED_CONCEPTS,
        EXTENDED_PERSPECTIVES,
        EXTENDED_CAUSAL_EDGES,
        EXTENDED_EVIDENCES
    )

    # Concept 병합
    existing_c_ids = {c["id"] for c in CONCEPTS}
    for c in EXTENDED_CONCEPTS:
        if c["id"] not in existing_c_ids:
            CONCEPTS.append(c)
            existing_c_ids.add(c["id"])

    # Evidence 병합
    existing_e_ids = {e["id"] for e in EVIDENCE_SOURCES}
    for e in EXTENDED_EVIDENCES:
        if e["id"] not in existing_e_ids:
            EVIDENCE_SOURCES.append(e)
            existing_e_ids.add(e["id"])

    # PerspectiveCase 병합
    existing_p_ids = {p["id"] for p in PERSPECTIVE_CASES}
    for p in EXTENDED_PERSPECTIVES:
        if p["id"] not in existing_p_ids:
            PERSPECTIVE_CASES.append(p)
            existing_p_ids.add(p["id"])

    # CausalEdge 병합
    existing_edge_keys = {
        (edge["source_concept_id"], edge["target_concept_id"], edge["relation_type"])
        for edge in CAUSAL_EDGES
    }
    for edge in EXTENDED_CAUSAL_EDGES:
        ek = (edge["source_concept_id"], edge["target_concept_id"], edge["relation_type"])
        if ek not in existing_edge_keys:
            CAUSAL_EDGES.append(edge)
            existing_edge_keys.add(ek)
except ImportError:
    pass

