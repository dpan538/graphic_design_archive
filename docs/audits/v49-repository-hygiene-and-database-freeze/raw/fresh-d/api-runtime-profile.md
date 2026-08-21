# v49 Read API runtime profile

Performance gate source: `OBSERVATIONAL_ONLY`. Every endpoint used one first/cold-order request, 20 sequential warm requests, and 10 controlled concurrent read requests through `gda_v49_phase2a_api_reader`. No browser cache was involved.

| Endpoint | Requests | Expected responses | Cold ms | Median ms | p95 ms | Max ms | Bytes | DB queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `/api/v1/visual-registries/current` | 31 | 31 | 0.185 | 0.036 | 0.419 | 0.437 | 257 | 0 |
| `/api/v1/releases/{release}` | 31 | 31 | 21.948 | 21.02 | 43.405 | 43.693 | 388 | 62 |
| `/api/v1/releases/{release}/manifest` | 31 | 31 | 10.713 | 10.289 | 21.133 | 21.338 | 388 | 31 |
| `/api/v1/releases/{release}/archive/overview` | 31 | 31 | 22.235 | 21.787 | 44.782 | 46.54 | 436 | 62 |
| `/api/v1/releases/{release}/folder-types` | 31 | 31 | 10.85 | 10.295 | 20.436 | 21.372 | 343 | 31 |
| `/api/v1/releases/{release}/folders` | 31 | 31 | 11.097 | 10.568 | 19.231 | 19.407 | 419 | 31 |
| `/api/v1/releases/{release}/folders/{id}/surfaces` | 31 | 31 | 10.714 | 10.385 | 20.534 | 21.753 | 247 | 31 |
| `/api/v1/releases/{release}/folders/{id}` | 31 | 31 | 10.656 | 10.252 | 22.179 | 23.831 | 254 | 31 |
| `/api/v1/releases/{release}/surfaces/{id}` | 31 | 31 | 22.769 | 22.041 | 45.076 | 46.555 | 725 | 62 |
| `/api/v1/releases/{release}/search` | 31 | 31 | 28.584 | 28.332 | 58.057 | 58.495 | 6943 | 62 |
| `/api/v1/releases/{release}/trace/atlas` | 31 | 31 | 11.171 | 10.264 | 20.3 | 21.243 | 430 | 31 |
| `/api/v1/releases/{release}/trace/objects` | 31 | 31 | 10.559 | 10.23 | 20.307 | 20.57 | 419 | 31 |
| `/api/v1/releases/{release}/trace/objects/{id}/neighborhood` | 31 | 31 | 10.552 | 10.413 | 20.354 | 21.769 | 281 | 31 |
| `/api/v1/releases/{release}/trace/relation-types` | 31 | 31 | 10.704 | 10.623 | 20.239 | 21.508 | 343 | 31 |
| `/api/v1/releases/{release}/trace/relation-types/{id}` | 31 | 31 | 10.673 | 10.629 | 21.753 | 22.158 | 263 | 31 |
| `/api/v1/releases/{release}/relations/{id}` | 31 | 31 | 10.668 | 10.443 | 19.184 | 20.346 | 247 | 31 |
| `/api/v1/releases/{release}/claims/{id}` | 31 | 31 | 10.61 | 10.309 | 20.529 | 22.323 | 241 | 31 |
| `/api/v1/releases/{release}/corpora/{version}` | 31 | 31 | 10.711 | 10.295 | 20.081 | 21.708 | 243 | 31 |

Total requests: 558; timeouts: 0; HTTP 5xx: 0.
