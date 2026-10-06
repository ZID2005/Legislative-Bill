# TASK 8.25 — Document Viewer

## Component

File: `components/viewer/DocumentViewer.tsx`

## Implementation

Option A: PDF rendered inline via browser-native iframe with zoom controls
Option B: "View Official Source" fallback when browser cannot render

## Features

- PDF rendering via iframe (browser-native)
- Zoom: 50% - 200%, 25% increments
- Zoom reset to 100%
- Fullscreen toggle
- Download button (direct PDF download)
- Official source button (opens in new tab)
- Document metadata footer: organization, document date, last verified, page count, document hash

## Fallback Behaviour

When pdfUrl is undefined OR when iframe reports an error:
- Shows document unavailable message
- Prominently shows "View Official Source" button
- No useless intermediate "PDF page" that just redirects

## Source Attribution

Every viewer instance shows:
- Source organization
- Document date
- Last verified date
- Document hash (where available)

## Accessibility

- iframe has title attribute
- All buttons have aria-label
- Download link uses native anchor
- Focus management on fullscreen toggle

## Safety

The viewer never fabricates:
- Source URLs
- Document hashes
- Page counts
- Organization names

All metadata comes from the bill record's provenance data.
