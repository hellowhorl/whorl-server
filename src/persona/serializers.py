from rest_framework import serializers
from .models import PersonaModel, PersonaThreadModel

class PersonaThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonaThreadModel
        fields = '__all__'

class PersonaModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = PersonaModel
        fields = '__all__'
