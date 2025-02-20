import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import Badge, BadgeProgress, GatorCheck

logger = logging.getLogger(__name__)

class BadgeSearchView(APIView):
    """
    Check if user has completed a specific badge.
    GET /v1/badger/search/?username=<username>&badge_id=<badge_id>
    """
    
    def get(self, request, *args, **kwargs):
        try:
            username = request.GET.get('username')
            badge_id = request.GET.get('badge_id')

            if not username or not badge_id:
                return HttpResponse(
                    json.dumps({'error': 'Username and badge_id are required'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            # Get badge and progress
            badge = Badge.objects.get(badge_id=badge_id)
            progress = BadgeProgress.objects.filter(
                badge=badge,
                student_username=username
            ).first()

            if not progress:
                return HttpResponse(
                    json.dumps({
                        'has_record': False,
                        'completed': False,
                        'steps': {}
                    }),
                    status=status.HTTP_200_OK,
                    content_type='application/json'
                )

            return HttpResponse(
                json.dumps({
                    'has_record': True,
                    'completed': progress.completed,
                    'steps': progress.step_status
                }),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Badge.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'Badge not found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error in badge search: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class BadgeStepUpdateView(APIView):
    """
    Update a specific step for a badge.
    PATCH /v1/badger/update/<badge_id>/step/<step>/
    """
    
    def patch(self, request, badge_id, step, *args, **kwargs):
        try:
            username = request.data.get('username')
            repository = request.data.get('repository')

            if not username or not repository:
                return HttpResponse(
                    json.dumps({'error': 'Username and repository are required'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            badge = Badge.objects.get(badge_id=badge_id)
            progress, created = BadgeProgress.objects.get_or_create(
                badge=badge,
                student_username=username,
                repository_name=repository
            )

            if created:
                progress.initialize_steps()

            progress.update_step(step, True)

            return HttpResponse(
                json.dumps({
                    'status': 'success',
                    'completed': progress.completed,
                    'steps': progress.step_status
                }),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Badge.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'Badge not found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error updating badge step: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class BadgeCollectionView(APIView):
    """
    Get all badges and their progress for a user.
    GET /v1/badger/collection/<username>/
    """
    
    def get(self, request, username, *args, **kwargs):
        try:
            progresses = BadgeProgress.objects.filter(
                student_username=username
            ).select_related('badge')

            badges = []
            for progress in progresses:
                badges.append({
                    'badge_id': progress.badge.badge_id,
                    'name': progress.badge.name,
                    'description': progress.badge.description,
                    'category': progress.badge.category,
                    'total_steps': progress.badge.total_steps,
                    'current_steps': progress.step_status,
                    'completed': progress.completed,
                    'repository': progress.repository_name,
                    'updated_at': progress.updated_at.isoformat()
                })

            return HttpResponse(
                json.dumps({'badges': badges}),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error getting badge collection: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class ProcessGatorOutputView(APIView):
    """
    Process GatorGrader output and update badges.
    POST /v1/badger/process/
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Extract data from request, handling both direct and nested formats
            if 'data' in request.data:
                data = request.data['data']
            else:
                data = request.data

            required_fields = ['repository_name', 'username', 'workflow_run_id', 'commit_hash', 'grading_output']
            if not all(field in data for field in required_fields):
                return HttpResponse(
                    json.dumps({'error': 'Missing required fields'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            # Create GatorCheck record
            gator_check = GatorCheck.objects.create(
                repository_name=data['repository_name'],
                student_username=data['username'],  # Note: changed from student_username to username
                workflow_run_id=data['workflow_run_id'],
                commit_hash=data['commit_hash']
            )

            # Process each badge step
            grading_output = data['grading_output']
            for check in grading_output:
                # Create or get badge
                badge = Badge.get_or_create_badge(
                    name=check['name'],
                    category=check.get('category', 'default')
                )

                # Get or create progress record
                progress, created = BadgeProgress.objects.get_or_create(
                    badge=badge,
                    repository_name=data['repository_name'],
                    student_username=data['username']
                )

                if created:
                    progress.initialize_steps()

                # Update step status
                progress.update_step(check['step'], True)

            # Update GatorCheck status
            gator_check.check_details = grading_output
            gator_check.passed_checks = len(grading_output)
            gator_check.total_checks = len(grading_output)
            gator_check.save()

            return HttpResponse(
                json.dumps(gator_check.as_dict()),
                status=status.HTTP_201_CREATED,
                content_type='application/json'
            )

        except Exception as e:
            logger.error(f"Error processing GatorGrader output: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )