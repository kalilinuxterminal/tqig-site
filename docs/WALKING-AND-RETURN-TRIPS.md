# Walking, destination stays and return journeys

## Controls

Open `/app/walk` for Walking Simulator or `/app/drive` for Drive Simulator. Both let you choose the origin, destination and intermediate stops, a destination stay of 0–240 minutes, and whether to return to the starting virtual location. The walking page adds an adjustable 1–8 km/h pace, Easy/Steady/Brisk presets and min/km or min/mile display.

Build Trip requests an outward route and, when enabled, a separate return route in reverse waypoint order. It never reverses the outward road line as a substitute for proper return routing. Walking uses the foot network; driving uses the selected road profile. One-way streets may make a return journey different or longer.

The planner displays travel time to destination, stay duration, return travel time, whole-trip distance and finish time. The instrument panel shows outward / stay / return, phase countdown, current virtual coordinates and ETA. During the stay, speed is zero and the last applied destination is held. Playback-clock multipliers apply to travel and stay estimates; a five-minute simulated stay at 2× takes approximately 2½ wall-clock minutes, excluding device-call delays.

## Device semantics

Preview never sends device commands. Device Test Mode uses the existing authorized connection and waits for movement acknowledgements. During destination stays and pauses, the helper refreshes the held coordinate every four seconds to keep the developer session active. `acknowledgedSamples` counts movement writes; `holdRefreshes` counts these periodic acknowledgements separately. Neither counter is GPS readback. Timeline index and elapsed time remain separate.

Pause freezes the phase clock, including the stay countdown. USB/network loss pauses the clock and commands. Resume requires an explicitly reconnected session. Stop exits the schedule and sends the device clear command when connected. Returning to the starting **virtual** point does not mean restoration of the phone's real GPS; use Stop and confirm normal location on the phone.

The helper must stay connected through outward travel, destination stay and return. Portable USB persistence failed on the tested iOS 26.6 setup. Offline stays or return journeys are not promised. The existing safety/location limitations apply.

## Validation

Automated tests cover pace-dependent duration, increasing timestamps/distances, fixed destination holds, phase countdowns, separate return geometry, a final return to start, one-way stays, invalid/missing return routes, pause/resume during a stay, disconnect during a stay and separate movement/hold counters and cessation of writes after Clear. These are software checks; physical observations are recorded separately in the device reports.

## Connected walking check — October 28, 2026

The authorized iOS 26.6/build 23G71 phone received the full walking schedule through the local website and USB helper. The test used 4.8 km/h, a separately requested 90.99 m outward route, a six-second stay, and a separate 90.99 m return route. The timeline finished at 144 simulated seconds (69 out + 6 stay + 69 back).

The helper recorded outbound, stay, return and complete phases, with **139 acknowledged coordinate updates** across 140 timeline frames. The stay advanced the clock without claiming new position acknowledgements. The final acknowledged coordinate matched the starting virtual point. The status observations are in `walking-device-evidence.json`; these are device-service acknowledgements, not GPS readback.

The user saw movement in Apple Maps but did not closely observe the pause or return. Those two effects therefore remain **not visually confirmed**. After Stop, the helper reported `clear_sent` and `stopped`; the user confirmed the phone was back at its real location. The test session was safely disconnected afterward.

This completed test took place in New York before the user's testing-area change. Historical evidence is preserved as observed. **All new sample journeys and future device tests use Clermont, Florida**, beginning with Clermont City Hall and Waterfront Park. No home or real current-location coordinates are used as test targets.

## Clermont physical relay check — October 29, 2026

The public HTTPS account relay sent both complete trips to the actual iOS 26.6 phone. Walking used separate 108.748 m routes: 82 seconds outward, six seconds at destination and 82 seconds back at 1×, with 165 acknowledged movement writes. Driving used a 1,638.506 m outward route and separately routed 1,285.646 m return: 256 seconds outward, nine seconds stay and 174 seconds back. Its 4× accelerated protocol test produced 413 movement acknowledgements; it does not establish real-time driving speed or Life360 telemetry.

Both reached outward, stay, return and complete, held the destination, and passed pause/resume with a frozen phase clock. Interrupted playback and access revocation sent Clear. No further coordinate writes occurred in the six-second post-Clear observation. Fresh app GPS output and Life360 MPH were not visually verified. See `remote-physical-evidence.json`.

Opening an existing trip in another browser now shows the live trip summary instead of unrelated planner defaults. Its nominal walking pace is not inferred from an unloaded plan. Screenshots named `live-trip-*-fixture.png` use isolated test data and are interface evidence only.
