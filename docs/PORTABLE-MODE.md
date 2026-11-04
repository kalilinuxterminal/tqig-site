# Portable mode — physical USB test

October 28, 2026; authorized user's iPhone18,5, iOS 26.6/build 23G71, Windows Apple Mobile Device Support 20.0.0.35, persistent pymobiledevice3 developer session.

The browser applied New York City Hall (40.7128, -74.0060), and the developer service accepted it. The user was instructed to observe Apple Maps, unplug USB without pressing Stop, wait at least 30 seconds, then refresh/recenter the current-location indicator.

User result: **“it returned after like 30 seconds or a minute.”**

USB simulation persistence failed for this tested setup. A short cache delay is not portable capability. The site must display **Connection required** and must not display Portable Mode Available for this transport/build.

The helper detected the missing USB device, stopped sending commands, and marked actual location unknown. The user reconnected/unlocked the phone. The developer connection was reopened and a final clear/disconnect command was sent for recovery.

Not tested: persistence after Wi-Fi loss, phone reboot behavior, airplane mode, or different OS builds. No security setting was toggled as a persistence workaround. No promise of offline control or continued offline route playback is made.

Recovery: reconnect to the same computer, unlock, connect in TQIG, choose Stop Simulation, and confirm current location in a phone app. Do not rely on simulated location for emergency, safety, crash-detection or driver-report features.

Primary implementation references: [pymobiledevice3 userspace tunnel](https://github.com/doronz88/pymobiledevice3/blob/master/pymobiledevice3/remote/userspace_tunnel.py), [maintainer session-lifetime discussion](https://github.com/doronz88/pymobiledevice3/issues/767). The historical discussion alone does not establish iOS 26.6 behavior; the user-observed experiment above supplies the build-specific result.
