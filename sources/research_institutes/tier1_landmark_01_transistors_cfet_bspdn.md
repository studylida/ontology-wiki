---
title: "Tier 1 Landmark Papers: Transistor Architecture (FinFET, HKMG, GAA, CFET, BSPDN)"
publisher: "IEEE IEDM, UC Berkeley, Intel, IBM, imec"
source_id: "tier1_landmark_01_transistors_cfet_bspdn"
tier: "Tier-1 Landmark Milestone"
---

# Tier 1 Landmark Papers: Transistor Architecture Evolution

반도체 트랜지스터 구조를 평면(2D)에서 입체(3D) 및 수직 적층(CFET/BSPDN)으로 진화시킨 5대 기념비적 논문 아카이브이다.

---

### [LM-01] FinFET의 기원 (1999 IEDM)
- **논문명**: *FinFET: A Self-Aligned Double-Gate MOSFET Scalable to 20 nm*
- **저자/기관**: D. Hisamoto, W-C. Lee, J. Kedzierski, H. Takeuchi, K. Asano, C. Kuo, E. Anderson, T-J. King, J. Bokor, Chenming Hu (UC Berkeley)
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 1999), DOI: 10.1109/IEDM.1999.826877
- **해결한 물리적 한계**: 
  - 게이트 길이가 20nm 이하로 줄어들 때 평면 벌크 실리콘에서 발생하는 드레인 유도 장벽 감소(DIBL, Drain-Induced Barrier Lowering) 및 단채널 누설 전류를 채널의 좌우 양면을 감싸는 수직 핀(Fin) 구조로 억제.
- **정량 실측 데이터**: 
  - 서브스레숄드 스윙(Subthreshold Swing, SS) $70\text{ mV/dec}$에 근접한 이상적 스위칭 특성 실증, 오프 전류(Off-state leakage) 3자릿수 이상 감소.
- **산업적 파급 효과**: 2011년 인텔 22nm Ivy Bridge 상용화를 시작으로 TSMC, 삼성전자 16nm~3nm 전 세계 파운드리 양산 표준이 됨.

---

### [LM-02] High-k Metal Gate (HKMG) 최초 양산 실증 (2007 IEDM)
- **논문명**: *A 45nm Logic Technology with High-k+Metal Gate Transistors, Strained Silicon, 9 Cu Interconnect Layers, 193nm Dry Patterning, and 100% Lead-free Packaging*
- **저자/기관**: K. Mistry, C. Allen, C. Auth, B. Beattie, P. Fischer, et al. (Intel Corporation)
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 2007), DOI: 10.1109/IEDM.2007.4418934
- **해결한 물리적 한계**:
  - $SiO_2$ 게이트 절연막 두께가 1.2nm(원자 5개 층) 이하로 얇아지면서 양자역학적 직접 터널링 누설 전류가 폭발하여 칩 전력 소모와 발열이 급증하던 문제.
- **공학적 해결책 및 소재**:
  - 하프늄 기반 고유전율 유전체($\text{HfO}_2$, $\kappa \approx 20\sim 25$)를 도입하여 물리적 두께는 두껍게 유지하면서 등가 산화막 두께(EOT)를 1nm 이하로 축소.
  - 폴리실리콘 게이트 고갈(Depletion) 현상을 제거하기 위해 금속 게이트(Metal Gate) 전극 적용.
- **정량 실측 데이터**: 게이트 누설 전류 25배 이상 감소, 드라이브 전류(Drive current) 20% 이상 향상.

---

### [LM-03] GAA (Gate-All-Around) 적층 나노시트 최초 실증 (2017 IEDM)
- **논문명**: *Stacked Nanosheet Gate-All-Around Transistor to Enable Scaling Beyond FinFET*
- **저자/기관**: N. Loubet, T. Hook, P. Montanini, C-W. Yeung, et al. (IBM Research Alliance: IBM, Samsung, GlobalFoundries)
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 2017), DOI: 10.1109/IEDM.2017.8268482
- **해결한 물리적 한계**:
  - 5nm 이하 노드에서 핀(Fin) 폭이 5nm 이하로 얇아짐에 따른 표면 거칠기 산란(Surface roughness scattering) 및 구동 전류 감소 딜레마.
- **공학적 해결책 및 공정**:
  - $Si / Si_{0.7}Ge_{0.3}$ 초격자(Superlattice)를 에피택시 성장시킨 후, 고선택비 등방성 식각(Selective Isotropic Etch)으로 SiGe만 제거하여 수직으로 분리된 3장의 실리콘 나노시트를 형성하고 게이트가 4면을 완전히 포위.
- **정량 실측 데이터**: 핀펫 대비 채널 폭 조절 자유도 확보, 동일 풋프린트에서 구동 전류 30% 증가, 작동 전압(Vdd) 75mV 감소.

---

### [LM-04] Complementary FET (CFET) 최초 3D 적층 실증 (2018/2020 IEDM)
- **논문명**: *First Demonstration of 3D Complementary Field Effect Transistors (CFET) for Sub-3nm Technology Node* / *CFET Architecture for Scaled Logic*
- **저자/기관**: J. Ryckaert, P. Schuddinck, P. Weckx, et al. (imec)
- **학회/발표**: IEEE IEDM 2018 / 2020
- **해결한 물리적 한계**:
  - 표준 셀(Standard Cell) 내에서 nMOS와 pMOS 트랜지스터 사이의 격리 거리(n-to-p separation)로 인해 트랙 높이(Track Height)를 5T 이하로 줄일 수 없는 면적 병목.
- **공학적 해결책**:
  - nMOS 위에 pMOS(또는 반대)를 수직으로 포개어 올려 n-to-p 수평 이격 공간을 0으로 제거.
- **정량 실측 데이터**: 인버터(INV) 및 SRAM 셀 면적 **50% 절감**, 표준 셀 높이 **4T 및 3.5T 달성**, Sub-1nm(A7/A5) 핵심 아키텍처로 채택.

---

### [LM-05] Backside Power Delivery Network (BSPDN) 실증 (2021 IEDM)
- **논문명**: *Enabling Sub-2nm Nodes with Backside Power Delivery Networks (BSPDN)*
- **저자/기관**: A. Veloso, K. Devriendt, S. Demuynck, et al. (imec)
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 2021)
- **해결한 물리적 한계**:
  - 전면 배선(BEOL)에서 미세 구리 배선의 저항 증가와 전자이동(EM) 한계로 인해 트랜지스터로 공급되는 전압이 깎이는 **IR Drop(전압 강하)** 및 신호선과의 라우팅 과밀.
- **공학적 해결책 및 공정**:
  - 전면 공정 완료 후 캐리어 웨이퍼에 본딩, 웨이퍼 후면을 수 마이크로미터 두께로 극박 연마(Grinding/CMP)한 뒤, 후면에서 마이크로/나노 TSV(nTSV)를 뚫어 트랜지스터 하부의 매몰 전력 레일(BPR, Buried Power Rail)로 직접 전원 연결.
- **정량 실측 데이터**: 전압 강하(IR Drop) **30% 이상 감소**, 표준 셀 면적 **16~20% 축소**, 배선 저항 및 기생 커패시턴스 대폭 감소.
