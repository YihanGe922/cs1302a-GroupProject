import unittest
from datetime import date
from deadline_conflict_solver.cli import make_report, main, interactive_payload
from deadline_conflict_solver.data import parse_payload
from deadline_conflict_solver.models import Task
from deadline_conflict_solver.planner import make_plan
from deadline_conflict_solver.reschedule import suggest_extra_hours
from unittest.mock import patch
import io
from contextlib import redirect_stdout

class TestMerged(unittest.TestCase):
    def setUp(self):
        self.payload = {'start_date':'2026-11-14','daily_free_time':2,'buffer_ratio':0,
                        'assignments':[{'id':'A','name':'Test','deadline':'2026-11-14','estimated_hours':3}]}

    def test_conflict(self):
        report = make_report(self.payload)
        self.assertEqual(report['remaining_hours']['A'],1)
        self.assertEqual(len(report['conflicts']),1)

    def test_suggestion(self):
        report = make_report(self.payload)
        self.assertEqual(report['suggestion']['extra_hours_per_day'], 1)

    def test_weekday_capacity(self):
        payload = {'start_date':'2026-11-14','daily_free_time':{'saturday':2},
                   'assignments':[{'name':'Reading','deadline':'2026-11-14','estimated_hours':1}]}
        self.assertEqual(make_report(payload)['conflicts'], [])

    def test_dependency(self):
        p = {'start_date':'2026-11-14','daily_free_time':3,'buffer_ratio':0,
             'assignments':[{'id':'A','name':'A','estimated_hours':2,'deadline':'2026-11-14'},
                           {'id':'B','name':'B','estimated_hours':1,'deadline':'2026-11-14','depends_on':['A']}]}
        report = make_report(p)
        self.assertEqual([x['task_id'] for x in report['schedule']],['A','B'])

    def test_cycle_rejected(self):
        p = {'start_date':'2026-11-14','daily_free_time':3,
             'assignments':[{'id':'A','name':'A','estimated_hours':1,'deadline':'2026-11-14','depends_on':['B']},
                           {'id':'B','name':'B','estimated_hours':1,'deadline':'2026-11-14','depends_on':['A']}]}
        with self.assertRaises(ValueError):
            make_report(p)

    def test_interactive(self):
        answers = iter(['2026-11-14','2','1','Reading','2026-11-14','1','2','n'])
        p = interactive_payload(input_fn=lambda _:next(answers),output_fn=lambda _:None)
        self.assertEqual(make_report(p)['conflicts'], [])

    def test_interactive_command(self):
        answers = ['2026-11-15', '2', '1', 'Python Project', '2026-11-15', '3', '1', 'n']
        out = io.StringIO()
        # Supply the payload explicitly because the input function is injectable.
        p = interactive_payload(input_fn=lambda _: answers.pop(0), output_fn=lambda _: None)
        with patch('deadline_conflict_solver.cli.interactive_payload', return_value=p):
            with redirect_stdout(out):
                self.assertEqual(main([]), 0)
        self.assertIn('1.2h unfinished', out.getvalue())
        self.assertIn('Extra hours per day: 1.5', out.getvalue())

    def test_advanced_input(self):
        answers = iter([
            '2026-11-15', '2', '2',
            'Project', '2026-11-16', '2', '1',
            'Report', '2026-11-16', '1', '2',
            'y', 'y', '1', '2', '3', '4', '5', '6', '7',
            'y', '1', '2026-11-15', '4',
            'y', '', 'T1', '0', '2'
        ])
        p = interactive_payload(input_fn=lambda _: next(answers), output_fn=lambda _: None)
        self.assertEqual(p['daily_free_time']['sunday'], 7)
        self.assertEqual(p['date_overrides']['2026-11-15'], 4)
        self.assertEqual(p['assignments'][1]['depends_on'], ['T1'])
        self.assertEqual(p['buffer_ratio'], 0)
        self.assertEqual(p['max_extra_hours'], 2)
        report = make_report(p)
        self.assertEqual(report['conflicts'], [])
        self.assertEqual([x['task_id'] for x in report['schedule']], ['T1', 'T2'])

    def test_invalid_interactive_values(self):
        answers = iter(['bad-date', '2026-11-15', 'nan', 'inf', '-1', '25', '2', '1',
                        '', 'Project', '2026-11-14', '2026-11-15', '0', '3', '6', '1', 'n'])
        messages = []
        p = interactive_payload(input_fn=lambda _: next(answers), output_fn=messages.append)
        self.assertEqual(p['daily_free_time'], 2)
        self.assertEqual(p['assignments'][0]['estimated_hours'], 3)
        self.assertGreater(len(messages), 5)

    def test_extra_hours_respects_limit(self):
        p = dict(self.payload)
        p['assignments'] = [{'id': 'A', 'name': 'Test', 'deadline': '2026-11-14', 'estimated_hours': 3.5}]
        start, tasks, cap, buffer = parse_payload(p)
        self.assertIsNone(suggest_extra_hours(tasks, cap, start, max_extra=1.3, buffer_ratio=buffer))

    def test_invalid_dates(self):
        p = dict(self.payload)
        p['start_date']='not-date'
        with self.assertRaises(ValueError):
            make_report(p)

    def test_invalid_negative_capacity(self):
        p = dict(self.payload)
        p['daily_free_time']=-3
        with self.assertRaises(ValueError):
            make_report(p)

if __name__ == '__main__': unittest.main()
