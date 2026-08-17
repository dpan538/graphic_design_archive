# Performance result

Final v5 measurements are not eligible for closure.  The builder exponent is
`ln(86370.397 / 26111.103) / ln(2) = 1.725873519`; the selection-plan exponent
is `ln(19125.186 / 3402.258) / ln(2) = 2.4908`.  Both exceed 1.35.

The first remediation removed v4's repeated public-set evaluation, scalar
membership snapshots, and unbounded full-row aggregate.  The second staged
component row digest work once.  It did not change the final 1k→2k gate.
The remaining hotspot is the current-leaf publishable-assignment SQL function,
whose outer plan is opaque Function Scan and whose measured selection time is
superlinear.  A third repair would violate the two-remediation limit.

Projected from the final builder measurements: 4k is approximately 285,696 ms
and 8k approximately 945,027 ms.  No projection is used as a pass result.
