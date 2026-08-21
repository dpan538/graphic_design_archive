# Gitignore, LFS, and large files

Runtime/cache/output patterns are ignored. Git LFS fsck passes. The active >10 MiB files are either manifested release inputs or existing frontend runtime data; new maintenance JSON files stay below 10 MiB. Duplicate large frontend/audit copies are explicitly classified and no unmanifested large blob or secret pattern remains.
