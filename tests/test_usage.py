import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/chaoxing-course-workflow/scripts/chapter_usage.py'


class UsageTests(unittest.TestCase):
    def run_case(self, invalid=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log, report = root / 'session.jsonl', root / 'usage.csv'
            def counter(time, inp, cached, out):
                return dict(timestamp=f'2026-01-01T10:{time}:00Z', type='event_msg', payload=dict(type='token_count', info=dict(total_token_usage=dict(input_tokens=inp, cached_input_tokens=cached, output_tokens=out))))
            data = [counter('00', 100, 80, 10), dict(timestamp='2026-01-01T10:02:00Z', type='response_item', payload=dict(type='function_call')), counter('04', 90 if invalid else 180, 100, 30)]
            log.write_text('\n'.join(map(json.dumps, data)), encoding='utf-8')
            cmd = [sys.executable, str(SCRIPT), str(log), '2.2', '2026-01-01T10:01:00Z', '2026-01-01T10:05:00Z', str(report)]
            if invalid:
                report.write_bytes(b'keep existing report')
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report.read_bytes(), b'keep existing report')
                return
            for _ in range(2):
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            with report.open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual({k: int(rows[0][k]) for k in ('input_tokens', 'cached_input_tokens', 'uncached_input_tokens', 'output_tokens', 'total_tokens', 'tool_calls')}, dict(input_tokens=80, cached_input_tokens=20, uncached_input_tokens=60, output_tokens=20, total_tokens=100, tool_calls=1))

    def test_measurement_and_replacement(self):
        self.run_case()

    def test_reset_preserves_report(self):
        self.run_case(invalid=True)


if __name__ == '__main__':
    unittest.main()
