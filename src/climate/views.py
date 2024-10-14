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
