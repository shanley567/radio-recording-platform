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

## 5. Recording and upload workflow

For each enabled station, the proposed worker workflow is:

1. Receive or discover the station assignment.
2. Start the recording binary with the station URL and required options.
3. Record audio into a bounded segment, using a configured duration.
4. On segment completion, validate that the file exists and is not empty; record its station ID, start time, end time, duration, and status.
5. Upload the completed segment to the recordings bucket.
6. Confirm successful upload before marking the segment delivered.
7. Remove the local file after successful delivery.
8. Continue recording the next segment.
9. On stream or upload errors, emit health and error signals, retry according to policy, and preserve or safely discard local data according to the defined disk-capacity policy.

A segment should only be considered complete when it has been finalized and is available in the bucket. If the recorder crashes while writing a segment, the incomplete local file should not be presented to downstream consumers as a completed recording.

Example object layout

```text
recordings/
  station-001/
    year=2026/month=11/day=10/hour=13/
      2026-11-10T13-00-00Z__2026-11-10T13-05-00Z.<audio-extension>
      2026-11-10T13-05-00Z__2026-11-10T13-10-00Z.<audio-extension>
```

The final audio extension and encoding depend on the recording binary and downstream requirements. Object keys should use UTC timestamps and a documented naming convention. Segment metadata can be stored alongside each object or in a separate index, depending on how downstream consumers query recordings.

## 6. Reliability and Recovery

The system should be designed so that a worker failure affects as few stations and as little recording time as practical.

### Worker and process failures

- Run health checks that distinguish a live process from a recorder that is alive but no longer producing segments.
- Restart a failed recorder process or replace its worker.
- Detect assignments that have not reported progress within a defined timeout.
- Ensure a replacement worker can take over an assignment without creating two indefinitely active recorders for the same station.
- Make upload and completion handling idempotent where possible. Retries must not silently create conflicting objects or duplicate downstream processing.

### Stream Failures

- Retry transient connection failures with retry, exponential backoffs and jitter
- Track reconnection attempts and time spent disconnected
- Alerts on failures
- Seperate stream & worker health - a stream may not recieve audio due to unavailable URL, not failed worker.

### Infastructure Failures

- Spread workloadsacross failure domains where available
- Use appropriate worker replicas and node capacity
- Configure disruption handling to prevent maintenance stopping all recorders
- Test recovery behaviour by restarting workers and interrupting streams in test env (can use spot instances and remove files to simulate)

### Delivery semantics

THis design allows for rapid recovery and eventual delivery.
However it cannot provide 100% audio due to:

- Source outage
- Network interruptions
- Worker Terminations
- Local disk failures
  It makes gaps observable, not conceal them.

## 7. Scaling Design

The unit of scaline is the number of stations being recorded at once.

- The desired station list determines how many revorder assignments should exist.
- Adding stations created additional assignments and recorder capacity.
- Disabling stations removes their assignment cleanly.
- Capacity is measured in CPU, memory, network & local disk used per recorder, with capacity for reconnects and uneaven stream behaviour.
- Scaling to be measured by increasing station count incrementally and observing metrics such as startup time, resource use, upload rate and gap rate.
- Worker placement and resource limits should prevent one busy or unhealthy revorder from exhausting resources needed by other stations.

A simple initial mode of one recorder per station would work.

Scaling should not rely on only average CPU.
Useful capacity signals include active assignments, pending assignments, recorder startup times, upload throughput, number of stations with no revent completed segment.

## 8. Monitoring & Gap Detection

## 9. S3 &  Downstream Access

## 10. Security & Operations

## 11. Service Objectives

## 12. Implementation Status

## 13. Validation Plan

## 14. Limitations
## 15. SRE Monitoring
Monitor both the recording service and the infrastructure it depends on. Audio-gap detection shows whether recordings are missing; platform monitoring helps explain why and whether the system can recover.

### Platform health signals

| Area | Signals to monitor |
|---|---|
| Recorder workloads | Pod readiness, restarts, pending pods, CPU and memory usage, and recorder process health |
| Kubernetes capacity | Node readiness, available CPU and memory, pod capacity, scheduling failures, and autoscaling activity |
| Application delivery | S3 upload success and failure rates, upload latency, retries, and any backlog of completed segments awaiting upload |
| Network and dependencies | DNS failures, connection errors, and sustained failures reaching station streams or required AWS services |
| Storage | Bucket access failures, object counts and growth, and local temporary-disk usage |
| Observability pipeline | Metrics and logs ingestion health, alert evaluation, and alert-notification delivery |

Use metrics for trends and alerting, structured logs for investigation, and dashboards for operational context. Logs should include station ID, worker identity, segment timestamps, and error category, but not sensitive URL credentials.

### Service-level indicators

Track service-level indicators (SLIs) that reflect the user-visible outcome:

- **Recording coverage:** delivered audio time divided by expected audio time for enabled stations.
- **Gap duration:** missing audio time per station over a reporting window.
- **Segment delivery delay:** time from segment completion to availability in the bucket.
- **Station recovery time:** time from a detected failure to resumed recording.
- **Healthy station ratio:** enabled stations with a healthy recorder and recent successful segment delivery, divided by all enabled stations.

Define the measurement window, grace periods, exclusions, and target values before setting service-level objectives (SLOs). Alert on sustained SLO risk or actionable failures, rather than every short-lived fluctuation.

### Alerting and response

Alerts should identify the affected service or station, the impact, when it began, and a useful next diagnostic step. Group related alerts to avoid flooding responders when one infrastructure issue affects many stations.

Create runbooks for at least:

- a station with a recording gap;
- recorder pods repeatedly restarting or failing to schedule;
- sustained S3 upload failures or a growing upload backlog;
- low worker capacity or unhealthy nodes;
- disk pressure; and
- missing metrics, logs, or alert notifications.

For each runbook, document how to assess impact, restore service, confirm recording has resumed, and record any remaining gap. Test alert delivery and recovery procedures in a non-production environment.
