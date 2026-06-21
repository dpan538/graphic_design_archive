# Research Packet Structure Requirements v1

Scope: non-mutating audit for cover/normal main/sub/text/appendix/card packet requirements.

This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.

## Summary

- scope: non_mutating_research_packet_structure_requirements (No rebuild, role override, image download, or rights/image-state change.)
- packet_requirement_rows: 2088 (Cluster-level packet structure requirements.)
- reading_note_requirement_rows: 2088 (Curated reading-note requirement rows.)
- packet_scale:single_or_micro: 886 (Packet scale distribution.)
- packet_scale:small: 766 (Packet scale distribution.)
- packet_scale:medium: 245 (Packet scale distribution.)
- packet_scale:large: 191 (Packet scale distribution.)
- cover_main:cover_main_optional: 825 (Cover main requirement distribution.)
- cover_main:cover_main_recommended: 699 (Cover main requirement distribution.)
- cover_main:cover_main_required: 564 (Cover main requirement distribution.)
- editorial:optional_editorial_page: 1099 (Editorial page requirement distribution.)
- editorial:recommended_editorial_page: 553 (Editorial page requirement distribution.)
- editorial:mandatory_editorial_page: 436 (Editorial page requirement distribution.)
- global_scope_policy:region_specific_or_not_global: 1907 (Global scope policy distribution.)
- global_scope_policy:global_host_requires_scope_review: 168 (Global scope policy distribution.)
- global_scope_policy:global_scope_manual_review: 9 (Global scope policy distribution.)
- global_scope_policy:global_site_acceptable_with_relation_review: 4 (Global scope policy distribution.)
- minimum_text_pages_total: 6508 (Estimated minimum text pages across requirement rows.)

## Method Commitments

- Normal main is not automatically demoted when a cover main organizes it.
- Cover main is the packet first page and curated entry point.
- Text pages are pure explanatory pages, but node-level summaries and relation notes remain required.
- Sub sheets can contain appendices; appendices can contain text and cards.
- Medium and large packets require an editorial reading page.
- Global/transnational scope is valid when justified; it must not be forced into a country folder without evidence.

## Largest Requirement Rows

- Global / transnational|Modern typography and layout|Wikimedia Commons|1970-1974: scale=large; cover=cover_main_required; sub_target=10-355; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Global / transnational|Modern typography and layout|Wikimedia Commons|1975-1979: scale=large; cover=cover_main_required; sub_target=10-522; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Mexico|World War and public-information graphics|Wikimedia Commons|1845-1849: scale=large; cover=cover_main_required; sub_target=10-45; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Global / transnational|Modern typography and layout|Wikimedia Commons|1940-1944: scale=large; cover=cover_main_required; sub_target=10-69; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Global / transnational|Modern typography and layout|Wikimedia Commons|1935-1939: scale=large; cover=cover_main_required; sub_target=10-84; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Kazakhstan|Modern typography and layout|Wikimedia Commons|1995-1999: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- India|Modern typography and layout|Wikimedia Commons|1940-1944: scale=large; cover=cover_main_required; sub_target=10-131; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Indonesia|Modern typography and layout|Wikimedia Commons|1975-1979: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Global / transnational|Modern typography and layout|Wikimedia Commons|1965-1969: scale=large; cover=cover_main_required; sub_target=10-48; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Global / transnational|Modern typography and layout|Wikimedia Commons|1930-1934: scale=large; cover=cover_main_required; sub_target=10-53; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Indonesia|Modern typography and layout|Wikimedia Commons|1970-1974: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Indonesia|Modern typography and layout|Wikimedia Commons|2000-2004: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Global / transnational|Modern typography and layout|Wikimedia Commons|1950-1954: scale=large; cover=cover_main_required; sub_target=10-44; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Indonesia|Modern typography and layout|Wikimedia Commons|1995-1999: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Iran|Modern typography and layout|Wikimedia Commons|1975-1979: scale=large; cover=cover_main_required; sub_target=10-75; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Algeria|Modern typography and layout|Wikimedia Commons|1940-1944: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Nigeria|Modern typography and layout|Wikimedia Commons|1955-1959: scale=large; cover=cover_main_required; sub_target=10-70; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Indonesia|Modern typography and layout|Wikimedia Commons|2005-2009: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global
- Global / transnational|Modern typography and layout|Wikimedia Commons|1985-1989: scale=large; cover=cover_main_required; sub_target=10-84; min_text=15; editorial=mandatory_editorial_page; scope=global_host_requires_scope_review
- Bolivia|Modern typography and layout|Wikimedia Commons|1935-1939: scale=large; cover=cover_main_required; sub_target=10-10; min_text=15; editorial=mandatory_editorial_page; scope=region_specific_or_not_global

## Frontend Implication

- Left Content should render packet tree, not a flat register.
- Folder Directory should show packet structure and counts, not engineering-only status.
- Reading Note should become curated editorial guidance.
- Assistant/search can be functional navigation over packet metadata and reading notes; WebLLM is optional.

## Safety

- No rights/source authority/image-state upgrades were made.
- No source-family signal may override macro/global scope review.
- No packet role is applied by this audit.
