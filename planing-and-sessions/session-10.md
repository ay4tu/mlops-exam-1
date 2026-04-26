# Session 10 — Documentation, Bonus Features & Demo Rehearsal

> Phase: **Phase 6 — Documentation, Bonus & Hardening**
> Plan ref: `plans/modelserve-plan.md#phase-6`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 09 complete ✓

---

## Goal

By the end of this session: the repository is in final submission state — `ARCHITECTURE.md` complete with all 5 ADRs, `/rollback` endpoint working, `README.md` polished, pipeline green, and the demo rehearsed end-to-end.

---

## Checklist

### `/rollback` Endpoint (Bonus +2)
- [ ] `GET /rollback` endpoint implemented in `app/main.py`
- [ ] Switches the active model to the previous Production version in MLflow Registry
- [ ] Response body confirms the new active model version
- [ ] Calling `/rollback` is visible in MLflow UI (version stage changes)
- [ ] Subsequent `/predict` calls use the rolled-back model version
- [ ] Demonstrated working: push a new model version → predict → rollback → predict again

### `docs/ARCHITECTURE.md` — Complete
- [ ] **System Overview**: 2–3 paragraphs (what it does, who it serves, design philosophy)
- [ ] **Architecture Diagram**: committed to `docs/diagrams/`, referenced in markdown
  - [ ] Shows all components (FastAPI, MLflow, Feast, Redis, Postgres, Prometheus, Grafana)
  - [ ] Shows where each component runs (local vs EC2)
  - [ ] Shows ports and communication paths
  - [ ] Local dev topology + production topology both present
- [ ] **ADR-1**: Deployment topology — why single EC2, trade-offs acknowledged
- [ ] **ADR-2**: CI/CD strategy — incremental update + hybrid trigger, when destroy-and-recreate is better
- [ ] **ADR-3**: Data architecture — Postgres for MLflow, Redis for Feast, S3 for artifacts
- [ ] **ADR-4**: Containerisation — base image choice, multi-stage rationale, image size trade-offs
- [ ] **ADR-5**: Monitoring design — alert threshold rationale, dashboard choices, known gaps
- [ ] **CI/CD Pipeline Documentation**: each job described, triggers, secrets, failure handling, expected deploy time
- [ ] **Runbook**:
  - [ ] Fresh-clone bootstrap (step by step, including secrets setup)
  - [ ] Deploying a new model version without restarting the whole stack
  - [ ] Recovering from: service crash, S3 permission loss, Pulumi state corruption
  - [ ] Full teardown procedure
- [ ] **Known Limitations**: honest list of gaps and what would change in real production

### `README.md` — Final Polish
- [ ] Project description (2–3 sentences)
- [ ] Prerequisites listed: Docker, Python, AWS CLI, Pulumi, Kaggle API
- [ ] Quick setup instructions for local development (numbered steps)
- [ ] REST endpoint table: method, path, description, example response
- [ ] Environment variable table with descriptions (matches `.env.example`)
- [ ] GitHub Secrets section: every secret listed without values
- [ ] Link to `docs/ARCHITECTURE.md`

### `.env.example` — Complete
- [ ] All required environment variables listed with descriptions
- [ ] No actual values committed (only placeholder/example values)

### Final Submission Checks
- [ ] Repository is public on GitHub
- [ ] `docker compose up` from a fresh clone reaches healthy state in under 15 minutes
- [ ] Latest commit on `main` shows green checkmark in GitHub Actions
- [ ] `training/features.parquet` committed (not gitignored)
- [ ] `training/sample_request.json` committed
- [ ] `docs/ARCHITECTURE.md` complete with all required sections
- [ ] `pulumi destroy --yes` run — AWS resources cleaned up

### Demo Rehearsal
- [ ] Cold-start rehearsal: fresh AWS sandbox → trigger pipeline → watch deploy → verify system
- [ ] Walk through architecture diagram out loud (practice the 15-minute TA walkthrough)
- [ ] Hit `/health`, make a prediction, show Grafana updating live
- [ ] Kill FastAPI container → show alert fires → restart → show alert clears
- [ ] Call `/rollback` → show model version changes in MLflow and `/health`
- [ ] Read Section 7 of `planing-and-sessions/exam-details.md` and prepare answers for sample questions
- [ ] Time the full cold-start: must complete in under 10 minutes

---

## Manual flow test — run this yourself (full submission check)

```bash
IP=<your-elastic-ip>

# 1. All TA validation checks from exam spec
curl http://$IP:8000/health
curl -X POST http://$IP:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json
curl http://$IP:8000/metrics | grep prediction_requests_total

# 2. Rollback endpoint
curl http://$IP:8000/rollback
curl http://$IP:8000/health   # model_version should have changed

# 3. Burst test — check Grafana updates live
for i in $(seq 1 50); do
  curl -s -X POST http://$IP:8000/predict \
    -H "Content-Type: application/json" \
    -d @training/sample_request.json > /dev/null
done
open http://$IP:3000   # watch panels update

# 4. Kill FastAPI — watch Prometheus alert fire
# 5. Restart — watch alert clear

# 6. Verify AWS tags
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=modelserve" \
  --query 'Reservations[].Instances[].InstanceId'
```

All pass? → **Final commit and push:**
```bash
git add docs/ README.md app/main.py
git commit -m "docs: complete ARCHITECTURE.md, runbook, ADRs, rollback endpoint"
git push
# Then: pulumi destroy --yes
```

---

## TA Demo Script (quick reference)

| Minute | Action |
|--------|--------|
| 0–10 | Fresh sandbox, trigger CI/CD pipeline |
| 10–25 | Walk TA through ARCHITECTURE.md + diagrams + ADRs |
| 25–40 | `/health`, `/predict`, open Grafana, show live traffic |
| 40–55 | Kill container → alert fires; `/rollback`; add field + push |
| 55–60 | Q&A + `pulumi destroy` |

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
