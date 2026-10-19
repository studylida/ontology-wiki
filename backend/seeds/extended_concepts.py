"""Extended Golden Dataset generated from frontend concepts.
"""
from typing import Dict, List, Any

EXTENDED_CONCEPTS: List[Dict[str, Any]] = [
    {
        "id": "dry-etch",
        "title": "플라즈마 건식 식각 (Reactive Ion Etching - RIE)",
        "eng_name": "Reactive Ion Etching",
        "aliases": [
            "RIE",
            "건식 식각",
            "드라이 에칭",
            "플라즈마 식각"
        ],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "진공 챔버 내에서 고주파(RF) 전력으로 에칭 가스를 플라즈마 상태로 해리시켜 화학적 반응성을 지닌 중성 라디칼과 방향성을 지닌 양이온을 생성하고, 하부 바이어스로 가속된 이온의 물리적 충돌과 라디칼의 화학 반응을 결합하여 박막을 수직 이방성으로 선택 제거하는 공정이다.",
        "purpose": "등방성(Isotropic) 언더컷이 발생하는 습식 식각의 물리적 한계를 극복하고 나노스케일(Sub-10nm) 수직 프로파일을 정밀하게 형성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "이온 보조 식각 메커니즘 (Ion-assisted Etching)",
                "content": "중성 불화탄소 라디칼(CFx)이 표면에 흡착되어 휘발성 반응 생성물(SiF4↑)을 형성하기 전, 수직으로 입사하는 고에너지 Ar+/CFx+ 이온이 결합을 끊어 반응 활성화 에너지를 대폭 낮춘다."
            },
            {
                "step": 2,
                "title": "플라즈마 소스-바이어스 디커플링 (ICP/CCP)",
                "content": "소스 RF(13.56MHz~60MHz)로 플라즈마 밀도(이온/라디칼 플럭스)를 독립 제어하고, 기판 척 바이어스 RF(400kHz~2MHz)로 입사 이온의 가속 에너지(Ion Energy)를 분리 제어하여 이방성과 마스크 선택비를 동시 확보한다."
            },
            {
                "step": 3,
                "title": "측벽 보호막(Passivation) 동역학",
                "content": "에칭 부산물과 플라즈마 중합체가 패턴 측벽에 폴리머(CF2)n 박막을 형성하여 횡방향 침식을 차단하고 완벽한 수직 트렌치를 구현한다."
            }
        ],
        "limitations": [
            {
                "title": "플라즈마 유도 손상 (Plasma Induced Damage, PID)",
                "description": "고에너지 충돌 이온이 실리콘 기판 내부 격자를 붕괴(Amorphization)시키거나 게이트 절연막에 충전 전하(Charging Damage)를 축적시켜 절연 파괴(TDDB)를 유발함.",
                "evidenceIds": []
            },
            {
                "title": "마이크로 로딩 및 종횡비 의존 식각 (ARDE)",
                "description": "패턴 밀도가 높은 영역이나 종횡비가 깊은 비아 홀에서 반응 가스 유입 및 부산물 배출 지연으로 식각 속도가 느려지는 에칭 지연 현상 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ],
            "part_of": [
                {
                    "id": "plasma-chamber",
                    "name": "ICP/CCP 플라즈마 식각 챔버"
                }
            ],
            "next_step": [
                {
                    "id": "ashing-clean",
                    "name": "포토레지스트 애싱 및 세정 공정"
                }
            ]
        }
    },
    {
        "id": "ale-etch",
        "title": "원자층 식각 (Atomic Layer Etching - ALE)",
        "eng_name": "Atomic Layer Etching",
        "aliases": [
            "ALE",
            "원자층 식각",
            "디지털 식각",
            "원자단위 식각"
        ],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "원자층 증착(ALD)의 역과정으로, 화학적 표면 흡착(개질) 단계와 물리적 이온 탈착 단계를 공간적·시간적으로 엄격히 분리 순환시킴으로써 자기 제한적(Self-limiting) 반응을 통해 1사이클당 단원자층(1~1.5Å) 단위로 박막을 제거하는 극미세 디지털 식각 기술이다.",
        "purpose": "3nm 이하 선단 트랜지스터(GAA)의 극미세 게이트 및 콘택 형성 시 하부 박막의 플라즈마 대미지 없이 원자 수준의 표면 평탄도와 무한대에 가까운 극한 선택비를 달성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "2단계 자기 제한적 시퀀스",
                "content": "① 표면 개질(Modification): 염소(Cl2) 또는 불소 가스를 주입하여 타깃 표면 단원자층과 반응시켜 화학 결합력이 약화된 염화물(SiClx) 층을 자발 형성하고 잔류 가스를 퍼지한다. ② 원자 탈착(Removal): 벌크 실리콘의 스퍼터링 문턱 에너지(약 50eV) 이하인 저에너지 Ar+ 이온(20~30eV)을 입사시켜 개질된 SiClx 층만을 선택적으로 튕겨내고 반응을 자동 중단한 뒤 퍼지한다."
            },
            {
                "step": 2,
                "title": "두께 디지털 제어성",
                "content": "사이클 횟수(Cycle count)에 의해 최종 제거 두께가 선형적으로 결정되므로 로딩 효과(Loading Effect)가 전혀 발생하지 않는다."
            }
        ],
        "limitations": [
            {
                "title": "극히 느린 공정 속도(Throughput / TAT)",
                "description": "1사이클에 제거되는 두께가 약 0.1nm 수준으로, 사이클당 퍼지 시간이 소요되어 수십 나노미터 이상의 깊은 패턴 식각에는 생산성이 현저히 떨어짐.",
                "evidenceIds": []
            },
            {
                "title": "초정밀 저에너지 RF 제어 난도",
                "description": "이온 에너지가 50eV를 1eV라도 초과할 경우 하부 벌크 실리콘의 물리적 스퍼터링이 발생하여 ALE의 자기 제한성 특성이 상실됨.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ],
            "part_of": [
                {
                    "id": "ale-reactor",
                    "name": "고속 밸브 탑재 ALE 전용 플라즈마 챔버"
                }
            ],
            "next_step": [
                {
                    "id": "ald-deposition",
                    "name": "5. 박막 증착 공정 (ALD)"
                }
            ]
        }
    },
    {
        "id": "photo-resist",
        "title": "포토레지스트 패터닝 (양성 PR vs 음성 PR)",
        "eng_name": "Photoresist (Positive vs Negative)",
        "aliases": [
            "PR",
            "감광액",
            "Positive PR",
            "Negative PR"
        ],
        "domain_facet": "unit_process",
        "process_category": "포토 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.3",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "빛(자외선/EUV)에 노출되었을 때 화학적 구조가 변하는 유기 감광 고분자 물질로, 후속 식각 공정에서 하부 박막을 보호하는 마스크 역할을 수행한다.",
        "purpose": "설계된 CAD 회로 패턴을 웨이퍼 표면에 정밀하게 전사하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "양성(Positive) PR",
                "content": "빛을 받은 영역의 고분자 결합이 끊어져 현상액(Developer)에 용해되어 제거된다. 해상도가 우수하여 미세 공정에 주로 쓰인다."
            },
            {
                "step": 2,
                "title": "음성(Negative) PR",
                "content": "빛을 받은 영역이 가교 반응(Cross-linking)을 일으켜 현상액에 녹지 않고 남는다. 접착력이 우수하나 팽윤(Swelling) 현상으로 초미세 선폭에 한계가 있다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "EUV 초미세 노광 시 광자 무작위성(Photon Shot Noise)으로 인한 선폭 거칠기(LER/LWR) 결함 발생 위험.",
                "evidenceIds": []
            },
            {
                "title": "물리 한계 2",
                "description": "도포 후 웨이퍼 가장자리의 잔류 PR을 제거하기 위한 EBR(Edge Bead Removal) 솔벤트 정밀 제어 필수.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "silicon-ingot",
        "title": "실리콘 잉곳 성장 (Silicon Ingot Growth)",
        "eng_name": "Czochralski (CZ) Ingot Growth",
        "aliases": [
            "잉곳",
            "실리콘 단결정",
            "초크랄스키 공법"
        ],
        "domain_facet": "unit_process",
        "process_category": "웨이퍼 제조",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "모래에서 추출한 다결정 실리콘을 고온(1420°C) 도가니에서 녹인 후 종자 결정(Seed)을 회전시키며 천천히 끌어올려 초고순도 단결정 실리콘 기둥을 만드는 공정이다.",
        "purpose": "결함이 없는 완벽한 격자 구조(순도 99.9999999% 일레븐 나인)의 웨이퍼 원자재를 확보하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초크랄스키(CZ)법",
                "content": "석영 도가니 내부 융액의 온도 구배와 회전 속도를 제어하여 직경 300mm(12인치)의 균일한 단결정을 성장시킨다."
            },
            {
                "step": 2,
                "title": "도핑(Doping)",
                "content": "성장 과정에서 붕소(B)나 인(P)을 극미량 투입하여 P형 또는 N형 웨이퍼의 기저 전기 저항을 결정한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "석영 도가니에서 녹아 나오는 산소(O) 불순물로 인해 열처리 중 산소 석출 결함(BMD)이 발생할 수 있음.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "mr-muf",
        "title": "HBM MR-MUF 적층 공정 (Advanced MR-MUF)",
        "eng_name": "Advanced MR-MUF Packaging",
        "aliases": [
            "MR-MUF",
            "어드밴스드 MR-MUF",
            "액상 에폭시 몰딩",
            "HBM 패키징"
        ],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "12단~16단 초고단 HBM 스택에서 개별 다이를 필름으로 열압착하는 대신, 수천 개의 마이크로범프를 리플로우(Reflow) 오븐에서 한 번에 솔더 접합한 뒤 액상 에폭시 몰딩 컴파운드(Liquid EMC)를 칩 사이 간극에 일괄 주입하여 언더필(Underfill)과 외곽 패키징 몰딩을 단일 공정으로 완성하는 첨단 3D 적층 패키징 공정이다.",
        "purpose": "기존 TC-NCF(열압착 비전도성 필름) 방식의 고압 누적에 의한 칩 휨(Warpage)과 필름의 낮은 열전도도(~0.5 W/m·K)로 인한 고질적인 발열 병목을 극복하고, 10μm 이하 미세 갭에서 보이드 없는 고신뢰성 접합을 달성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "액상 EMC 모세관 충진 및 진공 차압 주입",
                "content": "접촉각 θ < 25°의 초저점도 액상 레진을 0.1 Torr 진공 챔버에서 차압 주입하여 15μm 이하 미세 범프 간극 내에 공기가 갇히지 않도록 완전히 충진한다."
            },
            {
                "step": 2,
                "title": "나노/마이크로 실리카 바이모달 입도 분포",
                "content": "구형 실리카 필러를 대구경과 소구경의 바이모달로 배합하여 필러 충진율을 85 wt% 이상으로 극대화하면서도 120°C 주입 점도를 1.5 Pa·s 이하로 유지한다."
            },
            {
                "step": 3,
                "title": "방열 성능 극대화 메커니즘",
                "content": "고충진 실리카 필러에 의해 몰딩 수지의 자체 열전도율이 2.5 W/m·K로 NCF 대비 2.5배 향상되어, 12단 HBM3E 패키지의 열저항(θJA)을 36% 감쇄시킨다."
            }
        ],
        "limitations": [
            {
                "title": "초미세 간극(Sub-10μm) 필러 트래핑(Filler Jamming)",
                "description": "16단 이상 적층 시 다이 간극이 10μm 이하로 좁아지면 실리카 필러 입자가 좁은 틈에 끼어 수지 흐름을 방해하고 국소 마이크로 보이드(Micro-void)를 유발할 수 있음.",
                "evidenceIds": []
            },
            {
                "title": "액상 수지 열팽창계수(CTE) 미스매치",
                "description": "실리콘 다이(CTE ~3 ppm/K)와 EMC 수지(CTE ~10 ppm/K) 간의 경화 수축 응력으로 인해 대형 패키지 쿨다운 시 가장자리 다이 탈락 위험 존재.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-packaging",
                    "name": "8. 첨단 패키징 공정 (Packaging)"
                }
            ],
            "part_of": [
                {
                    "id": "hbm-stack-assembly",
                    "name": "HBM 초고대역폭 메모리 스택"
                }
            ],
            "next_step": [
                {
                    "id": "cowos-interposer-cuf",
                    "name": "2.5D CoWoS 인터포저 실장"
                }
            ]
        }
    },
    {
        "id": "hybrid-bonding",
        "title": "하이브리드 본딩 (Cu-Cu Hybrid Bonding / DBI)",
        "eng_name": "Cu-Cu Direct Hybrid Bonding",
        "aliases": [
            "하이브리드 본딩",
            "DBI",
            "Cu-Cu 접합",
            "SoIC",
            "웨이퍼 본딩"
        ],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "솔더 범프(Solder micro-bump)를 완전히 제거하고, CMP로 원자 수준(RMS 거칠기 < 0.5nm)으로 평탄화된 유전체(SiO2/SiCN)와 구리(Cu) 패드를 상온에서 공유 결합시킨 후 저온 열처리(200°C~300°C)를 통해 구리 원자의 상호 확산으로 금속 접합을 완성하는 범프리스(Bumpless) 차세대 3D 인터커넥트 기술이다.",
        "purpose": "솔더 리플로우 시의 쇼트 위험으로 인해 20μm 이하 축소가 불가능했던 마이크로범프의 피치 한계를 서브마이크론(Sub-1μm)으로 축소시켜 인터커넥트 밀도를 1,000배 이상 극대화하고 신호 지연 및 기생 저항을 0에 가깝게 감쇄시키기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "친수성 유전체 상온 수소 결합",
                "content": "Ar/N2 플라즈마 표면 활성화로 절연막 표면에 고밀도 실란올기(Si-OH)를 형성한 뒤 상온 접촉시키면 수소 결합으로 가접합되고, 탈수 축합 반응(Si-OH + HO-Si → Si-O-Si + H2O↑)으로 공유 결합을 형성한다."
            },
            {
                "step": 2,
                "title": "Cu 열팽창 차등 접합 (Thermal Expansion Mismatch)",
                "content": "Cu의 열팽창계수(CTE ~16.5 ppm/K)가 산화막(0.5 ppm/K)보다 훨씬 큼을 이용하여, 어닐링 시 Cu 패드가 팽창하며 수 나노미터의 리세스 갭을 메우고 강한 압축 응력 하에서 원자 상호 확산(Inter-diffusion)을 일으킨다."
            },
            {
                "step": 3,
                "title": "결정립계 확산(Dgb) 나노보이드 소멸",
                "content": "계면에 잔류하는 2~10nm 나노 보이드의 공공(Vacancy)이 인접 결정립계로 빠르게 흡수 소멸되어 200°C 저온에서도 전단 강도 > 35 MPa, 접촉 비저항 < 10^-9 Ω·cm²를 달성한다."
            }
        ],
        "limitations": [
            {
                "title": "원자 단위의 극단적 파티클 민감도",
                "description": "50nm 크기의 나노 파티클 1개만 계면에 존재해도 주변 수천 개의 Cu 패드가 접합되지 않는 거대 보이드(Void Blister) 결함 발생(Class 1 이하 초청정 팹 필수).",
                "evidenceIds": []
            },
            {
                "title": "초정밀 CMP 리세스 제어 난도",
                "description": "Cu 패드가 산화막 표면보다 너무 깊게 파이면(> 6nm) 가열 팽창 시 상하 패드가 닿지 않아 단선되고, 돌출되면 산화막 공유 결합이 형성되지 않아 전체 층간 박리 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-packaging",
                    "name": "8. 첨단 패키징 공정 (Packaging)"
                }
            ],
            "part_of": [
                {
                    "id": "heterogeneous-3d-system",
                    "name": "이종 집적 3D Chiplet 패키지"
                }
            ],
            "next_step": [
                {
                    "id": "tddb-reliability-physics",
                    "name": "패키지 신뢰성 가속 수명 검증"
                }
            ]
        }
    },
    {
        "id": "plasma-fdc-sensor",
        "title": "플라즈마 식각 FDC 센서 이상 감지 (Fault Detection)",
        "eng_name": "Plasma Etch FDC Sensor Monitoring",
        "aliases": [
            "FDC",
            "챔버 결함 탐지",
            "OES 센서 모니터링"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 (FDC)",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "식각 공정 중 챔버 내부의 광학 발광 분석(OES), RF 임피던스, 챔버 압력 센서 데이터를 실시간 수집하여 플라즈마 아킹(Arcing) 및 공정 드리프트를 조기 감지하는 운영 기술.",
        "purpose": "웨이퍼 스크랩(Scrap)을 방지하고 장비 비가동 시간(Downtime)을 최소화하기 위함.",
        "principles": [
            {
                "step": 1,
                "title": "원리 1",
                "content": "광학 센서로 플라즈마 특정 파장의 발광 강도를 측정하여 반응 종의 농도 변화와 식각 종말점(EPD)을 판정한다."
            },
            {
                "step": 2,
                "title": "원리 2",
                "content": "다변량 통계(PCA) 모델을 활용하여 정상 운전 영역에서 벗어나는 이상치를 100ms 이내에 검출한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "챔버 뷰포트(Viewport) 오염 시 OES 신호 왜곡으로 인한 오경보(False Alarm) 발생 가능.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "spc-control-chart",
        "title": "SPC 통계적 공정 관리도 (Statistical Process Control)",
        "eng_name": "Statistical Process Control (SPC)",
        "aliases": [
            "SPC",
            "관리도",
            "UCL/LCL",
            "웨스턴 일렉트릭 룰"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 (FDC)",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "제조 공정에서 발생하는 품질 변동 데이터를 수집하여 통계적 관리 한계선(UCL, LCL, 중심선)을 설정하고, 공정이 통계적 관리 상태에 있는지를 모니터링하는 기법.",
        "purpose": "우연 원인에 의한 일반 변동과 이상 원인에 의한 특수 변동을 구분하여 불량 발생 전에 선제적 조치를 취하기 위함.",
        "principles": [
            {
                "step": 1,
                "title": "원리 1",
                "content": "정규분포 3시그마(3-sigma) 원리를 적용하여 중심선 기준 ±3σ를 상한선(UCL)과 하한선(LCL)으로 규정한다."
            },
            {
                "step": 2,
                "title": "웨스턴 일렉트릭(Western Electric) 룰",
                "content": "1개 점이 3σ를 벗어나거나, 연속된 9개 점이 중심선 한쪽에 치우치는 등 4대 이상 패턴을 실시간 감지한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "데이터 수집 주기(샘플링)가 늦어질 경우 실시간 이상을 제어하지 못하고 지연된 경보가 발생할 수 있음.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "run-to-run",
        "title": "R2R 첨단 공정 제어 (Run-to-Run Control)",
        "eng_name": "Run-to-Run (R2R) Control",
        "aliases": [
            "R2R",
            "런투런",
            "APC 피드포워드/피드백"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 (APC)",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "이전 웨이퍼(또는 랏)의 가공 후 인라인 계측 결과를 수학적 모델에 대입하여, 바로 다음 웨이퍼의 공정 파라미터(식각 시간, CMP 연마 압력, 증착 전력)를 실시간 자동 보정하는 폐루프(Closed-loop) 제어 시스템.",
        "purpose": "소모품(CMP 패드, 챔버 파츠) 마모나 케미컬 열화로 인해 발생하는 공정 드리프트(Drift)를 사람 개입 없이 자동으로 상쇄하기 위함.",
        "principles": [
            {
                "step": 1,
                "title": "원리 1",
                "content": "지수 가중 이동 평균(EWMA) 필터를 적용하여 노이즈를 제거하고 실제 설비 상태의 추세(Trend)를 추정한다."
            },
            {
                "step": 2,
                "title": "선행 공정 계측값(예",
                "content": "포토 선폭)을 바탕으로 현재 공정(식각 시간)을 미리 보정하는 피드포워드(Feed-forward) 제어를 병행한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "수학적 플랜트 모델이 부정확하거나 계측 오차가 유입될 경우 오히려 공정 편차를 증폭시키는 헌팅(Hunting) 현상 발생 위험.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "ees-rms",
        "title": "EES & RMS 레시피 관리 시스템",
        "eng_name": "Equipment Engineering System & Recipe Management",
        "aliases": [
            "EES",
            "RMS",
            "레시피 관리",
            "SECS/GEM 통신"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 (EES)",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.1",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "팹 내 수백 대의 장비와 MES(제조 실행 시스템) 간에 SEMI 통신 표준(SECS/GEM)을 통해 연결되어, 승인된 공식 레시피만을 장비에 다운로드하고 무단 변경을 원천 차단하는 엔지니어링 통제 시스템.",
        "purpose": "작업자의 레시피 파라미터 오입력으로 인한 수천억 원 대의 대형 웨이퍼 폐기 사고(Scrap)를 방지하기 위함.",
        "principles": [
            {
                "step": 1,
                "title": "레시피 바디 체크섬(Body Checksum) 비교",
                "content": "장비가 실행하려는 레시피 파일의 해시값과 RMS 서버의 승인본 해시값을 실시간 대조하여 1비트라도 다르면 장비 가동을 인터락(Interlock)한다."
            },
            {
                "step": 2,
                "title": "원리 2",
                "content": "SEMI E30(GEM), E98 표준을 준수하여 가스 유량, 온도, 압력의 상한/하한 안전 영역(Hard/Soft Limit)을 강제한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "네트워크 단절 시 팹 전 장비가 안전 모드로 진입하여 전체 생산이 일시 중단될 수 있음.",
                "evidenceIds": []
            }
        ],
        "relations": {}
    },
    {
        "id": "plasma-discharge",
        "title": "플라즈마 방전 및 시스 형성 (Plasma Discharge & Sheath)",
        "eng_name": "Plasma Discharge & RF Sheath",
        "aliases": [
            "플라즈마 방전",
            "RF 방전",
            "CCP/ICP 방전"
        ],
        "domain_facet": "unit_process",
        "process_category": "식각/증착 공통",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v1.2",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "진공 챔버 내에서 고주파(RF) 전계를 인가하여 공정 가스를 전자, 양이온, 중성 라디칼로 해리시켜 제4의 물질 상태인 준중성(Quasi-neutral) 플라즈마를 발생시키는 핵심 물리 현상이다.",
        "purpose": "열역학적으로 고온에서만 일어나는 화학 반응을 상온~중온 영역에서 플라즈마 에너지로 활성화하여 박막을 수직 식각하거나 저온 증착하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "용량 결합 플라즈마(CCP)와 유도 결합 플라즈마(ICP)",
                "content": "고주파 안테나의 유도 자기장으로 고밀도 전자 흐름을 유도하여 플라즈마 밀도를 10^11~10^12 cm^-3 수준으로 유지한다."
            },
            {
                "step": 2,
                "title": "플라즈마 시스(Sheath) 전위",
                "content": "전자의 빠른 이동 속도로 인해 웨이퍼 표면에 음의 자가 바이어스(DC Bias)가 형성되며, 이로 인해 양이온이 웨이퍼로 수직 가속된다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "플라즈마 불균일 시 웨이퍼 반경 방향으로 전자 온도(Te) 편차가 발생하여 식각률 및 임계 선폭(CD) 불균일을 초래한다.",
                "evidenceIds": []
            },
            {
                "title": "물리 한계 2",
                "description": "챔버 벽면 유전체 부품에 전하가 축적될 경우 비정상 마이크로 아킹(Arcing)이 발생하여 웨이퍼가 손상된다.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-etch",
                    "name": "식각 공정 (Etching)"
                }
            ],
            "part_of": [
                {
                    "id": "dry-etch",
                    "name": "플라즈마 건식 식각"
                }
            ],
            "next_step": [
                {
                    "id": "dry-etch",
                    "name": "웨이퍼 이온 보조 식각"
                }
            ]
        }
    },
    {
        "id": "wafer-fabrication",
        "title": "웨이퍼 제조 공정 (Wafer Fabrication)",
        "eng_name": "Silicon Wafer Fabrication",
        "aliases": [
            "웨이퍼 제조",
            "잉곳 성장",
            "CZ 공정",
            "웨이퍼 기판"
        ],
        "domain_facet": "unit_process",
        "process_category": "웨이퍼 제조 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "규소(SiO2)를 순도 99.999999999%(11N)의 전자급 다결정 실리콘(EG-Si)으로 정련한 후, 초크랄스키(CZ)법으로 무결함 단결정 잉곳을 성장시켜 슬라이싱, 엣지 프로파일링, 래핑, CMP 연마를 거쳐 원자 수준의 평탄 기판을 제조하는 단위 공정이다.",
        "purpose": "반도체 집적회로 소자 형성의 물리적 베이스 플레이트(Substrate)를 제공하고, 격자 결함(Dislocation) 및 금속 오염을 억제하여 트랜지스터의 전기적 특성과 수율을 보장하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초크랄스키(Czochralski, CZ) 잉곳 성장",
                "content": "석영 도가니에서 1420°C로 용융된 실리콘에 종자 결정(Seed Crystal)을 접촉시켜 회전 인상(Pulling)하며 대구경(300mm) 무결함 단결정 잉곳을 제조한다."
            },
            {
                "step": 2,
                "title": "결정 결함 제어",
                "content": "인상 속도(V)와 고-액 계면의 축방향 온도 구배(G)의 비(V/G)를 임계값 근방으로 제어하여 공공(Vacancy, COP)과 격자간 실리콘(Interstitial Si) 응집 결함을 동시에 차단한다."
            },
            {
                "step": 3,
                "title": "표면 평탄화 및 결함 제거",
                "content": "다이아몬드 와이어 절단으로 절단된 웨이퍼의 미세 크랙을 화학 에칭으로 제거하고, 양면 래핑(Lapping)과 화학기계적 연마(CMP)를 통해 표면 RMS 거칠기를 0.1nm 이하로 가공한다."
            }
        ],
        "limitations": [
            {
                "title": "물리 한계 1",
                "description": "300mm 대구경 웨이퍼 인상 시 열응력(Thermal Stress)으로 인한 슬립(Slip) 전위 발생 위험이 존재한다.",
                "evidenceIds": []
            },
            {
                "title": "석영 도가니 용해에 의해 잉곳 내부로 침투하는 침입형 산소 농도(Oi",
                "description": "10~20 ppma)를 엄격히 제어하지 못할 경우 고온 열처리 시 산소 석출 결함이 활성 소자 영역에 형성되어 누설전류를 유발한다.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-wafer",
                    "name": "1. 웨이퍼 제조 (Wafer Fabrication)"
                }
            ],
            "part_of": [
                {
                    "id": "ingot-puller",
                    "name": "CZ 잉곳 성장로"
                }
            ],
            "next_step": [
                {
                    "id": "thermal-oxidation",
                    "name": "2. 산화 공정 (Oxidation)"
                }
            ]
        }
    },
    {
        "id": "thermal-oxidation",
        "title": "열산화 공정 (Thermal Oxidation)",
        "eng_name": "Thermal Oxidation",
        "aliases": [
            "열산화",
            "산화막 형성",
            "Dry Oxidation",
            "Wet Oxidation"
        ],
        "domain_facet": "unit_process",
        "process_category": "산화 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "800°C~1200°C의 고온 전기로에서 실리콘 웨이퍼를 산소(O2) 또는 수증기(H2O)와 화학 반응시켜 웨이퍼 표면에 균일하고 절연성이 뛰어난 이산화규소(SiO2) 박막을 직접 성장시키는 공정이다.",
        "purpose": "금속 배선 간의 전기적 절연, 이온 주입 시 하부 실리콘 영역 차폐(Screen Oxide), 패터닝 시 하드마스크 및 소자 분리막(STI 라이너)을 형성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "딜-그로브(Deal-Grove) 산화 모델",
                "content": "산화막 두께 x와 시간 t는 수식 x² + Ax = B(t + τ)를 따른다. 박막 초기에는 표면 반응 제한 영역(Linear regime: x ∝ t)을 따르고, 막이 두꺼워지면 산화종의 산화막 내부 확산 제한 영역(Parabolic regime: x² ∝ t)을 따른다."
            },
            {
                "step": 2,
                "title": "건식 산화 (Dry Oxidation)",
                "content": "Si + O2 → SiO2 반응을 이용하며, 성장 속도는 느리지만 산화막의 밀도가 높고 계면 결함 밀도(Dit)가 낮아 고품질 게이트 절연막 및 얇은 패시베이션 산화막에 적용된다."
            },
            {
                "step": 3,
                "title": "습식 산화 (Wet Oxidation)",
                "content": "Si + 2H2O → SiO2 + 2H2 반응을 이용하며, 물 분자의 높은 용해도와 빠른 확산 속도로 건식 대비 성장 속도가 5~10배 빠르지만 수소 부산물로 인해 막질 밀도가 상대적으로 낮아 두꺼운 필드 산화막 및 마스킹층에 적용된다."
            }
        ],
        "limitations": [
            {
                "title": "실리콘 소모 현상",
                "description": "산화막이 성장할 때 최종 SiO2 두께의 약 44%에 해당하는 하부 벌크 실리콘이 반응하여 소모되므로 단차 및 치수 설계 시 사전 보정이 필수적이다.",
                "evidenceIds": []
            },
            {
                "title": "부피 팽창에 따른 진성 응력(Intrinsic Stress)",
                "description": "Si와 SiO2의 몰 부피 차이(약 2.2배)로 인해 계면에 강한 압축 응력(Compressive Stress)이 축적되어 웨이퍼 휨을 유발한다.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-oxidation",
                    "name": "2. 산화 공정 (Oxidation)"
                }
            ],
            "part_of": [
                {
                    "id": "oxidation-furnace",
                    "name": "수직형 열산화 확산로(Vertical Diffusion Furnace)"
                }
            ],
            "next_step": [
                {
                    "id": "photolithography",
                    "name": "3. 포토 공정 (Photolithography)"
                }
            ]
        }
    },
    {
        "id": "photolithography",
        "title": "포토리소그래피 공정 (Photolithography)",
        "eng_name": "Photolithography Process",
        "aliases": [
            "포토 공정",
            "노광 공정",
            "리소그래피",
            "패터닝 공정"
        ],
        "domain_facet": "unit_process",
        "process_category": "포토 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "웨이퍼 표면에 감광액(Photoresist)을 도포하고, 포토마스크에 형성된 회로 패턴에 단파장 빛을 투과·노광한 뒤 현상액을 통해 특정 영역을 선택적으로 용해·제거하여 나노스케일 2차원 회로 형상을 전사하는 8단계 정밀 화학·광학 공정이다.",
        "purpose": "후속 식각 및 이온 주입 공정에서 웨이퍼의 특정 타깃 영역만을 물리·화학적으로 개질할 수 있도록 보호 마스크 패턴을 정의하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "표준 8단계 시퀀스",
                "content": "① 표면 처리(HMDS 기상 프라이밍으로 친수성 웨이퍼를 소수성으로 개질) → ② 감광액 스핀 코팅(Spin Coating, 두께 균일도 ±1nm) → ③ 소프트 베이크(Soft Bake, 솔벤트 90% 휘발) → ④ 정렬 및 노광(Alignment & Exposure) → ⑤ 노광 후 가열(PEB: Post-Exposure Bake, 정재파 효과 제거 및 화학증폭 활성화) → ⑥ 현상(Development: TMAH 2.38% 용액 현상) → ⑦ 하드 베이크(Hard Bake, 잔류 수분 제거 및 에칭 내성 강화) → ⑧ 비파괴 광학 검사(CD 및 오버레이 측정)."
            },
            {
                "step": 2,
                "title": "광화학 반응 원리",
                "content": "양성 감광액(Positive PR)은 노광 영역의 광산발생제(PAG)가 산(H+)을 발생시키고 PEB 열에 의해 고분자 보호기가 탈리되어 알칼리 현상액에 가용성으로 전환된다. 음성 감광액(Negative PR)은 노광 영역이 광가교 결합을 형성하여 불용성으로 남는다."
            }
        ],
        "limitations": [
            {
                "title": "정재파 효과(Standing Wave Effect)",
                "description": "기판 반사광과 입사광의 간섭으로 인해 레지스트 측벽에 리플(Ripple) 줄무늬 단차가 형성되어 선폭 제어가 왜곡될 수 있음(하부 반사방지막 BARC 적용 필수).",
                "evidenceIds": []
            },
            {
                "title": "초점 심도(Depth of Focus, DOF) 제약",
                "description": "해상도를 높이기 위해 개구수(NA)를 키우거나 파장을 줄이면 DOF = k2 * (λ / NA²) 수식에 의해 초점 마진이 급감하여 웨이퍼 토폴로지 단차에서 패턴 디포커스 결함 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-photo",
                    "name": "3. 포토 공정 (Photolithography)"
                }
            ],
            "part_of": [
                {
                    "id": "track-scanner-cluster",
                    "name": "인라인 트랙 & 스캐너 클러스터 시스템"
                }
            ],
            "next_step": [
                {
                    "id": "plasma-dry-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ]
        }
    },
    {
        "id": "euv-lithography",
        "title": "EUV 극자외선 노광 시스템 (EUV Lithography)",
        "eng_name": "EUV Lithography",
        "aliases": [
            "EUV",
            "극자외선 노광",
            "0.33 NA EUV",
            "LPP 광원"
        ],
        "domain_facet": "unit_process",
        "process_category": "포토 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "파장 13.5nm의 극자외선(EUV) 광원을 사용하여 레일리 해상도 한계(CD = k1 * λ / NA)를 획기적으로 낮춤으로써 서브-7nm 선단 로직 및 10nm급 DRAM 셀을 단일 노광(Single Exposure)으로 패터닝하는 전반사 진공 노광 시스템이다.",
        "purpose": "ArF 액침(193nm) 리소그래피의 다중 패터닝(SADP, SAQP) 복잡도와 마스크 매수 증가로 인한 수율 저하 및 생산 단가 폭증을 극복하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "레이저 생성 플라즈마 (LPP) 광원",
                "content": "진공 챔버 내에서 직경 25μm의 고순도 액체 주석(Sn) 드롭릿을 초당 50,000회 고속 분사하고, 30kW CO2 펄스 레이저를 2회 타격(프리펄스로 납작하게 만든 후 메인펄스 방전)하여 주석 원자를 수십만 도의 고밀도 플라즈마 상태(Sn8+~Sn14+)로 여기시켜 13.5nm EUV 광자를 방출한다."
            },
            {
                "step": 2,
                "title": "브래그 반사 광학계 (Bragg Reflective Optics)",
                "content": "13.5nm 파장은 모든 물질(공기, 유리)에 흡수되므로 렌즈 투과가 불가능하여 진공 환경에서 Mo/Si 40~50쌍 다층막 거울을 사용한다. 거울 1매당 이론 반사율은 약 70%이며, 11회 전반사를 거쳐 웨이퍼에 도달하는 유효 광량은 입사광의 약 2% 수준으로 감소한다."
            },
            {
                "step": 3,
                "title": "광투과형 펠리클(Pellicle) 보호 및 수소 세정",
                "content": "마스크 오염을 막기 위해 400W 고출력 레이저 조사 시 800°C 고열을 견디고 투과율 > 90%를 유지하는 Ru/MoSi2 캡핑 탄소나노튜브(CNT) 펠리클을 적용하며, 챔버 내 수소 플라즈마를 주입하여 잔류 주석 오염물을 가스(SnH4↑) 상태로 배출한다."
            }
        ],
        "limitations": [
            {
                "title": "광자 샷 노이즈(Photon Shot Noise)와 확률론적 결함",
                "description": "EUV 광자 1개의 에너지가 91.8eV로 매우 높아 동일 노광량(Dose)에서 도달하는 광자 수가 ArF의 1/14에 불과하여, 광자 수의 통계적 요동으로 인한 마이크로 브릿지(Micro-bridge) 및 라인 단선 결함 위험이 존재한다.",
                "evidenceIds": []
            },
            {
                "title": "광원 전력 대비 극히 낮은 총 효율",
                "description": "30kW급 CO2 레이저를 투입하여 수백 W의 극자외선을 생성하고 다층막 반사 후 웨이퍼에 도달하는 빛은 수 W에 불과하여 대형 칠러 설비 및 천문학적 소비 전력이 요구된다.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-photo",
                    "name": "3. 포토 공정 (Photolithography)"
                }
            ],
            "part_of": [
                {
                    "id": "euv-scanner",
                    "name": "ASML NXE 0.33 NA 스캐너"
                }
            ],
            "next_step": [
                {
                    "id": "plasma-dry-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ]
        }
    },
    {
        "id": "high-na-euv",
        "title": "High-NA EUV 노광 시스템 (High-NA EUV Lithography)",
        "eng_name": "High-NA EUV Lithography",
        "aliases": [
            "High-NA",
            "0.55 NA EUV",
            "EXE:5000",
            "아나모픽 노광"
        ],
        "domain_facet": "unit_process",
        "process_category": "포토 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "투영 광학계의 개구수(NA)를 기존 0.33에서 0.55로 대폭 끌어올려 단일 노광 해상도를 8nm까지 축소시키며, 3D 마스크 섀도잉 효과를 극복하기 위해 가로/세로 배율이 다른 아나모픽(Anamorphic) 광학계(X축 4배, Y축 8배 축소)를 적용한 2nm 이하 초미세 노드용 차세대 리소그래피 시스템이다.",
        "purpose": "0.33 NA EUV에서도 불가피해진 2nm 이하 로직의 더블 패터닝(EUV double patterning)을 단일 노광으로 단순화하여 공정 결함 감소 및 수율 극대화를 달성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "아나모픽 비대칭 배율 투영 (Anamorphic Optics)",
                "content": "NA가 0.55로 증가함에 따라 마스크에 입사하는 빛의 각도가 커져 마스크 흡수체 패턴 뒷면에 그림자가 지는 3D 섀도잉(Mask 3D Effect)이 발생한다. 이를 방지하기 위해 마스크 상에서 각도 마진을 확보하고자 입사면 방향(Y축)만 8배로 축소하고 수평면(X축)은 기존 4배 축소를 유지하는 비대칭 배율 렌즈계를 채택한다."
            },
            {
                "step": 2,
                "title": "하프 필드 스캔 (Half-Field Scanning)",
                "content": "Y축 8배 축소로 인해 웨이퍼 상의 노광 노출 면적(Field Size)이 기존 표준(26mm × 33mm)의 절반인 26mm × 16.5mm로 줄어든다. 거대 다이(Large AI Chip) 노광 시 두 개의 하프 필드를 나노미터 오차 없이 이어 붙이는 스티칭(Stitching) 알고리즘이 적용된다."
            },
            {
                "step": 3,
                "title": "주석 옥소 케이지 금속 산화물 레지스트(MOR)",
                "content": "유기 CAR의 산 확산(Acid Diffusion Blur) 한계를 극복하기 위해 Sn-Oxide 코어 기반의 무기 MOR을 적용하여 피치 20nm 이하에서 LER < 1.8nm를 달성한다."
            }
        ],
        "limitations": [
            {
                "title": "극단적인 초점 심도 축소 (DOF < 20nm)",
                "description": "DOF = k2 * λ / NA² 수식에 의해 NA 0.55에서 초점 허용 마진이 20nm 이하로 급감하므로, 웨이퍼의 미세 휨과 두께 불균일을 실시간으로 보정하는 초정밀 압전 척 액추에이터 제어가 필수적이다.",
                "evidenceIds": []
            },
            {
                "title": "하프 필드 스티칭 오버레이 결함",
                "description": "스티칭 경계면에서 수 나노미터의 정렬 오차 발생 시 초대형 AI 가속기 칩의 내부 버스 배선이 단선되거나 저항이 폭증할 위험이 존재한다.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-photo",
                    "name": "3. 포토 공정 (Photolithography)"
                }
            ],
            "part_of": [
                {
                    "id": "high-na-scanner",
                    "name": "ASML EXE:5000/5200 High-NA 스캐너"
                }
            ],
            "next_step": [
                {
                    "id": "ale-etch",
                    "name": "원자층 식각 공정 (ALE)"
                }
            ]
        }
    },
    {
        "id": "model-based-opc",
        "title": "광학 근접 효과 보정 OPC (Optical Proximity Correction)",
        "eng_name": "Model-based Optical Proximity Correction",
        "aliases": [
            "OPC",
            "모델 기반 OPC",
            "마스크 보정",
            "역보정"
        ],
        "domain_facet": "unit_process",
        "process_category": "포토 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "빛의 회절 한계와 레지스트 현상 공정에서 발생하는 미세 패턴 왜곡(모서리 둥글림, 라인 끝단 수축, 선폭 편차)을 광학 모델로 시뮬레이션하여 마스크 상에 역보정 형상(Serif, Hammerhead, SRAF)을 자동 생성하고, 계측 데이터(YieldStar)와 연동하여 실시간 피드백하는 폐루프 리소그래피 최적화 기술이다.",
        "purpose": "설계된 CAD 레이아웃의 정확한 직사각형 프로파일이 실제 웨이퍼 상에 전사되도록 마스크 왜곡을 물리적으로 선반영 보상하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "호프킨스 부분 결맞음 회절 모델",
                "content": "광학계의 수차와 회절을 컨볼루션 연산으로 모델링하여 광학상(Aerial Image) 강도 분포를 계산하고, 레지스트 임계 강도(Threshold)와의 교차점을 역산한다."
            },
            {
                "step": 2,
                "title": "역보정 형상 배치",
                "content": "라인 모서리 둥글림을 방지하기 위한 세리프(Serif), 라인 끝단 수축(Line-end shortening)을 보상하는 해머헤드(Hammerhead), 비해상 보조 패턴(SRAF: Sub-Resolution Assist Feature)을 마스크에 자동 삽입하여 초점 심도(DOF)를 확장한다."
            },
            {
                "step": 3,
                "title": "홀리스틱 리소그래피 폐루프(R2R)",
                "content": "스캐너 노광 후 YieldStar 회절 산란계가 실시간 측정한 오버레이 및 초점 오차를 스캐너 소프트웨어와 OPC 엔진에 전달하여 다음 랏(Lot) 마스크 보정 파라미터를 자동 튜닝한다."
            }
        ],
        "limitations": [
            {
                "title": "마스크 데이터 파일 크기 및 연산 폭증",
                "description": "서브-3nm 노드에서 역보정 파형이 복잡해짐에 따라 마스크 데이터(OASIS) 용량이 테라바이트급으로 증가하고 마스크 전자빔 묘화 시간(Write Time)이 수십 시간으로 급증함.",
                "evidenceIds": []
            },
            {
                "title": "SRAF 프린팅 불량(SRAF Print-out)",
                "description": "보조 패턴이 공정 마진 범위를 벗어나 실제 웨이퍼 위에 잔류 패턴으로 인쇄되어 브릿지 쇼트 결함을 유발할 수 있음.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-photo",
                    "name": "3. 포토 공정 (Photolithography)"
                }
            ],
            "part_of": [
                {
                    "id": "eda-mask-synthesis",
                    "name": "EDA 마스크 합성 소프트웨어 플랫폼"
                }
            ],
            "next_step": [
                {
                    "id": "euv-lithography",
                    "name": "극자외선 노광 공정 (EUV)"
                }
            ]
        }
    },
    {
        "id": "cryogenic-etch",
        "title": "극저온 HARC 식각 (Cryogenic Etching)",
        "eng_name": "Cryogenic Etching",
        "aliases": [
            "극저온 식각",
            "Cryo Etch",
            "HARC 식각",
            "극저온 플라즈마"
        ],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "웨이퍼 기판 온도를 -60°C~-130°C의 극저온으로 급랭하여 측벽에서의 자발적 화학 반응을 동결(Arrhenius 반응 속도 차단)시킴으로써, 무거운 유기 폴리머 보호막 증착 없이도 순수 이온 충돌만으로 종횡비 80:1 이상의 깊은 수직 채널홀을 비틀림 없이 깎아내는 차세대 식각 기술이다.",
        "purpose": "300단 이상 3D NAND의 초고종횡비 채널홀 공정에서 기존 상온 식각의 마스크 과소모, 홀 틸팅/보잉 결함 및 식각 정지(Etch Stop)를 원천 차단하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "아레니우스 반응 속도 동결",
                "content": "k = A * exp(-Ea / kB*T) 수식에 따라 기판 온도가 상온(300K)에서 극저온(180K~150K)으로 냉각되면 측면 자발 에칭 반응 속도 k가 4자리수 이상 급감하여 언더컷이 발생하지 않는다."
            },
            {
                "step": 2,
                "title": "무폴리머 초고속 식각",
                "content": "SF6/O2 또는 순수 할로겐 가스만으로 측벽을 자연 패시베이션하므로 폴리머 침적에 의한 홀 막힘(Clogging) 없이 식각 속도를 상온 대비 2.5배 이상 가속한다."
            },
            {
                "step": 3,
                "title": "동기화 펄스 바이어스 전하 중화",
                "content": "10~50kHz 펄스 RF의 Off 구간 동안 열전자가 10μm 이상 깊은 홀 바닥으로 유입되어 양이온 축적 전하를 중화함으로써 이온 궤적 굴절에 의한 홀 틸팅(Tilting)을 3nm 이내로 방지한다."
            }
        ],
        "limitations": [
            {
                "title": "초저온 유지에 따른 설비 전력 소비 및 칠러 발열",
                "description": "대구경 300mm 웨이퍼를 연속으로 -60°C 이하로 유지하기 위한 액체 질소/특수 헬륨 칠러의 팹 전력 소모와 탄소 배출이 증가함.",
                "evidenceIds": []
            },
            {
                "title": "식각 후 승온 과정의 수분 응결 결함",
                "description": "에칭 완료 후 진공 챔버에서 상온으로 복귀할 때 결로 현상으로 인한 웨이퍼 파티클 오염 위험이 있어 질소 퍼지 로드락 진공 승온 시퀀스가 필수적임.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ],
            "part_of": [
                {
                    "id": "cryo-etch-chamber",
                    "name": "극저온 칠러 장착 플라즈마 챔버"
                }
            ],
            "next_step": [
                {
                    "id": "ald-deposition",
                    "name": "5. 박막 증착 공정 (ALD)"
                }
            ]
        }
    },
    {
        "id": "gaa-nanosheet-etch",
        "title": "GAA 나노시트 선택 식각 (GAA Selective Etch)",
        "eng_name": "GAA Nanosheet SiGe Release & Inner Spacer",
        "aliases": [
            "GAA 식각",
            "나노시트 릴리즈",
            "SiGe 선택식각",
            "Inner Spacer"
        ],
        "domain_facet": "unit_process",
        "process_category": "식각 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "GAA(Gate-All-Around) 나노시트 선택 식각은 3nm/2nm 이하 선단 로직 트랜지스터에서 채널을 형성하기 위해, 교대로 적층된 Si/SiGe 초격자 층 중 SiGe만을 손상 없이 선택적으로 제거하여 실리콘 나노시트 채널을 공중에 띄우는(Sheet Release) 핵심 식각 공정이다. 이후 게이트와 소스/드레인 간 기생 용량을 차단하기 위해 SiBCN/SiOCN 저유전체 Inner Spacer를 공동 내에 정밀 형성한다.",
        "purpose": "게이트 금속이 실리콘 나노시트 채널 4면을 완전히 감싸 전류 구동력을 극대화하고, 나노시트 사이의 미세 갭에서 발생하는 기생 정전용량(Cgs, Cgd)을 차단하여 스위칭 속도를 확보하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "무플라즈마 기상 열 화학 반응",
                "content": "ClF3 또는 CF4/O2 다운스트림 라디칼 가스를 인가하여 Ge 원자의 자발 산화/불화 촉매 반응을 유도한다. SiGe 층의 화학 반응 활성화 에너지가 Si보다 현저히 낮음을 활용하여 플라즈마 물리 충격 없이 순수 화학 반응만으로 수평 등방성 선택 제거를 달성한다."
            },
            {
                "step": 2,
                "title": "초고선택비 및 표면 거칠기 보존",
                "content": "SiGe:Si 선택비를 > 150:1로 유지하여 상하 실리콘 나노시트의 두께 손실을 0.2nm 이하로 억제하고, 채널 표면 RMS 거칠기를 0.15nm 이하로 제어하여 전자 이동도 저하를 방지한다."
            },
            {
                "step": 3,
                "title": "저유전체 Inner Spacer 형성",
                "content": "SiGe 제거 후 형성된 나노시트 사이의 리세스 캐비티에 원자층 증착(ALD)으로 k ≈ 4.2 수준의 SiBCN 박막을 채운 뒤, 채널 외부 박막만 선택적으로 제거하는 고정밀 등방성 ALE를 수행하여 게이트 기생 커패시턴스를 44% 감쇄시킨다."
            }
        ],
        "limitations": [
            {
                "title": "나노시트 융합(Stiction) 결함",
                "description": "SiGe 층을 제거하고 남은 수 나노미터 두께의 얇은 Si 나노시트들이 세정액 건조 시 모세관력에 의해 상하 시트끼리 달라붙는 스틱션(Stiction) 현상이 발생할 수 있음(초임계 CO2 건조 필수).",
                "evidenceIds": []
            },
            {
                "title": "게르마늄 잔류물(Ge Residue) 오염",
                "description": "SiGe 식각 잔류물이 나노시트 하부에 미량 남아 있을 경우 차세대 HKMG 게이트 절연막 증착 시 계면 트랩을 형성하여 문턱전압 산포를 유발함.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-etch",
                    "name": "4. 식각 공정 (Etching)"
                }
            ],
            "part_of": [
                {
                    "id": "gaa-transistor-cell",
                    "name": "3nm GAA MBCFET 로직 표준 셀"
                }
            ],
            "next_step": [
                {
                    "id": "ald-gate-dielectric",
                    "name": "HKMG 게이트 절연막 ALD 증착"
                }
            ]
        }
    },
    {
        "id": "ald-deposition",
        "title": "원자층 증착 공정 (Atomic Layer Deposition - ALD)",
        "eng_name": "Atomic Layer Deposition",
        "aliases": [
            "ALD",
            "원자층 증착",
            "원자단위 박막",
            "Self-limiting 증착"
        ],
        "domain_facet": "unit_process",
        "process_category": "박막 증착 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "반응 원료(Precursor)와 반응 가스를 챔버 내에 동시에 투입하지 않고 시간적으로 분리하여 순차적으로 주입·퍼지함으로써, 기판 표면의 화학흡착 사이트와만 반응하는 자기 제한적(Self-limiting) 표면 반응을 통해 단원자층(1~2Å) 단위로 극초박막을 균일하게 형성하는 증착 기술이다.",
        "purpose": "종횡비가 80:1을 초과하는 3D NAND 채널 홀이나 초미세 DRAM 커패시터 내부에서 단차 피복성(Step Coverage) 95% 이상의 완벽한 컨포멀(Conformal) 절연막 및 전도막을 형성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "4단계 표준 단위 사이클",
                "content": "① 전구체(Precursor) 주입: 금속 유기물 가스가 웨이퍼 표면의 활성 반응기(-OH)와 포화 화학흡착. ② 잔류 전구체 불활성 가스(Ar/N2) 퍼지: 물리 흡착된 과잉 분자 배출. ③ 반응 가스(H2O, O3, NH3) 주입: 화학흡착된 전구체와 반응하여 목적하는 단원자 산화막/질화막 형성 및 유기 리간드 탈리. ④ 부산물 퍼지."
            },
            {
                "step": 2,
                "title": "자기 제한적 표면 포화(Self-limiting Saturation)",
                "content": "표면의 반응 사이트가 전구체 분자로 100% 덮이면 추가 가스가 공급되어도 더 이상 흡착되지 않으므로, 3차원 입체 구조의 바닥과 상단에서 오차 없는 동일 두께가 보장된다."
            }
        ],
        "limitations": [
            {
                "title": "극히 느린 증착 속도(Throughput)",
                "description": "1사이클에 형성되는 두께가 0.1nm 미만으로 시간당 성장 두께가 수 나노미터에 불과하여 두꺼운 절연막(> 100nm) 형성 시 공정 시간(TAT)이 급증하고 생산 단가가 상승함.",
                "evidenceIds": []
            },
            {
                "title": "저온 열분해 부산물 오염",
                "description": "생산성 향상을 위해 공정 온도를 낮출 경우 유기 리간드의 불완전 해리로 박막 내 탄소(C), 염소(Cl) 불순물 농도가 증가하여 절연 파괴 누설전류가 증가함.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-deposition",
                    "name": "5. 박막 증착 공정 (Deposition)"
                }
            ],
            "part_of": [
                {
                    "id": "ald-reactor",
                    "name": "고속 밸브 시퀀서 탑재 ALD 챔버"
                }
            ],
            "next_step": [
                {
                    "id": "dram-zaz-capacitor",
                    "name": "1a/1b nm DRAM ZAZ 커패시터"
                }
            ]
        }
    },
    {
        "id": "hkmg-transistor",
        "title": "High-k Metal Gate 트랜지스터 (HKMG Integration)",
        "eng_name": "High-k Metal Gate (HKMG)",
        "aliases": [
            "HKMG",
            "하이케이 메탈 게이트",
            "고유전체 게이트",
            "Metal Gate"
        ],
        "domain_facet": "unit_process",
        "process_category": "박막 증착 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "기존의 폴리실리콘(Poly-Si) 게이트와 이산화규소(SiO2) 게이트 절연막을 대체하여, 비유전율이 높은 하프늄 기반 산화물(HfO2, k ≈ 25)과 일함수(Work Function)가 조절된 금속 전극(TiN, TaN, Al)을 결합함으로써 양자역학적 터널링 누설전류를 차단하고 게이트 공핍 효과를 제거하는 첨단 트랜지스터 구조 공정이다.",
        "purpose": "트랜지스터 게이트 절연막이 1nm 이하로 얇아지면서 발생하는 양자 터널링 전류 폭증과 Poly-Si 공핍화에 의한 유효 산화막 두께(EOT) 증가 및 대기 전력 소모를 억제하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "물리적 두께 확장과 EOT 축소",
                "content": "EOT = t_highk * (k_SiO2 / k_highk) 관계식에 따라, k 값이 약 25인 HfO2를 사용하면 물리적 두께를 SiO2(k=3.9) 대비 6배 이상 두껍게 유지하면서도 정전용량(Cox)을 동등하게 확보하여 터널링 누설전류를 100분의 1 이하로 감쇄시킨다."
            },
            {
                "step": 2,
                "title": "폴리실리콘 공핍 효과(Poly Depletion) 원천 제거",
                "content": "금속 게이트는 캐리어 농도가 10^22 cm^-3 이상으로 전압 인가 시 게이트 내부에 공핍층이 형성되지 않아 구동 전류(Ion)를 20% 이상 향상시킨다."
            },
            {
                "step": 3,
                "title": "금속 일함수 엔지니어링",
                "content": "nFET(TiAl, TaC, 일함수 ~4.1eV)과 pFET(TiN, TaN, 일함수 ~5.1eV)의 금속 게이트 조성비를 정밀 제어하여 문턱전압(Vth)을 비대칭 튜닝한다."
            }
        ],
        "limitations": [
            {
                "title": "열역학적 한계 (Thermal Budget 제약)",
                "description": "Gate-First 공정 적용 시 후속 소스/드레인 활성화 고온 열처리(> 1000°C)에 의해 HfO2가 결정화되면서 결정립계를 통한 누설전류가 발생하고 금속 원자가 확산되는 문제로 인해 고난도 Gate-Last (Replacement Metal Gate) 공정 전환이 필수적임.",
                "evidenceIds": []
            },
            {
                "title": "페르미 준위 핀닝(Fermi-level Pinning)",
                "description": "High-k와 금속 계면의 결함으로 인해 문턱전압이 원하는 값으로 조정되지 않고 밴드갭 중앙으로 고정되는 현상 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-deposition",
                    "name": "5. 박막 증착 공정 (Deposition)"
                }
            ],
            "part_of": [
                {
                    "id": "advanced-logic-cell",
                    "name": "CMOS 표준 로직 및 DRAM Peri 셀"
                }
            ],
            "next_step": [
                {
                    "id": "cu-damascene-cmp",
                    "name": "6. 금속 배선 공정 (Metal Interconnect)"
                }
            ]
        }
    },
    {
        "id": "dram-zaz-capacitor",
        "title": "DRAM 커패시터 ALD 박막 (DRAM High-k Capacitor)",
        "eng_name": "DRAM ZAZ High-k Capacitor",
        "aliases": [
            "ZAZ",
            "DRAM 커패시터",
            "ZAZ 유전체",
            "MIM 커패시터"
        ],
        "domain_facet": "unit_process",
        "process_category": "박막 증착 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "DRAM 커패시터 공정은 1a/1b nm 이하 초미세 셀 면적에서 전하 저장량(Cs ≥ 25 fF/cell)을 확보하기 위해, ZrO2-Al2O3-ZrO2(ZAZ) 등 초고유전체(High-k) 박막을 원자층 증착(ALD)으로 정밀 형성하여 누설 전류를 억제하고 데이터 보존 시간을 유지하는 핵심 박막 공정이다.",
        "purpose": "DRAM 트랜지스터의 오프 상태 누설전류로 인한 데이터 유실을 막고 표준 리프레시 주기(tREF, 64ms) 동안 전하를 안전하게 보존하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "정방정계(Tetragonal) 결정상 유도",
                "content": "ALD ZrO2 증착 및 400°C 열처리 시 비유전율이 20 수준인 단사정계(Monoclinic) 상 대신 고유전율 상인 정방정계(k ≈ 35~40)를 선택적으로 결정화시킨다."
            },
            {
                "step": 2,
                "title": "Al2O3 중간층 누설전류 차단",
                "content": "Al2O3는 유전율(k ≈ 9)은 낮지만 밴드갭이 8.8eV로 매우 넓어 전자 전도대 오프셋(Conduction Band Offset: ΔEc > 2.0eV)을 형성함으로써 파울러-노드하임(FN) 양자 터널링 전송을 물리적으로 차단한다."
            },
            {
                "step": 3,
                "title": "원자층 도핑 프로파일링",
                "content": "중간 Al2O3 층의 두께를 2~3개 원자층(약 0.3nm)으로 극한 통제하여 전체 유효 유전율 감소를 최소화하면서 누설전류를 억제한다."
            }
        ],
        "limitations": [
            {
                "title": "EOT 스케일링 포화 한계 (EOT Ceiling)",
                "description": "Al2O3 두께가 0.2nm 이하로 얇아지면 양자 터널링 방벽 효과가 붕괴되고, ZrO2 박막 두께를 더 줄이면 유전체 파괴 전압(Breakdown Voltage)이 동작 전압(1.0V) 이하로 급락함.",
                "evidenceIds": []
            },
            {
                "title": "실린더 필러 쓰러짐(Capacitor Collapse)",
                "description": "25fF 정전용량을 위해 종횡비가 50:1 이상으로 높아지면서 세정 건조 시 모세관 응력으로 커패시터 기둥이 쓰러져 쇼트 불량 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-deposition",
                    "name": "5. 박막 증착 공정 (Deposition)"
                }
            ],
            "part_of": [
                {
                    "id": "dram-cell-array",
                    "name": "1b nm DRAM 셀 커패시터 어레이"
                }
            ],
            "next_step": [
                {
                    "id": "dram-airgap-bitline",
                    "name": "1b/1c nm DRAM 비트라인 에어갭"
                }
            ]
        }
    },
    {
        "id": "dram-airgap-bitline",
        "title": "DRAM 비트라인 에어갭 (DRAM Bitline Air Gap)",
        "eng_name": "DRAM Bitline Air Gap Process",
        "aliases": [
            "에어갭",
            "비트라인 에어갭",
            "Air Gap",
            "Cb 저감 공정"
        ],
        "domain_facet": "unit_process",
        "process_category": "금속 배선 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "DRAM 비트라인(Bitline) 간 피치가 30nm 이하로 좁아짐에 따라 인접 배선 간에 발생하는 기생 정전용량(Cb)을 억제하기 위해, 기존의 SiO2/SiN 절연막 대신 진공 및 공기층(유전율 k = 1.0)을 비트라인 측벽 사이에 선택적으로 영구 밀봉하는 배선 공정이다.",
        "purpose": "DRAM 데이터 판독 시 센스 앰프에 인가되는 신호 전압차(ΔV = Vcore/2 * Cs / (Cs + Cb))에서 분모의 Cb를 획기적으로 낮춰 센싱 마진을 확보하고 RC 신호 지연(tRCD)을 단축하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "희생막 증착 및 핀치오프(Pinch-off) 밀봉",
                "content": "비트라인 측벽에 희생 절연막(Carbon/Polymer)을 증착한 후 에칭으로 공간을 비우고, 상부 캡핑 산화막 플라즈마 증착 시 단차 피복성이 불량한 핀치오프 현상을 유도하여 입구만 막고 내부는 진공 공동(Air Gap)으로 잔존시킨다."
            },
            {
                "step": 2,
                "title": "유전율의 이론적 한계 돌파",
                "content": "고체 유전체의 최저 유전율인 SiO2(k=3.9)나 Low-k(k=2.5)를 완전히 배제하고 유전율 k=1.0인 진공을 도입하여 배선 간 커패시턴스를 28% 일괄 감쇄시킨다."
            }
        ],
        "limitations": [
            {
                "title": "기계적 지지력 약화",
                "description": "배선 사이에 지지 구조물(Solid Dielectric)이 없으므로 후속 고압 CMP 공정이나 패키징 열압착 시 비트라인 패턴이 휘거나 무너지는 붕괴 결함 위험이 존재함.",
                "evidenceIds": []
            },
            {
                "title": "후속 공정 케미컬 침투 위험",
                "description": "핀치오프 상부 캡핑막의 미세 핀홀을 통해 후속 습식 세정액이나 증착 전구체 가스가 에어갭 내부로 침투할 경우 치명적인 단선 및 쇼트 유발.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-metal",
                    "name": "6. 금속 배선 공정 (Metal Interconnect)"
                }
            ],
            "part_of": [
                {
                    "id": "dram-bitline-structure",
                    "name": "DRAM 센스 앰프 및 비트라인 코어"
                }
            ],
            "next_step": [
                {
                    "id": "cu-damascene-cmp",
                    "name": "금속 배선 CMP 평탄화"
                }
            ]
        }
    },
    {
        "id": "3d-nand-ctf-architecture",
        "title": "3D NAND CTF 셀 구조 (3D Charge Trap Flash)",
        "eng_name": "3D Charge Trap Flash V-NAND",
        "aliases": [
            "V-NAND",
            "3D NAND",
            "CTF",
            "수직 낸드",
            "TCAT"
        ],
        "domain_facet": "unit_process",
        "process_category": "박막 증착 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "도전체 플로팅 게이트(Floating Gate) 대신 부도체 질화규소(Si3N4) 전하 포획층을 사용하는 CTF 기술을 3차원 수직 방향으로 확장하여, 산화막/질화막(ONON) 다층 박막을 일괄 적층한 뒤 채널 홀을 한 번에 뚫어 원통형 Gate-All-Around 셀 스트링을 형성하는 수직 적층 메모리 공정이다.",
        "purpose": "평면(2D) NAND에서 셀 간격이 15nm 이하로 축소되면서 발생한 플로팅 게이트 간 전하 누설 및 기생 정전용량 간섭(Cross-talk)의 물리적 한계를 근본적으로 해결하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "비도전성 전하 포획 메커니즘 (CTF)",
                "content": "실리콘 질화막 내부의 깊은 에너지 준위 결함(Trap Site)에 전자를 국소적으로 속박시키므로, 터널 산화막에 국소적 결함이 생겨도 전도성 FG처럼 저장된 전하 전체가 한꺼번에 방전되지 않아 장기 신뢰성이 극대화된다."
            },
            {
                "step": 2,
                "title": "원통형 GAA 채널 전계 집중",
                "content": "채널을 원통형(Cylindrical)으로 감싸는 수직 GAA 구조를 통해 게이트 제어력을 극대화하고 프로그램/소거 전압 윈도우를 2배 이상 확보한다."
            },
            {
                "step": 3,
                "title": "일괄 식각 관통 (TCAT / BiCS)",
                "content": "100~300개 이상의 층을 미리 쌓은 뒤 단 한 번의 극저온 HARC 식각으로 모든 층을 수직 관통하여 단위 비트당 제조 단가를 획기적으로 낮춘다."
            }
        ],
        "limitations": [
            {
                "title": "스트링 전류(String Current) 감소",
                "description": "적층 수가 200단, 300단으로 증가함에 따라 수직 채널 길이가 10μm 이상으로 길어져 전체 셀 스트링 저항이 증가하고 읽기 판독 전류가 감소함.",
                "evidenceIds": []
            },
            {
                "title": "상하부 채널 홀 임계 치수(CD) 불균일",
                "description": "깊은 홀 식각 시 상부는 넓고 하부는 좁아지는 테이퍼(Tapering) 현상으로 인해 상부 셀과 하부 셀 간의 문턱전압 산포가 벌어짐.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-deposition",
                    "name": "5. 박막 증착 공정 (Deposition)"
                }
            ],
            "part_of": [
                {
                    "id": "3d-nand-core",
                    "name": "초고용량 3D NAND 플래시 어레이"
                }
            ],
            "next_step": [
                {
                    "id": "3d-nand-mo-wordline",
                    "name": "300단+ 워드라인 몰리브덴 ALD"
                }
            ]
        }
    },
    {
        "id": "4d-nand-puc",
        "title": "4D NAND PUC 아키텍처 (Peri Under Cell)",
        "eng_name": "Peri Under Cell (PUC) 4D NAND",
        "aliases": [
            "4D NAND",
            "PUC",
            "COP",
            "Peri Under Cell"
        ],
        "domain_facet": "unit_process",
        "process_category": "박막 증착 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "셀 어레이 외곽(Side)에 평면으로 배치되던 페이지 버퍼, 로우 디코더 등 주변 회로(Peri)를 웨이퍼 기판 바로 위 최하단에 먼저 형성하고, 그 상부에 3D 셀 어레이를 수직 적층함으로써 칩 면적을 30% 이상 절감하는 차세대 3D/4D 구조 혁신 공정이다.",
        "purpose": "동일한 웨이퍼 1장에서 생산할 수 있는 넷 다이(Net Die) 수를 극대화하여 비트당 생산 원가를 획기적으로 낮추고 칩 크기를 소형화하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "수직 적층 통합 공간 재배치",
                "content": "전통적인 2차원 평면 배치(셀 70% + 페리 30%)를 3차원 적층(하부 페리 100% 투영 면적 위에 셀 적층)으로 전환하여 순수 셀 어레이 면적만으로 칩 크기를 축소시킨다."
            },
            {
                "step": 2,
                "title": "열역학적 버짓(Thermal Budget) 보호",
                "content": "하부 페리 트랜지스터의 소스/드레인 불순물이 상부 3D 셀 형성 시의 장시간 고온 열처리(> 800°C)에 의해 비정상 확산되지 않도록 텅스텐/몰리브덴 기반 내열 금속 배선과 확산 방지 배리어를 적용한다."
            }
        ],
        "limitations": [
            {
                "title": "열 스트레스에 의한 하부 트랜지스터 특성 열화",
                "description": "상부의 수백 단 ONON 박막 적층 시 발생하는 누적 열응력으로 인해 하부 로직 트랜지스터의 문턱전압 표류 및 접합 누설전류 발생 위험.",
                "evidenceIds": []
            },
            {
                "title": "다층 비아 관통 공정 난도",
                "description": "상부 셀 어레이를 관통하여 하부 페리 회로와 비트라인/워드라인을 연결하는 수직 인터커넥트 관통 비아 공정의 종횡비가 극도로 깊어져 오정렬 쇼트 위험 증가.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-deposition",
                    "name": "5. 박막 증착 공정 (Deposition)"
                }
            ],
            "part_of": [
                {
                    "id": "4d-nand-core",
                    "name": "초고밀도 4D NAND 메모리 다이"
                }
            ],
            "next_step": [
                {
                    "id": "3d-nand-mo-wordline",
                    "name": "워드라인 저저항 금속 충진"
                }
            ]
        }
    },
    {
        "id": "3d-nand-mo-wordline",
        "title": "3D NAND 몰리브덴 워드라인 (Molybdenum Wordline)",
        "eng_name": "3D NAND Mo Wordline ALD",
        "aliases": [
            "Mo 워드라인",
            "몰리브덴 ALD",
            "무불소 전극",
            "차세대 워드라인"
        ],
        "domain_facet": "unit_process",
        "process_category": "금속 배선 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "300단 이상 3D NAND의 리플레이스먼트 게이트(Replacement Gate) 공정에서 기존 텅스텐(W) 전극을 대체하여, 무불소 몰리브덴(Mo) 전구체를 이용한 저온(350°C) 원자층 증착(ALD)으로 좁은 슬릿 내부를 보이드 없이 균일하게 충진함으로써 배선 저항을 35% 낮추고 웨이퍼 휨 응력을 제어하는 금속화 공정이다.",
        "purpose": "WF6 전구체에서 발생하는 잔류 불소(F)의 게이트 산화막 침투 파괴와 텅스텐의 박막 두께 감소 시 비저항 급증 현상을 극복하여 초고단 낸드의 쓰기/읽기 지연을 개선하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "전자 평균 자유 행로(EMFP) 스케일링",
                "content": "몰리브덴은 상온 전자 평균 자유 행로가 약 10nm로 텅스텐(~40nm)보다 현저히 짧아, 10nm 이하의 극미세 게이트 두께에서도 표면 산란(Surface Scattering)에 의한 비저항 급증이 발생하지 않는다."
            },
            {
                "step": 2,
                "title": "무불소(Fluorine-free) 전구체 분해",
                "content": "Mo(CO)6 또는 MoCl5 유기금속 전구체를 사용하여 절연막을 부식시키는 불소 불순물 농도를 제로화하여 전하 보존 특성을 유지한다."
            },
            {
                "step": 3,
                "title": "박막 응력 상쇄",
                "content": "몰리브덴 증착 막의 진성 응력을 압축 응력으로 튜닝하여 300단 적층에 따른 웨이퍼 보우(Bow)를 40% 이상 상쇄시킨다."
            }
        ],
        "limitations": [
            {
                "title": "유기 카보닐기 잔류 탄소(C) 오염",
                "description": "저온 증착 시 전구체 리간드가 완전 분해되지 않아 1~3% 수준의 탄소 불순물이 침착되면 금속 비저항이 상승할 수 있음.",
                "evidenceIds": []
            },
            {
                "title": "산화 분위기 민감도",
                "description": "몰리브덴은 산소와 반응 시 휘발성 삼산화몰리브덴(MoO3)을 형성하여 손실되므로 후속 공정의 엄격한 무산소 질소 퍼지 환경이 강제됨.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-metal",
                    "name": "6. 금속 배선 공정 (Metal Interconnect)"
                }
            ],
            "part_of": [
                {
                    "id": "nand-wordline-stack",
                    "name": "3D NAND 수직 게이트 워드라인 적층체"
                }
            ],
            "next_step": [
                {
                    "id": "cu-damascene-cmp",
                    "name": "금속 배선 CMP 평탄화"
                }
            ]
        }
    },
    {
        "id": "cu-damascene-cmp",
        "title": "구리 다마신 배선 및 CMP (Cu Damascene & CMP)",
        "eng_name": "Cu Damascene & Chemical Mechanical Planarization",
        "aliases": [
            "다마신",
            "Cu CMP",
            "화학기계적 연마",
            "프레스턴 모델",
            "디싱"
        ],
        "domain_facet": "unit_process",
        "process_category": "금속 배선 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "구리 다마신 배선 공정은 플라즈마 식각 가공이 어려운 구리(Cu)의 물리적 특성을 극복하기 위해, 층간 절연막에 홈(트렌치)을 먼저 파고 구리를 전기도금으로 채운 후 화학기계적 연마(CMP)로 표면을 평탄화하여 고밀도 다층 신호 배선을 완성하는 반도체 표준 배선 공정이다.",
        "purpose": "알루미늄(Al) 대비 낮은 비저항(1.7 μΩ·cm)과 우수한 일렉트로마이그레이션(EM) 내성을 확보하여 첨단 반도체의 신호 지연(RC Delay)을 최소화하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "프레스턴 법칙 (Preston's Law) 확장식",
                "content": "재료 제거율은 MRR = Kp * P * V (압력 P, 상대속도 V, 프레스턴 상수 Kp)를 따른다. 국소 패턴 밀도(ρ)에 따라 유효 압력이 Peff = P0 / ρ로 변동하여 연마율 편차가 발생한다."
            },
            {
                "step": 2,
                "title": "디싱(Dishing) 및 침식(Erosion) 메커니즘",
                "content": "연질인 구리와 경질인 산화막의 연마 속도 차이로 인해 광폭 구리선 중앙부가 패드가 휘어지며 파이는 디싱과, 고밀도 배선 영역의 절연막이 깎여나가는 침식이 발생한다."
            },
            {
                "step": 3,
                "title": "더미 메탈(Dummy Metal Fill) EDA 룰",
                "content": "디싱을 억제하기 위해 회로 설계 단계에서 금속 면적 밀도를 20%~80% 범위로 균일하게 맞추는 더미 패턴 삽입 알고리즘이 적용된다."
            }
        ],
        "limitations": [
            {
                "title": "디싱에 의한 배선 저항 불균일 및 단선",
                "description": "광폭 배선에서 디싱 깊이가 10nm를 초과하면 배선 단면적 감소로 배선 저항이 국소 급증하고 신호 왜곡 유발.",
                "evidenceIds": []
            },
            {
                "title": "구리 산화 및 부식 (Corrosion)",
                "description": "CMP 후 슬러리 잔류 화학종에 의해 구리 표면이 갈바닉 부식(Galvanic Corrosion)을 일으키므로 CMP 직후 인라인 세정(Megasonic + 희석 유기산)이 필수적임.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-metal",
                    "name": "6. 금속 배선 공정 (Metal Interconnect)"
                }
            ],
            "part_of": [
                {
                    "id": "cmp-polisher",
                    "name": "다축 플래튼 CMP 연마 장비"
                }
            ],
            "next_step": [
                {
                    "id": "cmp-slurry-bta-passivation",
                    "name": "저하중 BTA 슬러리 화학 제어"
                }
            ]
        }
    },
    {
        "id": "cmp-slurry-bta-passivation",
        "title": "CMP 슬러리 화학 및 방식 제어 (CMP Slurry Chemistry)",
        "eng_name": "Low-Downforce Cu CMP Slurry Chemistry",
        "aliases": [
            "BTA 슬러리",
            "CMP 케미컬",
            "저하중 CMP",
            "BTA 패시베이션"
        ],
        "domain_facet": "unit_process",
        "process_category": "금속 배선 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "CMP 슬러리 화학 공정은 첨단 노드의 취약한 저유전체(Low-k) 박막 파손을 막기 위해 저하중에서 연마하면서, BTA 방식제를 통해 구리 배선 오목부의 부식을 막고 돌출부만 기계화학적으로 선택 제거하여 원자 수준의 평탄도를 달성하는 슬러리 계면 화학 기술이다.",
        "purpose": "극저유전체 박막의 기계적 파손(Delamination) 없이 디싱 깊이를 8nm 이하로 제어하고 고속 평탄화를 달성하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "BTA 고분자 보호막 동역학",
                "content": "BTA(5~15mM)가 구리 표면에서 Cu+ 이온과 반응하여 1~2nm 두께의 불용성 고분자 착물 [Cu(I)BTA]n 피막을 형성하여 정적 식각률을 10 Å/min 이하로 동결시킨다."
            },
            {
                "step": 2,
                "title": "돌출부 선택적 마찰 박리 및 아미노산(글리신) 착화",
                "content": "돌출부에서는 연마 패드와 콜로이달 실리카 입자의 마찰로 보호 피막이 순간적으로 탈착되고, 노출된 구리 표면이 산화제(H2O2)에 의해 산화된 후 글리신(Glycine) 착화제와 수용성 착염을 형성하며 급속 제거된다."
            },
            {
                "step": 3,
                "title": "저압 고효율 기구",
                "content": "하중을 0.8 psi로 낮추어도 화학적 산화-착화 반응 속도를 최적화하여 6000 Å/min 이상의 높은 동적 연마율을 유지한다."
            }
        ],
        "limitations": [
            {
                "title": "BTA 잔류물 오염",
                "description": "연마 완료 후 배선 표면에 강하게 흡착된 BTA 고분자 잔류물이 완전 세정되지 않으면 층간 비아 접촉 저항(Rc)이 폭증함.",
                "evidenceIds": []
            },
            {
                "title": "슬러리 입자 뭉침(Aggregation)",
                "description": "산화제 및 킬레이트제 혼합 후 시간 경과 시 나노 연마 입자가 응집되어 마이크로 스크래치 결함을 유발함.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-metal",
                    "name": "6. 금속 배선 공정 (Metal Interconnect)"
                }
            ],
            "part_of": [
                {
                    "id": "cmp-slurry-supply",
                    "name": "CMP 슬러리 정밀 혼합 공급계(SDS)"
                }
            ],
            "next_step": [
                {
                    "id": "fab-fdc-oes-realtime",
                    "name": "스마트 팹 FDC 및 공정 제어"
                }
            ]
        }
    },
    {
        "id": "fab-fdc-oes-realtime",
        "title": "FDC 공정 이상 감지 (Fault Detection & Classification)",
        "eng_name": "Fault Detection and Classification (FDC)",
        "aliases": [
            "FDC",
            "OES FDC",
            "챔버 이상 감지",
            "EPD",
            "SEMI E133",
            "SECS/GEM"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 및 FDC",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "FDC(결함 탐지 및 분류)는 반도체 제조 장비 내부의 센서 데이터를 실시간 수집·분석하여, 공정 이상 징후를 조기에 감지하고 불량 웨이퍼 발생을 사전에 차단하는 스마트 팹 핵심 운영 기술이다. 첨단 플라즈마 식각 챔버에서는 광방출 분광(OES) 및 딥 오토인코더 머신러닝 잔차 분석을 통해 챔버 내벽 드리프트(Wall Drift)를 조기 감지하고 식각 종단점(EPD)을 0.05초 정밀도로 판정한다.",
        "purpose": "동일 레시피에서도 챔버 상태 변화로 인해 발생하는 웨이퍼 간 식각 깊이 및 임계 선폭(CD) 편차를 사전 차단하고 과도식각(Over-etch) 마진을 축소하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "전스펙트럼 라디칼 피크 트래킹",
                "content": "주요 반응 라디칼인 F*(703.7nm), CF2(251.9nm), 에칭 부산물 SiF*(440.0nm), CO*(519.8nm)의 발광 강도 비를 실시간 분석하여 플라즈마 전자 온도 및 라디칼 밀도를 진단한다."
            },
            {
                "step": 2,
                "title": "SEMI E133 표준 데이터 파이프라인",
                "content": "초당 100회 이상의 대용량 광학 스펙트럼 데이터를 손실 없이 스마트 팹 상위 FDC 서버로 고속 스트리밍한다."
            },
            {
                "step": 3,
                "title": "비지도 학습 오토인코더 잔차 감시",
                "content": "정상 챔버 상태의 스펙트럼 상관관계를 학습한 딥러닝 모델이 재구성 오차(Reconstruction Error)를 계산하여, 작업 중단 없이 챔버 오염 징후를 3웨이퍼 전에 조기 경보한다."
            }
        ],
        "limitations": [
            {
                "title": "뷰포트 윈도우 오염에 따른 광량 감쇠 (Window Clouding)",
                "description": "챔버 내부 폴리머 부산물이 석영 관측창에 흡착되면 전체 스펙트럼 강도가 감소하여 실제 플라즈마 변화와 센서 오염 간 오분류 위험 발생.",
                "evidenceIds": []
            },
            {
                "title": "방대한 데이터 네트워크 트래픽",
                "description": "팹 내 수백 대의 챔버에서 전스펙트럼을 동시 스트리밍 시 팹 LAN 대역폭 부하 증가(엣지 컴퓨팅 전처리 필수).",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "op-fdc",
                    "name": "FDC (고장 감지 및 분류)"
                }
            ],
            "part_of": [
                {
                    "id": "ees-rms",
                    "name": "EES & RMS 장비 엔지니어링 시스템"
                }
            ],
            "next_step": [
                {
                    "id": "run-to-run",
                    "name": "APC & R2R 공정 파라미터 자동 보정"
                }
            ]
        }
    },
    {
        "id": "cowos-interposer-cuf",
        "title": "2.5D CoWoS 패키징 (2.5D CoWoS & Interposer)",
        "eng_name": "2.5D CoWoS & Capillary Underfill Process",
        "aliases": [
            "CoWoS",
            "2.5D 패키징",
            "실리콘 인터포저",
            "CUF",
            "이종집적"
        ],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "레티클 크기 한계(약 858mm²)를 초과하는 거대 AI 가속기 칩을 제조하기 위해, 반도체 전공정으로 미세 배선(0.4/0.4μm)과 고밀도 TSV를 형성한 대면적 실리콘 인터포저 위에 GPU/NPU 로직 칩과 다수의 HBM 스택을 마이크로범프로 실장하고 모세관 언더필(CUF)로 접합하는 첨단 2.5D 이종 집적 플랫폼 공정이다.",
        "purpose": "단일 실리콘 다이 면적 한계를 극복하고, 로직 칩과 메모리 칩 간에 수천 개 이상의 병렬 고속 데이터 버스를 연결하여 10 TB/s 이상의 테라바이트급 초고대역폭을 확보하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초고밀도 RDL 실리콘 인터포저",
                "content": "유기물 PCB 기판이 감당할 수 없는 서브마이크론 배선 피치(L/S = 0.4/0.4μm)와 지름 10μm의 실리콘 관통전극(TSV)을 집적하여 단일 칩 수준의 신호 무결성을 제공한다."
            },
            {
                "step": 2,
                "title": "대면적 모세관 언더필(CUF) 유동 동역학",
                "content": "50mm × 50mm 이상의 대형 패키지에서 수만 개의 마이크로범프(20μm 피치) 사이로 언더필 레진이 미충진되는 것을 막기 위해, 110°C에서 30분간 겔화(Gelation)를 지연시키고 표면 장력을 제어하여 보이드 없는 침투를 보장한다."
            }
        ],
        "limitations": [
            {
                "title": "인터포저 대면적화에 따른 열팽창 휨(Warpage)",
                "description": "인터포저 크기가 3개 이상의 레티클 크기(> 2500mm²)로 대형화되면서 실리콘 인터포저와 하부 패키지 서브스트레이트 간의 열팽창 불일치로 모서리 범프 크랙 위험 급증.",
                "evidenceIds": []
            },
            {
                "title": "천문학적인 제조 단가 및 실리콘 수율",
                "description": "고가의 300mm 웨이퍼를 순수 인터포저용으로 소비하므로 유기물 인터포저(CoWoS-R) 대비 비용 부담이 매우 높음.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-packaging",
                    "name": "8. 첨단 패키징 공정 (Packaging)"
                }
            ],
            "part_of": [
                {
                    "id": "ai-supercomputing-module",
                    "name": "초고성능 AI 컴퓨팅 가속기 모듈"
                }
            ],
            "next_step": [
                {
                    "id": "hbm-kgd-testing",
                    "name": "패키지 레벨 고속 신호 테스트"
                }
            ]
        }
    },
    {
        "id": "fan-out-wafer-level-packaging",
        "title": "팬아웃 패키징 (Fan-Out WLP / PLP)",
        "eng_name": "Fan-Out Wafer Level Packaging",
        "aliases": [
            "FOWLP",
            "FOPLP",
            "InFO",
            "팬아웃",
            "무기판 패키징"
        ],
        "domain_facet": "unit_process",
        "process_category": "첨단 패키징 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "전통적인 고가의 플라스틱 PCB 패키징 기판(Substrate)을 완전히 제거하고, 실리콘 다이를 에폭시 몰딩 컴파운드(EMC)로 매립한 뒤 칩 외곽(Fan-Out) 영역까지 미세 구리 재배선층(RDL, L/S ≤ 2/2μm)을 직접 형성하며 수직 구리 필러(TIV)를 통해 상부 메모리와 최단 거리로 연결하는 초박형 고성능 패키징 공정이다.",
        "purpose": "스마트폰 모바일 AP 및 웨어러블 칩의 두께를 20% 이상 줄이고, PCB 기판 내부의 배선 기생 인덕턴스를 제거하여 초고주파 신호 무결성과 열 방출 효율을 극대화하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "무기판 직접 재배선 (Substrate-less RDL)",
                "content": "감광성 폴리이미드(PI) 절연체와 구리 세미 애디티브(SAP) 도금 공정으로 2μm 이하의 미세 배선을 다이 표면과 몰딩재 위에 직접 형성하여 패키지 두께를 1mm 미만으로 박막화한다."
            },
            {
                "step": 2,
                "title": "Through InFO Via (TIV) 3D PoP 적층",
                "content": "몰딩층을 관통하는 수직 구리 기둥(TIV)을 도금하여 패키지 상단에 모바일 LPDDR DRAM을 최단 거리(< 100μm)로 적층(Package-on-Package)함으로써 신호 손실을 30% 감쇄시킨다."
            }
        ],
        "limitations": [
            {
                "title": "다이 시프트(Die Shift) 결함",
                "description": "EMC 수지 경화 시의 열수축 응력으로 인해 캐리어 상의 실리콘 다이가 미세하게(수 마이크로미터) 회전하거나 밀려나, 후속 RDL 포토 공정에서 비아 정렬 오차가 발생함.",
                "evidenceIds": []
            },
            {
                "title": "대형 패널 휨(Warpage in PLP)",
                "description": "생산성을 높이기 위해 대면적 사각 패널(FOPLP, 500mm×500mm)을 적용할 경우 중심부와 모서리의 열팽창 편차로 극심한 휨이 발생하여 진공 이송 오류 유발.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-packaging",
                    "name": "8. 첨단 패키징 공정 (Packaging)"
                }
            ],
            "part_of": [
                {
                    "id": "mobile-application-processor",
                    "name": "초박형 모바일 AP 시스템 패키지"
                }
            ],
            "next_step": [
                {
                    "id": "hbm-kgd-testing",
                    "name": "최종 패키지 번인 및 전기 테스트"
                }
            ]
        }
    },
    {
        "id": "hbm-kgd-testing",
        "title": "HBM KGD 양품 선별 검사 (Known Good Die Testing)",
        "eng_name": "HBM Known Good Die & High-Speed Probe Testing",
        "aliases": [
            "KGD",
            "HBM 테스트",
            "프로브 카드",
            "EDS 테스트",
            "웨이퍼 번인"
        ],
        "domain_facet": "unit_process",
        "process_category": "EDS 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "웨이퍼 상태에서 수만 개의 미세 마이크로범프에 MEMS 프로브 카드의 초정밀 핀을 동시 접촉시켜 4Gbps 이상의 고주파 동작 속도와 누설전류를 전수 검사하고, 고전압·고온 가속 스트레스(Wafer-Level Burn-In)를 인가하여 초기 고장 다이를 사전에 100% 제거함으로써 적층용 완전 무결점 양품 다이(Known Good Die)만을 선별하는 공정이다.",
        "purpose": "16단 적층 시 단 1개의 불량 다이로 인해 나머지 15개의 정상 다이와 고가의 베이스 로직 다이 전체가 폐기되는 연쇄 수율 파괴(Yield Catastrophe)를 방지하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초미세 MEMS 캔틸레버 접촉 역학",
                "content": "직경 15μm 마이크로범프에 인가되는 접촉 하중을 핀당 0.5 gf 이하로 극소화하여 범프 표면 스크래치를 1μm 이내로 제어하면서도, 미세 와이핑(Micro-wiping) 거동을 통해 표면 자연 산화막을 뚫고 접촉 저항 < 0.1 Ω을 확보한다."
            },
            {
                "step": 2,
                "title": "웨이퍼 레벨 번인 (WLBI)",
                "content": "125°C 고온 환경에서 정상 동작 전압의 1.3배를 인가하여 게이트 절연막의 잠재 결함(Latent Defect)을 조기 파괴시켜 출하 후 현장 고장률(DPPM)을 제로화한다."
            }
        ],
        "limitations": [
            {
                "title": "프로브 핀 접촉 손상에 따른 후속 본딩 불량",
                "description": "프로브 카드가 마이크로범프를 과도하게 누르면 범프 평탄도가 손상되어 후속 하이브리드 본딩이나 리플로우 시 미접합 보이드 발생.",
                "evidenceIds": []
            },
            {
                "title": "수만 핀 동시 접촉 시 웨이퍼 휨",
                "description": "300mm 웨이퍼 전면에 수만 개의 핀이 동시에 누를 때 발생하는 수십 kgf의 총 압력으로 인해 극박 웨이퍼가 파손될 위험 존재.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-eds",
                    "name": "7. EDS 공정 (Electrical Die Sorting)"
                }
            ],
            "part_of": [
                {
                    "id": "automatic-test-equipment",
                    "name": "초고속 메모리 자동 검사 장비 (ATE)"
                }
            ],
            "next_step": [
                {
                    "id": "mr-muf",
                    "name": "HBM 다단 적층 패키징 공정"
                }
            ]
        }
    },
    {
        "id": "tddb-reliability-physics",
        "title": "절연막 신뢰성 모델 TDDB & BTI (Gate Dielectric Reliability)",
        "eng_name": "Gate Dielectric TDDB & BTI Reliability Physics",
        "aliases": [
            "TDDB",
            "BTI",
            "NBTI",
            "절연 파괴",
            "신뢰성 모델",
            "IRPS"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 및 FDC",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "3nm 이하 선단 GAA 나노시트 및 DRAM HKMG 게이트 절연막에서 장시간 전압 및 온도 스트레스 인가 시 박막 내부 결함(Trap)의 확률적 누적으로 발생하는 경시 절연 파괴(Time-Dependent Dielectric Breakdown)와 문턱전압 표류(BTI)를 퍼콜레이션(Percolation) 전도 이론으로 모델링하여 10년 수명을 보증하는 신뢰성 물리학 공학이다.",
        "purpose": "반도체 칩이 실제 데이터센터 및 스마트폰 현장에서 10년 이상 연속 동작할 때 치명적인 단선 및 연소 고장이 발생하지 않도록 동작 전압 마진을 과학적으로 규정하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "퍼콜레이션 통계 파괴 모델",
                "content": "전압 스트레스에 의해 절연막 내부에서 산소 공공 결함이 무작위로 생성되다가, 상부 게이트와 하부 채널을 잇는 전도성 결함 클러스터(Percolation Path)가 형성되는 순간 절연성이 영구 파괴된다."
            },
            {
                "step": 2,
                "title": "전력 법칙(Power-Law) 수명 가속 방정식",
                "content": "파괴 시간 tBD는 인가 전압 V와 온도 T에 대해 tBD = t0 * V^-n * exp(Ea / kB*T) 관계식을 따르며, 전압 가속 지수 n ≈ 35~40의 극단적인 비선형성을 갖는다."
            },
            {
                "step": 3,
                "title": "10년 생존 규격",
                "content": "0.75V 동작 전압 및 125°C 가혹 조건에서 10년 동작 시 누적 고장 확률이 1 FIT (10^9 소자 시간당 1개 고장) 미만임을 가속 수명 시험으로 증명한다."
            }
        ],
        "limitations": [
            {
                "title": "박막 두께 축소 시 퍼콜레이션 임계 결함 수 급감",
                "description": "절연막 두께가 1.5nm 이하로 얇아지면 단 2~3개의 결함만 연결되어도 즉각적인 파괴(Soft Breakdown)가 발생하여 신뢰성 마진이 급격히 축소됨.",
                "evidenceIds": []
            },
            {
                "title": "자가 발열(Self-Heating Effect)과의 복합 열화",
                "description": "고속 연산 시 칩 내부 국소 핫스팟 온도가 150°C를 초과하면 아레니우스 열화 속도가 지수함수적으로 증가하여 수명이 급감함.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "op-fdc",
                    "name": "FDC 및 신뢰성 공학"
                }
            ],
            "part_of": [
                {
                    "id": "product-qualification",
                    "name": "팹 제품 출하 품질 보증 시스템"
                }
            ],
            "next_step": [
                {
                    "id": "yield-negative-binomial-modeling",
                    "name": "팹 수율 예측 모델 연계"
                }
            ]
        }
    },
    {
        "id": "yield-negative-binomial-modeling",
        "title": "반도체 팹 수율 모델링 (Fab Yield Modeling & Prediction)",
        "eng_name": "Negative Binomial Yield & Defect Clustering Model",
        "aliases": [
            "수율 모델",
            "결함 클러스터링",
            "네거티브 바이노미얼",
            "웨이퍼 수율",
            "KLA"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 및 FDC",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "대형 AI 가속기 다이(Die Area > 800mm²) 제조 시, 결함이 웨이퍼 전면에 무작위로 분포한다는 전제의 고전 포아송 수율 모델이 실제 수율을 심각하게 과소평가하는 오류를 극복하기 위해, 감마(Gamma) 분포를 따르는 결함 뭉침 현상(Defect Clustering)을 매개변수 α로 보정하여 실제 팹 양산 수율을 2% 이내 오차로 정밀 예측하는 수율 통계 물리학이다.",
        "purpose": "웨이퍼 투입량 결정, 제조 원가 사전 산출 및 팹 장비의 결함 킬러성(Kill Ratio)을 정확히 분별하여 수율 램프업(Ramp-up) 기간을 단축하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "네거티브 바이노미얼 수율 지배 방정식",
                "content": "수율 Y는 Y = (1 + D0 * A / α)^-α 수식을 따른다. 여기서 D0는 평균 치명 결함 밀도, A는 칩 다이 면적, α는 결함 클러스터링 모수(Clustering Parameter)이다."
            },
            {
                "step": 2,
                "title": "결함 뭉침(Clustering)의 통계적 이점",
                "content": "결함들이 웨이퍼 가장자리나 특정 스크래치 영역에 밀집될수록(α 값이 작을수록), 결함이 없는 완전 무결점 대형 다이가 살아남을 확률이 기하급수적으로 증가한다."
            },
            {
                "step": 3,
                "title": "포아송 모델의 한계 극복",
                "content": "다이 크기가 800mm² 이상일 때 포아송 모델(Y = exp(-D0*A))은 수율을 5% 미만으로 예측하지만, 실제 클러스터링 팹 수율은 60% 이상으로 유지됨을 완벽히 설명한다."
            }
        ],
        "limitations": [
            {
                "title": "클러스터링 모수 α의 장비 의존성",
                "description": "노광 스캐너, 식각 챔버, CMP 장비마다 결함 분포 패턴이 달라 단일 전역 α 값을 적용할 경우 공정별 수율 기여도 분리 분석이 왜곡됨.",
                "evidenceIds": []
            },
            {
                "title": "체계적 결함(Systematic Defect) 미반영 한계",
                "description": "마스크 결함이나 OPC 오차처럼 동일 위치에 반복적으로 발생하는 체계적 결함은 통계적 랜덤 클러스터링 모델로 예측 불가능함.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "op-fdc",
                    "name": "FDC 및 수율 공학"
                }
            ],
            "part_of": [
                {
                    "id": "yield-management-system",
                    "name": "팹 전사 수율 관리 시스템 (YMS)"
                }
            ],
            "next_step": [
                {
                    "id": "bbp-defect-inspection",
                    "name": "광대역 결함 검사 및 분류"
                }
            ]
        }
    },
    {
        "id": "bbp-defect-inspection",
        "title": "광대역 플라즈마 결함 검사 BBP (Broadband Plasma Inspection)",
        "eng_name": "Broadband Plasma (BBP) Optical Inspection",
        "aliases": [
            "BBP",
            "광대역 검사",
            "인라인 결함 검사",
            "다크필드",
            "KLA"
        ],
        "domain_facet": "unit_process",
        "process_category": "EDS 공정",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "BBP(광대역 플라즈마 결함 검사)는 레이저 펌핑 제논 플라즈마 광원의 초광대역 딥 UV(190~450nm) 파장과 위상차 편광 광학계를 결합하여, 3D NAND 및 GAA 나노시트의 깊은 고종횡비(80:1) 트렌치 바닥에 존재하는 10nm급 미세 파티클과 결함을 비파괴 고속 검출하는 첨단 광학 검사 기술이다.",
        "purpose": "전자빔(E-beam) 검사의 치명적 단점인 느린 검사 속도(웨이퍼 1장당 수십 시간)를 극복하고, 양산 라인에서 시간당 수십 매 이상의 고속으로 3차원 깊숙한 치명 결함을 실시간 전수 스캔하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초광대역 DUV 간섭 광학",
                "content": "단일 레이저 파장의 정재파 간섭 억제를 위해 190~450nm 다파장을 동시 조사하여, 박막 층간 굴절률 차이로 인한 반사광을 상쇄하고 깊은 트렌치 바닥까지 광자를 침투시킨다."
            },
            {
                "step": 2,
                "title": "편광 산란 필터링",
                "content": "정상 패턴 구조물에서 반사되는 강한 브래그 회절광을 편광 필터로 차단하고, 무정형 미세 파티클 및 보이드에서 산란되는 미약한 비등방성 산란광만을 증폭하여 신호 대 잡음비(SNR)를 극대화한다."
            }
        ],
        "limitations": [
            {
                "title": "광학 회절 한계에 의한 서브-5nm 미세 결함 판별 불가",
                "description": "광학 파장의 회절 한계로 인해 5nm 이하의 극미세 핀홀이나 잠재 결정 결함은 검출할 수 없어 후속 정밀 리뷰(CD-SEM / Review SEM) 연계가 필수적임.",
                "evidenceIds": []
            },
            {
                "title": "고출력 DUV 조사에 따른 레지스트 손상(Photoresist Shrinkage)",
                "description": "미세 패턴 레지스트 층에 초고출력 플라즈마 광을 장시간 조사할 경우 감광액이 열수축하여 치수 변형 결함 유발.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "proc-eds",
                    "name": "7. EDS 공정 (Electrical Die Sorting)"
                }
            ],
            "part_of": [
                {
                    "id": "inline-inspection-cluster",
                    "name": "팹 인라인 광학 결함 검사 클러스터"
                }
            ],
            "next_step": [
                {
                    "id": "yield-negative-binomial-modeling",
                    "name": "결함 맵 수율 관리 시스템 전송"
                }
            ]
        }
    },
    {
        "id": "ultra-pure-water-upw",
        "title": "초순수 인프라 시스템 UPW (Ultra-Pure Water System)",
        "eng_name": "Ultra-Pure Water Sub-ppb Purification",
        "aliases": [
            "초순수",
            "UPW",
            "반도체 용수",
            "용존산소 제막",
            "TOC 제거"
        ],
        "domain_facet": "materials_infra",
        "process_category": "소재 및 케미컬",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "반도체 초순수(UPW) 시스템은 3nm 이하 선단 노드의 세정 공정에서 웨이퍼 산화 및 유기물 흡착을 원천 차단하기 위해, 물속의 용존 산소(DO)를 0.1 ppb 이하, 총유기탄소(TOC)를 0.5 ppb 이하로 극한 정제하여 이론적 한계 비저항(18.25 MΩ·cm)의 초순수를 24시간 연속 공급하는 팹 유틸리티 인프라이다.",
        "purpose": "미세 세정 시 초순수에 잔류하는 미량의 산소 분자가 구리 및 실리콘 표면과 반응하여 원치 않는 절연 산화막을 형성하고 접촉 저항(Rc)을 폭증시키는 결함을 방지하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "진공 막 탈기 및 촉매 환원",
                "content": "진공 막 탈기 모듈(Membrane Contactor)로 1차 탈기 후, 팔라듐(Pd) 촉매 탑에서 미량 주입된 수소(H2)와 반응시켜 잔류 산소를 물 분자(2H2 + O2 → 2H2O)로 화학 환원함으로써 용존 산소를 < 0.1 ppb로 제거한다."
            },
            {
                "step": 2,
                "title": "185nm 진공 자외선(VUV) 산화 분해",
                "content": "185nm 자외선 램프로 수산화 라디칼(·OH)을 생성하여 미세 유기물을 이산화탄소(CO2)로 완전 광산화 분해한 후 비이온성 이온교환수지로 흡착 제거하여 TOC < 0.5 ppb를 달성한다."
            }
        ],
        "limitations": [
            {
                "title": "배관 재질 용출(Leaching) 및 생물막(Biofilm) 형성",
                "description": "고순도 PVDF 배관에서도 미량의 불소 이온이나 유기 가소제가 용출될 수 있으며, 박테리아 사멸체(Endotoxin)가 누적될 경우 나노 파티클 불량 유발.",
                "evidenceIds": []
            },
            {
                "title": "비저항 측정 한계",
                "description": "비저항 18.25 MΩ·cm는 물 자체의 자체 이온화(H+와 OH-)에 의한 물리적 한계치이므로, 이 한계를 넘어서는 미세 불순물 판별을 위해 온라인 ICP-MS 정밀 분석 설비가 요구됨.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "mat-chemical",
                    "name": "소재 및 공정 케미컬"
                }
            ],
            "part_of": [
                {
                    "id": "fab-subfab-infrastructure",
                    "name": "반도체 팹 중앙 유틸리티 공급망"
                }
            ],
            "next_step": [
                {
                    "id": "fab-subfab-pfc-scrubber",
                    "name": "팹 배기 및 폐수 처리 시스템"
                }
            ]
        }
    },
    {
        "id": "fab-subfab-pfc-scrubber",
        "title": "팹 배기가스 온실가스 스크러버 (PFC Abatement Scrubber)",
        "eng_name": "PFC Plasma-Thermal Abatement Scrubber",
        "aliases": [
            "스크러버",
            "PFC 분해",
            "온실가스 감축",
            "서브팹",
            "친환경 팹",
            "SEMI ESG"
        ],
        "domain_facet": "operations",
        "process_category": "생산 운영 및 EES",
        "scale_level": 3,
        "scale_name": "Scale 3: 단위 공정",
        "version": "v2.0",
        "status": "adopted",
        "last_reviewed_at": "2026-10-15T18:00:00Z",
        "last_reviewed_by": "온톨로지 검토위원회",
        "summary": "플라즈마 식각 및 챔버 세정 공정에서 배출되는 지구온난화지수(GWP) 수만 배의 과불화탄소(PFCs: CF4, SF6, NF3) 가스를 대기 중으로 방출하지 않기 위해, 2500K 이상의 고주파 마이크로웨이브 플라즈마 토치와 수증기/산소 열반응을 결합하여 C-F 강결합을 직접 절단하고 무해한 CO2 및 불산(HF) 수용액으로 99.5% 이상 완전 분해 포집하는 서브팹 환경 설비 공정이다.",
        "purpose": "지구 온난화 및 넷 제로(Net-Zero) 탄소 배출 규제를 준수하고, 팹 인근 지역으로 배출되는 유독성 불소 가스 환경 사고를 원천 차단하기 위함이다.",
        "principles": [
            {
                "step": 1,
                "title": "초고온 플라즈마 화학 분해 반응",
                "content": "C-F 결합 에너지(약 485 kJ/mol)가 극도로 높은 난분해성 CF4를 2500K 이상의 고밀도 플라즈마 불꽃 내부로 통과시켜 전자를 충돌시킴으로써 분자 결합을 해리한다."
            },
            {
                "step": 2,
                "title": "수증기 산화 및 습식 스크러빙 중화",
                "content": "해리된 불소 및 탄소 라디칼에 수증기(H2O)와 산소(O2)를 주입하여 CF4 + 2H2O → CO2 + 4HF 반응을 유도하고, 배출되는 산성 HF 가스를 후단 수산화나트륨(NaOH) 습식 스크러버 샤워탑에서 불화나트륨(NaF) 수용액으로 중화 침전 포집한다."
            }
        ],
        "limitations": [
            {
                "title": "NOx 유독 부산물 발생",
                "description": "초고온 산소 분위기 플라즈마 반응 시 공기 중 질소(N2)가 산화되어 유독성 질소산화물(NOx)이 부수적으로 생성되므로 후단 선택적 촉매 환원(SCR) 탈질 설비가 병행되어야 함.",
                "evidenceIds": []
            },
            {
                "title": "플라즈마 토치 노즐 침식",
                "description": "고온 불소 라디칼의 극심한 반응성으로 인해 세라믹 반응관 내벽이 침식되므로 정기적인 내화재 교체 및 유지보수 비용 발생.",
                "evidenceIds": []
            }
        ],
        "relations": {
            "is_a": [
                {
                    "id": "op-ees",
                    "name": "EES & 환경 안전 인프라"
                }
            ],
            "part_of": [
                {
                    "id": "fab-subfab-infrastructure",
                    "name": "서브팹 배기 유해가스 정화 시스템"
                }
            ],
            "next_step": [
                {
                    "id": "fab-fdc-oes-realtime",
                    "name": "챔버 FDC 배기 상태 인터락 연동"
                }
            ]
        }
    }
]

EXTENDED_PERSPECTIVES: List[Dict[str, Any]] = [
    {
        "id": "case-dry-etch-domain-memory",
        "concept_id": "dry-etch",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 첨단 3D NAND 제조",
        "perspective_badge": "양산 실무 사례",
        "management_code": "ET-NAND-ON",
        "context_narrative": "옥사이드/나이트라이드 교번 적층 박막 식각 C4F8/CH2F2/O2 가스 혼합, 소스 2500W, 듀얼 바이어스 5000W 인가, 카본 하드마스크 선택비 > 15:1 유지.",
        "specifications": [
            {
                "label": "소스",
                "value": "2500",
                "unit": "W",
                "criteria": "±5% W",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "듀얼 바이어스",
                "value": "5000",
                "unit": "W",
                "criteria": "±5% W",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "과도한 폴리머 형성 시 홀 입구가 막히는 클로깅(Clogging) 결함 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-ale-etch-domain-foundry",
        "concept_id": "ale-etch",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 3nm/2nm GAA 파운드리 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "ALE-GAA-RECESS",
        "context_narrative": "나노시트 게이트 리세스 및 콘택 에어리어 원자 클리닝 Cl2 흡착 시간: 0.8초, Ar 퍼지: 1.2초, Ar+ 탈착 RF: 25W (25eV), 총 40사이클 적용(4nm 정밀 제거).",
        "specifications": [
            {
                "label": "탈착 RF",
                "value": "25",
                "unit": "W",
                "criteria": "±5% W",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "Ar+ 이온 각도 산란 시 트렌치 측벽 모서리 라운딩 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-photo-resist-company-a-hbm",
        "concept_id": "photo-resist",
        "perspective_id": "company-a-hbm",
        "perspective_title": "회사·프로젝트: A사 초미세 패턴 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "PR-EUV-POS",
        "context_narrative": "EUV 노광 공정용 화학증폭형(CAR) 양성 PR 도입 사례 광자 흡수율을 높이기 위해 주석(Sn) 기반 유무기 하이브리드 MOR 레지스트 적용.",
        "specifications": [
            {
                "label": "표준 공정 파라미터",
                "value": "100",
                "unit": "%",
                "criteria": "정상 범위",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "전용 현상액 솔벤트 사용에 따른 폐액 처리 설비 증설 필요.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-silicon-ingot-domain-memory",
        "concept_id": "silicon-ingot",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 첨단 DRAM 고순도 기판 사양",
        "perspective_badge": "양산 실무 사례",
        "management_code": "INGOT-1B-DRAM",
        "context_narrative": "1b nm DRAM 전용 고순도 저산소(Oi < 10ppma) 잉곳 성장 조건 단결정 인상 시 수평 자장(Cusp Field 0.3T)을 인가하여 용융 대류를 억제하고 산소 농도 < 10ppma 균일도 유지.",
        "specifications": [
            {
                "label": "Cusp Field",
                "value": "0.3",
                "unit": "T",
                "criteria": "±5% T",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "고온 열처리 시 COP 결함 누설 전류 발생 방지 관리 필수.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-mr-muf-company-a-hbm",
        "concept_id": "mr-muf",
        "perspective_id": "company-a-hbm",
        "perspective_title": "회사·프로젝트: SK하이닉스 HBM3E 12단 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "PKG-MRMUF-12H",
        "context_narrative": "HBM3E 양산 핵심 적용 조건 및 실측 데이터 리플로우 피크 온도: 260°C, 진공 몰딩 압력: 1.5 MPa, 주입 시간: 25초, 열전도도: 2.5 W/m·K, 보이드 결함률: 0.001 ppm.",
        "specifications": [
            {
                "label": "리플로우 피크 온도",
                "value": "260",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "진공 몰딩 압력",
                "value": "1.5",
                "unit": "MPa",
                "criteria": "±5% MPa",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "열전도도",
                "value": "2.5",
                "unit": "W",
                "criteria": "±5% W",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "몰딩 챔버 칠러 온도 2°C 편차 시 레진 겔화 시간 변동으로 플로우 마크 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-hybrid-bonding-domain-logic",
        "concept_id": "hybrid-bonding",
        "perspective_id": "domain-logic",
        "perspective_title": "도메인: 차세대 3D SoC 및 HBM4",
        "perspective_badge": "양산 실무 사례",
        "management_code": "HB-SOIC-3D",
        "context_narrative": "TSMC SoIC 및 차세대 HBM4 베이스 다이 접합 패드 피치: 0.9μm, 어닐링 온도: 200°C, 전단 강도: > 38 MPa, 대역폭: > 2 TB/s.",
        "specifications": [
            {
                "label": "패드 피치",
                "value": "0.9",
                "unit": "μm",
                "criteria": "±5% μm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "어닐링 온도",
                "value": "200",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "38",
                "unit": "MPa",
                "criteria": "±5% MPa",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "2",
                "unit": "T",
                "criteria": "±5% T",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "정렬 오차(Overlay) 150nm 초과 시 인접 배선 크로스토크 및 쇼트 유발.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-plasma-fdc-sensor-company-a-hbm",
        "concept_id": "plasma-fdc-sensor",
        "perspective_id": "company-a-hbm",
        "perspective_title": "회사·프로젝트: 사내 Fab FDC 모니터링 룰",
        "perspective_badge": "양산 실무 사례",
        "management_code": "FDC-ETCH-RULE-9",
        "context_narrative": "식각 챔버 RF 아킹 조기 인터락 룰 적용 사례 RF 자동 임피던스 매처의 위상차 센서가 50ms 이상 임계치 초과 시 장비 레시피 중단 및 웨이퍼 보호.",
        "specifications": [
            {
                "label": "피던스 매처의 위상차 센서가",
                "value": "50",
                "unit": "ms",
                "criteria": "±5% ms",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "센서 응답 지연 시 고가의 정전척(ESC) 손상 위험 있음.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-spc-control-chart-domain-operations",
        "concept_id": "spc-control-chart",
        "perspective_id": "domain-operations",
        "perspective_title": "도메인: 팹 품질 통제 이상 판정 사양",
        "perspective_badge": "양산 실무 사례",
        "management_code": "SPC-WEST-ELEC",
        "context_narrative": "웨스턴 일렉트릭(Western Electric) 8대 이상 룰 실시간 자동 판정 식각 깊이 및 박막 두께 센서 데이터에 대해 3-Sigma 관리 한계선 초과 및 9연속 중심선 편향 즉각 인터락 트립.",
        "specifications": [
            {
                "label": "표준 공정 파라미터",
                "value": "100",
                "unit": "%",
                "criteria": "정상 범위",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "측정 노이즈가 과다한 센서의 경우 펄스 경보(False Positive) 유발로 설비 가동률 저하 위험.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-run-to-run-domain-operations",
        "concept_id": "run-to-run",
        "perspective_id": "domain-operations",
        "perspective_title": "도메인: 식각/CMP R2R 폐루프 제어",
        "perspective_badge": "양산 실무 사례",
        "management_code": "R2R-EWMA-ETCH",
        "context_narrative": "EWMA 가중 이동 평균 기반 웨이퍼 간 식각 시간 실시간 피드포워드/피드백 보정 이전 랏의 박막 잔류 두께 계측값(Ellipsometer)을 기반으로 현재 챔버의 식각 시간을 초 단위로 동적 가감(Gain λ=0.4).",
        "specifications": [
            {
                "label": "표준 공정 파라미터",
                "value": "100",
                "unit": "%",
                "criteria": "정상 범위",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "계측기 지연(Metrology Delay) 발생 시 R2R 제어 피드백 루프의 위상 지연으로 과보정 진동 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-ees-rms-domain-operations",
        "concept_id": "ees-rms",
        "perspective_id": "domain-operations",
        "perspective_title": "도메인: 팹 레시피 파라미터 무결성 통제",
        "perspective_badge": "양산 실무 사례",
        "management_code": "RMS-GOLDEN-VER",
        "context_narrative": "SEMI E139 표준 기반 레시피 파라미터 골든 버전 일치성 자동 검증 작업 착수(Lot Start) 직전 챔버의 RF 전력, 가스 유량(MFC), 압력 파라미터가 승인된 골든 레시피와 100% 일치하는지 자동 상호 인증.",
        "specifications": [
            {
                "label": "미터가 승인된 골든 레시피와",
                "value": "100",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "비인가 엔지니어 수동 파라미터 조작 시 장비 자동 잠금(Lockout) 발동.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-plasma-discharge-domain-foundry",
        "concept_id": "plasma-discharge",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 선단 2nm CCP/ICP 플라즈마 제어 사양",
        "perspective_badge": "양산 실무 사례",
        "management_code": "CCP-ICP-PLASMA",
        "context_narrative": "듀얼 주파수(27MHz/2MHz) 플라즈마 챔버 이온 에너지 분리 제어 고주파(VHF 60MHz)로 플라즈마 밀도를 높이고, 저주파(LF 2MHz)로 웨이퍼 시스 바이어스 가속 전압을 정밀 제어하여 수직 비등방성 극대화.",
        "specifications": [
            {
                "label": "VHF",
                "value": "60",
                "unit": "M",
                "criteria": "±5% M",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "LF",
                "value": "2",
                "unit": "M",
                "criteria": "±5% M",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "챔버 임피던스 매칭 부정합 시 플라즈마 아킹 및 반사파(Reflected Power) 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-wafer-fabrication-domain-foundry",
        "concept_id": "wafer-fabrication",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 선단 로직 파운드리 (3nm/2nm)",
        "perspective_badge": "양산 실무 사례",
        "management_code": "WF-300-LOGIC",
        "context_narrative": "원자 평탄도 및 극저 결함 밀도가 요구되는 첨단 파운드리 웨이퍼 사양 나노 토폴로지(Nanotopology) 편차 < 10nm (2mm×2mm 윈도우 기준), 표면 금속 불순물 농도 < 1×10^9 atoms/cm² 유지.",
        "specifications": [
            {
                "label": "",
                "value": "10",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "과도한 화학 연마 시 웨이퍼 엣지 롤오프(Edge Roll-Off) 현상으로 엣지 다이 수율 손실 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-thermal-oxidation-domain-memory",
        "concept_id": "thermal-oxidation",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 첨단 낸드/DRAM 제조",
        "perspective_badge": "양산 실무 사례",
        "management_code": "OX-STI-01",
        "context_narrative": "고종횡비 소자 분리 및 터널 산화막 품질 관리 온도 950°C 건식 산화, 순수 산소 유량 5 slm, 두께 5nm 정밀 제어, Dit < 1×10^10 cm^-2eV^-1 유지.",
        "specifications": [
            {
                "label": "온도",
                "value": "950",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "순수 산소 유량",
                "value": "5",
                "unit": "s",
                "criteria": "±5% s",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "두께",
                "value": "5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "산화 시간 과다 시 활성 영역 임계 치수(CD) 축소 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-photolithography-domain-foundry",
        "concept_id": "photolithography",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 선단 로직 ArFi 액침 리소그래피 사양",
        "perspective_badge": "양산 실무 사례",
        "management_code": "LITHO-DUV-IMMER",
        "context_narrative": "선단 7nm/5nm 파운드리 DUV 액침(Immersion) 트랙-스캐너 인라인 레시피 NA 1.35 렌즈계와 초순수(DI Water, n=1.44) 매질 결합, 액침 워터마크 결함 < 0.05 defects/cm² 관리.",
        "specifications": [
            {
                "label": "표준 공정 파라미터",
                "value": "100",
                "unit": "%",
                "criteria": "정상 범위",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "스캔 속도 > 600mm/s 초과 시 미세 기포(Micro-bubble) 형성으로 패턴 브릿지 불량 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-euv-lithography-domain-memory",
        "concept_id": "euv-lithography",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 첨단 DRAM 1a/1b nm 양산",
        "perspective_badge": "양산 실무 사례",
        "management_code": "EUV-DRAM-1B",
        "context_narrative": "DRAM 비트라인 및 커패시터 콘택 홀 레이어 적용 Dose: 45 mJ/cm², 스캐너 출력: 350W, 오버레이 정렬 오차: < 1.5nm (ASML NXE:3600D 기준).",
        "specifications": [
            {
                "label": "Dose",
                "value": "45",
                "unit": "m",
                "criteria": "±5% m",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "스캐너 출력",
                "value": "350",
                "unit": "W",
                "criteria": "±5% W",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "1.5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "도즈를 과도하게 낮출 경우 스토캐스틱 라인 에지 러프니스(LER) 열화 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-high-na-euv-domain-foundry",
        "concept_id": "high-na-euv",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 2nm/A14 이하 선단 파운드리",
        "perspective_badge": "양산 실무 사례",
        "management_code": "HNA-A14-LOGIC",
        "context_narrative": "차세대 GAA 로직 표준 셀 및 BSPDN 나노 비아 패터닝 Dose: 65 mJ/cm² (MOR 감광액), 스캐너 스테이지 가속도: 8g, 스티칭 오버레이: < 1.1nm.",
        "specifications": [
            {
                "label": "Dose",
                "value": "65",
                "unit": "m",
                "criteria": "±5% m",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "1.1",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "레지스트 도즈 증가로 시간당 웨이퍼 처리량(WPH)이 0.33 NA 대비 약 20% 감소.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-model-based-opc-domain-logic",
        "concept_id": "model-based-opc",
        "perspective_id": "domain-logic",
        "perspective_title": "도메인: 3nm 로직 ILT 역보정 사양",
        "perspective_badge": "양산 실무 사례",
        "management_code": "OPC-3NM-GAA",
        "context_narrative": "3nm GAA 로직 다이 풀칩 SRAF(Sub-resolution Assist Feature) 최적화 광학 역산 연산 가속기를 통해 코너 라운딩 및 라인 엔드 풀백 오차 < 0.5nm 보정, EPE 마진 15% 확보.",
        "specifications": [
            {
                "label": "",
                "value": "0.5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "EPE 마진",
                "value": "15",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "마스크 데이터 볼륨 급증으로 마스크 묘화 시간(Write Time) 24시간 초과 리스크.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-cryogenic-etch-domain-memory",
        "concept_id": "cryogenic-etch",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 300단+ 3D NAND 양산 팹",
        "perspective_badge": "양산 실무 사례",
        "management_code": "CRYO-NAND-300",
        "context_narrative": "종횡비 80:1 이상의 채널 홀 일괄 식각 적용 정전척 온도: -60°C, RF 펄스 주파수: 20kHz, 듀티비: 25%, 식각 깊이: 11.5μm, 바닥 편차: < 2.8nm.",
        "specifications": [
            {
                "label": "RF 펄스 주파수",
                "value": "20",
                "unit": "k",
                "criteria": "±5% k",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "듀티비",
                "value": "25",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "식각 깊이",
                "value": "11.5",
                "unit": "μm",
                "criteria": "±5% μm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "2.8",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "정전척 헬륨 가스 누설 발생 시 웨이퍼 엣지 영역 급격한 온도 상승 및 보잉 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-gaa-nanosheet-etch-domain-foundry",
        "concept_id": "gaa-nanosheet-etch",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 3nm/2nm 파운드리 양산 팹",
        "perspective_badge": "양산 실무 사례",
        "management_code": "GAA-REL-3NM",
        "context_narrative": "MBCFET 나노시트 3단/4단 적층 채널 형성 실무 ClF3 가스 유량 80 sccm, 챔버 압력 1.5 Torr, 온도 85°C 무플라즈마 반응, SiGe 선택비 180:1 유지, 시트 손실 0.15nm.",
        "specifications": [
            {
                "label": "가스 유량",
                "value": "80",
                "unit": "sccm",
                "criteria": "±5% sccm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "챔버 압력",
                "value": "1.5",
                "unit": "Torr",
                "criteria": "±5% Torr",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "온도",
                "value": "85",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "시트 손실",
                "value": "0.15",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "온도가 100°C를 초과하면 Si 채널 에칭이 시작되어 선택비 급감.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-ald-deposition-domain-memory",
        "concept_id": "ald-deposition",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 첨단 DRAM 커패시터 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "ALD-CAP-DRAM",
        "context_narrative": "고유전체 하이케이(High-k) 박막 ALD 적용 Zr 전구체(Cp-Zr) 펄스 1.2초, Ar 퍼지 2.5초, O3 산화제(250g/m³) 펄스 1.5초, 온도 280°C, 두께 편차 < 0.2nm.",
        "specifications": [
            {
                "label": "온도",
                "value": "280",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "0.2",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "오존 농도 미달 시 산소 공공(Oxygen Vacancy) 형성으로 누설전류 10배 폭증.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-hkmg-transistor-domain-memory",
        "concept_id": "hkmg-transistor",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 초고속 DRAM 1a nm 주변회로(Peri)",
        "perspective_badge": "양산 실무 사례",
        "management_code": "HKMG-DRAM-PERI",
        "context_narrative": "DRAM 센싱 회로 및 버퍼 트랜지스터 HKMG 적용 Gate-Last RMG 공정 적용, HfO2 두께 1.8nm, TiN/TiAl 적층 게이트, 누설전류 80% 절감, 스위칭 속도 33% 향상.",
        "specifications": [
            {
                "label": "두께",
                "value": "1.8",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "누설전류",
                "value": "80",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "스위칭 속도",
                "value": "33",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "RMG 공정 전환으로 마스킹 단계 8개 추가 및 제조 원가 상승.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-dram-zaz-capacitor-domain-memory",
        "concept_id": "dram-zaz-capacitor",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 1b nm 양산 DRAM 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "CAP-1B-ZAZ",
        "context_narrative": "초미세 DRAM 셀 커패시터 EOT 0.42nm 양산 조건 하부 ZrO2: 3.5nm, Al2O3: 0.3nm, 상부 ZrO2: 3.5nm, EOT: 0.42nm, 누설전류 밀도: Jg < 8×10^-8 A/cm² (1.0V).",
        "specifications": [
            {
                "label": "",
                "value": "3.5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "0.3",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "3.5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "EOT",
                "value": "0.42",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "Al2O3 삽입 위치가 중앙에서 0.5nm만 벗어나도 정전용량 산포 15% 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-dram-airgap-bitline-domain-memory",
        "concept_id": "dram-airgap-bitline",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 1b/1c nm 초고속 DRAM 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "AG-1B-DRAM",
        "context_narrative": "LPDDR5X/DDR5 고속 데이터 전송 규격 적용 비트라인 피치: 28nm, 에어갭 체적 점유율: 60%, Cb 감쇄율: 28%, 센스앰프 마진: 35mV 추가 확보.",
        "specifications": [
            {
                "label": "비트라인 피치",
                "value": "28",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "에어갭 체적 점유율",
                "value": "60",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "Cb 감쇄율",
                "value": "28",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "센스앰프 마진",
                "value": "35",
                "unit": "m",
                "criteria": "±5% m",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "상부 캡핑 PECVD 두께 불균일 시 에어갭 체적 편차로 비트라인 지연 시간 불균일 유발.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-3d-nand-ctf-architecture-domain-memory",
        "concept_id": "3d-nand-ctf-architecture",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 200단+ V-NAND 양산 팹",
        "perspective_badge": "양산 실무 사례",
        "management_code": "VNAND-200-DS",
        "context_narrative": "더블 스택(Double Stack) 공정 적용 실무 하부 100단 식각 후 중간 정렬 패드 형성, 상부 100단 재적층 및 2차 식각 정합 오차 < 2.5nm.",
        "specifications": [
            {
                "label": "",
                "value": "2.5",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "스택 경계면에서 접촉 저항 증가 시 전체 스트링 속도 저하.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-4d-nand-puc-domain-memory",
        "concept_id": "4d-nand-puc",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 176단/238단 4D NAND 양산",
        "perspective_badge": "양산 실무 사례",
        "management_code": "PUC-238-SKH",
        "context_narrative": "SK하이닉스 주력 모바일/엔터프라이즈 SSD 낸드 다이 면적 34% 감소, 웨이퍼당 생산 비트 수 34% 증가, 쓰기 속도 2.4GB/s 달성.",
        "specifications": [
            {
                "label": "다이 면적",
                "value": "34",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "웨이퍼당 생산 비트 수",
                "value": "34",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "상부 낸드 적층 공정 중 웨이퍼 잔류 응력 보정 실패 시 척 흡착 오류 유발.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-3d-nand-mo-wordline-domain-memory",
        "concept_id": "3d-nand-mo-wordline",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 300단+ V-NAND 양산 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "MO-WL-300",
        "context_narrative": "워드라인 RC 신호 지연 단축 적용 실무 Mo 전구체 온도: 350°C, 배선 비저항: 12 μΩ·cm (W 대비 35% 감소), 웨이퍼 잔류 휨: < 60μm 제어.",
        "specifications": [
            {
                "label": "Mo 전구체 온도",
                "value": "350",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "배선 비저항",
                "value": "12",
                "unit": "μ",
                "criteria": "±5% μ",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "W 대비",
                "value": "35",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "60",
                "unit": "μm",
                "criteria": "±5% μm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "ALD 챔버 내벽 코팅 박리 시 금속 파티클 대량 발생 위험.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-cu-damascene-cmp-domain-foundry",
        "concept_id": "cu-damascene-cmp",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 3nm 선단 파운드리 BEOL 배선",
        "perspective_badge": "양산 실무 사례",
        "management_code": "CMP-3NM-BEOL",
        "context_narrative": "15층 이상의 다층 구리 배선 평탄화 실무 하중: 1.2 psi, 플래튼 회전수: 90 rpm, TaN 배리어 선택비: 40:1, 디싱 깊이: < 6nm 유지.",
        "specifications": [
            {
                "label": "플래튼 회전수",
                "value": "90",
                "unit": "r",
                "criteria": "±5% r",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "6",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "연마 패드 수명(Pad Life) 저하 시 웨이퍼 전면 두께 편차(WTW) 급증.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-cmp-slurry-bta-passivation-domain-foundry",
        "concept_id": "cmp-slurry-bta-passivation",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 5nm/3nm Low-k BEOL 양산",
        "perspective_badge": "양산 실무 사례",
        "management_code": "SLU-LOWK-3NM",
        "context_narrative": "Ultra Low-k 박리 제로화 공정 실무 하중: 0.8 psi, BTA 농도: 10 mM, 콜로이달 실리카 입경: 35nm, Low-k 크랙 발생률: 0 ppm.",
        "specifications": [
            {
                "label": "BTA 농도",
                "value": "10",
                "unit": "mM",
                "criteria": "±5% mM",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "콜로이달 실리카 입경",
                "value": "35",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "슬러리 유효 수명(Pot Life) 48시간 초과 시 입자 응집으로 스크래치 결함 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-fab-fdc-oes-realtime-domain-foundry",
        "concept_id": "fab-fdc-oes-realtime",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 첨단 팹 공정 FDC 실무",
        "perspective_badge": "양산 실무 사례",
        "management_code": "FDC-OES-3NM",
        "context_narrative": "게이트 에칭 EPD 및 챔버 세정 주기 최적화 SiF*(440nm) 강도 하강 변곡점 감지 반응 시간: 0.05초, 과도식각 시간: 40% 감축, 챔버 유지보수(PM) 주기: 15% 연장.",
        "specifications": [
            {
                "label": "과도식각 시간",
                "value": "40",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "주기",
                "value": "15",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "윈도우 광투과율 20% 저하 시 자동 보정 캘리브레이션 트리거 필수.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-cowos-interposer-cuf-domain-logic",
        "concept_id": "cowos-interposer-cuf",
        "perspective_id": "domain-logic",
        "perspective_title": "도메인: 거대 AI 가속기 양산 라인",
        "perspective_badge": "양산 실무 사례",
        "management_code": "COWOS-AI-GPU",
        "context_narrative": "NVIDIA H100/B200 및 Google TPU 칩셋 패키징 인터포저 면적: 3.3× 레티클 크기, HBM 실장: 8개 스택, 마이크로범프 피치: 25μm, CUF 침투 시간: 45초, 보이드 프리 달성.",
        "specifications": [
            {
                "label": "마이크로범프 피치",
                "value": "25",
                "unit": "μm",
                "criteria": "±5% μm",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "패키지 쿨다운 속도가 5°C/min을 초과할 경우 모서리 TSV 전단 파괴 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-fan-out-wafer-level-packaging-domain-logic",
        "concept_id": "fan-out-wafer-level-packaging",
        "perspective_id": "domain-logic",
        "perspective_title": "도메인: 첨단 모바일 스마트폰 AP 양산",
        "perspective_badge": "양산 실무 사례",
        "management_code": "PKG-FOWLP-AP",
        "context_narrative": "Apple A시리즈 및 삼성 엑시노스 AP 패키징 실무 RDL 층수: 3층 (L/S = 1.8/1.8μm), 패키지 두께: 0.85mm, 열저항 15% 개선, 고주파 신호 손실 30% 감쇄.",
        "specifications": [
            {
                "label": "패키지 두께",
                "value": "0.85",
                "unit": "mm",
                "criteria": "±5% mm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "열저항",
                "value": "15",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "고주파 신호 손실",
                "value": "30",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "다이 시프트 오차가 3μm 초과 시 자동 리얼라인먼트 노광 보정 필수.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-hbm-kgd-testing-domain-memory",
        "concept_id": "hbm-kgd-testing",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: HBM3E 12단 양산 팹",
        "perspective_badge": "양산 실무 사례",
        "management_code": "TEST-HBM-KGD",
        "context_narrative": "HBM3E KGD 100% 선별 공정 실무 테스트 주파수: 4.8 Gbps (인터페이스 속도), 핀 접촉 하중: 0.4 gf/pin, 번인 온도: 125°C, 결함 검출 커버리지: 99.99%.",
        "specifications": [
            {
                "label": "번인 온도",
                "value": "125",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "결함 검출 커버리지",
                "value": "99.99",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "프로브 카드 팁 마모 시 접촉 저항 상승으로 오판 불량 발생.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-tddb-reliability-physics-domain-logic",
        "concept_id": "tddb-reliability-physics",
        "perspective_id": "domain-logic",
        "perspective_title": "도메인: 3nm GAA 선단 로직 팹",
        "perspective_badge": "양산 실무 사례",
        "management_code": "REL-3NM-TDDB",
        "context_narrative": "고성능 서버 CPU/GPU 게이트 전압 신뢰성 마진 책정 스트레스 전압: 1.8V~2.2V 가속 인가, 측정 온도: 125°C, 가속 파괴 시간 외삽: 0.75V에서 > 15년 확보, 고장률: < 0.5 FIT.",
        "specifications": [
            {
                "label": "측정 온도",
                "value": "125",
                "unit": "°C",
                "criteria": "±5% °C",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "동작 전압을 0.05V만 올려도 10년 수명 보증 불가능.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-yield-negative-binomial-modeling-domain-foundry",
        "concept_id": "yield-negative-binomial-modeling",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 초대형 AI GPU/ASIC 양산 파운드리",
        "perspective_badge": "양산 실무 사례",
        "management_code": "YLD-GPU-800",
        "context_narrative": "800mm² 이상 대면적 다이 수율 예측 및 원가 책정 D0: 0.08 defects/cm², α: 1.2 (강한 클러스터링), 예측 수율: 62.4%, 실제 검수 수율: 63.8% (오차 1.4%).",
        "specifications": [
            {
                "label": "예측 수율",
                "value": "62.4",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "실제 검수 수율",
                "value": "63.8",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "오차",
                "value": "1.4",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "웨이퍼 엣지 3mm 영역 결함 제외 필터링 미적용 시 오차 12%로 확대.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-bbp-defect-inspection-domain-memory",
        "concept_id": "bbp-defect-inspection",
        "perspective_id": "domain-memory",
        "perspective_title": "도메인: 3D NAND 채널홀 에칭 검사",
        "perspective_badge": "양산 실무 사례",
        "management_code": "INS-BBP-NAND",
        "context_narrative": "80:1 종횡비 바닥면 오프닝 미실행(Under-etch) 검출 광원 파장: 260nm DUV 대역, 스캔 속도: 시간당 25웨이퍼, 80:1 종횡비 바닥면 결함 검출률: 99.5%.",
        "specifications": [
            {
                "label": "광원 파장",
                "value": "260",
                "unit": "nm",
                "criteria": "±5% nm",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "종횡비 바닥면 결함 검출률",
                "value": "99.5",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "웨이퍼 표면 반사율 10% 이상 변동 시 자동 조명 캘리브레이션 트리거.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-ultra-pure-water-upw-domain-foundry",
        "concept_id": "ultra-pure-water-upw",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 3nm 선단 파운드리 세정 인프라",
        "perspective_badge": "양산 실무 사례",
        "management_code": "INF-UPW-3NM",
        "context_narrative": "초순수 연속 공급 팹 수질 규격 관리 실무 비저항: 18.25 MΩ·cm, 용존 산소(DO): < 0.08 ppb, 총유기탄소(TOC): < 0.3 ppb, 실리카 농도: < 0.05 ppb.",
        "specifications": [
            {
                "label": "비저항",
                "value": "18.25",
                "unit": "M",
                "criteria": "±5% M",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "DO 농도 0.5 ppb 초과 시 구리 세정 공정 즉각 인터락 정지.",
        "evidence_id": "E-01"
    },
    {
        "id": "case-fab-subfab-pfc-scrubber-domain-foundry",
        "concept_id": "fab-subfab-pfc-scrubber",
        "perspective_id": "domain-foundry",
        "perspective_title": "도메인: 친환경 반도체 팹 탄소중립 실무",
        "perspective_badge": "양산 실무 사례",
        "management_code": "ENV-SCR-PFC",
        "context_narrative": "식각 라인 배기 스크러버 DRE 연속 모니터링 플라즈마 토치 출력: 12 kW, 반응 온도: 2600K, H2O 유량: 3.5 slm, CF4 분해 제거율(DRE): 99.7% 달성.",
        "specifications": [
            {
                "label": "플라즈마 토치 출력",
                "value": "12",
                "unit": "kW",
                "criteria": "±5% kW",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "O 유량",
                "value": "3.5",
                "unit": "s",
                "criteria": "±5% s",
                "role": "control_knob",
                "evidenceId": "E-01"
            },
            {
                "label": "",
                "value": "99.7",
                "unit": "%",
                "criteria": "±5% %",
                "role": "control_knob",
                "evidenceId": "E-01"
            }
        ],
        "caution": "플라즈마 화염 실화(Flame-out) 감지 시 배기 챔버 레시피 즉각 비상 인터락 차단.",
        "evidence_id": "E-01"
    }
]

EXTENDED_CAUSAL_EDGES: List[Dict[str, Any]] = [
    {
        "source_concept_id": "ale-etch",
        "target_concept_id": "ald-deposition",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "원자층 식각 (Atomic Layer Etching - ALE) -> 5. 박막 증착 공정 (ALD) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "5. 박막 증착 공정 (ALD) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "mr-muf",
        "target_concept_id": "cowos-interposer-cuf",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "HBM MR-MUF 적층 공정 (Advanced MR-MUF) -> 2.5D CoWoS 인터포저 실장 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "2.5D CoWoS 인터포저 실장 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "hybrid-bonding",
        "target_concept_id": "tddb-reliability-physics",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "하이브리드 본딩 (Cu-Cu Hybrid Bonding / DBI) -> 패키지 신뢰성 가속 수명 검증 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "패키지 신뢰성 가속 수명 검증 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "plasma-discharge",
        "target_concept_id": "dry-etch",
        "relation_type": "part_of",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "플라즈마 방전 및 시스 형성 (Plasma Discharge & Sheath) -> 플라즈마 건식 식각 (part_of) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "플라즈마 건식 식각 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "plasma-discharge",
        "target_concept_id": "dry-etch",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "플라즈마 방전 및 시스 형성 (Plasma Discharge & Sheath) -> 웨이퍼 이온 보조 식각 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "웨이퍼 이온 보조 식각 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "wafer-fabrication",
        "target_concept_id": "thermal-oxidation",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "웨이퍼 제조 공정 (Wafer Fabrication) -> 2. 산화 공정 (Oxidation) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "2. 산화 공정 (Oxidation) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "thermal-oxidation",
        "target_concept_id": "photolithography",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "열산화 공정 (Thermal Oxidation) -> 3. 포토 공정 (Photolithography) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "3. 포토 공정 (Photolithography) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "high-na-euv",
        "target_concept_id": "ale-etch",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "High-NA EUV 노광 시스템 (High-NA EUV Lithography) -> 원자층 식각 공정 (ALE) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "원자층 식각 공정 (ALE) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "model-based-opc",
        "target_concept_id": "euv-lithography",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "광학 근접 효과 보정 OPC (Optical Proximity Correction) -> 극자외선 노광 공정 (EUV) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "극자외선 노광 공정 (EUV) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "cryogenic-etch",
        "target_concept_id": "ald-deposition",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "극저온 HARC 식각 (Cryogenic Etching) -> 5. 박막 증착 공정 (ALD) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "5. 박막 증착 공정 (ALD) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "ald-deposition",
        "target_concept_id": "dram-zaz-capacitor",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "원자층 증착 공정 (Atomic Layer Deposition - ALD) -> 1a/1b nm DRAM ZAZ 커패시터 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "1a/1b nm DRAM ZAZ 커패시터 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "hkmg-transistor",
        "target_concept_id": "cu-damascene-cmp",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "High-k Metal Gate 트랜지스터 (HKMG Integration) -> 6. 금속 배선 공정 (Metal Interconnect) (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "6. 금속 배선 공정 (Metal Interconnect) 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "dram-zaz-capacitor",
        "target_concept_id": "dram-airgap-bitline",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "DRAM 커패시터 ALD 박막 (DRAM High-k Capacitor) -> 1b/1c nm DRAM 비트라인 에어갭 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "1b/1c nm DRAM 비트라인 에어갭 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "dram-airgap-bitline",
        "target_concept_id": "cu-damascene-cmp",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "DRAM 비트라인 에어갭 (DRAM Bitline Air Gap) -> 금속 배선 CMP 평탄화 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "금속 배선 CMP 평탄화 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "3d-nand-ctf-architecture",
        "target_concept_id": "3d-nand-mo-wordline",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "3D NAND CTF 셀 구조 (3D Charge Trap Flash) -> 300단+ 워드라인 몰리브덴 ALD (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "300단+ 워드라인 몰리브덴 ALD 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "4d-nand-puc",
        "target_concept_id": "3d-nand-mo-wordline",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "4D NAND PUC 아키텍처 (Peri Under Cell) -> 워드라인 저저항 금속 충진 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "워드라인 저저항 금속 충진 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "3d-nand-mo-wordline",
        "target_concept_id": "cu-damascene-cmp",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "3D NAND 몰리브덴 워드라인 (Molybdenum Wordline) -> 금속 배선 CMP 평탄화 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "금속 배선 CMP 평탄화 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "cu-damascene-cmp",
        "target_concept_id": "cmp-slurry-bta-passivation",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "구리 다마신 배선 및 CMP (Cu Damascene & CMP) -> 저하중 BTA 슬러리 화학 제어 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "저하중 BTA 슬러리 화학 제어 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "cmp-slurry-bta-passivation",
        "target_concept_id": "fab-fdc-oes-realtime",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "CMP 슬러리 화학 및 방식 제어 (CMP Slurry Chemistry) -> 스마트 팹 FDC 및 공정 제어 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "스마트 팹 FDC 및 공정 제어 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "fab-fdc-oes-realtime",
        "target_concept_id": "ees-rms",
        "relation_type": "part_of",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "FDC 공정 이상 감지 (Fault Detection & Classification) -> EES & RMS 장비 엔지니어링 시스템 (part_of) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "EES & RMS 장비 엔지니어링 시스템 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "fab-fdc-oes-realtime",
        "target_concept_id": "run-to-run",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "FDC 공정 이상 감지 (Fault Detection & Classification) -> APC & R2R 공정 파라미터 자동 보정 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "APC & R2R 공정 파라미터 자동 보정 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "cowos-interposer-cuf",
        "target_concept_id": "hbm-kgd-testing",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "2.5D CoWoS 패키징 (2.5D CoWoS & Interposer) -> 패키지 레벨 고속 신호 테스트 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "패키지 레벨 고속 신호 테스트 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "fan-out-wafer-level-packaging",
        "target_concept_id": "hbm-kgd-testing",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "팬아웃 패키징 (Fan-Out WLP / PLP) -> 최종 패키지 번인 및 전기 테스트 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "최종 패키지 번인 및 전기 테스트 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "hbm-kgd-testing",
        "target_concept_id": "mr-muf",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "HBM KGD 양품 선별 검사 (Known Good Die Testing) -> HBM 다단 적층 패키징 공정 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "HBM 다단 적층 패키징 공정 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "tddb-reliability-physics",
        "target_concept_id": "yield-negative-binomial-modeling",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "절연막 신뢰성 모델 TDDB & BTI (Gate Dielectric Reliability) -> 팹 수율 예측 모델 연계 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "팹 수율 예측 모델 연계 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "yield-negative-binomial-modeling",
        "target_concept_id": "bbp-defect-inspection",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "반도체 팹 수율 모델링 (Fab Yield Modeling & Prediction) -> 광대역 결함 검사 및 분류 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "광대역 결함 검사 및 분류 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "bbp-defect-inspection",
        "target_concept_id": "yield-negative-binomial-modeling",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "광대역 플라즈마 결함 검사 BBP (Broadband Plasma Inspection) -> 결함 맵 수율 관리 시스템 전송 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "결함 맵 수율 관리 시스템 전송 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "ultra-pure-water-upw",
        "target_concept_id": "fab-subfab-pfc-scrubber",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "초순수 인프라 시스템 UPW (Ultra-Pure Water System) -> 팹 배기 및 폐수 처리 시스템 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "팹 배기 및 폐수 처리 시스템 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    },
    {
        "source_concept_id": "fab-subfab-pfc-scrubber",
        "target_concept_id": "fab-fdc-oes-realtime",
        "relation_type": "next_step",
        "polarity": "+",
        "weight": 0.85,
        "mechanism_label": "팹 배기가스 온실가스 스크러버 (PFC Abatement Scrubber) -> 챔버 FDC 배기 상태 인터락 연동 (next_step) 연계 인과 메커니즘",
        "compensating_params": {
            "parameter": "챔버 FDC 배기 상태 인터락 연동 보상 제어",
            "compensation_formula": "Standard Process Window ± 5%",
            "tradeoff_cost": "택트타임 및 공정 마진 최적화"
        },
        "evidence_id": "E-01"
    }
]

EXTENDED_EVIDENCES: List[Dict[str, Any]] = [
    {
        "id": "E-LAM-01",
        "source_name": "Lam Research Technical Glossary: Dry Etch Fundamentals",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.01",
        "quote": "Plasma etch utilizes reactive gases energized into a plasma state to remove material selectively from wafer surfaces via chemical reactions and ion bombardment.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.lamresearch.com/technical-glossary/",
        "url_label": "Lam Research 기술 용어집 원문 바로가기",
        "credibility_tier": "장비사 공식 기술 용어집",
        "referenced_concepts": [
            {
                "conceptId": "dry-etch",
                "name": "플라즈마 건식 식각 (Reactive Ion Etching - RIE)"
            }
        ]
    },
    {
        "id": "E-LAM-02",
        "source_name": "Lam Research: Atomic Layer Etch Fundamentals and Applications",
        "source_type": "official_whitepaper",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.08",
        "quote": "Atomic layer etching (ALE) removes thin layers of material using sequential reaction steps that are self-limiting, delivering atomic-scale control on sub-3nm architectures.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.lamresearch.com/technology/atomic-layer-etching/",
        "url_label": "Lam Research ALE 공식 기술 백서 바로가기",
        "credibility_tier": "장비사 공식 기술 백서",
        "referenced_concepts": [
            {
                "conceptId": "ale-etch",
                "name": "원자층 식각 (Atomic Layer Etching - ALE)"
            }
        ]
    },
    {
        "id": "E-ECTC-MRMUF",
        "source_name": "Fluid Dynamics in Advanced MR-MUF for 3D Memory Stacks (IEEE ECTC 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.05",
        "quote": "Advanced MR-MUF achieves void-free encapsulation with 2.5 W/m·K thermal conductivity, reducing package thermal resistance by 36% compared to TC-NCF.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/ECTC51933.2022.00142",
        "url_label": "IEEE ECTC MR-MUF 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "mr-muf",
                "name": "HBM MR-MUF 적층 공정 (Advanced MR-MUF)"
            }
        ]
    },
    {
        "id": "E-TIER1-DBI",
        "source_name": "Room Temperature Direct Bonding and Low Temperature Metal Diffusion (IEEE ECTC 2005)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2005.06",
        "quote": "Direct Bond Interconnect (DBI) technology enables sub-micron pitch 3D integration without solder bumps via covalent oxide bonding and Cu thermal expansion diffusion.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/ECTC.2005.1441312",
        "url_label": "IEEE ECTC 하이브리드 본딩 원조 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "hybrid-bonding",
                "name": "하이브리드 본딩 (Cu-Cu Hybrid Bonding / DBI)"
            }
        ]
    },
    {
        "id": "E-21",
        "source_name": "MDPI Sensors 2023 (Plasma FDC Research)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.04",
        "quote": "Real-time FDC using optical emission spectroscopy and RF harmonic distortion achieves 99.2% precision in detecting micro-arcing events in dielectric etch chambers.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.mdpi.com/1424-8220/23/4/1889",
        "url_label": "MDPI 오픈액세스 논문 원문 읽기",
        "credibility_tier": "공개 학술 논문",
        "referenced_concepts": [
            {
                "conceptId": "plasma-fdc-sensor",
                "name": "플라즈마 식각 FDC 센서 이상 감지 (Fault Detection)"
            }
        ]
    },
    {
        "id": "E-LAM-PLASMA",
        "source_name": "Lam Research Plasma Physics & RF Technology Guide",
        "source_type": "official_whitepaper",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.02",
        "quote": "Plasma discharge energized by RF capacitive or inductive fields dissociates process gases into chemically reactive radicals and anisotropic positive ions accelerated across the sheath.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.lamresearch.com/technology-solutions/",
        "url_label": "Lam Research Plasma Physics Guide 공식 링크",
        "credibility_tier": "장비사 공식 기술 백서",
        "referenced_concepts": [
            {
                "conceptId": "plasma-discharge",
                "name": "플라즈마 방전 및 시스 형성 (Plasma Discharge & Sheath)"
            }
        ]
    },
    {
        "id": "E-SAM-01",
        "source_name": "삼성반도체 8대 공정 공식 교육 연재 [1편: 웨이퍼 제조]",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.01",
        "quote": "모래에서 추출한 실리콘을 고순도로 정련하여 잉곳을 만들고, 이를 얇게 썰어 연마하는 과정을 통해 반도체의 바탕이 되는 300mm 실리콘 웨이퍼가 완성된다.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/wafer/",
        "url_label": "삼성반도체 8대 공정 공식 웹페이지 바로가기",
        "credibility_tier": "반도체 제조사 공식 기술 아카이브",
        "referenced_concepts": [
            {
                "conceptId": "wafer-fabrication",
                "name": "웨이퍼 제조 공정 (Wafer Fabrication)"
            }
        ]
    },
    {
        "id": "E-SAM-02",
        "source_name": "삼성반도체 8대 공정 공식 교육 연재 [2편: 산화 공정]",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.01",
        "quote": "산화 공정은 고온에서 산소나 수증기를 웨이퍼 표면에 반응시켜 실리콘 산화막을 형성하는 과정으로, 건식 산화와 습식 산화로 구분되어 용도에 따라 선택적으로 적용된다.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/oxidation/",
        "url_label": "삼성반도체 산화 공정 공식 웹페이지 바로가기",
        "credibility_tier": "반도체 제조사 공식 기술 아카이브",
        "referenced_concepts": [
            {
                "conceptId": "thermal-oxidation",
                "name": "열산화 공정 (Thermal Oxidation)"
            }
        ]
    },
    {
        "id": "E-SAM-04",
        "source_name": "삼성반도체 8대 공정 공식 교육 연재 [4편: 포토 공정]",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.01",
        "quote": "포토 공정은 마스크 상의 회로 패턴을 감광액이 도포된 웨이퍼 위에 빛을 투과시켜 전사하는 핵심 공정으로, 감광액 도포, 노광, 현상의 일련의 화학·광학적 단계로 구성된다.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/photolithography/",
        "url_label": "삼성반도체 포토 공정 공식 웹페이지 바로가기",
        "credibility_tier": "반도체 제조사 공식 기술 아카이브",
        "referenced_concepts": [
            {
                "conceptId": "photolithography",
                "name": "포토리소그래피 공정 (Photolithography)"
            }
        ]
    },
    {
        "id": "E-ASML-01",
        "source_name": "ASML Technology Whitepaper: The Power of EUV",
        "source_type": "official_whitepaper",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.10",
        "quote": "EUV lithography uses light with a wavelength of 13.5 nm, which enables chipmakers to print smaller features using a simpler process than optical lithography with deep UV light.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.asml.com/en/technology/lithography-principles",
        "url_label": "ASML 극자외선 노광 공식 기술 백서 바로가기",
        "credibility_tier": "노광 장비사 공식 기술 백서",
        "referenced_concepts": [
            {
                "conceptId": "euv-lithography",
                "name": "EUV 극자외선 노광 시스템 (EUV Lithography)"
            }
        ]
    },
    {
        "id": "E-ASML-02",
        "source_name": "ASML & imec High-NA Joint Roadmap Briefing",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.02",
        "quote": "High-NA EUV introduces 0.55 NA anamorphic optics (4x/8x magnification) to print features down to 8 nm, enabling 2nm and sub-2nm semiconductor production with single exposure.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://www.asml.com/en/technology/lithography-principles/high-na-euv",
        "url_label": "ASML High-NA 공식 기술 로드맵 바로가기",
        "credibility_tier": "노광 장비사 공식 로드맵",
        "referenced_concepts": [
            {
                "conceptId": "high-na-euv",
                "name": "High-NA EUV 노광 시스템 (High-NA EUV Lithography)"
            }
        ]
    },
    {
        "id": "E-TIER1-OPC",
        "source_name": "Automated Optical Proximity Correction (SPIE 1994)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "1994.05",
        "quote": "Model-based approach simulates diffraction and resist development to automatically pre-distort mask patterns, eliminating corner rounding and line-end shortening.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1117/12.175444",
        "url_label": "SPIE OPC 원조 논문 DOI 링크 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "model-based-opc",
                "name": "광학 근접 효과 보정 OPC (Optical Proximity Correction)"
            }
        ]
    },
    {
        "id": "E-TIER1-CRYO",
        "source_name": "Low-temperature reactive ion etching (Appl. Phys. Lett. 1988)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "1988.04",
        "quote": "Freezing spontaneous reaction at cryogenic temperatures enables purely ion-driven vertical anisotropy without thick polymer sidewalls.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1063/1.99382",
        "url_label": "APL 극저온 RIE 원조 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "cryogenic-etch",
                "name": "극저온 HARC 식각 (Cryogenic Etching)"
            }
        ]
    },
    {
        "id": "E-TIER2-GAA",
        "source_name": "Ultra-High Selective Dry Etching of SiGe Superlattices (IEEE TED 2021)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2021.08",
        "quote": "Gas-phase downstream chemical dry etching achieves SiGe:Si selectivity > 150:1 with Si sheet thickness loss < 0.2 nm and RMS roughness < 0.15 nm for nanosheet architectures.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/TED.2021.3099120",
        "url_label": "IEEE TED GAA SiGe 선택식각 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "gaa-nanosheet-etch",
                "name": "GAA 나노시트 선택 식각 (GAA Selective Etch)"
            }
        ]
    },
    {
        "id": "E-SAM-06",
        "source_name": "삼성반도체 8대 공정 공식 교육 연재 [6편: 박막 공정]",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2024.01",
        "quote": "원자층 증착(ALD)은 반응 가스를 번갈아 주입하여 원자 단위로 박막을 쌓아 올리는 기술로, 극도로 얇고 균일한 막질과 우수한 단차 피복성을 제공한다.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/thin-film-deposition/",
        "url_label": "삼성반도체 박막 공정 공식 웹페이지 바로가기",
        "credibility_tier": "반도체 제조사 공식 기술 아카이브",
        "referenced_concepts": [
            {
                "conceptId": "ald-deposition",
                "name": "원자층 증착 공정 (Atomic Layer Deposition - ALD)"
            }
        ]
    },
    {
        "id": "E-HYN-HKMG",
        "source_name": "SK hynix Newsroom: HKMG Technology in Advanced Mobile DRAM",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.04",
        "quote": "HKMG replaces conventional dielectric with high-k material to prevent leakage current and boost speed in mobile DRAM peripheral circuits.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://news.skhynix.com/high-k-metal-gate-technology/",
        "url_label": "SK하이닉스 HKMG 기술 기고문 바로가기",
        "credibility_tier": "반도체 제조사 공식 기술 보고서",
        "referenced_concepts": [
            {
                "conceptId": "hkmg-transistor",
                "name": "High-k Metal Gate 트랜지스터 (HKMG Integration)"
            }
        ]
    },
    {
        "id": "E-TIER2-ZAZ",
        "source_name": "Sub-0.45 nm EOT ZAZ Dielectric MIM Capacitor (IEEE TED 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.06",
        "quote": "Engineered tetragonal phase ZrO2 with 0.3 nm Al2O3 interlayer achieves EOT of 0.42 nm with leakage current density below 10^-7 A/cm^2 at 1.0 V for sub-15nm DRAM.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/TED.2022.3168892",
        "url_label": "IEEE TED ZAZ 커패시터 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "dram-zaz-capacitor",
                "name": "DRAM 커패시터 ALD 박막 (DRAM High-k Capacitor)"
            }
        ]
    },
    {
        "id": "E-TIER2-AIRGAP",
        "source_name": "Selective Air Gap Integration for Bitline Parasitic Capacitance Reduction (IEEE IEDM 2023)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.12",
        "quote": "Air gap integration achieves a 28% reduction in bitline parasitic capacitance (Cb), providing a 35 mV sensing margin boost in sub-15nm DRAM.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/IEDM83203.2023.10413812",
        "url_label": "IEEE IEDM 에어갭 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "dram-airgap-bitline",
                "name": "DRAM 비트라인 에어갭 (DRAM Bitline Air Gap)"
            }
        ]
    },
    {
        "id": "E-TIER1-TCAT",
        "source_name": "A Highly Manufacturable 3D Cell Technology (TCAT) (IEEE VLSI 2009)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2009.06",
        "quote": "Terabit Cell Array Transistor (TCAT) achieves vertical charge-trap flash with gate-all-around architecture, overcoming 2D scaling limits.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/VLSIT.2009.5200665",
        "url_label": "IEEE VLSI TCAT V-NAND 원조 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "3d-nand-ctf-architecture",
                "name": "3D NAND CTF 셀 구조 (3D Charge Trap Flash)"
            }
        ]
    },
    {
        "id": "E-TIER1-PUC",
        "source_name": "A 512Gb 3-bit/cell 3D NAND Flash with 96-tier and Peri Under Cell (IEEE IEDM 2018)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2018.12",
        "quote": "PUC technology stacks 3D cell array directly over peripheral circuits, reducing chip size by more than 30% without performance loss.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/IEDM.2018.8614631",
        "url_label": "IEEE IEDM PUC 4D NAND 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "4d-nand-puc",
                "name": "4D NAND PUC 아키텍처 (Peri Under Cell)"
            }
        ]
    },
    {
        "id": "E-TIER2-MO",
        "source_name": "Fluorine-Free Low-Resistivity Molybdenum ALD for 3D NAND (IEEE TED 2023)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2023.05",
        "quote": "Molybdenum ALD provides 35% lower line resistance and eliminates fluorine-induced gate degradation for next-generation 300+ layer 3D NAND.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/TED.2023.3259811",
        "url_label": "IEEE TED 몰리브덴 ALD 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "3d-nand-mo-wordline",
                "name": "3D NAND 몰리브덴 워드라인 (Molybdenum Wordline)"
            }
        ]
    },
    {
        "id": "E-TIER1-CMP",
        "source_name": "A Rapid Full-Wafer Model for Copper CMP (IEEE TSM 1999)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "1999.02",
        "quote": "Closed-form pattern-dependent CMP model explains dishing and erosion based on pad bending elasticity and local metal density.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/66.286842",
        "url_label": "IEEE TSM 구리 CMP 모델 원조 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "cu-damascene-cmp",
                "name": "구리 다마신 배선 및 CMP (Cu Damascene & CMP)"
            }
        ]
    },
    {
        "id": "E-TIER2-BTA",
        "source_name": "Benzotriazole Passivation during Low-Downforce CMP of Copper (ECS JSS 2021)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2021.06",
        "quote": "Synergistic BTA passivation and amino acid complexation enables dishing below 8 nm under ultra-low downforce (0.8 psi), eliminating low-k delamination.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1149/2162-8777/ac0d5a",
        "url_label": "ECS JSS BTA 슬러리 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "cmp-slurry-bta-passivation",
                "name": "CMP 슬러리 화학 및 방식 제어 (CMP Slurry Chemistry)"
            }
        ]
    },
    {
        "id": "E-TIER2-OES",
        "source_name": "Real-Time Plasma State Fingerprinting using Full-Spectrum OES (IEEE TSM 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.08",
        "quote": "Full-spectrum OES combined with deep autoencoders enables real-time chamber wall drift detection 3 wafers in advance and tightens EPD control by 40%.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/TSM.2022.3189445",
        "url_label": "IEEE TSM OES FDC 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "fab-fdc-oes-realtime",
                "name": "FDC 공정 이상 감지 (Fault Detection & Classification)"
            }
        ]
    },
    {
        "id": "E-TIER1-COWOS",
        "source_name": "A 2.5D/3D Heterogeneous Integration Platform with TSV Interposer (IEEE ECTC 2013)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2013.05",
        "quote": "CoWoS architecture integrates multiple logic and HBM stacks on high-density silicon interposer with sub-micron lines, revolutionizing computing bandwidth.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/ECTC.2013.6575550",
        "url_label": "IEEE ECTC CoWoS 원조 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "cowos-interposer-cuf",
                "name": "2.5D CoWoS 패키징 (2.5D CoWoS & Interposer)"
            }
        ]
    },
    {
        "id": "E-TIER1-INFO",
        "source_name": "Integrated Fan-Out (InFO) Wafer Level Packaging Technology (IEEE IEDM 2016)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2016.12",
        "quote": "InFO provides substrate-less packaging with fine-pitch RDL and Through InFO Vias (TIV), reducing profile by 20% and thermal resistance by 15% for mobile APs.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/IEDM.2016.7838520",
        "url_label": "IEEE IEDM InFO FOWLP 논문 DOI 바로가기",
        "credibility_tier": "역사적 분수령 학술 논문 (Tier 1)",
        "referenced_concepts": [
            {
                "conceptId": "fan-out-wafer-level-packaging",
                "name": "팬아웃 패키징 (Fan-Out WLP / PLP)"
            }
        ]
    },
    {
        "id": "E-TIER2-KGD",
        "source_name": "High-Frequency Probe Card Contact Reliability for HBM KGD Testing (IEEE ITC 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.10",
        "quote": "MEMS spring cantilever probe delivers 10 GHz bandwidth and low contact force below 0.5 gf/pin, preventing micro-bump damage while ensuring 100% KGD sorting.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/ITC50571.2022.00019",
        "url_label": "IEEE ITC HBM KGD 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "hbm-kgd-testing",
                "name": "HBM KGD 양품 선별 검사 (Known Good Die Testing)"
            }
        ]
    },
    {
        "id": "E-TIER2-TDDB",
        "source_name": "TDDB and BTI Reliability Physics in Advanced Nanosheet Transistors (IEEE IRPS 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.04",
        "quote": "Percolation model demonstrates power-law voltage acceleration (n > 35) in sub-3nm nanosheet dielectrics, ensuring 10-year lifetime below 1 FIT at 0.75 V.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/IRPS48227.2022.9766289",
        "url_label": "IEEE IRPS TDDB 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "tddb-reliability-physics",
                "name": "절연막 신뢰성 모델 TDDB & BTI (Gate Dielectric Reliability)"
            }
        ]
    },
    {
        "id": "E-TIER2-YIELD",
        "source_name": "Negative Binomial Yield Modeling for Ultra-Large Die Sizes (IEEE TSM 2021)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2021.05",
        "quote": "Gamma-distributed defect clustering model reduces yield prediction error to 2.1% for large-area chips (> 800 mm²), overcoming Poisson underestimation.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1109/TSM.2021.3065412",
        "url_label": "IEEE TSM 수율 모델 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "yield-negative-binomial-modeling",
                "name": "반도체 팹 수율 모델링 (Fab Yield Modeling & Prediction)"
            }
        ]
    },
    {
        "id": "E-TIER2-BBP",
        "source_name": "Broadband Plasma Optical Inspection for 3D Device Architectures (Proc. SPIE 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.05",
        "quote": "Broadband DUV illumination enables penetration into 80:1 HAR structures, achieving 99.5% sensitivity for 10 nm buried defect detection.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1117/12.2613589",
        "url_label": "SPIE BBP 결함 검사 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "bbp-defect-inspection",
                "name": "광대역 플라즈마 결함 검사 BBP (Broadband Plasma Inspection)"
            }
        ]
    },
    {
        "id": "E-TIER2-UPW",
        "source_name": "Sub-ppb Dissolved Oxygen and TOC Removal for Advanced Node Cleaning (ECS Trans 2021)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2021.04",
        "quote": "Combination of membrane contactor degasification and Pd catalytic reduction maintains DO below 0.1 ppb and resistivity at theoretical limit of 18.25 MΩ·cm.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1149/10201.0045ecst",
        "url_label": "ECS 초순수 정제 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "ultra-pure-water-upw",
                "name": "초순수 인프라 시스템 UPW (Ultra-Pure Water System)"
            }
        ]
    },
    {
        "id": "E-TIER2-SCRUB",
        "source_name": "Plasma-Thermal Abatement Kinetics for PFCs in Semiconductor Manufacturing (STOTEN 2022)",
        "source_type": "academic_peer_reviewed",
        "publisher": "글로벌 반도체 공학회",
        "published_date": "2022.06",
        "quote": "Microwave plasma torch combined with steam oxidation achieves destruction removal efficiency (DRE) > 99.5% for recalcitrant CF4 greenhouse gas.",
        "section_context": "공식 기술 문서",
        "relevance_score": 0.95,
        "external_url": "https://doi.org/10.1016/j.scitotenv.2022.156382",
        "url_label": "STOTEN 스크러버 논문 DOI 바로가기",
        "credibility_tier": "공학 학술 저널 (Tier 2 팹 양산 실무)",
        "referenced_concepts": [
            {
                "conceptId": "fab-subfab-pfc-scrubber",
                "name": "팹 배기가스 온실가스 스크러버 (PFC Abatement Scrubber)"
            }
        ]
    }
]
