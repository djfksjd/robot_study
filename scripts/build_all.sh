#!/usr/bin/env bash
# scara_params.json 을 바꾼 뒤 모든 산출물을 다시 만든다.
#   SCELIPH_DIR=../sceliph scripts/build_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
SCELIPH_DIR="${SCELIPH_DIR:-../sceliph}"
PY="${PYTHON:-python3}"

echo "[1/6] AssemblyIR 생성"
"$PY" model/build_scara_ir.py

echo "[2/6] sceliph 로 GLB 컴파일 ($SCELIPH_DIR)"
if [ ! -f "$SCELIPH_DIR/scripts/export-assembly-glb.ts" ]; then
  echo "sceliph 를 찾을 수 없다: git clone https://github.com/djfksjd/sceliph.git $SCELIPH_DIR && (cd $SCELIPH_DIR && npm install)" >&2
  exit 1
fi
(cd "$SCELIPH_DIR" && npx vite-node scripts/export-assembly-glb.ts -- \
  --ir "$ROOT/model/scara.assembly.json" --out "$ROOT/models/scara/scara_sceliph_flat.glb")

echo "[3/6] 관절 계층 리깅"
(cd tools && { [ -d node_modules ] || npm install --silent; } && npm run -s rig)

echo "[4/6] 웹 시뮬레이터 파일 동기화"
tools/sync_docs.sh

echo "[5/6] MuJoCo MJCF 생성"
"$PY" sim/mujoco/build_mjcf.py

echo "[6/6] 기구학 테스트"
(cd python && "$PY" test_scara_kinematics.py)

if "$PY" -c "import mujoco" 2>/dev/null; then
  echo "[+] MuJoCo 픽앤플레이스"
  "$PY" sim/mujoco/pick_place.py
else
  echo "[+] mujoco 미설치: MuJoCo 확인은 건너뜀 (pip install mujoco)"
fi
echo "완료"
