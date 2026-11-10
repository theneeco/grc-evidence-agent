"""Deterministic pass/fail rules.

The AI never decides PASS/FAIL by 'looking'. These plain functions do,
so the same evidence always gives the same result (auditors care about this).
"""
from datetime import datetime


def _dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def check_AC_01(data, now, params):
    failing = [u["email"] for u in data if not u["mfa_factors"]]
    return {"total_checked": len(data), "failing": failing}


def check_AC_02(data, now, params):
    max_h = params.get("max_hours", 24)
    failing = []
    for l in data:
        if l["okta_status"] == "ACTIVE" or not l["okta_deactivated_at"]:
            failing.append(f'{l["email"]}: still ACTIVE in Okta after termination')
            continue
        hours = (_dt(l["okta_deactivated_at"]) - _dt(l["termination_at"])).total_seconds() / 3600
        if hours > max_h:
            failing.append(f'{l["email"]}: deactivated {hours:.0f}h after termination')
    return {"total_checked": len(data), "failing": failing}


def check_AC_03(data, now, params):
    max_d = params.get("max_age_days", 90)
    failing = []
    for k in data:
        age = (now - _dt(k["created"])).days
        if k["status"] == "Active" and age > max_d:
            failing.append(f'{k["user"]} ({k["access_key_id"]}): {age} days old')
    return {"total_checked": len(data), "failing": failing}


def check_DP_01(data, now, params):
    failing = [b["bucket"] for b in data if not b["block_public_access"] or b["public_policy"]]
    return {"total_checked": len(data), "failing": failing}


def check_CM_01(data, now, params):
    failing = []
    for r in data:
        p = r["protection"] or {}
        if p.get("required_reviews", 0) < 1 or p.get("allow_force_push", True):
            failing.append(f'{r["repo"]}: reviews={p.get("required_reviews", 0)}, force_push={p.get("allow_force_push")}')
    return {"total_checked": len(data), "failing": failing}


def run_check(control, data, now):
    fn = globals()[f'check_{control["id"].replace("-", "_")}']
    r = fn(data, now, control.get("params", {}))
    r["result"] = "FAIL" if r["failing"] else "PASS"
    r["rule"] = control["pass_if"]
    return r
