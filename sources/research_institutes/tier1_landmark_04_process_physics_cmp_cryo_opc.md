# Tier 1 분수령 논문 아카이브 04: 공정 물리, 식각 & 리소그래피 수율 물리학 (Process Physics, Etch & Litho Yield)

> 본 문서는 반도체 단위 공정(평탄화, 플라즈마 식각, 광학 왜곡 보정, 극자외선 확률론)의 물리적 지배 방정식과 수율 모델을 정립한 역사적 분수령(Landmark) 논문들의 서지 정보와 공학적 핵심 원리를 수록합니다.

---

## 1. Cu CMP 디싱(Dishing) 및 침식(Erosion) 지배 모델 (1994 / 1999)

### [서지 정보]
- **논문명 1:** Advances in Mathematically Modeling of Chemical-Mechanical Polishing for Wafer Planarization
- **논문명 2:** A Rapid Full-Wafer Pattern-Dependent CMP Model for Oxide and Copper CMP
- **저자:** S. R. Runnels (1994) / Brian E. Stine, Duane S. Boning et al. (MIT, 1999)
- **학회/저널:** IEEE Transactions on Semiconductor Manufacturing / Journal of The Electrochemical Society
- **연도:** 1994 / 1999
- **DOI:** 10.1109/66.286842 / 10.1149/1.1392607

### [역사적 배경 및 산업 패러다임 전환]
- **문제점:** 다마신(Damascene) 구리 배선 공정에서 연마(Polishing) 시 연질인 구리와 경질인 산화막(SiO2)/배리어 메탈(Ta/TaN) 간의 연마 속도 차이로 인해, 구리 배선 중앙부가 움푹 파이는 디싱(Dishing)과 고밀도 배선 영역의 절연막이 과도하게 깎여나가는 침식(Erosion)이 발생하여 배선 저항 폭증 및 단선 유발.
- **돌파구:** 프레스턴 법칙($\text{MRR} = K_p \cdot P \cdot V$)을 국소 영역(Pattern density)과 패드 탄성 변형(Pad elasticity)의 유체역학적 상호작용으로 확장한 닫힌 형태(Closed-form)의 해석적 모델 제시.

### [물리적/공학적 핵심 원리]
1. **패드 굽힘 모델 (Pad Bending Model):**
   - 연마 패드는 일정한 탄성 계수($E$)를 가지며, 폭이 넓은 Cu 배선(예: $> 10\ \mu\text{m}$) 상부에서는 패드가 휘어져 들어가 아래쪽 구리를 지속 연마함.
   - 디싱 깊이 $D$는 배선 폭 $W$와 유효 압력 $P$에 비례:
     $$D(W) \approx \frac{P \cdot W^4}{384 \cdot E \cdot I_{\text{pad}}}$$
2. **패턴 밀도 효과 (Pattern Density Dependency):**
   - 유효 압력 $P_{\text{eff}} = P_0 / \rho$ (여기서 $\rho$는 국소 구리 면적 밀도).
   - 밀도가 낮은 영역은 돌출부에 압력이 집중되어 연마율이 급증하고, 밀도가 균일하지 않으면 칩 전체 두께 편차가 발생.
3. **더미 메탈(Dummy Metal Fill) 삽입 규칙 정립:**
   - 본 논문의 모델을 통해 EDA 툴에서 CMP 이전에 금속 밀도를 $20\%\sim 80\%$ 범위 내로 균일하게 맞추는 자동 더미 패턴 생성 알고리즘이 탄생함.

---

## 2. 극저온 반응성 이온 식각 (Cryogenic RIE) 원조 논문 (1988)

### [서지 정보]
- **논문명:** Low-temperature reactive ion etching and its mechanism
- **저자:** Shinichi Tachi, Kazunori Tsujimoto, Sadayuki Okudaira (Hitachi Central Research Lab)
- **학회/저널:** Applied Physics Letters
- **연도:** 1988
- **권/호/페이지:** Vol. 52, No. 14, pp. 1159–1161
- **DOI:** 10.1063/1.99382

### [역사적 배경 및 산업 패러다임 전환]
- **기존 상온 식각의 한계:** 수평 방향의 자발적 화학 반응(Spontaneous chemical etching)을 막기 위해 탄화불소(Fluorocarbon) 중합막(Polymer)을 측벽에 두껍게 증착시켜야 했으며, 이는 미세 피치에서 보잉(Bowing), 클로깅(Clogging), 잔류물 오염을 유발함.
- **돌파구:** 기판 온도를 극저온($-100^\circ\text{C}\sim -130^\circ\text{C}$)으로 낮추어 자발적 화학 식각의 아레니우스 활성화 에너지를 동결시킴으로써, 폴리머 증착 없이도 순수 이온 충돌(Ion-assisted directionality)만으로 원자 수준의 수직 이방성(Vertical Anisotropy)을 달성함.

### [물리적/공학적 핵심 원리]
1. **아레니우스 반응 속도 동결:**
   $$k = A \exp\left(-\frac{E_a}{k_B T}\right)$$
   온도 $T$가 $300\ \text{K}$에서 $150\ \text{K}$로 감소함에 따라 수평 방향 중성 라디칼(F)의 실리콘 자발 반응 속도 $k$가 4자리수 이상 급감.
2. **극저온 이온 유도 반응 (Ion Activation Only):**
   - 수평 측벽은 반응하지 않고 보호막 없이 보존되며, 수직 바닥면만 입사하는 고에너지 이온에 의해 반응 장벽이 극복되어 선택적으로 에칭됨.
3. **마이크로 로딩 및 잔류물 제로:**
   - 무거운 폴리머 프리커서를 첨가하지 않고 단순 할로겐 가스($\text{SF}_6/\text{O}_2$)만으로 에칭하므로, 부산물 탈착 속도가 제어되어 결함률이 극소화됨.

### [현대적 부활]
- 300단 이상 3D NAND의 $80:1$ 초고종횡비(HAR) 채널홀 식각 공정에서 Lam Research 및 삼성전자/SK하이닉스가 극저온 식각 장비를 주력으로 도입하는 기술적 모태가 됨.

---

## 3. 모델 기반 광학 근접 효과 보정 (Model-based OPC) 원조 논문 (1994)

### [서지 정보]
- **논문명:** Automated Optical Proximity Correction: A Rules-Based versus Model-Based Approach
- **저자:** Oberdan W. Otto, Joseph G. Garofalo, K. K. Low et al.
- **학회:** SPIE 2197, Optical/Laser Microlithography VII
- **연도:** 1994
- **DOI:** 10.1117/12.175444

### [공학적 핵심 원리 및 영향]
- **광학 회절에 의한 왜곡 모델링:** 빛의 회절 한계로 인해 마스크의 직각 모서리가 둥글어지거나(Corner rounding), 미세 라인의 끝단이 짧아지는(Line-end shortening) 현상을 호프킨스 부분 결맞음 광학 방정식(Hopkins partially coherent formulation)을 고속 컨볼루션(Convolution) 연산으로 풀어냄.
- **역보정(Inverse correction):** 왜곡될 패턴의 반대 형상(Serif, Hammerhead, Assist feature)을 마스크에 자동 역산하여 배치함으로써, 레지스트 위에 원래 목표했던 정확한 직사각형 패턴이 전사되도록 확립.
- **현대 영향:** 전 세계 EDA 마스크 합성(Mask Synthesis) 소프트웨어(Synopsys Proteus, Siemens Calibre)의 근간 알고리즘이 됨.

---

## 4. 극자외선(EUV) 확률적 결함(Stochastic Defect) 물리학 (2018)

### [서지 정보]
- **논문명:** Fundamental Principles of EUV Photoresists: Extreme Ultraviolet Stochastics
- **저자:** Chris A. Mack
- **저널:** Journal of Micro/Nanolithography, MEMS, and MOEMS (JM3)
- **연도:** 2018
- **권/호/페이지:** Vol. 17, No. 3, 033501
- **DOI:** 10.1117/1.JMM.17.3.033501

### [물리적/공학적 핵심 원리]
1. **광자 샷 노이즈(Photon Shot Noise)와 광자 결핍:**
   - EUV 광자 1개의 에너지는 $91.8\ \text{eV}$로, ArF($6.4\ \text{eV}$) 대비 약 14배 큼.
   - 동일한 노광 도즈($\text{mJ/cm}^2$)에서 도달하는 광자 수($N$)가 $1/14$로 급감하여 포아송 분포에 따른 광자 수 변동($\sigma / \mu = 1/\sqrt{N}$)이 극심해짐.
2. **확률적 결함 메커니즘 (Nano-bridging & Line-breaking):**
   - 국소 영역에서 우연히 광자가 적게 도달하면 광산발생제(PAG) 활성화가 부족해 레지스트가 안 녹아 브릿지(Micro-bridge) 불량이 발생하고, 우연히 많이 도달하면 과노광되어 라인이 끊어지는(Broken line) 핀홀 결함 발생.
3. **EUV 수율의 수학적 제약 정립:**
   - 피치가 $30\ \text{nm}$ 이하로 줄어들 때 포톤 스토캐스틱 결함 밀도가 지수함수적으로 증가함을 입증하여, 산업계가 무조건적인 도즈 감축(생산성 위주)에서 벗어나 고감도 금속 산화물 레지스트(MOR) 및 High-NA 도입으로 선회하게 만든 이론적 기초.
