"""Command-line and interactive interface for Deadline Conflict Solver."""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
from datetime import date
import json
import sys
from .data import read_json, parse_payload
from .planner import make_plan
from .conflicts import analyze_conflicts
from .reschedule import suggest_extra_hours
from .io_utils import format_plan


def make_report(payload):
    start, tasks, capacities, buffer_ratio = parse_payload(payload)
    original = make_plan(tasks, capacities, start, buffer_ratio)
    conflicts = analyze_conflicts(tasks, original)
    max_extra = float(payload.get('max_extra_hours', 3))
    suggestion = suggest_extra_hours(tasks, capacities, start, max_extra=max_extra, buffer_ratio=buffer_ratio)
    return {
        'start_date': start.isoformat(),
        'schedule': [{'date': b.day.isoformat(), 'task_id': b.task_id, 'hours': round(b.hours, 2)} for b in original.blocks],
        'remaining_hours': {k: round(v, 2) for k, v in original.remaining.items()},
        'conflicts': conflicts,
        'suggestion': None if suggestion is None else {
            'extra_hours_per_day': suggestion[0],
            'schedule': [{'date': b.day.isoformat(), 'task_id': b.task_id, 'hours': round(b.hours, 2)} for b in suggestion[1].blocks]
        }
    }


def interactive_payload(input_fn=input, output_fn=print):
    output_fn('Deadline Conflict Solver — Interactive Mode')
    output_fn('You do not need to write any JSON.')
    def ask_number(label, min_value=0, integer=False):
        while True:
            try:
                raw = input_fn(label).strip()
                val = int(raw) if integer else float(raw)
                if val < min_value:
                    raise ValueError()
                return val
            except ValueError:
                output_fn(f'Please enter a number >= {min_value}.')
    def ask_date(label):
        while True:
            raw = input_fn(label).strip()
            try:
                date.fromisoformat(raw)
                return raw
            except ValueError:
                output_fn('Please use YYYY-MM-DD, e.g. 2026-11-22.')
    start = ask_date('Start date (YYYY-MM-DD): ')
    capacity = ask_number('Study hours available each day: ', 0)
    count = ask_number('Number of assignments: ', 1, integer=True)
    assignments = []
    for i in range(count):
        output_fn(f'\nAssignment {i+1}')
        name = ''
        while not name:
            name = input_fn('Name: ').strip()
        deadline = ask_date('Deadline (YYYY-MM-DD): ')
        hours = ask_number('Estimated hours (> 0): ', 0.01)
        priority = ask_number('Priority (1 highest to 5 lowest): ', 1, integer=True)
        while priority > 5:
            output_fn('Priority must be 1–5.')
            priority = ask_number('Priority (1–5): ', 1, integer=True)
        assignments.append({'id':f'T{i+1}','name':name,'deadline':deadline,
                            'estimated_hours':hours,'priority':priority})
    return {'start_date':start,'daily_free_time':capacity,'assignments':assignments}


def format_report(report):
    lines = ['INITIAL PLAN']
    if report['schedule']:
        for item in report['schedule']:
            lines.append(f"{item['date']}: {item['task_id']} - {item['hours']:g}h")
    else:
        lines.append('(no work scheduled)')
    lines.append('\nCONFLICT ANALYSIS')
    if report['conflicts']:
        for x in report['conflicts']:
            lines.append(f"{x['name']}: {x['hours_short']:g}h unfinished by {x['deadline']}")
    else:
        lines.append('None')
    lines.append('\nWHAT-IF: ADD EXTRA HOURS PER DAY')
    if report['suggestion'] is None:
        lines.append('No feasible schedule within the tested extra hours.')
    else:
        lines.append(f"Extra hours per day: {report['suggestion']['extra_hours_per_day']:g}")
        for item in report['suggestion']['schedule']:
            lines.append(f"{item['date']}: {item['task_id']} - {item['hours']:g}h")
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Plan assignments within daily free time and deadlines.')
    parser.add_argument('input', nargs='?', help='Path to a homework JSON file')
    parser.add_argument('--interactive', action='store_true', help='Enter assignments by answering prompts (no JSON needed)')
    parser.add_argument('--json', action='store_true', help='Print results as JSON')
    args = parser.parse_args(argv)
    if not args.interactive and not args.input:
        parser.error('Provide an input JSON file or use --interactive')
    if args.interactive and args.input:
        parser.error('Use either input JSON or --interactive, not both')
    try:
        payload = interactive_payload(output_fn=lambda s: print(s, file=sys.stderr)) if args.interactive else read_json(args.input)
        report = make_report(payload)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2) if args.json else format_report(report))
    return 0

if __name__ == '__main__':
    sys.exit(main())
