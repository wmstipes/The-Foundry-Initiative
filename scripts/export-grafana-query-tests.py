"""Emit a promtool fixture validating every panel expression plus ratio edge cases."""
import json
import sys
from pathlib import Path
import yaml

base = Path(__file__).resolve().parents[1] / 'k8s/grafana/dashboards'
dashboards = [json.loads(p.read_text()) for p in base.glob('*.json')]
queries = [t['expr'] for d in dashboards for p in d['panels'] for t in p['targets']]
error = next(p['targets'][0]['expr'] for d in dashboards for p in d['panels'] if p['id'] == 3)
labels = 'job="restaurant-api",namespace="forge-restaurant",traffic="application",method="GET",path="/menu",pod="fixture"'
def series(status,values):
    return {'series':'restaurant_api_requests_total{'+labels+',status="'+status+'"}', 'values':values}
def sample(value):
    return [{'labels':'{}','value':value}]
tests=[{'interval':'30s','input_series':[], 'promql_expr_test':[{'expr':q,'eval_time':'5m','exp_samples':[]} for q in queries]}]
for inputs,expected in [
    ([series('200','0+300x10')],sample(0)),
    ([series('200','0+270x10'),series('500','0+30x10')],sample(10)),
    ([series('200','0+0x10')],[]),
    ([series('500','0+0.003x10')],sample(100)),
]:
    tests.append({'interval':'30s','input_series':inputs,'promql_expr_test':[{'expr':error,'eval_time':'5m','exp_samples':expected}]})
Path(sys.argv[1]).write_text(yaml.safe_dump({'evaluation_interval':'30s','tests':tests},sort_keys=False),encoding='utf-8')
