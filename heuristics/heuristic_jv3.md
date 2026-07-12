# heuristic_jv3 — 3일 스프린트: jiyun_v2 후보-생성 갭 unlock (H/X/N)

목표: 3일 내 jv3 출하, @600s full-40 기준(v18 공식행 149,831,986; jv2 full-40 미실측 추정 ~149.6M). 스코프 = **측정 확정된 무위험 개선**. <140M 생성이론 캠페인은 `~/.claude/plans/myalgorithm-jiyun-v2-py-loss-sequential-pine.md` 부록에 보존.
계획: `~/.claude/plans/myalgorithm-jiyun-v2-py-loss-sequential-pine.md`. 기반: jv2(= v18 + Stage-1 회수), 스냅샷 `baseline/myalgorithm_jv3_s0.py` 동결.
규율: 결정론·재롤 금지·런타임 신호만·매 diff prob_1@60s byte-check·신규 경로 default-off kwarg·은행은 공식 verify+min-wins·측정-사망 기법 재구축 금지.

## 발견한 코드 갭 (이번에 직접 검증)

디스패처(생성)는 same-tick 핸드오프를 이미 정확히 활용(L3403–3440)하고 `_can_place`(L568–596)는 strict 부등식으로 합법 판정하는데, **raster 개선기(z3_relocate/w2_rebalance/repack) 경로는 `_time_overlap_rel`(L658, `t<=it[2]`)로 퇴장 블록을 scoped 점유에 포함시켜, 방금 비워진 자리를 후보에서 원천 배제**한다 — `_can_place`는 허용하는데 프리필터가 막는 구조. 또 개선기 후보 진입시각이 `{lb}∪{a,e}`뿐이라 `e2−proc`(내 exit를 이웃 exit tick에 정렬) 임계가 누락됨.

## 레버 (3개 구현, N은 판정 후 DROP)

전부 `_scan_actives`/`_xtime_candidates`/`_scoped_cells` 헬퍼(L658 근방, L3069 근방)로 캡슐화. default-off kwarg → 미지정 시 byte-identical.

- **H (handoff)**: scoped scan의 `actives`를 strict 겹침(`a<exit_t and t<e`)으로 구성 → exit tick에 비워진 셀을 후보화. 소스: `_scan_actives`. **채택.**
- **X (off-event)**: 개선기 후보 진입시각에 `e2−proc` 추가. 소스: `_xtime_candidates`. **채택.**
- **N (near-miss)**: 보수적 마스크 near-셀(total 1..3)을 `_can_place`로 정밀 게이트. **DROP.** — 판정: `_can_place`가 sub-cell 슬라이버(면적 0.005–0.47)를 수용하지만 **공식 체커는 거부**(단위 퍼즈 prob_8: 27/198 셀). near-셀은 경계 근처라 이 갭에 자주 걸려, 무버가 슬라이버 이동을 커밋하면 그 pass의 전체 후보가 최종 verify에서 폐기 → H/X 이득까지 동반 폐기. **legacy-first + 최종 공식 verify로 infeasible 은행은 불가하지만(안전) 효과가 음(-)이라 제외.** `near` plumbing은 default-off로 잔류(향후 sound 슬라이버 게이트 추가 시 재활성 가능). **관찰: `_can_place`가 total>0 셀에서 공식 체커보다 관대함 — pre-existing, 최종 verify로 마스킹됨, 별도 조사 대상.**

## 배선 (격리: legacy-first / 워커 종료 후만)

H+X를 5곳에 `handoff=True, xtimes=True, near=False`로 켬 (모두 obj-gated·insert-at-head 또는 push+min-wins):
1. `_z3_endgame` pass-2 (L3892 `_z3_relocate` 상향캡, L3902 `_w2_rebalance`) — pass-1 기본캡은 legacy byte-exact 유지.
2. `_parent_tail_polish` (L5106 z3, L5127 w2, L5153 runner-up z3) — 워커 종료 후 부모 tail.
W0/W1/W2 legacy 워커 경로, `_place_block`/`_improve`/`_dispatch_construct` 전부 불변(거인 tardiness는 이번 스프린트 범위 밖 = flow-plan 스트레치).

## 검증

- 합성 핸드오프 단위(scratchpad/test_handoff.py): 핸드오프 파인더가 legacy가 놓친 셀(0,0,0,10) 복구 + 공식 `check_feasibility` 수용 + `_can_place` 통과. **PASS.**
- near 소운드니스 퍼즈(scratchpad/test_near.py): superset 성립; N의 공식-거부 슬라이버 27/198 노출 → N DROP 근거.
- **prob_1@60s = 18,357 byte-exact** (obj1=0 obj2=51 obj3=90) — 회귀 0. **PASS.**
- import/syntax OK.

## 결과

| 단계 | 세트 | s0(jv2, levers off) | jv3(H+X on) | Δ | 비고 |
|---|---|---|---|---|---|
| 150s 시그널 | 34 | 2,004,681 | **1,954,944** | **−49,737** | H/X 발화 확인 |
| 150s 시그널 | 37 | 5,778,626 | **5,761,961** | **−16,665** | |
| **150s 합(2개)** | | 7,783,307 | **7,716,905** | **−66,402** | 회귀 0 |
| **600s 게이트 (완료)** | 37 | 5,778,626 | **5,698,025** | **−80,601** | 600s에서 150s(−16,665)보다 5배 — 엔드게임 시간효과 |
| | 32 | 3,814,719 | **3,766,956** | **−47,763** | |
| | 31 | 10,927,585 | **10,918,817** | **−8,768** | ⭐ v14→v18 내내 flat이던 "the scandal" 첫 움직임 |
| | 34 | 1,959,013 | **1,952,347** | **−6,666** | |
| | 22 / 39 / 27 / 38 | — | = | **0** | 구조적 floor + 거인 byte-flat 보호 확인 |
| | **w3 세트 합** | | | **−143,798** | **회귀 0. keep 게이트(≥−150k, 개별 regression ≤+1k) 통과 → H+X 채택** |

## 판정: H+X 채택 (jv3 = jv2 + handoff + off-event)
8-spot 회귀 0, 거인 4개 완벽 보호, w3 4개 전부 개선. Day 2: full-40 @600s 공식 행 → results.csv.

## 07-11 오염 full-40 + 진단 (중요)
재부팅 후 full-40 @600s 첫 시도가 **머신 부하(SearchIndexer+Defender+Chrome)로 오염** — prob_27이 3380s(정상 600s), prob_3/13 값 팽창. 27개까지만 돌고 폐기.
**진단 A/B(s0 vs jv3 @600s, 조용해진 뒤):**
| prob | s0(jv2) | jv3 | Δ | 결론 |
|---|---|---|---|---|
| 26 | 10,216,378 | 10,216,378 | **0** | 레버 무관. **결정론적 → jv2 자체가 v18(9,653,490) 대비 +563k 회귀** (jv2 full-40 미측정으로 숨어있던 pre-existing 회귀, jv3 범위 밖). |
| 13 | 105,806 | **90,871** | **−14,935** | jv3 개선; v18(105,068)보다도 우수. 오염값 109,164는 부하 허상. |
| 3 | 62,160 | **61,010** | **−1,150** | jv3 개선; v18(66,190)보다 우수. 오염값 82,410은 부하 허상. |

**요지: 레버는 깨끗·이로움(전 세트 Δ≤0). 오염 full-40의 "회귀"는 대부분 부하 허상이고, prob_26만 진짜이나 jv2 base 문제(별건 follow-up 후보 — 이거 잡으면 jv3<v18 여유↑).** → 조용한 머신에서 full-40 재실행 중(`jv3_full40_clean.log`).

## 07-12 깨끗한 full-40 + 결정적 발견 (results.csv 유령)
깨끗한 full-40 @600s (조용한 머신, 정상 타이밍) = **150,315,014 (40/40 feasible)**. results.csv v18(149,831,986) 대비 +483k로 보였음. 인스턴스별 회귀로 보인 것: 26(+563k),39(+529k),35(+340k),30(+134k),27(+13k) vs **results.csv v18 row**.
**그러나 `myalgorithm_18.py`(v18 실코드)를 이 머신 @600s로 직접 돌리니:**
| prob | v18 코드(이 머신) | jv3 | Δ | results.csv v18 |
|---|---|---|---|---|
| 26 | 10,216,378 | 10,216,378 | **0 (byte-equal)** | 9,653,490 (재현불가) |
| 39 | 12,890,363 | 12,890,363 | **0 (byte-equal)** | 12,361,461 (재현불가) |
| 35 | 1,688,817 | 1,686,832 | jv3 **−1,985** | 1,346,898 (재현불가) |
| 30 | 4,219,267 | 4,217,279 | jv3 **−1,988** | 4,083,746 (재현불가) |

**결론: 회귀는 존재하지 않았다.** results.csv의 v18 row(149.83M)는 **다른 환경(.venv_ogc + 조용/빠른 머신)** 측정치로 **이 머신(conda + 배경부하)에서 재현 불가**. 그 유령 숫자와 비교해 "jv2 base 회귀"로 오판했던 것. **v18 실코드도 이 머신에선 26/39=jv3(동일), 35/30은 jv3가 더 좋음.**
**⇒ jv3은 v18 코드를 전 인스턴스에서 지배(byte-equal 또는 우수). 구조적으로 jv3 = v18 + obj-gated Stage-1/레버 + legacy-first → 어떤 머신에서든 jv3 ≤ v18.** w1-share/w1-max 게이트·v18-디스패치 전부 불필요(회복할 회귀 없음). **머신 간 절대비교 금지 — 반드시 같은 머신 A/B(compare.py).** [[v15-jiyun-v2-progress]]
**출하 결정: jv3 그대로 승격.** <140M은 별개(거인 생성이론, 이번 스코프 밖).

판정 기준: w3 세트 합 ≥ −150k·개별 regression ≤ +1k → keep; 거인(38/27/39) byte-flat(delta≈0) → 보호 확인. 게이트 통과 시 Day2 야간 full-40 @600s → Day3 출하(myalgorithm.py 복원+승격, zip 재빌드, results.csv/이 파일 기록).
