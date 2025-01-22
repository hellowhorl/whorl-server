# whorl-server/src/badger/views.py
import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import Badge, BadgeProgress, GatorCheck

logger = logging.getLogger(__name__)

class BadgeCreateView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            badge = Badge.objects.create(
                badge_id=request.data.get('badge_id'),
                name=request.data.get('name'),
                category=request.data.get('category'),
                total_steps=request.data.get('total_steps', 1),
                description=request.data.get('description', '')
            )
            return HttpResponse(
                json.dumps({
                    'badge_id': badge.badge_id,
                    'name': badge.name,
                    'total_steps': badge.total_steps
                }),
                status=status.HTTP_201_CREATED,
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )

class GatorCheckSubmitView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            gator_check = GatorCheck.objects.create(
                repository_name=request.data.get('repository_name'),
                student_username=request.data.get('student_username'),
                workflow_run_id=request.data.get('workflow_run_id'),
                commit_hash=request.data.get('commit_hash')
            )
            gator_check.process_gator_output(request.data.get('grading_output', {}))
            
            return HttpResponse(
                json.dumps(gator_check.as_dict()),
                status=status.HTTP_201_CREATED,
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )

class BadgeSearchView(APIView):
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')
        badge_id = request.GET.get('badge_id')
        
        try:
            progress = BadgeProgress.objects.filter(
                student_username=username,
                badge__badge_id=badge_id
            ).select_related('badge').first()
            
            response = {'found': bool(progress)}
            if progress:
                response.update({
                    'completed': progress.completed,
                    'steps': progress.step_status
                })
            
            return HttpResponse(
                json.dumps(response),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class BadgeStepUpdateView(APIView):
    def patch(self, request, badge_id, step, *args, **kwargs):
        try:
            username = request.data.get('username')
            badge = Badge.objects.get(badge_id=badge_id)
            progress, created = BadgeProgress.objects.get_or_create(
                badge=badge,
                student_username=username,
                defaults={'repository_name': request.data.get('repository_name', 'default')}
            )
            
            if created:
                progress.initialize_steps()
                
            progress.update_step(step, True)
            
            return HttpResponse(
                json.dumps({
                    'updated': True,
                    'completed': progress.completed,
                    'steps': progress.step_status
                }),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )

class BadgeCollectionView(APIView):
    def get(self, request, username, *args, **kwargs):
        try:
            progresses = BadgeProgress.objects.filter(
                student_username=username
            ).select_related('badge')
            
            badges = [{
                'badge_id': p.badge.badge_id,
                'name': p.badge.name,
                'category': p.badge.category,
                'completed': p.completed,
                'steps': p.step_status
            } for p in progresses]
            
            return HttpResponse(
                json.dumps({'badges': badges}),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )