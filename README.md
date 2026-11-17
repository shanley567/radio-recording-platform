# Radio Recording Platform

A cloud-native AWS project for exploring the infrastructure and operational patterns behind a radio recording platform. It combines Terraform-managed AWS resources, a Python workload running on Kubernetes, S3 storage, workload identity, Prometheus metrics, and a Grafana dashboard.

**The current application generates synthetic JSON recording metadata; it does not capture or store live radio audio.** The infrastructure and observability components provide a foundation for developing a real recorder, but the project is not production-ready. See [Project status](#project-status) and the [design documentation](docs/design-documentation.md) for implemented capabilities, limitations, and future work.

> **Design reference:** [Solution Architecture and Design](docs/design-documentation.md)

## Contents

- [Project status](#project-status)
- [Architecture](#architecture)
- [Current data flow](#current-data-flow)
- [Observability](#observability)
- [Repository layout](#repository-layout)
- [Run locally](#run-locally)
- [Infrastructure workflows](#infrastructure-workflows)
- [Deploy to Kubernetes](#deploy-to-kubernetes)
- [Security and operational considerations](#security-and-operational-considerations)
- [Roadmap](#roadmap)
- [Technology stack](#technology-stack)

## Project status

| Area | Status |
| --- | --- |
| AWS infrastructure defined with Terraform | Implemented |
| Amazon EKS cluster and managed node group | Defined in Terraform |
| Amazon ECR repository | Defined in Terraform |
| Amazon S3 bucket with versioning, server-side encryption, and public-access blocking | Defined in Terraform |
| Python synthetic metadata generator | Implemented |
| Kubernetes deployment, service, and service account | Manifests present |
| IRSA role for S3 object uploads | Defined in Terraform |
| Prometheus metrics endpoint and ServiceMonitor manifest | Implemented / configured |
| Grafana dashboard definition | Checked in at `observability/dashboards/` |
| Terraform validation in GitHub Actions | Implemented |
| Container build in GitHub Actions | Implemented; does not publish or deploy the image |
| Live audio capture and station URL management | Planned |
| Recording-gap detection and alerting | Planned |
| Automated application deployment and multi-environment support | Planned |

“Defined” or “configured” does not necessarily mean a resource has been deployed or verified in a particular AWS account or cluster. The repository does not currently provide a complete install-and-deploy workflow for the monitoring stack or application.

Before production use, the project needs additional work in application reliability, configuration management, access control, monitoring and alerting, deployment automation, recovery testing, and cost and data-retention controls.

## Architecture

### Implemented prototype

```text
GitHub Actions
   ├── Terraform formatting and validation
   └── Container image build
             │
             ▼
      AWS resources (Terraform)
      ├── VPC
      ├── Amazon EKS
      ├── Amazon ECR
      └── Amazon S3
             │
             ▼
      Kubernetes workload
      ├── Python synthetic generator
      ├── Kubernetes Service
      └── ServiceAccount
             │
             ├── Prometheus metrics endpoint
             └── IRSA workload identity
                       │
                       ▼
                 Amazon S3
```

The application uses IAM Roles for Service Accounts (IRSA) to obtain AWS permissions through its Kubernetes service account rather than requiring AWS access keys in the container. The configured IAM policy grants object-upload permissions to the recording bucket.

The repository also includes a Prometheus Operator `ServiceMonitor` and a Grafana dashboard definition. A compatible monitoring stack, Prometheus data source, and cluster configuration are still required for those assets to work.

### Target architecture

The design documentation describes a future system that records real radio streams:

```text
Radio stream URLs
        │
        ▼
Station registry and workload assignment
        │
        ├── Recorder worker: station A
        ├── Recorder worker: station B
        └── Recorder worker: station N
                    │
                    ▼
          Bounded audio segments
                    │
                    ▼
       Validated, retryable uploads
                    │
                    ▼
                 Amazon S3
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
 Downstream consumers    Gap detection
                         and alerting
```

The target separates station configuration, recording, upload, storage, and gap detection. These are design goals, not capabilities of the current synthetic generator.

## Current data flow

The application generates a small JSON record for each of three hard-coded station IDs, writes the file under a local `output/` directory, and attempts to upload it to S3. After a successful upload, it deletes the local file. If an upload fails, the file is retained in the container’s writable filesystem, but durable buffering and retry management are not implemented.

```text
Generate synthetic JSON metadata
              │
              ▼
      Write local JSON file
              │
              ▼
         Upload to S3
              │
        ┌─────┴──────┐
        ▼            ▼
   Success         Failure
        │            │
 Delete local   Retain file in
     file       container storage
```

Example record:

```json
{
  "station_id": "station-001",
  "timestamp": "2026-11-10T13:00:00+00:00",
  "signal_strength": 97,
  "status": "SUCCESS"
}
```

The current S3 object key uses a station and UTC hour prefix, followed by the generated filename. For example:

```text
station-001/2026/11/10/13/1794315600.json
```

The station IDs and bucket name are currently hard-coded in `app/generator.py`. The `app/stations.yaml` file is present in the repository but is not currently read by the generator. Update the application configuration before using it with a different bucket or station list.

This workflow is a synthetic metadata demonstration—not audio capture, a recording-segment pipeline, or a guarantee of durable local buffering.

## Observability

The application exposes HTTP endpoints on port `8000`:

| Endpoint | Purpose |
| --- | --- |
| `/metrics` | Prometheus metrics |
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness probe |

The application exports metrics for generated records, successful and failed S3 uploads, upload duration, and generation-cycle duration. The Kubernetes deployment defines startup, liveness, and readiness probes. The current readiness endpoint returns success without checking S3 connectivity or other dependencies.

The repository includes:

- `observability/servicemonitor.yaml` — a Prometheus Operator `ServiceMonitor` that targets the application’s `/metrics` endpoint.
- `observability/dashboards/radio-recording.platform.json` — a Grafana dashboard definition with panels for generated recordings, upload successes and failures, upload duration, recording rate by station, pod restarts, and container CPU and memory.

The `ServiceMonitor` requires the Prometheus Operator CRDs and a Prometheus instance configured to select it. Its labels and namespace should be checked against the monitoring installation in your cluster. The dashboard requires a Prometheus data source named `prometheus` or an update to its data source configuration. These files do not install or configure Prometheus, Grafana, or an alert-delivery system.

### Grafana dashboard screenshots

Screenshots are optional. If you want to include them, save images in the repository (for example, under `docs/images/`) and insert Markdown image links here. Suggested views include an overview of recording and upload metrics, and a close-up of resource or upload-failure panels.

For example, after adding the image file:

```markdown
![Radio Recording Platform Grafana overview](docs/images/grafana-overview.png)
```

Avoid including screenshots that expose credentials, account identifiers, private URLs, or other sensitive operational data.

## Repository layout

```text
.
├── .github/
│   └── workflows/                  # Terraform validation and image build workflows
├── IAM/                            # IAM-related project files
├── app/
│   ├── generator.py                # Synthetic metadata generator and metrics endpoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── stations.yaml               # Present, but not currently loaded by the generator
├── docs/
│   └── design-documentation.md     # Architecture and target design
├── kubernetes/
│   ├── deployment.yaml
│   ├── namespace.yaml
│   ├── service.yaml
│   └── serviceaccount.yaml
├── observability/
│   ├── dashboards/
│   │   └── radio-recording.platform.json
│   └── servicemonitor.yaml
├── terraform/                      # AWS infrastructure definitions
└── README.md
```

## Run locally

### Prerequisites

- Python compatible with the application image (Python 3.13)
- AWS CLI and credentials with permission to upload objects to the configured S3 bucket
- Docker, if building the container
- Terraform and `kubectl` for infrastructure and cluster workflows

Install the application dependencies:

```bash
python -m pip install -r app/requirements.txt
```

Before running the generator, review and update the bucket name and station configuration in `app/generator.py`. The application uses the AWS SDK credential chain, so configure AWS credentials using an approved local method. Do not put access keys in source code or commit them to the repository.

Run the generator:

```bash
python app/generator.py
```

The process continuously generates records and attempts S3 uploads. Stop it with `Ctrl+C`.

On Windows PowerShell:

```powershell
python -m pip install -r app\requirements.txt
python app\generator.py
```

### Build the container

Run from the repository root:

```bash
docker build -t synthetic-generator:local ./app
```

The image runs as a non-root user and exposes port `8000`. To push an image, authenticate to the appropriate registry and use that registry’s full image URI and an explicit version tag. The GitHub Actions build workflow currently builds the image for validation; it does not log in to ECR, push an image, or deploy it.

## Infrastructure workflows

Run Terraform commands from the Terraform root directory:

```bash
cd terraform
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Review the plan, confirm the AWS account and region, and verify the effects on existing resources before applying:

```bash
terraform apply
```

To remove a development environment:

```bash
terraform destroy
```

> **Destructive-operation warning:** Terraform can create billable AWS resources and change or delete existing infrastructure. The S3 bucket configuration currently sets `force_destroy = true`, which can allow Terraform to delete a non-empty bucket. Confirm the plan, bucket contents, AWS account, and region before applying or destroying resources. Do not use this configuration for valuable data without first changing and reviewing its deletion safeguards.

The checked-in `terraform/terraform.tfvars` contains project-specific values. Review the bucket name and region before use. Supply environment-specific settings through a suitable local configuration or approved secret-management process; do not commit credentials or sensitive variable values.

The Terraform GitHub Actions workflow runs formatting and validation checks. It does not apply Terraform changes.

## Deploy to Kubernetes

The Kubernetes manifests are a starting point for deploying the workload to an existing cluster; the repository does not currently automate the full deployment process.

Before applying them:

1. Build and publish an image to a registry accessible by the cluster.
2. Update the image reference in `kubernetes/deployment.yaml` to the intended registry, repository, and immutable version tag.
3. Confirm that the Terraform-created cluster, IAM role, and IRSA trust relationship match the Kubernetes service account and namespace.
4. Review the namespace, permissions, resource requests and limits, probes, and monitoring configuration for your environment.
5. Apply the manifests only after confirming the current `kubectl` context and target cluster.

For example, after setting the correct image and confirming the target cluster:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/serviceaccount.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

The exact order and required configuration depend on the cluster and monitoring installation. The deployment manifest references a specific ECR image; verify that it exists and is the intended version before deploying. The manifests do not install the cluster, publish the image, or configure a complete Prometheus/Grafana stack.

## Security and operational considerations

The project uses or demonstrates the following controls:

- IRSA for workload access to AWS, avoiding long-lived AWS credentials in the container.
- A narrowly scoped S3 upload policy for the application role.
- S3 public-access blocking, server-side encryption, and versioning in Terraform.
- A non-root container user and Kubernetes resource requests and limits.
- Kubernetes startup, liveness, and readiness probes.
- Terraform and container build validation in GitHub Actions.

These controls do not by themselves establish production readiness. In particular:

- The application’s bucket and station list are hard-coded; introduce validated, environment-specific configuration before operating across environments.
- The readiness endpoint does not currently test downstream dependencies.
- Failed uploads are not retried through a durable queue or persistent buffer. Files retained after failure are on container-local storage and may be lost when a pod is replaced.
- There is no live stream recorder, recording-gap detector, alerting policy, or documented SLO implementation.
- The CI workflows do not publish or deploy images, run application tests, or provide a complete security-scanning pipeline.
- The S3 bucket’s `force_destroy` setting requires careful review and should not be used for production data without appropriate safeguards.
- Define retention, recovery, access logging, encryption, backup, and incident-response requirements before storing valuable recordings.

Keep credentials out of source control, container images, and logs. Review IAM policies and Terraform plans before use, and restrict access to state files and deployment credentials.

## Roadmap

1. **Configuration:** make bucket, station, and runtime settings explicit and validate them at startup.
2. **Observability:** verify Prometheus scraping and dashboard behavior in a documented monitoring setup; add actionable alerts and runbooks.
3. **Real recording:** implement stream capture, reconnect behavior, bounded segments, and validation.
4. **Resilient delivery:** add durable buffering, bounded retries, duplicate handling, and safe cleanup after confirmed delivery.
5. **Gap detection:** compare expected recording intervals with delivered segments and report missing data by station.
6. **Deployment and operations:** add tested deployment automation, environment separation, security scanning, recovery exercises, and defined SLOs.

The long-term goal is to make missing recordings visible and improve recovery as the number of stations grows. The system cannot guarantee uninterrupted capture during source, network, or infrastructure failures; production requirements and acceptable loss windows must be explicitly defined and tested.

## Technology stack

- **Cloud:** AWS
- **Infrastructure as code:** Terraform
- **Compute and orchestration:** Amazon EKS, Kubernetes
- **Container registry:** Amazon ECR
- **Object storage:** Amazon S3
- **Workload identity:** IAM Roles for Service Accounts (IRSA)
- **Application:** Python, Flask, Boto3
- **Metrics:** Prometheus client library
- **Dashboards:** Grafana
- **Containerization:** Docker
- **CI:** GitHub Actions

## Design documentation

For the detailed requirements, AWS architecture, component responsibilities, target recording workflow, reliability strategy, observability signals, and production-readiness criteria, see:

**[Solution Architecture and Design](docs/design-documentation.md)**