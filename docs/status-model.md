# Status / workflow model

> **Status: RESOLVED (`JN-D1`).** This document is the canonical specification of
> the `jira_nano` status/workflow model. It supersedes the earlier draft.

## Goal

A **configurable** workflow: a set of states and the allowed transitions between
them, defined in a versioned config file, validated by the service layer on every
mutation, and mirrored to Telegram. Terminal states close/archive a ticket.

## States

| State | Meaning | Icon | Telegram topic color | Terminal? |
|-------|---------|------|----------------------|-----------|
| `backlog` | Captured, deprioritized | 🗒️ | blue | no |
| `todo` | Ready to start | 📋 | yellow | no |
| `in-progress` | Being worked on | 🔧 | purple | no |
| `in-review` | Under review (e.g. MR/PR open) | 👀 | pink | no |
| `done` | Completed and verified | ✅ | green | yes (completed) |
| `archived` | Closed without completion | 📦 | red | yes (archived) |

- **Initial state:** `create` produces a ticket in `todo` — new tickets are
  immediately ready to start, with no separate planning step. `backlog` is
  reachable by moving a `todo` ticket back down when it is deprioritized.
- The six Telegram topic colors map 1:1 onto the six states (see §Telegram
  rendering).

## Transitions

```
todo        → in-progress | backlog | archived
backlog     → todo | archived
in-progress → in-review | todo | archived
in-review   → done | in-progress | archived
done        → todo        (reopen)
archived    → backlog     (revive)
```

- **Initial:** `todo`.
- Any non-terminal state may move to `archived`.
- Terminal states are **reopenable** via the explicit transitions above:
  `done → todo` (reopen) and `archived → backlog` (revive). Git history records
  the reopen; no separate flag is needed.

## `blocked` is a flag, not a state

"Blocked" is **orthogonal** to pipeline position: a ticket can be blocked while
`in-progress` or `in-review`. Modeling it as a state would lose the "where in the
pipeline were we" information on unblock. It is therefore a frontmatter flag, not
a workflow state:

```yaml
blocked: true
blocked_reason: "waiting on JN-42"
```

`status` always reflects true pipeline position; `blocked` is a separate axis
rendered as a 🚫 overlay in Telegram.

## Terminal semantics: `done` vs `archived`

Two **distinct** terminal states rather than one "closed" bucket — this keeps the
board columns and Telegram colors unambiguous.

- `done` — completed and verified. No resolution needed.
- `archived` — closed without completion, carrying an optional `resolution`
  field: `wontfix` | `duplicate` | `obsolete`.

## Transition guards

A guard is a precondition without which a transition is rejected. The default
workflow ships **one** guard:

- `in-progress` requires an `assignee` — you cannot start work with nobody
  assigned.

Guards are configurable; no other transition is gated by default. In particular,
`in-review` does **not** require an MR/PR link, so review of non-code work (design
discussion, manual checks) is not blocked.

## Git-host event → transition map

Events name a **target status**; the service advances the ticket **forward along
the legal transition path** to reach it, never skipping states. Backward moves
happen only via explicit events. Default map (symmetric across GitLab/GitHub):

| Event | Target |
|-------|--------|
| `mr_opened` / `pr_opened` | `in-review` |
| `mr_merged` / `pr_merged` | `done` |
| `mr_closed` / `pr_closed` (unmerged) | `in-progress` |

- **Forward auto-advance.** If an event targets `in-review` on a `todo` ticket,
  the service walks `todo → in-progress → in-review` (all legal) rather than
  jumping or stalling. If the target is unreachable by a forward legal path from
  the current state, the event is **skipped and a note is posted** to the ticket.
- **Guard interaction.** When forward auto-advance would cross the `in-progress`
  assignee guard on an unassigned ticket, the service **auto-assigns the MR/PR
  author** (the person actually doing the work) so the guard is satisfied
  naturally. The map itself is configurable.

## Validation strictness

- **Strict by default.** An illegal transition is a **hard error**.
- **Force override.** A caller may pass `force=true` to perform the transition
  anyway; the service records an explicit note in the commit message. Git is the
  audit trail, so a forced transition is fully traceable.

## Configuration

- The default workflow is **built in**.
- It is overridable **per repository** via `.jira_nano/workflow.yaml` in the
  ticket-store repo — versioned like everything else, so the workflow definition
  is itself part of the audit trail. One workflow per repository/project.

### Config shape

```yaml
workflow:
  initial: todo
  states:
    - {name: backlog,     icon: "🗒️", color: blue}
    - {name: todo,        icon: "📋", color: yellow}
    - {name: in-progress, icon: "🔧", color: purple}
    - {name: in-review,   icon: "👀", color: pink}
    - {name: done,        icon: "✅", color: green}
    - {name: archived,    icon: "📦", color: red}
  transitions:
    todo:        [in-progress, backlog, archived]
    backlog:     [todo, archived]
    in-progress: [in-review, todo, archived]
    in-review:   [done, in-progress, archived]
    done:        [todo]        # reopen
    archived:    [backlog]     # revive
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
`transitions[current]` (and any `guards[target]`) before writing to Git.

## Telegram rendering

- **Topic color** is taken from `state.color`. The Bot API exposes exactly six
  native forum-topic colors, which the six states use directly — always
  available, no special stickers required.
- **State icon** (emoji) is rendered as a prefix in the topic title and in update
  posts.
- **`blocked`** adds a 🚫 overlay to the title/posts.
- Note: arbitrary emoji as a *native topic icon* is **not** reliably available
  (the Bot API limits topic icons to `getForumTopicIconStickers`), so color +
  in-text emoji is the mechanism rather than custom native icons.

## Impact on the ticket schema (`JN-D3`)

This decision introduces three frontmatter fields consumed by the workflow —
`blocked` (bool), `blocked_reason` (string), and `resolution` (enum, on
`archived`). The full frontmatter schema remains open under `JN-D3`.
