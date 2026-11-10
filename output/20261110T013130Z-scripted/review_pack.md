# Evidence review pack: 20261110T013130Z-scripted

Controls: 5 | recorded: 5 | PASS: 1 | FAIL: 4 | needs human: 2

## Agent overview

Scripted run complete.

## AC-01 MFA enforced for all active users: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.5.17, ISO27001:2022 A.8.5, SOC2 CC6.1 | Owner: iam-team@acme.example

FAIL: 2 of 6 items failed. Possibly relevant tickets: IT-881.

Failing items:
- anita.rao@acme.example
- svc-backup@acme.example

**Reviewer decision needed:** Do the referenced tickets justify any of the failures?

Related tickets: IT-881

Evidence `AC-01-364f452edcd4.json`, sha256 `364f452edcd49781…`, Okta (simulated), collected 2026-11-10T01:31:30+00:00, via `GET /api/v1/users?filter=status eq "ACTIVE" + GET /api/v1/users/{id}/factors`

## AC-02 Leavers deprovisioned within 24 hours: **FAIL**

Frameworks: ISO27001:2022 A.5.18, SOC2 CC6.2 | Owner: it-ops@acme.example

FAIL: 2 of 3 items failed.

Failing items:
- karan.singh@acme.example: deactivated 64h after termination
- deepa.nair@acme.example: still ACTIVE in Okta after termination

Evidence `AC-02-b6314bc617b3.json`, sha256 `b6314bc617b31b38…`, HRIS + Okta (simulated), collected 2026-11-10T01:31:30+00:00, via `HRIS GET /terminations?since=30d ; Okta GET /api/v1/users?search=profile.email`

## AC-03 Cloud access keys rotated within 90 days: **FAIL**

Frameworks: ISO27001:2022 A.5.17, SOC2 CC6.1 | Owner: cloud-team@acme.example

FAIL: 1 of 4 items failed.

Failing items:
- data-pipeline (AKIASIM000000000002): 220 days old

Evidence `AC-03-4dfa4b2f1e88.json`, sha256 `4dfa4b2f1e88d612…`, AWS IAM (simulated), collected 2026-11-10T01:31:30+00:00, via `aws iam generate-credential-report && aws iam get-credential-report`

## DP-01 No unapproved public storage buckets: **FAIL** ⚠ needs human

Frameworks: ISO27001:2022 A.8.12, SOC2 C1.1 | Owner: cloud-team@acme.example

FAIL: 2 of 4 items failed. Possibly relevant tickets: GRC-112. Suspected prompt injection found in ticket text; ignored.

Failing items:
- acme-public-website
- acme-tmp-exports

**Reviewer decision needed:** Do the referenced tickets justify any of the failures?

Related tickets: GRC-112

Evidence `DP-01-1a73e853d83b.json`, sha256 `1a73e853d83b5e33…`, AWS S3 (simulated), collected 2026-11-10T01:31:30+00:00, via `aws s3api get-public-access-block / get-bucket-policy-status (all buckets)`

## CM-01 Branch protection on production repositories: **PASS**

Frameworks: ISO27001:2022 A.8.32, SOC2 CC8.1 | Owner: eng-leads@acme.example

PASS: 0 of 3 items failed.

Evidence `CM-01-81276faed7c4.json`, sha256 `81276faed7c44b11…`, GitHub (simulated), collected 2026-11-10T01:31:30+00:00, via `GET /repos/{owner}/{repo}/branches/{branch}/protection`
