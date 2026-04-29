# Session 04 — Prometheus & Grafana Observability

> Phase: **Phase 3 — Containerisation & Observability** (part 2)
> Plan ref: `plans/modelserve-plan.md#phase-3`

**Status:** `[x] Complete`

**Prerequisite:** Session 03 complete ✓

---

## Goal

By the end of this session: Prometheus scrapes FastAPI metrics, Grafana loads a provisioned dashboard automatically on `docker compose up`, and three alert rules are visible and configured.

---

## Checklist

### Prometheus
- [x] `monitoring/prometheus/prometheus.yml` scrape config targets FastAPI on port 8000
- [x] `monitoring/prometheus/alerts.yml` defines at least 3 alert rules:
  - [x] High latency (p95 > threshold)
  - [x] High error rate
  - [x] Service down (FastAPI unreachable)
- [x] Prometheus added to `docker-compose.yml` with correct volume mounts
- [x] Prometheus UI at `http://localhost:9090` shows FastAPI target as `UP`
- [x] All three alert rules visible at `http://localhost:9090/alerts`

### Grafana
- [x] `monitoring/grafana/provisioning/datasources/prometheus.yml` configures Prometheus as datasource
- [x] `monitoring/grafana/provisioning/dashboards/dashboard.yml` points to dashboard JSON directory
- [x] `monitoring/grafana/dashboards/modelserve-overview.json` contains the dashboard definition
- [x] Grafana added to `docker-compose.yml` with provisioning volumes mounted
- [x] Grafana at `http://localhost:3000` loads dashboard automatically (no manual setup)
- [x] Dashboard panels present and showing data after 10+ requests:
  - [x] Prediction latency p50
  - [x] Prediction latency p95
  - [x] Prediction latency p99
  - [x] Request rate
  - [x] Error rate
  - [x] Model version
  - [x] Feast hit/miss ratio

### End-to-End Verification
- [x] `docker compose up` (fresh) brings up full stack including Prometheus and Grafana
- [x] Send 20+ requests to `/predict` and verify all dashboard panels update live
- [x] Kill the FastAPI container — verify the service-down alert fires within expected time
- [x] Restart FastAPI — verify alert clears

---

## Manual flow test — run this yourself

```bash
# 1. Fresh stack up
docker compose down && docker compose up -d

# 2. Prometheus shows FastAPI as UP
open http://localhost:9090/targets

# 3. Three alert rules visible
open http://localhost:9090/alerts

# 4. Send 20 requests to populate Grafana
for i in $(seq 1 20); do
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d @training/sample_request.json > /dev/null
done

# 5. Open Grafana — dashboard loads automatically, panels show data
open http://localhost:3000

# 6. Kill FastAPI and watch alert fire (check Prometheus alerts page after ~1 min)
docker compose stop fastapi
```

All pass? → **Commit and push:**
```bash
git add monitoring/ docker-compose.yml
git commit -m "feat: Prometheus scraping, Grafana dashboard, alert rules"
git push
```

---

## Capture decisions now (feeds ADR-5)

Before finishing this session, jot these down in `docs/ARCHITECTURE.md`:

- [ ] What are your alert thresholds (latency, error rate) and how did you pick them?
- [ ] What does the dashboard prioritise and why (what's most useful to show first)?
- [ ] What is intentionally NOT on the dashboard that a real system would need?
- [ ] Why provision Grafana from files rather than manual setup?

---

## Notes

- Alert thresholds: p95 latency > 500ms (5 min window), error rate > 5% (2 min window), FastAPI down for 1 min
- FastAPIDown alert goes Pending (yellow) immediately on container stop, turns Firing (red) after 1 minute
- Grafana provisioned from files — datasource and dashboard load automatically on `docker compose up`, no manual UI steps
- Dashboard panels: latency p50/p95/p99, request rate, error rate, Feast hit/miss ratio, model version
