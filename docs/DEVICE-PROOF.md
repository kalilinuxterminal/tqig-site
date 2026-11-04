# Live physical-device results

Test date: October 28, 2026 (America/New_York).

**Result: browser-controlled device-level location set and restore passed on the attached physical iPhone.** Each of the four requested apps also passed an individual foreground location/restore check as observed and reported by the user on the phone. These results do not imply universal app or background compatibility.

## Environment and method

- Host: user's Windows computer; Apple Mobile Device Support 20.0.0.35 installed with user approval and its service running.
- Physical device: model identifier `iPhone18,5`, device-reported iOS `26.6`, build `23G71`.
- Developer Mode: confirmed `true` after the user enabled it and completed the restart/confirmation. Windows service restart restored discovery after USB reconnection.
- Device pairing: explicitly authorized by the user; trusted USB connection succeeded.
- Browser: Codex in-app Chromium browser on Windows. Separate installed Chrome and Edge runs are still pending. The API/feature targets remain desktop Chrome/Edge.
- Pipeline: actual website controls → same-origin authenticated loopback helper → usbmux/lockdown → persistent userspace RSD tunnel → DVT LocationSimulation on the physical phone.
- This was **not** a browser geolocation override, mock transport, or map-marker-only demonstration.
- Fixed target: latitude `40.712800`, longitude `-74.006000`, New York City Hall.
- Device service accepted the set call. Its clear operation returned; restoration was verified separately by user observation because the clear selector has no reply/readback.

## Test sequence

1. A transport-only probe opened the developer location-service channel without Set/Stop.
2. From the website, scanned USB devices, selected the authorized iPhone, and clicked Connect and Authorize. Connection succeeded and enabled Set Location.
3. Clicked Set Location on the New York preset. Browser displayed the device-service success and last accepted coordinates.
4. User checked Apple Maps' current-location indicator and reported: “im in new york city hall”.
5. Clicked Stop Simulation / Restore Location. User confirmed Apple Maps returned to the real location.
6. Reapplied the same New York coordinates for separate foreground checks in Snapchat, Life360 and Find My, all reported successful below.
7. Sent Stop/Restore again. User refreshed each of those three apps and confirmed real location in each.

## App results

| App | Simulated target observed by user | Real location after Stop observed by user | Background / other-device server refresh |
| --- | --- | --- | --- |
| Apple Maps | New York City Hall, current-location indicator | Confirmed | Not tested |
| Snapchat | Own Snap Map marker at New York City Hall | Confirmed after refresh | Not tested |
| Life360 | Own member/location card at New York City Hall or nearby | Confirmed after refresh | Not tested |
| Apple Find My | Me/current iPhone at New York City Hall or nearby | Confirmed after refresh | Not tested |

Observation source: the user's explicit per-app replies in this chat. The agent did not independently inspect the phone screen, capture exact physical coordinates, or implement a device GPS readback. App versions were not collected. No device serial, pairing secret, actual home/current location, or other people's location is included in this report.

## Scope and remaining validation

- The **website plus local Windows helper** path is physically demonstrated on the target build. The no-helper direct WebUSB/WASM path remains unproven.
- Separate installed Chrome and Edge runs, other phones/builds, background refresh, longer-duration stability, suspend/resume, loss of cable and crash recovery remain untested.
- This is compatibility evidence for the installed app versions during this session, not a permanent guarantee. Core Location can expose the software-simulation source flag; no attempt to hide that flag was made.
- The runtime still distinguishes command acceptance from observed GPS. It must not automatically turn a command response into “all apps verified.”
- Final user-reported phone state after the experiment: restored to real location in all four checked apps.
