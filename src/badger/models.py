import pgtrigger
from django.db import models

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
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    workflow_run_id = models.CharField(max_length=255, unique=True)
    commit_hash = models.CharField(max_length=40)
    
    passed_checks = models.IntegerField(default=0)
    total_checks = models.IntegerField(default=0)
    check_details = models.JSONField(default=dict)
    
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

    class Meta:
        indexes = [
            models.Index(fields=['repository_name', 'student_username']),
            models.Index(fields=['workflow_run_id'])
        ]