import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import GradeCheck, Badge, BadgeProgress

logger = logging.getLogger(__name__)

class AddGradeCheckView(APIView):
    """Handle submission of new grading results."""
    
    def post(self, request, *args, **kwargs):
        try:
            data = {
                'repository_name': request.data.get('repository_name'),
                'student_username': request.data.get('student_username'),
                'workflow_run_id': request.data.get('workflow_run_id'),
                'commit_hash': request.data.get('commit_hash')
            }

            # Create GradeCheck instance
            grade_check = GradeCheck.objects.create(**data)
            
            # Process GatorGrader output
            gator_output = request.data.get('grading_output')
            if not grade_check.process_gator_output(gator_output):
                return HttpResponse(
                    json.dumps({'error': 'Failed to process GatorGrader output'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            return HttpResponse(
                json.dumps(grade_check.as_dict()),
                status=status.HTTP_201_CREATED,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error processing grade check: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class ListBadgesView(APIView):
    """List all badges for a student/repository."""
    
    def get(self, request, *args, **kwargs):
        try:
            username = request.GET.get('username')
            repository = request.GET.get('repository')

            if not username or not repository:
                return HttpResponse(
                    json.dumps({'error': 'Username and repository are required'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            # Get badge progress for student/repo
            progresses = BadgeProgress.objects.filter(
                student_username=username,
                repository_name=repository
            ).select_related('badge')

            badges = [{
                'name': progress.badge.name,
                'category': progress.badge.category,
                'description': progress.badge.description,
                'current_step': progress.current_step,
                'total_steps': progress.badge.total_steps,
                'completed': progress.completed,
                'updated_at': progress.updated_at.isoformat()
            } for progress in progresses]

            return HttpResponse(
                json.dumps(badges),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error listing badges: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class GetBadgeView(APIView):
    """Get badge for specific badge/student/repository combination."""
    
    def get(self, request, username, repository, badge_name, *args, **kwargs):
        try:
            progress = BadgeProgress.objects.select_related('badge').get(
                student_username=username,
                repository_name=repository,
                badge__name=badge_name
            )

            return HttpResponse(
                json.dumps({
                    'name': progress.badge.name,
                    'category': progress.badge.category,
                    'description': progress.badge.description,
                    'current_step': progress.current_step,
                    'total_steps': progress.badge.total_steps,
                    'completed': progress.completed,
                    'updated_at': progress.updated_at.isoformat()
                }),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except BadgeProgress.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'Badge progress not found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error getting badge: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )