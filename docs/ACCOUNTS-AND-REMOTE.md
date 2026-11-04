# Accounts, invitations and the remote dashboard

## Product direction

TQIG is an invite-only iPhone location-simulation workspace. `/preview` is public and plays a real 14-second animated MP4. `/dashboard`, the local map/simulators, `/remote`, `/phone` and `/admin` require sign-in in the frontend. Every account, owner and remote-command API also checks identity and authorization on the server. Hiding a link is not the security boundary.

The three connection paths are distinct:

1. **This computer:** the previously proven local USB helper; shared-network Wi-Fi remains experimental.
2. **Remote home iPhone:** an account-authorized outbound relay controls only the phone attached to the home computer. The home helper must run continuously. It never opens an inbound internet port.
3. **The phone being carried:** experimental installed-native-companion handoff, separately described in `PHONE-ONLY-RESEARCH.md`. A home iPhone cannot substitute for this phone.

## Owner and invitations

`Start-TQIG.cmd` prepares dependencies/builds and runs both local services through `backend.launch`. Open `http://127.0.0.1:8766/owner/setup`. The account API runs on port 8770. The first owner can be initialized only through the loopback-only preview bootstrap or the interactive server command `python -m backend.manage`. Public signup never assigns owner rights; there is no default owner/password or hardcoded invitation.

The owner console lists actual registered accounts and creates invitations with optional email restriction, use count and expiry. Codes are randomly generated, stored hashed, shown once and consumed atomically. Revocation and expiry are enforced during signup. Disabling a member revokes sessions and computer access; the owner cannot be disabled through this UI.

Passwords use per-password salted scrypt. Session tokens are random and stored hashed; cookies are HttpOnly and SameSite=Lax, with Secure and the `__Host-` prefix in production. Browser-session cookies expire server-side after eight hours; “Keep me signed in” uses a 30-day cookie and server expiry. Unsafe authenticated account operations also require a session-bound CSRF value and an exact allowed Origin. Login/enrollment attempts are bounded.

Email is an account identifier, not a verified mailbox. Email verification, password recovery, account deletion, operational audit/review and production monitoring remain release gates.

## Linking a home computer

Sign into the public account website on the home computer, open Remote, and choose **Link this computer**. The setup component appears only after this deliberate action. The local helper must be running, authorized in this browser and already connected to the correct iPhone. For a hosted website, use the temporary code from the helper's loopback-only `/authorize` page. HTTPS-to-loopback browser permission handling still requires deployed Chrome/Edge validation.

After explicit remote-control consent, the account service issues a five-minute single-use enrollment code; the helper redeems it over its configured account-server address. The resulting per-computer credential stays in a private local runtime file. It is hashed on the server, revocable and never returned in computer listings. Only the originally authorized local device is eligible for remote reconnection.

The helper's account-server address is fixed by `TQIG_PORTAL_URL`; it does not accept an arbitrary destination URL from a website. Production requires HTTPS; only the loopback preview may use HTTP. No Apple trust material or device serial identifier is sent to the relay. Linking explicitly discloses sharing helper status and virtual coordinates.

## Commands and restoration

The remote dashboard supports stationary targets and walking/driving schedules. It queues validated, account-owned commands, with separate queued, delivered, acknowledged, failed, cancelled and expired states. An acknowledgement appears only after the home executor returns a result. This remains a service acknowledgement, not GPS readback.

Only allowlisted operations are accepted; the relay has no shell/file-execution command. Delivered commands are not automatically replayed. Missing acknowledgements expire to an unknown outcome. Stop can interrupt browser monitoring of an earlier command and is prioritized ahead of queued movement. A new location is never silently retried.

The helper sends heartbeats during long operations. Initial network failure pauses an active journey; repeated failures stop remote control and request restoration locally. Revocation requests local Stop and removes saved agent access. A missing physical connection can still prevent restoration: use the local recovery/USB workflow and verify actual GPS on the phone.

Command payloads are cleared after completion, cancellation or expiry. Scheduled cleanup removes command records older than 24 hours. The latest computer status is retained for the account and cleared on unlink. The account database, local agent secret and Wi-Fi address file live in ignored `.runtime/` storage and are excluded from source ZIPs and Docker builds.

## Deployment

The account website is a real Python service, separate from the Windows Apple integration. `Dockerfile.portal` packages only the account API and compiled frontend. It needs a persistent `/data` volume and HTTPS reverse proxy preserving the configured Host. Set `TQIG_LOCAL_PREVIEW=0` and `TQIG_PUBLIC_ORIGIN=https://tqig.space`; use the interactive management command for initial owner creation. Configure the home helper with `TQIG_PORTAL_URL=https://tqig.space`.

The frontend account API should be same-origin on the public website. Do not ship a production frontend pointing to the developer's loopback account database. A static-only Cloudflare Pages deployment alone cannot provide this account/relay backend. SQLite here targets a single-instance preview; a multi-instance public service needs an appropriate database/session/rate-limit deployment design.

No permanent cloud deployment or DNS change has been performed. Temporary HTTPS relay validation now includes real stationary, walking, driving, Stop and revocation commands on the authorized iPhone; see `CONNECTED-VALIDATION.md`. Automated relay tests use isolated user/device fixtures. Signed helper distribution and independent installed Chrome/Edge tests remain open.

The local agent binds enrollment to the explicitly authorized iPhone identity. If a different iPhone is later connected locally, remote connect and movement commands fail until that phone is deliberately linked. Stop/Restore remains available as a recovery action. This boundary is covered by the outbound-worker tests.

## Temporary phone access (0.7)

The local Dashboard can start/stop a checksum-verified official Cloudflare Quick Tunnel to a separate, loopback-only account listener on port 8772. The developer/Apple helper on 8766 is never forwarded. The public listener shares the same account store but runs with production cookie and owner-bootstrap settings for the exact generated HTTPS origin. It is advertised only after public HTTPS health succeeds. The account-bound helper can keep polling the local account service, so it never needs an inbound device-control port or an arbitrary URL supplied by a web visitor.

Setup downloads version 2026.10.0 from Cloudflare’s official release and verifies the published SHA-256. No Windows service, DNS setting or firewall rule is installed. The executable stays in ignored runtime storage and is excluded from source archives. The local dashboard displays a QR link; the address changes on restart. This is temporary preview infrastructure, not permanent domain hosting or an uptime guarantee.

Public/mobile Studio routes select the remote target; only the home helper’s local origin uses direct USB tools. The internet relay path passed both an isolated fixture check and fresh physical iPhone checks through public HTTPS. Temporary test accounts and their access were removed; the owner’s Home PC link remains. Public telemetry omits Apple identifiers and pairing records.

Sources: [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [official release](https://github.com/cloudflare/cloudflared/releases/tag/2026.10.0).

## Transport handling in 0.9

The saved home-device binding can remember a successful USB or Wi-Fi transport change only for the same authorized iPhone. Wi-Fi runs in an isolated, server-selected Python runtime with bounded JSON operations. The public relay cannot choose an interpreter, request the local LAN diagnostic mode or upload pairing records. Held coordinates refresh locally every four seconds after an acknowledged Set; Clear disables refreshes. Counts are sanitized before sharing status.

## Username sign-in — October 31, 2026

The owner may have a locally assigned username in addition to the existing email. Both identifiers resolve to the same account and linked computers. Sign-in accepts the password already assigned to that account; invitation registration and public owner creation still require at least 12 characters. A local owner credential reset hashes the new password, revokes existing browser sessions and preserves computer links. No default username/password is seeded or included in the archive. Public APIs cannot invoke the local reset method.

Validation: 31 account, security and phone-access tests passed, including username resolution, rejection of incorrect/default credentials, reset session revocation and preservation of the enrolled computer. The production build passed. The live local sign-in was checked after the requested owner reset.

Live browser checks also passed on both the local helper origin and refreshed public HTTPS phone link, opening the existing owner dashboard with a remembered sign-in. During the final check USB discovery returned zero devices, and the saved paired Wi-Fi phone was unreachable. Home PC remains linked and its helper online; the physical phone must be reconnected/unlocked before further location commands. No successful cable-free result is claimed.
