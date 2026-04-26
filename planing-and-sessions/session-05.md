# Session 05 — Pulumi Infrastructure: VPC, EC2, S3, ECR

> Phase: **Phase 4 — Pulumi Cloud Infrastructure** (part 1)
> Plan ref: `plans/modelserve-plan.md#phase-4`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 04 complete ✓

---

## Goal

By the end of this session: `pulumi up` provisions a VPC, public subnet, security group, EC2 instance (t3.small), Elastic IP, S3 bucket, and ECR repository on AWS — all tagged with `Project: modelserve`.

---

## Checklist

### Pulumi Setup
- [ ] `infrastructure/Pulumi.yaml` configured with correct project name
- [ ] `infrastructure/requirements.txt` lists required Pulumi packages
- [ ] AWS credentials configured locally (`aws configure` or environment variables)
- [ ] `pulumi stack init` completed for the dev/prod stack

### AWS Resources (via `pulumi up`)
- [ ] VPC created with a public subnet
- [ ] Internet Gateway attached to VPC
- [ ] Route table configured for public internet access
- [ ] Security group created with inbound rules:
  - [ ] Port 22 (SSH) — restricted CIDR only
  - [ ] Port 8000 (FastAPI)
  - [ ] Port 3000 (Grafana)
  - [ ] Port 5000 (MLflow)
  - [ ] Port 9090 (Prometheus)
  - [ ] All other inbound: DENY
- [ ] EC2 instance (`t3.small`) launched in public subnet with security group
- [ ] Elastic IP allocated and associated with EC2 instance
- [ ] S3 bucket created for MLflow artifacts + Feast offline store
- [ ] ECR repository created with `force_delete=True`
- [ ] All resources tagged: `{"Project": "modelserve"}`

### Stack Outputs
- [ ] `pulumi stack output` shows: EC2 public IP, ECR repository URL, S3 bucket name

### Verification
- [ ] `pulumi up --yes` runs to completion without errors
- [ ] EC2 instance visible and running in AWS console
- [ ] S3 bucket visible in AWS console
- [ ] ECR repository visible in AWS console
- [ ] SSH to EC2 instance succeeds
- [ ] `pulumi destroy --yes` cleanly removes all resources (no orphaned resources)
- [ ] All changes pushed to GitHub

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
