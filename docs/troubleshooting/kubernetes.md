# Troubleshooting Kubernetes

## Node NotReady

Check:

```bash
kubectl describe node <node>
```

Look for:

```text
NetworkPluginNotReady
```

---

## Missing CNI

Symptoms:

```text
Node registered
Node NotReady
```

Cause:

```bash
aws eks list-addons
```

returned:

```json
[]
```

Resolution:

Install:

- vpc-cni
- kube-proxy
- coredns

---

## Pod Pending

Check:

```bash
kubectl describe pod <pod>
```

Look at:

```text
Events
```

---

### Too Many Pods

Example:

```text
0/1 nodes are available
Too many pods
```

Resolution:

- Increase instance size
- Reduce CoreDNS replicas