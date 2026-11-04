# Phone-only and Wi-Fi research

**October 31 UI change:** the user declined the multi-app setup. The normal `/phone` page now states that phone-only mode is unavailable and does not offer installation or native-app launch controls. The research and earlier preparation below are preserved as history, not current user instructions. No phone-only test passed.

The browser Geolocation API reads/watches a location; it does not set the iPhone's system location. A browser-only GPS control path has not been established. [W3C Geolocation](https://www.w3.org/TR/geolocation/)

An installed IPA is a credible research path, rather than something categorically impossible. [TLocation](https://github.com/truongkma/t-location/blob/main/README.md) documents native location simulation using pairing material and a local VPN, plus `tlocation://simulate-location?lat=…&lon=…` and `tlocation://clear-location`. TQIG's earlier experimental phone page offered that explicit user-initiated app handoff; it has now been removed from the user flow. It cannot detect installation, confirm command acceptance or read back actual GPS.

These project claims do not establish compatibility with the tested iOS 26.6/build 23G71 phone. Documented initial install/pairing can still require a computer; pure zero-desktop first setup is not proven. Cellular, signing expiry, app suspension, local VPN setup and restoration need separate tests. [Pairing guide](https://github.com/StikDebug/StikDebug-Guide/blob/main/pairing_file.md)

[Anole's architecture](https://github.com/laatortuejaune/anole/blob/main/ARCHITECTURE.md) is another reference for a native Swift/Rust route. TLocation/StikDebug are AGPL-3.0 and Anole is GPL-3.0-or-later; no app implementation code was copied into TQIG. A separately written companion could evaluate the MIT-licensed [idevice library](https://github.com/jkcoxson/idevice/blob/master/LICENSE.txt), retaining its notice and validating its research-stage capabilities. No TQIG IPA has been built or signed on this Windows machine.

Paired Wi-Fi still needs a reachable phone and a live developer channel. Sharing a Wi-Fi network does not establish access over cellular or arbitrary internet networks. [Apple network pairing](https://help.apple.com/xcode/mac/current/en.lproj/dev3e2f4ee6d.html), [pymobiledevice3 tunnel guide](https://github.com/doronz88/pymobiledevice3/blob/master/docs/guides/ios17-tunnels.md)

## Snapchat module

The requested workflow was hundreds of group Snaps per second through alternative accounts. The reviewed [Login Kit](https://developers.snap.com/snap-kit/login-kit/overview) and [Creative Kit](https://developers.snap.com/snap-kit/creative-kit/overview) do not provide bulk group-Snap sending or a Snapscore setter. Creative Kit hands media to Snapchat's preview for the user to send. The dashboard therefore labels the booster unavailable; no score changes, spam sender, password collection, rate-limit evasion or integrity bypass was implemented.

Snapchat describes its score as activity plus undisclosed factors and warns about unauthorized credential-based integrations. No score-increase guarantee is made. [Snapscore](https://help.snapchat.com/hc/en-us/articles/7012326657044-What-is-a-Snapscore), [third-party integrations](https://help.snapchat.com/hc/en-us/articles/7012343686932-Can-I-use-third-party-apps-or-plugins-with-Snapchat)

## One carried iPhone: October 29 follow-up

The strongest available next test is an officially sourced, signed native companion after initial PC pairing. TLocation publishes an unsigned IPA; SideStore documents Windows first installation. Native signing, phone-side trust/Developer Mode, pairing and VPN setup remain necessary. No TQIG IPA has been built or installed.

Current TLocation guidance requires joining Wi-Fi when starting simulation. Reliable cellular-only simulation on the target iOS 26.6 phone is not established. Its URL handler asks for native confirmation and has no browser success callback, so links cannot substitute for acknowledged driving/walking playback. Anole claims independent operation but does not ship a ready iOS release and its documented build needs Xcode. These are separate research claims, not tested TQIG capabilities.

Primary sources: [TLocation](https://github.com/truongkma/t-location/blob/main/README.md), [source manifest](https://raw.githubusercontent.com/truongkma/t-location/main/source.json), [SideStore prerequisites](https://docs.sidestore.io/docs/installation/prerequisites), [Anole](https://github.com/laatortuejaune/anole), [MIT idevice](https://github.com/jkcoxson/idevice).

## Prepared on the authorized phone

The official idevice-tools v0.1.68 Windows release created a native RemotePairing-format export through the trusted USB connection, and the phone explicitly recognized the record during verification. The local export is access-restricted and excluded from archives. A separate pymobiledevice3 RemotePairing bootstrap enabled the successful LAN developer-service test. These two formats are not assumed interchangeable with the classic Apple trust record.

Read-only app inventory found no installed TLocation, SideStore or LocalDevVPN candidate. Native signing, app installation, phone-side VPN approval and actual carried-phone behavior remain unfinished. No Apple Account credentials were used. Preparing a pairing record does not establish a working installed companion, a signed TQIG IPA or cellular independence.
