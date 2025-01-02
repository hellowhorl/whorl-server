import pgtrigger
from django.db import models
from urllib.parse import quote

class Course(models.Model):
    """Course information for badge grouping."""
    name = models.CharField(max_length=255)
    course_id = models.CharField(max_length=50, unique=True)  # e.g., "CS200"
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_id}: {self.name}"

@pgtrigger.register(
    pgtrigger.Trigger(
        name='update_badge_status',
        level=pgtrigger.Row,
        operation=pgtrigger.Update | pgtrigger.Insert,
        when=pgtrigger.After,
        func="""
            BEGIN
                IF NEW.passed_checks = NEW.total_checks THEN
                    NEW.status := 'passed';
                ELSE
                    NEW.status := 'failed';
                END IF;
                RETURN NEW;
            END;
        """
    )
)
class GradeCheck(models.Model):
    """Stores grading results and badge status."""
    # Core fields
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    workflow_run_id = models.CharField(max_length=255, unique=True)
    commit_hash = models.CharField(max_length=40)
    
    # Course association
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    assignment_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Check results
    passed_checks = models.IntegerField(default=0)
    total_checks = models.IntegerField(default=0)
    check_details = models.JSONField(default=dict)
    
    # Badge status
    status = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'All checks passed'),
            ('failed', 'Some checks failed'),
            ('pending', 'Checks in progress')
        ],
        default='pending'
    )
    
    # Workflow metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['repository_name', 'student_username']),
            models.Index(fields=['workflow_run_id']),
            models.Index(fields=['course', 'student_username'])
        ]

    def __str__(self):
        return f"{self.repository_name} - {self.student_username} ({self.status})"

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
            'course': self.course.course_id if self.course else None,
            'assignment_name': self.assignment_name,
            'passed_checks': self.passed_checks,
            'total_checks': self.total_checks,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'badge_url': self.get_badge_url()
        }

    @staticmethod
    def process_gator_output(grading_output):
        """Process GatorGrader output into check results."""
        if not isinstance(grading_output, dict):
            raise ValueError("Grading output must be a dictionary")

        checks = grading_output.get('checks', [])
        passed_checks = sum(1 for check in checks if check.get('passed'))
        total_checks = len(checks)

        return {
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'details': checks
        }