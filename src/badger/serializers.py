from rest_framework import serializers
from .models import GradeCheck

class GradeCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeCheck
        fields = '__all__'
        read_only_fields = ('status',)