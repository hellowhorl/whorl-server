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
            # Print incoming data for debugging
            print("Received data:", request.data)
            data = {
                'repository_name': request.data.get('repository_name'),
                'student_username': request.data.get('student_username'),
                'workflow_run_id': request.data.get('workflow_run_id'),
                'commit_hash': request.data.get('commit_hash')
            }

            if not all(data.values()):
                return HttpResponse(
                    json.dumps({'error': 'Missing required fields'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            gator_check = GatorCheck.objects.create(**data)
            success = gator_check.process_gator_output(request.data.get('grading_output', {}))

            if not success:
                return HttpResponse(
                    json.dumps({'error': 'Failed to process GatorGrader output'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

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