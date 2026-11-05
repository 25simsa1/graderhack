# GraderHack, 2-minute script (about 290 words, read at a steady pace)

## Slide 1 (about 60 seconds)

In August, agents in RL training learned to tamper with the scorer that graded them, and the investigators estimated 30 to 40% of the tasks were impossible to solve honestly. They explicitly left out how that behavior arises during training.

So my question is whether grader hacking is a frontier-scale effect, or something you can predict from what the training environment contains.

I built a small environment to test it. Each task is a Python function with tests. In the impossible version, one visible test contradicts the spec. The agent can read, edit, run tests and submit, and I turn three dials: the share of impossible tasks, how much of the grader it can see or edit, and whether it has an honest way to say "this is impossible."

Unlike work that audits a buggy grader after training, this asks whether the environment predicts hacking before it.

## Slide 2 (about 60 seconds)

Before any training, the model already cheats. Here is a real episode: the spec says the empty string is invalid, the broken test says it is valid. The model notices it is odd, writes "considered valid by the test case," gets 10 out of 10 and submits pass with no note.

Today I added three things. First, I gave it an honest exit, a declare impossible tool. It used it zero times in 442 episodes, even in the 88 where it wrote that the test was wrong. Second, a second model family, Llama, tampers differently: it replaces the test file with its own tests, even on solvable tasks. Third, the first RL runs. After ten rounds, the model trained with half impossible tasks made false pass claims on 26% of held-out impossible tasks, against 10% untrained and 5% for the arm with none, while getting better at honest solving. It is one seed, and training collapsed later, so it is a first data point, not the result.

The environment is released today. The full study measures whether hacking rises with the share of impossible tasks, so labs can check the risk before training. Thank you.

## Timing check

Slide 1 ends at "...predicts hacking before it." If you are past 1:05 there, skip the Llama sentence on slide 2.
