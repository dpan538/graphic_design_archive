# External research model eligibility gate

Policy is deny by default. This round approves zero external models. A future separate research round may change that only after every mandatory gate passes:

1. Peer-reviewed methodological basis.
2. Construct matches the relation research task.
3. Validation on relation-level semantic/historical language or a defensibly adjacent scholarly task.
4. Selection is not based on a generic leaderboard.
5. Sentence similarity or object embeddings are not substituted for historical relation semantics.
6. Relation-level output is interpretable.
7. Required directionality is supported.
8. Negation, qualification, contestation, and uncertainty behavior are known.
9. Failure modes are documented.
10. Exact versions and reproducible artifacts exist.
11. Licensing and security requirements pass.
12. A project-specific validation set exists.
13. Domain-method review is complete.
14. The model does not generate historical facts from statistical proximity.
15. A new explicit governance decision approves it.

Failure of any mandatory gate means `MODEL_STATUS=REJECT`. Model cards, MTEB/BEIR results, license, popularity, and model size are insufficient.
