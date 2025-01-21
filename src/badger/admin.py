from django.contrib import admin
from .models import Badge, BadgeProgress, GatorCheck

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('badge_id', 'name', 'category', 'total_steps', 'created_at')
    list_filter = ('category',)
    search_fields = ('badge_id', 'name', 'description')
    ordering = ('badge_id',)

@admin.register(BadgeProgress)
class BadgeProgressAdmin(admin.ModelAdmin):
    list_display = ('badge', 'student_username', 'repository_name', 'completed', 'updated_at')
    list_filter = ('completed', 'badge')
    search_fields = ('student_username', 'repository_name')
    ordering = ('-updated_at',)

@admin.register(GatorCheck)
class GatorCheckAdmin(admin.ModelAdmin):
    list_display = ('repository_name', 'student_username', 'status', 'passed_checks', 'total_checks', 'created_at')
    list_filter = ('status', 'repository_name')
    search_fields = ('student_username', 'repository_name')
    ordering = ('-created_at',)