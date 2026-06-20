# Prefreeze Packet Role Applied Overrides v1

Scope: sandbox role-override file for testing main/sub/text structure after packet apply-ready review.

This pass does not mutate capture records, does not overwrite the canonical prefreeze role override file, does not download images, and does not change rights or image states.

## Summary

- base_override_rows: 2247 (Canonical prefreeze surface-role override input rows.)
- packet_apply_ready_rows: 200 (Packet role apply-ready rows considered.)
- merged_override_rows: 2445 (Rows written to sandbox merged override file.)
- collision_or_rejected_rows: 0 (Packet rows skipped because of duplicate/conflict/shape checks.)
- override_source:surface_role_override_v1: 2245 (Merged override source distribution.)
- override_source:packet_role_apply_ready_v1: 200 (Merged override source distribution.)
- role:card: 1943 (Merged override role distribution.)
- role:support_packet_appendix_text: 502 (Merged override role distribution.)

## Use

- Use this merged override file only for candidate rebuild / structure audit.
- Keep the canonical `prefreeze_surface_role_overrides_v1.csv` unchanged until the 200 packet rows pass sample review.
