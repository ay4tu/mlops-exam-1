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
- [ ] All changes pushed to GitHub

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
