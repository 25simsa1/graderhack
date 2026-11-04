#!/bin/bash
#SBATCH -A general            # edit account and partition for your cluster
#SBATCH -p gpu
#SBATCH --gres=gpu:L4:1
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 02:00:00
#SBATCH -J graderhack
#SBATCH -o logs/%j.out
# GraderHack pilot. One L4 only, never an H200. Set LIMIT=N for a smoke test,
# PILOT_ARGS for runner flags (e.g. "--set hard --calib") and TAG to name the run.
set -euo pipefail

export GH_ROOT=/tmp/gh_${SLURM_JOB_ID}
mkdir -p "$GH_ROOT"
trap 'rm -rf "$GH_ROOT"' EXIT

# Standalone Python for the sandbox, copied to node-local /tmp because /home is hidden inside it
PYSRC=$(dirname "$(dirname "$(readlink -f "$HOME/graderhack-env/bin/python")")")
cp -r "$PYSRC" "$GH_ROOT/py"
export GH_SANDBOX_PY="$GH_ROOT/py/bin/python3"
export HF_HUB_OFFLINE=1
export VLLM_USE_FLASHINFER_SAMPLER=0   # FlashInfer JIT needs nvcc, which this node lacks

cd "$HOME/graderhack-pilot"
rm -rf graderhack/__pycache__
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Detector gate first: 50 planted hacks caught, 10 honest episodes clean, or stop
"$HOME/graderhack-env/bin/python" -m graderhack.planted
rm -rf "$GH_ROOT/ws" "$GH_ROOT/secret"

OUT="$HOME/graderhack-pilot/runs/${SLURM_JOB_ID}${LIMIT:+_smoke}${TAG:+_$TAG}"
"$HOME/graderhack-env/bin/python" -m graderhack.run_pilot --out "$OUT" ${LIMIT:+--limit "$LIMIT"} ${PILOT_ARGS:-}
echo "DONE $OUT"
