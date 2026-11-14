# Full Runbook

AWS Login:

```
aws sts get-caller-identity
```

```
aws ecr get-login-password `
--region eu-west-2 |
docker login `
--username AWS 
```

Create docker image

```
docker build -t <docker_image> .
```

```
docker images
```

```
docker tag <docker_image> `
548722508417.dkr.ecr.eu-west-2.amazonaws.com/<docker_image>
```

```
docker push `                        
548722508417.dkr.ecr.eu-west-2.amazonaws.com/<docker_image>
```

Verify image is in ECR

```
aws ecr describe-repositories `
  --repository-names synthetic-generator `
  --region eu-west-2
```
