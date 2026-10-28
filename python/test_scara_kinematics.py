"""python3 -m pytest python/  또는  python3 python/test_scara_kinematics.py"""
import math
import random

from scara_kinematics import PARAMS_PATH, Scara, cartesian_line, joint_trajectory, min_duration

R = Scara.load()


def test_home_pose():
    x, y, z, yaw = R.fk((0, 0, 0, 0))
    assert (round(x, 6), round(y, 6), z, yaw) == (450, 0, 121, 0)


def test_fk_ik_roundtrip_random():
    rng = random.Random(7)
    checked = 0
    while checked < 2000:
        q = (math.radians(rng.uniform(-132, 132)), math.radians(rng.uniform(-145, 145)),
             rng.uniform(0, 180), math.radians(rng.uniform(-170, 170)))
        if abs(q[1]) < 1e-3:
            continue
        p = R.fk(q)
        elbow = "right" if q[1] < 0 else "left"
        try:
            q2 = R.ik(*p, elbow=elbow)
        except ValueError:
            continue  # wrap 으로 theta4 가 한계를 넘는 드문 경우
        p2 = R.fk(q2)
        assert all(abs(a - b) < 1e-6 for a, b in zip(p[:3], p2[:3]))
        assert abs(math.atan2(math.sin(p[3] - p2[3]), math.cos(p[3] - p2[3]))) < 1e-9
        checked += 1


def test_unreachable_rejected():
    for x, y in [(500, 0), (0, 0), (60, 60)]:
        try:
            R.ik(x, y, 50)
        except ValueError:
            continue
        raise AssertionError(f"({x},{y}) 는 거부되어야 한다")


def test_z_limit_rejected():
    try:
        R.ik(300, 0, 121 - 200)  # d3 = 200 > 180
    except ValueError:
        return
    raise AssertionError("d3 한계 초과가 거부되어야 한다")


def test_trajectory_endpoints_and_line():
    q0, q1 = (0, 0, 0, 0), R.ik(300, 150, 15)
    traj = joint_trajectory(q0, q1, 1.0)
    assert traj[0][1] == q0 and all(abs(a - b) < 1e-12 for a, b in zip(traj[-1][1], q1))
    line = cartesian_line(R, (300, -100, 60, 0), (300, 100, 60, 0), 1.0)
    for _, q in line:
        x, y, z, _ = R.fk(q)
        assert abs(x - 300) < 1e-6 and abs(z - 60) < 1e-6
    assert min_duration(PARAMS_PATH, q0, q1) > 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
