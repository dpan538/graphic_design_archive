# Executive decision

Remote `main` received authoritative repository-hygiene commit `cc311ab0c9a74731cc1bb0158579708a8a9158fc` while Round 11 and Round 12 continued from common ancestor `4bd82deba482ec2fbf8c4856080151416fb8ee83`. The observed graph is exactly one main-only commit and two Round12-side commits. A two-parent merge is therefore required; rebasing, squashing, cherry-pick reconstruction, or force pushing would break sealed provenance.

The coordination preserves all three identities: main maintenance `cc311ab0c9a74731cc1bb0158579708a8a9158fc`, Round 11 `5ca999b53d9a5d18b47317817402f9e51ad26cec`, and Round 12 `fc11f033d2fcdbb98130879cdbd3e4a52890e5d2`. Parent order is fixed as main first and Round 12 second. The sole content conflict is rebuilt from the final tracked-script set, preserving main's enhanced diagnostic implementation and all Round 10–12 scripts.

Decision: `AUTHORITATIVE_HISTORY_COORDINATION`. No vocabulary, grammar, real Image, public Exploration surface, database, Search, Context, Spacetime, deployment, branch deletion, or evidence rewrite is activated by this merge.
