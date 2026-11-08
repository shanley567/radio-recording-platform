# Radio Recording Platform

A cloud-native synthetic data acquisition and recording platform designed to simulate continuous radio recording workloads using modern DevOps, SRE, Kubernetes, Terraform, and AWS practices.

The project is being built incrementally using Infrastructure as Code and follows a production-style development approach where each layer is validated before additional complexity is introduced.

---

# Project Purpose

The original use case is a platform capable of:

- Continuously recording radio streams
- Persisting recordings to durable storage
- Scaling as stream count increases
- Detecting recording gaps
- Providing operational visibility
- Running with minimal manual intervention

To simplify development and testing, synthetic recording segments are generated instead of real radio streams.

These synthetic recordings allow the platform's architecture, observability, scalability and reliability to be demonstrated without depending on external radio providers.

---

# Current Status

## Infrastructure

### Implemented

- Terraform Repository Structure
- AWS Provider Configuration
- Variable-driven Terraform deployment
- Amazon S3 Recording Bucket
- S3 Versioning
- S3 Encryption
- S3 Public Access Blocking
- Amazon ECR Repository
- AWS VPC
- Private Subnets
- Public Subnets
- NAT Gateway
- Internet Gateway
- Route Tables
- Security Groups

### In Progress

- Amazon EKS Cluster
- EKS Managed Node Group

### Planned

- IRSA
- OIDC Authentication
- Cluster Autoscaler
- Multi-Node Worker Pools

---

## Application

### Implemented

- Python Synthetic Generator
- Docker Containerisation
- Synthetic Recording Generation
- S3 Upload Integration
- Structured S3 Object Storage

Generator creates synthetic recording metadata similar to:

```json
{
  "station_id": "station-001",
  "timestamp": "2026-11-08T15:00:00Z",
  "signal_strength": 97,
  "status": "SUCCESS"
}
```

---

## CI/CD

### Implemented

GitHub Actions workflows:

#### Terraform Validation

Validates:

- terraform fmt
- terraform init
- terraform validate

#### Docker Build Validation

Validates:

- Docker image builds successfully

### Planned

- TFLint
- Checkov
- Trivy
- Automated Container Publishing
- Kubernetes Deployment Workflow
- Smoke Tests

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
│   ├── Dockerfile
│   └── stations.yaml
│
├── docs
│
├── kubernetes
│
├── terraform
│   ├── providers.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   ├── storage.tf
│   ├── ecr.tf
│   ├── networking.tf
│   ├── eks.tf
│   └── outputs.tf
│
└── README.md
```

---

# Current Architecture

```text
                    GitHub

                       │

                       ▼

                GitHub Actions

                       │

                       ▼

                  Terraform

          ┌────────────┼────────────┐

          ▼            ▼            ▼

         S3           ECR          VPC

          ▲

          │

  Synthetic Generator

          │

          ▼

   Synthetic Records
```

---

# Synthetic Recording Workflow

Current application workflow:

```text
Generator Starts

      │

      ▼

Generate Synthetic Record

      │

      ▼

Write Local JSON File

      │

      ▼

Upload To S3

      │

      ▼

Delete Local File
```

---

# S3 Storage Structure

Recordings are stored in a time-partitioned structure:

```text
station-001/

└── 2026/
    └── 11/
        └── 08/
            └── 15/
                ├── xxxx.json
                ├── xxxx.json
                └── xxxx.json
```

Benefits:

- Easier retention management
- Faster navigation
- Time-based partitioning
- Data lake style organisation

---

# ECR Integration

Implemented:

```text
Build Container
       │
       ▼
Push To ECR
       │
       ▼
Store Versioned Container Image
```

Repository:

```text
synthetic-generator
```

Container images are successfully built and published to Amazon ECR.

---

# Kubernetes Progress

## Current State

The EKS control plane has been successfully provisioned.

Verified:

```text
Cluster Status: ACTIVE
```

Networking components:

```text
VPC
Private Subnets
Public Subnets
NAT Gateway
Security Groups
```

have been successfully deployed.

---

## Current Blocker

Managed Node Group deployment identified a launch failure.

### Root Cause

Initial node configuration used:

```text
t3.medium
```

The AWS account rejected the launch because:

```text
The specified instance type is not eligible for Free Tier
```

AWS Auto Scaling activity logs were used to identify the exact failure reason.

### Planned Resolution

Switch worker nodes to:

```text
t3.micro
```

or

```text
t3a.micro
```

allowing successful worker node creation.

This troubleshooting exercise provided valuable experience investigating:

- EKS Node Groups
- Auto Scaling Groups
- EC2 Launch Failures
- Terraform State
- AWS Service Diagnostics

---

# Lessons Learned

## Terraform State Management

Encountered:

```text
Resource exists in AWS
Terraform state unaware
```

Resolved using:

```bash
terraform import
```

where appropriate.

---

## S3 Versioning

Version-enabled buckets cannot be deleted while object versions remain present.

Improvement implemented:

```terraform
force_destroy = true
```

for development environments.

---

## Region Consistency

Standardised project deployment region:

```text
eu-west-2
```

This eliminated regional mismatches between:

- AWS CLI
- Terraform
- ECR
- EKS

---

## EKS Troubleshooting

Successfully diagnosed node launch failures using:

```bash
aws eks describe-nodegroup

aws autoscaling describe-auto-scaling-groups

aws autoscaling describe-scaling-activities
```

This highlighted the importance of using cloud-native diagnostics rather than relying solely on Terraform output.

---

# Local Development

## Install Dependencies

```powershell
python -m pip install -r app\requirements.txt
```

---

## Run Generator

```powershell
cd app

python generator.py
```

---

## Build Container

```powershell
docker build -t synthetic-generator ./app
```

---

## Push Image

```powershell
docker push <ecr-repository-uri>
```

---

# Infrastructure Management

## Initialise Terraform

```powershell
terraform init
```

---

## Review Changes

```powershell
terraform plan
```

---

## Deploy

```powershell
terraform apply
```

---

## Destroy

```powershell
terraform destroy
```

---

# Project Roadmap

## Phase 1 ✅

- Repository Setup
- GitHub Workflows
- Terraform Foundation
- S3 Storage
- Synthetic Generator
- Docker Build
- ECR Repository
- ECR Push

---

## Phase 2 ✅

- VPC
- Private Networking
- Internet Gateway
- NAT Gateway

---

## Phase 3 🚧

- EKS Cluster
- Managed Node Group
- Kubectl Connectivity
- Generator Deployment

---

## Phase 4

- Prometheus
- Grafana
- AlertManager

---

## Phase 5

- Recording Gap Detection
- Business Metrics
- SLOs
- Error Budgets
- Runbooks

---

## Phase 6

- OIDC
- IRSA
- Security Hardening
- Multi-Environment Terraform
- Production CI/CD

---

# Technologies

- AWS
- Terraform
- Amazon S3
- Amazon ECR
- Amazon EKS
- Python
- Docker
- GitHub Actions
- Kubernetes

---

# Key DevOps & SRE Skills Demonstrated

- Infrastructure as Code
- Terraform State Management
- AWS Networking
- Containerisation
- CI/CD Automation
- Cloud Architecture
- Kubernetes Operations
- S3 Storage Design
- Troubleshooting & Root Cause Analysis
- Cost Optimisation
- Platform Engineering Principles

---

# Current Resume Point

Next session objectives:

1. Fix Node Group instance type sizing
2. Complete EKS worker provisioning
3. Obtain successful `kubectl get nodes`
4. Deploy synthetic generator to Kubernetes
5. Verify generator uploads to S3 from EKS

Once those milestones are complete, the project will transition from infrastructure provisioning into an operational Kubernetes platform.