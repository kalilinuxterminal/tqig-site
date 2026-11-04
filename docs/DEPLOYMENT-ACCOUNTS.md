# Deploying the account/relay website

No permanent public deployment or DNS change has been made. Temporary phone access is available through the local Dashboard; see ACCOUNTS-AND-REMOTE.md. The 0.5 website needs the account API; the earlier static-only Cloudflare configuration by itself can serve only public assets, not a functional protected workspace.

## Single-origin Python deployment

1. Run the frontend tests and `npm run build`.
2. Build with `docker build -f Dockerfile.portal -t tqig-portal .` on a Docker-capable host. The Docker image has not been built on this Windows workspace.
3. Run it with a persistent `/data` volume and an HTTPS reverse proxy. Set `TQIG_LOCAL_PREVIEW=0`, `TQIG_PUBLIC_ORIGIN=https://tqig.space`, and protect the data volume. The proxy must preserve the configured Host; do not expose a development owner-setup endpoint.
4. Run `python -m backend.manage` interactively in the server environment to create the owner. Passwords are read interactively, not from shell arguments. There is no default account.
5. Route the public website and its `/api/auth`, `/api/admin`, `/api/computers`, `/api/commands`, `/api/agent` and `/api/portal` paths to this service. Keep cookies and the frontend API same-origin. Set TLS, HSTS, request-size limits, operational rate limits, backups and monitoring at the proxy/provider.
6. Initialize owner access, generate/redeem an invitation, verify Secure/HttpOnly cookies, member/owner permissions and revocation on the actual deployed origin before opening registration to users.

`backend/requirements-portal.txt` needs no Apple device libraries. The current SQLite design is a single-instance preview. Multiple replicas need shared durable database/session/queue/rate-limit infrastructure and an appropriate migration/backup plan.

## Home helper

Configure the installed helper with `TQIG_PORTAL_URL=https://tqig.space`. It connects outbound over HTTPS, without exposing port 8766 to the internet. A user signs in on the public website from the home computer, chooses Remote → Link this computer, authorizes the local helper with its temporary code, connects the intended iPhone and explicitly grants remote control.

The local `/authorize` and `/recovery` pages remain independent of cloud account availability. The browser must never be given the computer's persistent agent secret or an Apple trust record. Windows signing/packaging and deployed HTTPS-to-loopback/local-network permissions remain release gates; do not ask users to disable browser, TLS or firewall protections.

Remote commands may pass through the relay only for the account-bound home device. Test actual location application and restoration over an external internet connection, loss of internet, computer sleep/reboot and revocation. Automated fixture results are not a substitute for those hardware tests.

## Static assets

`wrangler.jsonc`, SPA redirects and public headers remain useful for a separately hosted static frontend/public preview. Such a deployment needs a properly configured same-origin proxy to the real account service; publishing `dist/` alone does not complete the product. Production frontend builds must not point account requests at a developer's localhost.

No accounts or runtime secrets should be in a source archive. `.runtime/`, local environment overrides, virtual environments and dependency trees are excluded from the delivered ZIP and Docker context.
