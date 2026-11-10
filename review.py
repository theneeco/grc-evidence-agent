"""The "supervisor": a human approves or rejects each finding.

  python review.py output/<run_id>

Nothing leaves the run folder until you approve it. Approved FAILs become
DRAFT tickets (files), they are not sent anywhere.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from evidence_store import EvidenceStore


def main():
    run_dir = Path(sys.argv[1])
    findings = json.loads((run_dir / "findings.json").read_text())
    bad = EvidenceStore(run_dir).verify()
    if bad:
        sys.exit(f"Evidence integrity check FAILED for {bad}. Do not approve this run.")

    reviewer = input("Your name (reviewer): ").strip() or "unknown"
    decisions, drafts = {}, run_dir / "draft_tickets"
    for cid, f in findings.items():
        print(f"\n{'='*70}\n{cid} {f['title']}: {f['result']}" + ("  [NEEDS HUMAN]" if f["needs_human"] else ""))
        print(f["summary"])
        for i in f["failing_items"]:
            print(f"  - {i}")
        for r in f.get("related_tickets", []):
            flag = "  <-- SUSPECTED PROMPT INJECTION, not an exception" if r["suspected_injection"] else \
                   (f"  (expires {r['expires']}{', EXPIRED' if r['expired'] else ''})" if r["type"] == "Risk Exception" else "")
            print(f"  ticket {r['ticket']} [{r['type']}, {r['status']}] for {r['item']}{flag}")
        if f["human_question"]:
            print(f"Decision needed: {f['human_question']}")
        d = input("[a]pprove / [r]eject / [e]xception accepted? ").strip().lower()[:1] or "a"
        note = input("Note (optional): ").strip()
        decisions[cid] = {"decision": {"a": "approved", "r": "rejected", "e": "exception_accepted"}.get(d, "approved"),
                          "note": note}
        if f["result"] == "FAIL" and decisions[cid]["decision"] == "approved":
            drafts.mkdir(exist_ok=True)
            (drafts / f"{cid}.md").write_text(
                f"# [DRAFT] {cid} control failure: {f['title']}\n\nAssignee: {f['owner']}\n\n{f['summary']}\n\n"
                + "\n".join(f"- {i}" for i in f["failing_items"]) + f"\n\nReviewer note: {note}\n")

    review = {"reviewer": reviewer, "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "decisions": decisions}
    (run_dir / "review.json").write_text(json.dumps(review, indent=2))
    print(f"\nSaved {run_dir/'review.json'}" + (f"; draft tickets in {drafts}" if drafts.exists() else ""))


if __name__ == "__main__":
    main()
