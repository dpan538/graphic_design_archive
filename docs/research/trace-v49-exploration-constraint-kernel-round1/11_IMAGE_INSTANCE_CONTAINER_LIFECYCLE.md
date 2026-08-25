# Image, Instance, and Container lifecycle

The synthetic compiled Image is deeply frozen and content-addressed. A synthetic Instance binds the Image ID, version, Image hash, seed, generation policy, and structural receipt hash. A mutable synthetic Container holds positions and local edits but may target only IDs already authorized by the Image. Container edits leave Image serialization and hash unchanged. Real Instance and Container creation remain zero.
