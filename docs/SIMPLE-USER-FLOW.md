# Simple user flow — October 31, 2026

The website now starts with two plainly labeled options: this iPhone, or an iPhone connected to a Windows computer. Phone-only is marked unavailable before any setup is offered. The previous third-party installation and URL-scheme handoff page is no longer part of the user flow; the technical research remains in PHONE-ONLY-RESEARCH.md.

Home no longer opens the remote control panel by default. The four primary links are Home, Location, Saved Places and Settings. Owner tools live in Settings. An existing owner opening the old owner-setup URL returns to the normal sign-in/home flow.

Computer mode shows a compact connection card, Place/Walk/Drive, a map, Set Location and Stop & Restore. Computer linking, QR phone access and removal are under Connection options. Walking retains pace, destination stay and return settings. Driving speed and intersection-stop details are collapsed. Preview is explicit and does not send device commands. Connection setup uses one Connect iPhone action for a single detected phone; Wi-Fi, connection codes and diagnostic checks are secondary.

This is interface simplification, not a new phone-only capability. No additional native applications are required or installed by this UI change. Existing backend authorization, device identity binding, acknowledgement semantics and Stop/Restore operations remain in place. Unknown device outcomes remain unconfirmed rather than displayed as successful location changes.

Validation: TypeScript and production build passed. Browser checks cover Home, phone-only availability, computer mode, walking planning and Preview Start/Pause/Stop, driving options, Settings and connection setup. New virtual sample routes remain in Clermont, Florida. No physical location writes are part of these interface checks. Desktop and 390×844 mobile layouts are inspected; screenshots beginning simple- are interface evidence only.

Saved-place validation used an isolated account and browser origin with synthetic device status: save Clermont, open Saved Places, select its saved card and confirm the map URL/selected place preserve its coordinates. Saved route links now carry their route identifier on both the local and phone origins. Distance preferences remain applied to trips. Real user favorites were untouched. A running-trip fixture retained its outward/stay/return summary after the cleanup. Stationary Set is unavailable while a trip is active; Stop & Restore remains available.
