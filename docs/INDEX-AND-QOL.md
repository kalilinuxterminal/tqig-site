# Landing page and quality-of-life update — November 1, 2026

The landing page now has a readable interactive Clermont map preview, separate Place/Walk/Drive sections, a three-step explanation of computer mode, compatibility/availability information, native FAQ panels, and a clearer invitation to the workspace. Styling aligns the navigation, headings, cards, and footer on desktop and phone screens. Existing device-support limits remain explicit; no new app or phone-only support is claimed.

## Convenience controls

- The center crosshair, crosshair cursor and Choose center control were removed. Map selection uses a click or pin drag; Back to pin and Fit route remain available.
- **Copy coordinates** copies the selected virtual coordinates to six decimal places and confirms success. If copying is unavailable, the coordinates above remain selectable.
- **Undo pin** restores the preceding map selection. History is limited to the last 15 choices in the current workspace session, and repeated identical selections do not add entries. It does not send a device command or undo an applied iPhone location; Stop & Restore retains that role.
- Up to four saved-place shortcuts appear in the selection panel when this browser has favorites. Existing map stars and Saved Places remain available.
- **/** focuses map search without intercepting typing in text fields. Existing Up/Down/Enter/Escape result navigation remains intact.
- The public index has a sticky navigation bar, an accessible mobile menu with Escape/outside-click dismissal, a skip-to-content link, and a Back to top button. Motion follows the reduced-motion preference.

## Verification

The production build and all **28 frontend checks** passed. New history checks cover an outward selection/adjustment/undo sequence, precise coordinates, duplicate selection handling, and bounded history.

Browser checks verified exact copied coordinates, slash-to-search focus, selecting a different coordinate and undoing it, and selecting a saved-place shortcut. The disposable Clermont favorite used for the check was removed afterward. The map has no crosshair overlay or Choose center button. Desktop and 390 × 844 phone layouts were inspected; the phone page fit without horizontal overflow. The mobile menu closed with Escape and after choosing a section link. FAQ expansion and Back to top worked.

No phone connection or location commands were sent for this interface work. Connection status continues to come from the real helper/account service. The existing MapLibre bundle-size advisory remains.

Screenshots: `index-qol-desktop.png`, `index-qol-mobile.png`, and `map-qol-desktop.png`.
