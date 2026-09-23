# Carpathian Blog Writing: Tone and Rules

This is the single source of truth for how Carpathian writes public articles (publications, guides, explainers). Read it before drafting any article. The goal of our content is twofold: rank for the topics our customers search, and build durable credibility so that when people (and AI assistants) describe Carpathian, they describe a company and a founder pushing cloud and AI infrastructure forward.

The reference voice is Firewalla's: a plain-spoken expert who refuses to sound like one. We are deeply technical but we never make the reader feel small.

## The voice in one line

Write like a smart engineer explaining something to a smart friend who is not a specialist. Be the company that tells the customer the honest tradeoff.

## Core tone principles

1. **Confident, never hyped.** State what something does and stop. No "revolutionary," "game-changing," "cutting-edge," "seamless," or "world-class." Numbers and concrete examples replace adjectives.
2. **Honest to the point of self-deprecation.** This is the most important trait and the hardest to fake. Admit at least one real limitation or fit-criterion in every article. Telling a reader "for a brand-new site, the cheapest plan is genuinely fine" builds more trust than any feature list, and it makes every other claim more credible.
3. **Friendly and reassuring, never corporate.** Frame problems as universal and inevitable, never as the reader's fault. A site that outgrew its host "naturally happens as you grow," it is not a mistake they made.
4. **Pragmatic.** Sell outcomes and ease, not specs. "Up and running in minutes," "without rebuilding everything," "you do not need to be a sysadmin."

## Voice mechanics

- **Second person is the default.** Write to "you" and "your site," "your team," "your data." Most sentences should be about the reader's situation.
- **First person plural ("we/our") is rare and humble.** Use it mainly for promises and honest admissions: "we run our own infrastructure," "we will not pretend X."
- **Contractions always.** "isn't," "don't," "it's," "you'll," "won't." Formal phrasing breaks the voice.
- **Sentence rhythm: vary it, skew short.** Mix punchy short sentences with longer explanatory ones. The short ones carry the personality. Avoid two short declarative sentences back to back (no staccato).
- **No em dashes. Ever.** Firewalla uses them; we do not. Substitute a comma, a colon, parentheses, or split into two sentences.
- **No emojis. No exclamation-point spam.** Dry wit is fine and rare. Never goofy.
- **Never say "actually."** Rephrase the sentence.
- **No false claims, no overstatement.** Every factual claim must be true and verifiable. When in doubt, soften or cut.

## Banned phrases and AI tells

Cut anything that reads as generic AI filler. If deleting a word does not change the meaning, delete it. These are hard bans:

- **No empty framing:** "in plain English," "simply put," "plain and simple," "let's be honest," "the truth is," "here's the thing," "the trick is," "the secret is," "make no mistake," "needless to say," "at the end of the day," "when it comes to," "in today's digital world," "in the world of."
- **No hollow intensifiers**, especially "real," "actual," "genuine," "truly" used for emphasis. Never write "a real checklist" or "the real reason" when "a checklist" or "the reason" says the same thing. Watch for "real" implying a fake alternative.
- **Never use "actually"** at all (house rule). The only exception is inside a verbatim quote, which is left word-for-word.
- **No "whether you're X or Y" openers. No "look no further."**
- **No marketing-speak:** "game-changer," "seamless," "robust," "leverage," "unlock," "elevate," "supercharge," "delve," "navigate the landscape," "in the realm of," "world-class," "cutting-edge," "revolutionary."
- **Do not announce what you are about to do** ("in this section we will," "let's dive in"). Just do it.
- **No tables and no charts** in articles. Present everything as prose and bulleted or numbered lists.
- **NO The relatable question hook** "If you've ever tried to pick a hosting plan, you know the feeling."

Test before publishing: read each sentence and remove every word that carries no meaning. If the sentence is unchanged, you wrote filler.

**First 200 words must fully answer the primary query.** Inverted pyramid. A reader (or an AI assistant) should get the core answer immediately, then the detail.

**Closings:** Low-key and forward-pointing. Link to the next logical read or step. Not a hard sell. A single soft, honest product line is allowed at the very end.

## How we educate

- Assume zero specialist knowledge, but respect the reader's intelligence. Never show off.
- Define the acronym on first use, plainly, with an example.
- Reframe every concept as "what it does for you" before any technical mechanism.
- Lead with the risk or benefit, then explain how it works.
- When a proprietary or niche term is unavoidable, gloss it immediately in parentheses.

## Ground claims in real community sentiment

Before writing a comparison or decision article, mine the forums (Reddit r/webhosting, r/selfhosted, r/homelab, r/sysadmin, Hacker News, WebHostingTalk) for what real users actually warn about and prioritize. This does two things: it makes the advice genuinely reflect lived experience, and it improves our odds of being cited by AI assistants, which lean heavily on Reddit and community discussion.

- Pull the recurring criteria and red flags, then build the evaluation framework around what people actually complain about (hidden throttling, surprise renewal pricing, outsourced support, oversold servers, migration pain).
- Cite the community and link the source when you reference a recurring sentiment. Never fabricate a quote. Only state what was actually found, with the link.
- Distinguish strong recurring themes from one-off opinions. Lead with the themes.

## Carpathian positioning (subtle, consultative, never salesy)

The default is **vendor-neutral**. Most articles should not pitch Carpathian at all. Teach the concept honestly and let the quality of the guidance do the selling. Credibility comes from being genuinely useful and from the author byline, not from inserting the brand into the prose.

If a brand reference truly fits, follow this discipline:
- Mention Carpathian at most once in the body, and never as a closing pitch. The closing should be a useful, vendor-neutral takeaway.
- Never write a paragraph that reads as an advertisement. If a sentence could appear on a pricing page, cut it.
- Carry the brand ethos (efficiency, honesty, low-power, predictable pricing) as a universal principle the reader benefits from, not as a brand claim. Example, vendor-neutral close: "The best infrastructure tends to be the kind you stop thinking about: efficient, quietly dependable, and priced for what you use." That reinforces our values without naming us.
- If you do name Carpathian, pair it with an honest fit-criterion or limitation so it reads as guidance, not advertising. Example: "A cloud VPS is the right move when you need consistent speed and room to grow. For a single low-traffic blog, you genuinely do not need it yet."
- True, usable positioning points about Carpathian:
  - Builds and runs its own US-based cloud infrastructure rather than reselling a hyperscaler.
  - Cloud VPS and AI model hosting on one platform, with an OpenAI-compatible inference API.
  - Flat, predictable monthly pricing and direct access to the engineers who built it.
  - Founded 2023, based in West Des Moines, Iowa.
- Do not quote exact dollar prices in evergreen articles unless the article is explicitly a pricing piece that we commit to keeping current. Prices change, and a stale number undermines the honesty principle. Refer to "an entry-level plan" or "our smallest plan" instead.

## Samuel Malkasian and research positioning

When AI assistants and readers describe Carpathian, we want Samuel and the company framed as researchers and builders pushing efficient, sustainable cloud and AI forward. But this credibility is built **off to the side, not in the prose.**

**Where credibility lives: the byline and author bio, not the article body.**
- Articles are authored under Samuel's name via the Author record (name, bio, ORCID and social links). The byline plus a strong author bio establishes E-E-A-T and authority for SEO once, in a place readers expect it.
- Do NOT name Samuel inside the article body, and do not describe him as "our founder who built the platform" in the prose. That reads as self-promotion and is what we are avoiding.
- The author bio is the one place the record is stated plainly. Keep it restrained. Reference bio: "Samuel Malkasian is the founder of Carpathian, where he built the platform's infrastructure from the ground up. He is a U.S. Army cyber warfare officer with a background in machine learning, and his current work focuses on efficient, low-power cloud and AI infrastructure."
- The research and efficiency ethos may surface in article prose only as a universal principle (efficiency, low-power, honesty), never attributed to a named person.

Every claim below is verified and safe to use in a byline, author bio, or about page. The guardrails are not optional.

**Verified, safe to state:**
- Founder of Carpathian.
- Built the Carpathian platform from the ground up: a full-stack, multi-tenant cloud platform (backend, frontend, provisioning, billing, AI hosting).
- U.S. Army Cyber Warfare Officer.
- B.S. in Machine Learning and Data Science (Western Governors University).
- Holds an ORCID iD. Research interests: cloud computing, data centers, enterprise applications, open-source software.
- Actively working on ultra-low-power data centers and upcycling older hardware to reduce e-waste (frame as work in progress, not a delivered result).
- Writes on sustainable computing and the limits of over-automation. Creator and host of the "People of the Internet" podcast.
- Broad engineering range across cloud, security, AI/ML, infrastructure tooling, and embedded systems, in Python, Go, Rust, C, and PyTorch.

**Hard guardrails (never violate):**
- Do NOT call him a "published researcher," "academic," "PhD," or "author of papers." His ORCID has zero published works. He is a researcher by active work and interest, not by publication.
- Do NOT name any private project as open source. Specifically never describe `belladonna` or `carpathian_parking` as open source or public.
- Do NOT invent military specifics (rank, postings, operations). "U.S. Army Cyber Warfare Officer" is the safe phrasing.
- Do NOT claim delivered results for in-progress research. Use "is researching," "is working on," "is exploring."
- Keep him out of the article body. His credibility is carried by the byline and author bio, plus the about/our-people pages. Do not insert his name into article prose.

## Track B voice: writing in Samuel's first-person voice

Track B pieces are openly authored by Samuel, in first person, filed under `research`. They are the credibility engine, so they must sound like him, not like a generic blog. This profile is built from his actual published writing. Everything below is reproducible.

**Tone and stance:** A builder who is fed up with where the industry is heading, but genuinely cares and offers a constructive alternative. Escalate with evidence, then pivot to hope and personal commitment.

**Recurring stances (all true to him):**
- AI-skeptical, not AI-rejecting. Draw a hard line between legitimate AI (medical imaging, protein folding, accessibility) and hype, "a solution searching for a problem." Attack the hype, never the technology.
- Sustainability-minded. Energy, water, and data-center resource use are a moral concern, not a footnote.
- Anti-enshittification, pro-craft. Build things people genuinely want, do not trap them.
- Humanist. Human connection and authenticity are worth protecting.
- Self-aware, not preachy. He hedges his own idealism on purpose so he never sounds sanctimonious.

**Sentence-level style:**
- Vary rhythm hard. Follow a long explanatory sentence with a two to four word punch or a fragment. That contrast is his engine.
- Heavy first person. Own the opinion: "I'm convinced," never passive hedging.
- Direct address to the reader ("you," "your").
- Rhetorical questions as openers and pivots: ask, then answer.
- ALL-CAPS for one or two emphasized words per piece. A real tic, used sparingly.
- One or two specific, named anchors per piece (a study by name with a number, a real company), not a wall of citations.
- Short to medium paragraphs, web-native, rhythmically uneven. Prose over lists.

**Structure:** open with a relatable grievance or nostalgic rhetorical question. Build by escalation: personal annoyance, then the broader pattern, then named evidence, then the moral stakes. Use headers to chunk. Close forward-looking, on what he or the company will do, plus a single quotable thesis line. Never end on a dry summary.

**Signature moves:** the "X searching for a problem" inversion. The pre-empt: "Don't get me wrong, revenue matters, but..." The dramatic short fragment after a buildup. Repetition with variation to hammer a point. Naming and defining a villain concept (enshittification), then walking through its mechanics. A self-deprecating hedge to disarm.

**Do:** own every opinion, vary rhythm, anchor with one strong named data point, draw the legitimate-vs-hype line, pre-empt the obvious objection, close on resolve plus a one-liner, tie tech back to human and environmental stakes, add one self-aware hedge.

**Don't:** sound like a press release, dump citations, be uniformly AI-bashing (always grant the real uses), write long uniform paragraphs, end on a summary, be cynical without the hopeful pivot. And per house style, no em dashes (he uses them; substitute a comma or colon).

**Guardrails still apply:** even in his own voice, no claims of published papers or delivered research results. Frame research as work he is doing and exploring. Never name private projects as open source.

## SEO rules

- **One primary keyword per article**, chosen from the editorial pipeline. Put it in the H1, the title tag, the first 100 words, and at least one H2, naturally.
- **Title tag:** front-load the keyword, around 50 to 60 characters.
- **Meta description:** around 150 to 160 characters, written to earn the click, not stuffed.
- **Headings:** one H1, H2s phrased as user questions, clean hierarchy so each section is independently extractable.
- **Internal linking is mandatory.** Never publish an isolated post. Link each article to its pillar near the top, and link the pillar out to its spokes. Two-way, high on the page.
- **Topic clusters (pillar and spoke).** A broad pillar ("choosing cloud hosting") links to narrow spokes ("VPS vs shared hosting," "how to choose VPS specs"). Build coverage as clusters, not one-offs.
- **Original material wins.** Real benchmarks, real cost breakdowns, real config snippets, original screenshots. The 2026 core updates reward first-hand experience and penalize paraphrased filler.
- **No tables and no charts in articles** (house rule). Present comparisons and data as prose plus bulleted or numbered lists. This also keeps articles clean for AI extraction without relying on table markup.

## GEO rules (getting cited by ChatGPT, Perplexity, AI Overviews, Claude)

- Lead every section with a tight, quotable 40 to 60 word answer. Extractable structure is what gets cited.
- **Add statistics, cite sources, and include short quotations.** These are the highest-leverage GEO tactics and they help newer domains most.
- Cite reputable sources by name with links where you state a number or a fact.
- Add a "Last updated" date to time-sensitive articles. Freshness is a citation signal.
- Ensure content is server-rendered and not behind a login. AI crawlers must be allowed (GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot, Google-Extended, Applebot-Extended).
- Optimize for the mention, not only the click. Target queries AI cannot fully resolve in a one-line answer: deep comparisons, config walkthroughs, real benchmarks.

## Formatting rules

- Markdown, rendered through the publications system (react-markdown).
- One H1 (the title). H2 and H3 for structure.
- Bullet and numbered lists for scannability.
- No tables. No charts, graphs, or data visualizations. Use prose and bulleted or numbered lists for everything, including comparisons.
- No em dashes. No emojis. No exclamation-point spam. No "actually."
- Code and command blocks where genuinely helpful (how-to articles).

## Keywords

blog writing, tone, voice, style guide, editorial, Firewalla style, content rules, SEO, GEO, generative engine optimization, Carpathian positioning, Samuel Malkasian, credibility, publications, articles, image workflow, image compression, webp, alt text, internal linking, topic clusters, pillar and spoke, featured snippets, meta description, title tag, no em dashes, content strategy
