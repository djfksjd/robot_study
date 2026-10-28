"""MuJoCo 물리 시뮬레이션: SCARA 픽앤플레이스.

python3 sim/mujoco/pick_place.py                 # 물리만 실행하고 결과 판정
python3 sim/mujoco/pick_place.py --video out.mp4 # 영상 저장 (Colab: MUJOCO_GL=egl)
python3 sim/mujoco/pick_place.py --plan plan.json

plan.json 형식은 웹 시뮬레이터와 같다 (docs/sim/README 참고):
  {"tasks": [{"action": "pick", "object": "red"}, {"action": "place", "target": "tray_A"}, ...]}
허용 행동: home, move_to, open_gripper, close_gripper, pick, place, wait, stop
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "python"))
from scara_kinematics import PARAMS_PATH, Scara, min_duration, smoothstep5  # noqa: E402

ROBOT = Scara.load()
PARAMS = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
GAP_HOME = PARAMS["gripper_gap_home_mm"]
SCENE = json.loads((HERE.parent.parent / "model" / "task_scene.json").read_text(encoding="utf-8"))
BLOCK = float(SCENE["block_size"])
Z_SAFE = float(SCENE["z_safe"])              # 이동 높이 (TCP z, mm)
GRIP_CLOSED = float(SCENE["grip_closed_mm"])  # 잡을 때 명령 간격 (블록보다 작게 -> 힘 제한으로 쥔다)
GRIP_OPEN = float(SCENE["grip_open_mm"])
ALLOWED = set(SCENE["allowed_actions"])

DEFAULT_PLAN = {"tasks": [
    {"action": "pick", "object": "red"}, {"action": "place", "target": "tray_A"},
    {"action": "pick", "object": "blue"}, {"action": "place", "target": "tray_B"},
    {"action": "pick", "object": "green"}, {"action": "place", "target": "tray_A"},  # red 위에 쌓기
    {"action": "home"},
]}


class SafetyError(Exception):
    pass


class Sim:
    def __init__(self, video=None, fps=30):
        self.model = mujoco.MjModel.from_xml_path(str(HERE / "scara.xml"))
        self.data = mujoco.MjData(self.model)
        mujoco.mj_forward(self.model, self.data)
        self.q = (0.0, 0.0, 0.0, 0.0)
        self.gap = GAP_HOME
        self.held = None
        self.log = []
        self.frames = []
        self.video = video
        self.fps = fps
        self.renderer = mujoco.Renderer(self.model, 720, 960) if video else None
        self._next_frame = 0.0

    # ---------------------------------------------------------- 저수준
    def _set_ctrl(self, q, gap):
        d = self.data
        d.ctrl[0], d.ctrl[1], d.ctrl[2], d.ctrl[3] = q[0], q[1], q[2] / 1000, q[3]
        d.ctrl[4] = (gap / 2 - GAP_HOME / 2) / 1000

    def _step(self, seconds):
        n = int(round(seconds / self.model.opt.timestep))
        for _ in range(n):
            mujoco.mj_step(self.model, self.data)
            if self.renderer and self.data.time >= self._next_frame:
                self.renderer.update_scene(self.data, camera="overview")
                self.frames.append(self.renderer.render().copy())
                self._next_frame += 1 / self.fps

    def _move_joints(self, q1, gap=None):
        gap = self.gap if gap is None else gap
        q0 = self.q
        T = max(0.3, min_duration(PARAMS_PATH, q0, q1))
        steps = int(T / 0.01)
        for i in range(1, steps + 1):
            s = smoothstep5(i / steps)
            self._set_ctrl(tuple(a + (b - a) * s for a, b in zip(q0, q1)), gap)
            self._step(0.01)
        self.q = q1
        self._step(0.25)  # 정착

    def _move_tcp(self, x, y, z, yaw=0.0):
        try:
            q = ROBOT.ik_best(x, y, z, yaw, q_now=self.q)
        except ValueError as e:
            raise SafetyError(str(e)) from e
        self._move_joints(q)

    def _grip(self, gap):
        self.gap = gap
        self._set_ctrl(self.q, gap)
        self._step(0.6)

    def body_xyz(self, name):
        return self.data.body(name).xpos * 1000

    # ---------------------------------------------------------- 허용 행동
    def run(self, plan):
        for i, task in enumerate(plan["tasks"]):
            act = task.get("action")
            if act not in ALLOWED:
                raise SafetyError(f"#{i} 허용되지 않은 행동: {act}")
            if act == "stop":
                self.log.append("STOP: 즉시 정지, 이후 작업 취소")
                return
            getattr(self, f"do_{act}")(task)
            self.log.append(f"#{i} {act} OK")

    def do_home(self, _):
        self._move_tcp(*ROBOT.fk((0, 0, 0, 0))[:3], 0.0)

    def do_wait(self, t):
        self._step(float(t.get("seconds", 0.5)))

    def do_open_gripper(self, _):
        self._grip(GRIP_OPEN)
        self.held = None

    def do_close_gripper(self, _):
        self._grip(GRIP_CLOSED)

    def do_move_to(self, t):
        self._move_tcp(t["x"], t["y"], t.get("z", Z_SAFE), math.radians(t.get("yaw_deg", 0)))

    def do_pick(self, t):
        name = t["object"]
        if name not in SCENE["objects"]:
            raise SafetyError(f"알 수 없는 물체: {name}")
        if self.held:
            raise SafetyError(f"이미 {self.held} 를 잡고 있음")
        x, y, z = self.body_xyz(name)
        self._grip(GRIP_OPEN)
        self._move_tcp(x, y, Z_SAFE)
        self._move_tcp(x, y, z)
        self._grip(GRIP_CLOSED)
        self._move_tcp(x, y, Z_SAFE)
        if self.body_xyz(name)[2] < BLOCK:  # 들리지 않았으면 실패
            raise SafetyError(f"{name} 파지 실패")
        self.held = name

    def do_place(self, t):
        if not self.held:
            raise SafetyError("잡은 물체가 없음")
        target = t["target"]
        if target not in SCENE["targets"]:
            raise SafetyError(f"알 수 없는 목표: {target}")
        gx, gy = SCENE["targets"][target]["x"], SCENE["targets"][target]["y"]
        # 목표 위에 이미 놓인 블록 높이를 실제 위치로 잰다
        top = 0.0
        for other in SCENE["objects"]:
            ox, oy, oz = self.body_xyz(other)
            if other != self.held and math.hypot(ox - gx, oy - gy) < BLOCK * 0.7:
                top = max(top, oz + BLOCK / 2)
        z = top + BLOCK / 2 + 1.0
        self._move_tcp(gx, gy, Z_SAFE)
        self._move_tcp(gx, gy, z)
        self._grip(GRIP_OPEN)
        self._move_tcp(gx, gy, Z_SAFE)
        self.held = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan")
    ap.add_argument("--video")
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8")) if a.plan else DEFAULT_PLAN
    sim = Sim(video=a.video)
    try:
        sim.run(plan)
    except SafetyError as e:
        sim.log.append(f"SAFETY STOP: {e}")
    for line in sim.log:
        print(line)
    print(f"시뮬레이션 시간 {sim.data.time:.1f} s")
    for name in SCENE["objects"]:
        print(f"  {name:5s} 위치(mm) = {np.round(sim.body_xyz(name), 1)}")
    if a.video and sim.frames:
        import imageio.v2 as imageio
        imageio.mimsave(a.video, sim.frames, fps=sim.fps, macro_block_size=1)
        print("영상 저장:", a.video, len(sim.frames), "frames")
    return sim


if __name__ == "__main__":
    main()
