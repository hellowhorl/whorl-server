from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from ..models import GradeCheck

class GradeCheckViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.submit_url = reverse('badger:submit-grade')
        self.list_url = reverse('badger:list-grades')
        
        self.valid_payload = {
            'repository_name': 'test-repo',
            'student_username': 'test-student',
            'workflow_run_id': 'test-workflow-1',
            'commit_hash': 'abcdef123456',
            'grading_output': {
                'checks': [
                    {'name': 'test1', 'passed': True},
                    {'name': 'test2', 'passed': True}
                ]
            }
        }

    def test_submit_grade_check(self):
        response = self.client.post(
            self.submit_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GradeCheck.objects.count(), 1)

    def test_list_grade_checks(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)