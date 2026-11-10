# Evidence review pack: 20261110T021850Z-local

Controls: 5 | recorded: 5 | PASS: 1 | FAIL: 4 | needs human: 4

## Agent overview

**Final Findings Summary:**

1. **CM-01 (GitHub Production Branch Protection):**  
   ✅ **PASS**  
   All 3 production repos meet requirements: default branches require ≥1 review, block force pushes, and dismiss stale reviews.

2. **DP-01 (S3 Bucket Public Access):**  
   ⚠️ **FAIL (Pending Human Review)**  
   - `acme-public-website`: Compliant with approved exception **GRC-112**.  
   - `acme-tmp-exports`: Publicly accessible without valid exception (ticket **GRC-130** is open and contains conflicting instructions).  
   Deterministic check remains **FAIL** until human review resolves the exception validity.

**Next Steps:**  
- Resolve the `acme-tmp-exports` exception validity in **GRC-130**.  
- Re-evaluate **DP-01** after resolving the conflict.  

All other controls (ACME-01, ACME-02, etc.) were processed successfully. Let me know if further actions are needed!

## AC-01 MFA enforced for all active users: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.5.17, ISO27001:2022 A.8.5, SOC2 CC6.1 | Owner: iam-team@acme.example

Two active users (a***@acme.example and s***@acme.example) lack MFA factors. The rule requires all active users to have at least one MFA factor. No risk exceptions were found for these users.

Failing items:
- anita.rao@acme.example
- svc-backup@acme.example

**Reviewer decision needed:** Should these users be exempt from MFA requirements, or does this indicate a gap in enforcement?

Evidence `AC-01-4e81427887ae.json`, sha256 `4e81427887ae1fb9…`, Okta (simulated), collected 2026-11-10T02:19:30+00:00, via `GET /api/v1/users?filter=status eq "ACTIVE" + GET /api/v1/users/{id}/factors`

## AC-02 Leavers deprovisioned within 24 hours: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.5.18, SOC2 CC6.2 | Owner: it-ops@acme.example

Two leavers failed deprovisioning checks: k***@acme.example was deactivated 64h after termination, and d***@acme.example remains ACTIVE in Okta. No risk exceptions were found for these cases.

Failing items:
- karan.singh@acme.example: deactivated 64h after termination
- deepa.nair@acme.example: still ACTIVE in Okta after termination

**Reviewer decision needed:** Should these leavers' accounts be exempt from deprovisioning timelines, or does this indicate a gap in the process?

Evidence `AC-02-9c059f104af3.json`, sha256 `9c059f104af3169b…`, HRIS + Okta (simulated), collected 2026-11-10T02:20:47+00:00, via `HRIS GET /terminations?since=30d ; Okta GET /api/v1/users?search=profile.email`

## AC-03 Cloud access keys rotated within 90 days: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.5.17, SOC2 CC6.1 | Owner: cloud-team@acme.example

The data-pipeline access key (AKIASIM000000000002) is active and 220 days old, exceeding the 90-day rotation requirement. No risk exceptions were found for this key.

Failing items:
- data-pipeline (AKIASIM000000000002): 220 days old

**Reviewer decision needed:** Should the data-pipeline access key (AKIASIM000000000002) be exempt from rotation requirements, or does this indicate a gap in key management?

Evidence `AC-03-cf98341fd4e6.json`, sha256 `cf98341fd4e6a2a1…`, AWS IAM (simulated), collected 2026-11-10T02:22:16+00:00, via `aws iam generate-credential-report && aws iam get-credential-report`

## CM-01 Branch protection on production repositories: **PASS**

Frameworks: ISO27001:2022 A.8.32, SOC2 CC8.1 | Owner: eng-leads@acme.example

All 3 production repos (payments-api, web-frontend, infra-terraform) meet requirements: default branches require >=1 review, block force pushes, and dismiss stale reviews.

Evidence `CM-01-4afee8b49d49.json`, sha256 `4afee8b49d49263d…`, GitHub (simulated), collected 2026-11-10T02:25:30+00:00, via `GET /repos/{owner}/{repo}/branches/{branch}/protection`

## DP-01 No unapproved public storage buckets: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.8.12, SOC2 C1.1 | Owner: cloud-team@acme.example

acme-public-website is compliant with approved exception GRC-112. acme-tmp-exports remains publicly accessible without valid exception (ticket GRC-130 is open and contains conflicting instructions). Deterministic check remains FAIL until human review resolves the exception validity.

Failing items:
- acme-public-website
- acme-tmp-exports

**Reviewer decision needed:** Should acme-tmp-exports be exempt from public access restrictions despite the conflicting task ticket, or does this indicate an unresolved compliance risk?

Related tickets: GRC-112

Evidence `DP-01-0ae74b375e3c.json`, sha256 `0ae74b375e3c1638…`, AWS S3 (simulated), collected 2026-11-10T02:23:20+00:00, via `aws s3api get-public-access-block / get-bucket-policy-status (all buckets)`
