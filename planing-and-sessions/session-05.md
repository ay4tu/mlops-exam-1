# Session 05 — Pulumi Infrastructure: VPC, EC2, S3, ECR

> Phase: **Phase 4 — Pulumi Cloud Infrastructure** (part 1)
> Plan ref: `plans/modelserve-plan.md#phase-4`

**Status:** `[x] Complete`

**Prerequisite:** Session 04 complete ✓

---

## Goal

By the end of this session: `pulumi up` provisions a VPC, public subnet, security group, EC2 instance (t3.small), Elastic IP, S3 bucket, and ECR repository on AWS — all tagged with `Project: modelserve`.

---

## Checklist

### Pulumi Setup
- [x] `infrastructure/Pulumi.yaml` configured with correct project name
- [x] `infrastructure/requirements.txt` lists required Pulumi packages
- [x] AWS credentials configured locally (`aws configure` or environment variables)
- [x] `pulumi stack init` completed for the dev/prod stack

### AWS Resources (via `pulumi up`)
- [x] VPC created with a public subnet
- [x] Internet Gateway attached to VPC
- [x] Route table configured for public internet access
- [x] Security group created with inbound rules:
  - [x] Port 22 (SSH) — restricted CIDR only (configurable via `ssh_cidr` config)
  - [x] Port 8000 (FastAPI)
  - [x] Port 3000 (Grafana)
  - [x] Port 5000 (MLflow)
  - [x] Port 9090 (Prometheus)
  - [x] All other inbound: DENY
- [x] EC2 instance (`t3.small`) launched in public subnet with security group
- [x] Elastic IP allocated and associated with EC2 instance
- [x] S3 bucket created for MLflow artifacts + Feast offline store
- [x] ECR repository created with `force_delete=True`
- [x] All resources tagged: `{"Project": "modelserve"}`

### Stack Outputs
- [x] `pulumi stack output` shows: EC2 public IP, ECR repository URL, S3 bucket name

### Verification
- [x] `pulumi up --yes` runs to completion without errors
- [x] EC2 instance visible and running in AWS console
- [x] S3 bucket visible in AWS console
- [x] ECR repository visible in AWS console
- [x] SSH to EC2 instance succeeds
- [ ] `pulumi destroy --yes` cleanly removes all resources (no orphaned resources)

---

## Manual flow test — run this yourself

```bash
# 1. Generate SSH key (once)
ssh-keygen -t rsa -b 4096 -f infrastructure/mlops-key -N ""
export SSH_PUBLIC_KEY="$(cat infrastructure/mlops-key.pub)"

# 2. Provision infrastructure
cd infrastructure && pulumi up --yes

# 3. Check stack outputs
pulumi stack output

# 4. SSH into EC2
ssh -i infrastructure/mlops-key ec2-user@$(cd infrastructure && pulumi stack output instance_ip)

# 5. Verify resources tagged in AWS console
aws ec2 describe-instances --filters "Name=tag:Project,Values=modelserve" \
  --query 'Reservations[].Instances[].InstanceId'

# 6. Destroy cleanly
cd infrastructure && pulumi destroy --yes
```

All pass? → **Commit and push:**
```bash
git add infrastructure/
git commit -m "feat: Pulumi VPC, EC2, S3, ECR infrastructure"
git push
```

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
