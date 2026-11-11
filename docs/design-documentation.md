# Radio Recording Platform

# Solution Architecture and Design

---

# 1. Executive Summary

The Radio Recording Platform is a cloud-native recording system designed to continuously capture audio streams from a dynamic set of radio station URLs and make completed recordings available to downstream consumers.

The platform is designed around DevOps, Platform Engineering, Kubernetes, AWS, and Site Reliability Engineering (SRE) principles.

Key goals:

- Minimise recording gaps
- Recover automatically from failures
- Provide strong operational visibility
- Scale recording capacity as station count changes
- Store recordings durably and reliably
- Minimise manual intervention

The target design can support growth from approximately:

```text
20 Stations

to

100+ Stations
```

without significant architectural changes.

---

# 2. Non-Technical Overview

A business requires continuous recording of radio streams from multiple stations.

These recordings must remain available for analysis, processing, compliance, or archival purposes.

The system should:

- Record continuously
- Store recordings reliably
- Recover from failures automatically
- Scale as additional stations are onboarded
- Alert operators when recordings are missing

The solution uses cloud-native infrastructure to automate recording, storage, monitoring, scaling, and recovery.

---

# 3. Technical Overview

The platform consists of four primary domains:

```text
Recording

↓

Storage

↓

Observability

↓

Operations
```

Recorder workloads execute within Amazon EKS and continuously ingest audio streams.

Completed segments are uploaded to Amazon S3 where they become available to downstream systems.

All infrastructure is managed through Terraform and workloads access AWS services using IAM Roles for Service Accounts (IRSA).

---

# 4. Requirements

The platform must:

1. Record continuously, aiming to minimise lost audio.
2. Write recordings to durable object storage.
3. Make recordings available to downstream systems.
4. Scale with station count.
5. Detect recording gaps.
6. Provide operational monitoring and alerting.
7. Recover automatically where practical.
8. Operate with minimal manual intervention.

---

# 5. Scope and Assumptions

## Current Prototype

The portfolio project currently validates:

- Terraform infrastructure
- Amazon EKS
- Amazon S3
- Amazon ECR
- IRSA authentication
- Kubernetes deployment
- End-to-end object delivery

The current implementation generates synthetic JSON records.

It does not yet record real audio streams.

---

## Assumptions

- A recording binary exists or can be containerised.
- Stations have unique identifiers and URLs.
- Recordings are created as bounded segments.
- Temporary local storage is available.
- AWS is the primary deployment target.
- Automatic recovery is preferred over manual intervention.

The design reduces audio loss but cannot guarantee perfectly lossless recording during every upstream or infrastructure failure.

---

# 6. High-Level Architecture

```text
                 External Radio Streams

                           │

                           ▼

            Station Configuration / Registry

                           │

                           ▼

          Assignment And Desired-State Controller

                           │

      ┌────────────┬────────────┬────────────┐

      ▼            ▼            ▼

 Recorder-1   Recorder-2   Recorder-N

      │            │            │

      └────────────┴────────────┘

                           │

                           ▼

                 Segment Generation

                           │

                           ▼

                     Upload Service

                           │

                           ▼

                       Amazon S3

                   ┌──────────────┐
                   │              │
                   ▼              ▼

         Gap Detection      Consumers

                             Analytics
                             Processing
```

---

# 7. AWS Architecture

```text
                             AWS Account

┌────────────────────────────────────────────────────────────┐
│                                                            │
│                            VPC                             │
│                                                            │
│  ┌─────────────┐        ┌─────────────────────────────┐    │
│  │ Public      │        │ Private Subnets            │    │
│  │ Subnets     │        │                            │    │
│  │             │        │ Amazon EKS Cluster        │    │
│  │ NAT Gateway │───────▶│ Managed Node Groups       │    │
│  └─────────────┘        │                            │    │
│                         └────────────┬───────────────┘    │
│                                      │                    │
└──────────────────────────────────────┼────────────────────┘
                                       │
                                       ▼

                              Service Account

                                       │

                                       ▼

                                 IAM Role

                                       │

                                       ▼

                                  Amazon S3
```

---

# 8. Component Responsibilities

## Station Registry

Stores:

- Station ID
- Stream URL
- Recording configuration
- Enabled state

Sensitive values should be stored using an approved secret management solution.

---

## Assignment Controller

Responsible for:

- Determining required recorder count
- Creating assignments
- Detecting stalled recorders
- Rebalancing workloads
- Maintaining desired state

Future enhancement.

---

## Recorder Worker

Responsible for:

- Connecting to stream
- Reconnecting after interruptions
- Recording audio
- Creating bounded segments
- Uploading completed files
- Reporting health signals

---

## Object Storage

Amazon S3 acts as the system of record.

Responsibilities:

- Durable storage
- Retention
- Lifecycle management
- Consumer access

---

## Gap Detection Service

Responsible for:

- Tracking expected recordings
- Detecting missing segments
- Measuring recording coverage
- Generating alerts

Future enhancement.

---

# 9. Recording Workflow

For each assigned station:

```text
Receive Assignment

        │

        ▼

Connect To Stream

        │

        ▼

Record Audio

        │

        ▼

Create Segment

        │

        ▼

Validate Segment

        │

        ▼

Upload To S3

        │

        ▼

Confirm Delivery

        │

        ▼

Remove Local Copy

        │

        ▼

Record Next Segment
```

A segment is not considered delivered until upload is successfully confirmed.

---

# 10. Storage Design

Example object structure:

```text
recordings/

  station-001/

    year=2026/
      month=11/
        day=10/
          hour=13/

            2026-11-10T13-00-00Z__2026-11-10T13-05-00Z.wav

            2026-11-10T13-05-00Z__2026-11-10T13-10-00Z.wav
```

Benefits:

- Time partitioning
- Analytical compatibility
- Efficient querying
- Lifecycle support
- Retention management

---

# 11. Reliability and Recovery

## Worker Failure

Controls:

- Health probes
- Pod restart policies
- Assignment recovery
- Stuck-recorder detection

A failed recorder should affect only its assigned station.

---

## Stream Failure

Controls:

- Reconnection logic
- Exponential backoff
- Jitter
- Failure metrics
- Station-specific alerts

A broken stream should not be confused with a failed worker.

---

## Infrastructure Failure

Controls:

- Multi-AZ node placement
- Managed node groups
- Capacity buffers
- Rolling updates
- Controlled disruption

Testing should validate recovery from:

- Pod termination
- Node failure
- Stream interruption
- Upload interruption

---

# 12. Delivery Semantics

The platform aims for:

```text
Eventual Delivery
```

and

```text
Rapid Recovery
```

The design cannot guarantee 100% audio capture due to:

- Source outages
- Network failures
- Infrastructure failures
- Local storage failures

Instead, the platform makes recording gaps observable and actionable.

---

# 13. Scaling Strategy

The scaling unit is:

```text
Station Count
```

Example:

```text
20 Stations

↓

20 Recorder Assignments
```

```text
100 Stations

↓

100 Recorder Assignments
```

Capacity planning should account for:

- CPU
- Memory
- Network throughput
- Temporary disk usage
- Reconnection behaviour

---

# 14. Monitoring and Observability

## Recorder Workloads

| Area | Signals |
|--------|--------|
| Pod Health | Readiness |
| Stability | Restarts |
| Utilisation | CPU |
| Utilisation | Memory |
| Recording | Process health |
| Recording | Failed captures |

---

## Kubernetes Capacity

| Area | Signals |
|--------|--------|
| Nodes | Node readiness |
| Resources | Available CPU |
| Resources | Available memory |
| Scheduling | Pending pods |
| Scaling | Autoscaling activity |

---

## Application Delivery

| Area | Signals |
|--------|--------|
| Uploads | Success rate |
| Uploads | Failure rate |
| Uploads | Upload latency |
| Delivery | Retries |
| Delivery | Backlog size |

---

## Network and Dependencies

| Area | Signals |
|--------|--------|
| DNS | Resolution failures |
| Streams | Connection failures |
| Streams | Timeout rate |
| AWS | S3 failures |
| AWS | STS failures |

---

## Storage

| Area | Signals |
|--------|--------|
| S3 | Upload failures |
| S3 | Object growth |
| S3 | Access failures |
| Local Storage | Disk usage |

---

## Observability Platform

| Area | Signals |
|--------|--------|
| Prometheus | Scrape health |
| Grafana | Availability |
| AlertManager | Delivery success |
| Logging | Ingestion health |

---

# 15. Service Level Indicators

Key SLIs:

## Recording Coverage

```text
Delivered Audio Time

÷

Expected Audio Time
```

---

## Gap Duration

```text
Missing Recording Time

Per Station

Per Reporting Window
```

---

## Segment Delivery Delay

```text
Segment Completion

↓

Bucket Availability
```

---

## Station Recovery Time

```text
Failure Detection

↓

Recording Resumed
```

---

## Healthy Station Ratio

```text
Healthy Stations

÷

Enabled Stations
```

---

# 16. Alerting Philosophy

Avoid alerting on every transient event.

Alert when actionable intervention is required.

Alerts should answer:

- What failed?
- Which station is affected?
- What is the business impact?
- What should the responder check first?

---

# 17. Runbooks

Minimum required runbooks:

- Recording Gap Investigation
- Recorder Crash Investigation
- Pod Scheduling Failure
- Node Failure
- S3 Upload Failure
- Upload Backlog Growth
- Disk Pressure
- Missing Metrics
- Failed Alert Delivery

Each runbook should document:

- Impact assessment
- Recovery procedure
- Validation checks
- Remaining recording gaps

---

# 18. AWS Well-Architected Alignment

## Operational Excellence

- Infrastructure as Code
- CI/CD
- Git workflows
- Runbooks
- Post-incident reviews

## Security

- IRSA
- Least privilege
- Encryption
- Auditability
- Secret management

## Reliability

- Self-healing workloads
- Health checks
- Capacity planning
- Recovery testing

## Performance Efficiency

- Horizontal scaling
- Metrics-driven optimisation
- Workload isolation

## Cost Optimisation

- Rightsizing
- Autoscaling
- Cost visibility

## Sustainability

- Efficient resource usage
- Reduced idle capacity
- Storage lifecycle management

---

# 19. Current Implementation Status

## Implemented

✅ Terraform Infrastructure

✅ Amazon VPC

✅ Amazon S3

✅ Amazon ECR

✅ Amazon EKS

✅ Managed Node Groups

✅ OIDC Provider

✅ IRSA

✅ Kubernetes Deployments

✅ Structured Logging

✅ End-to-End Upload Pipeline

✅ S3 Validation

---

## Planned

- Real Audio Recording
- Assignment Controller
- Gap Detection Service
- Prometheus
- Grafana
- AlertManager
- Autoscaling
- SLO Reporting
- Production CI/CD

---

# 20. Success Criteria

The platform is considered production ready when it can:

- Record continuously 24/7
- Scale from 20 to 100+ stations
- Detect recording gaps
- Recover automatically from expected failures
- Meet defined SLOs
- Provide actionable observability
- Operate with minimal manual intervention
- Support disaster recovery testing