"""Static scope guardrails. This is not a PromQL parser or promtool substitute."""
import configparser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = 'up{job="restaurant-api",namespace="forge-restaurant"}'
EXPECTED = {
    'RestaurantScrapeCoverageDegraded': (
        f'(sum({SELECTOR}) > 0) and (sum({SELECTOR}) < 3)', '5m', 'warning'),
    'RestaurantNoHealthyScrapeTargets': (
        f'(sum({SELECTOR}) == 0) or absent(sum({SELECTOR}))', '2m', 'critical'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compact(expression):
    return ''.join(expression.split())


def validate(root=ROOT):
    directory = root/'monitoring/alerts'
    require({p.name for p in directory.glob('*.yaml')} == {'restaurant-scrape.rules.yaml'},
            'Exactly one offline rule file is allowed')
    doc = yaml.safe_load((directory/'restaurant-scrape.rules.yaml').read_text(encoding='utf-8-sig'))
    require(set(doc) == {'groups'} and len(doc['groups']) == 1, 'Exactly one rule group is required')
    group = doc['groups'][0]
    require(set(group) == {'name', 'interval', 'rules'}, 'Unexpected rule group settings')
    require(group['name'] == 'signalforge-restaurant-scrape' and group['interval'] == '30s',
            'Group identity and evaluation interval must remain fixed')
    rules = group['rules']
    require(len(rules) == 2 and {r.get('alert') for r in rules} == set(EXPECTED),
            'Only the two accepted alert identities are allowed')
    for rule in rules:
        require(set(rule) == {'alert', 'expr', 'for', 'labels', 'annotations'},
                'Unexpected rule settings; no recording rules or keep_firing_for')
        expression, delay, severity = EXPECTED[rule['alert']]
        require(compact(rule['expr']) == compact(expression), 'Expression differs from accepted design')
        require(rule['for'] == delay, 'Provisional delay changed without design review')
        require(rule['labels'] == {'job': 'restaurant-api', 'namespace': 'forge-restaurant',
                                  'severity': severity}, 'Stable static service labels required')
        annotations = rule['annotations']
        require(set(annotations) == {'summary', 'description', 'runbook_url'}
                and all(isinstance(v, str) and v.strip() for v in annotations.values()),
                'Summary, description and runbook annotations required')
        require(annotations['runbook_url'] == (
            'https://github.com/wmstipes/The-Foundry-Initiative/blob/main/'
            'docs/runbooks/restaurant-api-operator-runbook.md'), 'Unexpected runbook link')
        if severity == 'critical':
            require('$value' not in annotations['description'],
                    'Critical expression value is not a healthy-target count')
    # The activation candidate embeds the canonical rules in the already-mounted
    # ConfigMap. No receiver or other alerting subsystem is approved.
    manifest = yaml.safe_load((root/'k8s/prometheus/prometheus-config.yaml').read_text(encoding='utf-8-sig'))
    data = manifest.get('data', {})
    require(set(data) == {'prometheus.yml', 'restaurant-scrape.rules.yaml'},
            'Prometheus ConfigMap must contain only the server config and accepted rules')
    config = yaml.safe_load(data['prometheus.yml'])
    require(config.get('rule_files') == ['/etc/prometheus/restaurant-scrape.rules.yaml'],
            'Prometheus must load only the accepted embedded rule file')
    require('alerting' not in config, 'Notification receivers and Alertmanager remain prohibited')
    require(config['global']['evaluation_interval'] == '30s', 'Evaluator interval drift')
    embedded = yaml.safe_load(data['restaurant-scrape.rules.yaml'])
    require(embedded == doc, 'Embedded rules must match the canonical offline-validated rules')
    grafana = configparser.ConfigParser(interpolation=None)
    grafana.read(root/'k8s/grafana/config/grafana.ini')
    require(not grafana.getboolean('unified_alerting', 'enabled'),
            'Grafana alerting must stay disabled')
    print('PASS: activation candidate matches the accepted rules; no receiver configuration present.')


if __name__ == '__main__':
    validate()
