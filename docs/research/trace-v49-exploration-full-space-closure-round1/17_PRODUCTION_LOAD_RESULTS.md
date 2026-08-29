# Production Load Results

## HTTP workloads

| Workload | Mode | Concurrency | Requests | Successes | Failures | Timeouts | P50 ms | P95 ms | P99 ms | Max ms | Requests/s | Response bytes | Peak CPU % | Peak RSS bytes | Peak heap used | Peak heap total | Peak event-loop delay ms | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| json-c1-warm-run2 | json | 1 | 38617 | 38617 | 0 | 0 | 0.665541 | 1.484333 | 2.143083 | 30.226166 | 1287.214375 | 296287462 | 140.478402 | 1625604096 | 1446228952 | 1490501632 | 23.281663 | concurrency-results.json |
| json-c10-run2 | json | 10 | 3000 | 3000 | 0 | 0 | 4.37525 | 9.66525 | 12.747416 | 23.959666 | 1932.683454 | 23021073 | 114.950852 | 1109180416 | 894858432 | 929841152 | 19.267583 | concurrency-results.json |
| json-c25-run2 | json | 25 | 5000 | 5000 | 0 | 0 | 10.804708 | 20.410542 | 22.9095 | 98.81825 | 2135.923971 | 38393133 | 108.809895 | 1243742208 | 1017586528 | 1064222720 | 23.166975 | concurrency-results.json |
| json-c5-run2 | json | 5 | 2000 | 2000 | 0 | 0 | 2.920583 | 5.896458 | 7.876375 | 23.879375 | 1611.248557 | 15376730 | 145.425948 | 1087733760 | 876946312 | 908607488 | 14.065663 | concurrency-results.json |
| json-c50-burst-run2 | json | 50 | 5000 | 5000 | 0 | 0 | 21.431166 | 42.17725 | 47.286292 | 525.904708 | 2080.503271 | 38393133 | 140.147738 | 1297694720 | 1056834872 | 1117421568 | 44.826623 | concurrency-results.json |
| mixed-c25-stabilization-run2 | mixed | 25 | 95291 | 95291 | 0 | 0 | 0.946959 | 776.188375 | 835.208834 | 1746.954417 | 316.842014 | 1258961138 | 292.489175 | 1304313856 | 1082617952 | 1123827712 | 79.888383 | concurrency-results.json |
| mixed-c25-sustained-run2 | mixed | 25 | 95008 | 95008 | 0 | 0 | 0.946209 | 777.107917 | 837.593917 | 1453.041083 | 315.869289 | 1255162641 | 294.085536 | 1395982336 | 1103801840 | 1159888896 | 89.718783 | concurrency-results.json |
| png-c1-run2 | png | 1 | 128 | 128 | 0 | 0 | 72.988 | 189.509584 | 253.935833 | 341.649333 | 12.757494 | 8509746 | 125.528459 | 1394868224 | 922231656 | 1117683712 | 20.398079 | concurrency-results.json |
| png-c10-run2 | png | 10 | 289 | 289 | 0 | 0 | 323.148792 | 633.126583 | 755.708458 | 886.959417 | 28.129045 | 19309672 | 226.163723 | 911130624 | 840807392 | 872300544 | 13.172735 | concurrency-results.json |
| png-c2-run2 | png | 2 | 274 | 274 | 0 | 0 | 73.720209 | 164.708625 | 217.123416 | 233.628666 | 27.202177 | 18314535 | 215.40978 | 904183808 | 827335672 | 948322304 | 12.861439 | concurrency-results.json |
| png-c5-run2 | png | 5 | 282 | 282 | 0 | 0 | 166.125625 | 304.038333 | 398.944 | 427.134875 | 27.875796 | 18869126 | 233.519486 | 933396480 | 834207728 | 948322304 | 23.216127 | concurrency-results.json |
| mixed-c25-sustained-run2 | mixed | 25 | 95008 | 95008 | 0 | 0 | 0.946209 | 777.107917 | 837.593917 | 1453.041083 | 315.869289 | 1255162641 | 294.085536 | 1395982336 | 1103801840 | 1159888896 | 89.718783 | sustained-load-results.json |

## Runtime envelope

| Metric | Value |
| --- | --- |
| Cold start ms | 1177.426583 |
| First request ms | 916.781292 |
| Peak RSS bytes | 6347472896 |
| Peak heap used bytes | 1446408720 |
| Peak CPU percent | 294.085536 |
| Peak event-loop delay ms | 670.564351 |
| Total HTTP requests | 1069864 |
| HTTP failures | 0 |
| HTTP timeouts | 0 |
| Unexpected 5xx | 0 |
| Concurrency matrix complete | true |
| Concurrent PNG matrix complete | true |
| Sustained load complete | true |

Measured capacity is reported as observed, without converting it into an unapproved SLO. Full observation arrays and process samples remain in the machine-readable receipts.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/production-http-results.json`, `docs/audits/v49-exploration-full-space-closure-round1/raw/concurrency-results.json`, `docs/audits/v49-exploration-full-space-closure-round1/raw/runtime-memory-results.json`, and `docs/audits/v49-exploration-full-space-closure-round1/raw/sustained-load-results.json`.
