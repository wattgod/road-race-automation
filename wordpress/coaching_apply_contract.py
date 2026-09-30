"""What a shippable /coaching/apply/ page must contain (stdlib only).

One contract, three users:
  - generate_coaching_apply.py takes the Worker URL from here;
  - scripts/push_wordpress.py refuses to upload an apply page that fails it
    (a stale wordpress/output/coaching-apply.html once meant FormSubmit-only);
  - scripts/validate_deploy.py checks the live page against it.
"""
from __future__ import annotations

# The shared, brand-aware coaching intake edge (wattgod/gravel-race-automation
# workers/coaching-intake). It maps the roadielabs.com Origin to brand
# "roadielabs" and forwards to the pipeline's /api/coaching-intakes.
COACHING_INTAKE_WORKER_URL = "https://coaching-intake.gravelgodcoaching.workers.dev"


def apply_page_problems(html: str) -> list[str]:
    """Return why this apply page would break applications ([] = shippable)."""
    problems = []
    if "formsubmit.co" in html.lower():
        problems.append("contains formsubmit.co — FormSubmit is dead (500s, no deliveries)")
    if COACHING_INTAKE_WORKER_URL not in html:
        problems.append(
            f"missing the coaching-intake Worker ({COACHING_INTAKE_WORKER_URL}) — "
            "applications won't reach the pipeline")
    if 'name="tier"' not in html:
        problems.append('missing name="tier" — the Worker rejects every application without a tier')
    if "coaching_intake_submission_id" not in html:
        problems.append("missing coaching_intake_submission_id — retries would create duplicate cases")
    return problems
