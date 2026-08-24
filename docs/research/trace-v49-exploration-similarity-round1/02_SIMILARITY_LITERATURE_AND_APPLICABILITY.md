# Similarity literature and applicability

## Scope and interpretation boundary

This is a research review, not a model-selection document. It evaluates what each required method actually measures and whether that question matches one of the four Exploration tasks. It does not authorize a public score, public weights, a public route or API, clustering, a renderer, or a historical-relation claim.

All uses of statistical probability below refer only to a paper's mathematical mechanism, such as a sampling probability, likelihood ratio, relevance framework, or transformed distance distribution. They never mean the probability that two archive objects are historically related. Every prospective output remains an `exploratory_derived_signal` with:

```text
historicalRelation=false
semanticRelation=false
probability=false
```

The review treats the Exploration tasks as different estimation or retrieval problems:

| Task | Question | Required directionality | Literature role |
| --- | --- | --- | --- |
| A | Which records share a balanced, explainable set of approved archive characteristics with an anchor object? | Normally symmetric | Gower-style family aggregation, independent-feature cosine/Jaccard, rarity-aware categorical matching, symmetric Tversky, and a non-scalar profile are benchmark candidates. |
| B | Which records best satisfy explicit query dimensions or an object-derived query? | May be asymmetric | Tversky contrast/ratio and BM25F-like fielded retrieval are directly relevant. |
| C | Which records match on declared dimensions while deliberately differing on another? | Query/template conditioned | This needs explicit match and difference constraints; it is not ordinary nearest-neighbor ranking. Tversky's distinction between common and distinctive features is conceptually useful, but no reviewed paper by itself defines the archive policy. |
| D | Which aggregate patterns occur inside a selected subset? | Not an object-pair task | Collection frequency, contingency-table likelihood ratios, rarity, concentration, and missingness summaries apply. Object affinity must not absorb this task. |

## 1. Gower: family-balanced similarity for mixed data

Primary source: [J. C. Gower, “A General Coefficient of Similarity and Some of Its Properties,” *Biometrics* 27(4), 1971](https://doi.org/10.2307/2528823).

- **Question answered.** How can per-variable similarities for heterogeneous observations be combined into one bounded coefficient while allowing a comparison to be unavailable for a particular variable? Gower defines an overall weighted average of partial similarities, with an indicator determining whether each character participates in the pair's denominator.
- **Symmetry or asymmetry.** Symmetric when every partial similarity and pair weight is symmetric. The original construction is intended for pairwise resemblance, not a directional query.
- **Data types supported.** Quantitative, qualitative/nominal, and dichotomous characters can be assigned type-specific partial similarities before aggregation. A quantitative contribution is range normalized; nominal values use an equality-style contribution; asymmetric binary characters can exclude a joint negative from comparison.
- **Multi-valued support.** Not native as an unconstrained set field. A multi-valued family can be supported only by declaring one symmetric partial set similarity for that family. Expanding every value into independent variables would let high-cardinality families contribute multiple times and would violate the Round 6 family-balance requirement.
- **Missing-feature behavior.** Gower's availability indicator removes a missing comparison from both numerator and denominator. This is a defensible available-family calculation, but it can make a pair observed on two families attain the same coefficient as a pair observed on six. The paper also limits its positive-semidefinite result when values are missing. Round 6 must therefore emit the availability mask and a separate comparability profile; a pairwise-renormalized value alone is insufficient.
- **Rare-feature behavior.** Ordinary nominal equality gives rare and common matches the same partial similarity. Rarity requires an independently justified partial similarity or weight; it is not supplied by the base coefficient.
- **Broad-feature behavior.** A match on a broad value receives full nominal credit unless explicitly attenuated. Family averaging limits the number of times a family can contribute, but it does not make a broad match discriminative.
- **Need for labels.** None. The coefficient uses observed attributes and declared type-specific comparison functions, not a target class.
- **Explainability.** High if implemented as one contribution per independent family: the numerator, eligibility indicator, family denominator, and partial similarity can all be exposed. Explainability falls if raw fields, derived interactions, and duplicated curatorial representations are silently treated as separate variables.
- **Metric properties.** Gower proved the similarity matrix positive semidefinite without missing data and related it to a Euclidean representation with distance proportional to `sqrt(1 - similarity)`. That result is not an unconditional claim that every implementation of `1 - S`, every custom partial set similarity, or every pairwise-missingness variant is a metric. The Round 6 implementation must test symmetry and must not claim triangle-inequality behavior merely from the method name.
- **Computational cost.** After ranges and categorical summaries are available, direct pair scoring is `O(F)` for `F` families. Candidate-only scoring is practical. Exhaustively scoring all pairs is still `O(N²F)` and belongs only in the bounded offline reference stream.
- **Applicability to this archive.** Strong conceptual fit for M5 and Task A because it makes type-specific family contributions and availability explicit. It also provides the cleanest literature precedent for keeping comparability visible. It is eligible for benchmarking, not automatically for selection.
- **Major failure modes.** Pairwise deletion can hide weak comparability; range normalization is sensitive to extremes; equality-only categorical contributions ignore rarity; custom set similarities can destroy the cited mathematical properties; and treating each token or derivation as a separate variable reintroduces family cardinality and lineage double counting.

**Round 6 consequence:** benchmark Gower-style family aggregation only after the independent signal basis is fixed. Emit `familyScores`, `jointlyObservableFamilies`, and `comparability` separately. Do not use projected map or centroid distance as a quantitative geography contribution.

## 2. Goodall: population-relative rarity-aware resemblance

Primary source: [D. W. Goodall, “A New Similarity Index Based on Probability,” *Biometrics* 22(4), 1966](https://doi.org/10.2307/2528080).

- **Question answered.** How unusual is an observed degree of resemblance relative to pairs drawn from the same population? Goodall orders value-pair resemblance within each attribute, computes the cumulative chance of the observed or a more similar pair, combines evidence across attributes, and takes its complement as similarity.
- **Symmetry or asymmetry.** Symmetric: the observed pair and its per-attribute resemblance do not designate a query and a candidate.
- **Data types supported.** The original framework is broader than a single modern “Goodall categorical” formula: it describes ordered per-attribute resemblance and combines per-attribute sampling probabilities. Round 6's M4 is specifically a Goodall-*style* categorical rarity experiment, not a claim to reproduce every original character treatment.
- **Multi-valued support.** Not automatic. Multi-valued archive families require a declared set-level observation model or a single bounded family contribution. Treating each membership as an independent Goodall attribute would overweight large sets and violate the independence assumptions behind combining attributes.
- **Missing-feature behavior.** Missingness is not a ready-made positive match in the method. Unavailable attributes must be excluded under an explicit availability rule and surfaced through comparability. Encoding `UNKNOWN`, `NOT_GOVERNED`, or another missing state as an ordinary rare category would give exactly the wrong kind of rarity credit.
- **Rare-feature behavior.** This is the method's attraction: an uncommon matched value can be more discriminative than a common matched value. It is also the archive risk. Estimated population probabilities at support 1–2 are unstable, change with the cohort, and can make a single rare observation dominate unless the contribution is smoothed and capped.
- **Broad-feature behavior.** Common matches receive less evidence because comparable random agreement is more likely. This aligns with broad-container attenuation, but only after curated memberships duplicated by governed Context/Spacetime values are removed.
- **Need for labels.** No target labels are required; observed population frequencies supply the reference distribution. The cohort definition is therefore part of the method and must be pinned in every analysis receipt.
- **Explainability.** Moderate to high for a bounded per-family adaptation: report the matched value, support, eligible population, smoothing rule, and cap. The original cross-attribute probability combination is harder to explain and relies on assumptions that are not automatically true of correlated archive families.
- **Metric properties.** It is a population-relative similarity index, not a guaranteed metric distance. Its value can change when the reference cohort changes even if the two objects do not.
- **Computational cost.** Frequency summaries are `O(NF)`; a simple capped per-family candidate score is `O(F)`. The original exact cross-attribute combination is more involved. Boriah et al. explicitly did not empirically evaluate the original combined procedure because of its computational cost, so a simplified “Goodall-style” benchmark must be named precisely.
- **Applicability to this archive.** Eligible for M4 as a sensitivity-tested, capped categorical component or diagnostic. It is most plausible inside independent governed families, not as a raw curatorial score and never as “rare means important.”
- **Major failure modes.** Support-1 inflation; cohort drift; correlated families treated as independent; missing states becoming rare matches; unstable values for small strata; and a statistical rarity statement being misread as historical importance.

**Round 6 consequence:** benchmark smoothed and capped variants over support thresholds `2,3,5,10,20`, report cohort and denominator, and count any low-support case that defeats the mechanical ordering rules. A rare match may improve discrimination but must never supply unbounded affinity.

## 3. Tversky: common and distinctive feature contrast

Primary source: [Amos Tversky, “Features of Similarity,” *Psychological Review* 84(4), 1977](https://doi.org/10.1037/0033-295X.84.4.327).

- **Question answered.** How can similarity be represented as a comparison of common features and features distinctive to each object, rather than as geometric distance alone? The contrast model uses a weighted common-feature term minus separately weighted `A - B` and `B - A` terms. The related ratio form normalizes common-feature mass by common and distinctive mass.
- **Symmetry or asymmetry.** Either. Equal weights on the two distinctive sets yield a symmetric task; unequal weights make directionality explicit. Tversky specifically treats task and context as determinants of feature salience and demonstrates why directional judgments need not be symmetric.
- **Data types supported.** Native input is a feature representation. Binary and nominal properties map naturally; ordinal or quantitative variables require an explicit feature construction or partial representation and are not automatically handled as calibrated distances.
- **Multi-valued support.** Native for sets of approved, family-qualified features. High-cardinality families still require family caps or normalization so that more tokens do not mean more evidential weight.
- **Missing-feature behavior.** The model distinguishes presence in both, only the first set, or only the second set. It does not know whether absence means “observed absent” or “unavailable.” Unknown states must therefore be removed from the base feature space and carried in the comparability/missingness channel. Otherwise a shared unknown token becomes a positive common feature, or one-sided missingness becomes an unjustified distinctive penalty.
- **Rare-feature behavior.** Rarity is controlled entirely by the feature measure `f`. Counts give no rarity attenuation; IDF-like or other declared weights can make uncommon features more salient. Those weights must be bounded and lineage-deduplicated.
- **Broad-feature behavior.** Broad features are harmless only if `f` downweights them or the family is capped. With unit feature counts, a broad container match is credited like a discriminative governed feature.
- **Need for labels.** None for a declared feature measure and parameter grid. Learning salience or tuning `alpha/beta` from relevance judgments would require labels; Round 6 has no such judgments, so parameters may only be benchmarked on a declared grid and mechanical cases.
- **Explainability.** High. Common features, query-only features, candidate-only features, and their weights directly form an explanation. It is especially suitable for Task B because asymmetry can be stated as a query policy instead of hidden inside a supposedly universal score.
- **Metric properties.** Tversky challenges the automatic use of metric assumptions. The contrast model is neither necessarily symmetric nor a metric; the linear form may not be bounded. The ratio form is bounded between zero and one under its parameter constraints, but asymmetry and the triangle inequality still depend on parameterization and representation.
- **Computational cost.** Sparse set intersection and difference are linear in the participating feature counts and can be driven by an inverted index. A parameter grid multiplies offline benchmark cost but not feature extraction cost.
- **Applicability to this archive.** Strong fit for M6 and Task B, where selected Theme/Medium/Time/Geography dimensions define a directional query. A symmetric grid is also relevant to Task A. The method is a benchmark family, not support for one global parameter choice.
- **Major failure modes.** Unjustified salience weights; task direction left implicit; missingness encoded as a feature; high-cardinality families dominating; negative or hard-to-compare raw contrast values; and a distinctive-feature penalty being misconstrued as historical opposition.

**Round 6 consequence:** report symmetric and asymmetric variants separately. Every asymmetric result must name the query, referent, feature measure, and parameter set. Parameter values cannot be learned or chosen from visual appeal.

## 4. Spärck Jones: collection-frequency specificity / IDF

Primary source: [Karen Spärck Jones, “A Statistical Interpretation of Term Specificity and Its Application in Retrieval,” *Journal of Documentation* 28(1), 1972](https://doi.org/10.1108/eb026526).

- **Question answered.** How should a matching term's retrieval value depend on how broadly that term is used in the collection? The paper interprets specificity statistically and gives less frequent terms greater matching value while retaining frequent terms because they remain useful for recall.
- **Symmetry or asymmetry.** Collection-frequency weighting itself is not a pairwise direction rule. Applied to the same weighted vectors with cosine or weighted Jaccard it can be symmetric; applied as query-document retrieval it participates in an asymmetric task.
- **Data types supported.** Sparse discrete terms or feature tokens. Numeric time extents and governed temporal precision require their own family functions rather than tokenization by accident.
- **Multi-valued support.** Native for multiple terms, but document/record exhaustivity matters. Records with more assigned values have more match opportunities, so family-level normalization and caps are necessary.
- **Missing-feature behavior.** An absent term makes no positive contribution, but ordinary sparse retrieval does not distinguish observed absence from unavailable metadata. A separate availability/comparability channel is still required, and missingness tokens must be excluded from base affinity.
- **Rare-feature behavior.** Rarer collection terms receive greater weight. The paper's central result does not imply that a singleton is important; it shows a retrieval-specific statistical role. Round 6 must smooth and cap modern IDF variants and test support thresholds.
- **Broad-feature behavior.** Broad terms are attenuated, not necessarily discarded. This exactly supports the Round 6 distinction between broad curation as recall substrate and broad curation as weak ranking evidence.
- **Need for labels.** Collection-frequency weights need no relevance labels. Selecting among formulas, family weights, or smoothing parameters using retrieval quality would require judgments; without them, use declared baselines and mechanical tests.
- **Explainability.** High: expose the token, document frequency, eligible cohort, formula, weight, and family cap. A family-qualified token vocabulary also makes lineage and source identity auditable.
- **Metric properties.** IDF is a weighting scheme, not a distance. Weighted cosine is symmetric but `1 - cosine` is not generally a metric; weighted Jaccard/Tanimoto has separate properties. Do not transfer a metric claim from the weighting to the scorer.
- **Computational cost.** One corpus pass produces document frequencies; an inverted index supports sparse candidate generation and dot products. It is well suited to object-local scoring without storing pair rows.
- **Applicability to this archive.** Foundational for M2 and M3 and for information-weighted candidate postings. It is also useful in M7 fields. Use only independent, approved family-qualified tokens, with within-family and global IDF benchmarked separately.
- **Major failure modes.** Singleton explosion; cohort changes altering weights; duplicated source facts receiving multiple tokens; verbose/high-cardinality families dominating cosine norms or weighted unions; and treating statistical specificity as semantic or historical significance.

**Round 6 consequence:** keep broad postings for candidate recall where useful, but cap or downweight their ranking contribution. Publish the exact `N`, `df`, smoothing, family normalization, and stop policy in every analysis receipt.

## 5. Robertson and Zaragoza: BM25 and BM25F as query-conditioned retrieval

Primary source: [Stephen Robertson and Hugo Zaragoza, “The Probabilistic Relevance Framework: BM25 and Beyond,” *Foundations and Trends in Information Retrieval* 3(4), 2009](https://doi.org/10.1561/1500000019).

- **Question answered.** Given a query, how should documents be ranked using term evidence, collection discrimination, within-document term frequency saturation, length normalization, and—in BM25F—multiple weighted document streams or fields?
- **Symmetry or asymmetry.** Asymmetric. Query and document have distinct roles, and BM25/BM25F should not be presented as a universal symmetric object distance. An anchor object can supply query features only under a declared object-as-query policy.
- **Data types supported.** Token/count fields and other explicitly modeled retrieval features. Categorical archive values map to family-qualified tokens. Temporal intervals and other continuous signals need separate field functions or query predicates; forcing them into term frequency would obscure their semantics.
- **Multi-valued support.** Native for multiple terms and multiple fields. Term-frequency saturation prevents repeated terms from growing linearly, while field normalization and field weights address stream length. Multi-valued archive fields still need deterministic tokenization and family boundaries.
- **Missing-feature behavior.** A missing field or absent query term gives no matching contribution, but BM25F does not by itself distinguish “no value” from “not observed.” Comparability and missingness therefore remain separate. Missing-state tokens are prohibited from ordinary affinity fields.
- **Rare-feature behavior.** IDF favors discriminative terms. Low-document-frequency terms need a documented nonnegative/smoothed formulation and cap so support 1–2 cannot dominate merely through rarity.
- **Broad-feature behavior.** High-document-frequency features are attenuated by IDF; field length normalization and saturation reduce repetition effects. A broad field can still dominate through an excessive field weight or many matching terms, so the source and curation families require caps and sensitivity analysis.
- **Need for labels.** The framework is motivated by relevance. Scoring can run with collection statistics and declared parameters, but choosing field weights and free parameters by retrieval effectiveness normally relies on relevance judgments. With no trusted archive relevance labels, Round 6 may benchmark a declared grid and mechanical expectations but may not learn or claim optimal weights.
- **Explainability.** Moderate to high if each query-term/field contribution, `df`, term frequency, saturation, normalization, and field weight is returned. It is less immediately intuitive than an equal-family baseline, particularly if an anchor object's many fields silently become a query.
- **Metric properties.** Not a metric. It is query-conditioned, generally asymmetric, and has no triangle-inequality requirement.
- **Computational cost.** Well suited to an inverted index: query cost follows postings for query terms rather than all objects. BM25F requires per-field lengths, averages, and weights but no pair matrix.
- **Applicability to this archive.** Strong candidate for M7 and Task B. It may serve explicit user filters or an object-derived query, but it is not an answer to Task A's symmetric affinity question and it is not a relation probability.
- **Major failure modes.** Presenting a retrieval score as affinity or probability; tuning without relevance judgments; field-length artifacts; dominant source/curation fields; duplicated lineage terms; negative or unstable rare-term weights; and query expansion that imports unavailable or disallowed metadata.

**Round 6 consequence:** BM25F-like experiments must be labeled `QUERY_CONDITIONED_ASYMMETRIC`, publish their field and parameter grid, and never be compared to symmetric scores without acknowledging the different task.

## 6. Boriah, Chandola, and Kumar: comparative discipline for categorical measures

Primary source: [Shyam Boriah, Varun Chandola, and Vipin Kumar, “Similarity Measures for Categorical Data: A Comparative Evaluation,” *Proceedings of the 2008 SIAM International Conference on Data Mining*, 2008](https://epubs.siam.org/doi/10.1137/1.9781611972788.22).

- **Question answered.** How do multiple data-driven categorical similarity measures compare on a specified downstream task? The paper evaluates fourteen measures for outlier detection and finds that no single measure dominates across all tested data sets.
- **Symmetry or asymmetry.** The per-attribute measures studied are principally pairwise categorical similarities and are generally symmetric. The paper's evaluation lesson, rather than one formula, is the relevant method here.
- **Data types supported.** Categorical attributes. It does not establish a complete mixed temporal/set/missingness model for this archive.
- **Multi-valued support.** The study's standard representation is one categorical value per attribute. Archive set-valued families would require a declared transformation or partial set similarity; exploding memberships into many attributes changes the family weighting problem.
- **Missing-feature behavior.** Missingness is not the paper's central evaluation dimension. An implementation must specify whether missing values are excluded or encoded; encoding them as categories would allow frequency-based missingness matches and is unacceptable for base affinity here.
- **Rare-feature behavior.** The compared measures deliberately differ in how they value rare matches and common/mismatching values. The paper therefore supports a sensitivity suite, not the assertion that one rarity formula is universally correct. It also distinguishes the original Goodall combination from simplified Goodall variants; the original is not empirically tested there because it is computationally expensive.
- **Broad-feature behavior.** Frequency-aware measures can treat common values differently, while simple overlap cannot. Results depend on the data distribution and downstream task, so broad-feature attenuation must be evaluated on this archive's real distributions.
- **Need for labels.** Computing most compared similarities uses corpus frequencies, not target labels. The paper's outlier-detection evaluation uses an external task outcome; its performance findings cannot substitute for archive researcher judgments or mechanical expectations.
- **Explainability.** Varies by formula. The comparative framework is explainable when per-attribute terms and statistics are retained, but a table of outlier performance does not explain an individual archive candidate.
- **Metric properties.** Vary across the fourteen measures; the study does not confer metric status on “categorical similarity” as a class.
- **Computational cost.** Frequency summaries are inexpensive, but the study's pairwise comparisons scale quadratically. Round 6 can reproduce the comparative discipline through streamed exhaustive reference rankings and bounded top-k, without committing a pair matrix.
- **Applicability to this archive.** Strong evidence for benchmarking M1–M5 rather than choosing by reputation. Its results are task-specific evidence about outlier detection, not evidence that any winner is correct for object-local Exploration.
- **Major failure modes.** Transferring outlier-detection results to affinity; treating single-valued attributes as equivalent to archive sets; overlooking missingness; collapsing fourteen distinct formulas into “categorical distance”; and citing a simplified Goodall variant as the original combined index.

**Round 6 consequence:** retain the transparent overlap baseline and multiple frequency-aware alternatives, test them on the same mechanical and real-data protocol, and describe each formula exactly. Literature fame and prior outlier performance are not selection criteria.

## 7. Dunning: log-likelihood ratio for interaction surprise

Primary source: [Ted Dunning, “Accurate Methods for the Statistics of Surprise and Coincidence,” *Computational Linguistics* 19(1), 1993](https://aclanthology.org/J93-1003/).

- **Question answered.** Given contingency counts, how strongly does the observed joint pattern depart from an independence model, especially when normal approximations are unreliable for sparse events? Dunning develops likelihood-ratio tests for binomial and multinomial counts and applies them to word/bigram association.
- **Symmetry or asymmetry.** The unsigned likelihood-ratio statistic for a fixed two-way contingency table is invariant under transposing its event dimensions, although the event design itself can be directional (for example, one event preceding another). It is not an object-to-object similarity direction. A signed interpretation must separately compare observed and expected counts.
- **Data types supported.** Discrete event counts and contingency tables. Archive pair/triple cells can be treated as categorical events after lineage deduplication.
- **Multi-valued support.** Multiple memberships can generate events, but the unit of observation and denominator must be declared. Correlated memberships from the same object or source structure violate a naive independent-event interpretation.
- **Missing-feature behavior.** Missing/unavailable cases must be excluded from the relevant eligible population or analyzed in the dedicated missingness channel. Encoding missingness as an ordinary event would make documentation practice look like substantive interaction.
- **Rare-feature behavior.** The likelihood ratio behaves better than a normal/chi-square approximation in sparse regimes, but “statistically surprising” is not “important.” A support-1 or support-2 cell remains estimation-sensitive and must not become an uncapped object-pair contribution.
- **Broad-feature behavior.** Expected counts account for broad marginals, so a frequent feature is not automatically interesting. Large samples can still make small departures produce large statistics; effect size, support, and bounded contribution remain necessary.
- **Need for labels.** No historical or class labels. It requires observed counts, an explicit null model, and eligible denominators.
- **Explainability.** High as an aggregate diagnostic when the four contingency counts, observed count, expected count, support, direction, statistic, and threshold are shown. It becomes misleading if emitted as a score without the null and denominators.
- **Metric properties.** None. A likelihood-ratio statistic is neither a pairwise metric nor an affinity coefficient.
- **Computational cost.** Once marginals and observed cells exist, each bounded interaction cell is constant-time to evaluate. Streaming observed cells is practical; enumerating or materializing all object pairs is unnecessary.
- **Applicability to this archive.** Strong for Task D and the interaction-statistics review. It can test whether an observed pair/triple cell contains information beyond parent marginals and may support a capped residual interaction experiment. It is not a base object similarity model.
- **Major failure modes.** Low-support inflation interpreted semantically; statistical significance confused with effect size; multiple-comparison burden; incorrect eligible denominators; correlated lineage treated as independent evidence; and adding the interaction statistic on top of its parents without residualization.

**Round 6 consequence:** compare raw support, lift, PMI, normalized PMI, log-likelihood ratio, and smoothed/shrunk variants on the declared support grid. Any interaction contribution must be residual, capped, and separated from base-family evidence.

## 8. Wilson and Martinez: VDM/HVDM and the label-dependency disqualifier

Primary sources: [D. Randall Wilson and Tony R. Martinez, “Improved Heterogeneous Distance Functions,” *Journal of Artificial Intelligence Research* 6, 1997](https://www.jair.org/index.php/jair/article/view/10182) ([DOI](https://doi.org/10.1613/jair.346)).

- **Question answered.** In supervised instance-based learning, how can distances combine nominal attributes with continuous attributes? VDM compares nominal values through the differences between their conditional distributions over output classes; HVDM combines that nominal distance with normalized continuous distance.
- **Symmetry or asymmetry.** Symmetric for a fixed training set and class-distribution table.
- **Data types supported.** Nominal plus continuous attributes. HVDM uses VDM for nominal values and a standard-deviation-normalized difference for continuous values.
- **Multi-valued support.** Not native. The paper assumes one input value per attribute. Set-valued archive families would need an encoding that could change both class statistics and weighting.
- **Missing-feature behavior.** The paper assigns per-attribute distance `1` if either value is unknown. That is useful for its classification experiments but conflicts with Round 6's requirement to separate unavailability from dissimilarity. It also means two records sharing an unknown value are not identical on that attribute, while any one-sided unavailability is treated as maximal difference.
- **Rare-feature behavior.** Nominal distance depends on estimated `P(class | attribute value)` rather than rarity alone. Rare attribute values have noisy class-distribution estimates. The paper discusses statistical sampling and normalization effects, including sensitivity to class imbalance.
- **Broad-feature behavior.** A broad value is close to another value when their conditional class distributions are similar; breadth itself is not an IDF attenuation. Dominant or skewed classes can reduce nominal attribute influence.
- **Need for labels.** **Required.** VDM/HVDM constructs nominal distances from output-class counts. The paper's algorithm explicitly iterates over each training instance's output class and estimates a probability for every attribute-value/class combination. The archive has no trusted historical-relation class and no accepted affinity label. Choosing Theme, Source, or another archive field as a pseudo-class would answer a different supervised prediction problem and would bake that field into every nominal distance.
- **Explainability.** A technical explanation can show per-class conditional distributions and per-attribute distances, but it would still need to explain why that output class defines similarity. In this archive there is no defensible answer to that prerequisite.
- **Metric properties.** HVDM is presented as a distance function for nearest-neighbor learning, but VDM can assign zero distance to distinct categorical values with identical class distributions, and the unknown-value rule complicates identity. It should not be assumed to be a strict metric over archive records.
- **Computational cost.** The paper reports `O(mn + mvC)` storage/statistics for HVDM-like methods and `O(mnC)` generalization when comparing a query with all training instances, or `O(mn)` with precomputed value distances, where `m` is attributes, `n` training instances, `v` values, and `C` output classes.
- **Applicability to this archive.** **Not applicable as an affinity model in Round 6.** Its mixed-attribute support does not repair the absent-label problem. The paper remains useful as a negative applicability result and as a warning that “handles heterogeneous data” does not mean “unsupervised.”
- **Major failure modes.** Invented class labels; target leakage if an archive family becomes the class; unstable low-support conditional distributions; class-imbalance distortion; maximal-distance treatment of missingness; and opaque supervised semantics presented as neutral affinity.

**Round 6 consequence:** `HVDM_AFFINITY_ELIGIBLE=false`. Do not implement VDM/HVDM by inventing a relation class or by treating a governed descriptive dimension as proxy truth. Mixed-data needs are addressed by explicit family functions and comparability masks instead.

## 9. Radovanović, Nanopoulos, and Ivanović: hubness as a required diagnostic

Primary source: [Miloš Radovanović, Alexandros Nanopoulos, and Mirjana Ivanović, “Hubs in Space: Popular Nearest Neighbors in High-Dimensional Data,” *Journal of Machine Learning Research* 11, 2010](https://www.jmlr.org/papers/v11/radovanovic10a.html).

- **Question answered.** Does a nearest-neighbor system produce objects that occur in unusually many other objects' top-`k` lists, and how does that `k`-occurrence distribution change with dimensionality and data geometry? The paper defines `N_k(x)` as the number of neighbor lists containing `x` and studies the skewness of that distribution.
- **Symmetry or asymmetry.** `N_k` diagnoses directed nearest-neighbor lists even when the underlying distance is symmetric. Neighbor membership itself need not be reciprocal.
- **Data types supported.** Any representation and distance/similarity that yields a ranked neighbor list. Categorical, sparse, or mixed archive features are supported indirectly through the tested base model.
- **Multi-valued support.** Inherited from the base representation. Token or membership expansion can increase effective dimensionality and create hubs, which is precisely why family normalization and lineage deduplication must precede interpretation.
- **Missing-feature behavior.** Inherited from the base scorer. High observability can itself correlate with hubness, so Round 6 must correlate occurrence with jointly observable family count rather than treating hubness as only a geometric effect.
- **Rare-feature behavior.** Also inherited. Extreme rarity weights can make a few records attract or repel many queries; `k`-occurrence reveals the outcome but does not justify the weight.
- **Broad-feature behavior.** Broad source/container/common-feature records are plausible archive-specific hubs. The diagnostic should explicitly correlate hub status with dominant source, largest containers, common Context values, geography/decade, and observability.
- **Need for labels.** None for ordinary `N_k`, skewness, Gini, maximum occurrence, or zero-occurrence counts. The paper's “good” versus “bad” hub analysis uses class labels, which Round 6 cannot reproduce without trusted labels; those terms must not be used as archive judgments.
- **Explainability.** High for detection: report occurrence count, distribution, source/family correlations, and representative neighbor lists. It does not explain why the underlying model produced the hub unless contribution diagnostics are joined.
- **Metric properties.** Not a metric. It is a property of ranked neighborhoods generated by another measure.
- **Computational cost.** After bounded top-`k` lists exist, counting occurrences is `O(Nk)`. Exact top-`k` lists may require streamed exhaustive scoring or high-recall candidates; no all-pairs artifact needs to be stored.
- **Applicability to this archive.** Mandatory evaluation architecture for every scalar candidate at `k=10,20,50`. The requested variance, skewness, Gini, top-1% share, maximum, and zero-occurrence count add complementary distribution diagnostics to `N_k`.
- **Major failure modes.** Declaring every popular neighbor erroneous; applying high-dimensional theory as proof without measuring the archive; ignoring deterministic tie policy; confusing hubs with high-quality results; using labels to call a hub “bad”; and measuring only average occurrence, which is fixed at `k` and hides skew.

**Round 6 consequence:** a model cannot be evaluated from its score distribution alone. Its reverse-neighbor occurrence distribution and correlations with source, curation, common values, and observability must be reported.

## 10. Schnitzer et al.: local/global scaling as conditional hubness correction

Primary source: [Dominik Schnitzer, Arthur Flexer, Markus Schedl, and Gerhard Widmer, “Local and Global Scaling Reduce Hubs in Space,” *Journal of Machine Learning Research* 13, 2012](https://www.jmlr.org/papers/v13/schnitzer12a.html).

- **Question answered.** Can a base distance be reinterpreted relative to local neighborhoods or each object's global distance distribution so that hubness and asymmetric neighbor relations are reduced? The paper evaluates local scaling/NICDM and proposes Mutual Proximity as a global transformation.
- **Symmetry or asymmetry.** The transformations combine statistics from both objects and are designed to make neighbor relations more reciprocal. The underlying ranked neighborhoods can remain nonidentical in finite top-`k` lists. Symmetry must be tested on the actual implementation.
- **Data types supported.** Any data type with a nonnegative base divergence and a usable distance distribution. The transformation does not define the underlying categorical, temporal, or missingness semantics.
- **Multi-valued support.** Inherited from the base distance. Scaling cannot repair lineage duplication or high-cardinality family dominance; it may only change the resulting neighborhood geometry.
- **Missing-feature behavior.** Inherited and potentially obscured. If low comparability distorts base distances, neighborhood scaling can normalize that distortion instead of correcting it. Comparability must be resolved before any scaling experiment.
- **Rare-feature behavior.** Inherited. A rare-feature spike can alter local scales or global distance distributions. Scaling may reduce the resulting hubness but does not justify the rare feature's evidential meaning.
- **Broad-feature behavior.** Scaling can reduce the popularity of points that are close to many others under a broad feature, but it acts on resulting distances rather than transparently attenuating the responsible container/source contribution.
- **Need for labels.** The transformations themselves are unsupervised. The paper evaluates some outcomes with classification and retrieval labels; those improvements are not available as an archive selection criterion. Hub reduction can be measured without labels.
- **Explainability.** Low to moderate. Local scaling depends on each object's neighborhood radius or mean neighbor distance. Global scaling depends on the distribution of distances from each object. The adjusted result is therefore collection-contextual and harder to explain from shared archive features alone.
- **Metric properties.** The paper requires only a nonnegative underlying divergence. The transformed affinities/distances should not be assumed to preserve identity, triangle inequality, or the base metric's geometry.
- **Computational cost.** Local scaling requires nearest-neighbor statistics. Exact global scaling uses all distance distributions and is quadratic; the paper describes a sampling approximation that can reduce parameter estimation toward linear cost for constant sample size. Round 6 prohibits randomness from affecting affinity or candidate sets, so a randomized approximation is ineligible unless replaced by an explicit deterministic policy and then separately validated. Exact analysis can use the bounded offline stream but must not persist a matrix.
- **Applicability to this archive.** Analysis-only fallback if a shortlisted base model exhibits severe measured hubness. It is not a baseline affinity model and must not precede fixing source/curation dominance, missingness, lineage, and family normalization.
- **Major failure modes.** Correcting symptoms while preserving biased evidence; opaque explanations; instability under cohort changes or neighborhood parameter `k`; loss of top-`k` stability; additional candidate-recall demands; distributional assumptions that do not fit; and sampled scaling violating deterministic ranking.

**Round 6 consequence:** test local/global scaling or reciprocal-neighbor filtering only after severe hubness is observed. Select no correction merely because it lowers one hubness statistic; also measure stability, recall, symmetry, source bias, and explanation complexity.

## Cross-method applicability conclusions

### Independent families must precede every method

None of the reviewed literature excuses double counting. Gower averages declared variables; Goodall combines attribute evidence; Tversky aggregates features; IDF/cosine and BM25F aggregate tokens; Dunning evaluates cells; HVDM aggregates attributes. Every one will faithfully count a duplicate representation if the implementation supplies it twice. The signal-lineage registry and independent basis are therefore logical prerequisites, not optional post-processing.

The following must remain one source-fact contribution, not four:

```text
governed theme
shared theme source folder
theme × decade cell
rare theme × decade cell
```

The direct governed theme may enter base affinity once. The source folder can support candidate retrieval or provenance. The interaction may enter only as a separately capped residual if it adds information beyond its parents. Rarity describes population support; it is not another independent match.

### Recall substrate is distinct from ranking evidence

Spärck Jones shows why frequent terms can aid recall even when their individual matches are weakly discriminative. BM25/BM25F formalizes efficient postings-driven retrieval and damped ranking. This supports retaining broad curation as a candidate-recall layer while prohibiting raw curated Jaccard from ranking. The fact that 28,008,976 public pairs share curation makes the raw overlap a negative control and structural diagnostic, not an eligible scorer.

### Comparability cannot be hidden in the score

Gower's missingness mask is the most relevant precedent, but a changing pair denominator makes the same scalar value carry different evidence volumes. Sparse IDF, Tversky, and BM25F likewise conflate absent with unavailable unless the data model intervenes. HVDM instead turns unknown into maximal per-attribute distance, which is also wrong for this task. The defensible architecture is the required two-channel form:

```text
observed-family affinity
+
explicit comparability profile
```

Shared `UNKNOWN_SOURCE_VALUE`, `QUALIFIED_UNKNOWN_SOURCE_VALUE`, `NO_PUBLISHED_MOVEMENT_CONTEXT`, or `NOT_GOVERNED` states contribute zero ordinary affinity. They may be explored in Task D or a dedicated missingness mode.

### Rarity and interaction are bounded diagnostics before they are evidence

Goodall-style weighting, IDF, PMI/lift, and Dunning's likelihood ratio all use population frequency in different ways. None makes rarity synonymous with importance. Goodall and IDF can amplify singleton matches; PMI and lift are especially unstable at low support; likelihood ratios improve sparse-count inference but do not turn a tiny cell into a historically meaningful pattern. The archive must report support, eligible denominator, smoothing, cap, and sensitivity threshold with every such contribution.

### HVDM/VDM is not an unsupervised mixed-data escape hatch

HVDM is the clearest negative applicability result. Its nominal distance is explicitly built from conditional output-class distributions. No trusted archive affinity class exists. Inventing one would violate the research boundary and make the result a classifier for the invented target, not a neutral mixed-data similarity. Therefore HVDM/VDM must not be adopted merely because its name promises heterogeneous attributes.

### Hubness correction is downstream of semantic correctness

Radovanović et al. makes reverse-neighbor occurrence measurement mandatory. Schnitzer et al. provides plausible transformations when severe hubness is observed. A correction cannot repair duplicate lineage, a dominant broad container, invalid missingness treatment, or an invented class label. Fix those causes first. If hubness remains severe, treat scaling as an analysis-only transformation and require deterministic behavior plus stable explanations.

## Implications for the Round 6 model suite

| Round 6 model | Literature support | Research disposition from literature review |
| --- | --- | --- |
| M0 raw curated Jaccard | The reviewed rarity/retrieval literature explains why ubiquitous features discriminate poorly; archive measurements already demonstrate saturation. | `DIAGNOSTIC_ONLY`; negative control; static production-import prohibition required. |
| M1 equal family overlap | Gower supports aggregation of type-specific partial similarities; Boriah et al. supports retaining transparent baselines. | Eligible baseline after lineage deduplication and with separate comparability. |
| M2 IDF sparse cosine | Spärck Jones supplies collection-frequency specificity; hubness literature requires reverse-neighbor diagnostics. | Eligible benchmark with global, within-family, smoothed, and capped variants. |
| M3 IDF weighted Jaccard/Tanimoto | Spärck Jones supports weighting, not the assumption that weighting cures set-similarity failure. | Eligible separate benchmark; must not inherit M0's raw curated features. |
| M4 Goodall-style categorical | Goodall supplies population-relative rarity; Boriah et al. demonstrates formula/task sensitivity. | Eligible bounded sensitivity experiment; original and simplified variants must not be conflated. |
| M5 Gower-style family composite | Gower directly supports mixed partial similarities and availability masks. | Eligible Task A benchmark with explicit family functions and a separate comparability profile. |
| M6 Tversky contrast/ratio | Tversky directly supports common/distinctive features and explicit asymmetry. | Eligible symmetric Task A and query-conditioned Task B parameter grids; no tuned weights. |
| M7 BM25F-like retrieval | Robertson and Zaragoza directly support fielded query-document retrieval. | Eligible only as Task B/query-conditioned retrieval; not a universal symmetric affinity. |
| M8 non-scalar/Pareto profile | None of the reviewed sources establishes that heterogeneous archive evidence must collapse to one scalar. | Necessary project baseline for testing whether multiple explainable profiles are preferable; no literature claim of dominance. |

Dunning's likelihood ratio is attached to interaction review rather than introduced as an additional object-pair model. Radovanović's `k`-occurrence statistics apply to every scalar benchmark. Schnitzer-style scaling is conditional on measured severe hubness. HVDM/VDM is excluded because of required class labels and incompatible missing-value semantics.

## Evaluation consequences

1. Mechanical expectations precede any ranking preference. A duplicate derivation, shared unknown state, broad-container-only match, or same-source-only match cannot win because a literature formula gives it a large number.
2. No historical-relation labels exist. HVDM/VDM is therefore ineligible; BM25F weights and Tversky parameters cannot be trained; and supervised “good/bad hub” categories cannot be emitted.
3. Real-data stability and ablation are mandatory because Boriah et al. shows method performance is data/task dependent, while all collection-frequency methods change with the cohort.
4. Hubness must be measured at `k=10,20,50` with reverse-neighbor distributions and correlations to archive breadth/observability. A low average is meaningless because mean `N_k` is structurally tied to `k`.
5. Human review remains necessary because none of the papers supplies archive-specific usefulness judgments. The review packet must ask about exploratory utility and explanation clarity, never hidden historical truth.
6. Explanations must expose retrieval reason, independent family contributions, distinctive features, unavailable families, comparability, attenuation, interaction residuals, method/version, and pinned input hashes.
7. Candidate generation and scoring remain separate. Inverted postings are supported by retrieval literature; no paper requires materializing the 31,956,015-pair space.
8. No reviewed method supports geographic screen/centroid distance as historical evidence. Geography remains exact governed overlap/state unless a separate governed research-distance model is later authorized.

## Literature-review decision

```text
REQUIRED_PRIMARY_SOURCE_COUNT=10
REQUIRED_PRIMARY_SOURCE_REVIEWED_COUNT=10
PRIMARY_SOURCE_URL_MISSING_COUNT=0
METHOD_APPLICABILITY_FIELD_COUNT=13
HVDM_REQUIRES_TRUSTED_CLASS_LABEL=true
HVDM_AFFINITY_ELIGIBLE=false
HUBNESS_DIAGNOSTIC_REQUIRED=true
HUBNESS_CORRECTION_AUTOMATICALLY_ELIGIBLE=false
LOCAL_GLOBAL_SCALING_EXPLANATION_COMPLEXITY=HIGH
RAW_CURATED_JACCARD_PRODUCTION_ELIGIBLE=false
LITERATURE_SELECTS_MODEL=false
PUBLIC_SIMILARITY_MODEL_SELECTED=false
```

## Primary-source register

1. [Gower 1971 — DOI 10.2307/2528823](https://doi.org/10.2307/2528823)
2. [Goodall 1966 — DOI 10.2307/2528080](https://doi.org/10.2307/2528080)
3. [Tversky 1977 — DOI 10.1037/0033-295X.84.4.327](https://doi.org/10.1037/0033-295X.84.4.327)
4. [Spärck Jones 1972 — DOI 10.1108/eb026526](https://doi.org/10.1108/eb026526)
5. [Robertson and Zaragoza 2009 — DOI 10.1561/1500000019](https://doi.org/10.1561/1500000019)
6. [Boriah, Chandola, and Kumar 2008 — SIAM/DOI 10.1137/1.9781611972788.22](https://epubs.siam.org/doi/10.1137/1.9781611972788.22)
7. [Dunning 1993 — ACL Anthology J93-1003](https://aclanthology.org/J93-1003/)
8. [Wilson and Martinez 1997 — JAIR article](https://www.jair.org/index.php/jair/article/view/10182)
9. [Radovanović, Nanopoulos, and Ivanović 2010 — JMLR 11](https://www.jmlr.org/papers/v11/radovanovic10a.html)
10. [Schnitzer, Flexer, Schedl, and Widmer 2012 — JMLR 13](https://www.jmlr.org/papers/v13/schnitzer12a.html)
