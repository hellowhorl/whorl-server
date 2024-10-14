from rest_framework import viewsets
from api.models import Climate
from api.serializers import ClimateSerializer


class ClimateViewSet(viewsets.ModelViewSet):
    """A viewset for viewing and editing Climate instances."""

    queryset = Climate.objects.all() # Define the queryset to be all instances of the Climate model
    serializer_class = ClimateSerializer # Specify the serializer class to be used for this viewset
