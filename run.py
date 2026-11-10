"""Run one evidence-collection cycle.

  python run.py --scripted     # no AI, no API key needed
  python run.py --local        # free local model via Ollama (no key)
  python run.py                # Claude drives the tools (needs ANTHROPIC_API_KEY)
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from agent import run_agent, run_agent_local, run_scripted
from evidence_store import EvidenceStore
from tools import Toolbox

ROOT = Path(__file__).parent


def write_review_pack(run_dir, toolbox, overview):
    f = toolbox.findings
    lines = [f"# Evidence review pack: {run_dir.name}", "",
             f"Controls: {len(toolbox.controls)} | recorded: {len(f)} | "
             f"PASS: {sum(x['result']=='PASS' for x in f.values())} | "
             f"FAIL: {sum(x['result']=='FAIL' for x in f.values())} | "
             f"needs human: {sum(x['needs_human'] for x in f.values())}", "",
             "## Agent overview", "", overview.strip(), ""]
    if toolbox.injections:
        lines += [f"> ⚠ **Suspected prompt injection detected by code in: {', '.join(sorted(toolbox.injections))}.** "
                  "The text was redacted before the AI saw it. Treat as a security event.", ""]
    missing = set(toolbox.controls) - set(f)
    if missing:
        lines += [f"**WARNING: no finding recorded for {sorted(missing)}**", ""]
    for cid, x in f.items():
        lines += [f"## {cid} {x['title']}: **{x['result']}**" + (" ⚠ needs human" if x["needs_human"] else ""),
                  "", f"Frameworks: {', '.join(x['frameworks'])} | Owner: {x['owner']}", "", x["summary"], ""]
        if x["failing_items"]:
            lines += ["Failing items:"] + [f"- {i}" for i in x["failing_items"]] + [""]
        if x.get("related_tickets"):
            lines += ["Related tickets found by code (not written by the AI):"]
            for r in x["related_tickets"]:
                tag = ""
                if r["suspected_injection"]:
                    tag = " ⚠ SUSPECTED PROMPT INJECTION (redacted), not an exception"
                elif r["type"] == "Risk Exception":
                    tag = f" (expires {r['expires']}{', EXPIRED' if r['expired'] else ''})"
                lines += [f"- {r['item']} → **{r['ticket']}** [{r['type']}, {r['status']}] {r['summary']}{tag}"]
            lines.append("")
        if x["human_question"]:
            lines += [f"**Reviewer decision needed (AI-written):** {x['human_question']}", ""]
        if x["exception_refs"]:
            lines += [f"Related tickets: {', '.join(x['exception_refs'])}", ""]
        for e in x["evidence"]:
            lines += [f"Evidence `{e['file']}`, sha256 `{e['sha256'][:16]}…`, {e['source_system']}, "
                      f"collected {e['collected_at']}, via `{e['api_call']}`"]
        lines.append("")
    (run_dir / "review_pack.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scripted", action="store_true", help="run without the AI")
    ap.add_argument("--local", action="store_true", help="use a free local model via Ollama")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    catalogue = yaml.safe_load((ROOT / "catalogue.yaml").read_text())
    mode = "scripted" if a.scripted else ("local" if a.local else "agent")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{mode}"
    run_dir = ROOT / "output" / run_id
    store = EvidenceStore(run_dir)
    toolbox = Toolbox(catalogue, store, actor=f"evidence-bot/{mode}")

    print(f"Run {run_id}")
    if a.scripted:
        overview = run_scripted(toolbox)
    elif a.local:
        overview = run_agent_local(toolbox, model=a.model)
    else:
        overview = run_agent(toolbox, model=a.model)

    (run_dir / "findings.json").write_text(json.dumps(toolbox.findings, indent=2))
    write_review_pack(run_dir, toolbox, overview)
    bad = store.verify()
    print(f"\nEvidence integrity check: {'OK' if not bad else 'TAMPERED: ' + str(bad)}")
    print(f"Review pack: {run_dir / 'review_pack.md'}")
    print(f"Next: python review.py {run_dir}")


if __name__ == "__main__":
    main()
