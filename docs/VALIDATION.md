# Validation summary

Updated: October 31, 2026. Current release: **0.9.0**.

Fresh connected-phone results are in [CONNECTED-VALIDATION.md](CONNECTED-VALIDATION.md); older milestones below are historical.

## Milestones

1. **Connection feasibility:** real Windows USB discovery, explicit trust/pairing, Developer Mode and developer-channel startup passed on the authorized iOS 26.6/build 23G71 phone. Browser-native transport is not implemented; local helper required. Separate installed Chrome/Edge tests remain pending.
2. **Stationary simulation:** actual device set and restore passed with individual user-observed foreground checks in Apple Maps, Snapchat, Life360 and Find My. No automatic GPS readback is claimed.
3. **Portable persistence:** failed on the tested USB setup. User observed return to real location about 30–60 seconds after unplugging. Recovery reconnect/clear completed. No portable/offline availability claim.
4. **Road engine / dashboard:** real OSRM road routes and alternatives returned. Preview movement, pause and route geometry checked in browser. Walking/cycling have separate provider networks. Signal lookup is optional mapped data, not live light phases.
5. **Connected journeys:** the earlier short road sequence passed with 71+ acknowledged updates, user-observed street movement and stop/restore. A full short walking schedule then reached outbound → six-second stay → return → complete with 139 acknowledged coordinate updates. The user observed walking movement and restoration, but missed the pause/return observation; those effects are acknowledged by the helper, not visually confirmed. Extended background behavior remains untested. A later complete Clermont driving round trip passed service acknowledgements at 4×; see the current report. Life360 MPH was not established; speedometer values are a model, not injected app telemetry.
6. **Consumer preview / release preparation:** routes, responsive dark interface, setup/recovery flow, local authorization, tests, static build and hosting configuration implemented. Signed Windows packaging, production service arrangements and deployed-origin browser checks remain release gates.

## Automated checks

- Frontend: 13 tests covering the original route checks plus walking pace, outward/stay/return composition, destination holds, proper return geometry, round-trip arrival and invalid-trip rejection.
- Backend: 81 tests covering lifecycle/security, trip stays and pause/recovery, account sessions, invitation atomicity, owner permissions, relay ownership/revocation/acknowledgements, sanitized telemetry, private-address trust checks and refusal to control a different locally connected iPhone.
- TypeScript and Vite production build passed. The MapLibre map engine still emits a large-chunk advisory; it is separated and lazy-loaded from the map component.
- Dependency installation reported zero npm advisories at the installed versions. Python `pip check` passed. Tests report a Starlette/httpx test-client deprecation warning; runtime HTTP uses the standard browser Fetch API.

## Evidence limits

Physical results are user-observed and scoped to one phone/build. No device real-location history, serial identifiers or trust records are in this report. No permanent public deployment or DNS change was made. Temporary HTTPS phone access is described below. No signed installer, subscriptions, integrity bypass, fabricated driving report or live traffic-light service is included. The account backend is implemented locally; public deployment remains pending.

Future tests and default website sample trips are centered on Clermont, Florida, at the user's request. Earlier New York reports remain unchanged as historical evidence. Algorithm fixtures now use synthetic coordinates in the Clermont area; they are not a road-survey or traffic dataset.

## Clermont interface checks

- Real FOSSGIS foot routing returned separate outward and return routes between City Hall and Waterfront Park. At 4.8 km/h the preview estimated 14:33 each way, five minutes at destination and 34:06 total over approximately 2.3 km. These are model estimates, not timed physical travel.
- At 6 km/h with a 7.5-minute stay, saved walking settings reopened as 11:39 outward, 7:30 stay and 11:39 return. Saving both walking and driving trips, refreshing the browser and opening the correct simulator preserved the route/settings. Saved cards show whole-trip distance.
- Car routing returned two outward alternatives and a separately routed return: approximately 2.9 km total for the selected trip. The baseline model estimated 4:16 outward, 5:00 stay and 2:54 back.
- Narrow 390 × 844 and desktop 1440 × 1000 layouts were inspected. Mobile uses a visible map above naturally scrolling controls, with no form/console overlap or horizontal overflow. Walking preview Start and Pause were checked. No device coordinates were sent during these interface checks.
- The primary public Overpass lookup timed out. The app released its loading state, retained the usable route and showed a clear fallback message. A separate public-instance connectivity probe also timed out; no mapped-light availability or live-light behavior is claimed from this run. Planned maneuver pauses remain usable.

## Account and remote milestone (0.5)

- Real account backend and public MP4 preview implemented. No production users are seeded. Owner initialization is local-only in preview or interactive on a production server.
- Isolated browser QA created a temporary owner, generated an invitation, registered a member, selected 30-day sign-in, refreshed successfully, signed out, and verified that a member opening `/admin` returns to the dashboard. These are test accounts, not customer registrations.
- Relay tests pass through enrollment, ownership checks, the actual outbound worker loop and a fixture device executor. Queued/delivered are not acknowledged. Stops cancel queued movement, revocation triggers local restoration, malformed status is rejected and device identifiers are omitted. This milestone originally used fixtures; fresh physical relay results are in the current report.
- The 14-second 1280×720 H.264 MP4 was encoded and inspected. Browser playback passed: the video reports a 14-second duration, advances while playing and has no decode error. Narrow 390 × 844 overview, remote setup and owner-console layouts fit the viewport; the user table scrolls inside its own card. Desktop 1440 × 1000 layouts were also checked. The real owner setup is available without an invitation, and its form was inspected without creating an account.
- Wi-Fi was physically attempted: setup accepted and paired LAN authentication passed with USB unplugged; developer tunnel startup failed and legacy DVT was unavailable. Zero Wi-Fi GPS coordinates were sent. See `WIFI-EXPERIMENT.md`.
- The installed-companion handoff is documented and explicit, without an installation/acknowledgement claim. The requested bulk-Snap booster remains unavailable.

Total automated checks: **81 backend + 13 frontend = 94**. The production frontend build passes. This does not establish a production cloud deployment, independent browser/phone app compatibility, or a signed native companion.

## Phone access and simplified navigation (0.7)

- The primary sidebar now has four items: Dashboard, Location Studio, Saved Places and Settings. Owner/account tools are secondary; map, walking and driving are tabs within the studio. A 1440 × 1000 desktop and 390 × 844 phone layout were inspected. The phone page has no horizontal overflow.
- On a public/mobile origin, Location Studio uses the account-bound home computer. Local helper polling is disabled for browser-only saved/settings views. Connection setup remains on the home PC.
- A checksum-pinned official Cloudflare client exposes only a loopback account listener. No Apple helper endpoint is tunneled. Starting/stopping access requires the local helper token, an exact local Origin and explicit confirmation. Owner setup is disabled publicly. Secure/HttpOnly cookies and backend permissions are verified in tests.
- Actual internet fixture test passed: HTTPS sign-in, one-time computer enrollment, real outbound worker polling, Clermont coordinate command, Stop, and acknowledged results. Anonymous account/device access was rejected. Zero physical iPhone coordinates were sent. The disposable test account store and its tunnel were closed afterward.
- Initial probes found a DNS propagation delay for a new temporary hostname. Access now waits for a successful public HTTPS health check before advertising Ready. Failed validation closes the link instead of presenting it as working.
- A separate real-account phone link was then started and verified over public HTTPS; its protected dashboard redirects to sign-in in the browser. No real credentials were entered by the agent. Its URL is runtime state, not a permanent tqig.space deployment.
- At the final physical readiness check there were zero USB devices and no verified phone session. This was the 0.7 readiness snapshot; 0.9 connected-phone testing subsequently passed and the owner’s Home PC is linked.
- The one-carried-iPhone path is documented under Settings. Native signing/install/pairing and exact iOS 26.6 behavior remain untested.
