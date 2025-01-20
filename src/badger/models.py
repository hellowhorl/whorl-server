# whorl-server/src/badger/models.py
import pgtrigger
from django.db import models
from urllib.parse import quote
import json

class Badge(models.Model):
    """Model for badge definitions."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    total_steps = models.IntegerField(default=1)
    category = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class BadgeProgress(models.Model):
    """Model for tracking badge progress."""
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    current_step = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['badge', 'repository_name', 'student_username']

    def __str__(self):
        return f"{self.badge.name} - {self.student_username} (Step {self.current_step})"

class GradeCheck(models.Model):
    """Stores grading results and processes GatorGrader output."""
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    workflow_run_id = models.CharField(max_length=255, unique=True)
    commit_hash = models.CharField(max_length=40)
    
    # GatorGrader results
    check_details = models.JSONField(default=dict)
    passed_checks = models.IntegerField(default=0)
    total_checks = models.IntegerField(default=0)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'All checks passed'),
            ('failed', 'Some checks failed'),
            ('pending', 'Checks in progress')
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def process_gator_output(self, gator_output):
        """Process GatorGrader output and update badge progress."""
        try:
            # Parse JSON if string
            if isinstance(gator_output, str):
                check_results = json.loads(gator_output)
            else:
                check_results = gator_output

            total_checks = len(check_results)
            passed_checks = sum(1 for check in check_results if check.get('status', False))

            # Store check results
            self.check_details = check_results
            self.passed_checks = passed_checks
            self.total_checks = total_checks
            self.save()

            # Process badges
            for check in check_results:
                badges = check.get('badges', [])
                for badge_info in badges:
                    badge_name = badge_info.get('name')
                    step = badge_info.get('step', 1)
                    category = check.get('category', 'default')

                    # Get or create badge
                    badge, _ = Badge.objects.get_or_create(
                        name=badge_name,
                        defaults={
                            'category': category,
                            'description': check.get('description', ''),
                        }
                    )

                    # Update badge progress if check passed
                    if check.get('status', False):
                        progress, _ = BadgeProgress.objects.get_or_create(
                            badge=badge,
                            repository_name=self.repository_name,
                            student_username=self.student_username,
                        )
                        progress.current_step = max(progress.current_step, step)
                        if progress.current_step >= badge.total_steps:
                            progress.completed = True
                        progress.save()

            return True
        except Exception as e:
            print(f"Error processing GatorGrader output: {str(e)}")
            return False

    def get_badge_url(self):
        """Generate badge URL based on check results."""
        repo_name = quote(self.repository_name)
        color = 'success' if self.status == 'passed' else 'critical'
        percentage = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        return f"https://img.shields.io/badge/{repo_name}-{self.passed_checks}%2F{self.total_checks}%20({percentage:.0f}%25)-{color}"

    def as_dict(self):
        """Convert instance to dictionary for API responses."""
        return {
            'id': self.id,
            'repository_name': self.repository_name,
            'student_username': self.student_username,
            'workflow_run_id': self.workflow_run_id,
            'commit_hash': self.commit_hash,
            'passed_checks': self.passed_checks,
            'total_checks': self.total_checks,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'badge_url': self.get_badge_url()
        }