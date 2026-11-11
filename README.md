# Radio Recording Platform

A cloud-native platform prototype for generating, storing, and operating recording data on AWS. It demonstrates infrastructure as code, containerized workloads on Kubernetes, workload identity, and delivery to durable object storage.

The current application generates **synthetic recording metadata**. It does not yet capture live radio audio. The architecture and roadmap describe how the prototype can evolve toward that capability.

> **Design reference:** [Solution Architecture and Design](docs/design-documentation.md)

## Contents

- [Project status](#project-status)
- [Architecture](#architecture)
- [Current data flow](#current-data-flow)
- [Repository layout](#repository-layout)
- [Run locally](#run-locally)
- [Infrastructure workflows](#infrastructure-workflows)
- [Security and operational principles](#security-and-operational-principles)
- [Roadmap](#roadmap)
- [Technology stack](#technology-stack)

## Project status

| Area | Status |
| --- | --- |
| AWS infrastructure provisioned with Terraform | Implemented |
| Amazon EKS cluster and managed node group | Implemented |
| Containerized Python synthetic generator | Implemented |
| Kubernetes deployment and IRSA workload identity | Implemented |
| Synthetic data uploaded to Amazon S3 | Implemented |
| Terraform and Docker build validation in GitHub Actions | Implemented |
| Live audio capture and station assignment controller | Planned |
| Recording-gap detection, metrics, dashboards, and alerting | Planned |
| Production deployment automation and multi-environment support | Planned |

The prototype validates an end-to-end path from a Kubernetes workload to S3. Production readiness will require additional reliability, security, observability, and operational work; see the [design document](docs/design-documentation.md) for target requirements and component responsibilities.

## Architecture

### Implemented prototype

```text
GitHub Actions
      │
      ├── Terraform validation
      └── Docker build validation
              │
              ▼
       AWS infrastructure
       ├── Amazon VPC
       ├── Amazon EKS
       ├── Amazon ECR
       └── Amazon S3
              │
              ▼
       EKS workload
       ├── Synthetic Python generator
       └── Kubernetes service account
              │
              ▼
             IRSA
              │
              ▼
        Amazon S3 bucket
```

The application uses IAM Roles for Service Accounts (IRSA) to access S3 without embedding AWS credentials in the container.

### Target architecture

The design documentation describes an evolution from a single synthetic generator to independently managed station recordings:

```text
Radio streams
      │
      ▼
Station registry and desired-state controller
      │
      ├── Recorder worker: station A
      ├── Recorder worker: station B
      └── Recorder worker: station N
                 │
                 ▼
        Bounded recording segments
                 │
                 ▼
       Validated, retryable uploads
                 │
                 ▼
            Amazon S3
           ├── Downstream consumers
           └── Gap detection and alerting
```

This target separates station configuration, workload assignment, recording, delivery, and gap detection. It is intended to support growth in station count without changing the core storage and operations model.

## Current data flow

The synthetic generator currently creates JSON records, writes them locally, uploads them to S3, and removes the local file after delivery.

```text
Generate synthetic record
          │
          ▼
Write local JSON file
          │
          ▼
Upload to S3 using IRSA
          │
          ▼
Remove local file
          │
          ▼
Repeat
```

Example record:

```json
{
  "station_id": "station-001",
  "timestamp": "2026-11-10T13:00:00Z",
  "signal_strength": 97,
  "status": "SUCCESS"
}
```

Objects are organized by station and time to support navigation, lifecycle policies, and downstream analytics. The future audio workflow will use bounded segments and should treat a segment as delivered only after a successful upload confirmation.

## Repository layout

```text
.
├── .github/
│   └── workflows/       # Terraform and container build validation
├── app/
│   ├── generator.py     # Synthetic record generator
│   ├── requirements.txt
│   ├── Dockerfile
│   └── stations.yaml
├── docs/
│   └── design-documentation.md
├── kubernetes/          # Namespace, service account, and deployment manifests
├── terraform/           # AWS infrastructure definitions
└── README.md
```

## Run locally

### Prerequisites

- Python and pip
- Docker, if building the container
- AWS CLI and valid AWS credentials, if testing uploads to AWS
- Terraform and `kubectl` for infrastructure and cluster workflows

Install the Python dependencies:

```bash
python -m pip install -r app/requirements.txt
```

Run the generator:

```bash
python app/generator.py
```

On Windows PowerShell, the equivalent commands are:

```powershell
python -m pip install -r app\requirements.txt
python app\generator.py
```

### Build the container

Run from the repository root:

```bash
docker build -t synthetic-generator ./app
```

Pushing an image requires an authenticated AWS account and the appropriate ECR repository URI:

```bash
docker push <ecr-repository-uri>
```

## Infrastructure workflows

Run Terraform commands from the directory containing the Terraform root configuration:

```bash
cd terraform
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Review the plan before applying infrastructure changes:

```bash
terraform apply
```

To remove a development environment:

```bash
terraform destroy
```

> **Caution:** `apply` and `destroy` change real AWS resources and may incur costs or delete data. Review the Terraform plan, confirm the AWS account and region, and understand the S3 bucket’s deletion and retention settings before proceeding.

Supply environment-specific values through an appropriate local configuration or approved secret-management process. Do not commit credentials, access keys, or sensitive `terraform.tfvars` values.

## Storage

The prototype stores time-partitioned objects under station-specific prefixes, for example:

```text
station-001/2026/11/10/13/<timestamp>.json
```

The target design uses a similar station-and-time layout for bounded audio segments. Before production use, define and document:

- A stable object-key and segment-naming convention
- Retention and lifecycle policies
- Encryption and access-control requirements
- Upload retry and duplicate-handling behavior
- Recovery behavior for locally buffered segments

## Security and operational principles

The project follows these principles as it develops:

- Use IRSA and least-privilege IAM policies for workload access to AWS.
- Keep secrets out of source control, container images, and logs.
- Keep S3 public access blocked and use encryption for stored data.
- Validate infrastructure and container builds in CI.
- Use bounded recording segments and confirm delivery before removing local copies.
- Distinguish upstream stream failures from worker or infrastructure failures.
- Monitor recording coverage, upload health, resource capacity, and storage usage.
- Test recovery from pod, node, network, stream, and upload failures.

These are design goals, not a claim that every production control is already implemented. See the [design documentation](docs/design-documentation.md) for the target reliability model, monitoring signals, service-level indicators, and runbooks.

## Roadmap

1. **Improve observability:** add application metrics, dashboards, and actionable alerts.
2. **Detect gaps:** track expected recordings and report missing segments by station and time window.
3. **Introduce real recording:** replace or extend the synthetic generator with a recorder that reconnects to streams and produces bounded segments.
4. **Improve delivery resilience:** define retry, buffering, validation, and duplicate-handling behavior for segment uploads.
5. **Manage station workloads:** add a registry and controller for assignments, stalled-worker detection, and rebalancing.
6. **Harden delivery and operations:** add security scanning, deployment automation, environment separation, SLO reporting, and recovery testing.

The target is to scale with station count, make recording gaps visible, and recover automatically where practical. The system cannot guarantee uninterrupted capture during source, network, or infrastructure failures; it should instead minimize loss and make gaps observable and actionable.

## Technology stack

- **Cloud:** AWS
- **Infrastructure as code:** Terraform
- **Compute and orchestration:** Amazon EKS, Kubernetes
- **Container registry:** Amazon ECR
- **Object storage:** Amazon S3
- **Workload identity:** IAM Roles for Service Accounts (IRSA)
- **Application:** Python
- **Containerization:** Docker
- **CI:** GitHub Actions

## Design documentation

For the detailed requirements, AWS architecture, component responsibilities, recording workflow, reliability strategy, observability signals, and production-readiness criteria, see:

**[Solution Architecture and Design](docs/design-documentation.md)**