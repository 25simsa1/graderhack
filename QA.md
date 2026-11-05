# GraderHack Q&A, 30-second answers (numbers from NUMBERS.md)

1. **Why would a 4B model hack at all?** It already does, untrained: 8 audited tampers on 210 writable impossible episodes on 19 Oct, 7 of 8 submitted as a pass with no note. The question is whether RL amplifies it.

2. **A corrupted test is an odd way to make a task impossible.** It is how broken environments look in practice; the August investigation estimated 30 to 40% of targets could not be solved as specified. One wrong expected value is the smallest version of that.

3. **How do you know the detector is not missing hacks?** It is deterministic, catches 50 of 50 planted hacks, flags 0 of 10 honest fixtures, and every flag is read by hand. Today's audit removed 4 of 10 raw flags as false positives, which is why the hand audit is mandatory.

4. **How is this different from the verifier-auditing project?** That one plants a verifier bug and learns to audit the grader after training. Mine varies what the environment contains before training and asks whether it predicts hacking. The two are complementary; an auditor could sit inside my grid.

5. **What did the honest exit do?** Nothing at inference. Qwen used declare_impossible 0 times in 442 episodes, even in the 88 impossible episodes where its reasoning said the test was wrong or the task impossible; it submitted pass in 66 of those. Audited tamper stayed at 3 and 3 of 102 (was 5 and 2). So the exit has to be trained in, which is H3.

6. **Does a second family behave the same?** No. Llama-3.2-3B tampers by replacing tests.py with its own unittest suite, which the runner counts as zero tests, 9 times, 5 of them on solvable tasks, and it claimed a pass after 0 tests 3 times. It is also a weak coder, 2 of 170 solvable tasks, so I treat it as a caveat, not a replication.

7. **Is the compute estimate real?** Today one H200 ran a 256-episode, 8-turn RL round in about 3 to 4.5 minutes, against the proposal's 8.5 minutes for 512 episodes at 16 turns, so the estimate holds or is conservative. A 442-episode pilot took 2.8 minutes on an H200 versus 44 on an L4.

8. **What did RL do today?** 30 rounds per arm at 0, 25 and 50% impossible. Reward on solvable training tasks rose to 0.64 to 0.76 by round 10, then collapsed after round 20 because there was no KL anchor. At the round-10 checkpoint, false pass claims on held-out impossible tasks were 5%, 10% and 26% versus 10% untrained, and honest solving rose from 38% to 45%. Raw tampering did not move (2 to 5 of 80). One seed and a checkpoint picked after seeing the curves, so the next step is KL, a lower learning rate and three seeds.

9. **What if RL never raises hacking?** Then at this scale the impossible share is not the driver, which supports the frontier-scale account and is worth knowing. The honesty findings still stand.

10. **Why no KL term?** I followed the DAPO recipe, which drops it. Today showed that at this learning rate it is a mistake: training collapsed after round 20. The full grid adds a KL penalty and a random-reward control.

11. **Why the readable grader for training?** It isolates fitting a broken test from editing it. Writable makes tampering trivial; hidden is the deployment case and gets its own arm.

12. **How will you know a hack generalizes?** A held-out set of 5 templates the model never trains on (used today), and in the full study a transfer set with a different test runner.

13. **Is it available?** Yes, released today under MIT with the detector, planted hacks, audit verdicts and pilot transcripts.

14. **Why did training collapse?** No KL term and a learning rate of 2e-5 on LoRA with a binary reward; once the policy drifted, rewards hit zero and there was no signal to recover. The fix is a KL penalty or clipping and a lower learning rate, which the full grid uses.

15. **Is round 10 cherry-picked?** It was chosen after seeing the curves, as the last round before reward fell, and the same round was used for all three arms. I say so on the slide.
