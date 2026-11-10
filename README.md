# Radio Recording Platform

A cloud-native synthetic radio recording platform built on AWS and Kubernetes.

The platform continuously generates synthetic radio recording metadata, runs inside Amazon EKS, authenticates using IAM Roles for Service Accounts (IRSA), and stores generated recordings in Amazon S3.

The project demonstrates modern DevOps, Platform Engineering, Cloud Infrastructure, Kubernetes Operations, and Site Reliability Engineering practices using Infrastructure as Code.

---

# Project Status

## MVP COMPLETE ✅

Current end-to-end workflow:

Synthetic Generator

↓

Docker Container

↓

Amazon ECR

↓

Amazon EKS

↓

IRSA Authentication

↓

Amazon S3

---

# Architecture

```text
                  GitHub

                     │

                     ▼

              GitHub Actions

                     │

                     ▼

                 Terraform

                     │

                     ▼

             AWS Infrastructure

        ┌────────────┼────────────┐

        ▼            ▼            ▼

       S3           ECR          EKS

                                  │

                                  ▼

                           Node Group

                                  │

                                  ▼

                        Synthetic Generator

                                  │

                                  ▼

                               IRSA

                                  │

                                  ▼

                                S3
```

---

# Features

## Infrastructure

- Terraform-managed infrastructure
- Amazon VPC
- Public and Private Subnets
- Internet Gateway
- NAT Gateway
- Security Groups
- Amazon EKS
- Managed Node Group
- OIDC Provider
- IAM Roles for Service Accounts (IRSA)

---

## Application

- Python synthetic recording generator
- Docker containerisation
- Structured JSON output
- Continuous generation cycle
- Time-partitioned S3 storage
- Structured application logging

---

## Storage

- Amazon S3
- Versioning enabled
- Server-side encryption enabled
- Public access blocked

Example object path:

```text
station-001/2026/11/10/14/1794317858.json
```

---

## Container Platform

Amazon EKS running:

- VPC CNI
- CoreDNS
- kube-proxy

Deployment:

```text
Namespace:
radio-platform

Deployment:
synthetic-generator

Service Account:
synthetic-generator

Authentication:
IRSA
```

---

# Repository Structure

```text
radio-recording-platform/

├── .github/
│
├── app/
│   ├── Dockerfile
│   ├── generator.py
│   ├── requirements.txt
│   └── stations.yaml
│
├── docs/
│
├── kubernetes/
│   ├── namespace.yaml
│   ├── serviceaccount.yaml
│   └── deployment.yaml
│
├── terraform/
│   ├── networking.tf
│   ├── storage.tf
│   ├── ecr.tf
│   ├── eks.tf
│   ├── iam.tf
│   └── outputs.tf
│
└── README.md
```

---

# Technology Stack

- AWS
- Terraform
- Amazon EKS
- Amazon S3
- Amazon ECR
- Python
- Docker
- Kubernetes
- GitHub Actions

---

# Deployment

## Terraform

```bash
terraform init
terraform plan
terraform apply
```

---

## Build Container

```bash
docker build -t synthetic-generator .
```

---

## Push To ECR

```bash
docker push <ecr-repository>
```

---

## Deploy To Kubernetes

```bash
kubectl apply -f kubernetes/
```

---

# Validation

Verify cluster:

```bash
kubectl get nodes
```

Expected:

```text
STATUS: Ready
```

---

Verify workload:

```bash
kubectl get pods -n radio-platform
```

Expected:

```text
1/1 Running
```

---

Verify S3 uploads:

```bash
aws s3 ls s3://jsp-radio-recordings-bucket-2026-demo --recursive
```

---

# Lessons Learned

Key troubleshooting activities completed:

- EKS Node Group provisioning failures
- EC2 launch diagnostics
- Auto Scaling Group investigation
- Kubernetes node registration troubleshooting
- Missing EKS addon diagnosis
- VPC CNI debugging
- Pod scheduling constraints
- ECR image pull failures
- Docker dependency issues
- IRSA implementation
- Kubernetes to AWS authentication troubleshooting

---

# Roadmap

## Phase 1 ✅ Complete

- Terraform Infrastructure
- EKS
- ECR
- S3
- IRSA
- Synthetic Generator

---

## Phase 2

- Prometheus
- Grafana
- CloudWatch Integration

---

## Phase 3

- Recording Gap Detection
- Alerting
- SLO Monitoring

---

## Phase 4

- Multi-environment deployment
- Production hardening
- Horizontal Pod Autoscaling
- Automated CI/CD deployment