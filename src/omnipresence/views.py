import json

from django.core import serializers
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import UpdateModelMixin
from omnipresence.models import OmnipresenceModel
from omnipresence.serializer import OmnipresenceSerializer

class OmnipresenceView(GenericAPIView):
    """ API view to retrieve and create OmnipresenceModel instances. """
    queryset = OmnipresenceModel.objects.all()

    def get(self, request, *args, **kwargs):
        """ Retrieve character information based on 'charname' query parameter. """
        character = OmnipresenceModel.objects.filter(
            charname = request.GET.get('charname')
        ).values('pk', 'username', 'charname', 'working_dir', 'is_active')
        if character:
            return HttpResponse(
                json.dumps(list(character)),
                status = 200,
                content_type = 'application/json'
        )
        return HttpResponse(json.dumps(dict()), status = 200, content_type = 'application/json')

    def post(self, request, *args, **kwargs):
        """ Create a new OmnipresenceModel instance with the provided data. """
        data = {
            'username': request.data.get('username'),
            'charname': request.data.get('charname'),
            'working_dir': request.data.get('working_dir')
        }
        serializer = OmnipresenceSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response(status = 201)
        return Response(serializer.errors, status = 400)

class OmnipresenceActiveView(GenericAPIView):
    """ API view to retrieve active OmnipresenceModel instances. """

    queryset = OmnipresenceModel.objects.all()

    def get(self, request, *args, **kwargs):
        """ Retrieve all active characters. """
        actives = OmnipresenceModel.objects.filter(
            is_active = True
        ).values('username','charname')
        return HttpResponse(
            json.dumps(list(actives)),
            status = 200,
            content_type = 'application/json'
        )

    def post(self, request, *args, **kwargs):
        """ Retrieve active characters based on the current working directory. """
        local_actives = OmnipresenceModel.objects.filter(
            working_dir = request.data.get('cwd')
        ).values('charname')
        return HttpResponse(
            json.dumps(list(local_actives)),
            status = 200,
            content_type = 'application/json'
        )

class OmnipresenceUpdateView(GenericAPIView, UpdateModelMixin):
    """ API view to update OmnipresenceModel instances. """
    queryset = OmnipresenceModel.objects.all()
    serializer_class = OmnipresenceSerializer

    def patch(self, request, *args, **kwargs):
        """ Partially update an OmnipresenceModel instance. """
        return self.partial_update(request, *args, **kwargs)
