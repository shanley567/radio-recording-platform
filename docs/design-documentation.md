# Radio Recording Platform

## Executive Summary

The Radio Recording Platform is a cloud-native system designed to continuously capture audio streams from a configurable set of radio station URLs and make those recordings available to downstream consumers.

The platform is designed to operate continuously, automatically recover from failures, scale as station counts change, and provide comprehensive operational visibility.

It has been built using AWS, Terraform, Kubernetes, and modern Site Reliability Engineering (SRE) practices.

The primary objective of the platform is to ensure that as much audio as possible is successfully recorded and made available for downstream processing while minimising manual operational effort.

---

# Non-Technical Overview

Imagine a business that needs to continuously record dozens of radio stations every hour of every day.

The platform must:

- Record audio continuously.
- Detect when recordings stop unexpectedly.
- Store recordings safely and durably.
- Scale as new stations are added.
- Recover automatically when failures occur.
- Provide visibility into platform health.

As the number of stations grows from 20 to 100 or more, the platform should require little to no manual intervention.

The solution uses cloud-native technologies to automate recording, storage, monitoring, recovery, and scaling.

---

# Business Problem

Radio stations provide continuous live-streamed audio.

The business requires:

- Continuous ingestion of audio streams
- Minimal recording gaps
- Long-term durable storage
- Rapid scalability
- Operational monitoring
- Automated recovery
- Cost-effective operation

Expected growth:

```text
20 Stations
    ↓
50 Stations
    ↓
100+ Stations
```

The architecture must support growth without requiring redesign.

---

# Technical Overview

The platform is built as a collection of independent cloud-native services.

Recorder workloads run inside Kubernetes and continuously record audio from configured URLs.

Completed recording segments are uploaded to Amazon S3 where they become available to downstream consumers.

Infrastructure is managed through Terraform and workloads authenticate using IAM Roles for Service Accounts (IRSA).

---

# Solution Architecture

```text
                 External Radio Streams

                           │

                           ▼

                  Amazon EKS Cluster

       ┌───────────────────────────────────────┐

       │             Recorder Pods            │

       │                                       │

       │  Stream Capture                       │

       │  Segment Creation                     │

       │  Upload To Storage                    │

       └───────────────────────────────────────┘

                           │

                           ▼

                  IAM Role (IRSA)

                           │

                           ▼

                     Amazon S3

                           │

                           ▼

                 Downstream Consumers

                           │

                           ▼

            Analytics / Gap Detection / ML
```

---

# AWS Infrastructure Architecture

```text
                             AWS Account

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                          VPC                                │
│                                                             │
│   ┌──────────────┐          ┌────────────────────────┐      │
│   │ Public       │          │ Private Subnets        │      │
│   │ Subnets      │          │                        │      │
│   │              │          │ Amazon EKS            │      │
│   │ NAT Gateway  │─────────▶│ Managed Node Group    │      │
│   └──────────────┘          │                        │      │
│                             └──────────┬─────────────┘      │
│                                        │                    │
└────────────────────────────────────────┼────────────────────┘
                                         │
                                         ▼

                             Service Account

                                         │

                                         ▼

                                 IAM Role (IRSA)

                                         │

                                         ▼

                                    Amazon S3
```

---

# Recording Workflow

Each recorder follows the same lifecycle:

```text
Connect To Stream

        │

        ▼

Capture Audio

        │

        ▼

Create Recording Segment

        │

        ▼

Store Locally

        │

        ▼

Upload To S3

        │

        ▼

Verify Upload

        │

        ▼

Delete Local Copy

        │

        ▼

Continue Recording
```

---

# Storage Design

Recordings are partitioned by station and time.

Example:

```text
station-001/

└── 2026/
    └── 11/
        └── 10/
            └── 14/
                ├── recording-0001.wav
                ├── recording-0002.wav
                └── recording-0003.wav
```

Benefits:

- Faster navigation
- Time-based retrieval
- Lifecycle policy support
- Improved analytics performance
- Data lake compatibility

---

# Scalability Strategy

## Current Model

```text
EKS Cluster

    │

    ▼

Recorder Pods
```

Each recorder can operate independently.

---

## Future Scaling Model

```text
20 Stations

↓

20 Recorder Pods
```

```text
100 Stations

↓

100 Recorder Pods
```

Benefits:

- Horizontal scalability
- Fault isolation
- Predictable resource consumption
- Easier operational management

---

## Scaling Mechanisms

Horizontal scaling will be driven by:

- Number of active stations
- CPU utilisation
- Memory utilisation
- Queue depth
- Recording workload demand

Platform scaling components:

```text
Horizontal Pod Autoscaler

+

Cluster Autoscaler
```

---

# Reliability Design

## Primary Objective

Maximise successful audio capture.

Example target:

```text
Recording Availability

99.5%+
```

---

## Reliability Controls

Current and planned controls:

- Kubernetes self-healing
- Health probes
- Managed node groups
- Rolling deployments
- Durable object storage
- Alerting
- Capacity planning
- Disaster recovery testing

---

## Failure Domains

Designed failure isolation:

```text
Single Stream Failure
        │
        ▼
Single Pod Failure
        │
        ▼
Restart Recorder
```

Rather than:

```text
Single Stream Failure
        │
        ▼
Entire Platform Failure
```

---

# Recording Gap Detection

The most important business failure is missing audio.

Future gap detection services will monitor expected recording frequency.

Example:

```text
Expected

station-001

Recording Every Minute


Observed

No Recording For 10 Minutes


Result

Generate Alert
```

Potential causes:

- Stream unavailable
- Recorder failed
- Upload failure
- Platform outage

---

# Monitoring Strategy

## Recorder Workloads

| Area | Signals to Monitor |
|--------|--------|
| Pod Health | Readiness failures |
| Stability | Pod restarts |
| Resources | CPU usage |
| Resources | Memory usage |
| Recording | Recorder process health |
| Recording | Failed recording attempts |

Example Alerts:

```text
Recorder Pod Not Ready

High Restart Rate

Recorder Process Failure
```

---

## Kubernetes Capacity

| Area | Signals to Monitor |
|--------|--------|
| Cluster Health | Node readiness |
| Compute | Available CPU |
| Compute | Available memory |
| Scheduling | Pending pods |
| Scheduling | Failed scheduling events |
| Capacity | Pod availability |
| Scaling | Autoscaler activity |

Example Alerts:

```text
Node Not Ready

Pods Pending > 5 Minutes

Cluster Capacity Exhausted
```

---

## Application Delivery

| Area | Signals to Monitor |
|--------|--------|
| Uploads | Upload success rate |
| Uploads | Upload failure rate |
| Performance | Upload latency |
| Reliability | Retry count |
| Throughput | Segments processed |
| Delivery | Upload backlog |

Example Alerts:

```text
Upload Failure Rate Above Threshold

Upload Latency Exceeds SLO
```

---

## Network and Dependencies

| Area | Signals to Monitor |
|--------|--------|
| DNS | Resolution failures |
| Streams | Connection failures |
| Streams | Timeout rates |
| AWS | S3 connectivity |
| AWS | STS authentication failures |

Example Alerts:

```text
Station Stream Unreachable

DNS Failure Rate High

AWS Credential Failure
```

---

## Storage

| Area | Signals to Monitor |
|--------|--------|
| S3 | Upload failures |
| S3 | Bucket growth |
| S3 | Object growth |
| Nodes | Local disk utilisation |
| Nodes | Temporary storage utilisation |

Example Alerts:

```text
Disk Usage Above 80%

Upload Failures Detected
```

---

## Observability Pipeline

| Area | Signals to Monitor |
|--------|--------|
| Prometheus | Scrape health |
| Grafana | Dashboard availability |
| AlertManager | Alert delivery |
| Logging | Log ingestion health |
| Monitoring | Missing metrics |

Example Alerts:

```text
Metrics Missing

Alert Delivery Failure
```

---

# SRE Operating Model

The platform measures success using business outcomes rather than infrastructure metrics alone.

Infrastructure metrics answer:

```text
Is the platform healthy?
```

Business metrics answer:

```text
Are recordings actually being captured?
```

The most important KPI is:

```text
Expected Recordings

vs

Missing Recordings
```

---

# Security Architecture

Security controls include:

- IAM Roles for Service Accounts (IRSA)
- Least privilege IAM policies
- Encryption at rest
- Encryption in transit
- Centralised secret management
- Access logging
- Dependency patching
- Security scanning

No long-lived AWS credentials are stored inside containers.

---

# AWS Well-Architected Alignment

## Operational Excellence

The platform uses:

- Infrastructure as Code
- Git workflows
- Automated validation
- CI/CD pipelines
- Runbooks
- Post-incident reviews

---

## Security

The platform provides:

- Least privilege access
- IRSA authentication
- Encryption
- Auditability
- Secret management

---

## Reliability

The platform implements:

- Kubernetes self-healing
- Health checks
- Managed infrastructure
- Capacity planning
- Recovery testing

---

## Performance Efficiency

The platform supports:

- Horizontal scaling
- Workload isolation
- Performance monitoring
- Capacity forecasting

---

## Cost Optimisation

The platform encourages:

- Rightsized infrastructure
- Autoscaling
- Cost ownership
- Resource lifecycle management
- Visibility into operational spend

---

## Sustainability

The platform supports:

- Elastic workload scaling
- Reduced idle capacity
- Efficient resource utilisation
- Storage lifecycle optimisation

---

# Operational Runbooks

Key runbooks should include:

- Recorder Pod Failure
- Station Stream Failure
- S3 Upload Failure
- EKS Node Failure
- High Restart Rate
- Missing Recording Investigation
- Disaster Recovery Testing

---

# Current Project Status

## Completed

✅ Terraform Infrastructure

✅ Amazon VPC

✅ Amazon S3

✅ Amazon ECR

✅ Amazon EKS

✅ Managed Node Groups

✅ EKS Add-ons

✅ OIDC Provider

✅ IRSA

✅ Kubernetes Deployments

✅ Continuous Recording Generation

✅ End-to-End Upload Pipeline

✅ S3 Storage Validation

✅ Production-style Logging

---

## Next Deliverables

- Prometheus
- Grafana
- AlertManager
- Recording Gap Detection Service
- Service Level Objectives (SLOs)
- Error Budgets
- Operational Runbooks
- Production CI/CD Pipeline
- Disaster Recovery Testing

---

# Technology Stack

- AWS
- Terraform
- Amazon EKS
- Amazon S3
- Amazon ECR
- Kubernetes
- Python
- Docker
- GitHub Actions
- IAM Roles for Service Accounts (IRSA)
- Prometheus (Planned)
- Grafana (Planned)

---

# Success Criteria

The platform will be considered production-ready when it can:

- Continuously record streams 24/7
- Automatically recover from failures
- Detect missing recordings
- Scale from 20 to 100+ stations
- Meet defined SLOs
- Provide actionable operational visibility
- Support disaster recovery procedures
- Operate with minimal manual intervention