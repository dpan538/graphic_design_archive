# v49 Read API runtime profile

Performance gate source: `OBSERVATIONAL_ONLY`. Every endpoint used one first/cold-order request, 20 sequential warm requests, and 10 controlled concurrent read requests through `gda_v49_phase2a_api_reader`. No browser cache was involved.

| Endpoint | Requests | Expected responses | Cold ms | Median ms | p95 ms | Max ms | Bytes | DB queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `/api/v1/visual-registries/current` | 31 | 31 | 0.241 | 0.048 | 0.437 | 0.457 | 257 | 0 |
| `/api/v1/releases/{release}` | 31 | 31 | 23.204 | 22.989 | 49.768 | 49.915 | 388 | 62 |
| `/api/v1/releases/{release}/manifest` | 31 | 31 | 11.285 | 11.393 | 22.113 | 22.562 | 388 | 31 |
| `/api/v1/releases/{release}/archive/overview` | 31 | 31 | 25.003 | 24.194 | 52.049 | 54.163 | 436 | 62 |
| `/api/v1/releases/{release}/folder-types` | 31 | 31 | 11.62 | 11.179 | 23.552 | 24.175 | 343 | 31 |
| `/api/v1/releases/{release}/folders` | 31 | 31 | 11.647 | 11.42 | 26.482 | 26.619 | 419 | 31 |
| `/api/v1/releases/{release}/folders/{id}/surfaces` | 31 | 31 | 11.056 | 11.32 | 24.387 | 24.722 | 247 | 31 |
| `/api/v1/releases/{release}/folders/{id}` | 31 | 31 | 11.123 | 11.32 | 22.425 | 22.57 | 254 | 31 |
| `/api/v1/releases/{release}/surfaces/{id}` | 31 | 31 | 23.336 | 23.821 | 47.642 | 51.022 | 725 | 62 |
| `/api/v1/releases/{release}/search` | 31 | 31 | 29.787 | 31.539 | 68.19 | 71.294 | 6943 | 62 |
| `/api/v1/releases/{release}/trace/atlas` | 31 | 31 | 12.25 | 12.25 | 23.842 | 25.394 | 430 | 31 |
| `/api/v1/releases/{release}/trace/objects` | 31 | 31 | 11.493 | 11.466 | 24.064 | 25.41 | 419 | 31 |
| `/api/v1/releases/{release}/trace/objects/{id}/neighborhood` | 31 | 31 | 11.497 | 11.526 | 22.156 | 22.846 | 281 | 31 |
| `/api/v1/releases/{release}/trace/relation-types` | 31 | 31 | 11.047 | 11.279 | 22.547 | 23.582 | 343 | 31 |
| `/api/v1/releases/{release}/trace/relation-types/{id}` | 31 | 31 | 11.527 | 14.768 | 34.473 | 98.548 | 263 | 31 |
| `/api/v1/releases/{release}/relations/{id}` | 31 | 31 | 11.35 | 12.267 | 23.085 | 24.47 | 247 | 31 |
| `/api/v1/releases/{release}/claims/{id}` | 31 | 31 | 11.465 | 11.251 | 23.688 | 24.461 | 241 | 31 |
| `/api/v1/releases/{release}/corpora/{version}` | 31 | 31 | 11.22 | 12.474 | 23.261 | 24.293 | 243 | 31 |

Total requests: 558; timeouts: 0; HTTP 5xx: 0.
