# Status / workflow model

> **Status: RESOLVED (`JN-D1`).** This document is the canonical specification of
> the `jira_nano` status/workflow model. It supersedes the earlier draft.

## Principles

- **Jira-conventional.** The model follows established Jira workflow conventions;
  it does not invent bespoke mechanics.
- **Fully user-configurable.** States, transitions, guards, git-host event
  mappings, and icons/colors are all defined in a config file. The set below is
  only the built-in **default** — a user may replace it entirely (e.g. add a
  `blocked` or `qa` state).
- **Strictly enforced.** Once configured, the workflow is a strict state machine.
  Only transitions declared in the config are legal; any other transition is
  rejected. **There is no force/override bypass** — the configured state machine
  is always honored.

## Default states

| State | Meaning | Icon | Telegram topic color | Terminal? |
|-------|---------|------|----------------------|-----------|
| `todo` | Ready to start | 📋 | yellow | no |
| `in-progress` | Being worked on | 🔧 | purple | no |
| `in-review` | Under review (e.g. MR/PR open) | 👀 | pink | no |
| `done` | Completed and verified | ✅ | green | yes (completed) |
| `archived` | Closed without completion | 📦 | red | yes (archived) |

- **Initial state:** `create` produces a ticket in `todo`.
- Each state binds to one of the six native Telegram forum-topic colors (see
  §Telegram rendering).

## Default transitions

```
todo        → in-progress | archived
in-progress → in-review | todo | archived
in-review   → done | in-progress | archived
done        → todo        (reopen)
archived    → todo        (revive)
```

- **Initial:** `todo`.
- Any non-terminal state may move to `archived`.
- Terminal states are **reopenable** via the explicit transitions above:
  `done → todo` (reopen) and `archived → todo` (revive). Git history records the
  reopen; no separate flag is needed.

## Terminal semantics: `done` vs `archived`

Two **distinct** terminal states rather than one "closed" bucket — this keeps the
board columns and Telegram colors unambiguous.

- `done` — completed and verified. No resolution needed.
- `archived` — closed without completion, carrying an optional `resolution`
  field: `wontfix` | `duplicate` | `obsolete`.

## Transition guards

A guard is a precondition without which a transition is rejected (a Jira-style
transition validator). The default workflow ships **one** guard:

- `in-progress` requires an `assignee` — you cannot start work with nobody
  assigned.

Guards are configurable; no other transition is gated by default. In particular,
`in-review` does **not** require an MR/PR link, so review of non-code work (design
discussion, manual checks) is not blocked.

## Git-host event → transition map

Events name a **target status**; the service advances the ticket **forward along
the legal transition path** to reach it, never performing an illegal jump.
Backward moves happen only via explicit events. Default map (symmetric across
GitLab/GitHub):

| Event | Target |
|-------|--------|
| `mr_opened` / `pr_opened` | `in-review` |
| `mr_merged` / `pr_merged` | `done` |
| `mr_closed` / `pr_closed` (unmerged) | `in-progress` |

- **Forward auto-advance.** If an event targets `in-review` on a `todo` ticket,
  the service walks `todo → in-progress → in-review` (each step legal) rather than
  jumping or stalling. If the target is unreachable by a forward legal path from
  the current state, the event is **skipped and a note is posted** to the ticket
  — never forced.
- **Guard interaction.** When forward auto-advance would cross the `in-progress`
  assignee guard on an unassigned ticket, the service **auto-assigns the MR/PR
  author** (the person actually doing the work) so the guard is satisfied
  legally. The map itself is configurable.

## Validation

- **Strict, no exceptions.** An illegal transition (one not declared in the
  configured `transitions`, or one failing a `guard`) is a **hard error**.
- **No force override.** There is no bypass; callers cannot perform an
  undeclared transition. Git history (one commit per transition, with a
  Conventional-Commit message referencing the ticket id) is the audit trail.

## Configuration

- The default workflow is **built in** but is **only a default**.
- It is overridable **per repository** via `.jira_nano/workflow.yaml` in the
  ticket-store repo — versioned like everything else, so the workflow definition
  is itself part of the audit trail. One workflow per repository/project.
- A user may redefine the full set of states (including adding states such as
  `blocked` or `qa`), transitions, guards, event mappings, and icons/colors.

### Config shape

```yaml
workflow:
  initial: todo
  states:
    - {name: todo,        icon: "📋", color: yellow}
    - {name: in-progress, icon: "🔧", color: purple}
    - {name: in-review,   icon: "👀", color: pink}
    - {name: done,        icon: "✅", color: green}
    - {name: archived,    icon: "📦", color: red}
  transitions:
    todo:        [in-progress, archived]
    in-progress: [in-review, todo, archived]
    in-review:   [done, in-progress, archived]
    done:        [todo]        # reopen
    archived:    [todo]        # revive
  terminal: [done, archived]
  guards:
    in-progress: {require: [assignee]}
  events:
    mr_opened:  in-review
    pr_opened:  in-review
    mr_merged:  done
    pr_merged:  done
    mr_closed:  in-progress
    pr_closed:  in-progress
```

The service layer loads this once. Every `transition` call is validated against
`transitions[current]` (and any `guards[target]`) before writing to Git; nothing
else is permitted.

## Telegram rendering

- **Topic color** is taken from `state.color`. The Bot API exposes exactly six
  native forum-topic colors, so each state binds directly to one — always
  available, no special stickers required.
- **State icon** (emoji) is rendered as a prefix in the topic title and in update
  posts.
- Note: arbitrary emoji as a *native topic icon* is **not** reliably available
  (the Bot API limits topic icons to `getForumTopicIconStickers`), so color +
  in-text emoji is the mechanism rather than custom native icons.

## Impact on the ticket schema (`JN-D3`)

This decision introduces one frontmatter field consumed by the workflow —
`resolution` (enum, set on `archived`). The full frontmatter schema remains open
under `JN-D3`.
