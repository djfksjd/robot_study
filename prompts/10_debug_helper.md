# 10 · 오류 해석 도우미 (공통)

## ▶ 프롬프트 10-1 · 오류 메시지 해석

```text
robot_study 실습 중 오류가 났다. 
- 실습: <<Lab 번호와 노트북/화면 이름>>
- 실행 환경: <<Colab / 로컬 macOS / Windows / 브라우저 이름>>
- 실행한 코드 또는 동작:
<<셀 코드 또는 누른 버튼>>
- 전체 오류 메시지(Traceback 처음부터 끝까지):
<<붙여넣기>>

1) 오류가 난 정확한 줄과 원인 한 문장
2) 고치는 방법 (가장 가능성 높은 것부터 최대 3개)
3) 고쳤는지 확인하는 방법
추측이면 추측이라고 표시해 줘.
```

## 자주 나는 오류

| 증상 | 원인 | 해결 |
|---|---|---|
| `ModuleNotFoundError: scara_kinematics` | 저장소 폴더 밖에서 실행 | 노트북 첫 셀(저장소 준비)을 다시 실행 |
| `FileNotFoundError: model/scara_params.json` | `%cd robot_study` 안 됨 | 첫 셀 재실행, `!pwd` 로 위치 확인 |
| `ValueError: 도달 불가` | 목표 반경이 144~450 mm 밖 | 정상 동작(안전 거부). 목표 수정 |
| `ValueError: 관절 한계 초과` | θ1 ±132°, θ2 ±145°, d3 0~180 | 정상 동작. 다른 팔꿈치 해/목표 수정 |
| MuJoCo `gladLoadGL error` (Colab) | 렌더러 설정 전 import | 런타임 재시작 → 설치 셀(MUJOCO_GL=egl)부터 |
| 웹 시뮬레이터 화면이 빈 회색 | GLB 로딩 실패, 오래된 브라우저 | 새로고침, Chrome/Edge 최신, 개발자도구 Console 오류 복사 |
| `JSON 문법 오류` | AI가 설명 문장이나 ```json 표시까지 붙임 | `{` 부터 `}` 까지만 붙여넣기 |

## ▶ 프롬프트 10-2 · 웹 시뮬레이터 콘솔 오류

```text
브라우저 개발자 도구(F12) Console 에 아래 오류가 나왔다. 웹 시뮬레이터는 three.js 0.179.1 과 GLTFLoader 로
docs/models/scara_rigged.glb 를 불러온다. 원인과 해결책을 알려 줘.
<<Console 오류 붙여넣기>>
```
