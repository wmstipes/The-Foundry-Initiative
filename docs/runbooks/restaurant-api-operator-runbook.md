# SignalForge Restaurant API Operator Runbook

This runbook explains how to operate, validate, troubleshoot, and recover the SignalForge Restaurant API running on the Raspberry Pi Kubernetes cluster.

## System Overview

The SignalForge Restaurant API is a FastAPI application deployed to the SignalForge Kubernetes cluster.

The app is built by GitHub Actions, published to Docker Hub, and deployed to Kubernetes using manifests stored in this repository.

## Current Application

Application: SignalForge Restaurant API

Namespace: forge-restaurant

Deployment: restaurant-api

Internal Service: restaurant-api

External Lab Service: restaurant-api-nodeport

NodePort: 30080

Current release: 0.6.0

Current image:

~~~text
wmstipes/signalforge-restaurant-api:0.6.0
~~~

## Cluster Nodes

Expected nodes:

~~~text
forge-head
forge-node-01
forge-node-02
forge-node-03
~~~

Check nodes:

~~~powershell
kubectl get nodes -o wide
~~~

## Public Lab URLs

The NodePort service exposes the API through any cluster node IP on port 30080.

~~~text
http://192.168.243.110:30080/docs
http://192.168.243.111:30080/docs
http://192.168.243.112:30080/docs
http://192.168.243.113:30080/docs
~~~

Useful direct endpoints:

~~~text
http://192.168.243.110:30080/version
http://192.168.243.110:30080/status
http://192.168.243.110:30080/menu
~~~

## Repository Paths

Application code:

~~~text
apps/restaurant-api
~~~

Kubernetes manifests:

~~~text
k8s/fastapi-restaurant
~~~

Scripts:

~~~text
scripts/deploy-restaurant-api.ps1
scripts/forge.ps1
~~~

Milestones:

~~~text
docs/milestones
~~~

Runbooks:

~~~text
docs/runbooks
~~~

## Normal Operating Workflow

From the Windows laptop:

~~~powershell
cd C:\Users\wmsti\The-Foundry-Initiative
git pull origin main
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 status
~~~

This confirms that the laptop can reach the Kubernetes cluster and that the Restaurant API resources exist.

## Deploy the Restaurant API

Use the deployment helper:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 deploy
~~~

The deploy command should:

- Apply Kubernetes manifests
- Wait for the Deployment rollout
- Show current Pods
- Show the deployed image
- Run smoke tests against `/version`
- Run smoke tests against `/status`

## Run Smoke Tests Only

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
~~~

Expected `/version` result includes:

~~~json
"version": "0.6.0"
~~~

Expected `/status` result includes:

~~~json
"status": "open"
~~~

## Check Current Deployment Image

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 image
~~~

Expected:

~~~text
wmstipes/signalforge-restaurant-api:0.6.0
~~~

## Check Pods

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 pods
~~~

Expected:

~~~text
Three restaurant-api Pods
Each Pod is 1/1
Each Pod is Running
Pods are spread across worker nodes when possible
~~~

## View Logs

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 logs
~~~

Use logs when:

- The app is reachable but behaving strangely
- Smoke tests fail
- A Pod restarted
- An endpoint returns an unexpected response

## Manual Kubernetes Checks

Show namespace resources:

~~~powershell
kubectl get all -n forge-restaurant
~~~

Describe the Deployment:

~~~powershell
kubectl describe deployment restaurant-api -n forge-restaurant
~~~

Describe matching Pods:

~~~powershell
kubectl describe pods -n forge-restaurant -l app=restaurant-api
~~~

Check rollout history:

~~~powershell
kubectl rollout history deployment/restaurant-api -n forge-restaurant
~~~

## Apply Manifests Manually

From the repo root:

~~~powershell
kubectl apply -f k8s\fastapi-restaurant\
~~~

Then verify rollout:

~~~powershell
kubectl rollout status deployment/restaurant-api -n forge-restaurant
~~~

## Kubernetes Context Check

Check current context:

~~~powershell
kubectl config current-context
~~~

Expected context:

~~~text
kubernetes-admin@kubernetes
~~~

Check cluster access:

~~~powershell
kubectl cluster-info
kubectl get nodes
~~~

## Common Issue: Laptop kubectl Tries localhost:8080

Symptom:

~~~text
dial tcp [::1]:8080: connectex: No connection could be made
~~~

Meaning:

Windows kubectl does not have a working kubeconfig or current Kubernetes context.

Temporary fix for current PowerShell session:

~~~powershell
$env:KUBECONFIG="$env:USERPROFILE\.kube\config-signalforge"
kubectl get nodes
~~~

Persistent user-level fix:

~~~powershell
[Environment]::SetEnvironmentVariable(
  "KUBECONFIG",
  "$env:USERPROFILE\.kube\config-signalforge",
  "User"
)
~~~

Close PowerShell, open a new one, then test:

~~~powershell
kubectl get nodes
~~~

## Common Issue: ImagePullBackOff

Symptom:

~~~text
ImagePullBackOff
ErrImagePull
~~~

Check Pods:

~~~powershell
kubectl get pods -n forge-restaurant
~~~

Describe the failing Pod:

~~~powershell
kubectl describe pods -n forge-restaurant -l app=restaurant-api
~~~

Check current image:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 image
~~~

Likely causes:

- Docker image tag does not exist
- GitHub Actions build failed
- Docker Hub push failed
- Deployment references the wrong image name
- Node cannot reach Docker Hub

Recovery:

1. Confirm GitHub Actions succeeded.
2. Confirm Docker Hub has the expected image tag.
3. Correct the image in `k8s/fastapi-restaurant/restaurant-api-deployment.yaml`.
4. Reapply manifests.
5. Watch rollout.

~~~powershell
kubectl apply -f k8s\fastapi-restaurant\
kubectl rollout status deployment/restaurant-api -n forge-restaurant
~~~

## Common Issue: ConfigMap Changed but App Still Shows Old Value

Meaning:

Environment variables from a ConfigMap are loaded when the container starts. Existing Pods do not automatically reload those environment variables.

Restart the Deployment:

~~~powershell
kubectl rollout restart deployment/restaurant-api -n forge-restaurant
kubectl rollout status deployment/restaurant-api -n forge-restaurant
~~~

Then smoke test:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
~~~

## Common Issue: Deployment Does Not Roll Out

Check rollout status:

~~~powershell
kubectl rollout status deployment/restaurant-api -n forge-restaurant
~~~

Check Deployment details:

~~~powershell
kubectl describe deployment restaurant-api -n forge-restaurant
~~~

Check ReplicaSets:

~~~powershell
kubectl get rs -n forge-restaurant
~~~

Check Pods:

~~~powershell
kubectl get pods -n forge-restaurant -o wide
~~~

Likely causes:

- New image cannot be pulled
- Readiness probe is failing
- App container is crashing
- Resource requests cannot be scheduled
- Node issue

## Common Issue: Readiness Probe Fails

Check Pods:

~~~powershell
kubectl get pods -n forge-restaurant
~~~

Describe Pods:

~~~powershell
kubectl describe pods -n forge-restaurant -l app=restaurant-api
~~~

Check app endpoint manually inside the cluster:

~~~powershell
kubectl run curl-test -n forge-restaurant --image=curlimages/curl:latest --restart=Never --rm -i --command -- curl -s http://restaurant-api/ready
~~~

Expected:

~~~json
{"status":"ready"}
~~~

Likely causes:

- App did not start
- `/ready` endpoint changed
- Service target port is wrong
- Container port is wrong

## Common Issue: NodePort Does Not Work from Browser

Check NodePort service:

~~~powershell
kubectl get svc restaurant-api-nodeport -n forge-restaurant
~~~

Expected NodePort:

~~~text
30080
~~~

Check endpoint from inside the cluster:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
~~~

If inside-cluster smoke tests work but browser access fails, likely causes include:

- Laptop is not on the same network
- Node IP changed
- Firewall or routing issue
- NodePort service was changed
- Cluster node is down

Check node IPs:

~~~powershell
kubectl get nodes -o wide
~~~

## Common Issue: Service Exists but Has No Endpoints

Check service:

~~~powershell
kubectl get svc restaurant-api -n forge-restaurant
~~~

Check endpoints:

~~~powershell
kubectl get endpoints restaurant-api -n forge-restaurant
~~~

Likely causes:

- Service selector does not match Pod labels
- Pods are not Ready
- Deployment labels changed

Check labels:

~~~powershell
kubectl get pods -n forge-restaurant --show-labels
kubectl describe svc restaurant-api -n forge-restaurant
~~~

## Rollback Procedure

Check rollout history:

~~~powershell
kubectl rollout history deployment/restaurant-api -n forge-restaurant
~~~

Rollback to previous revision:

~~~powershell
kubectl rollout undo deployment/restaurant-api -n forge-restaurant
kubectl rollout status deployment/restaurant-api -n forge-restaurant
~~~

Verify:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 image
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
~~~

## Roll Forward Procedure

Prefer rolling forward over staying rolled back.

Update the manifest with the desired known-good image tag, then apply:

~~~powershell
kubectl apply -f k8s\fastapi-restaurant\
kubectl rollout status deployment/restaurant-api -n forge-restaurant
powershell -ExecutionPolicy Bypass -File .\scripts\forge.ps1 smoke
~~~

## Release Procedure

1. Update the app version in `apps/restaurant-api/main.py`.
2. Update `APP_VERSION` in `k8s/fastapi-restaurant/restaurant-api-config.yaml`.
3. Commit and push changes to `main`.
4. Confirm GitHub Actions passes.
5. Create a release tag.
6. Push the tag.
7. Confirm GitHub Actions builds and pushes the versioned Docker image.
8. Deploy the new image to Kubernetes.
9. Run smoke tests.
10. Capture a milestone.

Example tag:

~~~powershell
git tag -a v0.6.0 -m "Restaurant API v0.6.0"
git push origin v0.6.0
~~~

Expected Docker image:

~~~text
wmstipes/signalforge-restaurant-api:0.6.0
~~~

## Recovery Checklist

When something breaks, check in this order:

1. Current Kubernetes context
2. Cluster nodes
3. Namespace resources
4. Deployment rollout status
5. Pod status
6. Current deployed image
7. Service and endpoints
8. Application logs
9. In-cluster smoke tests
10. Browser or NodePort access

## Restaurant Analogy

The cluster is the restaurant district.

The control plane is the district manager.

The worker nodes are buildings that can host restaurants.

The Deployment is the kitchen staffing plan.

The Pods are active kitchen stations.

The internal Service is the restaurant district phone number.

The NodePort is the public front door.

The ConfigMap is the settings sheet.

The runbook is the manager checklist.

## Success Standard

The system is considered healthy when:

- All nodes are Ready
- Three Restaurant API Pods are Running
- The Deployment rollout is complete
- The deployed image is the expected release image
- `/version` returns the expected version
- `/status` returns `status: open`
- `/docs` is reachable through NodePort from the laptop

