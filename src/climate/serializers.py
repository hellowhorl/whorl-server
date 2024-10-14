from rest_framework import serializers
from climate.models import ClimateModel

class ClimateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateModel
        fields = "__all__"

