# Image immutability validation

The compiled synthetic Image is deeply frozen and hash-verified. Synthetic Instance creation passes. Container positions and local edits remain mutable runtime state, cannot target unknown semantic IDs, and cause zero Image-hash mutations.
