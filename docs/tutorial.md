# r0b0tlabbra1n Tutorial

This walkthrough exercises the full local memory loop.

```bash
cd /home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
rm -rf /tmp/demo-brain
.venv/bin/brain init --vault /tmp/demo-brain
.venv/bin/brain lint --vault /tmp/demo-brain
.venv/bin/brain build-index --vault /tmp/demo-brain
.venv/bin/brain search "Hermes memory" --vault /tmp/demo-brain --context
.venv/bin/brain graph --vault /tmp/demo-brain --json
.venv/bin/brain drift-check --vault /tmp/demo-brain
.venv/bin/brain eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
.venv/bin/python hermes/cron_scripts/heartbeat.py --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
```

Open `/tmp/demo-brain` in Obsidian to inspect the generated Markdown vault.
