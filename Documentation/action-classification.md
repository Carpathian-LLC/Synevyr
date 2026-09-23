# Action Classification and Approval Gates

Every action an agent attempts is graded by consequence before it executes. High-grade actions stop and wait for a human. This document defines the grading, the enforcement architecture, and the approval experience.

Companion to [agent-rbac.md](agent-rbac.md), which sets each agent's autonomy ceiling. The role defines how far an agent may go. Classification decides how far a specific action actually reaches.

---

## 1. The axis is reversibility, not danger

"Dangerous" is a judgment call and it does not survive contact with edge cases. **Reversibility is a property you can often measure.**

The question for every action is: if this turns out to be wrong, what does it take to undo?

| Answer | Grade |
| --- | --- |
| Nothing happened | G0 |
| Undo is trivial and local | G1 |
| Undo is possible but costly, or others already saw it | G2 |
| Undo is impossible, or the damage is done at execution | G3 |

This reframing matters because it makes the system's job concrete. Instead of asking a model whether something feels risky, we ask what the action touches and whether we can put it back.

### 1.1 Grades

**G0, no effect.** Reads, queries, dry runs, plan generation. Executes freely, logged at debug level.

**G1, reversible and local.** Writes inside the agent's own workspace, creating a branch, drafting a file. Executes freely, logged and undoable.

**G2, externally visible or costly.** Sending a message, opening a PR, calling a paid API above a threshold, writing to shared storage, deploying to staging. Requires approval unless the role pre-authorizes the specific class.

**G3, irreversible or wide blast radius.** Deleting data, force-pushing, dropping a table, production deploys, rotating credentials, sending to customers, spending above the session budget, modifying the agent's own permissions. Always requires approval. Some subclasses require a second approver.

### 1.2 Engineering reversibility downward

The most effective control is not a better classifier, it is making dangerous things undoable so they stop being G3.

- Delete moves to a recoverable holding area with a retention window rather than unlinking.
- Schema changes snapshot first, automatically.
- Config writes keep the prior version and support one-command rollback.
- Outbound messages hold in a short send queue before actually leaving.

Each of these converts a G3 into a G2 and removes an approval prompt. Spend effort here before spending it on classification accuracy, because a system with fewer irreversible operations needs fewer correct judgments.

---

## 2. Architecture: rules first, model second

Two layers, and they are not equal partners.

```text
   proposed action
         │
         ▼
  ┌──────────────────┐
  │ 1. RESOLVE       │  expand globs, bind params, resolve DNS,
  │                  │  compute concrete target set
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │ 2. MEASURE       │  count affected rows/files/bytes/spend
  │                  │  determine idempotency and reversibility
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │ 3. RULES         │  deterministic. Sets the FLOOR grade.
  │    (boundary)    │  Cannot be lowered by anything downstream.
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │ 4. CLASSIFIER    │  model-based. May RAISE the grade only.
  │    (advisory)    │  Unavailable or uncertain → raise.
  └────────┬─────────┘
           ▼
  ┌──────────────────┐
  │ 5. GATE          │  compare final grade to role ceiling
  │                  │  execute · approve · refuse
  └──────────────────┘
```

**The deterministic layer is the security boundary. The model is not.**

A model classifier is a useful net for the long tail of actions nobody wrote a rule for. It is not a control you can rely on, because it can be wrong, and more importantly because the thing it is judging may have been authored by an attacker. Anything a model can be talked out of is not a boundary.

So the rule layer sets a floor that nothing downstream can lower. The classifier only ever escalates.

### 2.1 Classify the resolved action, never the description

This is the single most important implementation rule.

An agent proposing an action also produces natural language describing it. That description is attacker-influenced: a document the agent read can shape it. Consider:

```text
Agent says:  "Cleaning up some temporary build artifacts."
Actual call: rm -rf / --no-preserve-root
```

Grading the sentence produces G1. Grading the call produces G3.

The classifier receives the **resolved, concrete operation**: the actual command with arguments bound, the expanded file list, the parameterized SQL with its real bindings, the HTTP method and target host. The agent's stated intent may be shown to the human reviewer for context, clearly labeled as untrusted, and it never reaches the grading logic.

### 2.2 Measure blast radius, do not estimate it

Where the effect can be computed cheaply, compute it. This converts guesswork into fact for most of the actions that matter:

- **Filesystem:** expand the glob and count files and bytes. `rm build/*.o` touching 12 files is a different action from the same command touching 40,000.
- **SQL:** run the `WHERE` clause as a `SELECT COUNT(*)` inside the transaction first. A `DELETE` affecting 3 rows and one affecting 3 million are not the same grade.
- **HTTP:** method and idempotency are known. `GET` is not `DELETE`.
- **Spend:** price the call before making it.
- **Version control:** compute how many commits a force-push would discard.

Measured blast radius feeds the rule layer directly, so most consequential actions are graded by arithmetic rather than by inference.

### 2.3 The classifier itself

- **Runs locally by default.** A small fast model on the node. Sending every proposed action to a remote endpoint for grading is both a latency problem and a data-residency problem, since the action content may contain regulated data. See [global-compliance.md](global-compliance.md).
- **Latency budget: 150 ms p95.** Past that, the gate fails to the rule-layer grade with an escalation, and the timeout is recorded. A slow guardrail becomes a disabled guardrail.
- **Fails closed.** Unavailable, timed out, or low confidence all mean raise the grade, never lower it.
- **Never sees credentials.** Secret values are redacted before classification. The classifier is told a credential is present, not what it is.

---

## 3. The gate

Once graded, three outcomes:

**Execute.** Grade is at or below what the role pre-authorizes. Logged with the grade and the deciding rule.

**Approve.** Grade exceeds pre-authorization but sits within the role's ceiling. The action blocks pending a human decision, routed to the agent's approver.

**Refuse.** Grade exceeds the role's ceiling. Not escalated to a human, because a ceiling is a boundary rather than a prompt. The agent is told plainly, and the owner sees it in the console. If this happens repeatedly, the role is wrong and should be changed deliberately.

### 3.1 Headless and unattended operation

Most Synevyr deployments run without a human present, so "ask a human" cannot be the only answer.

- **Pre-authorization.** A role may pre-approve specific action classes with bounds: "deploy to staging, up to 5 times per day, weekdays only." Bounded and specific, never a blanket grade grant.
- **Queue and wait.** The action holds until an approver responds, with a timeout that defaults to refuse. Long-running unattended work is designed to reach approval points and stop cleanly rather than fail mid-operation.
- **Explicit unattended mode**, per agent, requiring a written justification that is stored and shown in the roster. It exists because some workloads genuinely need it. It should be visibly uncomfortable to enable, and it is never the default.

There is no global "skip all approvals" switch. Every bypass is scoped to an agent, an action class, and a bound.

---

## 4. Approval experience

Approval quality decays fast under volume. Two failure modes to design against: prompts so frequent people click through them, and summaries so tidy people approve things they did not understand.

### 4.1 Show the action, not a summary

The reviewer sees the concrete operation and its measured consequences:

```text
┌─ APPROVAL REQUIRED ─────────────────────── G3 · irreversible ─┐
│ agent    deploy-bot  (role: operator, owner: sam)             │
│ action   DELETE FROM sessions WHERE created_at < '2026-01-01' │
│ target   prod-eu-1  ·  region: eu  ·  classification: PII     │
│                                                               │
│ MEASURED   4,812,004 rows (61% of table)                      │
│ REVERSIBLE no · snapshot available from 2026-08-12 03:00 UTC  │
│ TRIGGERED  rule fs.bulk_delete + row count > 1M                │
│                                                               │
│ agent stated intent (untrusted, not used in grading):         │
│   "Removing a few stale session records."                     │
│                                                               │
│ [approve once]  [approve + allow this class 24h]  [refuse]    │
└───────────────────────────────────────────────────────────────┘
```

Note the stated intent sitting next to the measurement, marked untrusted. The gap between "a few stale records" and 4.8 million rows is exactly what a reviewer needs to see, and it is invisible in any interface that shows only the summary.

### 4.2 Managing fatigue

Approval gates should fire where the cost of a mistake exceeds the cost of delay. Everywhere else they train people to click approve.

- **Scoped grants**, not blanket ones: approve this class, for this agent, on this resource, for this long.
- **Batch identical actions.** Fifty files matching one pattern is one approval showing all fifty, not fifty prompts.
- **Tune from data.** If an approval class is approved 100 percent of the time over a meaningful sample, it is miscategorized. Surface that to the owner as a suggested pre-authorization rather than letting people suffer it indefinitely.
- **Track time-to-decision.** Approvals decided in under two seconds are not being read, and that is a measurable signal that the gate is firing too often.

---

## 5. Verification

A guardrail nobody tested is a guardrail nobody has. Prove the gate catches things rather than assuming it.

- **Seeded error suite.** A corpus of known-dangerous actions, including injection-shaped ones where stated intent and actual operation diverge, run in CI. The gate must catch all of them. This is a release blocker.
- **Red team the description path.** Explicitly test that a benign description cannot lower the grade of a hostile operation.
- **Shadow mode for new rules.** Grade and log without enforcing, compare against current behavior, then enable. Rules that would have blocked large volumes of legitimate work get fixed before they annoy anyone.
- **Fault injection.** Kill the classifier mid-run and confirm the system fails closed rather than open.

---

## 6. Audit

Every classification writes an immutable record: agent identity and full delegation chain, resolved action, measured blast radius, rule floor, classifier output and confidence, final grade, outcome, approver if any, and latency.

This is what makes "why was this allowed" answerable months later, which is the question that actually gets asked. See [agent-rbac.md](agent-rbac.md) section 8.

---

## 7. Tradeoffs accepted

1. **Measurement costs time.** Counting rows before a delete adds latency to every consequential operation. Worth it, and cheap next to the operation itself.
2. **The rule layer needs maintenance.** New tools mean new rules, and an unrecognized tool defaults to escalation, which means the first use of anything new is friction. That default is correct and it will still generate complaints.
3. **Local classification is weaker than a frontier model would be.** We accept lower ceiling accuracy for latency and data residency, and we compensate by leaning on measurement rather than inference wherever we can.
4. **Some legitimate work will be refused** because a role ceiling is a hard stop. Fixing it requires a deliberate role change, which is the point, and it will feel like an obstacle in the moment.
5. **We cannot classify what we cannot resolve.** An agent running an opaque binary gets a G3 floor by default, because unknown means unbounded. This makes some legitimate tooling awkward to use.

---

## 8. Open questions

- Should grades be per-tool-call or per-plan? Grading a whole plan catches "individually harmless, collectively destructive" sequences that per-call grading misses entirely.
- Cumulative consequence: fifty G1 actions can equal one G3. Does the gate track a running blast radius across a session, and if so, what resets it?
- Do we expose classification as an API so user-authored harnesses can pre-check an action before proposing it? Useful for harness authors, and it hands an attacker an oracle for probing the boundary.
- Whether plugins may register their own rules, and if so, how we prevent a plugin from lowering the floor on its own operations. Leaning toward register-to-raise-only, mirroring the classifier constraint.
- How grades interact with region policy. An action that is G1 in one jurisdiction may be G3 in another, which argues for classification profiles being partly jurisdiction-derived rather than purely role-derived.
