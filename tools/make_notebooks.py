"""notebooks/*.ipynb 를 만든다 (Colab 바로 실행용).  python3 tools/make_notebooks.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/djfksjd/robot_study.git"

SETUP = f'''# 0) 저장소 준비 — Colab에서는 처음 한 번 clone, 로컬에서는 저장소 루트에서 실행하면 건너뛴다
import os, sys
if not os.path.exists("model/scara_params.json"):
    if not os.path.exists("robot_study"):
        !git clone -q {REPO}
    %cd robot_study
sys.path.insert(0, "python")
print("작업 폴더:", os.getcwd())'''


_ids = iter(range(10_000))


def md(text):
    return {"cell_type": "markdown", "id": f"c{next(_ids):03d}", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "id": f"c{next(_ids):03d}", "metadata": {}, "execution_count": None, "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NB = {}

NB["01_forward_kinematics_workspace.ipynb"] = notebook([
    md("""
# Lab 2 · 정기구학과 작업 영역

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/djfksjd/robot_study/blob/main/notebooks/01_forward_kinematics_workspace.ipynb)

목표
1. 관절값 `q = (θ1, θ2, d3, θ4)` 로 TCP 위치 `(x, y, z, yaw)` 를 계산한다.
2. 팔을 그림으로 그려 식과 그림이 맞는지 확인한다.
3. 관절 한계 안에서 닿을 수 있는 영역(작업 영역)을 점으로 그린다.

막히면 `prompts/03_forward_kinematics.md` 의 프롬프트를 AI 챗에 붙여넣는다.
"""),
    code(SETUP),
    code('''import json, math
import numpy as np
import matplotlib.pyplot as plt
from scara_kinematics import Scara

robot = Scara.load()
print(json.dumps(json.load(open("model/scara_params.json", encoding="utf-8"))["limits"], indent=1))
print("L1 =", robot.L1, "mm,  L2 =", robot.L2, "mm")'''),
    md("""
## 1. 정기구학 식

$x = L_1\\cos\\theta_1 + L_2\\cos(\\theta_1+\\theta_2)$,
$y = L_1\\sin\\theta_1 + L_2\\sin(\\theta_1+\\theta_2)$,
$z = z_0 - d_3$, $\\;\\text{yaw} = \\theta_1+\\theta_2+\\theta_4$
"""),
    code('''def show(q_deg_mm):
    t1, t2, d3, t4 = q_deg_mm
    q = (math.radians(t1), math.radians(t2), d3, math.radians(t4))
    x, y, z, yaw = robot.fk(q)
    ex, ey = robot.elbow_xy(q)
    print(f"q = {q_deg_mm}  ->  TCP x={x:.1f} y={y:.1f} z={z:.1f} mm, yaw={math.degrees(yaw):.1f}°")
    return (0, ex, x), (0, ey, y)

fig, ax = plt.subplots(figsize=(5, 5))
for q, c in [((0, 0, 0, 0), "k"), ((30, 45, 50, 0), "tab:blue"), ((90, -90, 100, 0), "tab:orange"), ((-60, 120, 0, 0), "tab:green")]:
    xs, ys = show(q)
    ax.plot(xs, ys, "-o", color=c, lw=3, label=str(q))
ax.set_aspect("equal"); ax.grid(True); ax.legend(fontsize=8); ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
ax.set_title("SCARA top view (Z-up)")  # 그래프 글자는 Colab 한글 폰트 문제로 영어; plt.show()'''),
    md("""
## 2. 실습 과제
- `(θ1, θ2) = (0, 90)` 일 때 TCP 좌표를 **손으로** 먼저 계산하고 코드 결과와 비교하라.
- `θ4` 를 바꾸면 x, y 는 변하는가? yaw 는?
"""),
    code('''# 직접 바꿔 보기
show((0, 90, 0, 0)); show((0, 90, 0, 45));'''),
    md("## 3. 작업 영역 — 관절 공간을 무작위로 뽑아 FK로 찍는다"),
    code('''rng = np.random.default_rng(0)
lim = robot.limits
t1 = np.radians(rng.uniform(*lim["theta1_deg"], 20000))
t2 = np.radians(rng.uniform(*lim["theta2_deg"], 20000))
x = robot.L1 * np.cos(t1) + robot.L2 * np.cos(t1 + t2)
y = robot.L1 * np.sin(t1) + robot.L2 * np.sin(t1 + t2)

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(x, y, s=1, alpha=0.3)
for r in (robot.reach_min, robot.reach_max):
    ax.add_patch(plt.Circle((0, 0), r, fill=False, ls="--", color="r"))
scene = json.load(open("model/task_scene.json", encoding="utf-8"))
for n, o in scene["objects"].items():
    ax.plot(o["x"], o["y"], "s", ms=8, color=o["color"]); ax.annotate(n, (o["x"], o["y"]))
for n, t in scene["targets"].items():
    ax.plot(t["x"], t["y"], "*", ms=14, color="gold"); ax.annotate(n, (t["x"], t["y"]))
ax.set_aspect("equal"); ax.grid(True)
ax.set_title(f"Workspace: r {robot.reach_min:.0f}~{robot.reach_max:.0f} mm, theta1 {lim['theta1_deg']} deg")
plt.show()'''),
    md("""
## 확인 질문 (AI 챗에 물어보고, 답을 코드로 검증)
1. 작업 영역 안쪽 구멍(반경 약 143 mm)은 왜 생기는가?
2. 로봇 뒤쪽(x<0, |y| 작음)이 비는 이유는?
3. 같은 (x, y)에 팔꿈치 해가 2개인 이유는? → Lab 3
"""),
])

NB["02_inverse_kinematics_trajectory.ipynb"] = notebook([
    md("""
# Lab 3–4 · 역기구학과 궤적

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/djfksjd/robot_study/blob/main/notebooks/02_inverse_kinematics_trajectory.ipynb)

목표
1. 목표 좌표 → 관절값(IK). 팔꿈치 해 2개(right/left)를 비교한다.
2. 도달 불가·관절 한계 초과를 **거부**하는 것을 확인한다.
3. 관절 공간 보간과 직선(카테시안) 보간의 차이를 그래프로 본다.
"""),
    code(SETUP),
    code('''import math
import numpy as np
import matplotlib.pyplot as plt
from scara_kinematics import Scara, joint_trajectory, cartesian_line, min_duration, PARAMS_PATH
robot = Scara.load()

for elbow in ("right", "left"):
    q = robot.ik(300, 150, 15, 0.0, elbow=elbow)
    print(elbow, "θ1={:.1f}° θ2={:.1f}° d3={:.1f}mm θ4={:.1f}°".format(math.degrees(q[0]), math.degrees(q[1]), q[2], math.degrees(q[3])))
    print("   FK 검산 ->", [round(v, 3) for v in robot.fk(q)])'''),
    md("## 1. 거부되어야 하는 목표 — 안전 게이트의 기초"),
    code('''for target in [(500, 0, 50), (50, 50, 50), (300, 0, -100), (-300, -10, 50)]:
    try:
        robot.ik_best(*target)
        print(target, "-> OK")
    except ValueError as e:
        print(target, "-> 거부:", e)'''),
    md("## 2. 관절 보간 vs 직선 보간 — TCP 경로가 어떻게 다른가"),
    code('''p0, p1 = (330, 120, 60, 0.0), (60, 330, 60, 0.0)
q0 = robot.ik_best(*p0)
q1 = robot.ik_best(*p1, q_now=q0)
T = min_duration(PARAMS_PATH, q0, q1)
print(f"속도 한계를 지키는 최소 시간 ≈ {T:.2f} s")

jt = joint_trajectory(q0, q1, T, dt=0.02)
ct = cartesian_line(robot, p0, p1, T, dt=0.02, q_now=q0)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
for traj, name in [(jt, "joint interp"), (ct, "cartesian line")]:
    xy = np.array([robot.fk(q)[:2] for _, q in traj])
    axs[0].plot(xy[:, 0], xy[:, 1], label=name)
axs[0].set_aspect("equal"); axs[0].grid(True); axs[0].legend(); axs[0].set_title("TCP path (top view)")
t = [s for s, _ in jt]
for k, lab in [(0, "theta1"), (1, "theta2")]:
    axs[1].plot(t, [math.degrees(q[k]) for _, q in jt], label=f"{lab} joint")
    axs[1].plot(t, [math.degrees(q[k]) for _, q in ct], "--", label=f"{lab} line")
axs[1].grid(True); axs[1].legend(); axs[1].set_xlabel("t (s)"); axs[1].set_ylabel("deg"); axs[1].set_title("joint angles")
plt.tight_layout(); plt.show()'''),
    md("## 3. 픽앤플레이스 한 번의 Z 높이 계획"),
    code('''z_safe, z_grasp = 90, 15
seq = [("위로 접근", (330, 120, z_safe)), ("내려감", (330, 120, z_grasp)), ("상승", (330, 120, z_safe)),
       ("목표 위", (60, 330, z_safe)), ("내려놓기", (60, 330, z_grasp + 1)), ("상승", (60, 330, z_safe))]
q = (0, 0, 0, 0)
for name, (x, y, z) in seq:
    q = robot.ik_best(x, y, z, 0.0, q_now=q)
    print(f"{name:6s} d3={q[2]:6.1f} mm  θ1={math.degrees(q[0]):7.1f}°  θ2={math.degrees(q[1]):7.1f}°")'''),
    md("""
## 과제
- 직선 보간이 실패(IK 예외)하는 시작·끝점 쌍을 찾아라. 왜 실패하는가?
- `scara_params.json` 의 `max_speed` 를 절반으로 바꾸면 최소 시간은?
"""),
])

NB["03_mujoco_pick_place.ipynb"] = notebook([
    md("""
# Lab 6 · MuJoCo 물리 시뮬레이션 픽앤플레이스

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/djfksjd/robot_study/blob/main/notebooks/03_mujoco_pick_place.ipynb)

웹 시뮬레이터는 '조건이 맞으면 붙이는' 운동학 시뮬레이션이다. 여기서는 마찰·접촉·중력이 있는 물리 엔진에서
**같은 JSON 계획**이 실제로 성공하는지 본다.
"""),
    code(SETUP),
    code('''# Colab: 물리 엔진 설치 + 화면 없는 렌더링 설정
import os, sys, subprocess
if "google.colab" in sys.modules:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "mujoco", "mediapy"], check=True)
    os.environ["MUJOCO_GL"] = "egl"
import mujoco
print("MuJoCo", mujoco.__version__)'''),
    code('''sys.path.insert(0, "sim/mujoco")
import importlib, pick_place
importlib.reload(pick_place)

plan = {"tasks": [
    {"action": "pick", "object": "red"},   {"action": "place", "target": "tray_A"},
    {"action": "pick", "object": "blue"},  {"action": "place", "target": "tray_B"},
    {"action": "pick", "object": "green"}, {"action": "place", "target": "tray_A"},
    {"action": "home"}]}

RENDER = "google.colab" in sys.modules  # 로컬에서는 영상 없이 물리만
sim = pick_place.Sim(video="out.mp4" if RENDER else None, fps=20)
try:
    sim.run(plan)
except pick_place.SafetyError as e:
    print("SAFETY STOP:", e)
print("\\n".join(sim.log))
for n in ("red", "green", "blue"):
    print(n, sim.body_xyz(n).round(1))'''),
    code('''# 결과 판정: 목표 트레이 중심에서 5 mm 이내, 높이가 맞는가
import numpy as np
ok = (np.hypot(*(sim.body_xyz("red")[:2] - [60, 330])) < 5 and abs(sim.body_xyz("green")[2] - 45) < 3
      and np.hypot(*(sim.body_xyz("blue")[:2] - [60, -330])) < 5)
print("PASS" if ok else "FAIL")'''),
    code('''# 영상 (Colab)
if RENDER and sim.frames:
    import mediapy
    mediapy.show_video(sim.frames, fps=sim.fps)'''),
    md("""
## 실험 과제 (한 번에 하나만 바꾸고 결과를 기록)
1. `model/task_scene.json` 의 `grip_closed_mm` 를 28로 바꾸면? (쥐는 힘이 줄어든다)
2. `sim/mujoco/build_mjcf.py` 의 패드 마찰 `friction="1.5 ..."` 를 0.3으로 → `python3 sim/mujoco/build_mjcf.py` 로 다시 생성
3. 블록 질량 0.03 → 0.3 kg
기록 양식은 `seminar/lab_report_template.md`.
"""),
])

out = ROOT / "notebooks"
out.mkdir(exist_ok=True)
for name, nb in NB.items():
    (out / name).write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", out / name)
