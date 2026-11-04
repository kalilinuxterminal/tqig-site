# TQIG compatibility and release matrix

Evidence is scoped to the tested device/build and user observations. Device acknowledgement is not GPS readback, app acceptance, or a permanent guarantee.

| Capability | Status | Evidence / remaining work |
| --- | --- | --- |
| Windows local helper + USB | Physical pass | Apple service, trust, Developer Mode, RSD and DVT verified |
| iOS 26.6 / build 23G71 | Physical pass | One iPhone18,5 |
| Stationary Set / Restore | Physical pass | User observed New York then normal location |
| Apple Maps foreground | Set / restore pass | User-observed current-location indicator |
| Snapchat foreground | Set / restore pass | User-observed own Snap Map marker |
| Life360 foreground | Set / restore pass | User-observed own location card |
| Find My foreground | Set / restore pass | User-observed Me/current phone |
| Connected road sequence | Physical short-test pass | 71+ acknowledged updates; user saw dot moving along streets; stop/restore confirmed |
| Full walking schedule | Fresh Clermont device acknowledgements | 82 s out + 6 s stay + 82 s back at 1×; 165 movement acknowledgements, pause/resume and Clear passed; no fresh visual GPS readback |
| Full driving round trip | Clermont device acknowledgements | 256 s out + 9 s stay + 174 s back at 4× accelerated playback; 413 movement acknowledgements; no prolonged/background claim |
| Stationary hold | Device acknowledgements | 70 seconds with 17 periodic hold refresh acknowledgements; Clear then no further writes |
| Mapped signal pauses | Implemented; automated tests | Optional mapped data; planned timing; no live signal phases |
| Life360 MPH / driving reports | Not established | Coordinate-only interface; app controls those outputs |
| USB portable persistence | Failed on tested setup | Returned to real position after roughly 30–60 seconds unplugged |
| Wi-Fi location data path | LAN developer-service pass; cable-free pending | Authenticated RemotePairing TCP tunnel accepted Clermont Set, 20-second hold and Clear without USB data fallback; USB cable remained attached |
| Wi-Fi persistence / reboot behavior | Not tested | No portable availability claim |
| Direct browser-native USB | Unavailable in this build | No complete browser Apple protocol stack integrated |
| Installed Chrome / Edge independently | Pending | In-app Chromium browser used for current physical tests |
| Temporary HTTPS phone dashboard | Actual iPhone relay pass | Public HTTPS commands reached the connected phone: stationary, walking, driving, Stop and access revocation; safe telemetry checked |
| Public browser → local Apple helper | Intentionally avoided in phone mode | Public/mobile Studio uses the relay; device linking is performed on the home helper’s local page |
| Safety reports, crash alerts, integrity bypass | Not implemented | No claim of genuine driving events or evasion |

Clear was sent after each controlled test. Earlier user observations confirmed restoration; fresh unattended checks confirm the clear command and cessation of writes, not visual GPS restoration. No actual home/current coordinates, pairing credentials, or serial identifiers are published in these reports.
