from django.test import TestCase
from ..services import BadgeGenerator, GradeProcessor

class BadgeGeneratorTests(TestCase):
    def test_generate_badge_url(self):
        url = BadgeGenerator.generate_badge_url(
            'test-repo',
            5,
            10,
            'failed'
        )
        self.assertIn('test-repo', url)
        self.assertIn('critical', url)

class GradeProcessorTests(TestCase):
    def setUp(self):
        self.valid_output = {
            'checks': [
                {'name': 'test1', 'passed': True},
                {'name': 'test2', 'passed': False}
            ]
        }

    def test_process_grading_results(self):
        results = GradeProcessor.process_grading_results(self.valid_output)
        self.assertEqual(results['passed_checks'], 1)
        self.assertEqual(results['total_checks'], 2)
        self.assertEqual(results['status'], 'failed')
