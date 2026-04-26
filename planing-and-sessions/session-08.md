# Session 08 — GitHub Actions: Test & Build Jobs

> Phase: **Phase 5 — GitHub Actions CI/CD** (part 1)
> Plan ref: `plans/modelserve-plan.md#phase-5`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 07 complete ✓

---

## Goal

By the end of this session: the `test` and `build-and-push` jobs are working in GitHub Actions — every push to `main` runs pytest and builds + pushes the Docker image to ECR.

---

## Checklist

### GitHub Secrets
- [ ] `AWS_ACCESS_KEY_ID` configured in GitHub repo secrets
- [ ] `AWS_SECRET_ACCESS_KEY` configured in GitHub repo secrets
- [ ] `AWS_REGION` configured (e.g. `ap-southeast-1`)
- [ ] `ECR_REPOSITORY` configured (ECR repository URL)
- [ ] No credentials hardcoded anywhere in workflow files

### `test` Job
- [ ] `test` job defined in `.github/workflows/deploy.yml`
- [ ] Triggers on: push to `main` AND pull requests
- [ ] Runs `pytest app/tests/` — at least one test exercises the actual prediction flow (not just mocks)
- [ ] Job passes on push to `main`

### `build-and-push` Job
- [ ] `build-and-push` job triggers on: push to `main` AND version tags (`v*.*.*`)
- [ ] Job runs only after `test` passes (`needs: test`)
- [ ] Authenticates to ECR using AWS credentials from GitHub Secrets
- [ ] Builds Docker image with correct tag (commit SHA or `latest`)
- [ ] Pushes image to ECR
- [ ] Job shows green checkmark on GitHub Actions

### Trivy Scan (Bonus +2)
- [ ] `trivy-scan` job added to workflow
- [ ] Scans the built Docker image for critical CVEs
- [ ] Job fails the pipeline if critical vulnerabilities found
- [ ] Job runs after `build-and-push`

### Verification
- [ ] Push to `main` → `test` job → `build-and-push` job both pass in GitHub Actions UI
- [ ] ECR repository shows the newly pushed image
- [ ] All changes pushed to GitHub

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
