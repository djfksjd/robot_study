# 프롬프트 모음 — 상용 AI 챗만으로 따라 하기

ChatGPT, Claude, Gemini 같은 **일반 AI 챗 웹 화면**만 있으면 된다. 코드 실행은 브라우저(웹 시뮬레이터)와 Google Colab이 맡고, AI 챗은 설명·코드 작성·오류 해석·계획 JSON 생성을 맡는다.

## 사용 순서

1. 새 대화를 열고 [`00_tutor_system.md`](00_tutor_system.md)의 프롬프트를 **맨 먼저** 붙여넣는다. AI가 "튜터 모드"로 바뀐다.
2. 실습 번호에 맞는 파일을 열어 `▶ 프롬프트` 블록을 **위에서부터 하나씩** 붙여넣는다.
3. 각 블록 뒤의 `✔ 확인` 항목을 직접 실행해서 맞는지 본다. AI 답변은 제안일 뿐 정답이 아니다.
4. 막히면 [`10_debug_helper.md`](10_debug_helper.md)로 오류를 보여 준다.

| 파일 | 실습 | 어디서 실행 |
|---|---|---|
| [00_tutor_system.md](00_tutor_system.md) | 튜터 역할 설정(공통) | AI 챗 |
| [01_scara_concept.md](01_scara_concept.md) | Lab 0 · SCARA 구조 이해 | AI 챗 |
| [02_glb_model.md](02_glb_model.md) | Lab 1 · GLB 모델 열어 보기 | 브라우저 / Blender |
| [03_forward_kinematics.md](03_forward_kinematics.md) | Lab 2 · 정기구학·작업 영역 | Colab |
| [04_inverse_kinematics.md](04_inverse_kinematics.md) | Lab 3 · 역기구학 | Colab |
| [05_trajectory.md](05_trajectory.md) | Lab 4 · 궤적 계획 | Colab |
| [06_web_sim_task_json.md](06_web_sim_task_json.md) | Lab 5 · 웹 시뮬레이터로 작업 계획 실행 | 브라우저 |
| [07_natural_language_planner.md](07_natural_language_planner.md) | Lab 7 · 자연어 → 허용 행동 JSON, 안전 게이트 | AI 챗 + 브라우저 |
| [08_mujoco_physics.md](08_mujoco_physics.md) | Lab 6 · MuJoCo 물리 픽앤플레이스 | Colab |
| [09_modify_model_sceliph.md](09_modify_model_sceliph.md) | Lab 8 · 모델 치수 바꾸기(심화) | AI 챗 + 로컬 PC |
| [10_debug_helper.md](10_debug_helper.md) | 오류 해석(공통) | AI 챗 |
| [11_lab_report.md](11_lab_report.md) | 실습 보고서 정리(공통) | AI 챗 |

## 규칙 세 가지

- **붙여넣기 전에 읽는다.** 프롬프트에 `<<여기에 …>>` 표시가 있으면 내 값으로 바꾼다.
- **AI 출력은 실행해서 확인한다.** "될 것 같다"는 확인이 아니다. 숫자·그래프·로그로 확인한다.
- **개인정보·계정 키를 붙여넣지 않는다.** 코드와 오류 메시지만 보낸다.
