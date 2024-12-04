from django.test import TestCase
from django.db.utils import IntegrityError
from ..models import GradeCheck

class GradeCheckModelTests(TestCase):
    def setUp(self):
        self.valid_data = {
            'repository_name': 'test-repo',
            'student_username': 'test-student',
            'workflow_run_id': 'test-workflow-1',
            'commit_hash': 'abcdef123456',
            'passed_checks': 5,
            'total_checks': 10,
            'status': 'failed'
        }

    def test_create_grade_check(self):
        grade_check = GradeCheck.objects.create(**self.valid_data)
        self.assertEqual(grade_check.repository_name, 'test-repo')
        self.assertEqual(grade_check.passed_checks, 5)
        self.assertEqual(grade_check.status, 'failed')

    def test_unique_workflow_run_id(self):
        GradeCheck.objects.create(**self.valid_data)
        with self.assertRaises(IntegrityError):
            GradeCheck.objects.create(**self.valid_data)