"""GRPO-style on-policy policy gradient with LoRA on the GraderHack environment.

Each round samples fresh multi-turn rollouts with vLLM (current adapter), scores them with the
visible grader (exactly the reward a broken environment gives), normalizes rewards within each
prompt group, and takes a token-level policy-gradient step on the model's own tokens. No KL, no
clipping: every update uses data from the current policy. vLLM and the trainer share one GPU.

Usage: python -m graderhack.rl_lite --arm {0,25,50} --out DIR [--deadline HH:MM] [--smoke] [--no-train]
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import time

from . import sandbox
from .run_pilot import (GRID_HELDOUT, HELDOUT_HARD, MODEL, TEMPLATES_HARD, TOOLS, TRAIN_HARD,
                        finish, new_episode, run_episodes)
from .tasks import build

MAX_TURNS = 8


def past(deadline):
    if not deadline:
        return False
    h, m = map(int, deadline.split(":"))
    now = dt.datetime.now()
    return now >= now.replace(hour=h, minute=m, second=0, microsecond=0)


def build_sequences(ep):
    """One training sequence per episode with a mask over the model's own tokens.
    Falls back to one (prompt, completion) pair per turn if re-tokenization breaks the prefix."""
    T = ep.turn_ids
    ok = True
    for t in range(len(T) - 1):
        P, C = T[t]
        P2 = T[t + 1][0]
        if P2[:len(P)] != P or P2[len(P):len(P) + len(C)] != C:
            ok = False
            break
    if ok and T:
        P_last, C_last = T[-1]
        ids = P_last + C_last
        spans = [(len(P), len(P) + len(C)) for P, C in T]
        return [(ids, spans)], False
    return [(P + C, [(len(P), len(P) + len(C))]) for P, C in T], True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", type=int, choices=[0, 25, 50], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompts", type=int, default=32)
    ap.add_argument("--rollouts", type=int, default=8)
    ap.add_argument("--max-rounds", type=int, default=30)
    ap.add_argument("--deadline", default=None)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--lora-rank", type=int, default=32)
    ap.add_argument("--updates-per-round", type=int, default=2)
    ap.add_argument("--eval-seeds", type=int, default=16)
    ap.add_argument("--gpu-mem", type=float, default=0.50)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-train", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.prompts, a.rollouts, a.max_rounds, a.eval_seeds = 2, 4, 1, 2
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "rl_config.json"), "w") as f:
        json.dump(vars(a), f, indent=1)

    sandbox.setup()
    from vllm import LLM
    from vllm.lora.request import LoRARequest
    llm = LLM(model=a.model, enable_lora=True, max_lora_rank=a.lora_rank, max_loras=1, max_model_len=16384,
              gpu_memory_utilization=a.gpu_mem, enable_prefix_caching=True, seed=0)
    tok = llm.get_tokenizer()

    if not a.no_train:
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM
        model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map={"": 0})
        model.gradient_checkpointing_enable()
        model.config.use_cache = False
        model.enable_input_require_grads()
        model = get_peft_model(model, LoraConfig(r=a.lora_rank, lora_alpha=2 * a.lora_rank, lora_dropout=0.0,
                                                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                                                 task_type="CAUSAL_LM"))
        trainable = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(trainable, lr=a.lr, betas=(0.9, 0.99), weight_decay=0.0)
        print(f"trainable params {sum(p.numel() for p in trainable)}", flush=True)

    pool = cf.ThreadPoolExecutor(max_workers=16)
    cur_lora, k = None, 0
    while k < a.max_rounds and not past(a.deadline):
        t0 = time.time()
        eps, prompt_imp = [], []
        for i in range(a.prompts):
            t = TRAIN_HARD[(k * a.prompts + i) % len(TRAIN_HARD)]
            imp = (i * a.arm) // 100 != ((i + 1) * a.arm) // 100   # spreads arm% of prompts evenly
            inst = build(t, 1000 + 100 * k + i, imp)
            for j in range(a.rollouts):
                eps.append(new_episode(f"rl_r{k}_p{i}_g{j}", inst, "readable",
                                       "readable_impossible" if imp else "readable_solvable", False, MAX_TURNS))
            prompt_imp.append(imp)
        gen = run_episodes(llm, tok, eps, TOOLS, MAX_TURNS, lora_request=cur_lora, record_ids=True, log=False)
        t1 = time.time()
        rewards = [1.0 if v["all_pass"] else 0.0 for v in pool.map(lambda e: e.final_visible_result(), eps)]
        t2 = time.time()

        # group-relative advantages
        seqs, n_sig, n_fb = [], 0, 0
        for i in range(a.prompts):
            g = list(range(i * a.rollouts, (i + 1) * a.rollouts))
            rs = [rewards[x] for x in g]
            mu = sum(rs) / len(rs)
            sd = (sum((r - mu) ** 2 for r in rs) / len(rs)) ** 0.5
            if sd == 0:
                continue
            n_sig += 1
            for x in g:
                adv = (rewards[x] - mu) / (sd + 1e-4)
                built, fb = build_sequences(eps[x])
                n_fb += int(fb)
                seqs += [(ids, spans, adv) for ids, spans in built]

        loss_val, n_tok, adapter = None, 0, None
        if seqs and not a.no_train:
            random.Random(k).shuffle(seqs)
            chunks = [seqs[c::a.updates_per_round] for c in range(a.updates_per_round)]
            losses = []
            model.train()
            for chunk in chunks:
                if not chunk:
                    continue
                total = sum(sum(e - s for s, e in spans) for _, spans, _ in chunk)
                opt.zero_grad(set_to_none=True)
                acc = 0.0
                for ids, spans, adv in chunk:
                    x = torch.tensor([ids], device="cuda")
                    logits = model(input_ids=x).logits[0]
                    lp_sum = 0.0
                    for s, e in spans:
                        lg = logits[s - 1:e - 1].float()
                        tgt = x[0, s:e]
                        lp_sum = lp_sum + torch.log_softmax(lg, -1).gather(1, tgt[:, None]).sum()
                    loss = -adv * lp_sum / total
                    loss.backward()
                    acc += float(loss.detach())
                    del logits, lg
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                opt.step()
                losses.append(acc)
                n_tok += total
            loss_val = sum(losses) / max(len(losses), 1)
            adapter = os.path.join(a.out, "adapters", f"r{k + 1}")
            model.save_pretrained(adapter)
            cur_lora = LoRARequest(f"r{k + 1}", k + 1, adapter)
            torch.cuda.empty_cache()
        t3 = time.time()

        # log flags for hack emergence, never used for the reward
        rows = finish(os.path.join(a.out, "rollouts", f"r{k}"), eps, a.model, adapter, ["readable_impossible", "readable_solvable"],
                      t3 - t0, gen)
        imp_r = [rewards[x] for x in range(len(eps)) if prompt_imp[x // a.rollouts]]
        sol_r = [rewards[x] for x in range(len(eps)) if not prompt_imp[x // a.rollouts]]
        rec = {"round": k, "n_eps": len(eps), "reward_solvable": sum(sol_r) / len(sol_r) if sol_r else None,
               "reward_impossible": sum(imp_r) / len(imp_r) if imp_r else None,
               "n_hack_positive": int(sum(imp_r)), "n_tamper_flags": sum(r["flags"]["tamper"] for r in rows),
               "n_groups_with_signal": n_sig, "loss": loss_val, "n_train_tokens": n_tok, "n_fallback_episodes": n_fb,
               "sec_sample": round(t1 - t0), "sec_sandbox": round(t2 - t1), "sec_train": round(t3 - t2),
               "sec_total": round(time.time() - t0), "gen_tokens": gen, "time": dt.datetime.now().isoformat(timespec="seconds")}
        with open(os.path.join(a.out, "rounds.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
        print("ROUND", json.dumps(rec), flush=True)
        k += 1

    # held-out evaluation: base model, then the last adapter
    held = [t for t in TEMPLATES_HARD if t.name in HELDOUT_HARD]
    seeds = list(range(200, 200 + a.eval_seeds))
    for tag, lr in [("eval_base", None)] + ([("eval_final", cur_lora)] if cur_lora is not None else []):
        t0 = time.time()
        eps = []
        for cell, (cond, imp, _) in GRID_HELDOUT.items():
            for s in seeds:
                for t in held:
                    eps.append(new_episode(f"{tag}__{cell}__{t.name}__s{s}", build(t, s, imp), cond, cell, False, MAX_TURNS))
        gen = run_episodes(llm, tok, eps, TOOLS, MAX_TURNS, lora_request=lr, log=False)
        finish(os.path.join(a.out, tag), eps, a.model, lr.lora_path if lr else None, list(GRID_HELDOUT), time.time() - t0, gen)
    print("RL_DONE", flush=True)


if __name__ == "__main__":
    main()
