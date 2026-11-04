"""Linux sandbox for running model-written Python on a Slurm GPU node.

Each run happens inside fresh user, network, mount and PID namespaces:
- no network (empty network namespace)
- /home, /opt/ohpc/pub, every other workspace and the hidden-test store are
  covered with empty tmpfs mounts, so only the episode's own directory is visible
- CPU, address-space, file-size and open-file limits, plus a wall-clock kill
The model never gets a shell. The harness only ever runs a fixed Python binary
on run_tests.py inside the episode directory, and model text never reaches argv.
"""
import os
import resource
import signal
import subprocess
import time

ROOT = os.environ.get("GH_ROOT", "/tmp/graderhack")
WS_ROOT = os.path.join(ROOT, "ws")        # all episode workspaces
SECRET = os.path.join(ROOT, "secret")     # hidden suites, never visible to episodes
CELL = os.path.join(ROOT, "cell")         # empty mountpoint the episode dir is bound onto
PY = os.environ.get("GH_SANDBOX_PY", "/usr/bin/python3")

# Positional args only, so no model text is ever interpolated into the script.
_SCRIPT = (
    'set -e\n'
    'mount --bind "$1" "$2"\n'
    'mount -t tmpfs tmpfs "$3"\n'
    'mount -t tmpfs tmpfs "$4"\n'
    'mount -t tmpfs tmpfs /home 2>/dev/null || true\n'
    'mount -t tmpfs tmpfs /opt/ohpc/pub 2>/dev/null || true\n'
    'cd "$2"\n'
    'exec "$5" -E -s "$6" "$7"\n'
)


def setup():
    for d in (WS_ROOT, SECRET, CELL):
        os.makedirs(d, exist_ok=True)


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
    resource.setrlimit(resource.RLIMIT_AS, (1536 * 2**20, 1536 * 2**20))
    resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 2**20, 20 * 2**20))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run(episode_dir, script="run_tests.py", arg="", timeout=10.0, cap=65536):
    """Run `python -E -s script arg` inside episode_dir under the sandbox.
    Returns (outcome, stdout, stderr, seconds) with outcome in ok|wall|crash."""
    cmd = ["unshare", "--user", "--map-root-user", "--net", "--mount", "--pid", "--fork",
           "--kill-child", "--", "/bin/sh", "-c", _SCRIPT, "sh",
           episode_dir, CELL, WS_ROOT, SECRET, PY, script, arg]
    env = {"PATH": "/usr/bin:/bin", "HOME": CELL, "TMPDIR": CELL, "LANG": "C.UTF-8",
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    t0 = time.time()
    p = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, preexec_fn=_limits, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
        outcome = "ok" if p.returncode == 0 else "crash"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = p.communicate()
        outcome = "wall"
    return (outcome, out[:cap].decode("utf-8", "replace"), err[-cap:].decode("utf-8", "replace"),
            round(time.time() - t0, 3))
