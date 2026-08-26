# Spatial semantics contract

`SPATIAL_PROXIMITY=ASSOCIATION_STRENGTH_AND_LOCAL_ELIGIBILITY`; `COLOR=PRIMARY_GENERIC_TYPE`; `SATURATION_OR_OPACITY=EVIDENCE_CONFIDENCE_OR_STATUS` (choose one implementation and document it). Each channel has one primary role.

The ordinal-to-layout mapping is `STRONG→NEAR_BAND`, `MODERATE→LOCAL_BAND`, and `WEAK/QUALIFIED/INSUFFICIENT→NO_ACTIVE_PROXIMITY`. This is a deterministic layout band, not a numeric evidence score. HIGH and MODERATE confidence may receive distinct documented opacity/saturation bands; LOW is inactive in V1.

The renderer must detect visual neighbours independently of graph adjacency. Any non-adjacent pair entering a meaningful closeness band must pass the applicable local standard or the layout solver must separate it. Aesthetic clustering cannot create unsupported semantic meaning.
