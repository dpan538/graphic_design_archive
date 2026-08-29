# Repository hygiene gate

```json
{
  "format": "gda-v49-repository-hygiene/v1",
  "status": "PASS",
  "trackedFileCount": 6962,
  "checks": {
    "activeDatabaseRootCount": 1,
    "activeDatabaseRoot": "database",
    "legacyDbRootPresent": false,
    "trackedRuntimeFiles": [],
    "activeRawCaptureDirectories": [],
    "activeBackupDirectories": [],
    "preV49Generated": [],
    "unconsumedGenerated": [],
    "unmanifestedReleaseInputs": [],
    "brokenDocumentationLinks": [],
    "brokenScriptReferences": [],
    "brokenFrontendImports": [],
    "activeScriptAllowlistPass": true,
    "activeScriptAllowlistDeclaredCount": 311,
    "activeScriptAllowlistRowCount": 311,
    "activeScriptAllowlistTrackedCount": 311,
    "activeScriptAllowlistMissingScripts": [],
    "activeScriptAllowlistUnexpectedScripts": [],
    "activeScriptAllowlistDuplicatePathCount": 0,
    "unreferencedActiveScriptPolicy": "DOCUMENTED_ALLOWLIST",
    "historicalPromptActiveCount": 0,
    "unreferencedProjectAssetCount": 0,
    "brokenLfsPointerCount": 0,
    "lfsFsckOutput": "Git LFS fsck OK",
    "unmanifestedLargeFiles": [],
    "largeFileManifest": [
      {
        "path": "data/prefreeze_candidate_v48.sqlite",
        "byteSize": 421801984,
        "sha256": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
        "category": "release_input"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-functional-http-case-ledger-v2.tsv",
        "byteSize": 162498021,
        "sha256": "dad0a42f8a3efd11fec8fad45de517eb5f641d6795d136e4f4ec5e8c1af70aaa",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-functional-validation-v2.json",
        "byteSize": 78575302,
        "sha256": "1c61513c2d2dbb75dc280fab2a9171f3b44106d6b4379dcefad0dc4db1c06a3f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-v2-service-dto-case-ledger.tsv",
        "byteSize": 109706355,
        "sha256": "6cca40d5ea5d0b7baa4014b1445481cbd85d0723ef3776be96635140f274cfd9",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-v2-transition-case-ledger.tsv",
        "byteSize": 195678263,
        "sha256": "3e7651a372d53b671042c685ce17be34277023d72b878c1fa2e5d99a6337c6c2",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification-cases-v2.tsv",
        "byteSize": 186160119,
        "sha256": "f30a639b70a226a0d38ed60bce40597f286f00b057dd848ddb03b7b7e1dfceaa",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification.json",
        "byteSize": 182907607,
        "sha256": "794a16071edc9efce13c17de56c6b901aac86feb1dd5091fb490e1f20febf35f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv",
        "byteSize": 284522777,
        "sha256": "3a58b52f3c95fbc33ad992481ff55485b9a566418adc15daa1a39f86e9dd96a0",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/json-c1-warm-run2.json",
        "byteSize": 18931343,
        "sha256": "0ff0653ece2d600b0f88f25a6c4ecf186107a6b29162be2edfb54cd68ffd4612",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/mixed-c25-stabilization-run2.json",
        "byteSize": 46486621,
        "sha256": "bc956f72e1ffc0fe86025b2e8b4bc59e086600524341d334c23e3726a7caf864",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/mixed-c25-sustained-run2.json",
        "byteSize": 46348011,
        "sha256": "49264b0672c3e0ec03e3c156dfb2413d7a5ccfafc70fbac4de13c468e901adbd",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2/json-c1-warm.json",
        "byteSize": 19301266,
        "sha256": "15d51ebf4a0cd6945102a3b5a9d7d5e49f50cc9507c21f5c647131abd37b8931",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2/mixed-c25-sustained.json",
        "byteSize": 46331756,
        "sha256": "dac188ce06cab681b9c7be2617439a161967551c123d08a33c0226c58c20968a",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-00-03-v1.tsv",
        "byteSize": 11871944,
        "sha256": "e89f02e82714715a4c416cb7effd9c47d7b27fdcece33d029a37e0fb8c3497e2",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-04-07-v1.tsv",
        "byteSize": 11729632,
        "sha256": "20d55e69dc0a1b0d7fa7db8676e5ecae15b745ef58692ef15ecf352ce4b3e87f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-08-0b-v1.tsv",
        "byteSize": 11802106,
        "sha256": "ac59944f11e8d58cd84a5db238792e716cd7f59635d74b3bd7db661314827a83",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-0c-0f-v1.tsv",
        "byteSize": 11686063,
        "sha256": "212ab8d150d9820b1fd34db7417e04f50b575c3da775c3707208436803beb52e",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-10-13-v1.tsv",
        "byteSize": 11764254,
        "sha256": "9787f22b755949d12b9e69c12fe2b0940da2d775604a39eb4763902b0cb8d01d",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-14-17-v1.tsv",
        "byteSize": 11797039,
        "sha256": "e80ebf3a948f64b8c963c77ed52337a590c33abd4e7e3fbd42571a19c1614869",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-18-1b-v1.tsv",
        "byteSize": 11781104,
        "sha256": "323d2ffb37445e62f8b213cba3754a6232cb696869b1de89c855b1e576373912",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-1c-1f-v1.tsv",
        "byteSize": 12005125,
        "sha256": "f23384617896ef855785ac5877218ad0fadf513d36b81ab79aede7d6ab0d3796",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-20-23-v1.tsv",
        "byteSize": 11812669,
        "sha256": "964ea93bd65ce736e56da1dec1b4e438d150c31a667b1bf89d9c1441dc627b4e",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-24-27-v1.tsv",
        "byteSize": 11756936,
        "sha256": "ef0c49c959109144e70ae30decc7fb86bdd8564cc8e2be75b89d83893a5fcbf7",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-28-2b-v1.tsv",
        "byteSize": 11683960,
        "sha256": "5692c9932395c074ca44a3bd3ec683dbb25f8b60ee6292c8f0efb9b199f4efe6",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-2c-2f-v1.tsv",
        "byteSize": 11705796,
        "sha256": "352cd8b63756f1731a4a0a1076d7dd5267a7228cdeaaab4a98e4dbd1622ffa27",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-30-33-v1.tsv",
        "byteSize": 11814909,
        "sha256": "3352974ee14c8e234a370b69680c46f7f1d60de36b1d939967f0f3657e8ccfbe",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-34-37-v1.tsv",
        "byteSize": 11645361,
        "sha256": "5a7aa9e2259e45949a70d53e72f6a52e137741375d4cd7b09c5cc1f477f020db",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-38-3b-v1.tsv",
        "byteSize": 11532014,
        "sha256": "af466dc04c13339b872d22e5f42fc6e2d12ab628aa2cff7ea5f94bb2ed312de8",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-3c-3f-v1.tsv",
        "byteSize": 11830905,
        "sha256": "6a934b22efd0e27c17e507d614ad8946009ff70e12d6ea4ec5a3850b64db62ed",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-40-43-v1.tsv",
        "byteSize": 11975739,
        "sha256": "a3bf8b03c6dd2d25c7f1c01f0093013aba9ee16cc276bd4c7aa3321041ccf2ac",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-44-47-v1.tsv",
        "byteSize": 11827213,
        "sha256": "1856b5f8d4e0684318e3e2e9868021ee41c71518416ed64b002d54c9d8054b3b",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-48-4b-v1.tsv",
        "byteSize": 11879783,
        "sha256": "bf8afa2db2b78d34ae462c8ae731dde92c55d2ca7dbb12990b3116acd3f2ed3c",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-4c-4f-v1.tsv",
        "byteSize": 11596040,
        "sha256": "09d2bf06a6fe40b52fcfb4df9eff86879995d2b055852c50386240cc76d5b2a8",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-50-53-v1.tsv",
        "byteSize": 11807458,
        "sha256": "db5f5ddcc0282ff3a41dfeb41ed19402463768f9af35d281f31327b37f97efdc",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-54-57-v1.tsv",
        "byteSize": 11851332,
        "sha256": "38fd58e12d5ca296dd6517d2f4995caa4182d33ba447799dd8adb4a28d0e42a1",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-58-5b-v1.tsv",
        "byteSize": 11665786,
        "sha256": "06a28c63daafc6b81e5cedb175d98fb2d406c4d90b71787a6de230fce6b7d9dd",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-5c-5f-v1.tsv",
        "byteSize": 11952984,
        "sha256": "c1896e4d6b2dd1f42714d8fbb559770be8bb5f97e2b5c105886f41a724daf7b6",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-60-63-v1.tsv",
        "byteSize": 11941818,
        "sha256": "fd5a086044479da43616a3c6d01c8456ebfffee412e964f536339238680226ce",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-64-67-v1.tsv",
        "byteSize": 11861381,
        "sha256": "13a8d47be4eb54a7bb1160525be84d4bb19261a9139e91bedb8f777e682cb649",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-68-6b-v1.tsv",
        "byteSize": 11783982,
        "sha256": "50d5448eed5e6a5bde6060967949374e481078929a05bb78b90aa6a59bc6baf3",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-6c-6f-v1.tsv",
        "byteSize": 11585036,
        "sha256": "947f6a9ce5d160533f4e419c31ade6e4e941d19b2a1c327e0ce5c2cf302e008f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-70-73-v1.tsv",
        "byteSize": 11701034,
        "sha256": "e7ea83d15f310f416642846b379418a5a305f6f565faa9baed29fc12b9607a00",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-74-77-v1.tsv",
        "byteSize": 11817710,
        "sha256": "6bb205c5e2c75f8b0e90796aaee83340efc49776a7677ad0147c457b3dc9c56b",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-78-7b-v1.tsv",
        "byteSize": 11767047,
        "sha256": "de7d597bd4213810293bb4427a29bfbf952daf5a595550e53ac25625c818fc75",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-7c-7f-v1.tsv",
        "byteSize": 11743158,
        "sha256": "d3cdb86ba3fc4fadcc68b216201bfbde902f2d009b876ebf2fa74d4497119884",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-80-83-v1.tsv",
        "byteSize": 11849131,
        "sha256": "4b6c119adb50a2c77291414e30dc3aba919ee128b3be5f9899a73f2f907edfa5",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-84-87-v1.tsv",
        "byteSize": 11960968,
        "sha256": "ded3b69297b3108bf64da960775b0cb9092a21ce0be693cfbae9987e5c3e8e9d",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-88-8b-v1.tsv",
        "byteSize": 11729623,
        "sha256": "358e06298019391ec1ca5719209ed1621229367d68a3719e9429e35193668870",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-8c-8f-v1.tsv",
        "byteSize": 11815719,
        "sha256": "7ac814ac8c18fd606e94bfded77678ac5c9d45d67c87298892d4d7dcca609d7e",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-90-93-v1.tsv",
        "byteSize": 11643758,
        "sha256": "d2ef2f28131b92b3e24006e62c3622bd60895ac5295846a0086c7cddd061ae03",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-94-97-v1.tsv",
        "byteSize": 11686428,
        "sha256": "c06b167ebb1a9152e4d747980881ac78ce065f3f4764ab8a4bd57634813f5309",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-98-9b-v1.tsv",
        "byteSize": 11558251,
        "sha256": "cc871b58a50d527d7a60b3960e24d10246bb593e24d23a7544d8f8d8cedc720e",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-9c-9f-v1.tsv",
        "byteSize": 11519001,
        "sha256": "fb8c704d471e47fd5bd6258ee895b20c958f739c2288e766129d2d040cb93898",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-a0-a3-v1.tsv",
        "byteSize": 11828360,
        "sha256": "b892c9b66f574dba0c9b379941afa0ac82dd36c363caef0fdf83b9abb5183a31",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-a4-a7-v1.tsv",
        "byteSize": 11676881,
        "sha256": "cf628f8fb8b60f53e6bbc1d1d15d25828ddfb95ea893a28c401eb18814b5c4c3",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-a8-ab-v1.tsv",
        "byteSize": 11809487,
        "sha256": "edbf708d240cc825011a78e0c05bc84fd8df5a935e6a2eb12ed37d9ce64c93c8",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-ac-af-v1.tsv",
        "byteSize": 11948206,
        "sha256": "d6a3f3b395b035e3ed55a6562c89aa8e86570e009a73a1be824d93e779a1fde3",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-b0-b3-v1.tsv",
        "byteSize": 11850158,
        "sha256": "abb7cc84d61d9e726ff5248756086071f049e986a31d079be4133b80422cbc51",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-b4-b7-v1.tsv",
        "byteSize": 11903788,
        "sha256": "e532a9e12e58e8ef869cd9e7554133e4fa19849e80952f4897d4e3963cb59b9d",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-b8-bb-v1.tsv",
        "byteSize": 11730398,
        "sha256": "7b252cc88d94143dc0eb3db2702b502b41cde2fbd0950a6262d312d0e3aa5362",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-bc-bf-v1.tsv",
        "byteSize": 11698810,
        "sha256": "2d11df7f6b42559ae7339d23d89d3fc1c028eeed0a8e58b33c2b53d21059c31b",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-c0-c3-v1.tsv",
        "byteSize": 11906463,
        "sha256": "ce2589611e618321be45f3fb6810632f53e6a481ff2708e35d7697d3e6aa11dc",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-c4-c7-v1.tsv",
        "byteSize": 11916644,
        "sha256": "684f56067fd0cfb152a7b64c6869bc02913fe9bf7096ee7b55459eb2d1299d6f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-c8-cb-v1.tsv",
        "byteSize": 11849657,
        "sha256": "e2278da0dc1368e348360dfda9cca2452f41b7d63b11e86c82b1196230cd68de",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-cc-cf-v1.tsv",
        "byteSize": 11761180,
        "sha256": "2e8562c07c109983c907bafe7501b7b36ddcf73df52b44c905ac7ffb3462e696",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-d0-d3-v1.tsv",
        "byteSize": 11808122,
        "sha256": "981730498353e2c3799a03f34c35bc778f236dfee5ff61be15b8fd794d1de3d8",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-d4-d7-v1.tsv",
        "byteSize": 11824037,
        "sha256": "dfa86148054883f0211230eec62ca719ad57989758300471e69c0b8f6407e300",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-d8-db-v1.tsv",
        "byteSize": 11658880,
        "sha256": "db580c7f38f6222f7cf8f2a50f7f2734835b57a9f571810388f242507ad779a1",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-dc-df-v1.tsv",
        "byteSize": 11741101,
        "sha256": "b2a292b1dd974fc8284a229e7a9c2e1247a8b3a4382f52972cdd8e321ba29073",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-e0-e3-v1.tsv",
        "byteSize": 11630991,
        "sha256": "1148df28805c70357048e9c3464efe56065e4799e47a9a2d74e1558421990962",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-e4-e7-v1.tsv",
        "byteSize": 11875259,
        "sha256": "19fbbb78d2308ed4dff7be0f8f0f86e67318a3930ecf9840e1501731199d6056",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-e8-eb-v1.tsv",
        "byteSize": 11907569,
        "sha256": "94f0fbc6edbd41ef0fff68ba2462ef63c33d308ed3fbda7c6e652000c7d05141",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-ec-ef-v1.tsv",
        "byteSize": 11902719,
        "sha256": "1ce61573171cf597a181787d4eb970cd682a9b605d04301b1c50ab7b29d2a631",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-f0-f3-v1.tsv",
        "byteSize": 11660013,
        "sha256": "cd85c6161fcd7b1398a40806cadc521a86051c429a3585873c5ce9f457e4ff26",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-f4-f7-v1.tsv",
        "byteSize": 11677358,
        "sha256": "14aa5b66b780bbfca56bfd68e608a47dfd793c852c2da512fe367f4cf9721464",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-f8-fb-v1.tsv",
        "byteSize": 11867845,
        "sha256": "e0fe8fc7dd9b6178d6d815c80d861842ad8d92fa696f3b19b8a619de142a5fe8",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/round16a-transition-reconciliation-v1/round16a-transition-reconciliation-fc-ff-v1.tsv",
        "byteSize": 11892337,
        "sha256": "38f97cd48226dcff98353b34fabc7ed68744c1ad5f2ececb595a4719019cdaf2",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/prior-object-reconciliation-universe-v1-exports.tsv",
        "byteSize": 11541976,
        "sha256": "d0e7ee1eb8c44b74ec50246509f686e023d5b3bc7f38aa479b8e199521d4b836",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/prior-object-reconciliation-universe-v1-states.tsv",
        "byteSize": 12307984,
        "sha256": "fab7057bb7c59feeb91a09d08fee55dd843cf2059dac683f89760a8a64354c87",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/round16a-global-reconciliation-exports-v1.tsv",
        "byteSize": 14913499,
        "sha256": "4d34a51002bf5c86f75ea63d80fe4352109ba9e2807fd597693efb2b6b24a6cf",
        "category": "final_audit_evidence"
      },
      {
        "path": "frontend/generated/trace-context-v1/records.json",
        "byteSize": 13109622,
        "sha256": "c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7",
        "category": "current_frontend_runtime"
      },
      {
        "path": "frontend/public/data/public_surface_mock_v0.json",
        "byteSize": 90895254,
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "category": "current_frontend_runtime"
      },
      {
        "path": "frontend/src/data/public_surface_mock_v0.json",
        "byteSize": 90895254,
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "category": "current_frontend_runtime"
      },
      {
        "path": "generated/public_surfaces_prefreeze_candidate_v48.json",
        "byteSize": 190067852,
        "sha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
        "category": "release_input"
      }
    ],
    "duplicateLargeBlobViolations": [],
    "duplicateLargeBlobAllowlist": [
      {
        "sha256": "92335ba0c49e28b644374841fb5e1d0d72f8f49cbbcd4a7ab5d38bcd893329f0",
        "byteSize": 3272608,
        "paths": [
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/fresh-b-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "7815d5eb9bc666375bd1fe9c91b488f7e3f879f51a51970f767a8a8a6908d8de",
        "byteSize": 1749122,
        "paths": [
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/quarantined-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "01ac7dbf498e38f38eb1d8fbba6188722f7f56f390e38c04f00b1a183e0974b8",
        "byteSize": 3240896,
        "paths": [
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/fresh-b-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "byteSize": 90895254,
        "paths": [
          "frontend/public/data/public_surface_mock_v0.json",
          "frontend/src/data/public_surface_mock_v0.json"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      }
    ],
    "secretPatternMatches": [],
    "projectLogBytes": 36600,
    "projectLogPolicyPass": true,
    "readmeV49ArchitecturePass": true,
    "releaseManifestPass": true,
    "auditIndexPass": true,
    "databaseFreezePass": true,
    "databaseFreezeOutput": "{\"databaseVersion\": 50, \"frozenFileCount\": 126, \"frozenPathDriftCount\": 0, \"manifestSha256\": \"f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e\", \"mode\": \"verify\", \"status\": \"PASS\", \"unmanifestedV49DatabaseFileCount\": 8}",
    "sourceTagCommit": "d78f496bcdf2cd6941791986007cd7a885c4c532",
    "sourceTagResolvable": true
  },
  "violations": []
}
```
