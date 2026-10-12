"""Summarize one chapter from the explicitly selected current-thread log."""
import argparse
import csv
import datetime as dt
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('log', type=Path)
p.add_argument('chapter')
p.add_argument('start', help='ISO timestamp including timezone')
p.add_argument('end', help='ISO timestamp including timezone')
p.add_argument('csv', type=Path)
a = p.parse_args()
parse = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
start, end = parse(a.start), parse(a.end)
if start.tzinfo is None or end.tzinfo is None or end <= start:
    p.error('start/end must include timezone and end must be after start')
before, after, calls = None, None, 0
def events(path):
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)

for e in events(a.log):
    when, payload = parse(e['timestamp']), e.get('payload', {})
    if e['type'] == 'event_msg' and payload.get('type') == 'token_count':
        usage = (payload.get('info') or {}).get('total_token_usage')
        if usage and when <= start:
            before = usage
        if usage and when <= end:
            after = usage
    if start < when <= end and e['type'] == 'response_item' and payload.get('type') == 'function_call':
        calls += 1
if before is None or after is None:
    p.error('token counters unavailable at requested boundaries; CSV was not changed')
inp = after['input_tokens'] - before['input_tokens']
cached = after['cached_input_tokens'] - before['cached_input_tokens']
out = after['output_tokens'] - before['output_tokens']
if min(inp, cached, out, inp-cached) < 0:
    p.error('token counters reset or are inconsistent; CSV was not changed')
row = dict(chapter=a.chapter, input_tokens=inp, cached_input_tokens=cached,
           uncached_input_tokens=inp-cached, output_tokens=out,
           total_tokens=inp+out, tool_calls=calls)
rows = []
if a.csv.exists():
    with a.csv.open(encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['chapter'] != a.chapter]
rows.append(row)
a.csv.parent.mkdir(parents=True, exist_ok=True)
with a.csv.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=row.keys())
    w.writeheader()
    w.writerows(rows)
print(json.dumps(row, ensure_ascii=False))
