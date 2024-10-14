from rest_framework import serializers
from omnipresence.models import OmnipresenceModel

class OmnipresenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = OmnipresenceModel
        fields = ["username", "charname", "working_dir"]
