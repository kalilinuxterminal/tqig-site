# Architecture and status semantics

## Transports

`DeviceConnectionAdapter` has real discovery, open-session and capability methods. `LocalBridgeAdapter` uses the USB path physically tested in the previous milestone. `WifiDeviceAdapter` uses prior trusted Network records, rejects the phone while a USB record is present, checks again after tunnel startup and verifies DVT before reporting connection. Wireless remains experimental and untested on hardware. `BrowserUsbAdapter` explicitly rejects requests because the complete browser-native Apple protocol stack is not integrated; a WebUSB chooser is never represented as device control.

The controller owns all resources in one asyncio task so the DVT session remains open after Set. Commands share a lock and queue. Public mutations also reject overlapping actions rather than building an unbounded backlog. States cover disconnected, discovering, pairing, connecting, ready, applying, active, stopping and error; reconnect is explicit. Polling and a token-authenticated WebSocket carry actual helper state. No status is inferred from a map marker.

Set updates last accepted coordinates only after `LocationSimulation.set` returns. Stop uses `clear`, whose upstream selector expects no device reply. Thus command acceptance, user-observed output and restoration are separate concepts. No GPS readback is fabricated. On cable loss or interruption, device output is unknown and cleanup is best-effort. No automatic reconnect to another phone.

## Road route and clock

OSRM returns road/path geometry, maneuvers, alternative routes and segment speed estimates. Walking/cycling use the provider's separate foot/bike graphs; car profiles use its car graph. No straight-line fallback substitutes for a failed road route. Planning errors preserve the previous route and explain the failure.

The deterministic TypeScript engine samples distance along returned geometry, applies profile speed caps and bounded acceleration/deceleration, and adds optional planned pauses at selected maneuvers. Provider segment speed estimates substitute for unavailable road-class metadata; no exact road classifications or live intersection/traffic data are claimed. Turns follow the route polyline. Timeline distance and ETA come from this simulation plan, which can differ from OSRM's raw travel-time estimate.

Preview Mode runs only in the browser with animation-frame interpolation. Device Test Mode sends the planned samples through the same serialized real adapter, waiting for every acknowledgement. Virtual progress advances only on acknowledged frames; slow device calls stretch wall-clock ETA rather than skipping coordinates. Pause waits for the in-flight call to finish, then holds the last point. Stop sends clear; arrival holds the destination until Stop. A disconnected device pauses commands and requires explicit reconnect/resume. Nothing promises genuine Life360 driving events, safety reports or background continuation.

Max route: 8 hours, 30,000 frames, eight waypoints. Playback clock is configurable. Changing profile or playback settings is disabled while playing/paused. Backend validates time ordering, coordinate bounds, request size, frame count and finite values.

Walking and driving can now compose an outward leg, destination stay and separately routed return leg. Trip metadata carries durations/distances, and frames carry phase labels. Destination holds are sparse clock intervals rather than thousands of repeated coordinate writes. The backend keeps timeline elapsed time, actual acknowledged sample count and phase remaining time distinct. A lost connection pauses the clock even during a long stationary hold. See WALKING-AND-RETURN-TRIPS.md.

## Privacy

Device credentials remain in the host's Apple/library pairing storage. Temporary browser access codes stay in memory. Selected favorites/recents/routes are local browser storage and can be cleared. Device action logs include action result/state/error type, not coordinates, serials or trust records. Optional browser geolocation is triggered only by its explicit map-only control. Search and routing use the disclosed external services; the backend does not fetch the phone's real GPS.
