// robot_study SCARA 웹 시뮬레이터
// - 로봇 좌표: Z-up, mm.  three.js: Y-up, m.   r2t / t2r 로 변환한다.
// - AI(또는 사람)는 허용 행동 JSON만 만든다. 이 파일의 안전 게이트가 검사하고, STOP이 항상 우선이다.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const $ = (id) => document.getElementById(id);
const DEG = Math.PI / 180;
// index.html 의 sim.js?v=… 를 모든 자산 주소에 붙여, 모델을 다시 만들면 브라우저 캐시를 건너뛴다
const V = new URL(import.meta.url).searchParams.get('v') ?? 'dev';
const asset = (path) => `${path}?v=${V}`;
const [P, SCENE] = await Promise.all([
  fetch(asset('scara_params.json')).then((r) => r.json()),
  fetch(asset('task_scene.json')).then((r) => r.json()),
]);
const { L1, L2 } = P;
const LIM = P.limits;
const BLOCK = SCENE.block_size;

// ------------------------------------------------------------------ 좌표 변환
const r2t = (x, y, z) => new THREE.Vector3(x / 1000, z / 1000, -y / 1000);
const t2r = (v) => [v.x * 1000, -v.z * 1000, v.y * 1000];

// ------------------------------------------------------------------ 기구학 (python/scara_kinematics.py 와 같은 식)
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
function fk([t1, t2, d3, t4]) {
  return [
    L1 * Math.cos(t1) + L2 * Math.cos(t1 + t2),
    L1 * Math.sin(t1) + L2 * Math.sin(t1 + t2),
    P.tcp_z_at_d0 - d3,
    t1 + t2 + t4,
  ];
}
function checkLimits(q) {
  const keys = [['theta1_deg', true], ['theta2_deg', true], ['d3_mm', false], ['theta4_deg', true]];
  keys.forEach(([k, ang], i) => {
    const v = ang ? q[i] / DEG : q[i];
    const [lo, hi] = LIM[k];
    if (v < lo - 1e-6 || v > hi + 1e-6) throw new Error(`관절 한계 초과: ${k}=${v.toFixed(1)} (허용 ${lo}~${hi})`);
  });
}
function ik(x, y, z, yaw, elbow) {
  const r2 = x * x + y * y;
  let c2 = (r2 - L1 * L1 - L2 * L2) / (2 * L1 * L2);
  if (c2 > 1 + 1e-9 || c2 < -1 - 1e-9) throw new Error(`도달 불가: 반경 ${Math.sqrt(r2).toFixed(1)} mm (최대 ${L1 + L2})`);
  c2 = Math.max(-1, Math.min(1, c2));
  const s2 = (elbow === 'right' ? -1 : 1) * Math.sqrt(1 - c2 * c2);
  const t2 = Math.atan2(s2, c2);
  const t1 = wrap(Math.atan2(y, x) - Math.atan2(L2 * s2, L1 + L2 * c2));
  const q = [t1, t2, P.tcp_z_at_d0 - z, wrap(yaw - t1 - t2)];
  checkLimits(q);
  return q;
}
function ikBest(x, y, z, yaw, qNow) {
  const sols = []; let err;
  for (const e of ['right', 'left']) { try { sols.push(ik(x, y, z, yaw, e)); } catch (ex) { err = ex; } }
  if (!sols.length) throw err;
  if (!qNow) return sols[0];
  return sols.reduce((a, b) => (Math.abs(a[0] - qNow[0]) + Math.abs(a[1] - qNow[1]) <= Math.abs(b[0] - qNow[0]) + Math.abs(b[1] - qNow[1]) ? a : b));
}

// ------------------------------------------------------------------ 장면
const view = $('view');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.9;
view.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(matchMedia('(prefers-color-scheme: dark)').matches ? 0x1a1d22 : 0xe9ebef);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const camera = new THREE.PerspectiveCamera(40, 1, 0.01, 20);
camera.position.set(0.95, 0.75, 0.85);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0.18, 0.15, 0);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f99, 0.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(0.8, 1.6, 0.6);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -0.8, right: 0.8, top: 0.8, bottom: -0.8, near: 0.1, far: 4 });
scene.add(sun);

const table = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.02, 1.2), new THREE.MeshStandardMaterial({ color: 0xc9ccd2, roughness: 0.85 }));
table.position.set(0.15, -0.01, 0);
table.receiveShadow = true;
scene.add(table);
const grid = new THREE.GridHelper(1.2, 24, 0x9aa0a8, 0xb5bac1);
grid.position.set(0.15, 0.0005, 0);
scene.add(grid);
const axes = new THREE.AxesHelper(0.08); // 빨강=+X, 초록=three Y(=로봇 Z), 파랑=three Z(=로봇 -Y)
axes.position.set(-0.25, 0.001, 0.3);
scene.add(axes);

function label(text, color = '#222') {
  const c = document.createElement('canvas'); c.width = 256; c.height = 64;
  const g = c.getContext('2d'); g.font = 'bold 40px system-ui'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 8; g.strokeStyle = 'rgba(255,255,255,0.9)'; g.strokeText(text, 128, 32);
  g.fillStyle = color; g.fillText(text, 128, 32);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthWrite: false }));
  sp.scale.set(0.1, 0.025, 1);
  return sp;
}

// 목표 트레이
for (const [name, t] of Object.entries(SCENE.targets)) {
  const tray = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.002, 0.06), new THREE.MeshStandardMaterial({ color: 0xffc21a, roughness: 0.6 }));
  tray.position.copy(r2t(t.x, t.y, 1));
  tray.receiveShadow = true;
  scene.add(tray);
  const l = label(name, '#7a5600'); l.position.copy(r2t(t.x, t.y, 70)); scene.add(l);
}

// 블록
const blocks = {};
function resetBlocks() {
  for (const b of Object.values(blocks)) b.parent.remove(b);
  for (const [name, o] of Object.entries(SCENE.objects)) {
    const s = BLOCK / 1000;
    const m = new THREE.Mesh(new THREE.BoxGeometry(s, s, s), new THREE.MeshStandardMaterial({ color: o.color, roughness: 0.5 }));
    m.name = name; m.castShadow = true; m.receiveShadow = true;
    m.position.copy(r2t(o.x, o.y, BLOCK / 2));
    scene.add(m);
    blocks[name] = m;
  }
  held = null;
}
const blockPos = (name) => t2r(blocks[name].getWorldPosition(new THREE.Vector3()));

// 작업영역 점구름 (IK가 성공하는 점만)
const wsPts = [];
for (let x = -460; x <= 460; x += 12) for (let y = -460; y <= 460; y += 12) {
  try { ik(x, y, 60, 0, 'right'); wsPts.push(x / 1000, 0.002, -y / 1000); continue; } catch { /* 다른 팔꿈치 */ }
  try { ik(x, y, 60, 0, 'left'); wsPts.push(x / 1000, 0.002, -y / 1000); } catch { /* 도달 불가 */ }
}
const wsGeom = new THREE.BufferGeometry(); wsGeom.setAttribute('position', new THREE.Float32BufferAttribute(wsPts, 3));
const workspace = new THREE.Points(wsGeom, new THREE.PointsMaterial({ color: 0x2f6fdf, size: 0.004, transparent: true, opacity: 0.55 }));
workspace.visible = false;
scene.add(workspace);

// 로봇
const gltf = await new GLTFLoader().loadAsync(asset('models/scara_rigged.glb'));
const robot = gltf.scene;
robot.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
scene.add(robot);
const J = Object.fromEntries(['joint1', 'joint2', 'joint3', 'joint4', 'finger_left_joint', 'finger_right_joint'].map((n) => {
  const node = robot.getObjectByName(n);
  if (!node) throw new Error(`GLB 에 ${n} 노드가 없다`);
  return [n, node];
}));
const tcpMarker = new THREE.Mesh(new THREE.SphereGeometry(0.003), new THREE.MeshBasicMaterial({ color: 0xff2020 }));
scene.add(tcpMarker);

// ------------------------------------------------------------------ 상태
let q = [0, 0, 0, 0];
let gap = P.gripper_gap_home_mm;
let held = null;
let running = false;
let stopFlag = false;
resetBlocks();

function applyPose() {
  J.joint1.rotation.y = q[0];
  J.joint2.rotation.y = q[1];
  J.joint3.position.y = -q[2] / 1000;
  J.joint4.rotation.y = q[3];
  const off = (gap / 2 - P.gripper_gap_home_mm / 2) / 1000;
  J.finger_left_joint.position.z = -off;
  J.finger_right_joint.position.z = off;
  const [x, y, z, yaw] = fk(q);
  tcpMarker.position.copy(r2t(x, y, z));
  $('hud').textContent =
    `θ1 ${(q[0] / DEG).toFixed(1).padStart(7)}°   θ2 ${(q[1] / DEG).toFixed(1).padStart(7)}°\n` +
    `d3 ${q[2].toFixed(1).padStart(7)}mm  θ4 ${(q[3] / DEG).toFixed(1).padStart(7)}°\n` +
    `TCP x ${x.toFixed(1)}  y ${y.toFixed(1)}  z ${z.toFixed(1)} mm\n` +
    `yaw ${(wrap(yaw) / DEG).toFixed(1)}°  gripper ${gap.toFixed(1)} mm  held ${held ?? '-'}`;
  $('hud').style.whiteSpace = 'pre';
  syncSliders();
}

// ------------------------------------------------------------------ UI: 슬라이더
const SL = [
  ['θ1', 'theta1_deg', (v) => (q[0] = v * DEG), () => q[0] / DEG, '°'],
  ['θ2', 'theta2_deg', (v) => (q[1] = v * DEG), () => q[1] / DEG, '°'],
  ['d3', 'd3_mm', (v) => (q[2] = v), () => q[2], 'mm'],
  ['θ4', 'theta4_deg', (v) => (q[3] = v * DEG), () => q[3] / DEG, '°'],
  ['gripper', 'gripper_gap_mm', (v) => (gap = v), () => gap, 'mm'],
];
const sliderEls = SL.map(([lab, key, set, , unit]) => {
  const row = document.createElement('div'); row.className = 'row';
  const [lo, hi] = LIM[key];
  row.innerHTML = `<label>${lab}</label><input type="range" min="${lo}" max="${hi}" step="0.5"><output></output>`;
  const input = row.querySelector('input');
  input.addEventListener('input', () => {
    if (running) return;
    if (key === 'gripper_gap_mm' && held) { log('물체를 잡은 상태에서는 그리퍼 슬라이더를 쓸 수 없다. open_gripper 사용', 'warn'); return; }
    set(Number(input.value)); applyPose();
  });
  $('sliders').append(row);
  return { input, out: row.querySelector('output'), unit };
});
function syncSliders() {
  SL.forEach(([, , , get], i) => {
    const v = get();
    if (document.activeElement !== sliderEls[i].input) sliderEls[i].input.value = v;
    sliderEls[i].out.textContent = `${v.toFixed(1)}${sliderEls[i].unit}`;
    sliderEls[i].input.disabled = running;
  });
}

// ------------------------------------------------------------------ 로그
function log(msg, cls = '') {
  const line = document.createElement('div'); line.className = cls; line.textContent = msg;
  $('log').append(line); $('log').scrollTop = $('log').scrollHeight;
}
function setState(s) { const el = $('state'); el.textContent = s; el.className = `state ${s === 'RUNNING' ? 'run' : s === 'STOPPED' ? 'stop' : 'idle'}`; }

// ------------------------------------------------------------------ 동작 실행기
class StopError extends Error {}
const nextFrame = () => new Promise((r) => requestAnimationFrame(r));
function moveDuration(q0, q1, g0, g1) {
  const v = P.max_speed;
  const vmax = [v.theta1_dps * DEG, v.theta2_dps * DEG, v.d3_mmps, v.theta4_dps * DEG];
  let T = Math.max(...q0.map((a, i) => (1.875 * Math.abs(q1[i] - a)) / vmax[i]), (1.875 * Math.abs(g1 - g0)) / v.gripper_mmps);
  return Math.max(0.15, T) / Number($('speed').value);
}
const s5 = (s) => s * s * s * (10 - 15 * s + 6 * s * s);
async function animateTo(q1, g1 = gap) {
  const q0 = q.slice(), g0 = gap;
  const T = moveDuration(q0, q1, g0, g1) * 1000;
  const t0 = performance.now();
  for (;;) {
    if (stopFlag) throw new StopError();
    const s = Math.min(1, (performance.now() - t0) / T);
    const k = s5(s);
    q = q0.map((a, i) => a + (q1[i] - a) * k);
    gap = g0 + (g1 - g0) * k;
    applyPose();
    if (s >= 1) return;
    await nextFrame();
  }
}
async function moveTcp(x, y, z, yawDeg = 0) {
  const q1 = ikBest(x, y, z, yawDeg * DEG, q);
  await animateTo(q1);
}
async function wait(sec) {
  const t0 = performance.now();
  while (performance.now() - t0 < (sec * 1000) / Number($('speed').value)) { if (stopFlag) throw new StopError(); await nextFrame(); }
}
function supportTop(x, y, except) {
  let top = 0;
  for (const [n] of Object.entries(blocks)) {
    if (n === except) continue;
    const [bx, by, bz] = blockPos(n);
    if (Math.hypot(bx - x, by - y) < BLOCK * 0.7) top = Math.max(top, bz + BLOCK / 2);
  }
  return top;
}
async function closeGripper() {
  const [x, y, z] = fk(q);
  const cand = Object.keys(blocks).find((n) => {
    const [bx, by, bz] = blockPos(n);
    return n !== held && Math.hypot(bx - x, by - y) < 6 && Math.abs(bz - z) < 8;
  });
  if (cand) {
    await animateTo(q, BLOCK);
    J.joint4.attach(blocks[cand]);
    held = cand;
    log(`  파지: ${cand}`, 'ok');
  } else {
    await animateTo(q, SCENE.grip_closed_mm);
    log('  닫음: 손가락 사이에 물체 없음', 'warn');
  }
}
async function openGripper() {
  await animateTo(q, SCENE.grip_open_mm);
  if (held) {
    const b = blocks[held];
    scene.attach(b);
    const [bx, by] = t2r(b.position);
    const top = supportTop(bx, by, held);
    b.position.copy(r2t(bx, by, top + BLOCK / 2)); // 받침 위로 떨어뜨림(운동학 근사)
    b.rotation.set(0, b.rotation.y, 0);
    log(`  놓음: ${held} (z=${(top + BLOCK / 2).toFixed(1)} mm)`, 'ok');
    held = null;
  }
}

const ACTIONS = {
  async home() { await animateTo([0, 0, 0, 0]); },
  async move_to(t) { await moveTcp(t.x, t.y, t.z ?? SCENE.z_safe, t.yaw_deg ?? 0); },
  async open_gripper() { await openGripper(); },
  async close_gripper() { await closeGripper(); },
  async wait(t) { await wait(t.seconds ?? 0.5); },
  async pick(t) {
    if (held) throw new Error(`이미 ${held} 를 잡고 있다`);
    const [x, y, z] = blockPos(t.object);
    if (supportTop(x, y, t.object) > z + 1) throw new Error(`${t.object} 위에 다른 블록이 있다`);
    await openGripper();
    await moveTcp(x, y, SCENE.z_safe);
    await moveTcp(x, y, z);
    await closeGripper();
    if (held !== t.object) throw new Error(`${t.object} 파지 실패`);
    await moveTcp(x, y, SCENE.z_safe);
  },
  async place(t) {
    if (!held) throw new Error('잡은 물체가 없다');
    const g = SCENE.targets[t.target];
    const top = supportTop(g.x, g.y, held);
    await moveTcp(g.x, g.y, SCENE.z_safe);
    await moveTcp(g.x, g.y, top + BLOCK / 2 + 1);
    await openGripper();
    await moveTcp(g.x, g.y, SCENE.z_safe);
  },
};

// ------------------------------------------------------------------ 안전 게이트 (실행 전 정적 검사)
const FIELDS = {
  home: {}, open_gripper: {}, close_gripper: {}, stop: {},
  move_to: { x: 'number', y: 'number', z: 'number?', yaw_deg: 'number?' },
  pick: { object: 'object' }, place: { target: 'target' }, wait: { seconds: 'number?' },
};
function validatePlan(text) {
  const errors = [], warnings = [];
  let plan;
  try { plan = JSON.parse(text); } catch (e) { return { errors: [`JSON 문법 오류: ${e.message}`], warnings }; }
  if (!plan || !Array.isArray(plan.tasks)) return { errors: ['최상위는 {"tasks": [...]} 형식이어야 한다'], warnings };
  if (plan.tasks.length === 0 || plan.tasks.length > 60) errors.push(`작업 수 ${plan.tasks.length}: 1~60 개만 허용`);
  let holding = null; let stopped = false; let qSim = q.slice();
  plan.tasks.forEach((t, i) => {
    const tag = `#${i}`;
    if (stopped) { warnings.push(`${tag} stop 뒤의 작업은 실행하지 않는다`); return; }
    if (!t || typeof t !== 'object') { errors.push(`${tag} 객체가 아니다`); return; }
    const spec = FIELDS[t.action];
    if (!SCENE.allowed_actions.includes(t.action) || !spec) { errors.push(`${tag} 허용되지 않은 행동 "${t.action}" (허용: ${SCENE.allowed_actions.join(', ')})`); return; }
    for (const k of Object.keys(t)) if (k !== 'action' && !(k in spec) && k !== 'note') warnings.push(`${tag} 알 수 없는 필드 "${k}" 무시`);
    for (const [k, type] of Object.entries(spec)) {
      const v = t[k]; const optional = type.endsWith('?');
      if (v === undefined) { if (!optional) errors.push(`${tag} ${t.action}: "${k}" 필요`); continue; }
      if (type.startsWith('number') && !(typeof v === 'number' && Number.isFinite(v))) errors.push(`${tag} ${k} 는 숫자여야 한다`);
      if (type === 'object' && !(v in SCENE.objects)) errors.push(`${tag} 알 수 없는 물체 "${v}" (가능: ${Object.keys(SCENE.objects).join(', ')})`);
      if (type === 'target' && !(v in SCENE.targets)) errors.push(`${tag} 알 수 없는 목표 "${v}" (가능: ${Object.keys(SCENE.targets).join(', ')})`);
    }
    if (t.action === 'move_to' && typeof t.x === 'number' && typeof t.y === 'number') {
      const z = t.z ?? SCENE.z_safe;
      if (z < BLOCK / 2 - 0.5) errors.push(`${tag} z=${z} 는 작업대와 충돌 위험 (최소 ${BLOCK / 2})`);
      try { qSim = ikBest(t.x, t.y, z, (t.yaw_deg ?? 0) * DEG, qSim); } catch (e) { errors.push(`${tag} move_to: ${e.message}`); }
    }
    if (t.action === 'wait' && t.seconds !== undefined && (t.seconds < 0 || t.seconds > 10)) errors.push(`${tag} wait 는 0~10 초`);
    if (t.action === 'pick') { if (holding) errors.push(`${tag} 이미 ${holding} 를 잡은 상태에서 pick`); holding = t.object; }
    if (t.action === 'place') { if (!holding) errors.push(`${tag} 잡은 물체 없이 place`); holding = null; }
    if (t.action === 'open_gripper') holding = null;
    if (t.action === 'stop') stopped = true;
  });
  if (holding) warnings.push(`계획이 ${holding} 를 든 채로 끝난다`);
  return { plan, errors, warnings };
}

async function runPlan() {
  if (running) return;
  $('log').textContent = '';
  const { plan, errors, warnings } = validatePlan($('plan').value);
  warnings.forEach((w) => log(`경고 ${w}`, 'warn'));
  if (errors.length) { errors.forEach((e) => log(`거부 ${e}`, 'err')); log('안전 게이트: 계획 전체를 거부했다. 아무 동작도 하지 않았다.', 'err'); return; }
  log(`안전 게이트 통과: ${plan.tasks.length} 개 작업`, 'ok');
  running = true; stopFlag = false; setState('RUNNING'); syncSliders();
  try {
    for (const [i, t] of plan.tasks.entries()) {
      if (t.action === 'stop') { log(`#${i} stop: 계획에 따라 정지`, 'warn'); break; }
      log(`#${i} ${t.action}${t.object ? ` ${t.object}` : ''}${t.target ? ` → ${t.target}` : ''}`);
      await ACTIONS[t.action](t);
    }
    log('완료', 'ok'); setState('IDLE');
  } catch (e) {
    if (e instanceof StopError) { log('STOP: 즉시 정지했다. 남은 작업은 취소됐다.', 'err'); setState('STOPPED'); }
    else { log(`실행 중 안전 정지: ${e.message}`, 'err'); setState('STOPPED'); }
  } finally { running = false; stopFlag = false; syncSliders(); }
}

// ------------------------------------------------------------------ 버튼
const EXAMPLE = {
  tasks: [
    { action: 'pick', object: 'red' }, { action: 'place', target: 'tray_A' },
    { action: 'pick', object: 'blue' }, { action: 'place', target: 'tray_B' },
    { action: 'pick', object: 'green' }, { action: 'place', target: 'tray_A' },
    { action: 'home' },
  ],
};
$('plan').value = JSON.stringify(EXAMPLE, null, 2);
$('example').onclick = () => { $('plan').value = JSON.stringify(EXAMPLE, null, 2); };
$('run').onclick = runPlan;
$('validate').onclick = () => {
  $('log').textContent = '';
  const { plan, errors, warnings } = validatePlan($('plan').value);
  warnings.forEach((w) => log(`경고 ${w}`, 'warn'));
  errors.forEach((e) => log(`거부 ${e}`, 'err'));
  if (!errors.length) log(`통과: ${plan.tasks.length} 개 작업 (실행 전 현재 장면 기준 정적 검사)`, 'ok');
};
const stopNow = () => { if (running) { stopFlag = true; } else { log('STOP: 실행 중인 작업 없음', 'warn'); } };
$('stop').onclick = stopNow;
addEventListener('keydown', (e) => { if (e.code === 'Space' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'INPUT') { e.preventDefault(); stopNow(); } });
$('reset').onclick = () => { if (running) return; resetBlocks(); q = [0, 0, 0, 0]; gap = P.gripper_gap_home_mm; applyPose(); setState('IDLE'); $('log').textContent = ''; };
$('home').onclick = () => { if (!running) { $('plan').value = JSON.stringify({ tasks: [{ action: 'home' }] }); runPlan(); } };
$('ws').onclick = () => { workspace.visible = !workspace.visible; };
$('speed').oninput = () => { $('speedv').textContent = `${Number($('speed').value).toFixed(1)}×`; };
$('ikgo').onclick = async () => {
  if (running) return;
  const [x, y, z, yaw] = ['ikx', 'iky', 'ikz', 'ikyaw'].map((id) => Number($(id).value));
  $('plan').value = JSON.stringify({ tasks: [{ action: 'move_to', x, y, z, yaw_deg: yaw }] }, null, 2);
  await runPlan();
};
$('copyprompt').onclick = async () => {
  const objs = Object.keys(blocks).map((n) => { const [x, y, z] = blockPos(n).map((v) => Math.round(v)); return `- ${n}: x=${x}, y=${y}, z=${z}${held === n ? ' (그리퍼가 잡고 있음)' : ''}`; }).join('\n');
  const tg = Object.entries(SCENE.targets).map(([n, t]) => `- ${n}: x=${t.x}, y=${t.y}`).join('\n');
  const text = `너는 SCARA 로봇의 "작업 계획기"다. 모터 명령이 아니라 허용된 행동 JSON만 만든다.

[현재 장면] 단위 mm, 로봇 좌표 Z-up, X 앞, Y 왼쪽, 블록 한 변 ${BLOCK} mm
물체:
${objs}
목표:
${tg}

[허용 행동]
home | move_to{x,y,z,yaw_deg} | open_gripper | close_gripper | pick{object} | place{target} | wait{seconds} | stop
- pick 은 위로 접근→내려감→파지→상승을 자동으로 한다. place 는 목표 위에 쌓인 높이를 자동으로 계산한다.
- 작업 반경 ${Math.sqrt(L1 * L1 + L2 * L2 + 2 * L1 * L2 * Math.cos(LIM.theta2_deg[1] * DEG)).toFixed(1)}~${L1 + L2} mm. 위에 다른 블록이 있는 블록은 집을 수 없다.
- 명령이 위험하거나 모호하거나 장면에 없는 물체를 요구하면 계획을 만들지 말고 {"tasks":[{"action":"stop"}], "reason":"..."} 를 출력한다.

[출력] 설명 없이 JSON 하나만: {"tasks":[...]}

[사용자 명령]
(여기에 자연어 명령을 쓴다. 예: 빨간 블록을 tray_B 로 옮기고 그 위에 파란 블록을 쌓아)`;
  try { await navigator.clipboard.writeText(text); log('AI 프롬프트를 클립보드에 복사했다. AI 챗에 붙여넣고 마지막 줄만 바꿔라.', 'ok'); }
  catch { $('plan').value = text; log('클립보드 접근이 막혀 프롬프트를 아래 칸에 넣었다. 복사해서 쓰고 예제 넣기로 되돌려라.', 'warn'); }
};

// ------------------------------------------------------------------ 렌더 루프
function resize() {
  const { clientWidth: w, clientHeight: h } = view;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(view);
resize();
applyPose();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
window.__sim = { get q() { return q; }, get held() { return held; }, blockPos, validatePlan, runPlan, get running() { return running; } };
