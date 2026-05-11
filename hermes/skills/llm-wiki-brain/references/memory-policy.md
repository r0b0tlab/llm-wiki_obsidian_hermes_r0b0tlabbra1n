# Memory Policy Reference

## Tiers

### L1 HOT
- Location: Hermes built-in `MEMORY.md` and `USER.md`
- Max size: ~2,200 chars (MEMORY) + ~1,375 chars (USER)
- Purpose: Compact pointers to L2 warm pages
- Update frequency: Manual or cron (never auto during turns)

### L2 WARM
- Location: `START_HERE.md`, `dashboards/`, `_agent/semantic/project-status.md`
- Purpose: Agent orientation, project status, operating rules
- Auto-loaded: Yes (via skill or memory provider)

### L3 COLD
- Location: `sessions/summaries/`, `projects/`, `concepts/`, `_agent/episodic/`
- Purpose: Detailed pages, historical records
- Auto-loaded: No (retrieved on demand via search)

### L4 ARCHIVE
- Location: `raw/`, superseded pages
- Purpose: Immutable source captures, old records
- Auto-loaded: Never

## Promotion/Demotion

| From | To | Condition | Action |
|------|----|-----------|--------|
| L3 COLD | L2 WARM | 3+ corroborating sessions | Move to warm page |
| L2 WARM | L1 HOT | 5+ retrievals | Compact pointer in MEMORY.md |
| L2 WARM | L3 COLD | Stale > 30 days | Downgrade status |
| L3 COLD | L4 ARCHIVE | Stale > 90 days | Move to archive |

## Write Policy

- Raw files: immutable after ingest
- Compiled pages: atomic write
- Indexes: rebuilt from source
- Every automated write logs to `log.md`
- Bulk updates require explicit scope

## Secrets

NEVER store secrets in the vault.
- HF tokens, API keys, private keys, JWT tokens, passwords
- Store key names and config paths only
- Secret scanner runs on every write operation
- `brain lint` checks all files for secrets
