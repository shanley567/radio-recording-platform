# Radio Recording Platform

A cloud-native synthetic data recording platform designed to simulate continuous radio stream recording workloads.

The platform continuously generates synthetic recording segments, stores outputs in Amazon S3, and is being developed using Infrastructure as Code, containerisation, CI/CD, and Kubernetes-based deployment patterns.

This project is intended to demonstrate production-style DevOps, SRE, Cloud Engineering, and Platform Engineering practices.

---

## Project Objectives

The original business requirement is to support a platform that:

- Runs continuously (24/7)
- Records large numbers of radio streams
- Stores recordings in object storage
- Automatically scales with workload demand
- Detects gaps in generated recordings
- Provides operational visibility and monitoring
- Is fully managed via Infrastructure as Code

To simplify development and testing, radio recording workloads are currently represented using synthetic data generators that emulate recording activity.

---

## Current Status

### Completed

#### Repository & CI/CD

- GitHub repository created
- Branch-based development workflow established
- GitHub Actions configured
- Terraform validation workflow
- Docker build validation workflow

#### Infrastructure

Provisioned using Terraform:

- Amazon S3 Bucket
- S3 Versioning
- S3 Encryption
- S3 Public Access Blocking
- Amazon ECR Repository
- VPC
- Public Subnets
- Private Subnets
- NAT Gateway
- Internet Gateway
- Route Tables

#### Application

- Python synthetic recording generator
- Docker containerisation
- Container image stored in Amazon ECR
- Synthetic records uploaded to Amazon S3

---

### In Progress

- Kubernetes deployment architecture
- EKS cluster provisioning
- Pod deployment strategy

---

### Planned

#### Platform

- Amazon EKS
- Managed Node Groups
- Cluster Autoscaler

#### Observability

- Prometheus
- Grafana
- AlertManager

#### SRE Features

- Recording gap detection
- Service Level Objectives (SLOs)
- Error budgets
- Alerting strategy
- Runbooks

#### Security

- GitHub OIDC
- IRSA
- Least-privilege IAM
- Network Policies
- Secrets Management

---

# Architecture

Current architecture:

```text
                    GitHub
                       │
                       ▼

                GitHub Actions
                       │
                       ▼

                  Terraform
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼

       Amazon S3                Amazon ECR
         ▲                           ▲
         │                           │
         └─────────────┬─────────────┘
                       │

               Synthetic Generator

                       │

               JSON Recording Files
```

Target architecture:

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

                         AWS

            ┌───────────────────────────┐
            │            EKS            │
            │                           │
            │ Generator Pods            │
            │                           │
            └─────────────┬─────────────┘
                          │

                          ▼

                        S3

                          │

                          ▼

                Monitoring Stack

                 Prometheus
                 Grafana
                 AlertManager
```

---

# Repository Structure

```text
radio-recording-platform/

├── .github
│   └── workflows
│       ├── build.yml
│       └── terraform.yml
│
├── app
│   ├── generator.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs
│
├── kubernetes
│
├── terraform
│
└── README.md
```

---

# Local Development

## Install Dependencies

```powershell
python -m pip install -r app\requirements.txt
```

## Run Generator

```powershell
cd app

python generator.py
```

## Build Container

```powershell
docker build -t synthetic-generator ./app
```

## Run Container

```powershell
docker run synthetic-generator
```

---

# Infrastructure Deployment

## Initialise Terraform

```powershell
cd terraform

terraform init
```

## Review Changes

```powershell
terraform plan
```

## Deploy Infrastructure

```powershell
terraform apply
```

## Destroy Infrastructure

```powershell
terraform destroy
```

---

# CI/CD

The repository currently contains automated validation workflows.

## Terraform Workflow

Validates:

- Terraform formatting
- Terraform initialization
- Terraform configuration validation

## Build Workflow

Validates:

- Docker image builds successfully

Future enhancements will include:

- TFLint
- Checkov
- Trivy
- Automated ECR pushes
- Kubernetes deployments
- Smoke testing

---

# Current AWS Resources

| Service          | Purpose                  |
| ---------------- | ------------------------ |
| S3               | Recording storage        |
| ECR              | Container registry       |
| VPC              | Network foundation       |
| Subnets          | EKS networking           |
| NAT Gateway      | Outbound internet access |
| Internet Gateway | Public connectivity      |

Deployment Region:

```text
eu-west-2
```

---

# Lessons Learned

## S3 Versioning

Version-enabled buckets cannot be destroyed while object versions remain present.

Future improvements:

```terraform
force_destroy = true
```

for development environments.

## Regional Consistency

All infrastructure is standardised on:

```text
eu-west-2
```

to avoid provider and CLI region mismatches.

---

# Roadmap

## Phase 1 ✅

- Repository Setup
- GitHub Actions
- Terraform Foundation
- S3 Storage
- ECR Registry
- Synthetic Generator

## Phase 2 ✅

- Container Build
- Container Registry Integration
- VPC Networking

## Phase 3

- Amazon EKS
- Kubernetes Deployment
- Generator Pods

## Phase 4

- Prometheus
- Grafana
- Alerting

## Phase 5

- Recording Gap Detection
- SLOs
- Error Budgets
- Runbooks

## Phase 6

- OIDC Authentication
- IRSA
- Security Hardening
- Production Deployment Pipelines

---

# Author

Built as a cloud-native DevOps/SRE portfolio project demonstrating:

- Terraform
- AWS
- Docker
- GitHub Actions
- Kubernetes
- Site Reliability Engineering
- Infrastructure as Code
- Cloud Platform Engineering
