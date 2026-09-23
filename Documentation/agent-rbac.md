# Agent Identity and Role-Based Access Control

Agents are principals, not features. They get an identity, a role, a scope of authority, a budget, an approver, and an audit trail. This document defines that model.

Companion to [architecture.md](architecture.md) for the extension model, [action-classification.md](action-classification.md) for how individual actions are graded, and [networking.md](networking.md) section 10 for egress enforcement.

---

## 1. The employee analogy, and where it breaks

Treating agents as employees is a useful design frame. An employee has a name, a role, a manager, a spending limit, systems they can access, an onboarding process, and a termination process. Every one of those maps to something an agent needs and most agent frameworks lack.

Use it for structure. Do not use it for trust.

An employee carries judgment, accountability, and legal liability. An agent carries none of those. The analogy fails in three specific places, and each failure is a design rule:

1. **No probation-to-trust progression.** Do not build reputation scores that widen permissions over time. Hermes's defining complaint is an agent that grades its own work and always passes. An agent that earns privilege from its own track record is the same failure with more steps.
2. **No judgment under novelty.** An employee facing an unfamiliar situation escalates. An agent confidently proceeds. So the default on an unrecognized action is escalation, enforced by the system rather than requested of the model.
3. **The principal can be hijacked mid-task.** No employee has their intent rewritten by a document they read. Agents do. Permissions must therefore hold even when the agent has been fully compromised by injected instructions, which is why every control here is enforced outside the model.

---

## 2. Agent identity

Every agent is a first-class principal with a stable identity, distinct from the human who created it and from the harness process that runs it.

```text
Agent
  id            ed25519 keypair, hardware-backed where available
  name          human-readable, unique per workspace
  owner         the human principal accountable for it
  approver      who receives escalations (may differ from owner)
  role          one named role, see section 3
  attributes    region, data classification ceiling, environment
  budget        spend, tokens, wall-clock, per period
  created / last_active / expires
```

**Identity is not the same as the harness.** A harness process authenticates to the daemon and then acts *as* an agent. One harness may run several agents; one agent may be served by successive harness processes. Authorization binds to the agent, so replacing the harness does not silently inherit privilege.

**Every agent expires.** Default 90 days, renewed deliberately. Orphaned agents with standing credentials are the equivalent of a former employee's badge still working, and expiry is the only control that handles the case where nobody remembers to revoke.

---

## 3. Roles

A role is a named bundle of permissions plus a classification profile. Roles are workspace-scoped, versioned, and diffable.

### 3.1 Built-in roles

Ship a small set that covers most cases, because a system that requires everyone to author roles from scratch will be used with one over-broad role.

| Role | Intent | Autonomy ceiling |
| --- | --- | --- |
| `observer` | Read and report. Cannot change anything | G0 only |
| `researcher` | Read widely, write to its own workspace, call approved APIs | G1 |
| `operator` | Act on defined systems within a budget | G2 with approval |
| `maintainer` | Broad authority over a named scope, including deletes | G3 with approval |
| `custodian` | Manages other agents, roles, and credentials | G3, two-person rule |

Autonomy ceilings reference the consequence grades in [action-classification.md](action-classification.md). The role sets the **ceiling**; the classifier grades the **specific action**. An action graded above the role's ceiling is refused, not escalated, because a role ceiling is a boundary rather than a speed bump.

### 3.2 Role definition

```toml
[role.deploy-bot]
description = "Ships releases to staging, never production"
extends     = "operator"

  [role.deploy-bot.resources]
  repos       = ["synevyr/api", "synevyr/console"]
  environments = ["staging"]              # production absent, not denied
  models      = ["*"]
  regions     = ["us", "eu"]

  [role.deploy-bot.egress]
  allow = ["api.github.com:443", "registry.internal:443"]

  [role.deploy-bot.budget]
  spend_per_day = "25USD"
  tokens_per_day = 2_000_000

  [role.deploy-bot.classification]
  profile   = "strict"
  ceiling   = "G2"
  approver  = "team:platform"

  [role.deploy-bot.constraints]
  hours       = "Mon-Fri 08:00-18:00 America/Chicago"
  max_session = "2h"
  requires_sas_paired_node = true
```

**Absence is denial.** `production` is not listed, so it does not exist for this agent. There is no deny list to keep in sync, and no ordering question about which rule wins.

### 3.3 RBAC alone is not enough

Pure role-based control gets coarse fast: you end up with `researcher-eu-readonly-pii` and a hundred near-duplicates. The working pattern is **RBAC for the baseline, attributes for the refinement.**

The role grants a permission class. Attributes on the request narrow it at evaluation time:

```text
permitted = role.grants(action)
          ∧ region_policy(request.data_region, agent.regions)
          ∧ classification(request.data) ≤ agent.max_classification
          ∧ within(agent.budget)
          ∧ within(role.constraints.hours)
```

This keeps the role count small while letting policy respond to what the request actually touches. Region evaluation is where this connects to [global-compliance.md](global-compliance.md), and it fails closed.

---

## 4. Delegation and subagents

Agents spawn agents. This is where most permission systems quietly break.

### 4.1 Permissions intersect, never union

A subagent receives **at most** what its parent holds. The parent may narrow, never widen.

```text
child.permissions = parent.permissions ∩ requested.permissions
```

Enforced in the daemon, not in the harness. A harness asking for a subagent with broader authority than itself gets an error, not a subagent.

This is the confused deputy problem, and it is the specific mechanism by which an injected agent escalates: it cannot exceed its own authority, so it creates a helper that can. Intersection closes it.

### 4.2 Acting on behalf of a human

When an agent acts for a user, authority is the intersection of the user's rights and the agent's role. An agent working for an administrator does not become an administrator.

```text
effective = user.permissions ∩ agent.role.permissions
```

### 4.3 Delegation depth and provenance

- Maximum depth is a role property, default 2. Unbounded delegation chains are unauditable.
- Every request carries its full delegation chain. The audit log records the chain, not just the leaf, so "which agent did this" is always answerable as "which chain did this."
- Revoking any agent in a chain immediately invalidates everything below it.

---

## 5. No standing privilege

High-consequence authority is granted just in time and expires.

- **Session credentials live 24 hours** with silent renewal, matching the short-lived credential principle in [networking.md](networking.md) section 6.
- **Elevation is temporary.** An agent that needs G3 authority for a migration receives it for a bounded window tied to a specific approved action, and it lapses automatically. There is no permanent elevation grant.
- **Separation of duties.** Roles marked `two_person = true` require a second principal, human or a distinctly-owned agent, to approve. An agent cannot approve its own escalation, and two subagents of the same parent do not satisfy the rule.

---

## 6. Offboarding

Termination has to be immediate and total, because a partially revoked agent is worse than an active one: it looks handled.

`synevyr agent revoke <name>` performs, atomically:

1. Invalidates the agent's credentials
2. Tears down active sessions, including in-flight inference
3. Cascades revocation to every subagent in its delegation tree
4. Cancels scheduled and queued work owned by it
5. Removes cached grants on every paired node, and marks unreachable nodes as pending so they revoke on reconnect
6. Writes a termination record to the audit log

Step 5 matters for the distributed case. A revoked agent must not stay alive on a node that happened to be offline, so nodes verify agent status on reconnect before resuming any cached authority.

---

## 7. Evaluation, done honestly

Agents need performance visibility, and this is exactly where Hermes failed. The rule: **agents do not grade themselves, and grades never change permissions automatically.**

What we measure objectively:

- Task completion as reported by the system executing it, not by the agent describing it
- Approval request rate, and the human approve/deny ratio
- Policy violations, especially denied egress attempts
- Budget consumption against grant
- Error and retry rates
- Time-to-completion distribution

What we do with it: surface it to the owner. A pattern of denied approvals means the role is wrong, either too broad for what the agent should do or too narrow for what it needs. A burst of egress denials means investigate for compromise.

What we never do: let those numbers widen permissions. Permission changes are deliberate human acts, recorded with an actor and a reason.

---

## 8. Console surface

The role model is only real if it is legible. The console shows:

- **Roster.** Every agent, its role, owner, last activity, budget consumed, and pending approvals.
- **Effective permissions.** For any agent, the resolved answer to "what can this actually do right now," including attribute narrowing, not just the role name.
- **Delegation tree.** Live view of parents and children with the chain that authorized each.
- **"Why was this allowed."** For any audited action, the exact rule chain that permitted it. Auditors ask this question, and reconstructing it from logs after the fact is how compliance programs fail.
- **Diff on role change.** Before saving, show which agents gain or lose which permissions. Role edits have blast radius and it should be visible before the save, not discovered after.

---

## 9. Tradeoffs accepted

1. **Setup friction.** Assigning roles is more work than running everything as one all-powerful agent, which is what the incumbents do. We are betting that users who care about region separation also care about this, and that the built-in roles absorb most of the cost.
2. **Intersection semantics surprise people.** "I gave the subagent permission and it still can't" is a support category. Mitigated by the effective-permissions view, which shows exactly which term in the intersection failed.
3. **Roles drift toward over-broad** under delivery pressure, in every system that has ever had them. Mitigated by expiry, periodic access review prompts in the console, and making the effective-permission view uncomfortable to look at when it is too wide.
4. **We do not solve agent-to-agent trust across organizations.** An agent from another company's Synevyr instance is not a principal in yours. Federated agent identity is a real problem and it is out of scope for v1.

---

## 10. Open questions

- Do roles compose (multiple roles per agent) or stay single with `extends` inheritance? Current lean is single, because multi-role permission resolution is where RBAC systems become unexplainable.
- Should agent identity keys be hardware-backed on the node that *runs* the agent, or issued by the daemon that *owns* it? Affects portability across nodes.
- Is there a meaningful "agent group" abstraction, or does `extends` plus attributes cover it?
- How do budgets behave across a delegation tree: does a child draw from the parent's budget, or hold its own allocation? Leaning toward drawing from the parent, so a tree cannot multiply spend.
- Cross-workspace agent lending for the consulting or MSP case, which the current model does not address.
