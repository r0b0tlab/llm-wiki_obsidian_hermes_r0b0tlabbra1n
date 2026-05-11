# Cron: Heartbeat — check vault health and update dashboards

**Frequency:** Daily
**Delivery:** Local only
**Skill:** llm-wiki-brain

Run the brain lint, build-index, and update the agent dashboard.

## Instructions

1. Run `brain lint --vault ~/my-brain` and capture output
2. Run `brain build-index --vault ~/my-brain`
3. Check for stale pages (any page with `status: stale` or `status: archived`)
4. Update `dashboards/agent-dashboard.md` with current health status
5. Update `dashboards/stale-items.md` if any pages are stale
6. Report any ERROR-level lint issues to the user
