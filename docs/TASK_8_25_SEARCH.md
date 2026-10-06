# TASK 8.25 — Global Search

## Search Architecture

The search modal is embedded in the TopNavbar.

Triggers:
- Click the Search button
- ⌘K / Ctrl+K keyboard shortcut

## Result Grouping

Results are grouped by entity type:
- Central Bill
- State Bill
- Quantitative Co.
- Intel Entity
- Industry
- Sector
- State
- Monitoring

## Quick Links

When no query is entered, shows quick links:
- All Bills
- Companies
- Predictions
- Live Discovery

## Technical

- Uses existing `useSearch` hook (no new search backend)
- Debounced queries
- Grouped dropdown with category headers
- Shows up to 12 results + overflow count
- Keyboard navigation (Escape to close)
- Click-outside to close

## Features Added

- Grouped results by category (vs flat list before)
- Quick links when idle
- Improved styling with backdrop blur
- Better category labels
