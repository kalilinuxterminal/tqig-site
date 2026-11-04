# Shared-network Wi-Fi experiments

## Current result — October 29, 2026

**Actual Clermont Set, a 20-second hold and Clear passed over an authenticated private-IPv4 RemotePairing TCP tunnel with no USB data fallback. The USB cable remained physically attached. Cable-free, locked/background, reboot and cellular behavior are not validated.** Four periodic hold refresh writes were acknowledged. No writes followed Clear during six seconds of observation; current app GPS output was not visually read back. See `wifi-physical-evidence.json`.

The successful path differs from the earlier classic TCP/CoreDeviceProxy failure below. Trusted USB setup prepares RemotePairing, authenticates an identity-matched LAN provider, opens the userspace tunnel, verifies the exact authorized phone and iOS 26.6, then opens the developer location service. A cached peer address is used only with authentication and identity verification. No unpaired/public-address scan or automatic target substitution is performed.

Windows Python 3.12 in the USB runtime lacked a usable TLS-PSK callback. `Setup-WiFi.cmd` prepares a separate installed Python 3.13/3.14 runtime with native TLS-PSK and pinned pymobiledevice3 11.45.1. USB dependencies remain separate. `backend.wifi_worker` owns bounded open/set/clear/ping/close operations; tunnel closure is monitored. Source setup does not bundle its private runtime or credentials.

Normal website Wi-Fi connection refuses to initialize while USB is detected. The local diagnostic used for the LAN proof explicitly records the attached cable; its opt-in is forbidden by the HTTP connection contract. This prevents reporting a cabled diagnostic as cable-free validation.

No firewall, TLS, phone-lock or network isolation protection was disabled. Pairing files and listener addresses stay local. Shared-network reachability does not establish arbitrary internet access or a one-phone cellular workflow.

## Historical attempt — October 28, 2026

The following failed experiment is preserved as history and is superseded only for the explicit LAN path above.

The user explicitly approved enabling wireless access to the already-trusted iOS 26.6/build 23G71 iPhone. USB connection and developer-service verification succeeded. The phone accepted `EnableWifiConnections`; the USB session was cleared/disconnected, and the user physically unplugged USB.

Automatic Apple Network discovery returned zero records. A direct Bonjour browse returned zero advertisements in this session, including after the user toggled/rejoined Wi-Fi. Windows had the Apple Mobile Device Service, with no separate Bonjour service observed; this alone does not establish the cause.

The user supplied the phone's private LAN address. Using that address and the existing Apple-managed pairing record, direct TCP lockdown authentication succeeded: paired=true, exact authorized identity matched, iOS 26.6. The private address and device identity remain only in local runtime settings; neither is in this report or the source archive.

The device offered CoreDeviceProxy, but it closed during the CDTunnel handshake before a developer tunnel could be negotiated. A bounded direct legacy DVT probe returned `InvalidServiceError`. No Wi-Fi location coordinate was sent. **Wi-Fi location set/restore did not pass and remains experimental.** A successful trust session is not a successful location-control session.

The implemented private-address fallback uses the same pinned upstream TCP lockdown/CoreDeviceProxy and userspace tunnel APIs. It rejects missing pairing, the wrong device identity, public/loopback addresses and a USB-attached device during a claimed wireless initialization. The UI still requires the actual developer location service before showing Connected. Failed tunnel startup never reports a successful simulated location.

No firewall protections, TLS verification, phone lock, driver or OS network profile were weakened. No additional network service was installed. Discovery repair is not assumed to solve a peer-closed developer handshake. [Upstream Wi-Fi monitor](https://github.com/doronz88/pymobiledevice3/blob/master/pymobiledevice3/tunneld/server.py), [tunnel implementation](https://github.com/doronz88/pymobiledevice3/blob/master/pymobiledevice3/remote/tunnel_service.py)

A separate RemotePairing record/bootstrap and raw RemotePairing discovery are potential attended follow-ups. An empty record-matching helper result must not be confused with a raw discovery result. No working RemotePairing listener can be inferred from classic port 62078 or a native app's loopback port.

The preceding USB setup/disconnect sent clear before unplugging. All subsequent probes were connection/service checks, with no GPS Set. The failed Wi-Fi session closed. There is no new Maps or third-party app location result to claim from this experiment.
