# Session 04 — Prometheus & Grafana Observability

> Phase: **Phase 3 — Containerisation & Observability** (part 2)
> Plan ref: `plans/modelserve-plan.md#phase-3`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 03 complete ✓

---

## Goal

By the end of this session: Prometheus scrapes FastAPI metrics, Grafana loads a provisioned dashboard automatically on `docker compose up`, and three alert rules are visible and configured.

---

## Checklist

### Prometheus
- [ ] `monitoring/prometheus/prometheus.yml` scrape config targets FastAPI on port 8000
- [ ] `monitoring/prometheus/alerts.yml` defines at least 3 alert rules:
  - [ ] High latency (p95 > threshold)
  - [ ] High error rate
  - [ ] Service down (FastAPI unreachable)
- [ ] Prometheus added to `docker-compose.yml` with correct volume mounts
- [ ] Prometheus UI at `http://localhost:9090` shows FastAPI target as `UP`
- [ ] All three alert rules visible at `http://localhost:9090/alerts`

### Grafana
- [ ] `monitoring/grafana/provisioning/datasources/prometheus.yml` configures Prometheus as datasource
- [ ] `monitoring/grafana/provisioning/dashboards/dashboard.yml` points to dashboard JSON directory
- [ ] `monitoring/grafana/dashboards/modelserve-overview.json` contains the dashboard definition
- [ ] Grafana added to `docker-compose.yml` with provisioning volumes mounted
- [ ] Grafana at `http://localhost:3000` loads dashboard automatically (no manual setup)
- [ ] Dashboard panels present and showing data after 10+ requests:
  - [ ] Prediction latency p50
  - [ ] Prediction latency p95
  - [ ] Prediction latency p99
  - [ ] Request rate
  - [ ] Error rate
  - [ ] Model version
  - [ ] Feast hit/miss ratio

### End-to-End Verification
- [ ] `docker compose up` (fresh) brings up full stack including Prometheus and Grafana
- [ ] Send 20+ requests to `/predict` and verify all dashboard panels update live
- [ ] Kill the FastAPI container — verify the service-down alert fires within expected time
- [ ] Restart FastAPI — verify alert clears
- [ ] All changes pushed to GitHub

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
