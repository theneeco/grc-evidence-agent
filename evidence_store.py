"""The "filing cabinet": tamper-evident evidence storage + audit log.

Every item is saved raw (unmasked) with source, API call, timestamp and SHA-256,
then made read-only. A manifest lists every item; verify() re-hashes them so
you can prove nothing changed since collection. In production use write-once
storage (e.g. S3 Object Lock in compliance mode) instead of chmod.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EvidenceStore:
    def __init__(self, run_dir: Path):
        self.dir = run_dir / "evidence"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.manifest = run_dir / "manifest.jsonl"
        self.audit = run_dir / "audit_log.jsonl"

    def save(self, control_id, payload):
        collected_at = utcnow()
        record = {"control_id": control_id, "collected_at": collected_at, **payload}
        body = json.dumps(record, indent=2, sort_keys=True).encode()
        sha = hashlib.sha256(body).hexdigest()
        evidence_id = f"{control_id}-{sha[:12]}"
        path = self.dir / f"{evidence_id}.json"
        path.write_bytes(body)
        os.chmod(path, 0o444)  # read-only
        entry = {"evidence_id": evidence_id, "control_id": control_id, "file": path.name,
                 "sha256": sha, "collected_at": collected_at,
                 "source_system": payload["source_system"], "api_call": payload["api_call"]}
        with self.manifest.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def log(self, actor, tool, tool_input, output):
        out_hash = hashlib.sha256(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()
        with self.audit.open("a") as f:
            f.write(json.dumps({"ts": utcnow(), "actor": actor, "tool": tool,
                                "input": tool_input, "output_sha256": out_hash}) + "\n")

    def verify(self):
        problems = []
        for line in self.manifest.read_text().splitlines():
            e = json.loads(line)
            actual = hashlib.sha256((self.dir / e["file"]).read_bytes()).hexdigest()
            if actual != e["sha256"]:
                problems.append(e["evidence_id"])
        return problems
