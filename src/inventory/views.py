import json
import requests
import logging
import omnipresence

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import UpdateModelMixin
from .models import Inventory
from .serializers import InventorySerializer
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.db.utils import InternalError as PostgresException

# Set up the logger
logger = logging.getLogger(__name__)

schema_view = get_schema_view(
    openapi.Info(
        title="Inventory API",
        default_version='v1',
        description="API documentation for the Termunda Inventory service.",
        contact=openapi.Contact(email="dluman@allegheny.edu"),
        license=openapi.License(name="CC0"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

class AddInventoryView(APIView):

    def post(self, request, *args, **kwargs):
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname = request.data.get('item_owner')
        )
        item_owner_id = getattr(item_owner_record, 'id')
        item, created = Inventory.objects.get_or_create(
            item_owner_id = item_owner_id,
            item_name = request.data.get("item_name")
        )
        setattr(item, 'item_consumable', request.data.get('item_consumable'))
        setattr(item, 'item_bytestring', request.FILES['item_binary'].read())
        if not created: # In the case that the record exists; should be updated
            # Update quantity and space (bulk); TODO: need to figure out how to handle versioning
            qty = getattr(item, 'item_qty') + float(request.data.get('item_qty'))
            setattr(item, 'item_qty', qty)
            # TODO: This is really a trigger?
            setattr(item, 'item_bulk', qty * getattr(item, 'item_weight'))
            # Save modified item to database
        try:
            item.save()
        except PostgresException as e:
            return HttpResponse(
                json.dumps({'error': 'You are overburdened! Remove items from your inventory.'}),
                status = 409
            )
        return HttpResponse(
            status = 200
        )
        return HttpResponse(status = 400)

class ReduceInventoryView(GenericAPIView, UpdateModelMixin):

    def patch(self, request, *args, **kwargs):
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname = request.data.get('item_owner')
        )
        item = Inventory.objects.get(
            item_owner_id = getattr(item_owner_record, "id"),
            item_name = request.data.get('item_name')
        )
        is_drop_request = request.data.get('item_drop') or False
        if getattr(item, 'item_consumable') == False and not is_drop_request:
            return HttpResponse(status = 200)
        qty = getattr(item, 'item_qty') - 1
        setattr(item, 'item_qty', qty)
        # TODO: This is really a trigger?
        setattr(item, 'item_bulk', qty * getattr(item, 'item_weight'))
        item.save()
        return HttpResponse(status = 200)

class DropInventoryView(APIView):

    # TODO: Potentially also a patch request?
    # Super TODO: Can we drop this view altogether?

    def post(self, request, *args, **kwargs):
        logger.debug("DropInventoryView POST request data: %s", request.data)
        item_name = request.data.get('item_name')
        # TODO: Theoretically, as a foreign key, we should be able to page through
        #       inventory objects by name and read the foreign key data? Revisit.
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname = request.data.get('item_owner')
        )
        if not item_name:
            return Response({"error": "Item name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not item_owner:
            return HttpResponse({"error": "Item owner ID requred"}, status = 400)
        try:
            inventory_item = Inventory.objects.get(
                item_name = item_name,
                item_owner_id = item_owner
            )
            qty = getattr(inventory_item, 'item_qty')
            setattr(inventory_item, 'item_qty', qty - 1)
            serializer = InventorySerializer(data = inventory_item)
            if serializer.is_valid():
                serializer.save()
            return Response({"message": "Item dropped", "item": inventory_item.as_dict()}, status=status.HTTP_200_OK)
        except Inventory.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

class ListInventoryView(APIView):

    def get(self, request, *args, **kwargs):
        # Retrieve ID of inventory holder
        inventory_owner_data = omnipresence.models.OmnipresenceModel.objects.filter(
            charname = request.GET.get('charname')
        ).values('id')
        # Get information for the inventory holder
        inventory_owner_id = list(inventory_owner_data)[0]['id']
        # Filter inventory based on the inventory holder id
        inventory_items = Inventory.objects.filter(
            item_owner = inventory_owner_id
        )
        # Serialize to re-verify, run other checks
        serializer = InventorySerializer(inventory_items, many=True)
        # Create list representation to transmit back to query
        fields = [obj for obj in serializer.data]
        # Return HTTP response (JSON packet)
        return HttpResponse(
            json.dumps(serializer.data),
            status=status.HTTP_200_OK,
            content_type = 'application/json'
        )

class SearchInventoryView(APIView):

    def post(self, request, *args, **kwargs):
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname = request.data.get('charname')
        )
        item = Inventory.objects.get(
            item_owner_id = getattr(item_owner_record, "id"),
            item_name = request.data.get('item_name')
        )
        if not item:
            return HttpResponse(
                status = 404
            )
        response = item.as_dict()
        del response['item_owner']
        response["item_bytestring"] = response['item_bytestring'].hex()
        return HttpResponse(
            json.dumps(response),
            status = 200,
            content_type = 'application/json'
        )

class GiveInventoryView(GenericAPIView, UpdateModelMixin):

    def patch(self, request, to_charname, *args, **kwargs):
        item_name = request.data.get('item_name')
        # Retrieve the two parties' information
        try:
            item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
                charname = request.data.get('charname')
            )
            item_receiver_record = omnipresence.models.OmnipresenceModel.objects.get(
                charname = to_charname
            )
        except OmnipresenceModel.DoesNotExist:
            return HttpResponse(
                status = 400
            )
        # Get the item given from owner's inventory
        item = Inventory.objects.get(
            item_owner_id = getattr(item_owner_record, "id"),
            item_name = item_name
        )
        # If nothing, let's cause a ruckus
        if not item:
            return HttpResponse(
                status = 404
            )
        # Convert to dictionary to separate from original instance
        item_params = item.as_dict()
        del item_params['id'] # Delete the giver's object ID
        # Transfer owner ID
        item_params['item_owner_id'] = getattr(item_receiver_record, 'id')
        # Get or create; do we necessarily need to issue a search in receiver's
        # inventory first? Probably.
        # TODO: Consider what happens if they're not the same binary; probably
        #       reject
        given_item, created = Inventory.objects.get_or_create(
            item_owner_id = getattr(item_receiver_record, 'id'),
            item_name = item_name
        )
        # Set some sensible baselines for quanitity and bulk
        qty = 1
        weight = getattr(item, 'item_weight')
        if not created: # Some amount already existed in receiver's inventory
            qty = getattr(given_item, 'item_qty') + 1
        # Set properties of given record to reflect actual amounts, bulk
        # TODO: Reject if amount given is greater than space available -- this is a trigger
        item_params['item_qty'] = qty
        item_params['item_bulk'] = qty * weight
        # Regardless of creation, let's set up the whole record
        for param in item_params:
            setattr(given_item, param, item_params[param])
        given_item.save()
        # Update original item from giver's inventory to reflect new amounts, bulk
        setattr(item, 'item_qty', getattr(item, 'item_qty') - 1)
        setattr(item, 'item_bulk', getattr(item, 'item_qty') * getattr(item, 'item_weight'))
        item.save()
        # Return successful transaction status; TODO: Add a message for both giver and receiver?
        return HttpResponse(
            status = 200
        )