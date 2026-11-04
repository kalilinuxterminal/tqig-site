# Connected route test and speed limits

October 28, 2026. Same authorized iPhone on iOS 26.6/build 23G71 as the stationary proof. The phone was connected through the new TQIG local helper and consumer connection wizard.

- Actual OSRM car-road route: New York City Hall to coordinates 40.7139, -74.0025. The road network returned approximately 1.5 km due to legal road connectivity/one-way routing, not a straight line.
- Preview Mode was checked independently: map route, alternatives, progressing vehicle, pause, resume controls and explicit no-device-command label.
- Switched to **Device Test Mode**, connected the actual phone and started the road timeline.
- A helper status sample recorded index 34 with an actual acknowledged position and 218.3 m of virtual travel.
- The test was paused at index 71 / 243 frames, virtual time 72 s and approximately 438.9 m traveled. No complete-trip arrival test was claimed.
- User reported **“the dot is moving along the street”** in Apple Maps. This confirms physical-device sequence output, not just website animation.
- Stop was sent after the short observation window; user confirmed **“Yes, back at my real location.”**

## Red lights and MPH

The user requested red-light stops and noted that Life360 did not show MPH. These are different capabilities.

The location-service selector used here accepts latitude/longitude, not an explicit speed or traffic-event payload. TQIG's speedometer represents its simulation model; that value is not injected as a Life360 speed field. Apps may infer speed differently or require additional signals. There is no guarantee of Life360 MPH, genuine driving events, crash alerts or driver reports, and no attempt to falsify those features.

The planner now offers an explicit **Load mapped traffic lights** action. OpenStreetMap/Overpass supplies mapped signal positions near the road geometry. Those positions can produce longer planned stops, bounded braking and acceleration. They are not live red/green phases. Signal matching is approximate and does not establish that a particular lane is controlled. When data is unavailable, the UI says so and keeps the road route; it never invents a live phase. The new signal-stop model has automated coverage; live red-light timing is not implemented.

Sources: [location service selector](https://github.com/doronz88/pymobiledevice3/blob/master/pymobiledevice3/services/dvt/instruments/location_simulation.py), [OSRM route contract](https://project-osrm.org/docs/v5.24.0/api/), [mapped traffic-signal tag](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dtraffic_signals).
