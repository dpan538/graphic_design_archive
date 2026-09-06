# Exploration presentation — black-box and metamorphic report (2026-09-06)

Scope: the real page `/trace/exploration` and the real export endpoint `/api/trace/exploration-view/v1/exports/png` on http://localhost:3000; 3 governed states × 16 templates (variant 0) = 48 views, each reloaded five times and exported five times; the S4 variants exported once each. Image metrics over the VIEW pictures (the page's inline SVG rasterised at 420×560, so the forms' furniture does not enter the comparison): SHA-256 (exact), pHash (32×32 DCT, 63 bits, Hamming distance) and SSIM (144×192 grayscale, 8×8 windows). Export PNGs are checked for byte stability, form and dimensions.

**Acceptable visual delta — the hard gates.** Same state, other template: SSIM < 0.9 and pHash distance > 0. Same template, other state: SSIM < 0.65. Same state, other variant: SSIM < 0.85. Golden image: SSIM ≥ 0.99. Anything else is a failure; there is no review class.

## 48 views

| State | Template | Terms | Assoc. | Skeleton | Field | Seed | Fingerprint | PNG | Form | Reloads | Exports | View weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2 | DOTS | 2 | 1 | opposed | radial | 1164986919 | f1bf02ae59f9… | 7a98f34d2e88… | FRANCE 2800×1960 | 5/5 | 5/5 | 22 KB · 243 |
| S2 | SPOTS | 2 | 1 | opposed | radial | 3382456124 | 6a552f8450f5… | 37c744ad50dd… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 7 KB · 50 |
| S2 | CHEVRON | 2 | 1 | opposed | radial | 2637078198 | c2da057a3701… | 187b0418a442… | GERMANY 2800×1800 | 5/5 | 5/5 | 9 KB · 61 |
| S2 | CROSSFIELD | 2 | 1 | opposed | radial | 4134387635 | 5c00aca2ad1d… | 1d1a95a4142d… | CANADA 2400×2080 | 5/5 | 5/5 | 83 KB · 777 |
| S2 | LINES | 2 | 1 | opposed | radial | 2104814842 | e9f2ddd67bb1… | 31c04d396332… | SWEDEN 2200×2900 | 5/5 | 5/5 | 8 KB · 73 |
| S2 | GRID | 2 | 1 | opposed | radial | 2591891511 | 2fe71d64797c… | cdad5323dd23… | GERMANY 2800×1800 | 5/5 | 5/5 | 10 KB · 103 |
| S2 | RAYS | 2 | 1 | opposed | radial | 4214539234 | d7ffa503f353… | 999ce868abf2… | CANADA 2400×2080 | 5/5 | 5/5 | 14 KB · 111 |
| S2 | OVERLAP | 2 | 1 | opposed | radial | 2915777630 | a6be544bff6d… | d3e2366ba3c2… | FRANCE 2800×1960 | 5/5 | 5/5 | 10 KB · 61 |
| S2 | HALFTONE | 2 | 1 | opposed | radial | 2262877858 | 434b04d94a26… | 353eb57bcbd7… | CANADA 2400×2080 | 5/5 | 5/5 | 108 KB · 1363 |
| S2 | STRIPES | 2 | 1 | opposed | radial | 1557247787 | c4805b219c79… | d344da6107ad… | GERMANY 2800×1800 | 5/5 | 5/5 | 16 KB · 116 |
| S2 | PETALS | 2 | 1 | opposed | radial | 1082886598 | 76ee1f81306b… | b4baeaf1bad8… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 7 KB · 41 |
| S2 | WAVES | 2 | 1 | opposed | radial | 1198986603 | 94810c96269b… | b02497886bf9… | SWEDEN 2200×2900 | 5/5 | 5/5 | 9 KB · 25 |
| S2 | CUBES | 2 | 1 | opposed | radial | 744865111 | ca4686238162… | 50427da71385… | GERMANY 2800×1800 | 5/5 | 5/5 | 84 KB · 769 |
| S2 | ARCS | 2 | 1 | opposed | radial | 1619370694 | acfd5591eebc… | c4bad7d4b26b… | FRANCE 2800×1960 | 5/5 | 5/5 | 4 KB · 23 |
| S2 | MOIRE | 2 | 1 | opposed | radial | 815992043 | ee90496b44d1… | b7d43ab2a7aa… | SWEDEN 2200×2900 | 5/5 | 5/5 | 41 KB · 343 |
| S2 | SCATTER | 2 | 1 | opposed | radial | 1709338775 | 47d1382b81ed… | 8493213d3c47… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 12 KB · 98 |
| S3 | DOTS | 3 | 2 | triangle | radial | 3941137009 | 1826025355d4… | 324e9ef5bcc8… | FRANCE 2800×1960 | 5/5 | 5/5 | 23 KB · 248 |
| S3 | SPOTS | 3 | 2 | triangle | radial | 744211134 | 2ba0f046fc97… | 13466330020b… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 7 KB · 53 |
| S3 | CHEVRON | 3 | 2 | triangle | radial | 3238694560 | 77f5c5f8305b… | d068cfd2e69e… | GERMANY 2800×1800 | 5/5 | 5/5 | 17 KB · 137 |
| S3 | CROSSFIELD | 3 | 2 | triangle | radial | 2898094581 | 939da47ee777… | d486c9ed93ae… | CANADA 2400×2080 | 5/5 | 5/5 | 73 KB · 650 |
| S3 | LINES | 3 | 2 | triangle | radial | 1208730936 | daccba8fddba… | 8c3ddbc4a553… | SWEDEN 2200×2900 | 5/5 | 5/5 | 9 KB · 87 |
| S3 | GRID | 3 | 2 | triangle | radial | 1314059401 | ce6b341e8d9c… | 6f52393bfc4d… | GERMANY 2800×1800 | 5/5 | 5/5 | 12 KB · 130 |
| S3 | RAYS | 3 | 2 | triangle | radial | 3589948292 | 8b05480c6fa8… | 7e6106a7b6d9… | CANADA 2400×2080 | 5/5 | 5/5 | 16 KB · 130 |
| S3 | OVERLAP | 3 | 2 | triangle | radial | 2295337800 | 9e29b2b5fec6… | 1e66334a26e9… | FRANCE 2800×1960 | 5/5 | 5/5 | 13 KB · 83 |
| S3 | HALFTONE | 3 | 2 | triangle | radial | 2672180488 | b00065dcb478… | d9e762da3b11… | CANADA 2400×2080 | 5/5 | 5/5 | 63 KB · 778 |
| S3 | STRIPES | 3 | 2 | triangle | radial | 4130072501 | 75a5531ded5d… | a3c25b45bbc2… | GERMANY 2800×1800 | 5/5 | 5/5 | 17 KB · 125 |
| S3 | PETALS | 3 | 2 | triangle | radial | 69258108 | 08333a3519da… | 11918f15fa0f… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 10 KB · 62 |
| S3 | WAVES | 3 | 2 | triangle | radial | 3728745221 | 94997528fe28… | 8780658bc263… | SWEDEN 2200×2900 | 5/5 | 5/5 | 10 KB · 29 |
| S3 | CUBES | 3 | 2 | triangle | radial | 1717187561 | c052826ef675… | c98930d559f3… | GERMANY 2800×1800 | 5/5 | 5/5 | 93 KB · 891 |
| S3 | ARCS | 3 | 2 | triangle | radial | 1565629236 | 7880bf7af061… | 4f8e6ee45571… | FRANCE 2800×1960 | 5/5 | 5/5 | 6 KB · 31 |
| S3 | MOIRE | 3 | 2 | triangle | radial | 916165697 | 6135957a0316… | 6387c1f68f2a… | SWEDEN 2200×2900 | 5/5 | 5/5 | 56 KB · 469 |
| S3 | SCATTER | 3 | 2 | triangle | radial | 3246660089 | 6982efde74fb… | 54901474c95c… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 14 KB · 117 |
| S4 | DOTS | 4 | 3 | clusters | radial | 4115471889 | 40b2cf1ae1e5… | 56ed214cbf89… | FRANCE 2800×1960 | 5/5 | 5/5 | 26 KB · 280 |
| S4 | SPOTS | 4 | 3 | clusters | radial | 2574325150 | 77d7d09dee88… | 15eaa3a93240… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 8 KB · 60 |
| S4 | CHEVRON | 4 | 3 | clusters | radial | 2568530688 | a71f41a3b473… | c61830e4a735… | GERMANY 2800×1800 | 5/5 | 5/5 | 23 KB · 187 |
| S4 | CROSSFIELD | 4 | 3 | clusters | radial | 1998440597 | d07b4b204b43… | 38f6db31ca78… | CANADA 2400×2080 | 5/5 | 5/5 | 102 KB · 925 |
| S4 | LINES | 4 | 3 | clusters | radial | 541317784 | 793240005c43… | c92b83b5d24c… | SWEDEN 2200×2900 | 5/5 | 5/5 | 11 KB · 105 |
| S4 | GRID | 4 | 3 | clusters | radial | 531930921 | 30b9f9c1de5f… | 3947aa483f30… | GERMANY 2800×1800 | 5/5 | 5/5 | 23 KB · 249 |
| S4 | RAYS | 4 | 3 | clusters | radial | 851776548 | bdf0d87b28d9… | 38c2c6fa8ff0… | CANADA 2400×2080 | 5/5 | 5/5 | 16 KB · 128 |
| S4 | OVERLAP | 4 | 3 | clusters | radial | 3025447720 | c0212be2b213… | 475be87a29e3… | FRANCE 2800×1960 | 5/5 | 5/5 | 14 KB · 90 |
| S4 | HALFTONE | 4 | 3 | clusters | radial | 3413715752 | 1cd1864f1b4a… | a00ce62bcbdb… | CANADA 2400×2080 | 5/5 | 5/5 | 83 KB · 1030 |
| S4 | STRIPES | 4 | 3 | clusters | radial | 2528225173 | c8b888622ac0… | 04246698b40b… | GERMANY 2800×1800 | 5/5 | 5/5 | 18 KB · 134 |
| S4 | PETALS | 4 | 3 | clusters | radial | 216419228 | 8e526e3ea13c… | ea5866669aa1… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 11 KB · 67 |
| S4 | WAVES | 4 | 3 | clusters | radial | 231808229 | 20fbbf298289… | 361910f01fb6… | SWEDEN 2200×2900 | 5/5 | 5/5 | 12 KB · 38 |
| S4 | CUBES | 4 | 3 | clusters | radial | 445643593 | 56bbd8e83bd6… | daceb4a00cf0… | GERMANY 2800×1800 | 5/5 | 5/5 | 116 KB · 1052 |
| S4 | ARCS | 4 | 3 | clusters | radial | 3304053716 | b9af80e50e21… | 8a20477f3f8e… | FRANCE 2800×1960 | 5/5 | 5/5 | 8 KB · 41 |
| S4 | MOIRE | 4 | 3 | clusters | radial | 4020616225 | ba242adaac4e… | 366df28d7705… | SWEDEN 2200×2900 | 5/5 | 5/5 | 69 KB · 587 |
| S4 | SCATTER | 4 | 3 | clusters | radial | 3056181337 | fde07070c736… | cd4ddd9aadee… | SOUTH_AFRICA 1800×3600 | 5/5 | 5/5 | 16 KB · 134 |

## Black-box gates

| Test | Status | Detail |
| --- | --- | --- |
| dev_server | PASS | http://localhost:3000 answers |
| reload_stability:S2:DOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:DOTS | PASS | 5 exports → 1 PNG hash(es) 7a98f34d2e88… · TEP1-f5cb417246909ed66ea43ac7 · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S2:SPOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:SPOTS | PASS | 5 exports → 1 PNG hash(es) 37c744ad50dd… · TEP1-a925b666607d81bb6a687b45 · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S2:CHEVRON | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:CHEVRON | PASS | 5 exports → 1 PNG hash(es) 187b0418a442… · TEP1-5f09a2defde161ce4cb2000d · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S2:CROSSFIELD | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:CROSSFIELD | PASS | 5 exports → 1 PNG hash(es) 1d1a95a4142d… · TEP1-53996b9542c188cba2e13867 · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S2:LINES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:LINES | PASS | 5 exports → 1 PNG hash(es) 31c04d396332… · TEP1-6776fac353afe5b633a89f6a · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S2:GRID | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:GRID | PASS | 5 exports → 1 PNG hash(es) cdad5323dd23… · TEP1-674ece426d39b67d972520c0 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S2:RAYS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:RAYS | PASS | 5 exports → 1 PNG hash(es) 999ce868abf2… · TEP1-436b3df30d161aad890210e6 · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S2:OVERLAP | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:OVERLAP | PASS | 5 exports → 1 PNG hash(es) d3e2366ba3c2… · TEP1-b70fa1ac85f513b28fd400d8 · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S2:HALFTONE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:HALFTONE | PASS | 5 exports → 1 PNG hash(es) 353eb57bcbd7… · TEP1-1742d0e54b0cb1c244884f17 · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S2:STRIPES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:STRIPES | PASS | 5 exports → 1 PNG hash(es) d344da6107ad… · TEP1-86dd9ab914d607b93067cdf5 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S2:PETALS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:PETALS | PASS | 5 exports → 1 PNG hash(es) b4baeaf1bad8… · TEP1-5f0c81a8dc67969895caa5eb · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S2:WAVES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:WAVES | PASS | 5 exports → 1 PNG hash(es) b02497886bf9… · TEP1-94a548cb192516ec95ed1ae2 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S2:CUBES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:CUBES | PASS | 5 exports → 1 PNG hash(es) 50427da71385… · TEP1-cd156ebe5a99fafbeefa078f · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S2:ARCS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:ARCS | PASS | 5 exports → 1 PNG hash(es) c4bad7d4b26b… · TEP1-bc034e2adf7ea088c0d47b1b · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S2:MOIRE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:MOIRE | PASS | 5 exports → 1 PNG hash(es) b7d43ab2a7aa… · TEP1-53974c5fa74033612061fce6 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S2:SCATTER | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S2:SCATTER | PASS | 5 exports → 1 PNG hash(es) 8493213d3c47… · TEP1-8bb47cc99ac5c72e399635f6 · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S3:DOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:DOTS | PASS | 5 exports → 1 PNG hash(es) 324e9ef5bcc8… · TEP1-128abe67c7627782b93cfade · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S3:SPOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:SPOTS | PASS | 5 exports → 1 PNG hash(es) 13466330020b… · TEP1-02213a346abe497bb35f124c · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S3:CHEVRON | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:CHEVRON | PASS | 5 exports → 1 PNG hash(es) d068cfd2e69e… · TEP1-f9b7630f5819994676b05f77 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S3:CROSSFIELD | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:CROSSFIELD | PASS | 5 exports → 1 PNG hash(es) d486c9ed93ae… · TEP1-dc654ed9f1d003b73fba3157 · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S3:LINES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:LINES | PASS | 5 exports → 1 PNG hash(es) 8c3ddbc4a553… · TEP1-d721a66724344d3c04bfe1ca · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S3:GRID | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:GRID | PASS | 5 exports → 1 PNG hash(es) 6f52393bfc4d… · TEP1-a21849fd487e4d6ff59c5ba0 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S3:RAYS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:RAYS | PASS | 5 exports → 1 PNG hash(es) 7e6106a7b6d9… · TEP1-f8e087fb07e906c9d0e38b7f · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S3:OVERLAP | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:OVERLAP | PASS | 5 exports → 1 PNG hash(es) 1e66334a26e9… · TEP1-db7389e2cbf95f24689b7cc8 · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S3:HALFTONE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:HALFTONE | PASS | 5 exports → 1 PNG hash(es) d9e762da3b11… · TEP1-9194e014ffe571269ba2ba1b · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S3:STRIPES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:STRIPES | PASS | 5 exports → 1 PNG hash(es) a3c25b45bbc2… · TEP1-862be285e6aef2b48992d971 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S3:PETALS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:PETALS | PASS | 5 exports → 1 PNG hash(es) 11918f15fa0f… · TEP1-e293ab07805d1434e9af4bac · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S3:WAVES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:WAVES | PASS | 5 exports → 1 PNG hash(es) 8780658bc263… · TEP1-2e1459d61070a8807d00b702 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S3:CUBES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:CUBES | PASS | 5 exports → 1 PNG hash(es) c98930d559f3… · TEP1-575d75e13d7b4751aa3f4f40 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S3:ARCS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:ARCS | PASS | 5 exports → 1 PNG hash(es) 4f8e6ee45571… · TEP1-7927b22b4480bfbbf714764e · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S3:MOIRE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:MOIRE | PASS | 5 exports → 1 PNG hash(es) 6387c1f68f2a… · TEP1-1cd50f632a8d02d22a138642 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S3:SCATTER | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S3:SCATTER | PASS | 5 exports → 1 PNG hash(es) 54901474c95c… · TEP1-8cb51451a98c1707da291047 · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S4:DOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:DOTS | PASS | 5 exports → 1 PNG hash(es) 56ed214cbf89… · TEP1-167abfc9c35960e7de36dbde · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S4:SPOTS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:SPOTS | PASS | 5 exports → 1 PNG hash(es) 15eaa3a93240… · TEP1-7c9a12f2187ee88c18350cdc · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S4:CHEVRON | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:CHEVRON | PASS | 5 exports → 1 PNG hash(es) c61830e4a735… · TEP1-537d2453abf7e33b5788725c · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S4:CROSSFIELD | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:CROSSFIELD | PASS | 5 exports → 1 PNG hash(es) 38f6db31ca78… · TEP1-767d28dca8927cfd870afc2c · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S4:LINES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:LINES | PASS | 5 exports → 1 PNG hash(es) c92b83b5d24c… · TEP1-1761d640dc6891fe51e03623 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S4:GRID | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:GRID | PASS | 5 exports → 1 PNG hash(es) 3947aa483f30… · TEP1-66d3a6a388fc74eec3c5a23f · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S4:RAYS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:RAYS | PASS | 5 exports → 1 PNG hash(es) 38c2c6fa8ff0… · TEP1-ba0e60047f40eedda14c54ba · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S4:OVERLAP | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:OVERLAP | PASS | 5 exports → 1 PNG hash(es) 475be87a29e3… · TEP1-4084f780a29e23e12454f064 · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S4:HALFTONE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:HALFTONE | PASS | 5 exports → 1 PNG hash(es) a00ce62bcbdb… · TEP1-1768933b983304be9c7b7455 · CANADA 2400×2080 (2× 1200×1040) |
| reload_stability:S4:STRIPES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:STRIPES | PASS | 5 exports → 1 PNG hash(es) 04246698b40b… · TEP1-89275240d54807b5e2919988 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S4:PETALS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:PETALS | PASS | 5 exports → 1 PNG hash(es) ea5866669aa1… · TEP1-c0716463de8c8832476f0dfe · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| reload_stability:S4:WAVES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:WAVES | PASS | 5 exports → 1 PNG hash(es) 361910f01fb6… · TEP1-db36fb6d2bf3d4b6aa640973 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S4:CUBES | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:CUBES | PASS | 5 exports → 1 PNG hash(es) daceb4a00cf0… · TEP1-62be328ce6f663bc92ffe752 · GERMANY 2800×1800 (2× 1400×900) |
| reload_stability:S4:ARCS | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:ARCS | PASS | 5 exports → 1 PNG hash(es) 8a20477f3f8e… · TEP1-82bd631395733b285101bb21 · FRANCE 2800×1960 (2× 1400×980) |
| reload_stability:S4:MOIRE | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:MOIRE | PASS | 5 exports → 1 PNG hash(es) 366df28d7705… · TEP1-41a1b4a7eebbe072737589e7 · SWEDEN 2200×2900 (2× 1100×1450) |
| reload_stability:S4:SCATTER | PASS | 5 reloads → 1 SVG hash(es); page SVG equals the API's |
| export_stability:S4:SCATTER | PASS | 5 exports → 1 PNG hash(es) cd4ddd9aadee… · TEP1-441d1d88105ef66ac247fb80 · SOUTH_AFRICA 1800×3600 (2× 900×1800) |
| view_weight | PASS | 80 views: ≤ 116 KB and ≤ 1363 primitives each (heaviest HALFTONE/0 on S2); budget 400 KB · 6000 primitives; the grain is one 240 px turbulence tile repeated as a pattern |
| export_stress | PASS | 12 parallel exports of S4/CHEVRON/0 → 4 × 200, 8 × 429 (limiter MAX_IN_FLIGHT 4), 0 other; every 200 byte-identical to the sequential export true; every 429 a REQUEST_LIMIT_EXCEEDED problem true; the next sequential export recovers true |
| cross_template_distinct | PASS | 360 same-state pairs of different templates: SSIM -0.106–0.725, pHash distance 10–50; threshold SSIM < 0.9, pHash > 0 |
| cross_state_distinct | PASS | 48 same-template pairs of different states: SSIM 0.031–0.644, pHash distance 20–40; threshold SSIM < 0.65 |
| variant_distinct | PASS | 48 same-state pairs of different variants: SSIM 0.036–0.626, pHash distance 14–38; threshold SSIM < 0.85 |
| golden_regression | PASS | 48 views at SSIM ≥ 0.99 against their golden image |

## Metamorphic gates

| Test | Status | Detail |
| --- | --- | --- |
| A_same_state_other_template:S2 | PASS | GRID → LINES: research unchanged true, presentation changed true |
| A_same_state_other_template:S3 | PASS | GRID → LINES: research unchanged true, presentation changed true |
| A_same_state_other_template:S4 | PASS | GRID → LINES: research unchanged true, presentation changed true |
| B_same_template_other_state:LINES | PASS | production site (R16A-STATE-E7ABBC992C0DE6BC97715E9F) vs material displacement (R16A-STATE-8CB0E1D4B601A929B8376D17) under LINES/0: same primitive kinds true, fingerprints 8b2000dc6af0… ≠ 2f60fcbe258f… true |
| B_complexity_ladder:LINES | PASS | S2/S3/S4 under LINES/0: S2 e9f2ddd67bb1…, S3 daccba8fddba…, S4 793240005c43… |
| C_complexity_steps | PASS | S2 → More → 3 terms (template kept: true) → Less → 2 terms, back to S2's state and picture true |
| C_richest_refused | PASS | More at S4 → ACTION_NOT_AVAILABLE |
| D_another_view | PASS | 6 steps from S2 (design diplomacy): starting point kept, composition or treatment changed, picture changed each step — 1: HALFTONE/1 fa3938ff3e22… · 2: STRIPES/2 b6ab64360e14… · 3: PETALS/0 40230133adf3… · 4: WAVES/2 3ffc1c83d504… · 5: CUBES/0 a6b969cf7bd2… · 6: ARCS/1 40682d1ee564… |
| E_variants_distinct | PASS | 48 variant pairs on S4: research identical (white-box), every pair below SSIM 0.85 |
| F_form_follows_template | PASS | FRANCE: DOTS, OVERLAP, ARCS · SOUTH_AFRICA: SPOTS, PETALS, SCATTER · GERMANY: CHEVRON, GRID, STRIPES, CUBES · CANADA: CROSSFIELD, RAYS, HALFTONE · SWEDEN: LINES, WAVES, MOIRE |

## Pairwise comparisons (456; cross-template pairs listed only at SSIM ≥ 0.8 or failure — all are in the matrix JSON)

| Kind | State | A | B | Exact duplicate | pHash distance | SSIM | Threshold | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| state | S2~S3 | DOTS@S2 | DOTS@S3 | no | 22 | 0.152 | 0.65 | distinct |
| state | S2~S4 | DOTS@S2 | DOTS@S4 | no | 30 | 0.609 | 0.65 | distinct |
| state | S3~S4 | DOTS@S3 | DOTS@S4 | no | 28 | 0.134 | 0.65 | distinct |
| variant | S4 | DOTS/0 | DOTS/1 | no | 34 | 0.155 | 0.85 | distinct |
| variant | S4 | DOTS/0 | DOTS/2 | no | 22 | 0.133 | 0.85 | distinct |
| variant | S4 | DOTS/1 | DOTS/2 | no | 38 | 0.137 | 0.85 | distinct |
| state | S2~S3 | SPOTS@S2 | SPOTS@S3 | no | 20 | 0.194 | 0.65 | distinct |
| state | S2~S4 | SPOTS@S2 | SPOTS@S4 | no | 34 | 0.182 | 0.65 | distinct |
| state | S3~S4 | SPOTS@S3 | SPOTS@S4 | no | 24 | 0.541 | 0.65 | distinct |
| variant | S4 | SPOTS/0 | SPOTS/1 | no | 32 | 0.082 | 0.85 | distinct |
| variant | S4 | SPOTS/0 | SPOTS/2 | no | 26 | 0.126 | 0.85 | distinct |
| variant | S4 | SPOTS/1 | SPOTS/2 | no | 34 | 0.142 | 0.85 | distinct |
| state | S2~S3 | CHEVRON@S2 | CHEVRON@S3 | no | 32 | 0.289 | 0.65 | distinct |
| state | S2~S4 | CHEVRON@S2 | CHEVRON@S4 | no | 34 | 0.15 | 0.65 | distinct |
| state | S3~S4 | CHEVRON@S3 | CHEVRON@S4 | no | 22 | 0.183 | 0.65 | distinct |
| variant | S4 | CHEVRON/0 | CHEVRON/1 | no | 34 | 0.13 | 0.85 | distinct |
| variant | S4 | CHEVRON/0 | CHEVRON/2 | no | 28 | 0.168 | 0.85 | distinct |
| variant | S4 | CHEVRON/1 | CHEVRON/2 | no | 28 | 0.113 | 0.85 | distinct |
| state | S2~S3 | CROSSFIELD@S2 | CROSSFIELD@S3 | no | 28 | 0.276 | 0.65 | distinct |
| state | S2~S4 | CROSSFIELD@S2 | CROSSFIELD@S4 | no | 34 | 0.232 | 0.65 | distinct |
| state | S3~S4 | CROSSFIELD@S3 | CROSSFIELD@S4 | no | 28 | 0.232 | 0.65 | distinct |
| variant | S4 | CROSSFIELD/0 | CROSSFIELD/1 | no | 36 | 0.194 | 0.85 | distinct |
| variant | S4 | CROSSFIELD/0 | CROSSFIELD/2 | no | 26 | 0.198 | 0.85 | distinct |
| variant | S4 | CROSSFIELD/1 | CROSSFIELD/2 | no | 34 | 0.209 | 0.85 | distinct |
| state | S2~S3 | LINES@S2 | LINES@S3 | no | 34 | 0.1 | 0.65 | distinct |
| state | S2~S4 | LINES@S2 | LINES@S4 | no | 36 | 0.105 | 0.65 | distinct |
| state | S3~S4 | LINES@S3 | LINES@S4 | no | 30 | 0.099 | 0.65 | distinct |
| variant | S4 | LINES/0 | LINES/1 | no | 32 | 0.067 | 0.85 | distinct |
| variant | S4 | LINES/0 | LINES/2 | no | 32 | 0.143 | 0.85 | distinct |
| variant | S4 | LINES/1 | LINES/2 | no | 26 | 0.126 | 0.85 | distinct |
| state | S2~S3 | GRID@S2 | GRID@S3 | no | 38 | 0.031 | 0.65 | distinct |
| state | S2~S4 | GRID@S2 | GRID@S4 | no | 36 | 0.046 | 0.65 | distinct |
| state | S3~S4 | GRID@S3 | GRID@S4 | no | 32 | 0.049 | 0.65 | distinct |
| variant | S4 | GRID/0 | GRID/1 | no | 30 | 0.037 | 0.85 | distinct |
| variant | S4 | GRID/0 | GRID/2 | no | 34 | 0.036 | 0.85 | distinct |
| variant | S4 | GRID/1 | GRID/2 | no | 34 | 0.038 | 0.85 | distinct |
| state | S2~S3 | RAYS@S2 | RAYS@S3 | no | 28 | 0.319 | 0.65 | distinct |
| state | S2~S4 | RAYS@S2 | RAYS@S4 | no | 36 | 0.305 | 0.65 | distinct |
| state | S3~S4 | RAYS@S3 | RAYS@S4 | no | 30 | 0.225 | 0.65 | distinct |
| variant | S4 | RAYS/0 | RAYS/1 | no | 28 | 0.184 | 0.85 | distinct |
| variant | S4 | RAYS/0 | RAYS/2 | no | 28 | 0.235 | 0.85 | distinct |
| variant | S4 | RAYS/1 | RAYS/2 | no | 26 | 0.196 | 0.85 | distinct |
| state | S2~S3 | OVERLAP@S2 | OVERLAP@S3 | no | 22 | 0.644 | 0.65 | distinct |
| state | S2~S4 | OVERLAP@S2 | OVERLAP@S4 | no | 40 | 0.609 | 0.65 | distinct |
| state | S3~S4 | OVERLAP@S3 | OVERLAP@S4 | no | 32 | 0.584 | 0.65 | distinct |
| variant | S4 | OVERLAP/0 | OVERLAP/1 | no | 32 | 0.486 | 0.85 | distinct |
| variant | S4 | OVERLAP/0 | OVERLAP/2 | no | 22 | 0.586 | 0.85 | distinct |
| variant | S4 | OVERLAP/1 | OVERLAP/2 | no | 28 | 0.471 | 0.85 | distinct |
| state | S2~S3 | HALFTONE@S2 | HALFTONE@S3 | no | 26 | 0.342 | 0.65 | distinct |
| state | S2~S4 | HALFTONE@S2 | HALFTONE@S4 | no | 34 | 0.272 | 0.65 | distinct |
| state | S3~S4 | HALFTONE@S3 | HALFTONE@S4 | no | 24 | 0.313 | 0.65 | distinct |
| variant | S4 | HALFTONE/0 | HALFTONE/1 | no | 26 | 0.192 | 0.85 | distinct |
| variant | S4 | HALFTONE/0 | HALFTONE/2 | no | 22 | 0.3 | 0.85 | distinct |
| variant | S4 | HALFTONE/1 | HALFTONE/2 | no | 26 | 0.169 | 0.85 | distinct |
| state | S2~S3 | STRIPES@S2 | STRIPES@S3 | no | 28 | 0.224 | 0.65 | distinct |
| state | S2~S4 | STRIPES@S2 | STRIPES@S4 | no | 26 | 0.233 | 0.65 | distinct |
| state | S3~S4 | STRIPES@S3 | STRIPES@S4 | no | 20 | 0.32 | 0.65 | distinct |
| variant | S4 | STRIPES/0 | STRIPES/1 | no | 36 | 0.079 | 0.85 | distinct |
| variant | S4 | STRIPES/0 | STRIPES/2 | no | 24 | 0.105 | 0.85 | distinct |
| variant | S4 | STRIPES/1 | STRIPES/2 | no | 30 | 0.078 | 0.85 | distinct |
| state | S2~S3 | PETALS@S2 | PETALS@S3 | no | 28 | 0.626 | 0.65 | distinct |
| state | S2~S4 | PETALS@S2 | PETALS@S4 | no | 26 | 0.611 | 0.65 | distinct |
| state | S3~S4 | PETALS@S3 | PETALS@S4 | no | 30 | 0.621 | 0.65 | distinct |
| variant | S4 | PETALS/0 | PETALS/1 | no | 26 | 0.476 | 0.85 | distinct |
| variant | S4 | PETALS/0 | PETALS/2 | no | 32 | 0.588 | 0.85 | distinct |
| variant | S4 | PETALS/1 | PETALS/2 | no | 28 | 0.436 | 0.85 | distinct |
| state | S2~S3 | WAVES@S2 | WAVES@S3 | no | 22 | 0.549 | 0.65 | distinct |
| state | S2~S4 | WAVES@S2 | WAVES@S4 | no | 34 | 0.532 | 0.65 | distinct |
| state | S3~S4 | WAVES@S3 | WAVES@S4 | no | 34 | 0.513 | 0.65 | distinct |
| variant | S4 | WAVES/0 | WAVES/1 | no | 28 | 0.359 | 0.85 | distinct |
| variant | S4 | WAVES/0 | WAVES/2 | no | 22 | 0.438 | 0.85 | distinct |
| variant | S4 | WAVES/1 | WAVES/2 | no | 30 | 0.351 | 0.85 | distinct |
| state | S2~S3 | CUBES@S2 | CUBES@S3 | no | 40 | 0.069 | 0.65 | distinct |
| state | S2~S4 | CUBES@S2 | CUBES@S4 | no | 36 | 0.102 | 0.65 | distinct |
| state | S3~S4 | CUBES@S3 | CUBES@S4 | no | 26 | 0.078 | 0.65 | distinct |
| variant | S4 | CUBES/0 | CUBES/1 | no | 32 | 0.069 | 0.85 | distinct |
| variant | S4 | CUBES/0 | CUBES/2 | no | 14 | 0.626 | 0.85 | distinct |
| variant | S4 | CUBES/1 | CUBES/2 | no | 32 | 0.088 | 0.85 | distinct |
| state | S2~S3 | ARCS@S2 | ARCS@S3 | no | 28 | 0.581 | 0.65 | distinct |
| state | S2~S4 | ARCS@S2 | ARCS@S4 | no | 30 | 0.511 | 0.65 | distinct |
| state | S3~S4 | ARCS@S3 | ARCS@S4 | no | 30 | 0.539 | 0.65 | distinct |
| variant | S4 | ARCS/0 | ARCS/1 | no | 34 | 0.278 | 0.85 | distinct |
| variant | S4 | ARCS/0 | ARCS/2 | no | 34 | 0.325 | 0.85 | distinct |
| variant | S4 | ARCS/1 | ARCS/2 | no | 30 | 0.19 | 0.85 | distinct |
| state | S2~S3 | MOIRE@S2 | MOIRE@S3 | no | 30 | 0.282 | 0.65 | distinct |
| state | S2~S4 | MOIRE@S2 | MOIRE@S4 | no | 20 | 0.272 | 0.65 | distinct |
| state | S3~S4 | MOIRE@S3 | MOIRE@S4 | no | 34 | 0.275 | 0.65 | distinct |
| variant | S4 | MOIRE/0 | MOIRE/1 | no | 32 | 0.183 | 0.85 | distinct |
| variant | S4 | MOIRE/0 | MOIRE/2 | no | 30 | 0.272 | 0.85 | distinct |
| variant | S4 | MOIRE/1 | MOIRE/2 | no | 38 | 0.145 | 0.85 | distinct |
| state | S2~S3 | SCATTER@S2 | SCATTER@S3 | no | 34 | 0.606 | 0.65 | distinct |
| state | S2~S4 | SCATTER@S2 | SCATTER@S4 | no | 28 | 0.585 | 0.65 | distinct |
| state | S3~S4 | SCATTER@S3 | SCATTER@S4 | no | 32 | 0.565 | 0.65 | distinct |
| variant | S4 | SCATTER/0 | SCATTER/1 | no | 26 | 0.477 | 0.85 | distinct |
| variant | S4 | SCATTER/0 | SCATTER/2 | no | 32 | 0.507 | 0.85 | distinct |
| variant | S4 | SCATTER/1 | SCATTER/2 | no | 32 | 0.434 | 0.85 | distinct |

## Golden images (48)

| View | File | SSIM | Status |
| --- | --- | --- | --- |
| S2:DOTS:0 | golden/S2-DOTS-0.png | 1 | MATCH |
| S2:SPOTS:0 | golden/S2-SPOTS-0.png | 1 | MATCH |
| S2:CHEVRON:0 | golden/S2-CHEVRON-0.png | 1 | MATCH |
| S2:CROSSFIELD:0 | golden/S2-CROSSFIELD-0.png | 1 | MATCH |
| S2:LINES:0 | golden/S2-LINES-0.png | 1 | MATCH |
| S2:GRID:0 | golden/S2-GRID-0.png | 1 | MATCH |
| S2:RAYS:0 | golden/S2-RAYS-0.png | 1 | MATCH |
| S2:OVERLAP:0 | golden/S2-OVERLAP-0.png | 1 | MATCH |
| S2:HALFTONE:0 | golden/S2-HALFTONE-0.png | 1 | MATCH |
| S2:STRIPES:0 | golden/S2-STRIPES-0.png | 1 | MATCH |
| S2:PETALS:0 | golden/S2-PETALS-0.png | 1 | MATCH |
| S2:WAVES:0 | golden/S2-WAVES-0.png | 1 | MATCH |
| S2:CUBES:0 | golden/S2-CUBES-0.png | 1 | MATCH |
| S2:ARCS:0 | golden/S2-ARCS-0.png | 1 | MATCH |
| S2:MOIRE:0 | golden/S2-MOIRE-0.png | 1 | MATCH |
| S2:SCATTER:0 | golden/S2-SCATTER-0.png | 1 | MATCH |
| S3:DOTS:0 | golden/S3-DOTS-0.png | 1 | MATCH |
| S3:SPOTS:0 | golden/S3-SPOTS-0.png | 1 | MATCH |
| S3:CHEVRON:0 | golden/S3-CHEVRON-0.png | 1 | MATCH |
| S3:CROSSFIELD:0 | golden/S3-CROSSFIELD-0.png | 1 | MATCH |
| S3:LINES:0 | golden/S3-LINES-0.png | 1 | MATCH |
| S3:GRID:0 | golden/S3-GRID-0.png | 1 | MATCH |
| S3:RAYS:0 | golden/S3-RAYS-0.png | 1 | MATCH |
| S3:OVERLAP:0 | golden/S3-OVERLAP-0.png | 1 | MATCH |
| S3:HALFTONE:0 | golden/S3-HALFTONE-0.png | 1 | MATCH |
| S3:STRIPES:0 | golden/S3-STRIPES-0.png | 1 | MATCH |
| S3:PETALS:0 | golden/S3-PETALS-0.png | 1 | MATCH |
| S3:WAVES:0 | golden/S3-WAVES-0.png | 1 | MATCH |
| S3:CUBES:0 | golden/S3-CUBES-0.png | 1 | MATCH |
| S3:ARCS:0 | golden/S3-ARCS-0.png | 1 | MATCH |
| S3:MOIRE:0 | golden/S3-MOIRE-0.png | 1 | MATCH |
| S3:SCATTER:0 | golden/S3-SCATTER-0.png | 1 | MATCH |
| S4:DOTS:0 | golden/S4-DOTS-0.png | 1 | MATCH |
| S4:SPOTS:0 | golden/S4-SPOTS-0.png | 1 | MATCH |
| S4:CHEVRON:0 | golden/S4-CHEVRON-0.png | 1 | MATCH |
| S4:CROSSFIELD:0 | golden/S4-CROSSFIELD-0.png | 1 | MATCH |
| S4:LINES:0 | golden/S4-LINES-0.png | 1 | MATCH |
| S4:GRID:0 | golden/S4-GRID-0.png | 1 | MATCH |
| S4:RAYS:0 | golden/S4-RAYS-0.png | 1 | MATCH |
| S4:OVERLAP:0 | golden/S4-OVERLAP-0.png | 1 | MATCH |
| S4:HALFTONE:0 | golden/S4-HALFTONE-0.png | 1 | MATCH |
| S4:STRIPES:0 | golden/S4-STRIPES-0.png | 1 | MATCH |
| S4:PETALS:0 | golden/S4-PETALS-0.png | 1 | MATCH |
| S4:WAVES:0 | golden/S4-WAVES-0.png | 1 | MATCH |
| S4:CUBES:0 | golden/S4-CUBES-0.png | 1 | MATCH |
| S4:ARCS:0 | golden/S4-ARCS-0.png | 1 | MATCH |
| S4:MOIRE:0 | golden/S4-MOIRE-0.png | 1 | MATCH |
| S4:SCATTER:0 | golden/S4-SCATTER-0.png | 1 | MATCH |

Contact sheets: `exploration-48-view-contact-sheet.png` (rows = templates, columns = S2 / S3 / S4; the view pictures), `exploration-export-forms-sheet.png` (the five export forms on S4). Machine-readable: `visual-generation-matrix.json` (with `layout_seed_used`, `skeleton_family`, `semantic_field`, `term_anchors` per entry).

Result: PASS — 113/113 gates.
