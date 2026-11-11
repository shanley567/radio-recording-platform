# Project Implementation Notes and Engineering History

This document complements the project README and the architecture document in `docs/design-documentation.md`. It captures the implementation details, operational lessons, and engineering progression that are useful to preserve as part of the project record, even though they are not the primary summary for a high-level landing page.

## 1. Project purpose and scope

The original use case for the platform is a cloud-native system capable of:

- continuously recording radio streams,
- persisting recordings to durable object storage,
- scaling as stream count grows,
- detecting recording gaps,
- providing operational visibility,
- operating with minimal manual intervention.

To simplify development and validation, the current implementation uses synthetic recording data instead of live audio capture. This allows the architecture, automation, identity, storage, and Kubernetes deployment patterns to be validated before real-radio recording logic is introduced.

The project therefore exists at two layers:

1. A current prototype that proves the platform patterns work end-to-end.
2. A target production architecture described in the design documentation that extends the prototype to real radio recordings, assignment-based workload orchestration, and observability-driven operations.

## 2. Current implementation status

### Infrastructure

Implemented:

- Terraform repository structure
- AWS provider configuration
- variable-driven Terraform deployment
- Amazon S3 recording bucket
- S3 versioning
- S3 encryption
- public access blocking
- Amazon ECR repository
- Amazon VPC
- public and private subnets
- internet gateway
- NAT gateway
- route tables
- security groups
- Amazon EKS cluster
- managed node group
- EKS add-ons:
  - VPC CNI
  - CoreDNS
  - kube-proxy
- OIDC provider
- IAM Roles for Service Accounts (IRSA)
- Kubernetes namespace
- Kubernetes service account
- EKS-to-S3 authentication

In progress:

- platform observability
- Prometheus metrics
- Grafana dashboards

Planned:

- recording gap detection
- alerting
- horizontal pod autoscaling
- multi-environment deployment
- production CI/CD

### Application

Implemented:

- Python synthetic generator
- Docker containerisation
- structured application logging
- synthetic recording generation
- Kubernetes deployment
- IAM-authenticated S3 uploads through IRSA
- structured S3 object storage
- automatic local file cleanup

The generator produces synthetic recordings resembling:

```json
{
  "station_id": "station-001",
  "timestamp": "2026-11-10T13:00:00Z",
  "signal_strength": 97,
  "status": "SUCCESS"
}
```

### CI/CD

Implemented GitHub Actions workflows:

#### Terraform validation

Validates:

- `terraform fmt`
- `terraform init`
- `terraform validate`

#### Docker build validation

Validates:

- successful container image build

Planned:

- TFLint
- Checkov
- Trivy
- automated container publishing
- Kubernetes deployment workflow
- smoke tests

## 3. Current project architecture

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

This reflects the current validated prototype rather than the eventual production architecture. The design documentation expands this into a more complete recording platform that includes station registry, assignment controller, recorder workers, upload validation, storage partitioning, monitoring, and operational recovery.

## 4. Operational workflow

The currently validated application flow is:

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
Repeat Every 10 Seconds
```

The generated records are stored in a partitioned S3 layout by station and time, for example:

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

Benefits of this pattern include:

- easier retention management,
- faster navigation,
- time-based partitioning,
- data lake style organization,
- future analytics compatibility.

## 5. ECR and delivery workflow

The implemented container build and deployment pattern is:

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

The repository stores the container image under a repository named:

```text
synthetic-generator
```

This pattern has been successfully validated in AWS ECR and Amazon EKS.

## 6. Kubernetes and environment validation

The project has been validated in practice with the following operational outcomes:

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

Deployment components:

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

Successful end-to-end workflow:

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

Example successful S3 object outputs:

```text
station-001/2026/11/10/13/1794317730.json
station-002/2026/11/10/13/1794317828.json
station-003/2026/11/10/13/1794317869.json
```

## 7. Lessons learned and engineering issues resolved

### 7.1 Terraform state drift

A common issue encountered during the AWS infrastructure work was:

```text
Resource exists in AWS
Terraform state unaware
```

This was resolved using Terraform import where appropriate.

The lesson learned is that cloud resources that were created manually, or by an earlier iteration of infrastructure, cannot always be safely re-created without reconciling state. Maintaining disciplined state management and importing existing resources reduces drift and avoids surprising data loss or duplicate infrastructure.

### 7.2 S3 bucket deletion behavior

Version-enabled S3 buckets cannot be deleted while object versions remain present. The project resolved this by enabling:

```terraform
force_destroy = true
```

This is particularly useful for development environments where repeatable teardown and rebuild are required.

### 7.3 Region consistency

The project standardized deployment to a single AWS region:

```text
eu-west-2
```

This eliminated regional mismatches across:

- AWS CLI
- Terraform
- ECR
- EKS

This lesson is especially important for multistage deployment work, because inconsistent region configuration leads to confusing authentication and deployment failures that are often mistaken for deeper infrastructure issues.

### 7.4 EKS troubleshooting

The project successfully diagnosed and resolved multiple AWS and Kubernetes issues. One key example used:

```bash
aws eks describe-nodegroup
aws autoscaling describe-auto-scaling-groups
aws autoscaling describe-scaling-activities
```

This highlighted the value of using cloud-native diagnostics rather than relying only on Terraform outputs or partial cluster status.

### 7.5 Kubernetes node provisioning failure

Symptoms:

```text
Node group stuck in CREATING
```

Root cause:

```text
Unsupported instance type
```

Resolution:

```terraform
instance_types = ["t3.micro"]
```

This demonstrates the practical importance of matching capacity, instance type support, and workload sizing with the actual requirements of the EKS cluster and node group.

### 7.6 Node registration failure

Symptoms:

```text
NodeCreationFailure
```

Root cause:

```text
Missing EKS add-ons
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

### 7.7 Pod scheduling failure

Symptoms:

```text
Pending
```

Error:

```text
Too many pods
```

Root cause:

```text
t3.micro capacity limitation
```

Resolution:

```text
Increase worker node size
Reduce CoreDNS replicas
```

This is a useful reminder that the correct fix is not always to simply add more workloads. Capacity planning and cluster sizing must reflect expected pod density and the operational overhead of essential control-plane components.

### 7.8 ECR deployment failure

Symptoms:

```text
ImagePullBackOff
```

Root cause:

```text
Empty ECR repository
```

Resolution:

```bash
docker build
docker push
```

This is a very common issue in container-first projects and highlights the need for pipeline validation and deployment smoke tests.

### 7.9 Application startup failure

Symptoms:

```text
CrashLoopBackOff
```

Root cause:

```text
Missing boto3 dependency
```

Resolution:

```text
Install Python dependencies during Docker image build
```

This reinforces the importance of validating the application container in the same way a production service would be validated, not just from a local workstation environment.

### 7.10 AWS authentication failure

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

Root cause:

```text
Kubernetes workload lacked AWS credentials
```

Resolution:

```text
Implemented IRSA
IAM Role
OIDC trust
Service account annotation
```

This was one of the most important platform milestones because it proved the workload could authenticate securely without explicit AWS credentials in the pod or image.

## 8. Local development workflow

### Install dependencies

```powershell
python -m pip install -r app\requirements.txt
```

### Run the generator

```powershell
cd app
python generator.py
```

### Build the container

```powershell
docker build -t synthetic-generator ./app
```

### Push the image

```powershell
docker push <ecr-repository-uri>
```

## 9. Infrastructure management workflow

### Initialise Terraform

```powershell
terraform init
```

### Review changes

```powershell
terraform plan
```

### Deploy

```powershell
terraform apply
```

### Destroy

```powershell
terraform destroy
```

## 10. Project roadmap and progression

### Phase 1 ✅

- Repository setup
- GitHub workflows
- Terraform foundation
- S3 storage
- synthetic generator
- Docker build
- ECR repository
- ECR push

### Phase 2 ✅

- VPC
- private networking
- internet gateway
- NAT gateway

### Phase 3 ✅

- EKS cluster
- managed node group
- Kubernetes networking
- kubectl connectivity
- generator deployment
- EKS add-ons

### Phase 4 ✅

- OIDC provider
- IAM Roles for Service Accounts (IRSA)
- secure Kubernetes authentication
- end-to-end recording pipeline

### Phase 5 🚧

- Prometheus
- Grafana
- CloudWatch integration

### Phase 6

- recording gap detection
- business metrics
- SLOs
- error budgets
- runbooks

### Phase 7

- multi-environment Terraform
- horizontal pod autoscaling
- production CI/CD
- security hardening

## 11. Key DevOps and SRE skills demonstrated

- Infrastructure as Code
- Terraform state management
- AWS networking
- EKS operations
- Kubernetes troubleshooting
- containerisation
- CI/CD automation
- cloud architecture
- S3 storage design
- IAM and OIDC authentication
- IRSA implementation
- root cause analysis
- cost optimisation
- platform engineering principles

## 12. Resume-level project summary

The project now represents a fully working AWS-native platform prototype:

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

- Built a complete AWS platform using Terraform.
- Successfully deployed workloads to Amazon EKS.
- Implemented secure AWS authentication using IRSA.
- Diagnosed and resolved multiple real-world Kubernetes issues.
- Delivered successful end-to-end data ingestion into S3.

## 13. Next planned objectives

1. Add Prometheus metrics.
2. Deploy Grafana.
3. Implement recording gap detection.
4. Build operational dashboards.
5. Define recording availability SLOs.

At this point the project moves from infrastructure delivery into observability, monitoring, and reliability engineering.

## 14. Operational readiness and design context

The current implementation is valuable as a proving ground. It demonstrates that a cloud-native platform can be provisioned, containerised, deployed, and connected securely to object storage. However, production-grade recording needs more than successful upload of synthetic JSON.

The design documentation sets the required direction:

- station-level operational ownership,
- recording worker health model,
- assignment and desired-state controller,
- segment delivery semantics,
- S3 lifecycle and retention rules,
- monitoring and alerting that distinguishes service degradation from temporary network anomalies,
- operational runbooks and SLOs.

This engineering history is therefore the bridge between a working prototype and the target architecture described elsewhere in the repository.

## 15. Related documents

- [README.md](../README.md)
- [docs/design-documentation.md](design-documentation.md)

## 16. Conclusion

The project has already proven the foundation: cloud infrastructure, platform automation, secure identity, Kubernetes orchestration, and end-to-end data delivery. The next design step is not to rebuild the platform from scratch, but to evolve the current pattern into a more complete, resilient, auditable radio recording system aligned to the design document.
