"""리깅 GLB를 Blender로 불러와 자세를 바꿔 렌더한다 (README 이미지용).

blender --background --python tools/blender_render.py -- models/scara/scara_rigged.glb media/out.png \
    --theta1 30 --theta2 -60 --d3 80 --theta4 0 --gap 50 [--view iso|front|top]
"""
import argparse
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("glb")
ap.add_argument("out")
ap.add_argument("--theta1", type=float, default=0)
ap.add_argument("--theta2", type=float, default=0)
ap.add_argument("--d3", type=float, default=0)
ap.add_argument("--theta4", type=float, default=0)
ap.add_argument("--gap", type=float, default=50)
ap.add_argument("--view", default="iso")
ap.add_argument("--size", type=int, default=1200)
a = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
obj = {o.name: o for o in bpy.data.objects}

# glTF Y-up 은 Blender 에서 Z-up 으로 변환된다: glTF +Y 회전 = Blender +Z 회전, glTF -Z = Blender +Y
obj["joint1"].rotation_mode = "XYZ"
obj["joint1"].rotation_euler[2] = math.radians(a.theta1)
obj["joint2"].rotation_mode = "XYZ"
obj["joint2"].rotation_euler[2] = math.radians(a.theta2)
obj["joint3"].location[2] -= a.d3 / 1000
obj["joint4"].rotation_mode = "XYZ"
obj["joint4"].rotation_euler[2] = math.radians(a.theta4)
off = (a.gap / 2 - 25) / 1000
obj["finger_left_joint"].location[1] += off
obj["finger_right_joint"].location[1] -= off

# 작업대
bpy.ops.mesh.primitive_plane_add(size=8, location=(0.15, 0, 0))
table = bpy.context.object
mat = bpy.data.materials.new("table")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1)
mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
table.data.materials.append(mat)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x = a.size
scene.render.resolution_y = int(a.size * 0.75)
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.93, 0.94, 0.96, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

for loc, energy, size in [((1.2, -1.0, 1.6), 260, 1.5), ((-1.0, 1.2, 1.2), 90, 2.0), ((0.2, 1.5, 0.6), 50, 1.0)]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.rotation_euler = (Vector((0.15, 0, 0.25)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

target = Vector((0.17, 0, 0.24))
cams = {"iso": (1.05, -0.95, 0.72), "front": (0.2, -1.4, 0.3), "top": (0.17, 0.0, 1.5)}
bpy.ops.object.camera_add(location=cams[a.view])
cam = bpy.context.object
cam.data.lens = 45
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
if a.view == "top":
    cam.rotation_euler = (0, 0, 0)
scene.camera = cam
scene.render.filepath = a.out
bpy.ops.render.render(write_still=True)
print("rendered", a.out)
