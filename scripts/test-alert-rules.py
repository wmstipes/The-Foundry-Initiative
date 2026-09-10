"""Run local offline checks with an existing, exactly versioned promtool binary."""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--promtool', default='promtool', help='Path to promtool or promtool.exe')
    args = parser.parse_args()
    try:
        version = subprocess.run([args.promtool, '--version'], check=True,
                                 capture_output=True, text=True)
        version_text = version.stdout + version.stderr
        if not re.search(r'\bversion 3\.13\.2(?:\s|,|$)', version_text):
            raise ValueError(f'Expected promtool 3.13.2; got {version_text.strip()}')
        print(version_text.strip(), flush=True)
        subprocess.run([sys.executable, str(ROOT/'scripts/validate-alert-rules.py')], check=True)
        subprocess.run([args.promtool, 'check', 'rules',
                        str(ROOT/'monitoring/alerts/restaurant-scrape.rules.yaml')], check=True)
        with tempfile.TemporaryDirectory(prefix='signalforge-alert-tests-') as tmp:
            suite = Path(tmp)/'alerts.test.yaml'
            subprocess.run([sys.executable, str(ROOT/'scripts/export-alert-rule-tests.py'),
                            str(suite)], check=True)
            subprocess.run([args.promtool, 'test', 'rules', str(suite)], check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: offline alert validation did not complete: {exc}', file=sys.stderr)
        return 1
    print('PASS: offline alert rules only; nothing deployed or activated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
