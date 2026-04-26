# Session 07 — Cloud Verification & ADR Drafting

> Phase: **Phase 4 — Pulumi Cloud Infrastructure** (part 3) + start of Phase 6 docs
> Plan ref: `plans/modelserve-plan.md#phase-4`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 06 complete ✓

---

## Goal

By the end of this session: the full cloud deployment is verified end-to-end with all acceptance criteria met, and the architecture diagram + initial ADRs are drafted while deployment decisions are still fresh.

---

## Checklist

### Final Cloud Verification
- [ ] Full cold-start test: run `pulumi destroy` → `pulumi up` → verify stack comes up cleanly
- [ ] `curl http://<elastic-ip>:8000/health` returns 200 with correct model version
- [ ] `curl -X POST http://<elastic-ip>:8000/predict -d @training/sample_request.json` returns valid prediction
- [ ] Grafana dashboard shows live data after sending 10+ requests to EC2
- [ ] Prometheus shows all three alert rules configured
- [ ] MLflow UI shows registered model in Production stage
- [ ] AWS resources all tagged `Project: modelserve` (spot check 3+ resources in console)
- [ ] `pulumi stack output` shows all expected outputs (IP, ECR URL, S3 bucket)
- [ ] `pulumi destroy --yes` completes cleanly

### Architecture Diagram (draft)
- [ ] Draft created in `docs/diagrams/` (any tool: draw.io, Excalidraw, ASCII)
- [ ] Diagram shows: all components, where each runs (local vs EC2), ports, communication arrows
- [ ] Local development topology and production (EC2) topology both represented
- [ ] Diagram committed to repo (image file or source file)

### ADR Drafts (initial — will be polished in Session 10)
- [ ] ADR-1: Deployment topology (why single EC2, trade-offs) — drafted in `docs/ARCHITECTURE.md`
- [ ] ADR-2: CI/CD strategy (incremental update + hybrid trigger) — drafted
- [ ] ADR-3: Data architecture (Postgres for MLflow, Redis for Feast, S3 for artifacts) — drafted
- [ ] ADR-4: Containerisation (base image, multi-stage, image size) — drafted
- [ ] ADR-5: Monitoring design (alert thresholds, dashboard choices, gaps) — drafted
---

## Manual flow test — run this yourself

```bash
# 1. Cold-start: destroy then reprovision
cd infrastructure && pulumi destroy --yes && pulumi up --yes

# 2. Hit all endpoints on EC2
IP=$(pulumi stack output instance_ip)
curl http://$IP:8000/health
curl -X POST http://$IP:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json
curl http://$IP:9090/targets  # Prometheus
open http://$IP:3000          # Grafana

# 3. Clean up
pulumi destroy --yes
```

All pass? → **Commit and push:**
```bash
git add docs/
git commit -m "docs: architecture diagram and initial ADR drafts"
git push
```

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
