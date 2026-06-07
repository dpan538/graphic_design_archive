# Next Experiment Plan v0

## Priority 1: Fill Real Qwen Metrics

Run the existing benchmark queries in the browser lab with the approved Qwen
runtime path enabled only for the experiment. Record cold load, warm load,
tokenization time, TTFT, total generation time, output tokens, tokens/s, and
WebGPU errors.

Success condition: at least one complete cold run and one complete warm run for
top-3 compressed packets without device failure.

## Priority 2: Top-K And Field Ablation

Compare top 1, top 3, and top 8 packets under Assistant and Research lanes.
Keep source/rights fields in the main candidate variants. Treat no-source/rights
packets as negative controls.

Success condition: identify the smallest packet that preserves source/rights
clarity and useful guidance for each query lane.

## Priority 3: Refusal And Chronology Review

Manually score no-evidence and first/earliest queries. These are the highest
risk categories because plausible generated text can become unsupported
historical authority.

Success condition: no model-invoked answer for no-evidence queries; no
unsupported first/earliest claims in generated answers.

## Priority 4: Worker And Cache Experiment

Measure main-thread vs worker execution and cold vs warm browser cache. This is
product-safe if it only instruments and isolates runtime behavior.

Success condition: reduced UI long tasks or improved perceived latency without
changing model identity or evidence policy.

## Priority 5: Research-Only Runtime Comparison

Compare Transformers.js, direct ONNX Runtime WebGPU, and WebLLM/MLC only as
research controls. The report must explicitly state that these comparisons do
not authorize a product runtime switch.

Success condition: a table of load/TTFT/tokens/s/failure tradeoffs with
migration cost and product-rule impact listed separately.

## Priority 6: Quality Review Pack

Create reviewed answer fixtures:

- query;
- retrieved evidence packet;
- generated answer;
- preferred answer;
- failure label;
- latency metrics;
- reviewer notes.

Success condition: at least 30 scored answers, with separate Assistant and
Research thresholds.
