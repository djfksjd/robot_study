"""model/scara_params.json -> sim/mujoco/scara.xml (MuJoCo MJCF, Z-up, 단위 m).

python3 sim/mujoco/build_mjcf.py

외형은 GLB와 같은 치수를 단순 도형(원기둥·상자·캡슐)으로 근사한다.
충돌은 손가락 패드·블록·작업대만 켠다(팔 링크는 시각용).
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE.parent.parent / "model" / "scara_params.json").read_text(encoding="utf-8"))
m = lambda v: round(v / 1000, 5)  # noqa: E731

L1, L2, H1 = P["L1"], P["L2"], P["j1_height"]
LIM = P["limits"]
GAP = P["gripper_gap_home_mm"]
finger_lo = (LIM["gripper_gap_mm"][0] / 2 - GAP / 2)
finger_hi = (LIM["gripper_gap_mm"][1] / 2 - GAP / 2)

# 작업 장면: model/task_scene.json (웹 시뮬레이터와 공유)
SCENE = json.loads((HERE.parent.parent / "model" / "task_scene.json").read_text(encoding="utf-8"))


def rgba(hex_color):
    h = hex_color.lstrip("#")
    return " ".join(f"{int(h[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4)) + " 1"


BLOCKS = {n: (o["x"], o["y"], rgba(o["color"])) for n, o in SCENE["objects"].items()}
TRAYS = {n: (t["x"], t["y"]) for n, t in SCENE["targets"].items()}
BLOCK = SCENE["block_size"]

blocks_xml = "\n".join(
    f'''    <body name="{n}" pos="{m(x)} {m(y)} {m(BLOCK/2)}">
      <freejoint name="{n}_free"/>
      <geom class="col" type="box" size="{m(BLOCK/2)} {m(BLOCK/2)} {m(BLOCK/2)}" rgba="{c}" mass="0.03"/>
    </body>''' for n, (x, y, c) in BLOCKS.items())

trays_xml = "\n".join(
    f'''    <geom name="{n}" type="box" pos="{m(x)} {m(y)} 0.0005" size="0.03 0.03 0.0005" rgba="1 0.75 0.1 0.6" contype="0" conaffinity="0"/>'''
    for n, (x, y) in TRAYS.items())

xml = f'''<!-- 자동 생성: sim/mujoco/build_mjcf.py (직접 고치지 말고 scara_params.json 을 바꾼 뒤 다시 생성) -->
<mujoco model="rs450_scara">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="0.002" cone="elliptic" impratio="10" integrator="implicitfast"/>
  <visual>
    <global offwidth="960" offheight="720" azimuth="-130" elevation="-25"/>
    <quality shadowsize="4096"/>
  </visual>
  <default>
    <geom contype="0" conaffinity="0" density="2700"/>
    <default class="col">
      <geom contype="1" conaffinity="1" condim="4" friction="1.5 0.02 0.002" solref="0.004 1" solimp="0.95 0.99 0.001"/>
    </default>
  </default>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.82 0.83 0.85" rgb2="0.76 0.77 0.8" width="512" height="512"/>
    <material name="table" texture="grid" texrepeat="12 12" reflectance="0.0"/>
    <material name="white" rgba="0.93 0.94 0.95 1"/>
    <material name="dark" rgba="0.23 0.25 0.28 1"/>
    <material name="chrome" rgba="0.85 0.87 0.9 1" reflectance="0.3"/>
    <material name="orange" rgba="0.95 0.55 0.16 1"/>
    <material name="blue" rgba="0.18 0.43 0.87 1"/>
    <material name="rubber" rgba="0.08 0.09 0.1 1"/>
  </asset>
  <worldbody>
    <light pos="0.6 -0.6 1.5" dir="-0.4 0.4 -1" diffuse="0.8 0.8 0.8" castshadow="true"/>
    <light pos="-0.5 0.6 1.2" dir="0.3 -0.4 -1" diffuse="0.3 0.3 0.3" castshadow="false"/>
    <geom name="table" type="plane" size="1 1 0.01" material="table" contype="1" conaffinity="1"/>
{trays_xml}
    <camera name="overview" pos="0.95 -0.85 0.65" xyaxes="0.67 0.74 0 -0.32 0.29 0.9"/>
    <camera name="top" pos="0.2 0 1.2" xyaxes="1 0 0 0 1 0"/>

    <!-- 베이스 (고정) -->
    <geom type="box" pos="0 0 {m(12)}" size="{m(160)} {m(160)} {m(12)}" material="dark"/>
    <geom type="cylinder" pos="0 0 {m(112)}" size="{m(78)} {m(88)}" material="white"/>
    <geom type="cylinder" pos="0 0 {m(225)}" size="{m(92)} {m(25)}" material="dark"/>
    <geom type="box" pos="{m(-120)} 0 {m(84)}" size="{m(40)} {m(55)} {m(60)}" material="dark"/>

    <body name="link1" pos="0 0 {m(H1)}" gravcomp="1">
      <joint name="j1" type="hinge" axis="0 0 1" range="{math.radians(LIM['theta1_deg'][0]):.5f} {math.radians(LIM['theta1_deg'][1]):.5f}" damping="2" armature="0.05"/>
      <geom type="cylinder" pos="0 0 {m(30)}" size="{m(70)} {m(28)}" material="white"/>
      <geom type="box" pos="{m(L1/2)} 0 {m(30)}" size="{m(L1/2)} {m(62)} {m(28)}" material="white"/>
      <geom type="cylinder" pos="{m(L1)} 0 {m(30)}" size="{m(60)} {m(28)}" material="white"/>
      <geom type="box" pos="{m(L1/2)} 0 {m(30)}" size="{m(L1/2)} {m(64)} {m(7)}" material="blue"/>

      <body name="link2" pos="{m(L1)} 0 0" gravcomp="1">
        <joint name="j2" type="hinge" axis="0 0 1" range="{math.radians(LIM['theta2_deg'][0]):.5f} {math.radians(LIM['theta2_deg'][1]):.5f}" damping="1.5" armature="0.03"/>
        <geom type="cylinder" pos="0 0 {m(96)}" size="{m(62)} {m(28)}" material="white"/>
        <geom type="box" pos="{m(L2/2)} 0 {m(96)}" size="{m(L2/2)} {m(54)} {m(28)}" material="white"/>
        <geom type="box" pos="{m(L2/2)} 0 {m(96)}" size="{m(L2/2)} {m(56)} {m(7)}" material="orange"/>
        <geom type="cylinder" pos="0 0 {m(144)}" size="{m(50)} {m(20)}" material="dark"/>
        <geom type="box" pos="{m(L2-20)} 0 {m(159)}" size="{m(65)} {m(52)} {m(35)}" material="white"/>

        <body name="quill" pos="{m(L2)} 0 0" gravcomp="1">
          <joint name="j3" type="slide" axis="0 0 -1" range="{m(LIM['d3_mm'][0])} {m(LIM['d3_mm'][1])}" damping="30" armature="0.5"/>
          <joint name="j4" type="hinge" axis="0 0 1" range="{math.radians(LIM['theta4_deg'][0]):.5f} {math.radians(LIM['theta4_deg'][1]):.5f}" damping="0.3" armature="0.005"/>
          <geom type="cylinder" pos="0 0 {m(120)}" size="{m(10)} {m(170)}" material="chrome"/>
          <geom type="cylinder" pos="0 0 {m(-55)}" size="{m(30)} {m(5)}" material="dark"/>
          <geom type="box" pos="0 0 {m(-77)}" size="{m(22)} {m(48)} {m(17)}" material="orange"/>
          <site name="tcp" pos="0 0 {m(P['tcp_z_at_d0'] - H1)}" size="0.004" rgba="1 0 0 1"/>

          <body name="finger_left" pos="0 0 0" gravcomp="1">
            <joint name="jfl" type="slide" axis="0 1 0" range="{m(finger_lo)} {m(finger_hi)}" damping="5"/>
            <geom type="box" pos="0 {m(GAP/2+5)} {m(-119)}" size="{m(12)} {m(5)} {m(25)}" material="dark"/>
            <geom class="col" type="box" pos="0 {m(GAP/2+1.5)} {m(-129)}" size="{m(10)} {m(1.5)} {m(15)}" material="rubber" mass="0.01"/>
          </body>
          <body name="finger_right" pos="0 0 0" gravcomp="1">
            <joint name="jfr" type="slide" axis="0 -1 0" range="{m(finger_lo)} {m(finger_hi)}" damping="5"/>
            <geom type="box" pos="0 {m(-(GAP/2+5))} {m(-119)}" size="{m(12)} {m(5)} {m(25)}" material="dark"/>
            <geom class="col" type="box" pos="0 {m(-(GAP/2+1.5))} {m(-129)}" size="{m(10)} {m(1.5)} {m(15)}" material="rubber" mass="0.01"/>
          </body>
        </body>
      </body>
    </body>

{blocks_xml}
  </worldbody>

  <equality>
    <joint joint1="jfl" joint2="jfr" polycoef="0 1 0 0 0"/>
  </equality>

  <actuator>
    <position name="a1" joint="j1" kp="400" kv="40" forcerange="-60 60"/>
    <position name="a2" joint="j2" kp="300" kv="25" forcerange="-40 40"/>
    <position name="a3" joint="j3" kp="20000" kv="800" forcerange="-200 200"/>
    <position name="a4" joint="j4" kp="20" kv="1" forcerange="-5 5"/>
    <position name="agrip" joint="jfl" kp="1500" kv="20" forcerange="-15 15"/>
  </actuator>
</mujoco>
'''
(HERE / "scara.xml").write_text(xml, encoding="utf-8")
print("wrote", HERE / "scara.xml")
