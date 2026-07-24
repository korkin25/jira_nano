# Status / workflow model — DRAFT

> **This is a DRAFT and is OPEN for brainstorming.** Decision `JN-D1` in
> `TODO.md` tracks it. Nothing here is final; the open questions at the bottom
> must be resolved before implementation.

## Goal

A **configurable** workflow: a set of states and the allowed transitions between
them, defined in a config file, validated by the API/service layer on every
mutation, and mirrored to Telegram via status icons. Terminal states
archive/close a ticket.

## Draft state set

A minimal starting proposal (subject to change):

| State | Meaning | Icon (draft) | Terminal? |
|-------|---------|--------------|-----------|
| `backlog` | Captured, not scheduled | 🗒️ | no |
| `todo` | Ready to start | 📋 | no |
| `in-progress` | Being worked on | 🔧 | no |
| `in-review` | Under review (e.g. MR/PR open) | 👀 | no |
| `done` | Completed and verified | ✅ | yes (close) |
| `archived` | Closed without completion (won't-do / duplicate) | 📦 | yes (archive) |

## Draft transition rules

```
backlog     → todo | archived
todo        → in-progress | backlog | archived
in-progress → in-review | todo | archived
in-review   → done | in-progress | archived
done        → (terminal; reopen → todo?)
archived    → (terminal; reopen → backlog?)
```

- Any non-terminal state may move to `archived`.
- Reopening a terminal state is an **open question** (see below).
- Git-host events map onto transitions (draft): MR/PR opened → `in-review`;
  merged → `done`.

## Draft config shape

A config file (format TBD — YAML/TOML) declares states and transitions, e.g.:

```yaml
workflow:
  states:
    - name: backlog
      icon: "🗒️"
    - name: in-progress
      icon: "🔧"
      # ...
  transitions:
    backlog: [todo, archived]
    todo: [in-progress, backlog, archived]
    # ...
  terminal: [done, archived]
```

The service layer loads this once, and every `transition` call is validated
against `transitions[current]` before writing to Git.

## OPEN QUESTIONS (needs brainstorming — `JN-D1`)

1. **State set granularity.** Is the six-state draft right, or do we want fewer
   (e.g. `todo` / `doing` / `done`) or more (blocked, QA, staged)? How
   opinionated should the default be?
2. **Reopening terminal states.** Are `done`/`archived` truly terminal, or is a
   reopen transition allowed? If allowed, to which state?
3. **`archived` vs `done` semantics.** One terminal "closed" bucket with a
   resolution field, or two distinct states? How does that map to boards?
4. **Per-project override.** Global default workflow only, or per-repository /
   per-project workflow config? Where does the config file live relative to the
   ticket store?
5. **Icon ↔ state binding.** Fixed icons vs user-configurable; how are they
   represented in Telegram (topic icons vs message emoji vs both)?
6. **Git-host event → transition map.** Which events trigger which transitions,
   and is that map itself configurable? Do events force transitions or only
   suggest them?
7. **Validation strictness.** Reject an illegal transition hard (error), or
   allow a forced/admin override with an audit note?
8. **Assignee/label gating.** Should some transitions require an assignee or a
   label (e.g. can't go `in-review` without an MR link)?

Resolve these in the brainstorming session tracked by `JN-D1` before writing any
workflow code.
