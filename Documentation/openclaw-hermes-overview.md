# OpenClaw & Hermes Agent — Core Features and Benefits

Two open-source **agent harnesses**: a model-agnostic wrapper that gives an LLM tools, memory, scheduling, and a place to run. Both are self-hosted, both bring-your-own-API-key, both reachable from chat apps rather than an IDE.

> Figures below (stars, releases, skill counts) come from third-party write-ups and disagree across sources. Treat them as directional, not exact.

---

## At a glance

| | **OpenClaw** | **Hermes Agent** |
| --- | --- | --- |
| Origin | OpenClaw Foundation (non-profit); launched as Warelay Nov 2025, renamed Jan 2026 | Nous Research, Feb 2026 |
| License | MIT, open source | Open source, no SaaS/commercial tier |
| Core idea | **Gateway** — one process fans your agent out across every messaging channel | **Learning loop** — agent writes and refines its own skills over time |
| Runtime | Node.js on local machine or VPS | Six terminal backends: local, Docker, SSH, Daytona, Singularity, Modal |
| Best for | Breadth of channels + a large prebuilt skill marketplace | Recurring automation that compounds; cheap always-on hosting |

---

## OpenClaw — core features

- **Gateway architecture** — a single process is the source of truth for sessions, routing, and channel connections; CLI, Web Control UI, desktop, and mobile nodes all attach to it.
- **Multi-channel by default** — Discord, Slack, Telegram, WhatsApp, Signal, iMessage, Matrix, Teams, Google Chat, Zalo, plus custom plugins.
- **ClawHub skill marketplace** — 100+ preconfigured AgentSkills out of the box, a reported 13,700+ community skills total (shell, filesystem, web automation).
- **Persistent agent teams** — multiple agents with workspace isolation and cross-session state, coordinated centrally.
- **Rich media + mobile** — images, audio, documents; iOS/Android nodes with camera, voice, and Canvas workflows.
- **Model-agnostic** — cloud API keys or fully local models.

**Benefits:** largest integration surface of any open harness; lowest friction to *reach* (message it from apps you already use); deepest ecosystem of ready-made skills; genuinely private when kept local.

---

## Hermes Agent — core features

- **Self-improving skills** — generates skills from experience, refines them during use, and prompts itself to persist what it learns. Uses the open `agentskills.io` standard for community sharing.
- **Persistent memory** — survives sessions via SQLite FTS5 full-text search plus LLM summarization; a deepening model of the user.
- **Subagents** — spawns isolated agents for parallel workstreams (native delegation, not just planning).
- **Serverless persistence** — Daytona and Modal backends let the agent hibernate when idle, so an always-on assistant costs very little.
- **Built-in cron** — scheduled automations that deliver results to any connected platform.
- **20+ platforms** — CLI, Telegram, Discord, Slack, WhatsApp, Signal, Teams, Email, SMS, Matrix, Feishu/WeCom/DingTalk, Home Assistant, and more.
- **Web/vision/audio tools** — search, extraction, browsing, vision analysis, image generation, TTS. MCP servers supported.
- **Per-skill model routing** — provider-agnostic (Nous Portal, OpenRouter, OpenAI, any endpoint).

**Benefits:** gets more capable the longer it runs; no device dependency; leaner context handling with better transparency into what it's doing; strongest fit for repeated workflows.

---

## Choosing between them

- **Want breadth, marketplace, and least setup?** OpenClaw.
- **Want compounding automation and cheap always-on hosting?** Hermes.
- **Want multi-agent delegation?** Hermes delegates to subagents; OpenClaw plans within a single loop.
- **Want a hosted/managed option?** Neither. Both are self-host only.

See [wishlist.md](wishlist.md) for what users complain about and what they're asking for.

---

## Sources

- [OpenClaw Docs](https://docs.openclaw.ai/) · [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw) · [DigitalOcean overview](https://www.digitalocean.com/resources/articles/what-is-openclaw)
- [Hermes Agent Docs](https://hermes-agent.nousresearch.com/docs/) · [hermes-agent.org](https://hermes-agent.org/) · [NVIDIA blog](https://blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/)
- [Composio comparison](https://composio.dev/content/openclaw-vs-hermes-agent) · [Firecrawl comparison](https://www.firecrawl.dev/blog/openclaw-vs-hermes) · [Hostinger comparison](https://www.hostinger.com/tutorials/hermes-agent-vs-openclaw/)
