# Midnight workspace

Implemented November 1, 2026 in the existing local TQIG project.

## Visual direction

The signed-in workspace now uses a black and white foundation with midnight-purple accents. Home has a new editorial hero, a contour-map illustration, clear Place / Walk / Drive cards, and the existing saved places and secondary tools. Location studio and Settings share the same neutral surfaces, purple selections, and lighter typography. Navigation remains Home, Location, Saved Places and Settings.

The new TQIG mark is a white rounded Q with a purple route tail. It is rendered as native SVG in the shared logo, the workspace header and the Home illustration. Matching assets are available in `public/tqig-mark.svg` and `public/favicon.svg`. The favicon URL is versioned to refresh the old mark.

## Motion and responsive layout

- Page and hero entrances, card reveals when they enter the viewport, and hover feedback on links and cards.
- A drawn route, breathing destination halo, floating emblem and subtle contour movement in the decorative Home illustration.
- Four evenly spaced mobile navigation items, stacked action cards, and a compact account header.
- Reduced-motion preferences disable decorative CSS animation and transitions; card reveals also respect the browser preference.

The artwork is decorative. It does not indicate an active phone connection or a simulated location.

## Verification

- Production TypeScript/Vite build passed after the final CSS changes. The existing MapLibre chunk-size advisory remains.
- All 28 frontend tests passed during this visual update. Device/backend behavior was not changed.
- Actual in-app browser checks covered signed-in Home at 1280px, the phone layout at 390 × 844, Location studio with satellite imagery, and Settings.
- Phone layout had no horizontal overflow; the four navigation targets had equal widths. The new mobile header mark was present.
- The route animation was observed running. All three cards reached full opacity after scrolling into view. The complete Q glyph remains visible during the brand entrance.
- Map search remained transparent inside its styled container; sidebar hover no longer introduces a horizontal scrollbar.
- Map selections, clipboard tools, routing modes and account links remain available. No iPhone command was sent during this design validation.

## Saved previews

- [Desktop workspace](midnight-workspace-desktop.png)
- [Phone workspace](midnight-workspace-mobile.png)
- [Location studio](midnight-map-desktop.png)

Main implementation files: `src/components/Logo.tsx`, `src/pages/Workspace.tsx`, `src/styles/midnight.css`, `src/main.tsx`, `index.html` and the two public SVG assets. No new dependency was added.
