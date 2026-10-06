# TASK 8.25 — Frontend Architecture

## Navigation System

### Before (Task 8.24)
- Permanent left sidebar (240px / collapsed 56px)
- Hidden entirely on mobile (no fallback)
- Header: simple top bar with search + profile

### After (Task 8.25)
- Fixed top navbar (56px height)
- Dropdown mega-menus for grouped sections
- Mobile: hamburger → full-screen slide-in drawer
- All existing routes preserved and accessible

## New Components

| Component | Path | Purpose |
|-----------|------|---------|
| TopNavbar | `components/layout/TopNavbar.tsx` | Main navigation with dropdowns |
| DataStatusBadge | `components/ui/DataStatusBadge.tsx` | LIVE/MODELLED/INTELLIGENCE labels |
| DataLayerBanner | `components/ui/DataStatusBadge.tsx` | Section-level data provenance |
| DocumentViewer | `components/viewer/DocumentViewer.tsx` | In-platform PDF viewer |

## New Pages

| Route | Page | Phase |
|-------|------|-------|
| `/live-discovery` | Live Legislative Discovery | 6 |
| `/latest-bills` | Latest Bills | 7 |
| `/upcoming-legislation` | Upcoming Legislation | 8 |
| `/portfolio` | Personal Portfolio | 13-16 |
| `/reports` | Report Center | 17-19 |

## Design System (globals.css)

- CSS custom properties (design tokens)
- Animation utilities with `prefers-reduced-motion` support
- Data type badge CSS classes (badge-live, badge-modelled, badge-intelligence, badge-planned)
- Card system (card-base, card-hover, card-live, card-modelled, card-intelligence)
- Table system (data-table)
- Typography scale (text-display, text-headline, text-title, text-section-label)
- Skeleton shimmer animation
- Gradient text utilities

## Responsive Design

| Breakpoint | Behavior |
|-----------|---------|
| Mobile (<1024px) | Hamburger → slide-in drawer |
| Desktop (≥1024px) | Full horizontal navbar with dropdowns |

## Preserved Existing Layout

The Sidebar.tsx and Header.tsx files are preserved but no longer used in the root layout. The new TopNavbar replaces both. All existing page content files are unchanged.

## Animation Philosophy

- Fast (150-300ms), purposeful, restrained
- Respects `prefers-reduced-motion`
- No continuous background animations
- No excessive parallax or particle effects
- Micro-interactions: hover states, dropdown reveals, card transitions

## Accessibility

- All nav items keyboard accessible
- Mobile drawer traps focus when open
- `aria-label` on all icon buttons
- `aria-expanded` on dropdown toggles
- `role="menu"` and `role="menuitem"` on dropdowns
- High color contrast
- Focus-visible outlines on all interactive elements
