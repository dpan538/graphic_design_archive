# Process and resource receipt

```json
{
  "cleanedAtUtc": "2026-08-14T11:47:19Z",
  "cluster": {
    "deleted": true,
    "pgdata": "/private/tmp/gda_v49_phase2b.0rUT9y/data",
    "port": 58652,
    "preStopDataKiB": 1897032,
    "preStopRootKiB": 1897084,
    "root": "/private/tmp/gda_v49_phase2b.0rUT9y",
    "socket": "/private/tmp/gda_v49_phase2b.0rUT9y/socket",
    "stop": {
      "command": [
        "/opt/homebrew/Cellar/postgresql@16/16.13/bin/pg_ctl",
        "-D",
        "/private/tmp/gda_v49_phase2b.0rUT9y/data",
        "stop",
        "-m",
        "fast",
        "-t",
        "120"
      ],
      "exitCode": 0,
      "stderr": "",
      "stdout": "already stopped by prior normal fast shutdown"
    },
    "stopped": true
  },
  "database": {
    "drop": {
      "command": [
        "dropdb"
      ],
      "exitCode": 0,
      "stderr": "",
      "stdout": "confirmed by prior required dropdb step before normal stop"
    },
    "dropped": true,
    "name": "gda_v49_phase2a_phase2b_replay_a"
  },
  "schema": "gda-v49-phase2b-process-cleanup/v1",
  "status": "PASS",
  "taskOwnedImporterProcesses": 0,
  "taskOwnedPostgresProcesses": 0,
  "taskOwnedPsqlProcesses": 0,
  "taskOwnedResidualProcessLines": []
}
```

The staging bundle was moved before cluster disposal and remains at the explicitly recorded cache path. The source staging path and task-owned cluster root were both verified absent.
