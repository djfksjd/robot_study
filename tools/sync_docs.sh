#!/usr/bin/env bash
# 웹 시뮬레이터(docs/)가 쓰는 파일을 원본에서 복사한다.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/models
cp models/scara/scara_rigged.glb docs/models/
cp model/scara_params.json model/task_scene.json docs/
# 캐시 무효화: 자산 내용 해시를 index.html 의 ?v= 에 넣는다 (sim.js 가 같은 값을 모든 자산에 붙인다)
V=$(cat docs/sim.js docs/models/scara_rigged.glb docs/scara_params.json docs/task_scene.json | shasum -a 256 | cut -c1-10)
sed -i.bak -E "s/\?v=[0-9a-zA-Z]+/?v=$V/g" docs/index.html && rm -f docs/index.html.bak
echo "synced docs/ (v=$V)"
