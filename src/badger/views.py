import json
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin
from .models import GradeCheck
from .generate_badger import BadgeGenerator
from .grade_services import GradeService

logger = logging.getLogger(__name__)

class AddGradeCheckView(APIView):
    """Handle submission of new grading results."""
    
    def post(self, request, *args, **kwargs):
        try:
            # Process GatorGrader output
            grade_service = GradeService()
            grading_output = request.data.get('grading_output', {})
            
            # Validate and process the output
            results = grade_service.process_gator_output(grading_output)
            formatted_results = grade_service.format_check_output(results)
            
            data = {
                'repository_name': request.data.get('repository_name'),
                'student_username': request.data.get('student_username'),
                'workflow_run_id': request.data.get('workflow_run_id'),
                'commit_hash': request.data.get('commit_hash'),
                'passed_checks': results['passed_checks'],
                'total_checks': results['total_checks'],
                'check_details': formatted_results['details']
            }

            grade_check = GradeCheck.objects.create(**data)
            
            # Generate badge URL
            badge_generator = BadgeGenerator()
            badge_url = badge_generator.generate_badge_url(
                grade_check.repository_name,
                grade_check.passed_checks,
                grade_check.total_checks,
                grade_check.status
            )
            
            response_data = grade_check.as_dict()
            response_data['badge_url'] = badge_url

            return HttpResponse(
                json.dumps(response_data),
                status=status.HTTP_201_CREATED,
                content_type='application/json'
            )
        except ValueError as e:
            logger.error(f"Validation error in grade check: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error adding grade check: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class UpdateGradeCheckView(GenericAPIView, UpdateModelMixin):
    """Handle updates to existing grade checks."""
    
    def patch(self, request, *args, **kwargs):
        try:
            workflow_run_id = request.data.get('workflow_run_id')
            grade_check = GradeCheck.objects.get(workflow_run_id=workflow_run_id)
            
            # Process new GatorGrader output
            grade_service = GradeService()
            grading_output = request.data.get('grading_output', {})
            results = grade_service.process_gator_output(grading_output)
            formatted_results = grade_service.format_check_output(results)
            
            # Update grade check
            grade_check.passed_checks = results['passed_checks']
            grade_check.total_checks = results['total_checks']
            grade_check.check_details = formatted_results['details']
            grade_check.save()
            
            # Generate updated badge URL
            badge_generator = BadgeGenerator()
            badge_url = badge_generator.generate_badge_url(
                grade_check.repository_name,
                grade_check.passed_checks,
                grade_check.total_checks,
                grade_check.status
            )
            
            response_data = grade_check.as_dict()
            response_data['badge_url'] = badge_url

            return HttpResponse(
                json.dumps(response_data),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except GradeCheck.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'Grade check not found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except ValueError as e:
            logger.error(f"Validation error in grade check update: {str(e)}")
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error updating grade check: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

class ListGradeChecksView(APIView):
    """List all grade checks for a repository or student."""
    
    def get(self, request, *args, **kwargs):
        try:
            filters = {}
            username = request.GET.get('username')
            repository = request.GET.get('repository')

            if username:
                filters['student_username'] = username
            if repository:
                filters['repository_name'] = repository

            grade_checks = GradeCheck.objects.filter(**filters)
            badge_generator = BadgeGenerator()
            
            results = []
            for check in grade_checks:
                result = check.as_dict()
                result['badge_url'] = badge_generator.generate_badge_url(
                    check.repository_name,
                    check.passed_checks,
                    check.total_checks,
                    check.status
                )
                results.append(result)

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

class SearchGradeChecksView(APIView):
    """Search for specific grade checks."""
    
    def post(self, request, *args, **kwargs):
        try:
            repository = request.data.get('repository_name')
            username = request.data.get('student_username')

            if not repository or not username:
                raise ValueError("Both repository_name and student_username are required")

            grade_check = GradeCheck.objects.get(
                repository_name=repository,
                student_username=username
            )
            
            badge_generator = BadgeGenerator()
            badge_url = badge_generator.generate_badge_url(
                grade_check.repository_name,
                grade_check.passed_checks,
                grade_check.total_checks,
                grade_check.status
            )
            
            response_data = grade_check.as_dict()
            response_data['badge_url'] = badge_url

            return HttpResponse(
                json.dumps(response_data),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except GradeCheck.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'Grade check not found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except ValueError as e:
            return HttpResponse(
                json.dumps({'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error searching grade checks: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )
        

class GetBadgeView(APIView):
    """Generate and return badge for specific grade check."""
    
    def get(self, request, username, repository, *args, **kwargs):
        try:
            grade_check = GradeCheck.objects.filter(
                student_username=username,
                repository_name=repository
            ).latest('created_at')
            
            badge_generator = BadgeGenerator()
            badge_url = badge_generator.generate_badge_url(
                repository,
                grade_check.passed_checks,
                grade_check.total_checks,
                grade_check.status
            )
            
            return HttpResponse(
                json.dumps({
                    'badge_url': badge_url,
                    'status': grade_check.status,
                    'details': grade_check.as_dict()
                }),
                status=status.HTTP_200_OK,
                content_type='application/json'
            )
        except GradeCheck.DoesNotExist:
            return HttpResponse(
                json.dumps({'error': 'No grade checks found'}),
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error generating badge: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Internal server error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )