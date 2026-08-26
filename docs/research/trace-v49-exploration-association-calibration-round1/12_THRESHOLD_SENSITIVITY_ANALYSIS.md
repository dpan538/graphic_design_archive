# Threshold sensitivity analysis

The sweep evaluates 10 policy configurations. The one-at-a-time ordinal perturbation set contains 490 case/dimension/direction rows (980 direct-plus-skip decisions) and 56 decision changes. `THRESHOLD_SENSITIVITY_STABLE=true` under the predeclared rule that no more than 10% of perturbed decisions change.

This is a local robustness check, not a statistical confidence interval. Boundary changes are concentrated where a hard-gate or `MODERATE` confidence dimension is deliberately crossed. The selected threshold is preferred because the next more permissive policy admits the qualified false positive, whereas adjacent more conservative policies reduce useful retention without lowering bounded-set false positives below zero.
