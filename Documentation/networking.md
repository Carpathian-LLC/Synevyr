# Synevyr Networking Plan

How nodes find each other, authenticate, and carry workloads. This document covers the threat model, transport selection, the pairing protocol, relay and rendezvous design, and what we support versus document.

Companion to [architecture.md](architecture.md), which sets the constraints this plan works inside: no root, headless by default, loopback-bound, policy enforced in the daemon.

---

## 1. Scope

Not every connection needs this machinery.

**Plain outbound TLS, nothing to build:** any model behind an HTTPS API. Carpathian inference, OpenAI, OpenRouter, a vLLM server on a public host. These are ordinary client requests with pinned TLS and a stored credential.

**The hard path, and the subject of this document:** user-owned nodes that are not publicly reachable. A GPU workstation at home, a box in an office behind corporate NAT, a machine on a phone hotspot. NAT, CGNAT, and firewalls make this the only genuinely difficult case.

Keep the peer-to-peer transport confined to node-to-node links. Do not route API traffic through it.

---

## 2. Threat model

Written first, because every later decision refers back to it.

### Adversaries we defend against

| Adversary | Capability | Defense |
| --- | --- | --- |
| Passive observer | Reads all traffic on the wire | QUIC with TLS 1.3, end to end, no plaintext anywhere |
| Active MITM | Injects, modifies, redirects | Mutual authentication against pinned public keys, not a CA |
| Hostile rendezvous | Carpathian's pairing service is compromised | PAKE means it never sees usable key material and cannot MITM undetected |
| Hostile relay | Carpathian's relay is compromised or subpoenaed | Relays forward packets encrypted to the destination endpoint and cannot read them |
| Pairing code interception | Code leaked over Slack, shoulder-surfed, screenshotted | One guess only, session dies on failure, 60 second TTL, optional SAS confirmation |
| Hostile paired peer | A node we previously trusted turns malicious | Scoped capability tokens, policy enforced daemon-side, immediate revocation |
| Local unprivileged attacker | Another account on the same machine | Socket at 0600, keys in OS keychain or hardware, no secrets on disk |
| Future quantum adversary | Records now, decrypts later | Hybrid post-quantum key exchange on by default |

### What we explicitly do not defend against

Stating these plainly is more useful than implying coverage we don't have.

- **Root or administrator compromise on a node.** If the OS is owned, the daemon is owned. Hardware-backed keys raise the cost of key extraction but do not prevent use of the key while the machine is live.
- **Metadata visible to a relay operator.** A relay that carries your traffic learns which endpoint IDs talk to each other, when, and how much. It cannot read payloads. Users who need to hide the relationship itself should run direct connections or self-host the relay, and we should say so rather than pretend otherwise.
- **A user attacking their own node.** Local policy is a routing guarantee, not a DRM scheme.
- **Traffic analysis of packet timing and volume** on direct connections.

---

## 3. Design principles

1. **Carpathian services are convenience, never dependency.** Every service we operate has a documented path that works without it. This is testable, so we test it: CI runs a pairing and a workload with rendezvous and relay both unreachable.
2. **Identity is a key, not an address.** IP addresses are ephemeral hints. The public key is the stable identity, and it is what authorization binds to.
3. **The transport is swappable.** iroh types never leak past the transport boundary.
4. **Fail closed.** An unverifiable peer, an expired token, or an unsatisfiable region constraint fails the request. It never silently downgrades.
5. **Diagnose rather than instruct.** When connectivity fails, the daemon explains why. We do not ship walkthroughs that ask users to reconfigure their routers.

---

## 4. Node identity

**Key type.** Ed25519. This matches iroh, where endpoint IDs are Ed25519 keys used as the raw public key trust root in mTLS, and avoids introducing a second identity system.

**Generation and storage, in order of preference:**

1. **Hardware-backed** where available: Secure Enclave on macOS, TPM 2.0 on Windows and Linux. The private key is generated inside the secure element and never exists in process memory. Current best practice is that device identity keys live in a hardware root of trust rather than in flash or a config file.
2. **OS keychain** fallback: macOS Keychain, Windows Credential Manager, libsecret via the `keyring` crate.
3. **Encrypted file** as a last resort, for headless Linux with no TPM. Passphrase or a key derived from machine identity, clearly marked as the weakest tier in the console.

Note the honest limitation: Ed25519 in Secure Enclave is not universally available, since Apple's enclave is P-256 oriented. Where hardware cannot hold the Ed25519 identity directly, wrap it with a hardware-held key rather than claiming hardware protection we don't have.

**Node ID display.** The full key is a base32 string. The console and CLI show a short fingerprint (first 8 characters) plus a color-and-word mnemonic for human comparison. Never truncate to fewer than 8 characters in any security-relevant comparison.

---

## 5. Transports

Three, not four. WireGuard is not a transport we implement.

### 5.1 Carpathian routing (default)

iroh over QUIC. Nodes dial by public key. The library attempts a direct UDP hole punch first at roughly 90 percent success, falling back to relays, with about 95 percent of data volume flowing over direct connections in practice.

Security properties that made this the choice:

- All connections are end to end encrypted via QUIC and TLS 1.3.
- Dialing by public key makes connections mutually authenticated, since each endpoint's public key is its TLS identity. There is no certificate authority to compromise or misissue.
- Relay servers forward packets addressed to endpoint IDs and cannot read traffic, because the payload is always encrypted to the destination endpoint. Relays are stateless, which also makes them cheap to run and easy to federate.

### 5.2 Tailscale (detected, offered)

If a tailnet interface is present, offer it. The node is reachable at its tailnet address, and Synevyr uses the direct transport over it. No port forwarding, no root, since userspace mode needs neither.

We do not embed `libtailscale`. It pulls a Go runtime into the binary, threatening the 25 MB budget, and puts a third party's control plane in the trust path, which sits badly next to region-separation guarantees. If a user runs Tailscale, we use it. We do not manage it.

### 5.3 Direct address (advanced)

A reachable `host:port`. This one transport covers LAN, a VPS, a port-forwarded home server, and any VPN the user already runs, WireGuard included.

Even here, identity is still the public key. A direct address is an address hint, and the mTLS handshake still authenticates against the pinned key. An attacker who redirects the address gets a failed handshake, not a session.

### On WireGuard specifically

From Synevyr's perspective WireGuard and direct are the same thing. WireGuard is how a user makes an address reachable. Direct is how we connect to a reachable address.

Implementing it would mean owning key generation, config templating, `AllowedIPs` debugging, MTU issues, and NAT traversal that vanilla WireGuard does not provide, since it has no signaling layer. That is rebuilding Tailscale badly. It ships as a documented recipe under transport 5.3, with the prerequisite stated up front: you need at least one endpoint with a public IP.

### Port forwarding, accurately

The common framing is wrong. Both ends do not need forwarding. **At least one end must be reachable.**

- One side has a public IP: no forwarding anywhere. The NAT'd side dials out and holds the mapping with keepalives.
- Both sides behind NAT with no forward: needs hole punching or a relay. This is what transport 5.1 solves.
- Both sides behind CGNAT: forwarding is not available at all. The user cannot fix this from their router, and most do not know they are behind it.

---

## 6. Cryptography

**Transport.** QUIC with TLS 1.3, via `rustls`. No OpenSSL, so no C memory-safety surface in the TLS path.

**Hybrid post-quantum key exchange, enabled by default.** X25519MLKEM768, combining classical X25519 with ML-KEM. This is the mechanism the public internet standardized on through 2026, Cloudflare's edge prefers it on every site it fronts, every major browser offers it by default, and rustls supports it from 0.23.22.

The reason it matters here specifically: AI workloads carry prompts, documents, and inference results, and harvest-now-decrypt-later is a real threat profile for that content. Classical-only is a fallback for peers that cannot negotiate hybrid, logged as a downgrade in the audit trail.

**Authentication.** Mutual TLS with raw public keys, pinned per node. No CA, no web PKI, no certificate expiry to babysit on the peer link.

**Authorization credentials.** Short-lived and automatically renewed. Current guidance is to keep lifetimes short enough that revocation is a real control rather than a process, and to automate issuance and renewal so no human is in the loop. Node session credentials live 24 hours and renew silently. Revocation takes effect on the next handshake, with active sessions torn down on explicit revoke.

---

## 7. Pairing

The security-critical moment. A user has two machines that have never met, and needs them to trust each other without a shared CA.

### 7.1 Choice of PAKE: CPace

**We use CPace, not SPAKE2.**

This changed after research. SPAKE2 is the well-known choice, and it's what Magic Wormhole uses, but SPAKE2 was **not selected** by the CFRG PAKE selection process, with publication proceeding mainly because variants already exist in Kerberos and elsewhere. CPace is the CFRG's selected balanced PAKE, is on [draft-irtf-cfrg-cpace-21](https://datatracker.ietf.org/doc/draft-irtf-cfrg-cpace/), and is designed for constrained devices and both prime and non-prime order groups. Concerns were raised in the selection process about SPAKE2's internal constants.

Honest tradeoff: SPAKE2 has a more mature Rust ecosystem, including a battle-tested implementation inside `magic-wormhole.rs`. CPace has fewer implementations to choose from. If CPace implementation maturity blocks the schedule, SPAKE2 is an acceptable interim with a written migration path, because both are protocol details behind the same pairing UX. Do not ship both permanently.

### 7.2 Why a short code is safe

The property that makes a six-character code acceptable: an attacker gets **exactly one guess**. A wrong guess fails the PAKE and the session is destroyed. There is no offline dictionary attack, because no verifier crosses the wire. This is the same reasoning behind Magic Wormhole's human-pronounceable codes.

That property is load-bearing and must be enforced server-side too. See rate limiting in section 8.

### 7.3 Pairing flow

```text
NODE A (has console)                RENDEZVOUS               NODE B (joining)
        │                               │                            │
  1.    │ claim mailbox ───────────────▶│                            │
        │◀────── code: 4-ripple-cobalt ─│                            │
        │                               │                            │
  2.    │        user carries code out of band (type, QR, read aloud)
        │                               │                            │
  3.    │                               │◀──── open mailbox w/ code ──│
        │                               │                            │
  4.    │◀═════ CPace exchange over mailbox, code as password ══════▶│
        │       neither side reveals the code; both derive K          │
        │                               │                            │
  5.    │  exchange under K: node IDs, endpoint hints, relay set      │
        │                               │                            │
  6.    │  OPTIONAL: both screens show SAS "amber-falcon-73"          │
        │            user confirms they match                         │
        │                               │                            │
  7.    │  mailbox destroyed. direct QUIC dial, mTLS on pinned keys   │
        │◀══════════════ from here, no rendezvous ═══════════════════▶│
```

**Step 6 is the MITM backstop.** The strongest pattern in the pairing literature is numeric comparison: display a short authentication string derived from the session key on both devices and have the user confirm they match. A MITM produces different values on each side, so the attack is detected rather than merely made difficult, which is why numeric comparison is considered more secure than passkey entry even under physical access assumptions.

Make SAS confirmation **default-on for nodes that will hold credentials or serve regulated regions**, and skippable for a low-stakes local pairing. Do not make it always-optional, and do not make it always-mandatory. Tie it to what the node is authorized to do.

### 7.4 Three ways to pair

1. **Short code.** `4-ripple-cobalt`, human-pronounceable, 60 second TTL, one attempt. Needs the rendezvous.
2. **QR code.** Same payload for phones and headless boxes with a camera nearby.
3. **Offline blob.** Base32 of public key plus endpoint hints, no service involved at all. Long and ugly, and it works when everything of ours is down. This is what makes principle 1 true rather than aspirational.

### 7.5 After pairing

Each node stores the peer's public key, last-known endpoints, and the relay set. Reconnection is direct. **The rendezvous is never contacted again for that pair.**

---

## 8. Rendezvous service

Deliberately small. The less it does, the less its compromise matters.

**What it does:** holds ephemeral mailboxes, relays PAKE messages between two parties, expires them.

**What it never sees:** node private keys, the pairing code, the derived session key, or the contents of step 5. Compromise costs an attacker the ability to disrupt new pairings, not to read or join existing ones.

**Hardening:**

- Mailbox TTL 60 seconds. One open attempt. Wrong code destroys the mailbox, which preserves the one-guess property.
- Rate limits per IP, per ASN, and globally, since code-space exhaustion is the only real attack and it must be bounded.
- No logs beyond aggregate counters. There is nothing worth retaining and plenty worth not retaining.
- Federatable. `--rendezvous <url>` accepts any conformant server, and self-hosting is documented at launch rather than promised later.

---

## 9. Relay

Used when hole punching fails, roughly 5 to 10 percent of connections and higher on mobile and corporate networks.

**Properties inherited from iroh:** stateless, forwards packets addressed to endpoint IDs, cannot read payloads because they are encrypted to the destination endpoint.

**Abuse and DDoS.** UDP-based protocols are exposed to spoofing and reflection, and QUIC amplification can multiply an initial request substantially.

- **Address validation via stateless Retry** on every new connection. This is the standard defense, and it costs a small handshake round trip.
- **Crypto challenges under load.** Escalate to a proof-of-work style challenge when handshake volume crosses a threshold, reducing CPU amplification during a flood.
- **Authenticated relay use.** Only nodes presenting a valid Synevyr credential get relayed, so we are not running open infrastructure.
- **Per-node bandwidth quotas** with visible accounting in the console. Users should never be surprised by relay usage.
- **BCP38** at our own edge, and DDoS absorption in front of the public relays.

**Federation.** Ship with Carpathian relays as default, n0's public relays as secondary, and `--relay <url>` for self-hosting. Users who cannot accept a third party carrying even encrypted metadata self-host, and the docs say so directly.

---

## 10. Agent network ACLs and egress control

An agent with unrestricted outbound network access is an exfiltration channel and the payoff for every prompt injection. Egress filtering is the highest-value control available here, and the April 2026 CSA, SANS, and OWASP "AI Vulnerability Storm" briefing names it the first hardening control in their priority list, noting it blocked every public log4j exploit.

### 10.1 Deny by default, identity-aware

Old-style firewalls key on source IP. That does not work for agents, which move between machines, run in ephemeral environments, and share addresses. Rules bind to the **agent or harness token identity**, not the address it happens to come from.

Every agent gets an explicit allowlist. Anything outside it is refused, logged, and surfaced as a policy violation rather than a connection error, because the distinction matters when reviewing an incident.

### 10.2 Enforcement points

Three layers, each independently sufficient for its own scope:

1. **Plugin capability manifest** (see [architecture.md](architecture.md) section 5.2). WASM plugins have no socket API at all. They call a host function that checks the manifest, so egress policy is not something a plugin can route around.
2. **Agent egress proxy.** All agent-originated HTTP passes through the daemon. The daemon holds the credentials and applies the allowlist, so an agent never opens its own socket to the internet.
3. **Node policy.** Per-node ceilings that no agent policy can exceed, for the case where an operator wants a hard boundary regardless of what harness authors configure.

### 10.3 Rule semantics

```toml
[agent.research-bot.egress]
allow = ["api.anthropic.com:443", "arxiv.org:443"]
deny_override = false          # cannot be widened by the harness
max_distinct_hosts = 10
max_bytes_per_hour = "500MB"
```

- **Exact host and port.** Wildcards are opt-in and flagged in the console, because `*.s3.amazonaws.com` is an exfiltration allowlist wearing a costume.
- **DNS pinned and revalidated.** Resolve at policy-check time and connect to that address. Re-resolving between check and connect is a DNS rebinding hole on the egress side, and it is the same bug class as the inbound one in section 6.
- **Permanent deny list**, not overridable by any policy:
  - Cloud metadata endpoints (`169.254.169.254`, `fd00:ec2::254`, and the equivalents). An agent reading instance credentials is the fastest path from prompt injection to cloud account compromise.
  - Loopback and the daemon's own admin socket, so an agent cannot call the control API it is supposed to be governed by.
  - RFC1918 and link-local ranges unless explicitly granted for a named internal service.
- **Quotas** on distinct destinations, request rate, and bytes. A slow exfiltration to an allowed host is still exfiltration, so volume is part of the policy.

### 10.4 What gets logged

Every denied egress attempt records the agent identity, the attempted destination, the rule that denied it, and the surrounding tool call. Repeated denials from one agent are the clearest available signal of a compromised or injected harness, and the console should treat a burst of them as an alert rather than a log line.

---

## 11. DDoS, firewall, and abuse protection

Native, meaning built into the daemon and relays rather than assumed from an upstream provider. A self-hosted node has no Cloudflare in front of it.

### 11.1 The structural advantage: a closed peer set

The largest defense is architectural rather than a mitigation. A Synevyr node accepts connections only from **paired peers**. An unknown endpoint ID never reaches a handshake, never allocates session state, and never touches the router.

This is worth stating plainly because it is what separates us from the incumbent failure mode. OpenClaw's exposure was an open listening service reachable by anyone who found it. There is no equivalent surface here: the default is loopback-only, and even in peer-to-peer mode the acceptable-caller set is an explicit list the user built by pairing.

### 11.2 Layered inbound protection

| Layer | Control |
| --- | --- |
| Default posture | Loopback only. No inbound surface at all until the user pairs a peer |
| Admission | Unknown endpoint IDs dropped before session state is allocated |
| QUIC address validation | Stateless Retry on every new connection, defeating spoofed-source floods |
| Amplification limit | Never send more than QUIC's permitted multiple of received bytes before validation |
| Handshake flood | Escalating cryptographic challenge once handshake volume crosses a threshold, cutting CPU amplification under load |
| Per-peer limits | Connection attempts, handshake rate, and stream creation rate, all capped |
| Resource ceilings | Max concurrent sessions and a memory ceiling. Backpressure rather than unbounded queue growth |
| Relay edge | BCP38 at our own edge, upstream absorption in front of public relays, per-node bandwidth quotas with visible accounting |

### 11.3 Host firewall

We do not manage the OS firewall, because that requires root and section 3 of [architecture.md](architecture.md) rules it out.

Instead, `synevyr firewall --print` emits ready-to-apply rules for `ufw`, `pf`, `nftables`, and Windows Firewall, scoped to exactly the ports Synevyr uses. The user applies them deliberately. This keeps the no-root promise while still giving operators a correct starting point rather than a blog post they found.

The console shows current inbound exposure in plain language, including which ports are listening, which peers are permitted, and whether anything is reachable from outside the host.

### 11.4 Abuse of our own services

Rendezvous and relay hardening is covered in sections 8 and 9. The principle: our services are authenticated, quota'd, and federatable, so we are never operating open infrastructure that anyone can point at a target.

---

## 12. Degradation ladder

The test of "works regardless of Carpathian's status." Each row is a CI test, not a hope.

| Failure | Behavior |
| --- | --- |
| Rendezvous down | Paired nodes unaffected. Cached keys and endpoints, direct dial |
| Carpathian relays down | Direct connections unaffected, about 95 percent of traffic. Falls to secondary or self-hosted relays |
| All relays down | Direct-capable pairs work. CGNAT-to-CGNAT pairs fail closed with a clear diagnostic |
| New pairing during our outage | Offline blob or QR, no service required |
| Node has no internet | mDNS discovery on the LAN, direct connection |
| Endpoint changed (roaming, DHCP) | Rediscovery via cached relay set, then direct re-punch |
| Both ends CGNAT | Relay required. The one case where a relay is not optional |
| UDP blocked by policy | Relay over TCP 443 |
| Peer key mismatch | Hard fail. Never prompt to accept. Re-pairing is a deliberate act |

---

## 13. Transport interface

Keeping iroh swappable is a risk control, since 1.0 shipped in June 2026 and stable wire format is a commitment rather than a track record.

```rust
#[async_trait]
pub trait Transport: Send + Sync {
    fn kind(&self) -> TransportKind;
    async fn dial(&self, peer: &NodeId, hints: &[EndpointHint]) -> Result<Conn>;
    async fn listen(&self) -> Result<Incoming>;
    async fn probe(&self) -> Reachability;
}
```

Rules:

- iroh types never appear above this boundary. No `iroh::NodeAddr` in the router.
- Every transport passes the same conformance suite: identity verification, cancellation mid-stream, backpressure, roaming, clean teardown.
- `probe()` powers diagnostics and the setup flow.

---

## 14. Diagnostics

The highest-value support feature available, because it converts "it doesn't work" into a screenshot with an answer.

```text
$ synevyr connect --probe
  ✓ Tailnet detected (tailscale0)              → recommended
  ✓ Direct hole punch succeeded (UDP 41641)    → 12 ms
  ⚠ Symmetric NAT detected                     → relay fallback likely
  ✗ No inbound reachability                    → port forwarding will not help
  ℹ Hybrid PQ key exchange negotiated (X25519MLKEM768)
```

Detect symmetric NAT and CGNAT through multi-server STUN comparison **before** anyone is told to touch a router. The console shows, per peer: path taken, direct or relayed, latency, bytes relayed, negotiated cipher suite, and whether PQ hybrid was used.

---

## 15. Support scope

**We write and support:**

- Carpathian routing. Zero configuration, pairing code only.
- Tailscale. Short and accurate: install, `tailscale up`, done.
- VPS as the reachable endpoint. Works every time, and we can make it copy-paste exact because we control the platform.

**We document, user-supported:**

- WireGuard recipe. Prerequisite stated first, working config pair, labeled advanced.
- Direct address on a LAN.

**Deliberately minimized:**

Port forwarding gets one page, unlinked from the setup flow, opening with a CGNAT check and a plain warning. We are positioning against a product whose defining failure was 40,000 internet-exposed instances. A Carpathian-authored guide teaching people to open ports to an AI agent is a headline waiting to happen, and the daemon already refuses to bind externally without auth and TLS configured.

**UPnP and NAT-PMP:** opt-in, off by default, never silent. It works perhaps half the time given how many ISPs and routers disable it. Offer it as a "try this before giving up" step, never as a default, because silently opening ports on someone's router reads badly in a writeup.

---

## 16. Tradeoffs accepted

1. **iroh 1.0 is young.** Shipped June 2026, after four years and 65 pre-release versions, with wire-protocol stability committed and over 200 million endpoint connections per month through its public relays. That is real usage, but not a long track record. Mitigated by section 13, not eliminated.
2. **CPace has a thinner implementation ecosystem than SPAKE2.** We are taking the cryptographically better-vetted choice at some engineering cost.
3. **Relays cost money** when hole punching fails, and self-hosting shifts that cost to users who care.
4. **Relay operators see metadata.** Stated in the threat model rather than buried. Direct connections and self-hosted relays are the answer, and we should not market our way around it.
5. **PQ hybrid adds handshake bytes and a little latency.** Worth it for content with a long confidentiality lifetime.
6. **P2P debugging becomes our support category.** Section 14 is the mitigation, and it is not optional scope.

---

## 17. Open questions

- Does a node's authorization live in its key alone, or in a signed capability document that a peer can verify offline? Offline verification matters if the rendezvous is down during a policy change.
- Hardware attestation: do we ever require a TPM-attested identity for nodes handling regulated regions, or is that a later enterprise feature?
- Do we support multi-hop routing (A reaches C through B), or is that a scope trap? Current lean is no.
- Should the audit log be hash-chained for tamper evidence, given the compliance cases region separation implies? Open in [architecture.md](architecture.md) as well.
- Relay selection policy for region-separated workloads: an EU-only workload must not relay through a US relay, which makes relay geography part of policy rather than an operational detail.

---

## Sources

- iroh: [What is iroh](https://docs.iroh.computer/what-is-iroh), [FAQ and security model](https://docs.iroh.computer/about/faq), [iroh-relay](https://github.com/n0-computer/iroh/tree/main/iroh-relay), [1.0 release coverage](https://www.techtimes.com/articles/318490/20260616/peer-peer-library-iroh-10-ships-dial-devices-key-not-ip-address.htm)
- PAKE: [CFRG PAKE selection](https://github.com/cfrg/pake-selection/blob/master/README.md), [draft-irtf-cfrg-cpace-21](https://datatracker.ietf.org/doc/draft-irtf-cfrg-cpace/), [SPAKE2 draft](https://www.ietf.org/archive/id/draft-irtf-cfrg-spake2-26.html), [magic-wormhole.rs](https://github.com/magic-wormhole/magic-wormhole.rs)
- Post-quantum: [Measurement Study of Post-Quantum Readiness of the Internet, 2026](https://arxiv.org/abs/2606.16473), [Akamai on PQC in TLS](https://www.akamai.com/blog/security/post-quantum-cryptography-implementation-considerations-tls), [hybrid TLS migration](https://quantumoutpost.com/tutorials/51-hybrid-tls-pqc/)
- QUIC abuse: [QFAM crypto challenges](https://arxiv.org/html/2412.08936v1), [Akamai on QUIC flood](https://www.akamai.com/glossary/what-is-a-quic-flood-ddos-attack), [Nexusguard on QUIC amplification](https://www.nexusguard.com/blog/could-quic-turn-into-the-next-most-prevalent-amplification-attack-vector)
- Identity and revocation: [Smallstep on zero trust device identity](https://smallstep.com/blog/ncsc-zero-trust-device-identity/), [wolfSSL on HSM, TPM, and secure enclaves](https://www.wolfssl.com/difference-hsm-tpm-secure-enclave-secure-element-hardware-root-trust/)
- Pairing: [Bluetooth Secure Simple Pairing analysis](https://www.sciencedirect.com/science/article/abs/pii/S2214212618301728), [BLE Secure Connections weaknesses](https://arxiv.org/pdf/1908.10497)
- Tailscale: [tsnet docs](https://tailscale.com/docs/features/tsnet), [userspace networking](https://tailscale.com/docs/concepts/userspace-networking)
