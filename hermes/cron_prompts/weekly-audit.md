# Cron: Weekly Audit — deep vault audit and memory promotion/demotion

**Frequency:** Weekly (Sunday)
**Delivery:** Local, with summary to Telegram if configured
**Skill:** llm-wiki-brain

Perform deep vault audit: check staleness, promote/demote memory items, report memory health.

## Instructions

1. Run `brain lint --vault ~/my-brain` and capture all output
2. Run `brain build-index --vault ~/my-brain`
3. Scan all pages for staleness:
   - Pages with `updated` field > 30 days ago → mark status: stale
   - Pages with `updated` field > 90 days ago → mark status: archived
4. Check for duplicate or contradictory facts across pages
5. Identify orphan pages that should be linked
6. Update `dashboards/memory-health.md` with:
   - Total page count by tier
   - Total page count by type
   - Stale page count
   - Orphan page count
7. Update `dashboards/stale-items.md`
8. Report summary to user
