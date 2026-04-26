# Session 09 — GitHub Actions: Deploy Job & PR Preview

> Phase: **Phase 5 — GitHub Actions CI/CD** (part 2)
> Plan ref: `plans/modelserve-plan.md#phase-5`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 08 complete ✓

---

## Goal

By the end of this session: a push to `main` triggers a complete test → build → deploy cycle, the deployed service is verified live by CI, and Pulumi PR preview comments work on pull requests.

---

## Checklist

### GitHub Secrets (additional)
- [ ] `EC2_HOST` configured (Elastic IP of the EC2 instance)
- [ ] `EC2_SSH_KEY` configured (private key for SSH access to EC2)

### `deploy` Job
- [ ] `deploy` job defined in workflow
- [ ] Runs after `build-and-push` passes (`needs: build-and-push`)
- [ ] Triggers on: push to `main` AND version tags (`v*.*.*`)
- [ ] SSHes into EC2 using `EC2_SSH_KEY` and `EC2_HOST` secrets
- [ ] Pulls latest image from ECR on the EC2 instance
- [ ] Restarts the FastAPI service (via `docker compose pull && docker compose up -d`)
- [ ] Verifies `/health` returns 200 after restart — fails job if not
- [ ] `pulumi up` runs as part of deploy to keep infrastructure current (or as a separate `infra` job)

### Pulumi PR Preview (Bonus +2)
- [ ] `pulumi-preview` job defined in workflow
- [ ] Triggers only on pull requests
- [ ] Runs `pulumi preview` against the PR's infrastructure changes
- [ ] Posts the Pulumi diff as a comment on the PR
- [ ] Uses GitHub token for PR commenting (no extra secret needed)

### End-to-End Pipeline Verification
- [ ] Push to `main` triggers all jobs in sequence: `test` → `build-and-push` → `trivy-scan` → `deploy`
- [ ] All jobs show green checkmarks in GitHub Actions
- [ ] After successful pipeline: `curl http://<elastic-ip>:8000/health` returns 200 from local machine
- [ ] Pipeline runs end-to-end without manual intervention between runs
- [ ] Create a version tag (`git tag v1.0.0 && git push --tags`) → verify `build-and-push` + `deploy` trigger
- [ ] Open a test PR → verify `pulumi-preview` posts a comment with the infrastructure diff
---

## Manual flow test — run this yourself

```bash
# 1. Trigger full pipeline
git push origin main
open https://github.com/<your-repo>/actions

# 2. Watch all jobs pass: test → build-and-push → trivy-scan → deploy

# 3. After deploy job completes, verify live service
IP=<your-elastic-ip>
curl http://$IP:8000/health
curl -X POST http://$IP:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json

# 4. Test tag-based trigger
git tag v1.0.0 && git push --tags

# 5. Open a test PR and check pulumi-preview comment appears
```

All pass? → the pipeline push IS the commit. Confirm green checkmark on GitHub.

---

## Capture decisions now (feeds ADR-2)

Before finishing this session, jot these down in `docs/ARCHITECTURE.md`:

- [ ] Why incremental `pulumi up` instead of destroy-and-recreate? When would you switch?
- [ ] Why hybrid trigger (push to main + tags) instead of tags-only?
- [ ] How does the pipeline handle a failed deploy — what's the recovery path?
- [ ] Expected end-to-end deploy time (test → build → deploy → health check)?

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
