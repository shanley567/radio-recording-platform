# Troubleshooting ECR

## ImagePullBackOff

Check:

```bash
kubectl describe pod <pod>
```

---

Verify image exists:

```bash
aws ecr list-images \
    --repository-name synthetic-generator
```

---

Root Cause Encountered

Repository was empty:

```json
{
  "imageIds": []
}
```

Resolution:

```bash
docker build
docker tag
docker push
```