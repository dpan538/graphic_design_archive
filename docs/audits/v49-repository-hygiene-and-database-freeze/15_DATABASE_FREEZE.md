# Database freeze

Database version is 49. The freeze manifest covers 126 implementation/contract files and verifies at SHA-256 `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e`. CI rejects frozen-file drift and unmanifested v49 database files; a future change requires version 50+, a new forward-only migration, and a v50 ADR.
