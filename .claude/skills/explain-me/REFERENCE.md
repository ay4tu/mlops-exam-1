# Explain Me — TA Question Bank

Sample questions from the exam spec (Section 7) with the answer structure to use.
For each: read the actual code first, then adapt the template to what was actually built.

---

## Model & Training

**"Walk me through train.py. What metrics did you log and why?"**
- What: describe the data load → feature engineering → split → train → log → register flow
- Why those metrics: accuracy alone misleads on imbalanced data (0.5% fraud rate) → ROC-AUC + precision/recall tell the real story
- Follow-up: "How would you decide this model is good enough to deploy?" → AUC threshold + business cost of false negatives

**"Your FastAPI service loads the model on startup. What's the trade-off vs loading per request?"**
- Startup load: fast predictions, but slow cold start; model version locked until restart
- Per-request load: always latest version, but ~200–500ms extra latency per call + S3 costs
- Follow-up: "How would you handle a model too big for memory?" → streaming prediction, model sharding, or a dedicated inference server

**"Why pull the model from MLflow Registry instead of baking it into the Docker image?"**
- Baking in: faster startup, no registry dependency, but forces a full image rebuild + redeploy for every model update
- Registry pull: decouple model lifecycle from service lifecycle — retrain and promote without touching the container
- Follow-up: "What are the risks of registry pull?" → registry downtime blocks cold start → mitigate with a local cache fallback

---

## Feature Store

**"Why is Feast in this stack at all? What would break if you replaced it with a direct Redis client?"**
- Feast provides: training/serving consistency (same feature definitions used for both), entity row abstraction, offline-to-online materialisation pipeline
- Without Feast: direct Redis calls — fast, but you lose the guarantee that training features == serving features → silent model drift
- Follow-up: "When would you NOT use a feature store?" → low-cardinality features, features computed at request time, very small team

**"Walk me through what happens between a POST /predict request and the response."**
1. Request hits FastAPI → Pydantic validates `entity_id`
2. `feature_client.py` calls `feast.get_online_features(entity_rows=[{"cc_num": entity_id}])`
3. Feast queries Redis → returns feature vector
4. `model_loader.py` model (loaded at startup) runs `predict_proba` on the vector
5. Prometheus metrics incremented (counter, histogram)
6. Response JSON built with prediction, probability, model version, timestamp

---

## Infrastructure & Deployment

**"Why did you choose this deployment topology?"**
- Single EC2: simple to reason about, one network boundary, easy to demo cold-start in 10 min
- Trade-off: single point of failure, all services compete for the same CPU/RAM
- What I would change with more time: separate the inference service onto its own instance behind a load balancer

**"Walk me through the security group. Which ports are open and to whom?"**
- 8000 (FastAPI), 3000 (Grafana), 5000 (MLflow), 9090 (Prometheus) open to 0.0.0.0/0 for the demo
- 22 (SSH) open to a restricted CIDR only
- Production hardening: 5000 and 9090 should be internal only; Grafana behind auth

**"What's in the user-data script? What happens if it fails halfway through?"**
- Installs Docker, clones repo, runs docker compose up
- If it fails: instance starts but no containers → health check fails → CI deploy job catches it via /health verification
- Recovery: SSH in, check `/var/log/cloud-init-output.log`, re-run the failed step

**"If the deployment target died right now, walk me through recovery."**
1. `pulumi up` provisions a new EC2 instance (Elastic IP reassigns automatically)
2. User-data script bootstraps Docker + pulls containers
3. MLflow pulls model from S3 (no data loss — artifact store is S3)
4. Feast materialises features from S3 offline store back into Redis
5. Total time: ~5–10 min; data loss: none (stateless compute, stateful data in S3)

---

## CI/CD

**"Why destroy-and-recreate vs incremental update?"**
- Chose incremental (`pulumi up`): faster, no downtime, sufficient for a single-node setup
- Destroy-and-recreate is cleaner for stateless infra but overkill here — takes 5+ min and causes service interruption
- When to switch: if infrastructure drift becomes a real problem or for blue/green deployments

**"Walk me through every step from git push to new version serving traffic."**
1. `git push origin main` triggers GitHub Actions
2. `test` job: pytest runs against the FastAPI service
3. `build-and-push` job: Docker image built, tagged with commit SHA, pushed to ECR
4. `trivy-scan` job: image scanned for CVEs
5. `deploy` job: SSHes into EC2, pulls new image, restarts docker compose, hits /health
6. If /health returns 200: pipeline green. If not: job fails, previous container still running

**"What happens if someone pushes a commit that breaks the test suite?"**
- `test` job fails → `build-and-push` job never runs (`needs: test`)
- No new image is pushed, no deploy happens
- Previous version continues serving traffic uninterrupted

---

## Observability

**"Show me the Prometheus alert rules. Why did you pick those thresholds?"**
- High latency: p95 > Xms — chosen based on baseline p95 observed during load testing
- High error rate: > Y% over 5 min — chosen as a threshold that would never trigger on healthy traffic
- Service down: target unreachable for > 1 min — fast enough to catch a crash before users notice
- Honest answer: thresholds are estimates; in production you tune them from real traffic histograms

**"Your S3 bucket holds MLflow artifacts and Feast offline data. What would go wrong if the IAM role lost S3 read permissions?"**
- Immediate: FastAPI startup fails on next cold start (cannot load model from S3)
- Feast materialisation: fails silently — online store goes stale
- Detection: Prometheus `prediction_errors_total` spikes; /health returns unhealthy
- Fix: check IAM role in AWS console, re-attach policy, restart service

---

## Debugging Under Pressure

When the TA asks you to do something live and it breaks:
1. Say out loud what you expected to happen
2. State the first place you would look (`docker compose logs <service>`, `/metrics`, Grafana)
3. Narrow down: is it the container, the network, or the application?
4. Fix or explain why you cannot fix it in the time available

Never go silent. Narrating your debugging process scores points even if the fix fails.
