"""Validate the Grafana deployment boundary and dashboard/provisioning contract."""
import configparser
import json
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[1] / 'k8s/grafana'
IMAGE = 'grafana/grafana:13.2.1@sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(base=BASE):
    docs = {p.name: yaml.safe_load(p.read_text(encoding='utf-8-sig')) for p in base.glob('*.yaml')}
    require(len(docs) == 6, 'Expected exactly six standalone Grafana resource manifests')
    for name, doc in docs.items():
        require(doc['kind'] in ('ServiceAccount','PersistentVolume','PersistentVolumeClaim','Deployment','Service','Pod'), f'Unexpected resource: {name}')
        if doc['kind'] != 'PersistentVolume':
            require(doc['metadata']['namespace'] == 'forge-observability', f'Wrong namespace: {name}')
    pv = docs['grafana-local-pv.yaml']['spec']
    require(pv['local']['path'] == '/mnt/signalforge-grafana/data', 'Grafana must have isolated storage')
    require(pv['persistentVolumeReclaimPolicy'] == 'Retain', 'Grafana PV must be retained')
    require(pv['accessModes'] == ['ReadWriteOnce'] and pv['capacity']['storage'] == '3Gi', 'Wrong storage sizing/access')
    require(pv['storageClassName'] == 'signalforge-local-nvme', 'Wrong StorageClass')
    require(pv['claimRef'] == {'name':'grafana-data','namespace':'forge-observability'}, 'PV not reserved')
    terms = pv['nodeAffinity']['required']['nodeSelectorTerms']
    require(terms == [{'matchExpressions':[{'key':'kubernetes.io/hostname','operator':'In','values':['forge-head']}]}], 'PV must require forge-head')
    pvc = docs['grafana-data-pvc.yaml']['spec']
    require(pvc['volumeName'] == 'grafana-local-nvme' and pvc['resources']['requests']['storage'] == '3Gi', 'Wrong PVC binding')
    require(pvc['accessModes'] == ['ReadWriteOnce'] and pvc['storageClassName'] == 'signalforge-local-nvme', 'Wrong PVC policy')
    service = docs['grafana-service.yaml']['spec']
    require(service['type'] == 'ClusterIP', 'External Grafana exposure prohibited')
    require(service['selector'] == {'app':'grafana'} and service['ports'] == [{'name':'http','port':3000,'targetPort':'http'}], 'Wrong Service target')
    require(not any(k in service for k in ('externalIPs','loadBalancerIP')), 'External Service address prohibited')
    require(docs['grafana-service-account.yaml']['automountServiceAccountToken'] is False, 'Service account token must be disabled')
    deployment = docs['grafana-deployment.yaml']['spec']
    require(deployment['replicas'] == 1 and deployment['strategy']['type'] == 'Recreate', 'Single writer required')
    spec = deployment['template']['spec']
    require(spec['serviceAccountName'] == 'grafana' and spec['automountServiceAccountToken'] is False, 'API token or account mismatch')
    require(not spec.get('hostNetwork') and not spec.get('hostPID') and not spec.get('hostIPC'), 'Host namespaces prohibited')
    require(spec['securityContext']['runAsNonRoot'] and spec['securityContext']['runAsUser'] == 472, 'Wrong runtime identity')
    require(spec['securityContext']['seccompProfile']['type'] == 'RuntimeDefault', 'Seccomp required')
    require(spec['tolerations'] == [{'key':'node-role.kubernetes.io/control-plane','operator':'Exists','effect':'NoSchedule'}], 'Overbroad tolerations')
    require(len(spec['containers']) == 1 and not spec.get('initContainers'), 'No additional containers approved')
    c = spec['containers'][0]
    require(c['image'] == IMAGE, 'Unverified Grafana image')
    require(c['securityContext'] == {'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}}, 'Container privilege policy mismatch')
    require(c['resources'] == {'requests':{'cpu':'100m','memory':'512Mi'},'limits':{'cpu':'1000m','memory':'1Gi'}}, 'Resource budget mismatch')
    require(c['ports'] == [{'name':'http','containerPort':3000}], 'Unexpected container/host ports')
    require(c['startupProbe']['httpGet']['path'] == '/api/health' and c['readinessProbe']['httpGet']['path'] == '/api/health', 'Health probes missing')
    require(c['livenessProbe']['tcpSocket']['port'] == 'http', 'TCP liveness required')
    env = {e['name']:e for e in c['env']}
    for key,field in [('GF_SECURITY_ADMIN_USER','admin-user'),('GF_SECURITY_ADMIN_PASSWORD','admin-password'),('GF_SECURITY_SECRET_KEY','secret-key')]:
        require(env[key].get('valueFrom') == {'secretKeyRef':{'name':'grafana-admin','key':field}}, 'Credentials must come from Secret references')
    volumes = {v['name']:v for v in spec['volumes']}
    require(volumes['data']['persistentVolumeClaim']['claimName'] == 'grafana-data', 'Wrong active PVC')
    require(not any('hostPath' in v for v in volumes.values()), 'hostPath prohibited')
    for mount in c['volumeMounts']:
        require('subPath' not in mount, 'Do not use subPath mounts for configuration')
        if mount['name'] not in ('data','tmp'):
            require(mount.get('readOnly') is True, 'Config mounts must be read-only')
    pre = docs['grafana-storage-preflight-pod.yaml']['spec']
    require(pre['automountServiceAccountToken'] is False and pre['restartPolicy'] == 'Never', 'Preflight policy mismatch')
    require(pre['containers'][0]['image'] == IMAGE and pre['volumes'][0]['persistentVolumeClaim']['claimName'] == 'grafana-data', 'Preflight must validate approved image/PVC')
    conf = configparser.ConfigParser(interpolation=None)
    conf.read(base/'config/grafana.ini')
    for section, option in [('auth.anonymous','enabled'),('users','allow_sign_up'),('unified_alerting','enabled'),('snapshots','enabled')]:
        require(conf.getboolean(section,option) is False, f'{section}.{option} must be disabled')
    require(conf.getboolean('plugins','preinstall_disabled') is True, 'Plugin auto-install must be disabled')
    require(conf['log']['mode'] == 'console', 'Use console logging')
    source = yaml.safe_load((base/'provisioning/datasources/prometheus.yaml').read_text())['datasources']
    require(len(source) == 1, 'Only one data source approved')
    require(source[0]['uid'] == 'signalforge-prometheus' and source[0]['type'] == 'prometheus', 'Wrong data source identity')
    require(source[0]['url'] == 'http://prometheus.forge-observability.svc.cluster.local:9090' and source[0]['access'] == 'proxy', 'Wrong Prometheus endpoint/access')
    require(source[0]['editable'] is False and source[0]['jsonData']['timeInterval'] == '30s', 'Data source contract mismatch')
    provider = yaml.safe_load((base/'provisioning/dashboards/signalforge.yaml').read_text())['providers'][0]
    require(provider['allowUiUpdates'] is False and provider['updateIntervalSeconds'] == 30, 'Provisioning policy mismatch')
    require(provider['options']['path'] == '/etc/grafana/dashboards', 'Wrong dashboard path')
    dashboards = [json.loads(p.read_text()) for p in sorted((base/'dashboards').glob('*.json'))]
    require({d['uid'] for d in dashboards} == {'signalforge-restaurant-overview','signalforge-scrape-diagnostics'}, 'Dashboard identity mismatch')
    for d in dashboards:
        require(len(d['panels']) == 6 and d['refresh'] == '30s', 'Dashboard scope/refresh mismatch')
        require(d['time'] == {'from':'now-30m','to':'now'}, 'Wrong default range')
        for p in d['panels']:
            require(p['datasource']['uid'] == 'signalforge-prometheus', 'Panel data source mismatch')
            for t in p['targets']:
                require('job="restaurant-api"' in t['expr'] and 'namespace="forge-restaurant"' in t['expr'], 'Unscoped PromQL')
                require('vector(0)' not in t['expr'], 'Missing data must not become a healthy zero')
                require('node_cpu' not in t['expr'] and 'kube_' not in t['expr'], 'Uncollected telemetry')
    for directory in ('config','provisioning/datasources','provisioning/dashboards','dashboards'):
        require(sum(p.stat().st_size for p in (base/directory).iterdir()) < 900_000, 'ConfigMap source exceeds safe size')
    print('OK: Grafana storage, exposure, privileges, provisioning and 12 panels')


if __name__ == '__main__':
    validate()
