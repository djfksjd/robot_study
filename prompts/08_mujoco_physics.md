# 08 · Lab 6 — MuJoCo 물리 시뮬레이션

노트북: [03_mujoco_pick_place.ipynb](../notebooks/03_mujoco_pick_place.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/djfksjd/robot_study/blob/main/notebooks/03_mujoco_pick_place.ipynb)

목표: 웹 시뮬레이터와 **같은 JSON 계획**을 마찰·접촉·중력이 있는 물리 엔진에서 실행해, 파지가 실제로 성공하는 조건을 실험으로 찾는다.

## ▶ 프롬프트 8-1 · MJCF 읽기

[`sim/mujoco/scara.xml`](../sim/mujoco/scara.xml)의 `<worldbody>`부터 `</actuator>`까지 붙여넣는다.

```text
아래는 MuJoCo MJCF 파일이다. 
1) body 계층과 joint(hinge/slide)를 표로 정리하고, 웹 시뮬레이터의 GLB 노드(joint1~4, finger_*)와 대응시켜 줘.
2) position actuator 의 kp, kv, forcerange 가 무슨 뜻인지, 왜 j3(상하축)만 kp 가 큰지
3) gravcomp="1" 은 무엇이고 왜 넣었는지
4) 손가락 두 개를 equality joint 로 묶은 이유

<<scara.xml 일부 붙여넣기>>
```

## ▶ 프롬프트 8-2 · 실험 설계

```text
MuJoCo 픽앤플레이스에서 파지 성공 조건을 알아보는 실험을 설계해 줘. 바꿀 변수:
(a) task_scene.json 의 grip_closed_mm (20, 24, 28, 29.5)
(b) 패드 마찰계수 (1.5, 0.8, 0.3)
(c) 블록 질량 (0.03, 0.1, 0.3 kg)
한 번에 하나만 바꾸는 계획표, 각 조건의 예상 결과와 근거(마찰력 = μ·N, N ≈ kp·간격 오차)를 표로 줘.
```

## ▶ 프롬프트 8-3 · 결과 해석

```text
실험 결과는 다음과 같다. 
<<조건 / PASS·FAIL / 블록 최종 위치 붙여넣기>>
예상과 다른 결과가 있다면 원인 후보를 2~3개 들고, 그 원인을 구분할 추가 실험을 하나씩 제안해 줘.
웹 시뮬레이터(운동학)에서는 모두 성공했는데 MuJoCo 에서 실패한 경우, 그 차이가 무엇을 뜻하는지도 설명해 줘.
```

## 확인

- 기본 계획은 `PASS`가 나와야 한다 (빨강·초록 tray_A 적층, 파랑 tray_B, 오차 5 mm 이내).
- Colab에서 영상이 안 나오면 `MUJOCO_GL=egl` 셀을 먼저 실행했는지 확인한다. 그래도 안 되면 [`10_debug_helper.md`](10_debug_helper.md).
