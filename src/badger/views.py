import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import GradeCheck
from .serializers import GradeCheckSerializer
from .services.grade_service import GradeService
from .services.badge_service import BadgeService

logger = logging.getLogger(__name__)

class SubmitGradeCheckView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            grade_service = GradeService()
            results = grade_service.process_gator_output(request.data.get('grading_output', {}))
            
            data = {
                'repository_name': request.data.get('repository_name'),
                'student_username': request.data.get('student_username'),
                'workflow_run_id': request.data.get('workflow_run_id'),
                'commit_hash': request.data.get('commit_hash'),
                'passed_checks': results['passed_checks'],
                'total_checks': results['total_checks'],
                'check_details': results['details']
            }
            
            serializer = GradeCheckSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
                return HttpResponse(
                    json.dumps(instance.as_dict()),
                    status=status.HTTP_201_CREATED,
                    content_type='application/json'
                )
            return HttpResponse(
                json.dumps({'error': serializer.errors}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error processing grade check: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class ListGradeChecksView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            username = request.GET.get('username')
            repository = request.GET.get('repository')
            
            queryset = GradeCheck.objects.all()
            if username:
                queryset = queryset.filter(student_username=username)
            if repository:
                queryset = queryset.filter(repository_name=repository)
            
            results = [check.as_dict() for check in queryset]
            return HttpResponse(
                json.dumps(results),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error listing grade checks: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class GetBadgeView(APIView):
    def get(self, request, username, repository, *args, **kwargs):
        try:
            latest_check = GradeCheck.objects.filter(
                student_username=username,
                repository_name=repository
            ).latest('created_at')
            
            badge_service = BadgeService()
            badge_url = badge_service.generate_badge_url(
                repository,
                latest_check.passed_checks,
                latest_check.total_checks,
                latest_check.status
            )
            
            return HttpResponse(
                json.dumps({'badge_url': badge_url}),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except GradeCheck.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'No grade checks found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )