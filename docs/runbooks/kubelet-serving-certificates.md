# SignalForge Kubelet Serving-Certificate Runbook

This runbook covers the serving certificates used when Metrics Server connects to SignalForge kubelets on TCP 10250.

## Current state

- `serverTLSBootstrap: true` is present in every node's `/var/lib/kubelet/config.yaml`.
- The same setting is stored in the kubeadm-managed `kube-system/kubelet-config` ConfigMap.
- Each kubelet serves a Kubernetes-CA-signed ECDSA certificate.
- Each certificate contains only that node's hostname and InternalIP SANs.
- Metrics Server supplies `--kubelet-certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`.
- Metrics Server does not use `--kubelet-insecure-tls`.

## Expected node identities

| Node | InternalIP |
|---|---|
| `forge-head` | `192.168.243.110` |
| `forge-node-01` | `192.168.243.111` |
| `forge-node-02` | `192.168.243.112` |
| `forge-node-03` | `192.168.243.113` |

## Check bootstrap configuration

Central kubeadm configuration:

```bash
kubectl get configmap kubelet-config \
  -n kube-system \
  -o jsonpath='{.data.kubelet}' |
  grep -nE '^(rotateCertificates|serverTLSBootstrap):'
```

Control plane:

```bash
sudo grep -E \
  '^(rotateCertificates|serverTLSBootstrap):' \
  /var/lib/kubelet/config.yaml
```

Workers from `forge-head`:

```bash
for node in forge-node-01 forge-node-02 forge-node-03; do
  echo
  echo "=== $node ==="

  ssh "wmstipes@$node" \
    "sudo grep -E '^(rotateCertificates|serverTLSBootstrap):' /var/lib/kubelet/config.yaml"
done
```

Expected on every node:

```text
rotateCertificates: true
serverTLSBootstrap: true
```

## Check the active certificates

On a node:

```bash
sudo openssl x509 \
  -in /var/lib/kubelet/pki/kubelet-server-current.pem \
  -noout \
  -subject \
  -issuer \
  -dates \
  -ext subjectAltName
```

The issuer must be `CN=kubernetes`. The subject and SANs must match the node table above.

From `forge-head`, verify the live TLS endpoint by InternalIP:

```bash
for target in \
  "forge-head=192.168.243.110" \
  "forge-node-01=192.168.243.111" \
  "forge-node-02=192.168.243.112" \
  "forge-node-03=192.168.243.113"
do
  name="${target%%=*}"
  ip="${target#*=}"

  echo
  echo "=== ${name} at ${ip} ==="

  curl \
    --cacert /etc/kubernetes/pki/ca.crt \
    --silent \
    --show-error \
    --output /dev/null \
    --write-out 'HTTP %{http_code}\n' \
    "https://${ip}:10250/healthz"
done
```

`HTTP 401` is expected. TLS succeeded, and the kubelet correctly rejected the unauthenticated HTTP request.

## Review a pending serving CSR

List CSRs:

```bash
kubectl get csr --sort-by=.metadata.creationTimestamp
```

Select only one current pending serving CSR:

```bash
csr="<csr-name>"

kubectl get csr "$csr" \
  -o jsonpath='signer: {.spec.signerName}{"\n"}requester: {.spec.username}{"\n"}groups: {.spec.groups[*]}{"\n"}usages: {.spec.usages[*]}{"\n"}'
```

Required metadata:

- Signer: `kubernetes.io/kubelet-serving`
- Requester: `system:node:<expected-node-name>`
- Groups: `system:nodes system:authenticated`
- ECDSA usages: `digital signature server auth`

Compare with the registered Node addresses:

```bash
node="<expected-node-name>"

kubectl get node "$node" \
  -o jsonpath='{range .status.addresses[*]}{.type}: {.address}{"\n"}{end}'
```

Decode the request:

```bash
csr_file="$(mktemp)"

kubectl get csr "$csr" -o jsonpath='{.spec.request}' |
  base64 --decode > "$csr_file"

openssl req -in "$csr_file" -noout -verify
openssl req -in "$csr_file" -noout -subject
openssl req -in "$csr_file" -noout -text |
  sed -n '/Requested Extensions:/,/Signature Algorithm:/p'

rm -f "$csr_file"
```

Required identity:

- Subject: `O=system:nodes, CN=system:node:<expected-node-name>`
- DNS SAN: expected node hostname
- IP SAN: expected node InternalIP
- No unrelated DNS names or IP addresses

Reject or leave pending any request that does not match. Never approve all pending CSRs as a group.

## Approve a validated request

```bash
kubectl certificate approve "$csr"
kubectl get csr "$csr"
```

Expected condition: `Approved,Issued`.

Verify the new certificate on that node and repeat the live TLS test before returning a cordoned node to scheduling.

## One-node-at-a-time repair sequence

Use this only when a node has lost the serving-bootstrap setting or needs its serving PKI repaired.

1. Confirm the other nodes are Ready.
2. Cordon the target node.
3. Back up `/var/lib/kubelet/config.yaml` to `/var/lib/kubelet/config.yaml.pre-m024` if that backup does not already exist.
4. Add top-level `serverTLSBootstrap: true` without setting `tlsCertFile` or `tlsPrivateKeyFile`.
5. Restart kubelet, not the entire node.
6. Confirm kubelet is active and the Node remains Ready.
7. Review and approve only the exact valid serving CSR.
8. Verify the issued certificate and live TLS endpoint.
9. Uncordon the node.
10. Repeat for another node only after the current node is healthy.

Example control commands:

```bash
node="forge-node-01"
kubectl cordon "$node"
sudo systemctl restart kubelet
sudo systemctl is-active kubelet
sudo journalctl -u kubelet -n 30 --no-pager
kubectl uncordon "$node"
```

## Rollback

If kubelet does not become active after a configuration edit, restore the node-local backup:

```bash
sudo cp -a \
  /var/lib/kubelet/config.yaml.pre-m024 \
  /var/lib/kubelet/config.yaml

sudo systemctl restart kubelet
sudo systemctl is-active kubelet
```

Do not delete the existing kubelet certificates as an initial recovery step. Preserve them for diagnosis and restore the known-good configuration first.

## Hostname and SSH trust notes

SignalForge uses stable DHCP reservations and explicit node-name mappings. On systems where cloud-init manages `/etc/hosts`, the persistent override is:

```yaml
# /etc/cloud/cloud.cfg.d/99-signalforge-hosts.cfg
manage_etc_hosts: false
```

Before adding or replacing an SSH `known_hosts` entry, compare the network-presented ED25519 fingerprint with the public host key read directly from that node's console:

```bash
sudo ssh-keygen -E sha256 -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Do not trust a scanned host key until its fingerprint matches the console value.
