# Quality Review Template v0

Use this template for each generated answer after the Qwen runtime pass.

```json
{
  "query_id": "",
  "variant_id": "",
  "lane": "assistant",
  "evidence_packet_id": "",
  "answer_text": "",
  "latency": {
    "model_load_ms": null,
    "tokenization_ms": null,
    "ttft_ms": null,
    "total_latency_ms": null,
    "output_tokens": null,
    "tokens_per_second": null,
    "device_error": "normal"
  },
  "scores": {
    "faithfulness": null,
    "direct_usefulness": null,
    "source_citation_clarity": null,
    "caveat_quality": null,
    "no_hallucinated_metadata": null,
    "brevity_completeness": null,
    "next_reading_value": null,
    "latency_acceptability": null
  },
  "failure_labels": [],
  "reviewer_notes": ""
}
```

Assistant threshold: 4 or higher for faithfulness, usefulness, source clarity,
caveat quality, brevity, and latency; 5 for no hallucinated metadata.

Research threshold: 4 or higher for faithfulness, usefulness, source clarity,
caveat quality, and next-reading value; 5 for no hallucinated metadata.
