# SnapscoreBoosterPlus review

Reviewed November 1, 2026 for the requested TQIG integration. No upstream code was installed, executed, or copied into TQIG. No Snapchat session was opened and no message was sent.

## Findings

The repository is archived. GitHub reports no license, and its root contains no license file. Reviewed revision: `5c009fe3b873e85e6b1b8a2c4af9d0d25d5aa2ce`.

Its Python program uses PyAutoGUI, keyboard hooks and a desktop Tkinter interface. It relies on calibrated screen positions in an already-open Snapchat session, then repeatedly clicks capture, recipient selection and send. Its displayed count is a local estimate, incremented before sending. It does not read Snapscore or confirm delivery through a Snapchat API. There is no website service, iPhone integration or browser-only execution path in this repository.

These findings come from static inspection, not a successful runtime test. The reviewed code does not present a Snapchat credential-entry form; this is not a complete dependency or security audit.

## TQIG decision

The mass-spam sending loop is not being integrated. A product button must not claim a verified score increase from a local click counter. Adapting a desktop script also would not deliver the requested phone-only experience. TQIG's current manual tracker remains accurately labeled.

The supported alternative is user-controlled activity in Snapchat itself, with score history and goals in TQIG. An automatic read/sync feature would need a separately verified, permitted integration; this project does not establish one.

## Sources

- [Repository](https://github.com/FlazeIGuess/SnapscoreBoosterPlus)
- [Reviewed source revision](https://github.com/FlazeIGuess/SnapscoreBoosterPlus/blob/5c009fe3b873e85e6b1b8a2c4af9d0d25d5aa2ce/main.py)
- [GitHub repository metadata](https://api.github.com/repos/FlazeIGuess/SnapscoreBoosterPlus)
- [Snapchat's explanation of Snapscore](https://help.snapchat.com/hc/en-us/articles/7012326657044-What-is-a-Snapscore)

Only documentation changed during this review. Existing application tests were not rerun for a documentation-only update.
