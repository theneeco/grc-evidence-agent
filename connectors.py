"""Read-only connectors (the "keys").

Each connector does ONE narrow thing and returns the raw data plus metadata
describing where it came from. In the simulation they read JSON files in sim/;
in a real build you'd swap the body for an API call (boto3, Okta SDK, GitHub API)
using a read-only service account. Nothing here can write to any system.
"""
import json
from pathlib import Path

SIM_DIR = Path(__file__).parent / "sim"


def _load(name):
    return json.loads((SIM_DIR / name).read_text())


def okta_users_with_mfa():
    users = _load("okta_users.json")
    return {
        "source_system": "Okta (simulated)",
        "api_call": "GET /api/v1/users?filter=status eq \"ACTIVE\" + GET /api/v1/users/{id}/factors",
        "data": [u for u in users if u["status"] == "ACTIVE"],
    }


def hr_okta_leavers():
    leavers = _load("hr_terminations.json")
    okta = {u["email"]: u for u in _load("okta_users.json")}
    joined = []
    for l in leavers:
        u = okta.get(l["email"], {})
        joined.append({**l, "okta_status": u.get("status"), "okta_deactivated_at": u.get("deactivated_at")})
    return {
        "source_system": "HRIS + Okta (simulated)",
        "api_call": "HRIS GET /terminations?since=30d ; Okta GET /api/v1/users?search=profile.email",
        "data": joined,
    }


def aws_iam_access_keys():
    return {
        "source_system": "AWS IAM (simulated)",
        "api_call": "aws iam generate-credential-report && aws iam get-credential-report",
        "data": _load("aws_iam_access_keys.json"),
    }


def aws_s3_public_access():
    return {
        "source_system": "AWS S3 (simulated)",
        "api_call": "aws s3api get-public-access-block / get-bucket-policy-status (all buckets)",
        "data": _load("aws_s3_buckets.json"),
    }


def github_branch_protection():
    repos = _load("github_repos.json")
    return {
        "source_system": "GitHub (simulated)",
        "api_call": "GET /repos/{owner}/{repo}/branches/{branch}/protection",
        "data": [r for r in repos if r["production"]],
    }


import re

# Phrases that try to give instructions to an AI. Deliberately simple and visible:
# in a real deployment, tune these and treat a hit as a security event.
INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above|earlier) instructions",
    r"system (note|prompt|message) to (the )?(ai|agent|assistant|model)",
    r"mark (every|all|each)\b.{0,40}\bas pass",
    r"do not (report|flag|mention) (any )?(failures|issues|findings)",
    r"disregard (your|the|all) (rules|instructions)",
    r"you are now ",
]
REDACTED = "[REDACTED BY CODE: suspected prompt injection]"


def scan_ticket(ticket):
    """Return (sanitised copy, list of matched patterns). Matching text fields are
    replaced so the model never reads the injected instruction at all."""
    t = json.loads(json.dumps(ticket))
    hits = []

    def clean(s):
        found = [p for p in INJECTION_PATTERNS if re.search(p, s, re.I)]
        hits.extend(found)
        return REDACTED if found else s

    for k in ("summary", "description"):
        if isinstance(t.get(k), str):
            t[k] = clean(t[k])
    if isinstance(t.get("comments"), list):
        t["comments"] = [clean(c) if isinstance(c, str) else c for c in t["comments"]]
    if hits:
        t["suspected_injection"] = True
        t["injection_patterns"] = sorted(set(hits))
    return t, bool(hits)


def jira_search(query):
    """Keyword search over tickets (used to find documented risk exceptions).
    Splits the query on OR / spaces / commas and returns tickets matching ANY term.
    Masked terms (containing ***) are ignored because they can never match.
    Ticket text is written by humans and is UNTRUSTED input."""
    import re
    terms = [t for t in re.split(r"\s+OR\s+|[,\s]+", query, flags=re.I)
             if len(t) >= 3 and "***" not in t and t.lower() != "or"]
    hits = []
    for t in _load("jira_tickets.json"):
        text = json.dumps(t).lower()
        matched = [w for w in terms if w.lower() in text]
        if matched:
            clean, _ = scan_ticket(t)          # scanned BEFORE anything sees it
            hits.append({**clean, "matched_terms": matched})
    return {"source_system": "Jira (simulated)", "api_call": f"keyword search {terms}", "data": hits}


CONNECTORS = {
    "okta.users_with_mfa": okta_users_with_mfa,
    "hr_okta.leavers": hr_okta_leavers,
    "aws.iam_access_keys": aws_iam_access_keys,
    "aws.s3_public_access": aws_s3_public_access,
    "github.branch_protection": github_branch_protection,
}
