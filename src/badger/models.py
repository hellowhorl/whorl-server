import pgtrigger
from django.db import models
from django.core.exceptions import ValidationError
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Badge(models.Model):
    """Canonical badge definitions."""
    badge_id = models.CharField(max_length=50, unique=True, default="BADGE_DEFAULT")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=255)
    total_steps = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.badge_id}: {self.name}"

    def clean(self):
        if not self.badge_id.isalnum():
            raise ValidationError("Badge ID must be alphanumeric")

    @staticmethod  # Changed from classmethod to staticmethod since we don't need cls
    def get_or_create_badge(name, category, steps=1, description=""):
        """Get existing badge or create a new one."""
        badge_id = f"{category.upper()}_{name.upper().replace(' ', '_')}"
        badge, created = Badge.objects.get_or_create(
            badge_id=badge_id,
            defaults={
                'name': name,
                'category': category,
                'total_steps': steps,
                'description': description
            }
        )
        return badge

class BadgeProgress(models.Model):
    """Tracks user progress towards badges."""
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    step_status = models.JSONField(default=dict)  # {'1': true, '2': false, ...}
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['badge', 'repository_name', 'student_username']
        indexes = [
            models.Index(fields=['student_username', 'repository_name']),
            models.Index(fields=['badge', 'completed'])
        ]

    def __str__(self):
        return f"{self.badge.name} - {self.student_username}"

    def initialize_steps(self):
        """Initialize step_status for all steps as false."""
        self.step_status = {str(i): False for i in range(1, self.badge.total_steps + 1)}
        self.save()

    def update_step(self, step_number: int, passed: bool):
        """Update a specific step's status."""
        if not isinstance(self.step_status, dict):
            self.step_status = {}
        
        self.step_status[str(step_number)] = passed
        self._check_completion()
        self.save()

    def _check_completion(self):
        """Check if all steps are complete."""
        if not self.step_status:
            self.completed = False
            return

        required_steps = range(1, self.badge.total_steps + 1)
        self.completed = all(
            self.step_status.get(str(step), False) 
            for step in required_steps
        )

@pgtrigger.register(
    pgtrigger.Trigger(
        name='update_check_status',
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
class GatorCheck(models.Model):
    """Records GatorGrader check results."""
    repository_name = models.CharField(max_length=255)
    student_username = models.CharField(max_length=255)
    workflow_run_id = models.CharField(max_length=255, unique=True)
    commit_hash = models.CharField(max_length=40)
    
    # Check results
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
                
            if not isinstance(check_results, list):
                check_results = [check_results]

            self.check_details = check_results
            self.total_checks = len(check_results)
            self.passed_checks = 0

            # Process each check
            for check in check_results:
                logger.debug(f"Processing check: {check}")  # Add debug logging
                
                if check.get('status', False):
                    self.passed_checks += 1
                
                # Process badges if check has any
                badges = check.get('badges', [])
                for badge_info in badges:
                    badge_name = badge_info.get('name')
                    step = badge_info.get('step', 1)
                    category = check.get('category', 'default')

                    # Skip if no badge name
                    if not badge_name:
                        continue

                    logger.debug(f"Processing badge: {badge_name}, category: {category}, step: {step}")  # Add debug logging

                    try:
                        # Get or create badge record
                        badge = Badge.get_or_create_badge(
                            name=badge_name,
                            category=category,
                            steps=max(step, 1)
                        )

                        # Get or create progress record
                        progress, created = BadgeProgress.objects.get_or_create(
                            badge=badge,
                            repository_name=self.repository_name,
                            student_username=self.student_username
                        )

                        # Initialize steps if new record
                        if created:
                            progress.initialize_steps()

                        # Update step status
                        progress.update_step(step, check.get('status', False))
                        
                        logger.debug(f"Successfully processed badge {badge_name}")  # Add debug logging
                        
                    except Exception as e:
                        logger.error(f"Error processing badge {badge_name}: {str(e)}")
                        continue

            self.save()
            return True

        except Exception as e:
            logger.error(f"Error processing GatorGrader output: {str(e)}")
            return False

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
            'check_details': self.check_details
        }