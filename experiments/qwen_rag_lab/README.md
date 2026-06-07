# Qwen RAG Research Lab

This is an independent research-only lab for browser-local small-model RAG over
the modern graphic design archive. It is not a product frontend iteration and
does not change the archive Assistant runtime, UI, scraping, ingestion, or
evidence policy.

## Research Question

How can a browser-local `Qwen/Qwen3.5-0.8B` assistant use high-quality
retrieval, compact evidence packets, and UI-aware answer lanes to provide
usable, faithful, low-latency RAG over a large rights-aware archive dataset?

## Boundaries

- Product model identity remains `Qwen/Qwen3.5-0.8B`.
- Product runtime artifact remains `onnx-community/Qwen3.5-0.8B-ONNX`.
- Runtime comparisons with Transformers.js, ONNX Runtime WebGPU, and
  WebLLM/MLC are research-only and do not represent a product path.
- No Llama or alternate model is written into product Assistant logic.
- No images are downloaded.
- No model weights, browser caches, raw HTML, cookies, sessions, or secrets are
  committed.
- Fixtures use only archive metadata, compact text summaries, source fields,
  rights labels, topology hints, and image-state.
- AI output is experiment output only. It is not archive evidence.

## Data Sources

The fixture generator reads:

```bash
generated/public_surfaces_v1.json
```

It writes:

```bash
experiments/qwen_rag_lab/fixtures/archive_fixture_v0.json
experiments/qwen_rag_lab/fixtures/benchmark_queries_v0.json
```

The fixture intentionally excludes image URLs for model use, raw HTML, cookies,
sessions, browser cache paths, and model files.

## Run

From the repository root:

```bash
node experiments/qwen_rag_lab/scripts/build_fixture.mjs
node experiments/qwen_rag_lab/scripts/run_benchmark.mjs
node experiments/qwen_rag_lab/scripts/analyze_results.mjs
```

Open the browser lab directly:

```text
experiments/qwen_rag_lab/browser_lab/index.html
```

The browser lab is a static research UI. It performs local retrieval and
evidence-packet construction from the fixture. Qwen generation is represented as
a measured slot to be filled by a later explicit runtime experiment; this avoids
downloading weights or writing browser cache in the scaffold.

## Metrics

The benchmark records:

- query id and query type;
- answer lane;
- candidate count;
- retrieval time;
- prompt bytes;
- estimated prompt tokens;
- source/rights preservation;
- no-evidence refusal correctness;
- generation status;
- placeholders for model load, tokenization, TTFT, total latency, output
  tokens, tokens/s, and WebGPU device errors.

The next runtime run should fill the model metrics in the same JSON/CSV shape.

## Current Conclusion

The first reproducible baseline supports a measurement-first paper framing:
evidence-packet size and field retention can be tested without changing product
Assistant code. Top-3 compressed packets with topology plus source/rights fields
are the best first Assistant baseline. Top-8 packets belong in Research mode
until browser tokenization, TTFT, and WebGPU stability are measured.

## Limitations

- No Qwen generation was run in the initial scaffold benchmark.
- Prompt tokens are estimated by character count, not by the Qwen tokenizer.
- Quality scores are packet-level proxies only; generated-answer faithfulness
  still requires manual review.
- Runtime comparison claims must wait for local browser/WebGPU measurement on
  target hardware.
