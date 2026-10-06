# TASK 8.25 — UI/UX REVAMP AUDIT

## Phase 1: Full Frontend UX Audit

### Current State Summary

**Navigation:** Permanent left sidebar (240px), collapses to 56px icon mode. Completely hidden on mobile with NO fallback navigation — critical gap.

**Header:** 48px top bar with centered search, notifications, profile dropdown. Functional but minimal.

**Cards:** Generic bg-slate-900 border border-slate-800 pattern used uniformly everywhere. No visual hierarchy differentiation.

**Typography:** Body text 10–12px in many places. 9px uppercase labels. Inconsistent sizes.

**Mobile:** Sidebar hidden. No mobile nav at all. CRITICAL GAP.

**Animations:** animate-fade-in + animate-pulse only. No page transitions, no micro-interactions, no skeleton loading on most pages.

**Missing:** Portfolio, Reports, Live Discovery, Document Viewer, Live vs Modelled separation, Upcoming Legislation.

---

## Phase 2: New Navigation Structure

Top Navbar: [⚖ LegisIntel] [Discover ▾] [Analyze ▾] [Monitor ▾] [Portfolio] [Reports] [AI]
Right: [Search ⌘K] [🔔] [User ▾]

Mobile: Hamburger → slide-in drawer

All existing routes preserved and reachable.

---

## Phase 3: Visual Language

- Keep dark identity: slate-950/900 base
- Stronger typography hierarchy
- Fewer borders, more whitespace
- Accent gradients for data-type separation
- Colored indicators: LIVE (emerald), MODELLED (indigo), INTELLIGENCE (amber)

---

## Implementation Status

- [ ] Design system tokens (globals.css)
- [ ] TopNavbar component
- [ ] Mobile drawer
- [ ] New layout.tsx
- [ ] DataStatusBadge component
- [ ] Live Discovery pages
- [ ] Portfolio pages
- [ ] Reports pages
- [ ] Document viewer
- [ ] Improved search
- [ ] Updated homepage
- [ ] Tests
