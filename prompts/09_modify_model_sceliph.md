# 09 · Lab 8 (심화) — 모델 치수를 바꿔 GLB 다시 만들기

목표: 치수 하나(예: L2)를 바꾸고, **모델(GLB)·기구학·MuJoCo·웹 시뮬레이터가 모두 같이 바뀌는지** 확인한다. 단일 기준값 파일([`model/scara_params.json`](../model/scara_params.json))의 의미를 체험한다.

필요한 것: Node.js 20.19+, Python 3.10+, git. (AI 챗만으로는 GLB 컴파일을 할 수 없으므로 로컬 PC가 필요하다. 강사가 시연만 해도 된다.)

## 파이프라인

```text
scara_params.json ─▶ model/build_scara_ir.py ─▶ scara.assembly.json (sceliph AssemblyIR)
                                                     │  sceliph: scripts/export-assembly-glb.ts
                                                     ▼
                                          scara_sceliph_flat.glb  (부품 31개, 평면 구조)
                                                     │  tools/rig_scara_glb.mjs
                                                     ▼
                                          scara_rigged.glb  (관절 계층) ─▶ docs/ 웹 시뮬레이터
scara_params.json ─▶ sim/mujoco/build_mjcf.py ─▶ scara.xml (MuJoCo)
scara_params.json ─▶ python/scara_kinematics.py (FK/IK)
```

## ▶ 프롬프트 9-1 · IR 이해

[`model/build_scara_ir.py`](../model/build_scara_ir.py)의 `comp(...)` 몇 개와 [`model/scara.assembly.json`](../model/scara.assembly.json)의 부품 하나를 붙여넣는다.

```text
아래는 sceliph AssemblyIR(morphloom.assembly/0.1) 로 SCARA 부품을 선언한 코드와 결과다.
1) roundedBox / cylinder / extrude / lathe 가 각각 어떤 모양인지
2) IR 좌표는 Y-up mm 인데 로봇 좌표는 Z-up 이다. ir_pos() 함수가 하는 변환을 설명해 줘
3) 부품 id 앞부분(base__, link1__ ...)이 리깅에서 어떤 역할을 하는지
4) 링크 단면을 만드는 slot() 함수의 외접선 각도 phi = asin((r0-r1)/d) 를 그림으로 설명해 줘

<<코드 붙여넣기>>
```

## ▶ 프롬프트 9-2 · 치수 변경 계획

```text
L2 를 200 → 230 mm 로 늘리려고 한다. 저장소 구조는 위 파이프라인과 같다.
1) 고쳐야 하는 파일은 scara_params.json 하나뿐인지, 아니면 다른 곳에 하드코딩된 숫자가 있을 수 있는지 확인하는 방법 (grep 명령 포함)
2) 다시 실행할 명령 순서
3) 바뀐 뒤 확인할 것: 작업 영역 반경, tray 위치가 여전히 도달 가능한지, 웹 시뮬레이터 동작, MuJoCo PASS
```

## 실행 명령 (로컬)

```bash
# 1) sceliph 엔진 준비 (한 번)
git clone https://github.com/djfksjd/sceliph.git ../sceliph && (cd ../sceliph && npm install)

# 2) 값 바꾸기: model/scara_params.json 의 "L2": 230

# 3) 다시 만들기
python3 model/build_scara_ir.py
(cd ../sceliph && npx vite-node scripts/export-assembly-glb.ts -- \
    --ir "$OLDPWD/model/scara.assembly.json" --out "$OLDPWD/models/scara/scara_sceliph_flat.glb")
(cd tools && npm install && npm run rig)
tools/sync_docs.sh
python3 sim/mujoco/build_mjcf.py
python3 python/test_scara_kinematics.py
python3 sim/mujoco/pick_place.py   # mujoco 설치 필요: pip install mujoco
```

`scripts/build_all.sh`가 2)를 뺀 나머지를 한 번에 한다.

## ▶ 프롬프트 9-3 · 형상 수정 요청 (IR 편집)

```text
build_scara_ir.py 에서 그리퍼 손가락을 지금(24x10x50 mm)보다 길게(70 mm) 바꾸고 싶다.
손가락 끝과 패드 아래 끝이 같은 높이를 유지해야 하고, TCP(패드 중심) 높이 tcp_z_at_d0 도 같이 바뀌어야 한다.
고쳐야 할 줄과 새 tcp_z_at_d0 값을 계산 과정과 함께 알려 줘. 아래가 현재 코드다.

<<fingers 부분 코드 붙여넣기>>
```

✔ 확인: GLB를 다시 만든 뒤 웹 시뮬레이터에서 픽앤플레이스가 그대로 성공하는가? (실패하면 TCP 높이 불일치를 의심한다)
