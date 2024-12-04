from django.contrib import admin
from .models import GradeCheck

@admin.register(GradeCheck)
class GradeCheckAdmin(admin.ModelAdmin):
    list_display = ('repository_name', 'student_username', 'status', 'passed_checks', 'total_checks', 'created_at')
    list_filter = ('status', 'repository_name')
    search_fields = ('student_username', 'repository_name')
    ordering = ('-created_at',)
