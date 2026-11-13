# Radio Recording Platform Runbook

This runbook documents the current platform implementation in this repository: Terraform provisions AWS EKS/ECR/VPC/S3; the app builds as a Python container; the Kubernetes deployment runs a synthetic generator that uploads JSON payloads to S3; Prometheus metrics are exposed on port 8000; Prometheus/Grafana are installed separately with Helm for monitoring.

This is a runbook only and has not been added to the project repository.

## 1. Scope and assumptions

The project currently:
- Provisions AWS infrastructure with Terraform
- Builds a Python container in `app/`
- Pushes the image to Amazon ECR
- Deploys to EKS with Kubernetes manifests under `kubernetes/`
- Generates synthetic recording metadata and uploads it to S3
- Exposes Prometheus metrics at `/metrics` on port `8000`

Important repo-specific details:
- Terraform default region is `eu-west-2`
- Terraform default bucket is `jsp-radio-recordings-bucket-2026-demo`
- EKS cluster name is `radio-platform`
- Namespace is `radio-platform`
- The Kubernetes deployment is called `synthetic-generator`
- The app has a hard-coded bucket name in `app/generator.py`
- The service account uses IRSA and a role ARN annotation in `kubernetes/serviceaccount.yaml`

This repository does not currently contain a Prometheus/Grafana deployment manifest. Monitoring is done by installing the `kube-prometheus-stack` via Helm and creating a `ServiceMonitor`.

---

## 2. Prerequisites

Install and configure:

- Docker
- AWS CLI v2
- Terraform >= 1.6
- `kubectl`
- Helm 3
- Git
- Access to the target AWS account and AWS ECR/EKS resources

Confirm your AWS identity:

```bash
aws sts get-caller-identity
aws configure get region
```

Set environment variables:

```bash
export AWS_REGION=eu-west-2
export CLUSTER_NAME=radio-platform
export NAMESPACE=radio-platform
export IMAGE_TAG="$(git rev-parse --short HEAD)"
```

> Do not store AWS keys in the repo. Use AWS SSO, profile-based auth, or another approved credential source.

---

## 3. Provision AWS infrastructure

Terraform code is in `terraform/` and creates:
- VPC
- EKS cluster
- Managed node group
- ECR repository
- IAM role for IRSA
- S3 bucket

From the repo root:

```bash
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan
```

Review the plan carefully. This can create real AWS resources and costs.

Then apply:

```bash
terraform -chdir=terraform apply
```

Capture key outputs:

```bash
export ECR_URI="$(terraform -chdir=terraform output -raw ecr_repository_url)"
export BUCKET_NAME="$(terraform -chdir=terraform output -raw bucket_name)"
export CLUSTER_NAME="$(terraform -chdir=terraform output -raw cluster_name)"

echo "ECR: ${ECR_URI}"
echo "Bucket: ${BUCKET_NAME}"
echo "Cluster: ${CLUSTER_NAME}"
```

Important:
- Check the bucket name and account are correct before proceeding.
- The app source code contains a hard-coded `BUCKET_NAME`, so ensure it matches the Terraform-created bucket.
- The service account annotation in `kubernetes/serviceaccount.yaml` must match the Terraform role ARN for your AWS account.

---

## 4. Build the Docker image

The Dockerfile is in `app/Dockerfile`. Build it from the repo root:

```bash
docker build --pull -t synthetic-generator ./app
```

If you want the build to match the ECR tag you will push:

```bash
docker build --pull -t "${ECR_URI}:${IMAGE_TAG}" ./app
```

Verify the image exists locally:

```bash
docker image inspect "${ECR_URI}:${IMAGE_TAG}" --format '{{.Id}}'
```

---

## 5. Push the image to Amazon ECR

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_URI%%/*}"
```

Push the image:

```bash
docker push "${ECR_URI}:${IMAGE_TAG}"
```

Verify the image is in the repository:

```bash
aws ecr describe-images \
  --region "${AWS_REGION}" \
  --repository-name synthetic-generator \
  --image-ids imageTag="${IMAGE_TAG}"
```

> Prefer unique immutable tags such as the Git SHA rather than `latest`. This makes rollback easier and deployment safer.

---

## 6. Connect `kubectl` to the EKS cluster

Update the kubeconfig:

```bash
aws eks update-kubeconfig --region "${AWS_REGION}" --name "${CLUSTER_NAME}"
kubectl config current-context
kubectl cluster-info
kubectl get nodes -o wide
```

Wait for the cluster and node group to be healthy before deploying.

---

## 7. Deploy to Kubernetes

### 7.1 Validate the IRSA role and service account

From `terraform/iam.tf`, the trust relationship is set for:

```text
system:serviceaccount:radio-platform:synthetic-generator
```

Check the Terraform IAM role:

```bash
terraform -chdir=terraform state show aws_iam_role.generator
```

Ensure the role ARN in `kubernetes/serviceaccount.yaml` matches the one created in the target AWS account. If it does not, update it before deployment.

### 7.2 Apply Kubernetes manifests

Apply namespace, service account, service, and deployment:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/serviceaccount.yaml
kubectl apply -f kubernetes/service.yaml

sed "s|image: .*|image: ${ECR_URI}:${IMAGE_TAG}|" kubernetes/deployment.yaml \
  | kubectl apply -f -
```

Check rollout:

```bash
kubectl -n "${NAMESPACE}" rollout status deployment/synthetic-generator --timeout=180s
kubectl -n "${NAMESPACE}" get deployment,pods,service,serviceaccount -o wide
kubectl -n "${NAMESPACE}" get events --sort-by=.lastTimestamp
```

Expected result:
- One pod is Running and Ready
- Deployment has desired replicas available
- Service exposes port `8000`
- Service account has the correct IAM role annotation

---

## 8. Validate the platform is working

### 8.1 Review pod logs

```bash
kubectl -n "${NAMESPACE}" logs deployment/synthetic-generator --since=15m
kubectl -n "${NAMESPACE}" logs deployment/synthetic-generator --follow
```

Look for:
- Boot logs
- Generation cycle started
- Station processing
- Upload attempts
- Success logs or failure logs
- The app logs a metrics endpoint on `http://0.0.0.0:8000/metrics`

### 8.2 Check S3 uploads

Because this app uploads JSON files to S3, verify that data is being created:

```bash
aws s3 ls "s3://${BUCKET_NAME}/" --recursive --human-readable | tail -30
```

Expected:
- Objects appear in prefixes like `station-001/...`, `station-002/...`, `station-003/...`
- Files are created under date/time-based directories

If you see `AccessDenied` or no uploads:
- Confirm IRSA is working
- Check the service account annotation
- Validate the IAM trust policy and S3 upload policy
- Confirm the bucket name in the app matches the real bucket name
- Check the pod logs for exception messages

### 8.3 Port-forward the app and inspect the metrics endpoint

```bash
kubectl -n "${NAMESPACE}" port-forward service/synthetic-generator 8000:8000
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:8000/metrics | grep -E '^(recordings_generated_total|s3_upload_success_total|s3_upload_failure_total|upload_duration_seconds|generation_cycle_duration_seconds)'
```

You should see metrics in Prometheus text format.

The app exports:
- `recordings_generated_total`
- `s3_upload_success_total`
- `s3_upload_failure_total`
- `upload_duration_seconds`
- `generation_cycle_duration_seconds`

These are labeled by `station` where relevant.

---

## 9. Install Prometheus and Grafana

The repo does not currently define monitoring components. To view metrics in Grafana, install the community stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

Check the pods:

```bash
kubectl -n monitoring get pods
```

Wait until Prometheus and Grafana are ready.

---

## 10. Configure Prometheus to scrape the app

The Kubernetes service already exposes port 8000 with the name `metrics`.

Create a `ServiceMonitor`:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: synthetic-generator
  namespace: radio-platform
  labels:
    release: prometheus
spec:
  namespaceSelector:
    matchNames:
      - radio-platform
  selector:
    matchLabels:
      app: synthetic-generator
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
EOF
```

Validate:

```bash
kubectl -n radio-platform get servicemonitor synthetic-generator
kubectl -n monitoring port-forward service/prometheus-kube-prometheus-prometheus 9090:9090
```

Open:
- http://localhost:9090

Check:
- Status → Targets
- The target should show as `UP`

Prometheus queries to test:

```promql
up{namespace="radio-platform"}

sum by (station) (rate(recordings_generated_total{namespace="radio-platform"}[5m]))

sum by (station) (rate(s3_upload_success_total{namespace="radio-platform"}[5m]))

sum by (station) (increase(s3_upload_failure_total{namespace="radio-platform"}[15m]))
```

If the target is not `UP`, check:
- `release: prometheus` label on the `ServiceMonitor`
- `matchLabels: app: synthetic-generator` on the Service
- Service port name is `metrics`
- Prometheus can reach the app on port 8000
- The `ServiceMonitor` CRD is installed by the Helm chart

---

## 11. View metrics in Grafana

Port-forward Grafana:

```bash
kubectl -n monitoring port-forward service/prometheus-grafana 3000:80
```

Open:
- http://localhost:3000

Login:
- Username: `admin`

Get the Grafana password:

```bash
kubectl -n monitoring get secret prometheus-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode; echo
```

Once logged in:
- Open Grafana Explore
- Select the Prometheus data source
- Run queries like:

```promql
# Scrape health
up{namespace="radio-platform"}

# Generated records by station
sum by (station) (rate(recordings_generated_total{namespace="radio-platform"}[5m]))

# Successful S3 uploads by station
sum by (station) (rate(s3_upload_success_total{namespace="radio-platform"}[5m]))

# Failed uploads
sum by (station) (increase(s3_upload_failure_total{namespace="radio-platform"}[15m]))

# Upload latency
histogram_quantile(0.95, sum by (station, le) (rate(upload_duration_seconds_bucket{namespace="radio-platform"}[5m])))

# Generation cycle latency
histogram_quantile(0.95, sum by (le) (rate(generation_cycle_duration_seconds_bucket{namespace="radio-platform"}[5m])))
```

Expected behavior:
- Metrics should be scrapped successfully
- Upload counters should increase over time
- Duration histograms should show data
- The app is healthy if it continues generating and uploading records

---

## 12. Routine release procedure

For each release:

1. Update code and validate changes
2. Build a new container image with a unique tag
3. Push to ECR
4. Update the Kubernetes deployment image
5. Verify rollout
6. Review logs
7. Check S3 output
8. Confirm Prometheus target is `UP`
9. Check Grafana data

Example deployment update:

```bash
kubectl -n "${NAMESPACE}" set image deployment/synthetic-generator \
  synthetic-generator="${ECR_URI}:${IMAGE_TAG}"

kubectl -n "${NAMESPACE}" rollout status deployment/synthetic-generator --timeout=180s
kubectl -n "${NAMESPACE}" logs deployment/synthetic-generator --since=5m
```

Rollback example:

```bash
kubectl -n "${NAMESPACE}" set image deployment/synthetic-generator \
  synthetic-generator="${ECR_URI}:<previous-tag>"

kubectl -n "${NAMESPACE}" rollout status deployment/synthetic-generator --timeout=180s
kubectl -n "${NAMESPACE}" rollout history deployment/synthetic-generator
```

---

## 13. Troubleshooting quick reference

### Pod is not starting
```bash
kubectl -n "${NAMESPACE}" describe pod <pod-name>
kubectl -n "${NAMESPACE}" logs deployment/synthetic-generator --previous
```

### Image pull failure
```bash
kubectl -n "${NAMESPACE}" describe pod <pod-name>
aws ecr describe-images --region "${AWS_REGION}" --repository-name synthetic-generator
```

### AccessDenied on S3 upload
Check:
- service account annotation
- IAM trust relationship for IRSA
- AWS role ARN
- bucket name
- `s3:PutObject` permission on the actual bucket

### Metrics endpoint not reachable
```bash
kubectl -n "${NAMESPACE}" get svc
kubectl -n "${NAMESPACE}" get endpoints
kubectl -n "${NAMESPACE}" port-forward service/synthetic-generator 8000:8000
curl -v http://127.0.0.1:8000/metrics
```

### Prometheus target is down
```bash
kubectl -n monitoring get pods
kubectl -n radio-platform get servicemonitor
kubectl -n monitoring port-forward service/prometheus-kube-prometheus-prometheus 9090:9090
```

Then verify:
- `ServiceMonitor` exists
- target appears in Prometheus
- the service label matches `app: synthetic-generator`
- the port is named `metrics`

### Grafana no data
- Confirm target is `UP`
- Give Prometheus enough time to scrape
- Use a recent time range
- Verify the metric names and labels are present

---

## 14. Operational cautions

- This project is a prototype synthetic-data generator; it is not a full live radio capture environment.
- It does not currently include production-grade alerting, readiness/liveness probes, or full observability automation.
- The app uses a hard-coded bucket name and some values are static in YAML; keep these aligned with Terraform.
- EKS, NAT Gateway, ECR, and S3 can incur AWS cost.
- `terraform destroy` deletes infrastructure and can remove data.
- Do not expose Prometheus or Grafana publicly without authentication and network controls.

---

## 15. Useful commands summary

```bash
# Terraform
terraform -chdir=terraform init
terraform -chdir=terraform validate
terraform -chdir=terraform plan
terraform -chdir=terraform apply

# Container build
docker build --pull -t synthetic-generator ./app
docker build --pull -t "${ECR_URI}:${IMAGE_TAG}" ./app
docker push "${ECR_URI}:${IMAGE_TAG}"

# EKS
aws eks update-kubeconfig --region "${AWS_REGION}" --name "${CLUSTER_NAME}"
kubectl -n "${NAMESPACE}" get pods
kubectl -n "${NAMESPACE}" logs deployment/synthetic-generator --follow

# Metrics
kubectl -n "${NAMESPACE}" port-forward service/synthetic-generator 8000:8000
curl -fsS http://127.0.0.1:8000/metrics

# Prometheus/Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

kubectl -n monitoring port-forward service/prometheus-grafana 3000:80
kubectl -n monitoring port-forward service/prometheus-kube-prometheus-prometheus 9090:9090
```

This runbook is based on the repository’s current implementation and should be updated when the project adds live audio capture, actual alerting, or deployment automation beyond the current prototype.