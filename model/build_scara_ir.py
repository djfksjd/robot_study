"""scara_params.json -> sceliph AssemblyIR(morphloom.assembly/0.1) JSON.

사용법:
    python3 model/build_scara_ir.py            # model/scara.assembly.json 생성

좌표 규칙
- AssemblyIR/glTF는 Y-up, 단위 mm(내보낸 GLB는 m).
- 로봇 좌표(Z-up) (x, y, z)  ->  IR 좌표 (x, z, -y).
- 모든 부품은 홈 자세(theta1=theta2=theta4=0, d3=0, 그리퍼 간격 50 mm)에서 배치한다.
- 부품 id 앞부분(base__, link1__, link2__, quill__, fingerL__, fingerR__)이 리그 그룹이다.
  tools/rig_scara_glb.mjs 가 이 접두어로 관절 노드 아래에 부품을 붙인다.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "scara_params.json").read_text(encoding="utf-8"))

L1 = P["L1"]
L2 = P["L2"]
H1 = P["j1_height"]
GAP = P["gripper_gap_home_mm"]

# 재질 팔레트 (학생이 바꿔 보기 쉬운 곳)
WHITE = {"color": "#eef0f2", "surface": "coated-metal", "roughness": 0.42, "metalness": 0.05, "clearcoat": 0.3, "clearcoatRoughness": 0.35}
DARK = {"color": "#3a3f46", "surface": "coated-metal", "roughness": 0.55, "metalness": 0.2}
CAST = {"color": "#2b2f35", "surface": "bead-blasted-metal", "roughness": 0.7, "metalness": 0.6}
CHROME = {"color": "#d9dde2", "surface": "polished-metal", "roughness": 0.12, "metalness": 1.0, "anisotropy": 0.5}
ANOD = {"color": "#1f2227", "surface": "anodized-metal", "roughness": 0.35, "metalness": 0.85}
ORANGE = {"color": "#f28c28", "surface": "molded-polymer", "roughness": 0.45, "metalness": 0.0}
RUBBER = {"color": "#15171a", "surface": "rubber", "roughness": 0.9, "metalness": 0.0}
GREEN = {"color": "#3ccf6e", "surface": "molded-polymer", "roughness": 0.3, "metalness": 0.0}
BLUE = {"color": "#2f6fdf", "surface": "molded-polymer", "roughness": 0.4, "metalness": 0.0}

ROT_X_DOWN = [-math.pi / 2, 0, 0]  # 압출 단면(로봇 XY)을 세로(Y) 방향으로 세운다
ROT_Z_90 = [0, 0, math.pi / 2]     # 원기둥 축 Y -> X


def ir_pos(x, y, z):
    """로봇 좌표(mm, Z-up) -> IR 좌표(mm, Y-up)."""
    return [round(x, 4), round(z, 4), round(-y, 4)]


def slot(x0, r0, x1, r1, n=24):
    """두 원(반지름 r0, r1)을 외접선으로 이은 링크 단면. 로봇 XY 평면 좌표."""
    d = x1 - x0
    phi = math.asin((r0 - r1) / d)
    pts = []
    # 끝단(x1) 호: -90°+phi .. +90°-phi (바깥쪽)
    a0, a1 = -math.pi / 2 + phi, math.pi / 2 - phi
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append([x1 + r1 * math.cos(a), r1 * math.sin(a)])
    # 시작단(x0) 호: 90°-phi .. 270°+phi
    a0, a1 = math.pi / 2 - phi, 3 * math.pi / 2 + phi
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append([x0 + r0 * math.cos(a), r0 * math.sin(a)])
    return [[round(px, 4), round(py, 4)] for px, py in pts]


def comp(cid, name, material_name, detail, geometry, pos, material, rotation=None):
    c = {
        "id": cid,
        "name": name,
        "category": "mechanical",
        "materialName": material_name,
        "detail": detail,
        "geometry": geometry,
        "position": pos,
        "material": material,
    }
    if rotation:
        c["rotation"] = rotation
    return c


def cyl(r, depth, seg=64, r_bottom=None):
    return {"op": "cylinder", "radiusTop": r, "radiusBottom": r if r_bottom is None else r_bottom, "depth": depth, "radialSegments": seg}


def box(sx, sy, sz, radius):
    """sx, sy, sz 는 로봇 좌표 기준 크기(x, y, z)."""
    return {"op": "roundedBox", "size": [sx, sz, sy], "radius": radius, "segments": 4}


components = []

# ---------------------------------------------------------------- base (고정)
components += [
    comp("base__plate", "베이스 플레이트", "주물 알루미늄", "바닥 고정판 320x320x24 mm, 4볼트 고정", box(320, 320, 24, 8), ir_pos(0, 0, 12), CAST),
    comp("base__column", "베이스 기둥", "도장 알루미늄", "J1 모터·감속기를 담는 원기둥 (inferred 내부 구조)",
         {"op": "lathe", "profile": [[0, 200], [76, 200], [74, 196], [80, 40], [84, 24], [0, 24]], "segments": 72}, ir_pos(0, 0, 0), WHITE),
    comp("base__j1_housing", "J1 하우징", "도장 알루미늄", "J1 회전부 링", cyl(92, 50, 72), ir_pos(0, 0, 225), DARK),
    comp("base__connector_box", "커넥터 박스", "도장 알루미늄", "뒤쪽 케이블 인입부", box(80, 110, 120, 10), ir_pos(-120, 0, 84), DARK),
    comp("base__connector_a", "전원 커넥터", "니켈 도금", "원형 커넥터(시각용)", cyl(12, 14, 32), ir_pos(-167, 22, 100), CHROME, ROT_Z_90),
    comp("base__connector_b", "신호 커넥터", "니켈 도금", "원형 커넥터(시각용)", cyl(9, 14, 32), ir_pos(-167, -24, 100), CHROME, ROT_Z_90),
    comp("base__status_led", "상태 LED", "폴리카보네이트", "전원 표시등(시각용)", cyl(6, 4, 24), ir_pos(-167, 0, 60), GREEN, ROT_Z_90),
]
for i, (bx, by) in enumerate([(130, 130), (-130, 130), (130, -130), (-130, -130)]):
    components.append(comp(f"base__bolt_{i}", f"고정 볼트 {i}", "스테인리스", "M10 육각 소켓 볼트 머리(시각용)",
                           cyl(8, 6, 6), ir_pos(bx, by, 27), CHROME))

# ---------------------------------------------------------------- link1 (J1 회전)
components += [
    comp("link1__body", "제1 링크", "도장 알루미늄 주물", f"J1-J2 중심거리 L1={L1} mm, 두께 56 mm",
         {"op": "extrude", "points": slot(0, 70, L1, 60), "depth": 56, "bevelSize": 3, "bevelThickness": 3, "bevelSegments": 2},
         ir_pos(0, 0, H1 + 30), WHITE, ROT_X_DOWN),
    comp("link1__band", "제1 링크 측면 띠", "폴리머", "식별용 색 띠",
         {"op": "extrude", "points": slot(0, 75, L1, 65), "depth": 14}, ir_pos(0, 0, H1 + 30), BLUE, ROT_X_DOWN),
    comp("link1__j2_ring", "J2 베어링 링", "양극산화 알루미늄", "J2 회전 경계", cyl(56, 10, 64), ir_pos(L1, 0, H1 + 63), ANOD),
    comp("link1__j1_cap", "J1 캡", "도장 알루미늄", "J1 축 상단 캡", cyl(40, 6, 48), ir_pos(0, 0, H1 + 61), DARK),
]

# ---------------------------------------------------------------- link2 (J2 회전)
Z2 = H1 + 68  # link2 바닥
components += [
    comp("link2__body", "제2 링크", "도장 알루미늄 주물", f"J2-J3 중심거리 L2={L2} mm, 두께 56 mm",
         {"op": "extrude", "points": slot(L1, 62, L1 + L2, 52), "depth": 56, "bevelSize": 3, "bevelThickness": 3, "bevelSegments": 2},
         ir_pos(0, 0, Z2 + 28), WHITE, ROT_X_DOWN),
    comp("link2__band", "제2 링크 측면 띠", "폴리머", "식별용 색 띠",
         {"op": "extrude", "points": slot(L1, 67, L1 + L2, 57), "depth": 14}, ir_pos(0, 0, Z2 + 28), ORANGE, ROT_X_DOWN),
    comp("link2__j2_cover", "J2 모터 커버", "도장 알루미늄", "J2 모터 상단 커버", cyl(50, 40, 64), ir_pos(L1, 0, Z2 + 76), DARK),
    comp("link2__head", "J3/J4 모터 헤드", "도장 알루미늄", "Z축·회전축 모터를 덮는 헤드 커버 (inferred 내부)",
         box(130, 104, 70, 14), ir_pos(L1 + L2 - 20, 0, Z2 + 56 + 35), WHITE),
    comp("link2__head_cap", "헤드 상판", "도장 알루미늄", "헤드 상단 판", box(110, 86, 6, 2), ir_pos(L1 + L2 - 20, 0, Z2 + 56 + 73), DARK),
    comp("link2__spline_housing", "스플라인 너트 하우징", "양극산화 알루미늄", "볼스크루 스플라인 너트 하우징",
         cyl(30, 34, 48), ir_pos(L1 + L2, 0, Z2 - 13), ANOD),
    comp("link2__led", "동작 LED", "폴리카보네이트", "동작 표시등(시각용)", cyl(5, 4, 24), ir_pos(L1 + L2 - 85, 0, Z2 + 56 + 50), GREEN, ROT_Z_90),
]

# ---------------------------------------------------------------- quill (J3 직동 + J4 회전)
components += [
    comp("quill__shaft", "볼스크루 스플라인 축", "경질 크롬 도금강", "지름 20 mm, 길이 340 mm, Z 스트로크 180 mm",
         cyl(10, 340, 48), ir_pos(L1 + L2, 0, 200 + 170), CHROME),
    comp("quill__stopper", "상단 스토퍼", "강", "축 상단 기계식 스토퍼", cyl(16, 12, 48), ir_pos(L1 + L2, 0, 534), DARK),
    comp("quill__flange", "툴 플랜지", "양극산화 알루미늄", "엔드이펙터 장착 플랜지", cyl(30, 10, 48), ir_pos(L1 + L2, 0, 195), ANOD),
    comp("quill__gripper_body", "그리퍼 본체", "폴리머", "평행 2지 그리퍼 본체 96x44x34 mm", box(96, 44, 34, 4), ir_pos(L1 + L2, 0, 173), ORANGE),
    comp("quill__gripper_rail", "그리퍼 레일", "양극산화 알루미늄", "손가락 직선 가이드", box(104, 16, 6, 1.5), ir_pos(L1 + L2, 0, 153), ANOD),
]

# ---------------------------------------------------------------- fingers (그리퍼 직동)
for side, sign in (("fingerL", 1), ("fingerR", -1)):
    # 손가락은 로봇 y 방향으로 벌어진다(홈 자세에서 그리퍼 로컬 y = 로봇 y)
    yc = sign * (GAP / 2 + 5)
    ypad = sign * (GAP / 2 + 1.5)
    label = "왼쪽" if sign > 0 else "오른쪽"
    components += [
        comp(f"{side}__finger", f"{label} 손가락", "양극산화 알루미늄", "손가락 24x10x50 mm", box(24, 10, 50, 2), ir_pos(L1 + L2, yc, 131), ANOD),
        comp(f"{side}__pad", f"{label} 패드", "우레탄 고무", "마찰 패드 20x3x30 mm, 아래 끝이 손가락 끝과 일치", box(20, 3, 30, 1), ir_pos(L1 + L2, ypad, 121), RUBBER),
    ]

ir = {
    "schema": "morphloom.assembly/0.1",
    "name": P["name"],
    "units": "mm",
    "metadata": {
        "source": "robot_study/model/build_scara_ir.py",
        "params": "robot_study/model/scara_params.json",
        "evidence": "창작 학습용 형상. 실측·특정 제품 복제가 아니며 내부 구조는 inferred.",
        "pose": "home: theta1=theta2=theta4=0, d3=0, gripper gap 50 mm",
    },
    "components": components,
}

out = ROOT / "scara.assembly.json"
out.write_text(json.dumps(ir, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out} ({len(components)} components)")
