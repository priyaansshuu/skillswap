---
name: SkillSwap
description: Welcoming peer skill exchange with equal-value time credits.
colors:
  primary: "#c83b46"
  primary-hover: "#a82c39"
  tint: "#feefee"
  ink: "#252326"
  paper: "#fefcfa"
  white: "#fff"
  surface: "#fffdfd"
  muted: "#635c62"
  border: "#e9dfe0"
  field-border: "#d5c9ce"
  placeholder: "#716a71"
  focus: "#932435"
  danger: "#923040"
  profile-tint: "#fdeeed"
  profile-action: "#bd2e40"
  filter-surface: "#f7f4f2"
  booking-surface: "#fff4f1"
  chip-surface: "#fff0ed"
  status-surface: "#f2efef"
  status-text: "#575059"
  status-positive-surface: "#e8f2e8"
  status-positive-text: "#315c36"
  status-pending-surface: "#fff0dc"
  status-pending-text: "#775121"
  status-negative-surface: "#f8e0e4"
  status-negative-text: "#843542"
  coral-ribbon: "#fee4e1"
  coral-avatar: "#ffd1cd"
  coral-initials: "#a32839"
  blue-ribbon: "#e3effb"
  blue-avatar: "#cce4fa"
  blue-initials: "#215d85"
  green-ribbon: "#e9f4eb"
  green-avatar: "#d0ebd5"
  green-initials: "#366547"
  lavender-ribbon: "#f3e5fb"
  lavender-avatar: "#e7ccf7"
  lavender-initials: "#70408c"
typography:
  display:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "clamp(3rem, 6.1vw, 5.6rem)"
    fontWeight: 900
    lineHeight: 1.06
    letterSpacing: "-0.035em"
  headline:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "clamp(2rem, 4vw, 3.5rem)"
    fontWeight: 900
    lineHeight: 1.13
    letterSpacing: "-0.025em"
  section:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "1.9rem"
    fontWeight: 900
    lineHeight: 1.13
    letterSpacing: "-0.025em"
  title:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "1.25rem"
    fontWeight: 900
    lineHeight: 1.13
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"Nunito Sans", sans-serif'
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: '"Nunito Sans", sans-serif'
    fontWeight: 700
  action:
    fontFamily: '"Nunito Sans", sans-serif'
    fontWeight: 800
  small:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "0.9rem"
    lineHeight: 1.5
  status:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "0.78rem"
    fontWeight: 800
  wordmark:
    fontFamily: '"Nunito Sans", sans-serif'
    fontSize: "2.45rem"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.04em"
rounded:
  status: "8px"
  chip: "10px"
  field: "12px"
  ribbon: "13px"
  button: "15px"
  search-field: "16px"
  compact-avatar: "17px"
  navigation-panel: "18px"
  card: "20px"
  utility-panel: "22px"
  search: "24px"
  auth: "25px"
  profile-avatar: "26px"
  circle: "50%"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  field-gap: "18px"
  grid-gap: "20px"
  form-gap: "22px"
  lg: "24px"
  panel: "28px"
  empty: "36px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.white}"
    typography: "{typography.action}"
    rounded: "{rounded.button}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.white}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.primary}"
    typography: "{typography.action}"
    rounded: "{rounded.button}"
    padding: "12px 24px"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.white}"
    typography: "{typography.action}"
    rounded: "{rounded.button}"
    padding: "12px 24px"
  button-text:
    textColor: "{colors.primary}"
    typography: "{typography.action}"
    padding: "8px 0"
  field:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "10px 13px"
  navigation:
    textColor: "{colors.ink}"
    typography: "{typography.action}"
  chip:
    backgroundColor: "{colors.chip-surface}"
    rounded: "{rounded.chip}"
    padding: "8px 12px"
  provider-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "16px"
  provider-card-compact:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "22px 18px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "28px"
  status:
    backgroundColor: "{colors.status-surface}"
    textColor: "{colors.status-text}"
    typography: "{typography.status}"
    rounded: "{rounded.status}"
    padding: "5px 11px"
  skill-search:
    backgroundColor: "{colors.tint}"
    rounded: "{rounded.search}"
    padding: "24px 28px"
  profile-action:
    backgroundColor: "{colors.profile-tint}"
    textColor: "{colors.profile-action}"
    typography: "{typography.action}"
    rounded: "{rounded.field}"
---

# Design System: SkillSwap

## Overview

**Creative North Star: "The Welcoming Skill Marketplace"**

SkillSwap's approved world pairs an approachable, large-type marketplace with calm account screens. Warm paper, pale coral search surfaces, a coral wordmark, generous spacing, and rounded member silhouettes make finding a peer feel straightforward. The same identity continues through teaching, learning, credits, and administration.

This is a record of the built frontend, refreshed from the provisional direction after implementation and the independent Ship review on 2026-10-14. The authority is the approved warm-white, pale-coral, dark-text world and the actual stylesheet; this pass does not reopen the visual choice. Member identity uses semantic initials and line icons. Names, skill details, and ratings remain real UI text.

**Key Characteristics:**
- Warm paper and pale coral frame dark, readable content.
- Rounded Nunito Sans headings provide a confident, welcoming hierarchy.
- Broad search surfaces and restrained controls keep tasks clear.
- Pastel initials distinguish members without photographs.
- Sparse shadows, visible focus, and quiet hover feedback support use.

## Colors

The palette is warm and restrained: coral carries action, near-black carries reading, and pastel member treatments add variety. Frontmatter values are normative; they replace the seed's proposed values.

### Primary

- **Deep Coral** (`primary`): wordmark, primary actions, active navigation, and inline links. The darker hover sibling belongs to shared filled buttons.
- **Pale Coral** (`tint`): broad search surfaces and the time-credit explanation.
- **Profile Coral** (`profile-action` / `profile-tint`): the full-width profile link in homepage member cards.
- **Dark Rose** (`danger`): destructive-action buttons; these retain the shared button hover behavior.

### Secondary

- **Member pastels:** coral, blue, green, and lavender ribbon/avatar/initials triples belong to member identity. The variant is derived from the member name; it is not a rating, skill, or status encoding. Homepage avatars use lighter, locally authored versions of these fills.

### Neutral

- **Warm Paper** (`paper`): page ground.
- **Ink** (`ink`): headings, navigation, and form text.
- **Muted Plum** (`muted`): supporting prose and secondary metadata.
- **Near White** (`surface`) and **White** (`white`): cards/panels and editable fields.
- **Soft Border** (`border`) and **Field Border** (`field-border`): containment and form edges.
- **Filter Stone** (`filter-surface`) and **Booking Blush** (`booking-surface`): filter and booking/authentication surfaces.
- **Placeholder Plum** (`placeholder`): input prompts.
- **Focus Rose** (`focus`): the shared visible keyboard outline.

### Status

Neutral, positive green, pending amber, and negative rose pairs apply to explicit text status badges. Success notices and error alerts use their own authored tint/text pairs, recorded in the sidecar snippets only when included; do not substitute a badge pair automatically.

**The Readable State Rule.** A pastel fill never replaces the written status. Member colors never imply achievement or trust.

## Typography

**Display Font:** Nunito Sans, with sans-serif fallback.
**Body Font:** Nunito Sans, with sans-serif fallback.
**Character:** Rounded letterforms and heavy, balanced headings make the marketplace welcoming; lighter prose and bold actions keep operational screens legible. The frontend self-hosts the Latin 400, 600, 700, 800, and 900 weights.

### Hierarchy

- **Display:** the homepage hero uses the frontmatter display role. At widths up to 1000px it changes to `clamp(2.8rem, 6vw, 4.6rem)`; up to 760px it uses `clamp(2.7rem, 11.2vw, 3.75rem)` with line-height (1.13). Desktop preserves the two-line phrase; phone captures show the approved four-line reflow.
- **Headline:** ordinary page h1 uses the responsive headline role. Profiles, exploration, and authentication have local size overrides.
- **Section / Title:** default h2 and h3 use the recorded roles. Featured section headings use (2rem); panel headings use (1.45rem); standard member-card names use (1.15rem) with tracking (-0.01em).
- **Body:** ordinary paragraph line-height is (1.55). The root leaves body size to the browser default rather than declaring a separate size token. Profile prose is constrained to (70ch); card excerpts use line-height (1.45) and a four-line clamp.
- **Label / Action:** form labels use weight (700); buttons and navigation use (800). Labels retain ordinary case.
- **Small / Status:** supporting text uses the recorded small role; written statuses use the status role and CSS capitalization.
- **Wordmark:** a compact, heavy coral logotype with the recorded wordmark role; responsive header and footer sizes are local variants.
- **Numeric data:** table cells use tabular numerals.

**The Honest Member Rule.** Names, offered skills, initials, and rating summaries stay semantic text. Unrated members display "No reviews yet"; do not decorate them with invented stars, credentials, or testimonials.

## Layout

The desktop content container is `min(100% - 128px, 1376px)`, centered within the page. The header and footer cap at (1600px). Spacing uses the observed steps in frontmatter, with larger gaps assigned locally for page composition.

Member grids have three equal columns and a (20px) gap. Results pair a (250px) filter column with the grid, separated by (28px). Profiles pair flexible prose with a (370px) booking panel and a (70px) gap. Account forms generally use two columns; activity details and wallet summaries use clear grouped blocks.

The stylesheet's responsive boundaries are exact:
- At widths up to **1200px**, container side space becomes (40px), results filters narrow to (220px), and result cards use two columns. The homepage member grid remains three columns.
- At widths up to **1000px**, container side space becomes (30px), the main navigation becomes a toggleable floating panel, and header/content density reduces.
- At widths up to **760px**, side space becomes (20px); search controls stack; member grids, account forms, details, and wallet summaries become one column. Profiles place booking below content. Category links scroll horizontally, with circular icon plates. Filters move from the sidebar to a native modal dialog.
- At widths from **1600px**, the hero display size is explicitly capped at (5.6rem).

The filter dialog is (380px) wide with a maximum of `calc(100% - 32px)`, a (90vh) height cap, and internal scrolling. Tables and activity tabs retain horizontal scrolling when needed. Navigation account actions appear inside the compact menu.

**The Reflow Rule.** Preserve the search, member identity, and task action hierarchy as columns collapse. Do not shrink desktop controls into a phone-sized row.

## Elevation & Depth

Surfaces are flat at rest. Tone, generous inset spacing, fine borders, and nested rounded shapes establish hierarchy. Only shared button hover and compact navigation use authored shadows.

### Shadow Vocabulary

- **Button hover:** `0 4px 12px #7d303020`; a small lift attached to a hovered shared action.
- **Compact navigation:** `0 8px 20px #47323616`; separates the expanded floating navigation from page content.

The modal backdrop uses `#25232675`; it obscures the page without changing the filter panel's material.

**The Quiet Feedback Rule.** Shared buttons transition background and shadow over (0.15s) with `ease-out`. The built app has no authored entrance sequence. Reduced-motion preferences remove transitions and animation.

## Shapes

Rounded rectangles are the governing form. Field and profile-action corners use (12px), shared buttons (15px), search internals (16px), member cards and content panels (20px), utility panels (22px), and the desktop search surround (24px). Status badges and removable skill chips use smaller corners (8px and 10px). The shape values in frontmatter are observed component roles, not a new CSS variable scale.

Result-card initials sit in circular avatars (62px). Homepage member previews use rounded-square avatars (88px, 17px corners), with smaller intermediate-width variants and a (78px, 20px corners) phone variant. Large profiles use (120px, 26px corners), reduced to (80px, 20px corners) on phones.

Containment uses single-pixel borders. Avoid adding ornamental frames, photo placeholders, or repeated shadow stacks to these established shapes.

## Components

### Buttons

Confident filled actions and quieter alternatives share one shape. Primary buttons use the recorded primary colors, padding, and action weight, with a minimum height of (48px), a single-pixel primary border, and a (9px) content gap. Hover darkens the background and adds the button shadow. Secondary buttons have white fill, a field-colored border, coral text, and a locally authored `#fff0ee` hover fill. Danger buttons use Dark Rose at rest and the same shared hover treatment. Text buttons use transparent fill and underline on hover.

Disabled buttons use opacity (0.6) and the not-allowed cursor. Keyboard focus uses a (3px) Focus Rose outline offset by (4px). No separate active/pressed visual treatment is authored. Search buttons use local sizing and become at least (56px) high on phones.

### Chips

Removable offered-skill and learning-goal chips use the chip surface, (10px) corners, and (8px 12px) padding. A coral icon button performs removal. These are content chips, not a selected/unselected filter-pill system.

### Cards / Containers

Member cards and panels use near-white fill, fine soft borders, and (20px) corners. Standard result cards use (16px) padding; homepage previews use (22px 18px) before responsive overrides. Result cards show a pastel ribbon with circular initials, skill/mode metadata, a real rating summary, proficiency, a brief bio, and an inline profile link. Homepage previews instead place rounded-square initials beside identity and use a full-width tinted profile action.

General panels use (28px) padding, reduced to (22px) on phones. Booking/authentication and filters use distinct tonal surfaces. Empty states use a centered warm tint with (36px) padding. List rows use fine dividers instead of separate floating cards.

### Inputs / Fields

Fields use white fill, a single-pixel Field Border, (12px) corners, minimum height (46px), and padding (10px 13px). Textareas start at (110px) and resize vertically. Placeholders remain fully opaque and use Placeholder Plum. Associated labels and optional hint descriptions come from the shared Field component. Native selects remain native controls; checkboxes use coral accent and (18px) geometry.

The common keyboard outline applies to controls. The search input's surrounding plate instead uses a (2px) primary focus-within outline offset by (1px), because the internal input has no border or outline. Errors are written alerts with a line icon, optional field details, and a retry action. Success feedback uses a written status notice.

### Navigation

The coral wordmark anchors an otherwise dark, bold desktop navigation. Active links become coral; ordinary link hover underlines with a (4px) offset. At (1000px) and below, a labelled menu toggle controls a white floating panel with soft border, (18px) corners, (24px) padding, and the navigation shadow. On phones account actions join this menu. A keyboard skip link reveals itself on focus.

Activity tabs use a soft bottom divider and a coral (2px) underline for the active item. Tabs may scroll horizontally.

### Status Badges

Compact, written badges use (5px 11px) padding and neutral, positive, pending, or negative pairs. Completed/approved/fulfilled/resolved use green; requested/pending/scheduled/open use amber; rejected/disputed/reversed use rose. Other values retain the neutral treatment. Their meaning remains in the text.

### Skill Search and Time Explanation

The broad pale-coral search surround contains white icon-bearing skill and mode plates plus a filled action. Desktop padding is (24px 28px); phone padding is (16px), with stacked controls. Homepage mode begins Online; the results search defaults to Any mode when no URL mode exists.

The time explanation uses the same tint, numbered circular markers, and a compact teaching/earning/learning sequence. On phones its steps stack. Maintain plain minutes wording and the server-confirmed sequence: acceptance reserves minutes; matching completion confirmations transfer them exactly once.

## Do's and Don'ts

### Do:
- Do keep the coral wordmark, warm paper ground, and pale-coral search identity consistent across public and account screens.
- Do use the observed Nunito Sans hierarchy and self-hosted weights.
- Do preserve readable written statuses, labelled fields, visible focus, and reduced-motion behavior.
- Do use semantic initials and line icons with actual member information.
- Do let search controls, member grids, and forms reflow at the recorded boundaries.
- Do show minutes plainly and distinguish review ratings from reputation.

### Don't:
- Don't replace controls or member data with rasterized mockup content.
- Don't add photographs, invented reviews, credentials, testimonials, or marketing totals.
- Don't use member pastels as a trust or status encoding.
- Don't introduce dense shadow stacks or decorative entrance motion into this quiet system.
- Don't imply that a request reserves credits before the teacher accepts it.
- Don't hide transaction meaning or an error behind color alone.
