# SCARA GLB 모델 — RS-450 학습용

| 파일 | 용도 | 크기 |
|---|---|---|
| [`scara_rigged.glb`](scara_rigged.glb) | **학생용 기본 파일.** 관절 노드 계층(joint1~4, finger_*)이 있어 회전·이동으로 자세를 바꿀 수 있다 | 약 2.2 MB |
| [`scara_sceliph_flat.glb`](scara_sceliph_flat.glb) | sceliph가 컴파일한 원본. 부품 31개가 한 층에 놓인 홈 자세 | 약 2.2 MB |
| [`../../model/scara.assembly.json`](../../model/scara.assembly.json) | sceliph AssemblyIR 원본(편집 가능한 선언형 형상) | — |

다운로드: 파일을 누른 뒤 **Download raw file**, 또는 [Releases](https://github.com/djfksjd/robot_study/releases)의 첨부 파일.

![홈 자세](../../media/scara_iso_home.png)

## 규격

- 단위 m, glTF Y-up (Blender는 불러올 때 Z-up으로 바꾼다)
- 홈 자세: θ1 = θ2 = θ4 = 0, d3 = 0, 그리퍼 간격 50 mm. 팔은 +X 방향
- 로봇 좌표(Z-up, mm) `(x, y, z)` ↔ glTF `(x, z, -y) / 1000`

## 관절 노드

| 노드 | 종류 | 축(glTF) | 로봇 좌표 의미 | 한계 | 위치(부모 기준, mm) |
|---|---|---|---|---|---|
| `joint1` | 회전 | +Y | θ1, +Z 반시계 | ±132° | (0, 250, 0) |
| `joint2` | 회전 | +Y | θ2 | ±145° | (250, 0, 0) |
| `joint3` | 이동 | −Y | d3 (아래로 +) | 0~180 mm | (200, 0, 0) |
| `joint4` | 회전 | +Y | θ4 | ±360° | (0, 0, 0) |
| `finger_left_joint` | 이동 | −Z | 로봇 +y 쪽 손가락 | 이동량 = 간격/2 − 25 mm | (0, 0, 0) |
| `finger_right_joint` | 이동 | +Z | 로봇 −y 쪽 손가락 | 이동량 = 간격/2 − 25 mm | (0, 0, 0) |

three.js 예:

```js
robot.getObjectByName('joint1').rotation.y = THREE.MathUtils.degToRad(30);
robot.getObjectByName('joint3').position.y = -0.080;           // d3 = 80 mm
const off = (34 / 2 - 25) / 1000;                              // 간격 34 mm
robot.getObjectByName('finger_left_joint').position.z  = -off;
robot.getObjectByName('finger_right_joint').position.z =  off;
```

TCP(두 패드 중심) 높이: `z = 121 − d3` mm.

## 부품 (31개)

`base__*` 11 · `link1__*` 4 · `link2__*` 7 · `quill__*` 5 · `fingerL__*` 2 · `fingerR__*` 2. 각 부품에 한글 이름·재질 이름·설명이 sceliph IR에 들어 있다.

## 검증

- Khronos glTF Validator 2.0.0-dev.3.10: 두 파일 모두 오류 0, 경고 0, 정보 0
- Blender 5 glTF 가져오기 → 관절 회전·이동으로 자세 변경 → Cycles 렌더 ([`tools/blender_render.py`](../../tools/blender_render.py))
- three.js r179 GLTFLoader로 웹 시뮬레이터에서 픽앤플레이스 실행

## 출처와 한계

sceliph(Apache-2.0) 로컬 엔진으로 컴파일한 **창작 학습용 형상**이다. 특정 제품의 복제나 실측 모델이 아니며 내부 구조(모터·감속기·케이블)는 표현하지 않았다. 충돌 형상·질량 특성은 들어 있지 않다(MuJoCo는 [`sim/mujoco/scara.xml`](../../sim/mujoco/scara.xml)의 단순 도형을 쓴다).
