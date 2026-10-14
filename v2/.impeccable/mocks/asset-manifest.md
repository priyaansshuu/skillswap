# SkillSwap approved-comp asset inventory

Independent asset pass, 2026-10-14. All three images were opened and inspected. Approval is supplied by the implementation task; the older pending-review wording in DESIGN.md and README.md is stale and must be updated by the build owner.

## Reference images

| Comp | Exact dimensions | Role |
| --- | --- | --- |
| homepage-desktop.png | 1469 × 1071 | Desktop homepage spatial contract |
| homepage-mobile.png | 783 × 2008 | Mobile homepage spatial contract |
| results-desktop.png | 1505 × 1045 | Discovery/filter/results spatial contract |

The images are design references, not shipping page assets. Do not crop them into interface images or render their text as pixels.

## Implementation manifest

| Visible ingredient | Medium | Fidelity commitment |
| --- | --- | --- |
| SkillSwap wordmark | Semantic text + CSS | Heavy rounded sans wordmark. Use one consistent treatment across surfaces; desktop homepage is the navigation/logo authority. |
| Navigation, login/join actions | Semantic links/buttons + CSS | Wide desktop header with generous outer gutters; compact mobile header and accessible menu button. Preserve homepage labels; results-only invented nav items do not add scope. |
| Hero headline and supporting copy | Semantic headings/text + CSS | Very heavy, rounded, normal-width sans. Desktop headline spans two centered lines and dominates the fold; mobile is left-aligned in four large lines. Avoid a lighter or markedly wider face. |
| Main skill search and primary action | Semantic form inputs/select/button + CSS | Broad pale-coral rounded field. Desktop: long skill input, shorter mode select, coral CTA in one row. Mobile: three full-width stacked controls. CTA remains the field's highest-contrast element. |
| Search, screen, chevron, arrow, menu, book, star, and subject icons | Inline SVG or chosen icon library | Simple line geometry, consistent stroke and optical sizing. Decorative icons hidden from assistive technology; icon-only controls receive labels. No icon raster needed. |
| Subject navigation | Semantic links/buttons + CSS/SVG | Centered text row on desktop; horizontally scrollable, overflow-safe row with coral circular icon grounds on mobile. |
| Homepage member previews | Semantic cards + CSS | Three wide cards on desktop; single column on mobile. Desktop initials sit in rounded square pastel grounds, alongside member identity. Preserve card whitespace, rounded silhouettes, bio depth, and clear profile action. |
| Discovery member cards | Semantic cards + CSS | Three-column results grid beside sidebar. Each card has a shallow pastel header ribbon and circular initials badge, then identity, skill/mode, review status, proficiency, excerpt, and coral profile link. |
| Initials avatars | Actual member initials + CSS | Initials only. Homepage and results may use their respective approved square/circle grammar. Pastel hues are presentational; never imply a rating, credential, or member claim. |
| Results filter sidebar and sort | Semantic labelled form controls + CSS | Tall warm neutral sidebar, five stacked filter groups, clear-filters action; sorting above grid on the right. Mobile adaptation uses an accessible filter drawer. |
| Time-banking explanation | Semantic section, ordered list, links + CSS | Desktop coral strip with intro, separator, three numbered steps, and join CTA. Continue the partially shown mobile section in the same grammar rather than treating the crop as its endpoint. |
| Flat backgrounds, card borders, pastel fields, tiny soft color variation | CSS | Flat shape/material system; thin low-contrast borders, soft corners, no pronounced shadows. Generated-image noise is not an authored texture asset. |

**Produce bucket: empty.** No photographs, illustrations, textures, hosted avatars, or other generated/sourced rasters are needed. No assets were generated. All required UI can be semantic HTML/CSS with simple SVG icons. No image conversion, transparency, or crop requirements apply to shipping assets.

## Sampled color evidence

These samples record the existing approved desktop comp, not a new palette. Fields were sampled away from edges; 8 × 8 interior averages reduce incidental image-generation pixel noise. Coordinates are image pixels measured from the top left.

| Region | Sample | Method/location |
| --- | --- | --- |
| Warm page ground | #FEFCFA | 8 × 8 average at (1430, 545) |
| Coral search ground | #FEEFEE | 8 × 8 average at (80, 382) |
| Primary button left/right interior | #CE4150 / #CF4452 | 8 × 8 averages at (1135, 408) / (1350, 447) |
| Headline dark interior | #201C1D | Interior glyph pixels (309, 155) and (312, 155) agree |
| Card interior | #FEFDFD | 8 × 8 average at (460, 775) |
| Input interior | #FEFEFF | Interior pixel (600, 450) |
| Profile-action tint | #FDEEED | Interior pixel (105, 883) |
| Homepage avatar grounds, AS / RM / PK | #FDE2DE / #E0EFFE / #F1D7FD | 8 × 8 averages at (105, 684) / (555, 683) / (1008, 683) |

The build owner should compare actual rendered values and geometry at the comp dimensions. Do not promote one noisy pixel into an unnecessary gradient or add depth that the comp does not carry.

## Composition and content guardrails

- Match the large headline, broad search field, and first member section before extending the page. The desktop homepage's search and cards nearly fill the horizontal content width; shrinking them into a narrow center column changes the composition.
- At the exact desktop comp size, the homepage fits the member row and time-credit explanation below the hero; results fit sidebar, three cards across, and the start of a second row. Preserve those density relationships.
- Mobile is a reflow of the same product world: large readable type, stacked search, horizontal subjects, and full-width member cards. The mock image is 783 pixels wide; normal phone widths require proportional scaling and appropriate line wraps, not fixed pixel dimensions copied blindly.
- Use real API identities, bios, offers, and rating summaries. Synthetic names, proficiency values, and biography text in comps are illustrative only. Show “No reviews yet” for an unrated member; proficiency is distinct from reviews and reputation.
- Preserve the confirmed 120 starter minutes and equal-value time exchange. Browsing and availability previews do not create requests; teacher acceptance precedes credit reservation.
- The mobile mock changes logo coloring, avatar hue, and profile-button treatment. Apply README's explicit consistency instruction and desktop homepage authority to identity details; retain mobile topology and card scale. Record any resolved variants in the implementation design record.
- Initials, labels, controls, filters, cards, and step numerals remain semantic, responsive code with keyboard access, visible focus, contrast, and reduced-motion support. No rasterized core UI is warranted.
