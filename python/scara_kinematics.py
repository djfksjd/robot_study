"""RS-450 학습용 SCARA 기구학.

로봇 좌표계: Z-up, 단위 mm / rad (함수 인자는 rad, 사람이 읽는 출력은 deg).
관절 q = (theta1, theta2, d3, theta4)
    theta1, theta2, theta4 : +Z 축 반시계 회전 [rad]
    d3                     : 퀼이 아래로 내려간 거리 [mm], 0 이 최상단
TCP 자세 = (x, y, z, yaw)
    yaw = theta1 + theta2 + theta4   (그리퍼가 바라보는 방향)

모든 치수는 model/scara_params.json 에서 읽는다.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

PARAMS_PATH = Path(__file__).resolve().parent.parent / "model" / "scara_params.json"


@dataclass(frozen=True)
class Scara:
    L1: float
    L2: float
    tcp_z_at_d0: float
    limits: dict

    @classmethod
    def load(cls, path: Path = PARAMS_PATH) -> "Scara":
        p = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(p["L1"], p["L2"], p["tcp_z_at_d0"], p["limits"])

    # ------------------------------------------------------------ 기본 정보
    @property
    def reach_max(self) -> float:
        return self.L1 + self.L2

    @property
    def reach_min(self) -> float:
        """theta2 한계에서 접힌 팔의 최소 반경."""
        t2 = math.radians(self.limits["theta2_deg"][1])
        return math.sqrt(self.L1**2 + self.L2**2 + 2 * self.L1 * self.L2 * math.cos(t2))

    # ------------------------------------------------------------ 정기구학
    def fk(self, q):
        """q=(theta1, theta2, d3, theta4) -> (x, y, z, yaw)."""
        t1, t2, d3, t4 = q
        x = self.L1 * math.cos(t1) + self.L2 * math.cos(t1 + t2)
        y = self.L1 * math.sin(t1) + self.L2 * math.sin(t1 + t2)
        z = self.tcp_z_at_d0 - d3
        yaw = t1 + t2 + t4
        return x, y, z, yaw

    def elbow_xy(self, q):
        """J2(팔꿈치) 위치."""
        t1 = q[0]
        return self.L1 * math.cos(t1), self.L1 * math.sin(t1)

    # ------------------------------------------------------------ 역기구학
    def ik(self, x, y, z, yaw=0.0, elbow="right"):
        """(x, y, z, yaw) -> q.  elbow: 'right'(theta2<0) 또는 'left'(theta2>0).

        도달 불가 / 관절 한계 초과면 ValueError.
        """
        r2 = x * x + y * y
        c2 = (r2 - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        if c2 > 1 + 1e-9 or c2 < -1 - 1e-9:
            raise ValueError(f"도달 불가: 반경 {math.sqrt(r2):.1f} mm (허용 {self.reach_min:.1f}~{self.reach_max:.1f})")
        c2 = max(-1.0, min(1.0, c2))
        s2 = math.sqrt(1 - c2 * c2)
        if elbow == "right":
            s2 = -s2
        elif elbow != "left":
            raise ValueError("elbow 는 'right' 또는 'left'")
        t2 = math.atan2(s2, c2)
        t1 = math.atan2(y, x) - math.atan2(self.L2 * s2, self.L1 + self.L2 * c2)
        t1 = wrap(t1)
        d3 = self.tcp_z_at_d0 - z
        t4 = wrap(yaw - t1 - t2)
        q = (t1, t2, d3, t4)
        self.check_limits(q)
        return q

    def ik_best(self, x, y, z, yaw=0.0, q_now=None):
        """두 팔꿈치 해 중 관절 한계 안에 있고 현재 자세에서 가장 가까운 해."""
        sols = []
        for elbow in ("right", "left"):
            try:
                sols.append(self.ik(x, y, z, yaw, elbow))
            except ValueError as e:
                err = e
        if not sols:
            raise err  # noqa: F821  (마지막 오류를 그대로 전달)
        if q_now is None:
            return sols[0]
        return min(sols, key=lambda q: abs(q[0] - q_now[0]) + abs(q[1] - q_now[1]))

    # ------------------------------------------------------------ 안전 검사
    def check_limits(self, q):
        names = [("theta1_deg", True), ("theta2_deg", True), ("d3_mm", False), ("theta4_deg", True)]
        for v, (key, is_angle) in zip(q, names):
            lo, hi = self.limits[key]
            val = math.degrees(v) if is_angle else v
            if val < lo - 1e-6 or val > hi + 1e-6:
                raise ValueError(f"관절 한계 초과: {key}={val:.2f} (허용 {lo}~{hi})")


def wrap(a):
    """각도를 (-pi, pi] 로."""
    return math.atan2(math.sin(a), math.cos(a))


# ---------------------------------------------------------------- 궤적
def smoothstep5(s):
    """0..1 -> 0..1, 시작·끝 속도·가속도 0 (5차 다항식)."""
    return s * s * s * (10 - 15 * s + 6 * s * s)


def joint_trajectory(q0, q1, duration, dt=0.01):
    """관절 공간 보간. [(t, q), ...]"""
    n = max(1, int(round(duration / dt)))
    out = []
    for i in range(n + 1):
        s = smoothstep5(i / n)
        out.append((i * dt, tuple(a + (b - a) * s for a, b in zip(q0, q1))))
    return out


def cartesian_line(robot: Scara, p0, p1, duration, dt=0.01, q_now=None):
    """TCP 직선 보간(매 점마다 IK). p=(x, y, z, yaw)."""
    n = max(1, int(round(duration / dt)))
    out, q = [], q_now
    for i in range(n + 1):
        s = smoothstep5(i / n)
        p = [a + (b - a) * s for a, b in zip(p0, p1)]
        q = robot.ik_best(*p, q_now=q)
        out.append((i * dt, q))
    return out


def min_duration(robot_params_path: Path, q0, q1):
    """속도 한계(scara_params.max_speed)를 지키는 최소 이동 시간 [s] (5차 보간의 최고속도 = 1.875*평균)."""
    p = json.loads(Path(robot_params_path).read_text(encoding="utf-8"))["max_speed"]
    vmax = [math.radians(p["theta1_dps"]), math.radians(p["theta2_dps"]), p["d3_mmps"], math.radians(p["theta4_dps"])]
    return max(1.875 * abs(b - a) / v for a, b, v in zip(q0, q1, vmax))


if __name__ == "__main__":
    r = Scara.load()
    print(f"L1={r.L1} L2={r.L2}  작업 반경 {r.reach_min:.1f} ~ {r.reach_max:.1f} mm")
    q = r.ik(300, 150, 15, math.radians(0))
    print("IK(300,150,15,0°) ->", [round(math.degrees(v), 2) if i != 2 else round(v, 2) for i, v in enumerate(q)])
    print("FK 확인 ->", [round(v, 3) for v in r.fk(q)])
