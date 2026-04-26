# Session 01 — Model Training & MLflow Setup

> Phase: **Phase 1 — Model & MLflow Foundation**
> Plan ref: `plans/modelserve-plan.md#phase-1`

**Status:** `[ ] Not Started`

---

## Goal

By the end of this session: a trained fraud-detection model is registered in MLflow as `Production`, and `features.parquet` + `sample_request.json` are exported and committed.

---

## Checklist

- [ ] `data/fraudTrain.csv` downloaded from Kaggle to local `data/` directory
- [ ] `data/` added to `.gitignore`
- [ ] `docker compose up postgres mlflow` starts cleanly (Postgres + MLflow only)
- [ ] MLflow UI accessible at `http://localhost:5000`
- [ ] `python training/train.py` runs to completion without errors
- [ ] MLflow UI shows at least one experiment run with logged parameters
- [ ] Metrics logged: accuracy, precision, recall, F1, ROC-AUC
- [ ] Model `fraud-detector` registered in MLflow Model Registry
- [ ] Model version transitioned to `Production` stage
- [ ] `training/features.parquet` exported (contains `cc_num`, `event_timestamp`, ≥5 feature columns)
- [ ] `training/sample_request.json` exported with a valid `cc_num` value
- [ ] Second run of `train.py` registers a new version with comparable metrics (reproducibility)
- [ ] ROC-AUC ≥ 0.85 on test split

---

## Manual flow test — run this yourself

```bash
# 1. MLflow UI shows the model
open http://localhost:5000

# 2. Model is in Production stage (check in UI under Models > fraud-detector)

# 3. Exported files exist
ls -lh training/features.parquet training/sample_request.json

# 4. sample_request.json contains a valid cc_num
cat training/sample_request.json
```

All pass? → **Commit and push:**
```bash
git add training/features.parquet training/sample_request.json training/train.py
git commit -m "feat: train fraud-detector model and export features"
git push
```

---

## Capture decisions now (feeds ADR-3)

Before finishing this session, jot these down in `docs/ARCHITECTURE.md` while they're fresh:

- [ ] Which model algorithm did you choose and why? (RandomForest / XGBoost / LightGBM)
- [ ] Which features did you include and which did you drop, and why?
- [ ] Why Postgres as the MLflow backend store?
- [ ] Why S3 for the artifact store (vs local volume in production)?

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
