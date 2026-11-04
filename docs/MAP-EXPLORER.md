# Interactive map update

For the subsequent Home/workspace redesign and current map controls, see [Design and navigation](DESIGN-AND-NAVIGATION.md).

The Location map now opens at neighborhood scale with a readable street basemap. Tap a named landmark or street to select it, drag the selected pin for precise placement, or search by name, address or coordinates. Saved places appear as selectable stars. The selected place, coordinates and actual iPhone simulation status remain separate.

Map and Satellite switch the background without recreating the map. Route lines, A/B markers, the moving journey marker and the chosen point remain mounted. Labels can be hidden independently. The map includes a scale bar, compass, world view, recenter, full-route view and fullscreen. A resize refits an existing route; reduced-motion preferences disable animated camera changes. Selecting or exploring the map does not send device commands.

## Imagery sources

- Street map and labels: [OpenFreeMap Liberty](https://openfreemap.org/quick_start/), based on OpenStreetMap/OpenMapTiles.
- Worldwide satellite background: the **2016–17** Sentinel-2 cloudless mosaic by EOX. This particular mosaic is [CC BY 4.0](https://eox.at/2017/08/sentinel-2-global-cloudless-mosaic/). The newer EOX mosaics are not substituted because their terms differ. The required attribution and links appear in the map.
- Closer imagery in the continental-US coverage box: USDA/USGS National Map orthoimagery. [Service metadata](https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer?f=pjson) describes NAIP imagery and variable dates/resolution. The frontend requests up to level 16 and overzooms it rather than assuming higher levels contain additional detail.

This is a composite satellite/aerial view, not live imagery. Global detail is lower than the US aerial layer, and images can be several years old. The map displays that limitation. The sources require no embedded account key. Public services can be slow, unavailable or rate limited; the view provides loading/error notices, Retry and a Map fallback. [EOX service information](https://maps.eox.at/) describes its as-is availability and rate limiting. Production capacity and a newer licensed global high-resolution provider remain deployment considerations.

## Validation

The production build and all **23 frontend tests** passed. Five map checks cover landmark coordinates, road selection, unnamed/localized labels, repeated-world longitude normalization and route framing across the date line.

Browser checks used a separate account/phone fixture with no device executor: Clermont aerial tiles and London global satellite tiles loaded, named Kehlor Park selection returned its actual map point, dragging changed the chosen coordinates, searching selected Waterfront Park, and selecting a saved star restored its place. Walking route planning and preview movement remained visible after switching between Map and Satellite. No phone location commands were sent for these map checks.

The 390 × 844 layout was inspected with the saved Clermont walking route. Both endpoints stay clear of map controls and expanded imagery credits, and the page has no horizontal overflow. Labels and fullscreen enter/exit were also checked on the normal local account map.

Driving preview planning also returned two outward alternatives and a separately routed return near Clermont, with the route displayed over satellite imagery. The final local account page uses the real connection status; fixture connection indicators in the mobile route screenshot are test data.
