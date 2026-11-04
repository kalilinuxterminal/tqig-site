# Workspace design and map navigation — November 1, 2026

This describes the preceding workspace revision. See [Landing page and quality-of-life update](INDEX-AND-QOL.md) for the latest controls, including removal of the center crosshair.

The workspace keeps its four main navigation items: Home, Location, Saved Places and Settings. Shared typography, spacing, panels, buttons and mobile navigation now follow the same visual treatment. Home leads to the working map, walking and driving tools; saved places and secondary tools follow underneath. Phone-only availability remains explicit, and the Snapscore tool is still a manual tracker.

## Map workflow

- Search is directly on the interactive map, including fullscreen. Results show more address context, support Up/Down/Enter/Escape, and reject malformed coordinates or unnamed results. A ten-second search deadline releases failed requests.
- Search favors the map area at neighborhood scale using Photon's [documented location bias](https://github.com/komoot/photon/blob/master/docs/api-v1.md#location-bias). It doesn't restrict results to a bounding box. At world scale, the bias is removed. A real request for “Clermont” near the test area returned Clermont, Florida first.
- Street/satellite selection, labels, world view and optional browser location are grouped under **Layers**. Layer and label preferences persist in the browser. Escape and outside clicks close the panel.
- Clicking a location or dragging the pin preserves the camera view. Search selections still bring their location into view. **Back to pin** recenters without discarding a close zoom level. **Choose center** selects the geographic point under the crosshair.
- The side panel separates the selected place from acknowledged iPhone status. **Set Location** and **Stop & Restore** retain their existing device controls and connection requirements. Map actions never apply a phone location automatically.
- Route mode has a labeled **Fit route** action. The mobile action sits above the route, keeping endpoints clear of controls and imagery credits.
- Missing provider category icons use a neutral point marker so places remain visible without inventing a replacement category icon.

## Verification

- Production build and all **26 frontend checks** passed, including three new search-response validation checks.
- Normal desktop and 390 × 844 phone layouts were inspected. Home and map pages fit without horizontal overflow; phone navigation remains visible while scrolling.
- Browser checks confirmed nearby search ranking, keyboard selection, stable camera position after a map click, panning without a target change, center selection, recentering, persisted satellite view, and Layers dismissal with Escape.
- A Clermont walking route and separately routed return were planned in **Preview** on the normal account. Both endpoints remained visible with the redesigned mobile controls. The website reported no connected phone; no phone connection, location or playback commands were sent for this design work.
- The existing MapLibre bundle-size advisory remains. No new libraries were added.

Screenshots: `refined-home-desktop.png`, `refined-home-mobile.png`, `refined-map-desktop.png`, `refined-map-mobile.png`, and `refined-route-mobile.png`.
