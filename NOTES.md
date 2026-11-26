# Notes (round 7)

Scope: only the fixes requested in this round. The preview was regenerated from the site
source (Jekyll build, then `tools/preview/build_preview.py`).

## Banner
- One incoming path per destination node in every composition. The marked atom's only
  incoming path is the violet one. Desktop: 28 paths for 28 nodes; tablets: 25 for 25;
  phones: 17 for 17. `--check` now also reports the most paths any node receives (1).
- Phones: the signal now sits at x 382-470 and the molecule at x 294-333 (art units), so
  both stay fully in view at 390 px (view 125-515) and also at 320 px (view 160-480).
  Masthead sizing is unchanged.

## Funding
- Removed Wilmar PhD Scholarship and LPDP–NTU Graduate Scholarship: their only
  scheme-specific official pages (NTU Graduate College) return 404; the LPDP pages found
  were general 2024 documents, not a current scheme page.
- Kept SINGA: A*STAR's SINGA page confirms the award (bond-free, PhD at NTU among the
  partners, for international students). Audience text changed to "International
  students" to match that page. No date shown: A*STAR's deadline line, as indexed, still
  refers to the August 2026 intake.
- MSCA now points to the official 2027 call and shows its published indicative timeline:
  applications 7 April to 8 September 2027 (both marked TBC by the Commission).

## Application
- "Submit your application" links to https://gradadmissions.ntu.edu.sg/apply/.

## News
- COLM item: https://colm.cc/ (COLM 2026).
- Oberwolfach item: the workshop report page (2508b, 16-21 February 2025).
- Year-specific event pages: ICML 2026, 2025 and 2024 items; AISTATS 2026 item.
  (https://icml.cc/ now opens ICML 2027.) The AISTATS 2025 and 2023 items already had
  year-specific links and were left unchanged.
- Tracking parameters (`utm_source`) were not copied into any link.

## Checks on the regenerated preview
- 390, 619, 620 and 1440 px: no horizontal scrolling; masthead 273, 273, 273 and 421 px.
- Skip link is the first Tab stop on Home, Team, Join and the PI profile and moves focus
  to the main content.
- Each Join topic moves focus to its research area.
- Publication order, funding statuses and the Twitter label as listed in the reply.
