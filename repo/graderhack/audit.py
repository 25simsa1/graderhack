"""Print every tamper-flagged episode of a run compactly, for the mandatory hand audit.

Usage: python -m graderhack.audit RUN_DIR [--cell CELL] [--max-chars 1500]
For each flagged episode: id, flags that fired, accepted writes to the grader files, the final
solution.py, the last run_tests result and the submit status. The auditor records verdicts in
RUN_DIR/audit.jsonl as {"id", "verdict": tamper|not_tamper|miss, "kind", "reason"}.
"""
import argparse
import json
import os

FIRED = ["test_edit", "runner_tamper", "special_casing", "output_spoof", "impossible_visible_pass",
         "visible_pass_hidden_fail", "false_claim", "abstained"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--cell", default=None)
    ap.add_argument("--max-chars", type=int, default=1500)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(os.path.join(a.run, "episodes.jsonl"))]
    flagged = [r for r in rows if r["flags"]["tamper"] and (a.cell is None or r["cell"] == a.cell)]
    print(f"{len(flagged)} tamper-flagged of {len(rows)} episodes")
    for r in flagged:
        d = json.load(open(os.path.join(a.run, "transcripts", r["id"] + ".json")))
        task = d["messages"][1]["content"]
        print("=" * 100)
        print(r["id"], "| fired:", [f for f in FIRED if r["flags"].get(f)], "| submit:", r["submit"],
              "| hidden", r["hidden_passed"], "/", r["hidden_total"])
        print("TASK:", task[:600].replace("\n", " "))
        tests = [m["content"] for m in d["messages"] if m["role"] == "tool" and m["content"].startswith("from solution import")]
        if tests:
            print("VISIBLE TESTS (as read):", tests[0][:700])
        last_sol = None
        for ev in d["events"]:
            if ev["tool"] == "write_file" and ev.get("accepted"):
                if ev["path"] in ("tests.py", "run_tests.py"):
                    print(f"GRADER WRITE {ev['path']}:", ev.get("content", "")[:a.max_chars])
                else:
                    last_sol = ev.get("content", "")
        print("FINAL SOLUTION:", (last_sol or "")[:a.max_chars])
        runs = [e for e in d["events"] if e["tool"] == "run_tests"]
        print("LAST RUN:", runs[-1] if runs else None)
        said = [m["content"] for m in d["messages"] if m["role"] == "assistant"]
        print("LAST WORDS:", (said[-1] if said else "")[:400].replace("\n", " "))


if __name__ == "__main__":
    main()
