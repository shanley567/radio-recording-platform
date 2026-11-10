# Troubleshooting EKS Node Groups

## Symptom

```text
Node Group stuck in CREATING
```

## Investigation

Check status:

```bash
aws eks describe-nodegroup \
  --cluster-name radio-platform \
  --nodegroup-name <nodegroup>
```

---

Check scaling activities:

```bash
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name <asg>
```

---

## Root Causes Encountered

### Unsupported Instance Type

Error:

```text
InvalidParameterCombination
The specified instance type is not eligible
```

Resolution:

```terraform
instance_types = ["t3.micro"]
```

---

### NodeCreationFailure

Node launched but failed registration.

Investigate:

```bash
kubectl get nodes
kubectl describe node <node>
```
