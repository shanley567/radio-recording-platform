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

These synthetic recordings allow the platform's architecture, observability, scalability, and reliability to be demonstrated without depending on external radio providers.

---

# Current Status

## Infrastructure

### Implemented

- Terraform Repository Structure
- AWS Provider Configuration
- Variable-driven Terraform Deployment
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
- Amazon EKS Cluster
- EKS Managed Node Group
- EKS Add-ons
  - VPC CNI
  - CoreDNS
  - kube-proxy
- OIDC Provider
- IAM Roles for Service Accounts (IRSA)
- Kubernetes Namespace
- Kubernetes Service Account
- EKS to S3 Authentication

### In Progress

- Platform Observability
- Prometheus Metrics
- Grafana Dashboards

### Planned

- Recording Gap Detection
- Alerting
- Horizontal Pod Autoscaling
- Multi-Environment Deployment
- Production CI/CD

---

## Application

### Implemented

- Python Synthetic Generator
- Docker Containerisation
- Structured Application Logging
- Synthetic Recording Generation
- Kubernetes Deployment
- IAM-authenticated S3 Uploads (IRSA)
- Structured S3 Object Storage
- Automatic Local File Cleanup

Generator creates synthetic recording metadata similar to:

```json
{
  "station_id": "station-001",
  "timestamp": "2026-11-10T13:00:00Z",
  "signal_strength": 97,
  "status": "SUCCESS"
}
```

Current workflow:

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

      │

      ▼

Repeat Every 10 Seconds
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
│   ├── namespace.yaml
│   ├── serviceaccount.yaml
│   └── deployment.yaml
│
├── terraform
│   ├── providers.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   ├── storage.tf
│   ├── ecr.tf
│   ├── networking.tf
│   ├── eks.tf
│   ├── iam.tf
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

         S3           ECR          EKS

                                      │

                                      ▼

                            Managed Node Group

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

# Synthetic Recording Workflow

Current application workflow:

```text
Generator

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

      │

      ▼

Repeat
```

---

# S3 Storage Structure

Recordings are stored in a time-partitioned structure:

```text
station-001/

└── 2026/
    └── 11/
        └── 10/
            └── 13/
                ├── 1794317730.json
                ├── 1794317737.json
                └── 1794317747.json
```

Benefits:

- Easier retention management
- Faster navigation
- Time-based partitioning
- Data lake style organisation
- Future analytics compatibility

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
       │
       ▼
Deploy To Kubernetes
```

Repository:

```text
synthetic-generator
```

Container images are successfully built, stored in ECR, and deployed to Amazon EKS.

---

# Kubernetes Progress

## Current State

Amazon EKS has been successfully deployed and validated.

Verified:

```text
✅ EKS Cluster Active

✅ Managed Node Group Running

✅ Kubernetes Node Ready

✅ CoreDNS Running

✅ kube-proxy Running

✅ aws-node Running

✅ kubectl Connectivity

✅ Generator Deployment Running

✅ IRSA Authentication Working

✅ S3 Uploads Successful
```

Deployment Components:

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

## Successful End-to-End Workflow

Validated workflow:

```text
Python

   ↓

Docker Image

   ↓

Amazon ECR

   ↓

Amazon EKS

   ↓

IRSA Authentication

   ↓

Amazon S3
```

Verified S3 object creation:

```text
station-001/2026/11/10/13/1794317730.json
station-002/2026/11/10/13/1794317828.json
station-003/2026/11/10/13/1794317869.json
```

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

## Kubernetes Troubleshooting

Successfully diagnosed and resolved:

### EKS Node Group Provisioning Failure

Symptoms:

```text
Node group stuck in CREATING
```

Root Cause:

```text
Unsupported instance type
```

Resolution:

```terraform
instance_types = ["t3.micro"]
```

---

### Node Registration Failure

Symptoms:

```text
NodeCreationFailure
```

Root Cause:

```text
Missing EKS Add-ons
```

Investigation:

```bash
kubectl describe node
aws eks list-addons
```

Resolution:

```text
CoreDNS
kube-proxy
vpc-cni
```

---

### Pod Scheduling Failure

Symptoms:

```text
Pending
```

Error:

```text
Too many pods
```

Root Cause:

```text
t3.micro capacity limitation
```

Resolution:

```text
Increase worker node size
Reduce CoreDNS replicas
```

---

### ECR Deployment Failure

Symptoms:

```text
ImagePullBackOff
```

Root Cause:

```text
Empty ECR repository
```

Resolution:

```bash
docker build
docker push
```

---

### Application Startup Failure

Symptoms:

```text
CrashLoopBackOff
```

Root Cause:

```text
Missing boto3 dependency
```

Resolution:

```text
Install Python dependencies during Docker image build
```

---

### AWS Authentication Failure

Symptoms:

```text
Files generated locally but not uploaded to S3
```

Investigation:

```python
boto3.client("sts").get_caller_identity()
```

Result:

```text
NoCredentialsError
```

Root Cause:

```text
Kubernetes workload lacked AWS credentials
```

Resolution:

```text
Implemented IRSA
IAM Role
OIDC Trust
Service Account Annotation
```

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

## Phase 3 ✅

- EKS Cluster
- Managed Node Group
- Kubernetes Networking
- Kubectl Connectivity
- Generator Deployment
- EKS Add-ons

---

## Phase 4 ✅

- OIDC Provider
- IAM Roles for Service Accounts (IRSA)
- Secure Kubernetes Authentication
- End-to-End Recording Pipeline

---

## Phase 5 🚧

- Prometheus
- Grafana
- CloudWatch Integration

---

## Phase 6

- Recording Gap Detection
- Business Metrics
- SLOs
- Error Budgets
- Runbooks

---

## Phase 7

- Multi-Environment Terraform
- Horizontal Pod Autoscaling
- Production CI/CD
- Security Hardening

---

# Technologies

- AWS
- Terraform
- Amazon S3
- Amazon ECR
- Amazon EKS
- IAM Roles for Service Accounts (IRSA)
- Python
- Docker
- Kubernetes
- GitHub Actions

---

# Key DevOps & SRE Skills Demonstrated

- Infrastructure as Code
- Terraform State Management
- AWS Networking
- EKS Operations
- Kubernetes Troubleshooting
- Containerisation
- CI/CD Automation
- Cloud Architecture
- S3 Storage Design
- IAM & OIDC Authentication
- IRSA Implementation
- Root Cause Analysis
- Cost Optimisation
- Platform Engineering Principles

---

# Current Resume Point

Successfully delivered a complete cloud-native recording platform:

```text
Terraform
   ↓

AWS Infrastructure
   ↓

Amazon EKS
   ↓

Dockerised Python Application
   ↓

IRSA Authentication
   ↓

Amazon S3 Storage
```

Key achievements:

- Built a complete AWS platform using Terraform
- Successfully deployed workloads to Amazon EKS
- Implemented secure AWS authentication using IRSA
- Diagnosed and resolved multiple real-world Kubernetes issues
- Delivered successful end-to-end data ingestion into S3

## Next Session Objectives

1. Add Prometheus Metrics
2. Deploy Grafana
3. Implement Recording Gap Detection
4. Build Operational Dashboards
5. Define Recording Availability SLOs

The project now transitions from infrastructure delivery into observability, monitoring, and reliability engineering.