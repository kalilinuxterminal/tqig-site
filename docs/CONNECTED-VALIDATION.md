# Connected validation — TQIG 0.9.0

Tested October 29, 2026 (UTC evidence timestamps extend into October 30), on the authorized Windows/iOS 26.6 build 23G71 setup. New virtual targets are in Clermont, Florida. No real current location or Apple identifier is published.

## Results

| Test | Result |
| --- | --- |
| Public HTTPS account relay → actual USB iPhone | Passed stationary and trip developer-service acknowledgements |
| Stationary hold | 70 seconds; 17 periodic hold refresh acknowledgements |
| Driving out / stay / return | 256 / 9 / 174 virtual seconds, 4× accelerated playback; 413 movement acknowledgements |
| Walking out / stay / return | 82 / 6 / 82 seconds, 1×; 165 movement acknowledgements |
| Pause / resume | Both trips froze the clock and held their acknowledged target |
| Interrupted trip → Clear | Passed; no further writes in six seconds |
| Revoked computer access | Local Stop/Clear requested; revoked local access removed |
| Account boundaries | Invalid coordinates and member access to admin rejected |
| Authenticated Wi-Fi LAN Set / hold / Clear | Passed without USB data fallback; 20-second hold and four refreshes |
| Physically unplugged Wi-Fi | Pending: USB remained attached during the successful LAN test |
| One carried iPhone / cellular independence | Pending: no signed native companion installed |
| Automated checks | 81 backend + 13 frontend = 94 passed; production build passed |

`remote-physical-evidence.json` and `wifi-physical-evidence.json` record the device-service results. An acknowledgement is not GPS readback. Fresh unattended tests do not establish current Snapchat/Life360/Find My behavior, optical restoration, Life360 MPH or genuine driving reports. Earlier foreground Set/restore observations for the four apps remain scoped to that tested phone/build.

The native protocol sends coordinates; model speed, traffic-stop schedules and UI speedometers do not directly inject app speed/course telemetry. Mapped signals are optional planned pauses, not live traffic-light phases. Full background, reboot and independent installed Chrome/Edge tests remain open.

## Product changes

- Four primary navigation items, with map/walk/drive grouped in Location Studio.
- Another browser viewing a running trip shows its actual timing, destination stay, return and distance instead of default planner values.
- Last applied stationary target is separate from the selected map pin.
- Held coordinates refresh every four seconds while active. Movement and hold acknowledgement counters remain separate. Clear disables refreshes.
- Wi-Fi has an isolated TLS-PSK runtime, authenticated identity checks and no automatic USB fallback. Normal Wi-Fi initialization rejects an attached USB phone.
- Owner’s Home PC link is preserved; temporary physical-test accounts/access were removed. Stop/Clear was sent at the end of the tests.

Desktop 1440×1000 and mobile 390×844 layouts were inspected. `live-trip-desktop-fixture.png` and `live-trip-mobile-fixture.png` show isolated UI test data, not physical GPS evidence.

## Remaining delivery work

Cable-free validation requires physically unplugging USB and repeating Set/hold/Clear. A carried-phone path requires native signing, installation, VPN setup and target-device testing. No Apple Account password was used. Pairing exports are prepared locally and excluded from the source archive. Permanent tqig.space hosting, signed distribution and production account recovery remain release work.

## Resume check — October 31, 2026

The same iOS 26.6 phone was verified again over USB. Clermont Set, a 12-second hold with two refresh acknowledgements, Clear and a six-second no-further-write check passed. A separate authenticated LAN session repeated Set, a 20-second hold with four refreshes and Clear successfully. USB remained physically attached during that LAN diagnostic. See `resumed-physical-evidence.json` and `wifi-resumed-physical-evidence.json`.

The local helper and owner Home PC link were restarted. A new temporary public HTTPS account link passed its health check and the browser displayed the protected sign-in page. The address remains temporary runtime state; no permanent domain was deployed. The final USB session was reconnected and Clear sent. GPS restoration was not visually read back in this unattended run.
