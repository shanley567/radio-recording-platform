# Troubleshooting Workflow

Follow this order when investigating failures.

## Infrastructure

```bash
terraform plan
terraform apply
```

---

## Cluster

```bash
aws eks describe-cluster
kubectl get nodes
```

---

## Node Group

```bash
aws eks describe-nodegroup
aws autoscaling describe-scaling-activities
```

---

## Pods

```bash
kubectl get pods -A
kubectl describe pod <pod>
kubectl logs <pod>
```

---

## Authentication

```bash
kubectl exec -it <pod> -- sh
```

```python
import boto3
print(boto3.client("sts").get_caller_identity())
```

---

## Storage

```bash
aws s3 ls s3://bucket --recursive
```

---

Always work from:

```text
Infrastructure
↓
Cluster
↓
Nodes
↓
Pods
↓
Application
↓
AWS Service
```

Avoid jumping directly into application debugging before validating platform health.
