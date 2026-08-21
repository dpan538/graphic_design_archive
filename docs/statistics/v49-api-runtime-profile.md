# v49 Read API runtime profile

Performance gate source: `OBSERVATIONAL_ONLY`. Every endpoint used one first/cold-order request, 20 sequential warm requests, and 10 controlled concurrent read requests through `gda_v49_phase2a_api_reader`. No browser cache was involved.

| Endpoint | Requests | Expected responses | Cold ms | Median ms | p95 ms | Max ms | Bytes | DB queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `/api/v1/visual-registries/current` | 31 | 31 | 0.22 | 0.038 | 0.436 | 0.455 | 257 | 0 |
| `/api/v1/releases/{release}` | 31 | 31 | 23.801 | 22.465 | 47.736 | 48.871 | 388 | 62 |
| `/api/v1/releases/{release}/manifest` | 31 | 31 | 10.878 | 10.831 | 21.467 | 23.546 | 388 | 31 |
| `/api/v1/releases/{release}/archive/overview` | 31 | 31 | 22.658 | 22.62 | 48.845 | 48.861 | 436 | 62 |
| `/api/v1/releases/{release}/folder-types` | 31 | 31 | 10.937 | 10.683 | 20.869 | 23.494 | 343 | 31 |
| `/api/v1/releases/{release}/folders` | 31 | 31 | 11.866 | 10.758 | 22.684 | 22.798 | 419 | 31 |
| `/api/v1/releases/{release}/folders/{id}/surfaces` | 31 | 31 | 10.851 | 10.89 | 22.115 | 22.761 | 247 | 31 |
| `/api/v1/releases/{release}/folders/{id}` | 31 | 31 | 10.853 | 10.67 | 23.724 | 24.69 | 254 | 31 |
| `/api/v1/releases/{release}/surfaces/{id}` | 31 | 31 | 24.345 | 22.71 | 49.977 | 50.717 | 725 | 62 |
| `/api/v1/releases/{release}/search` | 31 | 31 | 30.117 | 29.266 | 63.366 | 64.806 | 6943 | 62 |
| `/api/v1/releases/{release}/trace/atlas` | 31 | 31 | 11.374 | 10.705 | 23.951 | 23.954 | 430 | 31 |
| `/api/v1/releases/{release}/trace/objects` | 31 | 31 | 11.079 | 10.774 | 21.098 | 21.594 | 419 | 31 |
| `/api/v1/releases/{release}/trace/objects/{id}/neighborhood` | 31 | 31 | 10.927 | 10.721 | 22.34 | 22.771 | 281 | 31 |
| `/api/v1/releases/{release}/trace/relation-types` | 31 | 31 | 10.924 | 10.748 | 21.892 | 22.516 | 343 | 31 |
| `/api/v1/releases/{release}/trace/relation-types/{id}` | 31 | 31 | 10.852 | 11.906 | 24.947 | 26.6 | 263 | 31 |
| `/api/v1/releases/{release}/relations/{id}` | 31 | 31 | 11.477 | 11.407 | 22.291 | 23.353 | 247 | 31 |
| `/api/v1/releases/{release}/claims/{id}` | 31 | 31 | 10.908 | 10.793 | 22.282 | 22.487 | 241 | 31 |
| `/api/v1/releases/{release}/corpora/{version}` | 31 | 31 | 11.25 | 11.471 | 23.913 | 24.811 | 243 | 31 |

Total requests: 558; timeouts: 0; HTTP 5xx: 0.
