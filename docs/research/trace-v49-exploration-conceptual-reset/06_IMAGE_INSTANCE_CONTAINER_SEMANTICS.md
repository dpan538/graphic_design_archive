# Image, Instance, and Container semantics

`ExplorationImage` uses Docker-image semantics: immutable, compiled, versioned, content-addressed, and reproducible. Its build SHA-256 is calculated from canonical key-sorted serialization excluding the digest field itself. Compilation deep-freezes the Image.

`ExplorationInstance` is a deterministic receipt for one Image, seed, and generation-policy version. The same inputs produce the same instance ID and structural receipt digest.

`ExplorationContainer` is mutable runtime state for an Instance: active conceptual components, positions, local edits, expanded branches, and hidden components. It stores no Image object and cannot mutate the base Image. Container edits do not change the Image build hash.

`RenderedPng` is a future flattened export contract. Its safe metadata binds Image ID/version/build hash, Instance ID, seed, and renderer version. It cannot carry arbitrary metadata or archive identity, and `pngIsSourceOfTruth` must be `false`.

SAVE INSTANCE preserves structured mutable state. EXPORT PNG produces flattened visual output. SAVE is not EXPORT, and PNG cannot reconstruct semantic state.
