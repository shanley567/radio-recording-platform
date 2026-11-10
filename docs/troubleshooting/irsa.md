# Troubleshooting IRSA

## Symptom

Files generated locally.

No files uploaded to S3.

---

## Verification

Enter pod:

```bash
kubectl exec -it <pod> -- sh
```

Run:

```python
import boto3
print(boto3.client("sts").get_caller_identity())
```

---

## Error

```text
NoCredentialsError:
Unable to locate credentials
```

---

## Resolution

Implemented:

- OIDC Provider
- IAM Role
- IAM Policy
- Service Account Annotation

Example:

```yaml
annotations:
  eks.amazonaws.com/role-arn: arn:aws:iam::<account>:role/radio-platform-generator
```

---

## Validation

```python
boto3.client("sts").get_caller_identity()
```

Expected:

```text
arn:aws:sts::<account>:assumed-role/radio-platform-generator
```
