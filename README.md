# GRC Evidence-Collection Agent: Simulation Kit

A safe, offline practice build of an AI agent that collects audit evidence.
"Acme" is a fake company. Its Okta, HR, AWS, GitHub and Jira are JSON files in `sim/`.
Nothing here connects to a real system.

## The pieces

| Piece | File | What it is |
|---|---|---|
| Checklist | `catalogue.yaml` | Each control, what evidence it needs, where it lives, what "pass" means |
| Fake company | `sim/*.json` | Simulated Okta, HRIS, AWS IAM/S3, GitHub, Jira |
| Keys | `connectors.py` | Read-only functions, one per evidence source |
| Rules | `checks.py` | Deterministic PASS/FAIL logic. The AI never decides this. |
| Filing cabinet | `evidence_store.py` | Saves raw evidence + SHA-256 + timestamp + source, read-only, plus audit log |
| Toolbox + guardrails | `tools.py` | The only actions the AI can take. It masks personal data, labels untrusted text, and blocks overrides. |
| Brain | `agent.py` | Claude agent loop, and a scripted (no-AI) version of the same steps |
| Runner | `run.py` | Runs one cycle and writes the review pack |
| Supervisor | `review.py` | You approve, reject, or accept exceptions. Approved failures become draft tickets. |

## Step-by-step

### Step 1: Set up
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Read the checklist
Open `catalogue.yaml`. Five controls (MFA, leavers, key rotation, public buckets,
branch protection), each mapped to ISO 27001:2022 and SOC 2. In a real build you
write this part first, and it is pure GRC work.

### Step 3: Look at the fake company
Browse `sim/`. Planted problems:
- 2 active users without MFA (one is a service account, with a ticket mentioning a compensating control)
- 1 leaver deactivated 64h late, 1 leaver still active
- 1 AWS access key 220 days old
- 2 public buckets: one covered by an approved risk exception (GRC-112), one not
- a Jira comment containing a **prompt-injection attack** (GRC-130)

### Step 4: Run it without AI first
```bash
python run.py --scripted
```
This proves the plumbing (connectors → evidence store → checks → findings) works
before any AI is involved. Open `output/<run>/review_pack.md`.

### Step 5: Run it with the AI agent
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # from console.anthropic.com
python run.py                            # optional: --model <model-id>
```
Watch the tool calls stream past. Compare the agent's review pack with the
scripted one. The agent should write better summaries, link GRC-112 to
`acme-public-website` only, notice the service-account context, and flag the injection.

### Step 5b: Free alternative: run a local model with Ollama
No API key or cost, and the evidence never leaves your Mac.
```bash
brew install ollama          # or download from ollama.com
ollama serve                 # leave this running in its own Terminal tab
ollama pull qwen3:8b         # ~5 GB; any model tagged "tools" on ollama.com works
python run.py --local                      # uses qwen3:8b by default
python run.py --local --model llama3.1:8b  # or pick another
```
Small local models make more mistakes than Claude: they skip controls, call
tools in the wrong order, or write vaguer summaries. The runner nudges them if they stop
early, and the guardrails in `tools.py` hold regardless of which model drives them.
Comparing the local and Claude review packs is an exercise in itself.

### Step 6: Be the supervisor
```bash
python review.py output/<run>
```
Approve, reject, or accept an exception for each finding. Your decisions go to
`review.json`, and approved failures become `draft_tickets/*.md`. Nothing is sent anywhere.

### Step 7: Inspect the audit trail
In `output/<run>/`:
- `evidence/` holds the raw, read-only evidence files
- `manifest.jsonl` has hash, source, API call and time for every item
- `audit_log.jsonl` records every tool call the agent made (the auditor audits the bot too)

## Exercises (try to break it)

1. **Tamper test.** `chmod u+w` an evidence file, edit it, then run `review.py`. It refuses because the hash no longer matches.
2. **Prompt injection.** Make the GRC-130 comment more convincing. Does the agent obey? Even if it tried, `record_finding` rejects a PASS that contradicts `checks.py`.
3. **Expired exception.** Change GRC-112's `expires` to `2026-01-01`. Does the agent notice? (The scripted version won't, which shows where the AI earns its place.)
4. **Add a control.** e.g. "Laptops have disk encryption". Add `sim/mdm_devices.json`, a connector, a check, and a catalogue entry.
5. **Data minimisation.** Look at what the model actually sees (`data_masked`) versus what's stored. Decide what else should be masked.

## Taking it towards real systems (later, carefully)
- Swap a connector body for the real API (boto3, Okta SDK, GitHub REST) using a **read-only** service account kept in a secrets manager.
- Optionally wrap connectors as **MCP servers** so any agent framework can use them.
- Replace `chmod 0444` with **write-once storage** (e.g. S3 Object Lock, compliance mode).
- Keep the human review step. Add write tools (ticket creation) only behind approval.
- Check what data leaves your environment for the model provider, and record that in your own risk register.
