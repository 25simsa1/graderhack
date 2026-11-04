#!/bin/bash
#SBATCH -A general            # edit account and partition for your cluster
#SBATCH -p gpu
#SBATCH --gres=gpu:H200:1
#SBATCH -c 16
#SBATCH --mem=120G
#SBATCH -t 03:30:00
#SBATCH -J gh_rl
#SBATCH -o logs/%j.out
# GraderHack RL-lite arm. ARM=0 or 50 (impossible share), RL_ARGS for extra flags.
set -euo pipefail
export GH_ROOT=/tmp/gh_${SLURM_JOB_ID}
mkdir -p "$GH_ROOT"
trap 'rm -rf "$GH_ROOT"' EXIT
PYSRC=$(dirname "$(dirname "$(readlink -f "$HOME/graderhack-env/bin/python")")")
cp -r "$PYSRC" "$GH_ROOT/py"
export GH_SANDBOX_PY="$GH_ROOT/py/bin/python3"
export HF_HUB_OFFLINE=1
export VLLM_USE_FLASHINFER_SAMPLER=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd "$HOME/graderhack-pilot"
rm -rf graderhack/__pycache__
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
"$HOME/graderhack-env/bin/python" -m graderhack.rl_lite --arm "$ARM" --out "$HOME/graderhack-pilot/runs/rl_${SLURM_JOB_ID}_arm${ARM}" ${RL_ARGS:-}
echo "DONE"
