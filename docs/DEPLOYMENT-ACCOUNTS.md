# Deploying the account/relay website

## Render setup for tqig.space

1. In Render, create a Blueprint from `kalilinuxterminal/tqig-site` on `main`. Review the Starter service and 1 GB persistent disk before approving the paid resources. Render builds the website inside `Dockerfile.portal`.
2. Open the new service’s Shell and run `gosu tqig python -m backend.manage`. Enter the owner details and a unique password of at least 12 characters directly in the shell.
3. In Render’s Custom Domains settings, copy the records it gives for `tqig.space`. In Spaceship, replace the GitHub Pages records for the affected hostnames with those values. Keep unrelated DNS records. Verify the domain in Render and check that `https://tqig.space/api/portal/health` returns JSON with `localPreview: false`.

The hosted service starts with an empty account database. Keep the existing local database, Apple pairing files, and relay credentials on the home PC.

## Single-origin Python deployment

1. Run the repository checks.
2. Build with `docker build -f Dockerfile.portal -t tqig-portal .` on a Docker-capable host. The image compiles the frontend from the same checkout.
3. Run it with a persistent `/data` volume and an HTTPS reverse proxy. Set `TQIG_LOCAL_PREVIEW=0`, `TQIG_PUBLIC_ORIGIN=https://tqig.space`, and protect the data volume. Preserve the configured Host at the proxy.
4. Run `gosu tqig python -m backend.manage` inside the container to create the owner. Enter the password interactively.
5. Route the public website and its `/api/auth`, `/api/admin`, `/api/computers`, `/api/commands`, `/api/agent` and `/api/portal` paths to this service. Keep cookies and the frontend API same-origin. Set TLS, HSTS, request-size limits, operational rate limits, backups and monitoring at the proxy/provider.
6. Initialize owner access, generate/redeem an invitation, verify Secure/HttpOnly cookies, member/owner permissions and revocation on the actual deployed origin before opening registration to users.

`backend/requirements-portal.txt` needs no Apple device libraries. The current SQLite design is a single-instance preview. Multiple replicas need shared durable database/session/queue/rate-limit infrastructure and an appropriate migration/backup plan.

## Home helper

After the official origin passes its health check, create a one-time enrollment code in the hosted Shell with `gosu tqig python -m backend.manage --enroll-home-pc`. Enter the owner sign-in there. Use the code within five minutes.

On the home PC, after restoring any active simulation, close the existing TQIG launcher. Open PowerShell in the project folder and start TQIG with a separate hosted link file:

```powershell
$env:TQIG_PORTAL_URL = 'https://tqig.space'
$env:TQIG_AGENT_STATE_FILE = Join-Path $PWD '.runtime\remote-agent-hosted.json'
.\Start-TQIG.cmd
```

In the PC's local TQIG workspace, use **Computer connection** to connect the backup iPhone. Then run this in another PowerShell window on the PC:

```powershell
$origin = 'http://127.0.0.1:8766'
$headers = @{
    Origin = $origin
    'X-TQIG-Token' = (Invoke-RestMethod "$origin/api/session").token
}
$code = Read-Host 'Paste the one-time Home PC enrollment code'
$body = @{code = $code; confirm = $true} | ConvertTo-Json -Compress
$result = Invoke-RestMethod "$origin/api/remote/link" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
$result.remoteControl | Select-Object linked, running, portalUrl
```

The hosted relay uses the existing USB helper and its outbound HTTPS connection. The original local link file remains available if you restart without these two environment settings. Confirm **Ready** on the official dashboard and test from the carried phone over cellular before relying on it.

The local `/authorize` and `/recovery` pages remain independent of cloud account availability. The browser must never be given the computer's persistent agent secret or an Apple trust record. Windows signing/packaging and deployed HTTPS-to-loopback/local-network permissions remain release gates; do not ask users to disable browser, TLS or firewall protections.

Remote commands may pass through the relay only for the account-bound home device. Test actual location application and restoration over an external internet connection, loss of internet, computer sleep/reboot and revocation. Automated fixture results are not a substitute for those hardware tests.

## Static assets

`wrangler.jsonc`, SPA redirects and public headers remain useful for a separately hosted static frontend/public preview. Such a deployment needs a properly configured same-origin proxy to the real account service; publishing `dist/` alone does not complete the product. Production frontend builds must not point account requests at a developer's localhost.

No accounts or runtime secrets should be in a source archive. `.runtime/`, local environment overrides, virtual environments and dependency trees are excluded from the delivered ZIP and Docker context.
