import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import Badge, BadgeProgress, GatorCheck

logger = logging.getLogger(__name__)

class BadgeSearchView(APIView):
    """Check if user has completed a specific badge."""
    
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

            # First check if badge exists
            try:
                badge = Badge.objects.get(badge_id=badge_id)
            except Badge.DoesNotExist:
                return HttpResponse(
                    json.dumps({'error': 'Badge not found'}),
                    status=status.HTTP_404_NOT_FOUND,
                    content_type='application/json'
                )

            # Get badge progress
            progress = BadgeProgress.objects.filter(
                badge=badge,
                student_username=username
            ).first()

            # Return appropriate response based on progress
            if not progress:
                return HttpResponse(
                    json.dumps({'has_record': False, 'completed': False}),
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
        except Exception as e:
            logger.error(f"Error searching badge: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class BadgeStepUpdateView(APIView):
    """Update a specific step for a badge."""
    
    def patch(self, request, badge_id, step, *args, **kwargs):
        try:
            username = request.data.get('username')
            if not username:
                return HttpResponse(
                    json.dumps({'error': 'Username is required'}),
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            # Get or create badge progress
            badge = Badge.objects.get(badge_id=badge_id)
            progress, created = BadgeProgress.objects.get_or_create(
                badge=badge,
                student_username=username
            )

            # Initialize steps if new record
            if created:
                progress.initialize_steps()

            # Update step
            progress.update_step(int(step), True)

            return HttpResponse(
                json.dumps({'status': 'success'}),
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
    """Get all badges and their progress for a user."""
    
    def get(self, request, username, *args, **kwargs):
        try:
            # Get all badge progress for user
            progresses = BadgeProgress.objects.filter(
                student_username=username
            ).select_related('badge')

            # Format response
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