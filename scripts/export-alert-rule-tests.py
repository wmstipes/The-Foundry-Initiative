"""Generate offline promtool cases from explicitly specified expected states.

Expected states and annotations are independent of the rule file. A broken rule
must fail fixtures, not rewrite their expectations. Values are spaced 30s apart.
"""
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RULE_FILE = ROOT / 'monitoring/alerts/restaurant-scrape.rules.yaml'
WARNING = 'RestaurantScrapeCoverageDegraded'
CRITICAL = 'RestaurantNoHealthyScrapeTargets'
RUNBOOK = ('https://github.com/wmstipes/The-Foundry-Initiative/blob/main/'
           'docs/runbooks/restaurant-api-operator-runbook.md')


def target(pod, values, job='restaurant-api', namespace='forge-restaurant'):
    return {'series': f'up{{job="{job}",namespace="{namespace}",pod="{pod}"}}',
            'values': values}


def targets(*values):
    return [target(f'pod-{i}', v) for i, v in enumerate(values)]


def labels(name):
    return {'job': 'restaurant-api', 'namespace': 'forge-restaurant',
            'severity': 'warning' if name == WARNING else 'critical'}


def annotations(name, healthy):
    if name == WARNING:
        return {'summary': 'Restaurant API scrape coverage below three targets',
                'description': f'{healthy} healthy scrape targets; expected 3. Investigate scrape errors, discovery and rollout context. This does not establish user-facing availability.',
                'runbook_url': RUNBOOK}
    return {'summary': 'No healthy Restaurant API scrape targets observed',
            'description': 'All scoped scrapes are failing or scoped target series are absent. Inspect discovery and scrape errors; separately verify user-facing access. The evaluator cannot detect its own outage.',
            'runbook_url': RUNBOOK}


def case(name, inputs, checkpoints):
    """Checkpoint: (time, warning state, critical state, warning count).

    State is None, pending, or firing. Check BOTH rules and the full ALERTS
    vector at every checkpoint, catching unexpected overlaps/label leakage.
    """
    result = {'name': name, 'interval': '30s', 'input_series': inputs,
              'alert_rule_test': [], 'promql_expr_test': []}
    for time, warning_state, critical_state, healthy in checkpoints:
        samples = []
        for alert, state in [(WARNING, warning_state), (CRITICAL, critical_state)]:
            expected = []
            if state == 'firing':
                expected = [{'exp_labels': labels(alert),
                             'exp_annotations': annotations(alert, healthy)}]
            result['alert_rule_test'].append(
                {'eval_time': time, 'alertname': alert, 'exp_alerts': expected})
            if state is not None:
                fields = {'alertname': alert, 'alertstate': state, **labels(alert)}
                label_text = ','.join(f'{k}="{v}"' for k, v in sorted(fields.items()))
                samples.append({'labels': 'ALERTS{' + label_text + '}', 'value': 1})
        result['promql_expr_test'].append(
            {'expr': 'ALERTS', 'eval_time': time, 'exp_samples': samples})
    return result


def build_suite(rule_file=RULE_FILE):
    # xN means N additional samples: 1+0x20 spans t=0 through t=10m.
    tests = []
    tests.append(case('healthy and idle application', targets(*(['1+0x20'] * 3)),
                      [('0s', None, None, 0), ('10m', None, None, 0)]))
    for count in (1, 2):
        tests.append(case(f'{count} healthy targets: warning boundary',
                          targets(*(['1+0x20'] * count + ['0+0x20'] * (3-count))),
                          [('0s', 'pending', None, count),
                           ('4m30s', 'pending', None, count),
                           ('5m', 'firing', None, count),
                           ('10m', 'firing', None, count)]))
    for name, inputs in [('all discovered down', targets(*(['0+0x20'] * 3))),
                         ('absent at startup', [])]:
        tests.append(case(name, inputs,
                          [('0s', None, 'pending', 0),
                           ('1m30s', None, 'pending', 0),
                           ('2m', None, 'firing', 0),
                           ('10m', None, 'firing', 0)]))
    tests.append(case('all down becomes stale: critical timer continuity',
                      targets(*(['0+0x1 stale'] * 3)),
                      [('30s', None, 'pending', 0), ('1m', None, 'pending', 0),
                       ('2m', None, 'firing', 0), ('5m', None, 'firing', 0)]))
    tests.append(case('healthy becomes explicitly stale at 1m',
                      targets(*(['1+0x1 stale'] * 3)),
                      [('30s', None, None, 0), ('1m', None, 'pending', 0),
                       ('2m30s', None, 'pending', 0), ('3m', None, 'firing', 0)]))
    # No stale marker: last sample is t=0. Bracket the default five-minute
    # lookback; do not conflate missing samples with immediate stale markers.
    tests.append(case('missing samples wait for lookback expiry',
                      targets(*(['1 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _'] * 3)),
                      [('4m30s', None, None, 0), ('5m30s', None, 'pending', 0),
                       ('6m30s', None, 'pending', 0), ('7m30s', None, 'firing', 0)]))
    tests.append(case('short partial deficit recovers before warning delay',
                      targets('1+0x20', '1+0x20', '0+0x8 1+0x11'),
                      [('4m', 'pending', None, 2), ('4m30s', None, None, 0),
                       ('5m', None, None, 0), ('10m', None, None, 0)]))
    tests.append(case('short total failure recovers before critical delay',
                      targets(*(['0+0x2 1+0x17'] * 3)),
                      [('1m', None, 'pending', 0), ('1m30s', None, None, 0),
                       ('2m', None, None, 0)]))
    tests.append(case('count changes without resetting warning identity',
                      targets('1+0x20', '0+0x3 1+0x6 0+0x9', '0+0x20'),
                      [('1m30s', 'pending', None, 1), ('2m', 'pending', None, 2),
                       ('4m30s', 'pending', None, 2), ('5m', 'firing', None, 2),
                       ('5m30s', 'firing', None, 1)]))
    tests.append(case('warning escalates then partially recovers: independent timers',
                      targets('1+0x11 0+0x5 1+0x12',
                              '1+0x11 0+0x5 1+0x12', '0+0x30'),
                      [('5m', 'firing', None, 2), ('6m', None, 'pending', 0),
                       ('7m30s', None, 'pending', 0), ('8m', None, 'firing', 0),
                       ('9m', 'pending', None, 2), ('13m30s', 'pending', None, 2),
                       ('14m', 'firing', None, 2)]))
    tests.append(case('firing warning clears on full recovery',
                      targets('1+0x20', '1+0x20', '0+0x11 1+0x8'),
                      [('5m30s', 'firing', None, 2), ('6m', None, None, 0)]))
    tests.append(case('firing critical clears on full recovery',
                      targets(*(['0+0x5 1+0x14'] * 3)),
                      [('2m30s', None, 'firing', 0), ('3m', None, None, 0)]))
    tests.append(case('extra rollout target: four healthy',
                      targets(*(['1+0x20'] * 4)), [('10m', None, None, 0)]))
    tests.append(case('three healthy plus a failed rollout target: diagnostic only',
                      targets('1+0x20', '1+0x20', '1+0x20', '0+0x20'),
                      [('10m', None, None, 0)]))
    unrelated = [target('other-job', '1+0x20', job='other'),
                 target('other-namespace', '1+0x20', namespace='other')]
    tests.append(case('unrelated series cannot mask scoped absence', unrelated,
                      [('1m30s', None, 'pending', 0), ('2m', None, 'firing', 0)]))
    tests.append(case('unrelated series cannot inflate partial coverage',
                      targets('1+0x20', '0+0x20', '0+0x20') + unrelated,
                      [('5m', 'firing', None, 1)]))
    tests.append(case('pod replacement preserves service-level warning timer',
                      [target('old', '1+0x3 stale'), target('new', '_ _ _ _ 1+0x16'),
                       target('second', '1+0x20'), target('failed', '0+0x20')],
                      [('1m30s', 'pending', None, 2), ('2m', 'pending', None, 2),
                       ('5m', 'firing', None, 2)]))
    return {'rule_files': [str(Path(rule_file).resolve())],
            'evaluation_interval': '30s', 'tests': tests}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(yaml.safe_dump(build_suite(), sort_keys=False), encoding='utf-8')
    print(f'Wrote 19 offline scenarios to {args.output}')


if __name__ == '__main__':
    main()
