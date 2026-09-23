# Synevyr Architecture Standard

This is the reference for how Synevyr is built. It covers process boundaries, the IPC contract, the extension model, and the security defaults. Read it before adding a component.

Synevyr distributes AI workloads across remote, local, and region-separated models. The product is the routing and policy layer, not the agent loop. Users bring their own harness, or write one.

### Document map

| Document | Covers |
| --- | --- |
| **architecture.md** (this file) | Process boundaries, IPC, extension model, security defaults, packaging |
| [networking.md](networking.md) | Transports, pairing, relays, DDoS and firewall, agent egress ACLs |
| [agent-rbac.md](agent-rbac.md) | Agent identity, roles, permissions, delegation, offboarding |
| [action-classification.md](action-classification.md) | Consequence grading and approval gates for agent actions |
| [global-compliance.md](global-compliance.md) | Jurisdiction, data residency, export control, sanctions |
| [openclaw-hermes-overview.md](openclaw-hermes-overview.md) | What the incumbents do well |
| [wishlist.md](wishlist.md) | The documented failures this standard is designed around |

---

## 1. Non-negotiables

These are the constraints every design decision answers to. If a feature can't be built inside them, the feature changes.

1. **One static binary, no runtime dependency.** No Node, no Python, no JVM on the user's machine. OpenClaw requires Node 26 and loses people at step one.
2. **Headless is the default.** The GUI is an optional client of a service that runs fine without it.
3. **Loopback-bound and authenticated from first boot.** There is no unauthenticated mode to misconfigure.
4. **Under 25 MB resident when idle.** If a component can't hold that, it loads lazily or it doesn't ship.
5. **Extensions are untrusted by default.** Capability-scoped, sandboxed, and reversible.
6. **Policy is enforced in the daemon.** A client cannot route around region, budget, or credential rules by misbehaving.
7. **Every setup step that can be automatic is automatic.** Config files are for overrides, never for getting started.
8. **Agents are principals, not features.** Every agent has an identity, a role, a budget, and an approver. See [agent-rbac.md](agent-rbac.md).
9. **Consequential actions are gated outside the model.** Deterministic rules set the floor; a classifier may only escalate. See [action-classification.md](action-classification.md).
10. **Jurisdiction is a routing constraint**, evaluated in the daemon and failing closed. See [global-compliance.md](global-compliance.md).

---

## 2. System shape

```text
                      ┌──────────────────────────────────────┐
   Browser ──────────▶│  Console (embedded SPA, loopback)    │
   Tray applet ──────▶│                                      │
   CLI ──────────────▶│         S Y N E V Y R  D A E M O N   │
   Your harness ─────▶│                                      │
   (SDK, any language)│  router · policy · registry · audit  │
                      └───────────────┬──────────────────────┘
                                      │
                    ┌─────────────────┼──────────────────┐
                    ▼                 ▼                  ▼
             Plugin host        Local models       Remote providers
             (WASM sandbox)     (llama.cpp,        (region-tagged
                                 vLLM, Ollama)      endpoints)
```

One process is the source of truth for sessions, routing, credentials, and policy. Everything else attaches to it.

---

## 3. Components

**Daemon (`synevyrd`).** Rust, tokio. Owns the router, policy engine, credential store, plugin host supervision, audit log, and the local socket. Runs as a user-level service. Never requires root.

**Console.** A small SPA (Svelte or SolidJS, target under 100 KB gzipped) compiled at build time and embedded in the binary with `rust-embed`. Served from loopback by the daemon itself. No separate web server, no static files on disk, no version skew between UI and backend. Because the browser renders it, we ship no webview and no Chromium.

**CLI (`synevyr`).** The same binary. Subcommands speak the local protocol to a running daemon, so anything the console can do is scriptable.

**Tray applet.** Optional, feature-gated, roughly 1 MB. Status indicator and "Open Console". This is the entire desktop presence. If a user never wants it, it's never installed.

**Plugin host.** A separate supervised process running WASM modules. Spawned lazily on first plugin call, idles down after inactivity. A crashing plugin cannot take down the router.

### Why no Tauri

An earlier draft used Tauri. Once the console is browser-served, a bundled webview renders a page the user's existing browser already renders, so it costs 40 to 80 MB for nothing. The tradeoff we accept: Synevyr feels less like a native app than a Tauri build would. If that becomes a real complaint, a Tauri shell can wrap the same console later with zero backend changes. The architecture keeps that door open rather than paying for it now.

---

## 4. IPC contract

**Transport.** Unix domain socket at `$XDG_RUNTIME_DIR/synevyr.sock` (0600), named pipe `\\.\pipe\synevyr` on Windows with an owner-only DACL. Filesystem permissions are the first auth layer.

**Protocol.** JSON-RPC 2.0 over the socket, with the same method surface exposed over HTTP/WebSocket on loopback for the console. One protocol, three transports, no second API to keep in sync.

**Core methods.**

```text
session.create        → open a routed session, returns handle
session.complete      → inference request, streams tokens back
model.list            → available models with region + cost metadata
policy.evaluate       → dry-run: where would this route, and why
plugin.invoke         → call a plugin capability
audit.tail            → stream of routing decisions
```

**Streaming.** Server-to-client notifications for token streams and progress. Every long operation reports progress. OpenClaw and Hermes both draw complaints about work that looks frozen, and the fix is a protocol obligation, not a UI patch.

**Cancellation is first-class.** Every request carries an ID and can be cancelled mid-flight, including in-flight upstream inference. Hermes users complain the agent can't be interrupted; that's a protocol gap, so we close it in the protocol.

**Versioning.** `protocol.version` is negotiated on connect. Breaking changes bump major and the daemon supports N-1 for one release cycle. Both incumbents are criticized for breaking workflows between versions.

---

## 5. Extension model

Users ship plugins and write their own harnesses. These are different directions of call, and conflating them is what produces either an unusable sandbox or an unsafe one.

- A **plugin** is code Synevyr calls. It runs inside our trust boundary, so it is sandboxed.
- A **harness** is code that calls Synevyr. It runs in its own process, as the user, so it needs no sandbox. It is an API client holding a scoped credential.

This split gives harness authors full power (it's their machine, their process) while keeping registry-distributed plugins contained. Nobody has to choose between the two.

### 5.1 Harnesses (full power, scoped credential)

A harness is any program that speaks the Synevyr protocol. Write it in whatever you like. We publish SDKs for TypeScript, Python, Rust, and Go, each a thin wrapper over JSON-RPC.

```ts
const s = await Synevyr.connect()            // discovers socket, reads local token
const session = await s.session.create({ policy: "eu-only" })
for await (const tok of session.complete({ prompt, model: "auto" })) { ... }
```

Properties that matter:

- **Scoped tokens.** A harness is granted a token limited to specific models, regions, spend ceiling, and rate. The console shows every issued token and revokes any of them instantly.
- **The daemon enforces policy regardless of harness behavior.** A buggy or hostile harness cannot route an EU-tagged workload to a US endpoint, exceed its budget, or read a credential. It asks; the daemon decides. This is the property that makes user-authored harnesses safe to encourage.
- **Credentials never leave the daemon.** A harness never sees a provider API key. It sends a request and gets tokens back.
- **Harnesses are processes, not plugins.** They start, crash, and are debugged independently. Killing one affects nothing else.

### 5.2 Plugins (sandboxed, capability-scoped)

Plugins extend what the daemon itself can do: tools, provider adapters, transports, policy evaluators.

**Tiers.**

| Tier | What it is | Isolation | Distributable |
| --- | --- | --- | --- |
| T1 WASM | Default plugin format | `wasmtime`, no ambient filesystem or network | Yes, signed |
| T2 Sidecar | Subprocess speaking the protocol over stdio | OS sandbox where available, explicit consent | Yes, signed, prominent warning |
| T3 Dev | Unsigned local build | Dev mode only | No |

Most plugins are T1. T2 exists because some provider adapters genuinely need a native library, and pretending otherwise pushes authors to fork the daemon. T3 never installs from a registry, shows a persistent console banner, and is off by default when running as a service.

**Capability manifest.** Every plugin declares what it needs, and gets nothing else:

```toml
[plugin]
name = "acme-vector-store"
version = "1.4.0"

[capabilities]
net.outbound = ["api.acme.com:443"]     # exact hosts, no wildcards
fs.read      = ["$PLUGIN_DATA"]          # scoped dir, not $HOME
secrets      = ["acme_api_key"]          # named, brokered by daemon
```

Grants are shown in plain language at install time, listed in the console, and revocable without uninstalling. Requesting a new capability in an update requires fresh consent, so an innocuous plugin cannot quietly acquire network access in v1.5.

**Registry rules, written against ClawHavoc.** ClawHub shipped over 800 malicious skills, roughly 20 percent of the registry, mostly macOS stealers. So:

- Publisher identity is verified and signing keys are pinned per publisher.
- Versions are immutable and pinned by default. No floating installs.
- No auto-update of plugin code without consent. Hermes users complain that self-improvement silently overwrites their tuned work; the same principle applies here.
- Automated scanning plus a quarantine window on first publish.
- Global revocation: a compromised publisher key disables affected plugins on next daemon start.
- The console shows provenance (publisher, signature, capability diff versus installed) before install.

We accept the honest cost: this is more friction than ClawHub, and some plugin authors will find it annoying. Retrofitting a sandbox onto a trusting plugin API is close to impossible, so it goes in first or never.

---

## 6. Security defaults

**Network**

- Bind `127.0.0.1` always. Binding externally requires an explicit flag and refuses to start unless auth and TLS are configured. There is no path to an accidental `0.0.0.0`.
- Validate `Host` and `Origin` on every HTTP request. This blocks DNS rebinding, which is how a loopback-only service gets taken over from a web page.
- **Never accept a gateway, backend, or callback URL from a query parameter.** That was CVE-2026-25253 exactly: OpenClaw's control UI trusted a URL passed in the query string, so one malicious link handed over full agent control, including on localhost-only deployments.
- Remote access is mTLS or an overlay network (WireGuard, Tailscale). "Open the port" is not a documented option.

**Authentication**

- Token generated at install, stored in the OS keychain, never written to a config file.
- Bearer token in an `Authorization` header, not an ambient cookie. That removes CSRF as a category.
- Console login is a one-time link on first run, then a short-lived session. Devices are listed and revocable.

**Credentials and policy**

- Provider keys live in the OS keychain (`keyring` crate): macOS Keychain, Windows Credential Manager, libsecret. Never in YAML, never logged, never rendered in the console.
- Region policy is a hard routing constraint. A workload tagged EU-only fails closed rather than falling back to a US endpoint. Fail-closed is the default for every policy class.
- Append-only audit log of every routing decision, credential use, plugin invocation, and consent grant. Queryable from the console and `synevyr audit`.

**Build and supply chain**

- `cargo-deny` and dependency review in CI. `rustls` rather than OpenSSL.
- Signed and notarized per platform. Updates verified with minisign or TUF before the binary is swapped.
- Reproducible builds when we can afford them.

### Mapping to documented incumbent failures

| Failure | Where it came from | Our answer |
| --- | --- | --- |
| 40k+ exposed instances, many with no auth | OpenClaw, Feb 2026 | Loopback default, auth always on, refuses unsafe external bind |
| One-click RCE via URL in query param | CVE-2026-25253 | Never trust URLs from parameters; Host and Origin validated |
| 800+ malicious registry skills | ClawHavoc | WASM sandbox, capability manifests, signed and pinned versions |
| Keys in plaintext config | Both | OS keychain only |
| Context bloat, cross-project bleed | OpenClaw | Session-scoped state, explicit retention windows |
| Self-graded success, always passes | Hermes | We don't self-grade. Routing outcomes are measured, not judged |
| Silently overwrites user customization | Hermes | No auto-update of user-authored artifacts without consent |
| Breaking changes every release | Both | Negotiated protocol version, N-1 support window |
| Work looks frozen | Both | Progress reporting is a protocol obligation |
| Setup requires Node 26, Docker, YAML | OpenClaw | Static binary, zero-config first run |

---

## 7. Automatic setup

The loudest OpenClaw complaint is not the agent, it's the infrastructure burden. Users report giving up after weeks of Docker, SSH, and YAML debugging. Setup is a product surface, so it gets designed like one.

**Install.** One-line script (`curl | sh`, `irm | iex`) plus native channels: Homebrew, winget, `.deb`, `.rpm`, AUR. Linux builds link against musl so they run anywhere.

**Service registration.** `synevyr service install` writes a launchd plist, a Windows Service entry, or a systemd **user** unit. Root is never required. `service uninstall` removes everything it created, including the socket and service definition.

**First run, zero config.**

1. Generate keypair and local token, store in keychain
2. Create the state directory, run migrations
3. Bind loopback, pick a free port, write the discovery file
4. Print the console URL with a one-time login link, and open a browser unless `--headless`

No config file is required at any point. `synevyr.toml` exists only for overrides, and every value in it has a working default.

**Provider onboarding.** Paste a key, and the daemon probes the endpoint, discovers available models, infers region from the endpoint, and writes nothing to disk in plaintext. Detected local runtimes (Ollama, vLLM, llama.cpp) are offered automatically.

**Updates.** Signature-verified, staged, atomic swap with rollback on failed health check. Off by default for anyone running as a service, because surprise updates to infrastructure are how you lose trust.

---

## 8. Resource budget

Treated as a test, not an aspiration. CI fails a PR that regresses these.

| Component | Idle target | Notes |
| --- | --- | --- |
| Daemon, no sessions | under 25 MB RSS | tokio, no thread-per-connection |
| Daemon idle CPU | under 0.5 percent | Event-driven, no polling loops |
| Plugin host | 0 MB | Not spawned until first plugin call, idles down |
| Console | 0 MB | Rendered by the user's browser |
| Tray applet | under 5 MB | Optional |
| Installed size | under 40 MB | Single binary plus embedded assets |

For reference, OpenClaw's Node gateway runs 150 to 300 MB resident. Beating that by an order of magnitude is a positioning claim, so it has to hold under measurement, not just at startup.

---

## 9. Tradeoffs we accept

Stated plainly so nobody relitigates them later.

1. **The browser console feels less like a product** than a native window. The tray applet recovers some of it. Reversible via a Tauri shell if it becomes a real complaint.
2. **Rust costs velocity** against Go, especially early. The gain is no GC pauses on the routing path, a genuinely static binary, and a stronger security story. If the team can't sustain it, Go keeps this entire design and shifts the numbers by roughly 20 percent.
3. **Capability-scoped plugins are more friction than ClawHub.** We will have fewer plugins, later. That's the price of not shipping malware to users, and it is not negotiable after launch.
4. **Fail-closed policy will block work that a fail-open system would complete.** For region-separated workloads that's the whole point, but it will generate support requests that look like bugs.
5. **We are not the harness.** Users who want a batteries-included agent will pick OpenClaw or Hermes. We're the layer underneath, and the SDK is how we stay useful to them anyway.

---

## 10. Open questions

- Multi-tenancy: does one daemon serve multiple OS users, or one per user? Current lean is one per user, because it keeps the keychain and permission story simple.
- Whether T2 sidecar plugins are allowed in the public registry at launch, or held for a later release.
- Policy language: declarative config, or embedded expressions (Rhai, CEL)? Config first, expressions only if it proves too rigid.
- ~~Whether the audit log needs tamper-evidence (hash chain).~~ **Resolved:** required. See [global-compliance.md](global-compliance.md) section 5, where the audit trail is the evidence customers rely on for their own conformity obligations.
