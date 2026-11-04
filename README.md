# TQIG 0.9 · iPhone location simulation

A browser-first workspace with invitation-only accounts, an owner console, a public animated MP4 preview, local device tools and an outbound remote-home-device relay. **Engineering preview; not a deployed or signed consumer release.**

## Start locally

Windows 11, Python 3.12+ and Node 24 recommended. Double-click **Start-TQIG.cmd**. It prepares dependencies, builds the frontend and runs:

- Website/device helper: **http://127.0.0.1:8766/dashboard**
- Account API/website: **http://127.0.0.1:8770**
- First owner setup: **http://127.0.0.1:8766/owner/setup**
- Account-independent Stop/Restore: **http://127.0.0.1:8766/recovery**

Create your own owner email/password, then use Owner Console to create invitations. There are no default credentials, seeded production users or public owner registration. Other users need a valid invitation. Keep me signed in uses a revocable 30-day session.

Manual setup from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm ci
npm run build
.\.venv\Scripts\python.exe -m backend.launch
```

Apple Mobile Device Support, explicit Trust, Developer Mode and a compatible developer image are required for the physical iPhone. The adapter targets iOS 26.6. The helper remains unsigned. Ctrl+C closes both local services through the coordinated launcher.

## Open the dashboard from a phone

On the home PC, run `Setup-Phone-Access.cmd` once, then sign into the local Dashboard and choose **Enable phone access**. Scan its QR code or copy the HTTPS phone link. Sign in with the same TQIG account on the phone. Keep the home PC awake with TQIG running. The temporary address changes when access restarts; it is not a permanent deployment of tqig.space.

The link exposes the authenticated account/relay service only. Local Apple commands and pairing credentials remain behind the helper boundary. Public access is marked ready only after a real HTTPS health check succeeds. Turn it off from the local Dashboard.

Connect and verify the target iPhone on the home PC, then link that computer in Dashboard. A phone browser uses the linked home device in Location Studio, including map, walking and driving. It does not attempt to connect to a Windows helper on the phone.

The carried phone and the target at home are separate devices in this mode. The one-carried-iPhone goal remains unavailable in the website. Native installation and exact iOS 26.6 behavior remain unverified; the normal site no longer asks users to install third-party apps for it. No browser-only, zero-computer or cellular-only capability is claimed.

## Included

The [Midnight workspace](docs/MIDNIGHT-WORKSPACE.md) adds a black and white design with deep-purple accents, a new SVG TQIG mark, animated Home artwork and responsive card reveals.

Home now clearly separates this-iPhone availability from computer mode. The map uses Set Location and Stop & Restore; setup details stay under Connection options. See [the simple user flow](docs/SIMPLE-USER-FLOW.md).

- Public landing page with clear iPhone GPS location-simulation wording and `/preview` with a real 14-second H.264 MP4.
- Invitation-only signup/signin, eight-hour browser sessions or 30-day remembered sessions, salted password hashing, HttpOnly cookies, CSRF/origin checks and server-side authorization.
- Four-item navigation (Home, Location, Saved Places, Settings), grouped map/walking/driving tabs, registered-user management, account disable/revocation, expiring invitations and optional email restrictions.
- Worldwide MapLibre selection/search, draggable pins, favorites and recents; actual stationary Set and Stop.
- Walking pace and driving profiles; outward ETA, destination stay, separately routed return, pause/resume, preview and acknowledged device playback. New samples/tests use Clermont, Florida.
- Remote home-computer linking, outbound-only polling, allowlisted commands, ownership checks, heartbeats, stop priority, revocation and unknown-outcome handling. Stationary, walking and driving use the same relay.
- A plain phone-only availability page. This mode is unavailable; the declined third-party installation/handoff flow is removed from the normal website. Native research remains documented separately.
- Snapscore manual tracker at `/snapscore`: log your own score, goal and history in this browser. Automatic boosting remains unavailable; no Snapchat passwords, score changes or spam sender are implemented. See [visual polish and tracker scope](docs/ANIMATIONS-AND-SNAPSCORE.md).

The requested [SnapscoreBoosterPlus repository review](docs/SNAPSCORE-REPOSITORY-REVIEW.md) records its desktop-only mechanism and why its bulk-send loop was not integrated.

## Actual device evidence

Earlier USB set/restore was user-observed on one **iOS 26.6 / build 23G71** phone in Apple Maps, Snapchat, Life360 and Find My. Fresh Clermont tests passed through the real public HTTPS account relay to that phone: a 70-second stationary hold, a complete driving round trip at 4× playback, a walking round trip at 1×, destination stays, pause/resume, Stop/Clear and access revocation. These fresh results are developer-service acknowledgements; current app GPS output was not visually read back. See [connected validation](docs/CONNECTED-VALIDATION.md).

USB portable persistence **failed**: real location returned after about 30–60 seconds unplugged. A separate authenticated RemotePairing LAN path now passed actual Set, a 20-second hold and Clear, with no USB data fallback. **The USB cable remained physically attached**, so cable-free operation still needs validation. Run `Setup-WiFi.cmd` to prepare the separate Windows TLS-PSK runtime, then perform trusted USB wireless setup. Wi-Fi remains experimental; cellular/arbitrary internet access to a carried phone is not established.

The remote relay controls the **iPhone attached to the home computer**, not the phone being carried. The public HTTPS relay has passed stationary and trip commands on the actual connected phone, alongside isolated software tests.

## Tests and architecture

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
npm test
npm run build
```

See [interactive map and satellite imagery](docs/MAP-EXPLORER.md), [accounts/remote architecture](docs/ACCOUNTS-AND-REMOTE.md), [compatibility](docs/COMPATIBILITY.md), [Wi-Fi experiment](docs/WIFI-EXPERIMENT.md), [phone-only research](docs/PHONE-ONLY-RESEARCH.md), [walking evidence](docs/WALKING-AND-RETURN-TRIPS.md) and [validation](docs/VALIDATION.md).

## Public deployment and data

The current [landing page and quality-of-life tools](docs/INDEX-AND-QOL.md) include coordinate copying, map-selection undo, saved-place shortcuts, and keyboard search. The preceding [workspace design and map navigation](docs/DESIGN-AND-NAVIGATION.md) report covers map-area search, the Layers menu, and separate map-selection and device controls.

The account/relay service needs a real backend; a static-only site cannot protect/relay these operations. `Dockerfile.portal` includes the Python account service plus `dist/`, without Apple device libraries. Use a persistent volume, HTTPS reverse proxy and production settings in the accounts/remote document. Initialize its owner with `python -m backend.manage`.

Account/computer credentials, native pairing exports and the separate Wi-Fi runtime are in ignored `.runtime/` storage, excluded from source ZIPs/Docker builds. Apple-managed trust records stay in existing local Apple storage. External map/search/route/signal providers receive their corresponding queries. Remote mode explicitly shares virtual targets and sanitized helper status; it does not upload Apple pairing material or device serials.

No permanent DNS or hosting change was made. The temporary Cloudflare phone-access link and its physical iPhone relay were tested with disposable accounts; those test accounts were removed and the owner’s Home PC link was preserved. Signed packaging, deployed Chrome/Edge permissions, cable-free Wi-Fi and extended background tests, email verification/recovery/deletion, production storage/rate-limit design, provider arrangements and security/legal review remain release gates.
