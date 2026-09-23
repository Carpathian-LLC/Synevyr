# Wishlist — What Users Complain About in OpenClaw & Hermes

Aggregated from Reddit/X sentiment analyses, GitHub issue threads, and security research. Each item is a gap someone is actively frustrated by — i.e. a place a competing harness can win.

---

## OpenClaw

### Complaints

**Stability & release churn**
- *"Every single update ships more bugs and more problems than before"* (+305 upvotes). Users report ~25% failure rates on heartbeat messages after updates and week-long integration outages.
- High release velocity is treated as a liability, not a feature — breaking changes force workflow rewrites.

**Memory that doesn't hold**
- Forgets instructions, bleeds data between projects, repeats past mistakes.
- **Context bloat** — drags irrelevant history into current tasks, degrading answers and burning tokens.
- *"I'm having to put way too much time into figuring out how to stop it forgetting stuff."*

**Self-hosting burden**
- The single loudest complaint is infrastructure, not intelligence: Docker, SSH, YAML, and security hardening consume more time than actual workflow building.
- *"Got obsessed with it for a month straight… gave up because it just never ran as expected."*
- No one-click installer; configuration is manual file editing.

**Security — the big one**
- Feb 2026: **40,000+ internet-exposed instances** observed (later scans reported 135,000+), with ~35% flagged vulnerable and many running with **no authentication at all**.
- **CVE-2026-25253** (CVSS 8.8) — one-click RCE; the control UI trusted any gateway URL passed as a query param, so a single malicious link handed over full agent control, *even on localhost-only deploys*. Patched in 2026.1.29 alongside two other high-severity CVEs.
- **Supply chain:** the "ClawHavoc" campaign found 341 malicious ClawHub skills, later scans 800+ (~20% of the registry), mostly delivering Atomic macOS Stealer. Bitdefender measured ~17% of skills actively malicious in one sample week.
- Root cause: designed for *trusted local environments*, then adopted onto internet-facing servers it was never built for. China's national CERT issued a public warning.

**Operational blind spots**
- Opaque resource usage — you have to read logs to know what it's consuming.
- Poor mid-task interruption handling.
- Frequent rate-limit hits with no way to throttle.
- Less flexible model swapping than Hermes.
- Weak multi-agent story: one planning loop rather than delegation to specialists.

### Wish it had

- One-click installer + GUI config (no hand-edited YAML)
- Configurable **rate limiting** — tokens-per-interval and requests-per-interval ([issue #30828](https://github.com/openclaw/openclaw/issues/30828))
- Simplified configuration surface ([issue #74575](https://github.com/openclaw/openclaw/issues/74575)) — power is in the options, but most users never use them correctly
- "Software-style" polished UX rather than tinkerer-grade ([issue #23653](https://github.com/openclaw/openclaw/issues/23653))
- **Secure-by-default deployment** — auth on, narrow network binding, signed/vetted skills
- Skill provenance and registry moderation for ClawHub
- Stable LTS release track separate from the fast channel
- Enterprise basics: telemetry, credential management, stable releases, standardized tool ecosystem
- Memory pruning / project-scoped isolation to kill context bloat
- Visible resource-usage dashboard
- Broader regional channels (Feishu, WeChat)

---

## Hermes Agent

### Complaints

**Self-evaluation is broken (top complaint)**
- The agent grades its own work and almost always passes itself. *"It always thinks it did a good job. ALWAYS. I had it pull water test results from the Indiana DNR site and it jumbled up everything… It thought it kicked ass!"* (+107 upvotes).
- Because the learning loop feeds on these self-assessments, bad outcomes get encoded as good ones.

**Self-improvement overwrites human work**
- Autonomous skill refinement erases user-tuned customizations without asking — unpredictable for power users who invested in tuning.
- Flawed skills get learned: the agent omits hidden preconditions and bakes in incorrect behavior.
- Failed tasks persist into memory and keep steering future runs.

**Immaturity**
- ~11 releases vs OpenClaw's 137 (some sources: 6 vs 82). Stability claims are viewed as unearned.
- Rapid evolution → frequent breaking changes.
- Setup wizard gets stuck in loops requiring repeated restarts.

**Ecosystem gap**
- Far fewer channels and community skills than OpenClaw's 13,700+.
- Requires more upfront decisions (pick an execution backend *and* a model provider).
- No hosting platform, subscription, or marketplace — everything is on you.

**Bugs and rough edges**
- CLI text floats into the wrong conversation section; output stalls then dumps in chunks.
- Progress indicators freeze — work looks dead until you intervene.
- Memory/skill DB grows unbounded; disk and RAM concerns over long runs.
- Telegram/external gateway tokens truncated or misparsed.
- Docker/deployment quirks on non-Linux; missing deps.
- Android/Termux installs unsupported.
- Tool calling degrades badly on 7B-class local models.

**Trust**
- Visible skepticism about astroturfing — the community suspects orchestrated promotion, which colors reception of the stats.

### Wish it had

- **Honest self-evaluation** — real success/failure detection, ideally an independent verifier rather than self-grading
- **Consent before overwrite** — protect manually authored skills; diff-and-confirm on self-improvement
- Memory pruning, size caps, and a way to purge failed-task memories
- Native multi-agent / simultaneous profiles (Profiles landed later; still requested)
- Broader integrations and a real skill marketplace
- Stable release cadence with backward compatibility
- Better small-model support for tool calling
- GUI/dashboard for non-CLI users *(shipped — Hermes Dashboard + desktop app, mid-2026)*
- First-class Android/Termux and non-Linux Docker support

---

## The overlap — what neither does well

1. **Verification.** Both let the agent judge its own output. Hermes fails loudly; OpenClaw fails by forgetting.
2. **Memory hygiene.** Unbounded growth on one side, context bloat on the other. Nobody has scoped, prunable, project-aware memory.
3. **Secure defaults.** Self-hosting means users become sysadmins, and the evidence says they aren't good at it.
4. **Supply chain trust.** Community skill registries are unvetted code execution surfaces.
5. **The setup cliff.** Both lose users to configuration before any value is delivered.

---

## Sources

- [The 20 Biggest Problems with Hermes Agent (Reddit/X analysis)](https://aiagentstore.ai/agentic-ai-and-workflow-automation/en/the-20-biggest-problems-with-hermes-agent-what-thousands-of-reddit-and-x-users-are-actually-struggling-with-ranked)
- [Kilo — OpenClaw vs Hermes, 1,300 Reddit comments analyzed](https://kilo.ai/openclaw/vs-hermes)
- [Bitsight — Risks of Exposed AI Agents](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances) · [Oasis — ClawJacked takeover](https://www.oasis.security/blog/openclaw-vulnerability) · [Sangfor — vulnerabilities to supply chain abuse](https://www.sangfor.com/blog/cybersecurity/openclaw-ai-agent-security-risks-2026) · [Backslash](https://www.backslash.security/blog/openclaw-security-risks-explained) · [The Register](https://www.theregister.com/2026/02/09/openclaw_instances_exposed_vibe_code/)
- [OpenClaw GitHub issues](https://github.com/openclaw/openclaw/issues) · [Composio comparison](https://composio.dev/content/openclaw-vs-hermes-agent)
