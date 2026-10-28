// GLB 노드 계층과 전체 크기를 출력한다.  node tools/inspect_glb.mjs <file.glb>
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { getBounds } from '@gltf-transform/core';

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(process.argv[2]);
const scene = doc.getRoot().getDefaultScene() ?? doc.getRoot().listScenes()[0];
const walk = (n, d) => {
  const t = n.getTranslation().map((v) => (v * 1000).toFixed(1)).join(', ');
  console.log(`${'  '.repeat(d)}${n.getName()}${n.getMesh() ? ' [mesh]' : ''}  t(mm)=(${t})`);
  n.listChildren().forEach((c) => walk(c, d + 1));
};
scene.listChildren().forEach((n) => walk(n, 0));
const b = getBounds(scene);
console.log('bounds(mm) min', b.min.map((v) => Math.round(v * 1000)), 'max', b.max.map((v) => Math.round(v * 1000)));
console.log('meshes', doc.getRoot().listMeshes().length, 'materials', doc.getRoot().listMaterials().length);
