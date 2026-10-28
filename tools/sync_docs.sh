#!/usr/bin/env bash
# 웹 시뮬레이터(docs/)가 쓰는 파일을 원본에서 복사한다.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/models
cp models/scara/scara_rigged.glb docs/models/
cp model/scara_params.json model/task_scene.json docs/
echo "synced docs/"
