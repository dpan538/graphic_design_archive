# Authoritative external reference register

Only technical primary/authoritative sources were used. Visual reference images supplied for product direction were not treated as technical authority.

| Authority | URL | Facts consulted | Decision supported |
| --- | --- | --- | --- |
| D3 geo API | https://d3js.org/d3-geo | GeoJSON projection/streaming and spherical geography primitives | Use D3 functions for governed geometry rather than hand-authored paths |
| D3 geo paths | https://d3js.org/d3-geo/path | `geoPath` projects/serializes geographic objects and provides bounds/centroids | Function-derived SVG path and geometry metrics |
| D3 projections | https://d3js.org/d3-geo/projection | Projection fitting/configuration behavior | Versioned `fitProjection` contract |
| D3 cylindrical projections | https://d3js.org/d3-geo/cylindrical | Equal Earth is equal-area; Natural Earth 1 is neither conformal nor equal-area | Equal Earth default, Natural Earth 1 alternative |
| Natural Earth 50m cultural vectors | https://www.naturalearthdata.com/downloads/50m-cultural-vectors/ | Admin-0 countries and tiny-country/map-unit companion themes; 5.1.1 theme baseline | 50m candidate and tiny-geography investigation |
| Natural Earth 110m cultural vectors | https://www.naturalearthdata.com/downloads/110m-cultural-vectors/ | 110m cultural baseline | Scale benchmark |
| Natural Earth Admin 0 Countries | https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/ | Admin-0 Countries theme version 5.1.1 and de facto boundary convention | Pinned geometry identity and disclosure |
| Natural Earth terms | https://www.naturalearthdata.com/about/terms-of-use/ | Natural Earth data are public domain | Asset license statement |
| Natural Earth vector release 5.1.1 | https://github.com/nvkelso/natural-earth-vector/releases/tag/v5.1.1 | Versioned source release used for the exact raw geometry URL | Release pin and source SHA |
| World Atlas README | https://github.com/topojson/world-atlas/blob/master/README.md | Package redistributes Natural Earth-derived TopoJSON; current package source describes Natural Earth 4.1.0 | Legacy/reference comparison |
| World Atlas 2.0.2 release | https://github.com/topojson/world-atlas/releases/tag/v2.0.2 | Installed dependency release identity | Dependency benchmark pin |
| Textures.js repository | https://github.com/riccardoscalco/textures | SVG pattern API, MIT license, source/package version 1.2.3 | Isolated texture experiment and rejection rationale |

The committed geometry manifest records the exact raw source URL and source/output SHA-256 values. No runtime request is made to any external reference.
