# SignalForge Milestone 002 — Validation Workload Running

Date: 2026-08-26

## Result

A three-replica nginx validation workload was deployed successfully to the SignalForge Kubernetes cluster.

## Validation

- Namespace: signalforge-test
- Deployment: signalforge-web
- Replicas: 3/3 Ready
- Service: signalforge-web
- Service type: ClusterIP
- Pod network: 10.244.0.0/16
- CNI: Calico
- Runtime: containerd

## Pod Placement

| Pod Role | Node |
|---|---|
| signalforge-web replica | forge-node-01 |
| signalforge-web replica | forge-node-02 |
| signalforge-web replica | forge-node-03 |

## Confirmed

- Scheduler places workloads on worker nodes
- Pods receive Calico pod-network IPs
- Deployment controller maintains desired replicas
- ClusterIP Service exists and selects the workload Pods
- CNI plugin path issue was resolved by pointing containerd to /opt/cni/bin

## Next

- Test in-cluster DNS and Service routing
- Optional NodePort browser test
- Deploy first custom FastAPI app
