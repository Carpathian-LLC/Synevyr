# Global Compliance and Jurisdiction

Synevyr routes AI workloads across regions, which makes jurisdiction a routing input rather than a legal footnote. This document defines how jurisdiction is modeled, enforced, and honestly described.

> **This is engineering analysis, not legal advice.** Every claim here needs review by counsel before it appears in marketing, contracts, or documentation. Regulations cited were current as of August 2026 and several are actively changing.

Companion to [networking.md](networking.md) for relay geography, [agent-rbac.md](agent-rbac.md) for attribute-based narrowing, and [architecture.md](architecture.md) for policy enforcement in the daemon.

---

## 1. The division of responsibility

We cannot encode the law of 195 countries, and any product claiming to would be lying. The honest and scalable split:

**The customer defines policy.** They are the data controller. They know their sector, their contracts, and their regulators.

**Synevyr enforces it, provably.** Region constraints are hard routing rules, fail-closed, with an audit trail sufficient to demonstrate compliance after the fact.

We ship policy packs for the jurisdictions that matter most, as a starting point and a convenience. We do not represent them as legal sufficiency. This distinction has to hold in the product copy as firmly as it holds here, because "compliant with GDPR" is a claim no infrastructure product can truthfully make on a customer's behalf.

---

## 2. Residency is not sovereignty

The distinction that most vendors blur, and the one that matters most to us.

**Data residency** means the bytes are physically in a place. Inference runs in Frankfurt.

**Data sovereignty** means the data is outside the reach of another government's legal process. Frankfurt data stays outside US jurisdiction.

These are not the same, and the gap is legal rather than technical. The US CLOUD Act permits US law enforcement to compel American companies to produce data held abroad. If the provider is US-headquartered, the data is exposed to US legal process even when the servers sit in Frankfurt or Zurich.

### 2.1 What this means for Carpathian, stated plainly

Carpathian is a US company. **We can offer EU data residency. We cannot offer EU data sovereignty.** No amount of engineering changes that, because it is a question of corporate jurisdiction rather than infrastructure.

Three consequences we accept and publish:

1. Any customer whose requirement is genuinely sovereignty, not residency, must run Synevyr in **sovereign mode** (section 6) on their own infrastructure with no Carpathian service in the path. The software supports that fully, and it is the correct answer for them.
2. We say this in the docs before a customer discovers it in a due diligence questionnaire. Being the vendor who volunteered the limitation is worth more than the deals it costs.
3. Marketing never uses "sovereign" for the hosted offering. Residency claims only, with the jurisdiction of the operating entity stated.

---

## 3. Jurisdiction tiers

Rather than country-by-country logic, nodes and endpoints carry a jurisdiction tag and each tag maps to a policy pack. Tiers reflect how restrictive the transfer regime is.

| Tier | Character | Examples |
| --- | --- | --- |
| **A. Permissive** | Transfers allowed with contractual safeguards or consent | Singapore, Japan, Hong Kong |
| **B. Conditional** | Transfers allowed subject to a defined mechanism | EU/EEA, UK, Brazil, Canada |
| **C. Restricted** | Specific conditions, consent with disclosure, or approval | South Korea, Philippines, Taiwan, India |
| **D. Localizing** | Storage mandates and security assessments for export | China, Vietnam, Indonesia, Thailand, Russia |
| **E. Prohibited** | Sanctions or embargo. No service | Per OFAC list, see section 7 |

**Unknown jurisdiction defaults to tier D**, the second most restrictive. Conservative defaults are the only safe behavior when the alternative is guessing.

### 3.1 Notes on the tiers that drive design

**EU and UK (tier B).** GDPR does not mandate storage inside the EU. It conditions transfers, permitting them under adequacy decisions, standard contractual clauses, or binding corporate rules. So the enforcement primitive is not "keep bytes in region," it is "only transfer where a valid mechanism exists." Our policy model has to express transfer mechanisms, not just geography.

**EU AI Act.** Full applicability for high-risk systems arrived 2 August 2026, bringing conformity assessment, EU database registration, quality management, technical documentation, and logging obligations, with penalties reaching 15 million euros or 3 percent of global turnover. Synevyr is infrastructure rather than a high-risk system in itself, but customers will build high-risk systems on it. Our obligation is to give them what their conformity assessment requires: complete, exportable, tamper-evident logs of what ran where, on which model, with which data classification. That is a product feature, described in section 5.

**India (tier C).** The DPDP Rules use a negative-list model: transfers are permitted to all destinations except those the government specifically restricts. This is simpler to implement than an allowlist, and the policy pack has to track a list that can change.

**China (tier D).** The most demanding regime we would encounter. Sensitive data must be stored domestically and cross-border transfer requires government approval. Cybersecurity Law amendments effective 1 January 2026 raised penalties to as much as 20 times illegal income. Separately, VPN services require Ministry of Industry and Information Technology licensing, and unlicensed commercial VPN provision is illegal.

**Russia (tier D).** Law 242-FZ requires personal data of Russian citizens to be stored on servers inside Russia.

---

## 4. Jurisdiction as a routing constraint

### 4.1 Every routable thing carries a tag

Nodes, model endpoints, relays, and storage each declare a jurisdiction. Workloads carry a required jurisdiction set and a data classification.

```toml
[policy.eu-restricted]
allowed_jurisdictions = ["eu", "eea"]
transfer_mechanism    = "scc"          # required for any egress from the set
allow_relay           = ["eu"]         # relays are routing, and routing is policy
data_classification   = "personal"
fallback              = "fail"         # never "nearest available"
```

Evaluation happens in the daemon, before a request leaves. It composes with the RBAC attribute narrowing in [agent-rbac.md](agent-rbac.md) section 3.3 and it fails closed. A workload tagged EU-only with no available EU capacity fails with a clear diagnostic. It does not quietly land in Virginia.

### 4.2 Relay geography is policy, not operations

Called out because it is easy to miss. An EU-only workload that falls back to a relay in Ashburn has left the EU, even though the payload stayed encrypted and the relay could not read it. Metadata crossed a border and, depending on the regulator, so did the transfer.

Consequences:

- Relay selection filters on the workload's jurisdiction set before considering latency.
- If no compliant relay is reachable, the connection fails rather than downgrading.
- Operating a hosted offering with regional guarantees means operating relays in each of those regions. That is a real cost, and it should be priced in rather than discovered.

### 4.3 Verifying location, honestly

We cannot cryptographically prove where a machine physically sits. IP geolocation is a heuristic and it is wrong often enough to be dangerous as a control.

What we do instead, in descending order of strength:

1. **Provider attestation** for infrastructure we or a named partner operate, backed by contract.
2. **Hardware attestation** binding a node identity to a specific machine in a known facility, where TPM-based attestation is available.
3. **Corroborating evidence**: latency triangulation and network path observation, used to *detect contradiction* rather than to establish truth.
4. **Operator declaration**, recorded with the declaring identity and timestamp, for self-hosted nodes.

The console shows which basis a node's jurisdiction rests on. A tag backed by a declaration is displayed differently from one backed by attestation, because a customer relying on the former should know they are relying on their own assertion.

---

## 5. Compliance evidence as a feature

Regulated customers do not need us to be compliant. They need us to make *them* provably compliant. The audit trail is the product surface for that.

Every routing decision records: timestamp, workload identity, agent and delegation chain, data classification, source and destination jurisdiction, transfer mechanism relied upon, model and provider, relay path if any, and the policy version in force.

Requirements that follow:

- **Exportable** in a form an auditor accepts, not just queryable in a console.
- **Tamper-evident.** Hash-chained, which resolves the open question carried in [architecture.md](architecture.md) and [networking.md](networking.md). For regulated deployments this stops being optional.
- **Retention configurable** per jurisdiction, since retention limits are themselves regulated and "keep everything forever" is non-compliant in several regimes.
- **Policy versioning.** Records reference the policy version applied, so a customer can demonstrate what the rules were on a given date rather than what they are today.

---

## 6. Deployment modes

Compliance posture is a deployment decision, not a configuration detail.

**Connected.** Carpathian rendezvous and relays available. Best experience, lowest setup. Residency guarantees per region, no sovereignty claim.

**Regional.** Carpathian services pinned to a single region. Nothing crosses the boundary, including pairing and relay metadata. Requires regional infrastructure to exist for that jurisdiction.

**Sovereign.** No Carpathian service in any path. Customer runs rendezvous and relays, or uses direct transports only. Updates fetched manually and verified by signature. This is the answer for tier D jurisdictions, defense, and anyone whose requirement is genuinely sovereignty.

Sovereign mode is not a degraded tier we tolerate. It is the mode that makes "Carpathian services are convenience, never dependency" a testable claim, and CI exercises it on every build.

---

## 7. Export control and sanctions

### 7.1 Encryption export

Published, publicly available open source software is not subject to the EAR. BIS eliminated the email notification requirement for publicly available encryption source code, **except where the software implements non-standard cryptography.**

That exception is a direct design constraint, and it is one we were already satisfying for other reasons:

**Use only standard, published cryptographic algorithms and protocols. Never roll our own.** TLS 1.3, QUIC, Ed25519, X25519, ML-KEM, and a CFRG-selected PAKE all qualify. A clever custom handshake would move us into a materially worse regulatory position on top of being a bad idea cryptographically.

Note the source license here is PolyForm Noncommercial, which is not an OSI open source license. Whether the publicly-available exemption applies to source published under a noncommercial license is exactly the kind of question that needs counsel rather than an engineering guess. Flagged, not resolved.

### 7.2 Sanctions

OFAC compliance is **strict liability**. Not knowing is not a defense.

- Most sanctions carry an exemption for informational materials, which generally covers existing open source code. It does not extend to producing new code on request, providing services, or support relationships.
- Some sanctions target entire countries or regions rather than listed individuals, so screening the SDN list alone is insufficient.
- Practical split for us: published source distribution likely relies on the informational-materials exemption, while **the hosted service, support, and any paid relationship require end-user screening**. Those are different legal footings and should be operated as such.
- Screening belongs in account provisioning, not in the daemon. The software does not geofence itself; the commercial relationship is where the control sits.

### 7.3 Not shipping a VPN

Transport is application-level peer-to-peer, not a virtual private network service. We do not create tunnel interfaces, we do not route arbitrary system traffic, and we do not sell network transit.

This distinction is worth preserving deliberately, because VPN provision triggers licensing obligations in several jurisdictions, including MIIT licensing in China. A design decision made for the no-root constraint turns out to carry a regulatory benefit.

Stated carefully: this is our reading of a category boundary, and whether a regulator agrees is a question for counsel in each jurisdiction where we operate commercially.

---

## 8. Policy packs

Law changes faster than release cycles, so jurisdiction rules ship as **versioned data, not code**.

- Signed, independently updatable, with the active version recorded in every audit entry.
- A pack contains: jurisdiction definitions, permitted transfer mechanisms, retention limits, data classification mappings, and restriction lists.
- Customers can override any pack with their own. Ours is a default, and theirs wins, because they are the controller.
- Pack updates never silently change enforcement. A pack that would newly block existing traffic surfaces a diff and requires acknowledgment, since a compliance update that breaks production without warning teaches people to stop updating.

---

## 9. What we will not do

1. **Claim compliance on a customer's behalf.** We provide enforcement and evidence. Compliance is a property of their whole system.
2. **Use "sovereign" for anything Carpathian operates.** Section 2.1.
3. **Implement key escrow or lawful-access backdoors** to enter a market that requires them. That would compromise every user, not only the ones in that jurisdiction. It also means some markets are closed to the hosted service, and sovereign mode is what we offer there instead.
4. **Geofence the open source distribution** beyond what sanctions law requires of us.
5. **Ship non-standard cryptography**, for the reasons in section 7.1.

---

## 10. Open questions

- Does the PolyForm Noncommercial license affect the EAR publicly-available analysis? Counsel question, flagged in 7.1.
- Which jurisdictions get policy packs at launch? Leaning toward EU/EEA, UK, US, Canada, Australia, Japan, Singapore, and India, with everything else defaulting to tier D.
- Do we operate relays in every region we make residency claims for, or partner? This determines whether regional mode is real at launch or aspirational.
- Is there an offering for tier D markets beyond sovereign mode, and is the compliance cost of entering them worth it at our size? Current lean is no, and sovereign mode is the answer.
- How does data classification get assigned in the first place? Customer-declared is the honest default, but it means a mislabeled workload routes wrongly with full audit-trail confidence. Automated classification is its own accuracy problem.
- EU AI Act: are we ever a "provider" of an AI system component with our own obligations, or always outside the regulated perimeter? Needs counsel, and the answer shapes how much conformity tooling we owe customers.
