> **TQIG 0.5 update:** the account/relay website requires a real backend. Follow [account deployment](DEPLOYMENT-ACCOUNTS.md). The static instructions below describe the earlier frontend-only preparation and are not a complete authenticated deployment.

# tqig.space deployment preparation

No deployment or DNS change has been made. This repository separates the static website from the Windows device helper.

## Public website

Cloudflare Pages: build command `npm ci && npm run build`, output directory `dist`, Node 24. Connect the user's project/repository, then attach `tqig.space` through the provider's custom-domain flow. The generated `_redirects` serves the SPA on direct `/app`, `/app/drive`, `/app/walk`, `/privacy`, `/terms` and `/support` requests. `_headers` supplies CSP, framing, MIME and permission controls. An equivalent Workers Static Assets configuration is included in `wrangler.jsonc`.

Configure `VITE_BRIDGE_URL=http://127.0.0.1:8766`, map style and production routing base at build time. These are public endpoint settings, not secrets. Public deployment must use HTTPS. Do not proxy USB traffic through the hosting platform.

## Local helper

The helper binds only `127.0.0.1:8766`. It accepts only the exact local/dev origins and `https://tqig.space`. A hosted page cannot retrieve the helper token automatically. The user opens `/authorize` on the local helper and copies its temporary code into the wizard. Device APIs require that code in an HTTP header; WebSockets require it in the first message, never a logged URL. Apple pairing records never leave the machine.

Chromium may require local-network permission when an HTTPS site connects to loopback. Validate this on deployed Windows Chrome/Edge. Do not disable browser security or bypass certificates to make the bridge work. The local `/app` remains the working fallback.

## Release gates still open

- Obtain a Windows code-signing certificate; create and sign a versioned helper installer, publish checksums and an update/uninstall strategy. The included launcher is source-level and unsigned; it must not be marketed as a signed download.
- Contract or self-host production map/search/routing services. FOSSGIS OSRM is limited to light development usage at one request/second, requires attribution, and logs route requests. The application rate-limits its own route requests but does not create a commercial service agreement.
- Independently test installed Chrome and Edge, hosted-origin authorization/local-network permission, Wi-Fi setup, prolonged sessions, reconnect, sleep and crash behavior. Local Chromium tests do not replace this matrix.
- Review the packaged helper's dependency licenses, including pymobiledevice3's GPL requirements. Obtain operator/contact details and reviewed public legal/privacy terms; current pages are truthful preview disclosures.
- Run a release security audit, dependency audit and accessibility/performance checks with representative users.

No cloud account or subscription backend is included or required.
