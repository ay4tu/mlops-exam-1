import json
import os

import pulumi
import pulumi_aws as aws

# ── Config ──────────────────────────────────────────────────────────────────
config = pulumi.Config()
ssh_cidr = config.get("ssh_cidr") or "0.0.0.0/0"
ssh_public_key = os.environ.get("SSH_PUBLIC_KEY", "")
github_repo = config.get("github_repo") or ""

region = aws.get_region().region

tags = {"Project": "modelserve"}

# ── VPC ──────────────────────────────────────────────────────────────────────
vpc = aws.ec2.Vpc(
    "modelserve-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**tags, "Name": "modelserve-vpc"},
)

# ── Internet Gateway ─────────────────────────────────────────────────────────
igw = aws.ec2.InternetGateway(
    "modelserve-igw",
    vpc_id=vpc.id,
    tags={**tags, "Name": "modelserve-igw"},
)

# ── Public Subnet ────────────────────────────────────────────────────────────
subnet = aws.ec2.Subnet(
    "modelserve-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=f"{region}a",
    map_public_ip_on_launch=True,
    tags={**tags, "Name": "modelserve-subnet"},
)

# ── Route Table ──────────────────────────────────────────────────────────────
route_table = aws.ec2.RouteTable(
    "modelserve-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={**tags, "Name": "modelserve-rt"},
)

aws.ec2.RouteTableAssociation(
    "modelserve-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

# ── Security Group ───────────────────────────────────────────────────────────
sg = aws.ec2.SecurityGroup(
    "modelserve-sg",
    vpc_id=vpc.id,
    description="ModelServe security group",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=[ssh_cidr],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="FastAPI",
            from_port=8000,
            to_port=8000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="Grafana",
            from_port=3000,
            to_port=3000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="MLflow",
            from_port=5000,
            to_port=5000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="Prometheus",
            from_port=9090,
            to_port=9090,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={**tags, "Name": "modelserve-sg"},
)

# ── Key Pair ─────────────────────────────────────────────────────────────────
key_pair = None
if ssh_public_key:
    key_pair = aws.ec2.KeyPair(
        "modelserve-key",
        key_name="modelserve-key",
        public_key=ssh_public_key,
        tags=tags,
    )

# ── IAM Role (S3 + ECR access for EC2) ───────────────────────────────────────
ec2_role = aws.iam.Role(
    "modelserve-ec2-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "ec2.amazonaws.com"},
        }],
    }),
    tags=tags,
)

aws.iam.RolePolicy(
    "modelserve-s3-ecr-policy",
    role=ec2_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:DescribeRepositories",
                    "ecr:ListImages",
                ],
                "Resource": "*",
            },
        ],
    }),
)

instance_profile = aws.iam.InstanceProfile(
    "modelserve-instance-profile",
    role=ec2_role.name,
)

# ── AMI (Amazon Linux 2) ─────────────────────────────────────────────────────
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["amzn2-ami-hvm-*-x86_64-gp2"]),
    ],
)

# ── S3 Bucket (MLflow artifacts + Feast offline store) ───────────────────────
s3_bucket = aws.s3.Bucket(
    "modelserve-artifacts",
    force_destroy=True,
    tags=tags,
)

# ── ECR Repository ───────────────────────────────────────────────────────────
ecr_repo = aws.ecr.Repository(
    "modelserve-app",
    name="modelserve-app",
    force_delete=True,
    tags=tags,
)

# ── User Data ────────────────────────────────────────────────────────────────
def _make_user_data(ecr_url: str, s3_bucket_name: str) -> str:
    return f"""#!/bin/bash
set -e
exec > /var/log/bootstrap.log 2>&1

ECR_URL="{ecr_url}"
S3_BUCKET="{s3_bucket_name}"
REGION="{region}"
GITHUB_REPO="{github_repo}"

# ── Docker ────────────────────────────────────────────────────────────────
yum update -y
amazon-linux-extras install docker -y
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# ── Docker Compose ────────────────────────────────────────────────────────
curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \\
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# ── Git ───────────────────────────────────────────────────────────────────
yum install -y git

[ -z "$GITHUB_REPO" ] && {{ echo "No GITHUB_REPO set, skipping clone"; exit 0; }}

# ── Clone repo (idempotent) ───────────────────────────────────────────────
if [ ! -d /home/ec2-user/app ]; then
  git clone "$GITHUB_REPO" /home/ec2-user/app
fi
chown -R ec2-user:ec2-user /home/ec2-user/app

# ── Write .env ────────────────────────────────────────────────────────────
cat > /home/ec2-user/app/.env <<'ENVEOF'
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow
POSTGRES_DB=mlflow
MODEL_NAME=fraud-detector
MODEL_STAGE=Production
ENVEOF
printf 'MLFLOW_S3_BUCKET=%s\\n' "$S3_BUCKET"       >> /home/ec2-user/app/.env
printf 'AWS_DEFAULT_REGION=%s\\n' "$REGION"         >> /home/ec2-user/app/.env
printf 'FASTAPI_IMAGE=%s:latest\\n' "$ECR_URL"      >> /home/ec2-user/app/.env

# ── ECR login + pull FastAPI image ────────────────────────────────────────
aws ecr get-login-password --region "$REGION" | \\
  docker login --username AWS --password-stdin "$ECR_URL"
docker pull "$ECR_URL:latest" || true

# ── Start stack ───────────────────────────────────────────────────────────
cd /home/ec2-user/app
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
"""

user_data = pulumi.Output.all(ecr_repo.repository_url, s3_bucket.bucket).apply(
    lambda args: _make_user_data(args[0], args[1])
)

# ── EC2 Instance ─────────────────────────────────────────────────────────────
instance = aws.ec2.Instance(
    "modelserve-ec2",
    ami=ami.id,
    instance_type="t3.medium",
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    key_name=key_pair.key_name if key_pair else None,
    iam_instance_profile=instance_profile.name,
    user_data=user_data,
    tags={**tags, "Name": "modelserve-ec2"},
)

# ── Elastic IP ───────────────────────────────────────────────────────────────
eip = aws.ec2.Eip(
    "modelserve-eip",
    instance=instance.id,
    domain="vpc",
    tags={**tags, "Name": "modelserve-eip"},
)

# ── Stack Outputs ─────────────────────────────────────────────────────────────
pulumi.export("instance_ip", eip.public_ip)
pulumi.export("ecr_repository_url", ecr_repo.repository_url)
pulumi.export("s3_bucket_name", s3_bucket.bucket)
