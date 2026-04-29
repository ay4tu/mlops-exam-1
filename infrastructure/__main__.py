import json
import os

import pulumi
import pulumi_aws as aws

# ── Config ──────────────────────────────────────────────────────────────────
config = pulumi.Config()
ssh_cidr = config.get("ssh_cidr") or "0.0.0.0/0"
ssh_public_key = os.environ.get("SSH_PUBLIC_KEY", "")

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

# ── User Data (install Docker + Docker Compose) ───────────────────────────────
user_data = """#!/bin/bash
set -e
yum update -y
amazon-linux-extras install docker -y
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
"""

# ── EC2 Instance ─────────────────────────────────────────────────────────────
instance = aws.ec2.Instance(
    "modelserve-ec2",
    ami=ami.id,
    instance_type="t3.medium",
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    key_name=key_pair.key_name if key_pair else None,
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

# ── Stack Outputs ─────────────────────────────────────────────────────────────
pulumi.export("instance_ip", eip.public_ip)
pulumi.export("ecr_repository_url", ecr_repo.repository_url)
pulumi.export("s3_bucket_name", s3_bucket.bucket)
