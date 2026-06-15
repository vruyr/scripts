# Internet-Facing Wi-Fi SSID Detection — Design & Implementation Spec


This document is the complete brief for the `wifi-ssid` capability and its
integration into the `wifi-speed` script in this repo. It is meant to be
self-contained: a fresh agent should be able to read only this file, ask the
clarifying questions in [Open Questions](#open-questions-resolve-before-implementing),
and then implement confidently.


## Purpose — the one question


The tool answers exactly one question:

> **Which Wi-Fi SSID am I connected to that takes me to the broader internet?**

That is the *effective internet-facing Wi-Fi hop*, not merely "what Wi-Fi is
this Mac associated to." The two differ whenever there is a personal relay
(a travel router) between the Mac and the real network.

Two things must be true of the answer:

1. If there genuinely is a Wi-Fi link carrying you to the internet, return **its
   SSID** — even if that link is one hop beyond the Mac.
2. If the internet path is **not Wi-Fi at all** (wired, tethered, cellular),
   **say so explicitly** rather than reporting an irrelevant SSID.

The plain case — a Mac on public/home Wi-Fi with no travel router — is the
**primary** use case and must work on its own. GL.iNet detection is the *smarts*
layered on top, not the sole reason the tool exists.


## Context — how this plugs into `wifi-speed`


`wifi-speed` (already committed, same directory) runs Ookla `speedtest`, renders
a live grid panel to stderr, and prints/clipboard-copies a one-line
Obsidian/Templater summary matching `/w/Templates/Wi-Fi Speed.md`:

```
[Wi-Fi SSID: `<% tp.file.cursor() %>`: 19.96↓ 4.05↑ Mbps ⬩ 26.75ms 8.10ms ⬩ ↓ 37.61ms 18.53ms ↑ 28.85ms 10.37ms](https://www.speedtest.net/result/c/27138981-...)
```

The SSID slot is currently a literal Templater cursor — `<% tp.file.cursor() %>`
— filled in by hand. This work fills that slot with the *internet-facing*
answer when it can be determined, and keeps the cursor as the final fallback.


## Mental model — the internet-facing Wi-Fi hop


Walk the path from the Mac outward toward the internet and find the **last Wi-Fi
link in the chain that you actually ride to get online**:

```
Mac ──? hop 1 ──▶ [gateway] ──? hop 2 ──▶ ... ──▶ internet
```

Rules that define the answer:

- A **personal relay you control** (a GL.iNet travel router) is *transparent*.
  Its **local** SSID — the one the Mac joins — is **never** the answer, because
  it is just an extension of your own kit. Look at what the relay uses on its
  **WAN side**.
- A **network you do not control** (a normal/public router or AP) is the
  **edge** of what we can see. If you reached it over Wi-Fi, **that SSID is the
  answer** — we do not (and cannot) peer past it into its DOCSIS/fiber backhaul,
  and we would not want to: "which Wi-Fi am I on" is answered by the SSID you
  joined.
- If the link that actually carries you to the internet is **not Wi-Fi**
  (Ethernet, USB tether, cellular modem), the answer is a **medium label**, not
  an SSID.

So the only place we "go one hop further" is across a GL.iNet (or similar
controlled travel router). Everything else terminates at the first
non-controlled hop.


## Cases and expected answers


| Mac uplink | Gateway | Gateway's path to internet | Answer |
|---|---|---|---|
| Wi-Fi | normal/public router or AP | (irrelevant) | the Mac's Wi-Fi **SSID** |
| Wi-Fi | **GL.iNet** | repeating upstream Wi-Fi | the **upstream SSID** |
| Wi-Fi | **GL.iNet** | wired Ethernet WAN | "not Wi-Fi — Ethernet (via GL.iNet)" |
| Wi-Fi | **GL.iNet** | USB tether / cellular modem | "not Wi-Fi — cellular/tether (via GL.iNet)" |
| Ethernet | **GL.iNet** | repeating upstream Wi-Fi | the **upstream SSID** |
| Ethernet | **GL.iNet** | wired Ethernet WAN | "not Wi-Fi — Ethernet end-to-end" |
| Ethernet | **GL.iNet** | tether / cellular | "not Wi-Fi — cellular/tether" |
| Ethernet | normal router | (irrelevant) | "not Wi-Fi — Ethernet" |
| USB / phone tether | n/a | (irrelevant) | "not Wi-Fi — cellular/tether" |
| anything | undetectable / error | — | `<% tp.file.cursor() %>` (cursor fallback) |

Exact wording of the non-Wi-Fi labels and of the "via GL.iNet" provenance is an
[open question](#open-questions-resolve-before-implementing).


## Detection algorithm


Every step is wrapped in short timeouts and error guards; on any failure the
chain returns whatever it has (often nothing → cursor). Detection must never
hang or crash `wifi-speed`.


### Step 1 — The Mac's uplink interface, link type, and gateway


```sh
route -n get default        # → "interface: en0" and "gateway: 192.168.77.1"
```

Classify the default-route interface as Wi-Fi vs wired vs tether:

- `networksetup -getairportnetwork <dev>` returns the current network for a
  Wi-Fi device, or `<dev> is not a Wi-Fi interface.` otherwise — so it doubles
  as link-type detection and the local-SSID read.
- `networksetup -listallhardwareports` maps each `Device:` to a `Hardware Port:`
  (`Wi-Fi`, `Thunderbolt Bridge`, `USB 10/100/1000 LAN`, `iPhone USB`, …).

Record `uplink_kind` (wifi | ethernet | tether) and `gateway_ip`.

If there is no default route → offline → cursor fallback.


### Step 2 — Classify the gateway: GL.iNet or not?


Decide whether the gateway is a **controlled travel router** (recurse past it)
or a **non-controlled edge** (terminate here).

- Cheap/offline pre-check: `arp -n <gateway_ip>` → gateway MAC → compare the OUI
  (first 3 octets) to GL.iNet's registered prefixes. **Do not hardcode a guessed
  OUI**; verify the actual prefix from the unit in hand against the IEEE OUI
  registry (GL.iNet registers under GL Technologies / Shenzhen assignments).
- Positive confirm: HTTP probe `http://<gateway_ip>/` for GL.iNet UI markers, or
  that `http://<gateway_ip>/rpc` answers JSON-RPC. The HTTP probe is the reliable
  positive signal; the OUI check is the cheap filter.

Default GL.iNet LAN address is `192.168.8.1`, but the gateway here is whatever
Step 1 found (`192.168.77.1` in the sample) — **derive it, never hardcode**.


### Step 3 — Terminal (non-controlled) cases


If the gateway is **not** a GL.iNet:

- `uplink_kind == wifi` → answer = the Mac's Wi-Fi SSID (from Step 1 / the macOS
  read in [Getting the Mac's own SSID](#getting-the-macs-own-ssid)). Done.
- `uplink_kind == ethernet` → answer = "not Wi-Fi — Ethernet". Done.
- `uplink_kind == tether` → answer = "not Wi-Fi — cellular/tether". Done.

We stop at the first non-controlled hop by design.


### Step 4 — Recurse across a GL.iNet (the smarts)


If the gateway **is** a GL.iNet, ignore the Mac's local link entirely and
determine **how the router itself reaches the internet**, then classify that.

General, mode-agnostic method (preferred) — find the router's egress interface
and classify it:

```sh
ssh root@<gateway_ip> "ip route get 1.1.1.1"     # → '... dev <egress> ...'
ssh root@<gateway_ip> "iwinfo <egress> info"     # if Wi-Fi: ESSID = upstream SSID
```

Classify `<egress>`:

- Wi-Fi STA / repeater device (`apcli*`, `*-sta`, `sta*`, `wlan*` in client
  mode) → answer = the **upstream SSID** (`iwinfo` `ESSID`, or the `uci`
  `wifi-iface` with `mode='sta'`).
- Ethernet device (`eth*`, `wan`, bridge) → answer = "not Wi-Fi — Ethernet (via
  GL.iNet)".
- Cellular/tether device (`wwan*`, `usb*`, `rmnet*`, `3g-*`, `modem*`) → answer
  = "not Wi-Fi — cellular/tether (via GL.iNet)".

See [Talking to the GL.iNet](#talking-to-the-glinet) for the SSH vs API choice.
If the router is unreachable or the egress can't be classified → cursor fallback.


### Step 5 — Compose and inject


Turn the answer into the SSID-slot string (an SSID, optionally with provenance,
or a non-Wi-Fi label) and inject it into the `wifi-speed` summary line; add a
matching row to the stderr panel. Always keep the cursor fallback intact.


## Getting the Mac's own SSID


Needed only for the **terminal Wi-Fi case** (Step 3: Mac on Wi-Fi to a
non-controlled AP). For the GL.iNet-relay case the answer comes from the router,
so the macOS read is not on the critical path there.

**Hard constraint:** on recent macOS (Sonoma/Sequoia), reading the connected
SSID requires the **calling app to hold Location Services permission**. Without
it, `networksetup`, `wdutil`, CoreWLAN, and `system_profiler` all return empty
or redacted SSIDs. The terminal running `wifi-speed` must be granted Location
access once in System Settings, or this case degrades to the cursor.

Read order:

1. `networksetup -getairportnetwork <dev>` → after `Current Wi-Fi Network: `.
2. `wdutil info` → `SSID` field (needs `sudo`; probably out of scope).
3. A small CoreWLAN Swift call (also Location-gated).


## Talking to the GL.iNet


Two paths; **prefer Path A** (far smaller). Path B only when SSH is unavailable.


### Path A — SSH (preferred, tiny)


One-time: install a root SSH key for `root@<gateway_ip>`. Then everything in
Step 4 is a couple of `ssh` one-liners (`ip route get`, `iwinfo`, or
`uci show wireless` to read the `mode='sta'` iface's `ssid`). ~15–20 lines.

Egress/repeater detail via `uci`:

```sh
ssh root@<gateway_ip> "uci show wireless"   # mode='sta' entry → its .ssid = upstream
```


### Path B — GL.iNet JSON-RPC API (no SSH, larger)


Firmware 4.x exposes JSON-RPC 2.0 at `http://<gateway_ip>/rpc`:

1. `challenge` for the admin user → `salt`, `nonce`, algorithm.
2. Compute the password hash per GL.iNet's recipe (a `crypt`-style hash with the
   salt, then SHA-256 over `user:crypthash:nonce` — **verify the exact recipe
   against the firmware version in hand**).
3. `login` with the hash → session id (`sid`).
4. `call` the repeater/wifi/WAN status method (4.x: e.g. `repeater get_status`,
   `wifi get_status`, or a WAN/multi-WAN status call) → tells you the active
   uplink mode and, if repeating, the upstream SSID.

Admin password from macOS Keychain (`security find-generic-password`).
Stdlib-only otherwise (`urllib`, `hashlib`, `hmac`, `crypt`). ~100 lines; the
fiddly parts are the challenge-hash recipe and the method names.


## Output format


Candidates for the SSID slot (confirm exact strings — open question):

- Terminal Wi-Fi: `` `CoffeeShop` ``
- Via GL.iNet repeater: `` `HotelWiFi` `` (optionally `` `HotelWiFi` (via GL.iNet) ``)
- Non-Wi-Fi: a clear label, e.g. `Ethernet (no Wi-Fi)`, `cellular/tether` —
  note the template literally reads "Wi-Fi SSID:", so a non-Wi-Fi answer needs
  wording that still reads sensibly there (or a tweak to the template).
- Undetectable / disabled / error: `<% tp.file.cursor() %>` unchanged.

Optionally surface the full traversal in the stderr panel (e.g. a `Path` /
`Uplink` / `Upstream` row) even when the one-line slot shows only the answer.


## Integration with `wifi-speed`


- Add a flag (e.g. `--detect-ssid`), **default off**, so current behavior (emit
  the cursor) is unchanged unless requested. Default-on-vs-off is an open
  question.
- Run detection after the speed test (or in parallel), strictly off the critical
  path; speedtest already takes ~30s.
- Hard per-step timeouts (~2–3s for `ssh`/HTTP) so a flaky router never stalls
  the result.
- Reuse the existing `DASH`/fallback conventions and `state` dict pattern.
- Keep the PEP 723 uv polyglot shebang; stdlib-only. Shelling out to `route`,
  `arp`, `networksetup`, `ssh` is expected and fine.


## Failure handling / fallbacks


Ordered degradation, each falling back to the next:

1. A concrete Wi-Fi SSID (terminal or upstream).
2. A concrete non-Wi-Fi medium label.
3. Partial info (e.g. "GL.iNet detected, mode unknown") — optional, or skip to 4.
4. `<% tp.file.cursor() %>` — on detection disabled or any error.

Never crash, never hang, never block the speed-test result on a router lookup.


## Size estimate


| Piece | SSH variant (Path A) | API variant (Path B) |
|---|---|---|
| Uplink iface + link type + gateway (macOS) | ~30 lines | same |
| Mac SSID (terminal Wi-Fi case) | included above | same |
| GL.iNet detection (ARP/OUI + HTTP) | ~20 lines | same |
| Recurse: router egress + classify | ~20 lines | ~100 lines |
| Wiring / fallbacks / output | ~20 lines | ~25 lines |
| **Total added** | **~90 lines** | **~180 lines** |

Recommendation: build the **SSH variant** first; it is dominated by the macOS
link-type/SSID handling, not the router part.


## Open Questions (resolve before implementing)


Ask the operator these before writing code:

1. **SSH availability:** Is a root SSH key already installed on the Beryl
   (`root@<gateway_ip>`)? If yes → Path A. If no → install one, or use Path B?
2. **Non-Wi-Fi wording:** Exact labels for Ethernet / tether / cellular answers,
   and whether to keep the `[Wi-Fi SSID: …]` template text when the answer is
   not Wi-Fi (or adjust the template / link text in those cases).
3. **Provenance:** When the answer is an upstream SSID reached via the GL.iNet,
   do we annotate it (`(via GL.iNet)`) or just show the SSID?
4. **Mac-SSID source for the terminal case:** Rely on macOS (needs Location
   Services granted to the terminal) — acceptable? Any non-Location fallback we
   should attempt before giving up to the cursor?
5. **Multiple upstreams / multi-WAN:** The Beryl supports multi-WAN with
   failover. If more than one uplink is up, which is "the" answer — the one
   currently holding the default route (the `ip route get` approach handles
   this) or something else?
6. **Default behavior:** detection default-on, or behind `--detect-ssid`?
7. **API path specifics (only if Path B):** Keychain item name/account for the
   admin password, and firmware version (to pin the challenge-hash recipe and
   RPC method names).
8. **GL.iNet OUI:** Provide the actual gateway MAC so the OUI prefix is verified,
   not guessed.
9. **Nested relays:** Out of scope (assume at most one controlled relay between
   Mac and the edge), or must we recurse arbitrarily?


## Command cheat-sheet


```sh
# Default route: interface + gateway IP
route -n get default

# Map interface → hardware port (Wi-Fi vs wired vs tether)
networksetup -listallhardwareports

# Is it Wi-Fi? + local SSID in one shot (Location-gated for the SSID value)
networksetup -getairportnetwork en0

# Gateway MAC (for OUI / GL.iNet pre-check)
arp -n 192.168.77.1

# GL.iNet web/RPC presence
curl -s -m 2 http://192.168.77.1/ | head
curl -s -m 2 http://192.168.77.1/rpc

# On the GL.iNet: how does IT reach the internet?
ssh root@192.168.77.1 "ip route get 1.1.1.1"   # → dev <egress>
ssh root@192.168.77.1 "iwinfo <egress> info"    # Wi-Fi egress → ESSID = upstream
ssh root@192.168.77.1 "uci show wireless"        # mode='sta' iface → .ssid = upstream
```
