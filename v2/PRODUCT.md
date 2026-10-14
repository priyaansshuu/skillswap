# SkillSwap

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
User-selected React + TypeScript with Vite, React Router, and TanStack Query. Existing FastAPI + PostgreSQL backend remains authoritative. The user requested publication in the repository's top-level `frontend/` directory; the backend remains in `v2/`.

## Users
College students demonstrating and using peer skill exchange. Every ordinary account can both teach and learn. Administrators manage the skill hierarchy, suggestions, moderation, and disputes.

## Product Purpose
Find someone who can teach a skill, request a session, and exchange time credits after both participants confirm completion. Success is two independent browser sessions completing a real exchange through the UI and observing exactly one credit transfer.

## Positioning
Every participant's time has equal value. Time spent teaching earns minutes that can be spent learning; there are no monetary prices or variable teaching rates.

## Operating Context
The first complete demo runs locally on a Windows laptop using the existing PostgreSQL database and demo accounts. Public visitors can browse offers before login; booking and account management require authentication.

## Capabilities and Constraints
- One account and wallet, 120 starter minutes, offers and learning goals, dated availability, session requests, dual completion confirmation, reviews, reputation, notifications, disputes, and administrator tools.
- Blank accounts remain customizable. Discovery requires an active account with an offered skill.
- Initials avatars only. No photo uploads, hosting, direct messaging, video calls, maps, or monetary payments in this build.
- Missing catalog skills are suggested by members and approved or rejected by an administrator.
- Public listings exclude emails, learning goals, wallets, and private review text. Actual teaching ratings and reputation scores are distinct.
- Browsing and availability previews create no exchange requests. Existing backend contracts remain compatible.

## Brand Commitments
SkillSwap name; close Superprof-inspired marketplace composition with large search, welcoming member cards, and clear profiles. The user approved a warm-white, pale-coral, dark-text direction with rounded cards and generous spacing. User-selected workflow: visual mockups reviewed before coding.

## Evidence on Hand
Existing source, migrations, tests, seed accounts, OpenAPI contract, and walkthrough. Superprof's homepage was visually inspected in the in-app browser on 2026-10-14. Mockup member identities and descriptions are synthetic design content, not testimonials or verified expertise. Implementation must use actual API data.

## Product Principles
Make teaching and learning equally available to the same member. Explain minutes plainly. Keep transaction state on the server. Never invent reviews, credentials, success statistics, or availability. Preserve valid form input when an action fails.

## Accessibility & Inclusion
Responsive desktop, tablet, and mobile web; keyboard navigation, visible focus, labelled controls, adequate contrast, reduced-motion support, and explicit timezone labels.
