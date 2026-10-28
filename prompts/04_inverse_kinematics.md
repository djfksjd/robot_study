# 04 · Lab 3 — 역기구학

노트북: [02_inverse_kinematics_trajectory.ipynb](../notebooks/02_inverse_kinematics_trajectory.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/djfksjd/robot_study/blob/main/notebooks/02_inverse_kinematics_trajectory.ipynb)

목표: 목표 좌표 `(x, y, z, yaw)`에서 관절값을 구하고, 해가 2개인 이유와 **거부해야 하는 목표**를 이해한다.

## ▶ 프롬프트 4-1 · 유도

```text
SCARA 역기구학을 코사인 법칙으로 유도해 줘. (L1=250, L2=200 mm)
1) c2 = (x²+y²-L1²-L2²)/(2·L1·L2), θ2 = atan2(±sqrt(1-c2²), c2)
2) θ1 = atan2(y, x) - atan2(L2·sinθ2, L1 + L2·cosθ2)
3) d3 = 121 - z, θ4 = yaw - θ1 - θ2
4) 왜 acos 대신 atan2 를 쓰는지
5) |c2| > 1 이면 무슨 뜻인지
그림으로 "오른팔(elbow right, θ2<0)", "왼팔(elbow left, θ2>0)" 두 해를 설명해 줘.
```

## ▶ 프롬프트 4-2 · 직접 구현해 보기

```text
위 식으로 ik(x, y, z, yaw_deg, elbow) 함수를 직접 짜 줘. 조건:
- 도달 불가이면 ValueError, 관절 한계(θ1 ±132°, θ2 ±145°, d3 0~180) 밖이면 ValueError
- 결과를 저장소의 Scara().fk 로 역검산하는 테스트 코드 포함 (무작위 1000개)
저장소의 python/scara_kinematics.py 와 내 구현의 결과가 같은지 비교하는 셀도 줘.
```

✔ 확인: 무작위 1000개에서 FK 역검산 오차가 1e-6 mm 이하인가? 저장소 함수와 같은가?

## ▶ 프롬프트 4-3 · 안전 관점

```text
아래 목표들을 IK 에 넣으면 어떻게 되어야 하는지 예측하고 이유를 말해 줘. 그다음 내가 실행해서 결과를 붙여 넣을게.
(500, 0, 50), (50, 50, 50), (300, 0, -100), (-300, -10, 50)
"계산이 안 되면 그냥 가장 가까운 점으로 가면 되지 않나?" 라는 의견의 위험성도 설명해 줘.
```

✔ 확인: 네 개 모두 거부(도달 불가 / θ2 한계 / d3 한계 / θ1 한계)되는가? 실제 실행 결과와 예측을 표로 비교한다.

## ▶ 프롬프트 4-4 · 해 선택

```text
두 팔꿈치 해가 모두 가능할 때 저장소의 ik_best 는 "현재 자세에서 θ1, θ2 변화량 합이 작은 해"를 고른다.
이 기준의 장점과, 이 기준만 쓰면 생길 수 있는 문제(예: 장애물, 케이블 꼬임, θ4 한계)를 설명해 줘.
```
