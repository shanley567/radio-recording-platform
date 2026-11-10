# Radio Recording Platform — Solution Design

## 1. Purpose

This document describes a resilient, scalable design for continuously recording audio from radio stream URLs and storing completed recordings in a data bucket for downstream processing.

The current portfolio project validates parts of the infrastructure and deployment path using synthetic JSON records. It does **not** yet record real radio audio. This document describes the proposed target design and identifies which parts are implemented versus planned.

## 2. Requirements

The design addresses these requirements:

1. Record continuously, aiming to minimize lost audio.
2. Write recordings to durable object storage accessible to another system.
3. Scale the number of active recordings up or down with the station count.
4. Monitor recording health, identify gaps, and support operational response.

## 3. Scope and assumptions

- A pre-built recording binary is available and can run in a container.
- Each station has a configured radio URL and recording settings.
- A station may need to reconnect when its stream or network connection fails.
- Recording files are produced as segments, rather than a single indefinitely growing file. Segment duration and audio format are configuration choices to confirm.
- The initial deployment target is AWS, using the existing Terraform, EKS, ECR, and S3 foundation.
- The design aims for automatic recovery and clear detection of gaps. It does not claim lossless recording through every upstream, network, or infrastructure failure.
- Real audio ingestion, station scheduling, gap detection, and production alerting are not implemented in the current prototype.

## 4. Proposed architecture

```text
Station configuration
        │
        ▼
Station registry / configuration store
        │
        ▼
Station assignment and desired-state controller
        │
        ├── station-001 ──► recorder worker ──┐
        ├── station-002 ──► recorder worker ──┤
        └── station-N   ──► recorder worker ──┤
                                             ▼
                                  Audio segment storage
                                             │
                                  Validate and finalize
                                             │
                                             ▼
                                  S3 recordings bucket
                                     │             │
                                     ▼             ▼
                              Gap monitoring   Downstream
                              and alerting      processing
```
### Main components
- Station configuration: Holds station IDs, stream URLs, enabled state, and recording settings. Secrets or sensitive URLs should be stored and accessed using an appropriate secret-management mechanism.
- Assignment controller: Ensures each enabled station has an active recorder assignment. It detects stale assignments and replaces workers that stop reporting health.
- Recorder worker: Runs the pre-built recording binary for an assigned station. It reconnects after transient stream failures, writes bounded audio segments, and uploads completed segments.
- Object storage: Stores finalized audio segments using a predictable station-and-time-based object key.
Monitoring and alerting: Tracks recorder health, segment delivery, stream failures, and missing or short segments. It notifies operators when recovery does not happen automatically.
- Downstream processor: Reads finalized audio objects. Its integration should be independent of the recorder’s local filesystem and pod lifecycle.

The current EKS deployment can be a starting point for running recorder workers. The assignment controller and the production workflow described here are proposed components, not part of the current implementation.