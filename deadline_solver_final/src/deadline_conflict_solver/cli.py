"""Command-line and interactive interface for Deadline Conflict Solver."""
from __future__ import annotations
import argparse
from datetime import date
import sys
from math import isfinite
from .data import parse_payload
from .planner import make_plan
from .conflicts import analyze_conflicts
from .reschedule import suggest_extra_hours


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
    """Collect basic and optional advanced settings as a Python dictionary."""
    output_fn('Deadline Conflict Solver — Interactive Mode')
    output_fn('Answer the questions to create your study plan.')

    def ask_number(label, minimum=0, maximum=None, integer=False, default=None):
        while True:
            raw = input_fn(label).strip()
            if not raw and default is not None:
                return default
            try:
                value = int(raw) if integer else float(raw)
                if not isfinite(value) or value < minimum:
                    raise ValueError()
                if maximum is not None and value > maximum:
                    raise ValueError()
                return value
            except ValueError:
                upper = '' if maximum is None else f' and <= {maximum}'
                output_fn(f'Please enter a finite number >= {minimum}{upper}.')

    def ask_date(label, minimum=None, maximum=None):
        while True:
            raw = input_fn(label).strip()
            try:
                value = date.fromisoformat(raw)
                if minimum is not None and value < minimum:
                    output_fn(f'Date must be on or after {minimum}.')
                    continue
                if maximum is not None and value > maximum:
                    output_fn(f'Date must be on or before {maximum}.')
                    continue
                return raw
            except ValueError:
                output_fn('Please use YYYY-MM-DD, e.g. 2026-11-22.')

    def ask_yes(label):
        while True:
            raw = input_fn(label).strip().lower()
            if raw in ('', 'n', 'no'):
                return False
            if raw in ('y', 'yes'):
                return True
            output_fn('Please enter y or n (Enter means no).')

    start = ask_date('Start date (YYYY-MM-DD): ')
    start_day = date.fromisoformat(start)
    capacity = ask_number('Study hours available each day: ', maximum=24)
    count = ask_number('Number of assignments: ', 1, integer=True)
    assignments = []
    for i in range(count):
        output_fn(f'\nAssignment {i + 1} (T{i + 1})')
        name = ''
        while not name:
            name = input_fn('Name: ').strip()
            if not name:
                output_fn('Name must not be blank.')
        deadline = ask_date('Deadline (YYYY-MM-DD): ', minimum=start_day)
        hours = ask_number('Estimated hours (> 0): ', 0.01)
        priority = ask_number('Priority (1 highest to 5 lowest): ', 1, 5, integer=True)
        assignments.append({'id': f'T{i + 1}', 'name': name, 'deadline': deadline,
                            'estimated_hours': hours, 'priority': priority})

    payload = {'start_date': start, 'daily_free_time': capacity, 'assignments': assignments}
    if not ask_yes('Configure advanced settings? [y/N]: '):
        return payload

    if ask_yes('Set different available hours for each weekday? [y/N]: '):
        day_names = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
        payload['daily_free_time'] = {
            day: ask_number(f'{day.title()} hours [Enter = {capacity:g}]: ', maximum=24, default=capacity)
            for day in day_names
        }

    if ask_yes('Override available hours for specific dates? [y/N]: '):
        end_day = max(date.fromisoformat(row['deadline']) for row in assignments)
        overrides = {}
        number = ask_number('Number of date overrides: ', 1, integer=True)
        for _ in range(number):
            day = ask_date('Override date (YYYY-MM-DD): ', minimum=start_day, maximum=end_day)
            overrides[day] = ask_number('Available hours on this date: ', maximum=24)
        payload['date_overrides'] = overrides

    if ask_yes('Add task dependencies? [y/N]: '):
        output_fn('Enter prerequisite task IDs separated by commas, or Enter for none.')
        for row in assignments:
            output_fn(f"{row['id']}: {row['name']}")
        ids = {row['id'] for row in assignments}
        while True:
            for row in assignments:
                while True:
                    raw = input_fn(f"Prerequisites for {row['id']} ({row['name']}): ").strip()
                    deps = list(dict.fromkeys(part.strip().upper() for part in raw.split(',') if part.strip()))
                    if row['id'] in deps or any(dep not in ids for dep in deps):
                        output_fn('Use listed task IDs and do not include the task itself.')
                        continue
                    row['depends_on'] = deps
                    break
            try:
                from .planner import validate_tasks
                _, tasks, _, _ = parse_payload(payload)
                validate_tasks(tasks, start_day)
                break
            except ValueError as exc:
                output_fn(f'Invalid dependencies: {exc}. Please enter them again.')

    percent = ask_number('Buffer percentage (0 to less than 100) [Enter = 10]: ', maximum=100, default=10)
    while percent >= 100:
        output_fn('Buffer must be less than 100%.')
        percent = ask_number('Buffer percentage [Enter = 10]: ', maximum=100, default=10)
    payload['buffer_ratio'] = percent / 100
    payload['max_extra_hours'] = ask_number('Maximum extra study hours per day to try [Enter = 3]: ', maximum=24, default=3)
    return payload


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
    parser = argparse.ArgumentParser(description='Plan assignments through interactive questions.')
    parser.parse_args(argv)
    try:
        payload = interactive_payload()
        report = make_report(payload)
    except (EOFError, KeyboardInterrupt):
        print('\nInput cancelled.', file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(format_report(report))
    return 0


if __name__ == '__main__':
    sys.exit(main())
