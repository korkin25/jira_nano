# Tests

Test-driven per `CLAUDE.md`: for each Phase 1 task, write the failing test(s)
first, then implement until green. One test module per module under test.

| Test module | Covers | Task |
|-------------|--------|------|
| `test_models.py` | validators / presence rules | JN-1 |
| `test_serialization.py` | `loads`/`dumps` round-trip | JN-1 |
| `test_ids.py` | sequential id allocation, no reuse | JN-3 |
| `test_config.py` | workflow load + defaults, paths | JN-28 |
| `test_users.py` | user directory load + handle resolution | JN-28 |
| `test_store.py` | pygit2 read/write/commit/history | JN-2 |
| `test_cache_schema.py` | schema create + version | JN-4 |
| `test_cache_rebuild.py` | full rebuild from disk | JN-5 |
| `test_cache_upsert.py` | incremental upsert | JN-6 |
| `test_sync.py` | HEAD-diff refresh + working-tree edits | JN-29 |
| `test_service.py` | create/get/update, commit-first→cache | JN-7 |
| `test_queries.py` | search / list / board | JN-8 |

`conftest.py` holds shared fixtures (the temp `repo`).
