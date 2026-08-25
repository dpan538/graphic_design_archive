# Determinism and hashing

Canonical serialization sorts record keys and preserves explicitly ordered semantic arrays. Package, request, Image, and Instance receipts use SHA-256. Semantic hashes exclude time, filesystem paths, PIDs, and random IDs. Identical package/request/seed/compiler inputs replay identically; seed can alter only a preauthorized synthetic layout choice and never authorization.
