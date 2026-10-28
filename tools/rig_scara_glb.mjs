// sceliph 가 만든 평면(flat) SCARA GLB 를 관절 계층이 있는 GLB 로 바꾼다.
//
//   node tools/rig_scara_glb.mjs models/scara/scara_sceliph_flat.glb models/scara/scara_rigged.glb
//
// 결과 계층 (glTF Y-up, 단위 m):
//   scara_root
//     base_link            (base__*)
//     joint1  [회전 +Y]     (link1__*)
//       joint2 [회전 +Y]    (link2__*)
//         joint3 [이동 -Y]  quill 직동
//           joint4 [회전 +Y] (quill__*)
//             finger_left_joint  [이동 +로컬 -Z = 로봇 +y]  (fingerL__*)
//             finger_right_joint [이동 +로컬 +Z = 로봇 -y]  (fingerR__*)
//
// 홈 자세의 모든 관절 회전은 단위 회전이므로 부품의 로컬 위치 = 월드 위치 - 관절 월드 위치.
import { readFileSync } from 'node:fs';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';

const [, , input, output] = process.argv;
if (!input || !output) throw new Error('usage: rig_scara_glb.mjs <flat.glb> <rigged.glb>');

const params = JSON.parse(readFileSync(new URL('../model/scara_params.json', import.meta.url), 'utf8'));
const mm = (v) => v / 1000;
const L1 = params.L1, L2 = params.L2, H1 = params.j1_height;

// 관절 월드 위치(m, glTF 좌표)
const JOINTS = {
  base_link: [0, 0, 0],
  joint1: [0, mm(H1), 0],
  joint2: [mm(L1), mm(H1), 0],
  joint3: [mm(L1 + L2), mm(H1), 0],
  joint4: [mm(L1 + L2), mm(H1), 0],
  finger_left_joint: [mm(L1 + L2), mm(H1), 0],
  finger_right_joint: [mm(L1 + L2), mm(H1), 0],
};
const PARENT = {
  base_link: 'scara_root',
  joint1: 'scara_root',
  joint2: 'joint1',
  joint3: 'joint2',
  joint4: 'joint3',
  finger_left_joint: 'joint4',
  finger_right_joint: 'joint4',
};
const GROUP = {
  base: 'base_link',
  link1: 'joint1',
  link2: 'joint2',
  quill: 'joint4',
  fingerL: 'finger_left_joint',
  fingerR: 'finger_right_joint',
};

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(input);
const scene = doc.getRoot().getDefaultScene() ?? doc.getRoot().listScenes()[0];
const [assemblyRoot] = scene.listChildren();

const root = doc.createNode('scara_root');
root.setExtras({
  robot_study: {
    description: 'RS-450 학습용 SCARA. 관절 노드 이름으로 자세를 바꾼다.',
    joints: {
      joint1: { type: 'revolute', axis: '+Y(glTF) = +Z(robot)', limit_deg: params.limits.theta1_deg },
      joint2: { type: 'revolute', axis: '+Y(glTF) = +Z(robot)', limit_deg: params.limits.theta2_deg },
      joint3: { type: 'prismatic', axis: '-Y(glTF) = -Z(robot)', limit_mm: params.limits.d3_mm },
      joint4: { type: 'revolute', axis: '+Y(glTF) = +Z(robot)', limit_deg: params.limits.theta4_deg },
      finger_left_joint: { type: 'prismatic', axis: '-Z(glTF) = +y(robot)', note: 'gap/2 - 25 mm 만큼 이동' },
      finger_right_joint: { type: 'prismatic', axis: '+Z(glTF) = -y(robot)', note: 'gap/2 - 25 mm 만큼 이동' },
    },
    params,
  },
});
const nodes = { scara_root: root };
for (const name of Object.keys(JOINTS)) nodes[name] = doc.createNode(name);
for (const [name, parentName] of Object.entries(PARENT)) {
  const world = JOINTS[name];
  const parentWorld = JOINTS[parentName] ?? [0, 0, 0];
  nodes[name].setTranslation(world.map((v, i) => v - parentWorld[i]));
  nodes[parentName].addChild(nodes[name]);
}

let moved = 0;
for (const part of [...assemblyRoot.listChildren()]) {
  const prefix = part.getName().split('__')[0];
  const jointName = GROUP[prefix];
  if (!jointName) throw new Error(`rig group 이 없는 부품: ${part.getName()}`);
  const world = part.getTranslation();
  const jw = JOINTS[jointName];
  assemblyRoot.removeChild(part);
  part.setTranslation(world.map((v, i) => v - jw[i]));
  nodes[jointName].addChild(part);
  moved += 1;
}

root.setExtras({ ...root.getExtras(), source_ir: assemblyRoot.getExtras() });
scene.removeChild(assemblyRoot);
assemblyRoot.dispose();
scene.addChild(root);

await io.write(output, doc);
console.log(`rigged ${moved} parts -> ${output}`);
