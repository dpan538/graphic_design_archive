# v49 Phase 2A — Zero TRACE and zero positive-rights receipt

The physical model deliberately contains no non-zero acceptance requirement.
It preserves operational, proposed, held and rejected rows separately from
accepted release projection.

The release fixture validates, seals, independently verifies and promotes a
research release with zero `release.trace_projection_edge` rows. No legacy
projection edge is inserted or promoted to a canonical semantic relation.

The visual fixture validates, seals, independently verifies and promotes a
registry with zero entries and therefore zero positive delivery permission.
The current research object remains queryable, while every public locator is
absent. A separate positive visual fixture then proves that rights, policy,
attribution and bounded healthy evidence are all required for `REMOTE_IMAGE`,
and that health/takedown sidecars can only downgrade it.

Locked data facts remain unchanged:

```text
OPERATIONAL_ARCHIVE_OBJECTS=15923
RESEARCH_ELIGIBLE_OBJECTS=7995
HELD_OBJECTS=7928
ACCEPTED_TRACE_RELATIONS=0
POSITIVE_VISUAL_RIGHTS_COVERAGE=0.0000%
```

They are migration evidence, not hard-coded DDL counts or capacity limits.

`EMPTY_TRACE_STATE_SUPPORTED=true`

`ZERO_POSITIVE_RIGHTS_STATE_SUPPORTED=true`
