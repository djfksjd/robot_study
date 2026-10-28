# 02 · Lab 1 — GLB 모델 열어 보기

목표: `scara_rigged.glb`를 내려받아 열고, 관절 노드 계층(`joint1 → joint2 → joint3 → joint4 → finger_*`)을 직접 확인한다.

## 준비

1. GLB 내려받기: [models/scara/scara_rigged.glb](../models/scara/scara_rigged.glb) → 오른쪽 위 **Download raw file**
   (또는 저장소 [Releases](https://github.com/djfksjd/robot_study/releases)에서 받기)
2. 여는 방법 (하나만 고르면 된다)
   - 설치 없음: <https://gltf-viewer.donmccurdy.com/> 에 파일을 끌어다 놓기
   - 설치 없음: 웹 시뮬레이터 <https://djfksjd.github.io/robot_study/>
   - Blender 4.x 이상: File → Import → glTF 2.0

## ▶ 프롬프트 2-1 · glTF 기초

```text
glTF/GLB 파일 형식을 로봇 실습 관점에서 설명해 줘.
1) node, mesh, material, scene 이 각각 무엇인지
2) node의 translation/rotation/scale 과 부모-자식 계층이 로봇 관절과 어떻게 연결되는지
3) glTF는 Y-up, 단위 m 이 기본이다. 로봇 좌표 Z-up(mm)과 어떻게 바꾸는지 식으로
   (우리 저장소 규칙: 로봇 (x, y, z) -> glTF (x, z, -y))
```

✔ 확인: 변환식이 `glTF = (x, z, -y)`, 역변환이 `로봇 = (x_g, -z_g, y_g)` 인지 직접 확인한다.

## ▶ 프롬프트 2-2 · 계층 읽기

Blender 아웃라이너나 뷰어의 Scene 트리를 캡처하거나 아래 텍스트를 붙여넣는다.

```text
아래는 scara_rigged.glb 의 노드 계층이다. 
1) 어떤 노드가 회전 관절이고 어떤 노드가 직동(이동) 관절인지 표로 정리해 줘.
2) joint2 의 회전을 바꾸면 움직이는 부품 목록은?
3) 왜 base_link 는 joint1 의 자식이 아니라 형제(sibling)여야 하는지 설명해 줘.

scara_root
  base_link (base__plate, base__column, base__j1_housing, ...)
  joint1  t=(0, 250, 0) mm
    link1__body, link1__band, link1__j2_ring, link1__j1_cap
    joint2  t=(250, 0, 0)
      link2__body, link2__head, link2__spline_housing, ...
      joint3  t=(200, 0, 0)
        joint4  t=(0, 0, 0)
          quill__shaft, quill__flange, quill__gripper_body, ...
          finger_left_joint  -> fingerL__finger, fingerL__pad
          finger_right_joint -> fingerR__finger, fingerR__pad
```

## ▶ 프롬프트 2-3 · Blender에서 자세 바꾸기 (선택)

```text
Blender 에서 scara_rigged.glb 를 불러왔다. Python 콘솔에서 다음 자세로 바꾸는 코드를 줘.
θ1=30°, θ2=-60°, d3=80 mm, θ4=0°, 그리퍼 간격 34 mm.
조건: Blender 는 glTF 를 Z-up 으로 바꿔 불러온다. joint1/2/4 는 로컬 Z 회전, joint3 는 로컬 Z 방향으로 -d3(m),
finger_left_joint 는 로컬 +Y 로 (gap/2-25)/1000 m, finger_right_joint 는 -Y 로 같은 양 이동.
```

✔ 확인: 저장소의 [`tools/blender_render.py`](../tools/blender_render.py) 와 같은 방식인지 비교한다.
