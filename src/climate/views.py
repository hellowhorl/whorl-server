import json

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from django.http import HttpResponse
from django.core import serializers
from rest_framework.permissions import AllowAny

from climate.models import ClimateModel
from climate.serializers import ClimateModelSerializer


class ClimateDataViewAll(RetrieveAPIView):
    """
    API view to retrieve all climate data records.

    This view provides a GET endpoint that returns the most recent climate data 
    stored in the database. It retrieves all records from the `ClimateModel` table 
    and returns the latest entry in JSON format.

    Attributes:
        * permission_classes (list): Allows unrestricted access to the view.
        * serializer_class (ClimateModelSerializer): Defines the serializer for the model.
    """

    permission_classes = [AllowAny]
    serializer_class = ClimateModelSerializer

    def get_queryset(self):
        try:
            queryset = ClimateModel.obj.all()
            return queryset
        except Exception as e:
            raise APIException(e) from e

    def get(self, request):
        fields = [obj.as_dict() for obj in self.get_queryset()][-1]
        return HttpResponse(json.dumps(fields), content_type = "application/json")
