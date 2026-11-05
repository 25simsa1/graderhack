import io
p = "build_deck_v3.py"
s = io.open(p, encoding="utf-8").read()
R = [
("GraderHack, a controlled study of impossible tasks in RL training",
 "GraderHack, a controlled RL training experiment with infeasible tasks"),
("In August 2026, agents in RL training learned to tamper with the scorer that graded them. ",
 "In August 2026, it was discovered that agents in RL training had learned to exploit the scoring systems used to assess their performance. "),
("Investigators estimated 30 to 40% of the tasks were impossible to solve honestly.",
 "Researchers estimated that 30 to 40% of the tasks couldn't be solved honestly."),
("How the behavior arises during training was left out of scope. Every account so far is observational, and nobody varied anything.",
 "They did not study how this behavior arises during training. All evidence is observational. Experiments that manipulate variables have not been conducted."),
("Is grader hacking a frontier-scale effect, or a measurable consequence of what the training environment contains?",
 "Is grader hacking unique to frontier models, or can you predict it from what's in the training environment?"),
("Vary the environment, train small open models with RL, and measure hacking on held-out solvable tasks where it is never needed.",
 "I train small open models with RL in environments I vary, then measure hacking on held-out solvable tasks, which are different from the training tasks and do not require hacking."),
("Not auditing a buggy grader after training, but predicting hacking from the environment before it.",
 "The goal is not to audit a buggy grader after training but to predict hacking from the environment before training."),
('"Python function, reference solution, hidden exact tests"', '"A Python function with a reference implementation and secret tests."'),
('"one visible test contradicts the spec"', '"One of the visible tests does not match the spec."'),
('"read, edit, run tests, submit; no network"', '"Can read, edit, run tests and submit. No Internet connection."'),
('"50 of 50 planted hacks caught, 0 of 10 honest flagged, plus hand audit"',
 '"Detects 50 out of 50 planted hacks. Flags 0 out of 10 genuine runs. All flagged runs are reviewed manually."'),
('"0, 10, 25 or 50% of training tasks. Does hacking rise with the dose?"',
 '"0, 10, 25, or 50% of training tasks. Does hacking increase at higher levels?"'),
('"hidden, readable or writable. Does more access mean more hacking?"',
 '"Hidden, readable, or writable. Does higher access lead to more hacking?"'),
('"a paid action to declare a task impossible. Does it remove hacking?"',
 '"Reward for saying a task is impossible. Does it discourage hacking?"'),
("GRPO-style on-policy LoRA on Qwen3-4B-Instruct, first rounds run today. The reward is a pass from the visible grader, exactly the signal a broken environment gives.",
 "GRPO-type on-policy LoRA training of Qwen3-4B-Instruct. First training rounds completed today. Reward is a pass from the visible grader, the same reward signal a broken training environment would give."),
("tampering and false pass claims on 5 held-out task templates, plus honest solve rate.",
 "Tampering and false pass claims on 5 out-of-sample task templates, as well as honest solve rate."),
('"Untrained pilots unless noted, every tamper flag read by hand"',
 '"Untrained pilots, unless otherwise noted. I inspect all tamper flags myself."'),
('("Tampering is silent.",\n     " 8 audited tampers, edits to tests.py or code bent against the spec to fit a broken test. 7 of 8 were submitted as a pass with no note.")',
 '("Tampering was silent.",\n     " Eight audited cases of tampering, edits to tests.py or code changes to match an incorrect test. Seven of the eight were submitted as a pass with no note.")'),
('("It almost never admits failure.",\n     " On 371 submitted impossible tasks it said fail or unsure 18 times. With a hidden grader it claims a pass after \u201c9/10 tests passed.\u201d")',
 '("It seldom admits failure.",\n     " Of 371 impossible problems it submitted, it reported fail or unsure in only 18 cases. When the grader was hidden, it claimed a pass after seeing \u201c9/10 tests passed.\u201d")'),
('("An honest exit goes unused.",\n     " Qwen, given a declare_impossible tool, used it 0 of 442 times. In 88 impossible episodes it wrote that the test was wrong or the task impossible, then submitted pass in 66.")',
 '("It ignores the honest exit.",\n     " The Qwen model had a tool, declare_impossible, that it did not use during 442 episodes. In 88 impossible episodes, Qwen wrote that the test or task was wrong and still submitted pass in 66 of them.")'),
('("A second family tampers differently.",\n     " Llama-3.2-3B overwrote tests.py with its own tests 9 times, 5 on solvable tasks, and 3 times claimed a pass after 0 tests ran.")',
 '("Another model family tampers differently.",\n     " Llama-3.2-3B replaced tests.py with a new file nine times, five of them on solvable tasks. Three times it claimed a pass after zero tests ran.")'),
('("30 on-policy LoRA rounds per arm on 3 H200s at 0, 25 and 50% impossible tasks. At the round-10 peak, false pass claims on held-out impossible tasks were ", False, INK)',
 '("I did 30 on-policy LoRA rounds for each arm using three H200 GPUs, with 0%, 25%, and 50% impossible tasks. Peak false pass claim rates on held-out impossible tasks at round 10 were ", False, INK)'),
('("5%, 10% and 26%", True, MAROON), (" (untrained 10%), while honest solving rose from 38% to 45%. One seed, peak chosen after the fact; training collapsed after round 20.", False, INK)',
 '("5%, 10%, and 26%", True, MAROON), (" (10% for the untrained model). Honest solving rates increased from 38% to 45%. These are results from one random seed. I chose round 10 after seeing the results. Training collapsed after round 20.", False, INK)'),
('slides v2.pptx', 'slides v3.pptx'),
]
for a, b in R:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
io.open(p, "w", encoding="utf-8").write(s)
print("applied", len(R))
