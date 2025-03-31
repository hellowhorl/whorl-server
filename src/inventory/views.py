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
        default_version="v1",
        description="API documentation for the Termunda Inventory service.",
        contact=openapi.Contact(email="dluman@allegheny.edu"),
        license=openapi.License(name="CC0"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class AddInventoryView(APIView):
    """
    Handles the addition of inventory items for a specific user.

    Methods:
        post(request, *args, **kwargs):
            Processes a POST request to add or update an inventory item.

    POST Request Parameters:
        - item_owner (str): The character name of the item owner.
        - item_name (str): The name of the item to be added or updated.
        - item_consumable (bool): Indicates whether the item is consumable.
        - item_binary (file): A binary file representing the item.
        - item_qty (float): The quantity of the item to be added.

    Behavior:
        - Retrieves the item owner record based on the provided character name.
        - Creates a new inventory item or retrieves an existing one based on the item owner ID and item name.
        - Updates the item's attributes, including consumable status, binary data, and quantity.
        - If the item already exists, updates its quantity and recalculates its bulk.
        - Saves the item to the database.
        - Handles potential database exceptions, such as exceeding inventory capacity.

    Responses:
        - 200: Item successfully added or updated.
        - 400: Bad request.
        - 409: Conflict, typically due to exceeding inventory capacity.
    """

    def post(self, request, *args, **kwargs):
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname=request.data.get("item_owner")
        )
        item_owner_id = getattr(item_owner_record, "id")
        item, created = Inventory.objects.get_or_create(
            item_owner_id=item_owner_id, item_name=request.data.get("item_name")
        )
        setattr(item, "item_consumable", request.data.get("item_consumable"))
        setattr(item, "item_bytestring", request.FILES["item_binary"].read())
        if not created:  # In the case that the record exists; should be updated
            # Update quantity and space (bulk); TODO: need to figure out how to handle versioning
            qty = getattr(item, "item_qty") + float(request.data.get("item_qty"))
            setattr(item, "item_qty", qty)
            # TODO: This is really a trigger?
            setattr(item, "item_bulk", qty * getattr(item, "item_weight"))
            # Save modified item to database
        try:
            item.save()
        except PostgresException as e:
            return HttpResponse(
                json.dumps(
                    {"error": "You are overburdened! Remove items from your inventory."}
                ),
                status=409,
            )
        return HttpResponse(status=200)
        return HttpResponse(status=400)


class ReduceInventoryView(GenericAPIView, UpdateModelMixin):
    """
    ReduceInventoryView is a view that handles reducing the quantity of an item in the inventory.

    This view supports PATCH requests to update the quantity of an item owned by a specific character.
    If the item is not consumable and the request is not a drop request, no changes are made.

    Methods:
        patch(request, *args, **kwargs):
            Handles the PATCH request to reduce the quantity of an item in the inventory.
            - Retrieves the item owner record based on the provided character name.
            - Retrieves the inventory item based on the owner ID and item name.
            - Checks if the item is consumable or if the request is a drop request.
            - Reduces the item quantity by 1 and updates the item's bulk based on its weight.
            - Saves the updated item to the database.
            - Returns an HTTP 200 response.

    Attributes:
        Inherits from:
            - GenericAPIView: Provides generic behavior for API views.
            - UpdateModelMixin: Provides behavior for updating model instances.
    """

    def patch(self, request, *args, **kwargs):
        item_owner_record = omnipresence.models.OmnipresenceModel.objects.get(
            charname=request.data.get("item_owner")
        )
        item = Inventory.objects.get(
            item_owner_id=getattr(item_owner_record, "id"),
            item_name=request.data.get("item_name"),
        )
        is_drop_request = request.data.get("item_drop") or False
        if getattr(item, "item_consumable") == False and not is_drop_request:
            return HttpResponse(status=200)
        qty = getattr(item, "item_qty") - 1
        setattr(item, "item_qty", qty)
        # TODO: This is really a trigger?
        setattr(item, "item_bulk", qty * getattr(item, "item_weight"))
        item.save()
        return HttpResponse(status=200)


class DropInventoryView(APIView):
    """
    Handles the dropping of an inventory item via a POST request.

    This view allows a user to reduce the quantity of a specific inventory item
    associated with a given owner. If the item does not exist, an error response
    is returned.

    Methods:
        post(request, *args, **kwargs):
            Processes the POST request to drop an inventory item.

    POST Request:
        - Expects `item_name` (str): The name of the item to be dropped.
        - Expects `item_owner` (str): The identifier of the item's owner.

    Responses:
        - 200 OK: If the item is successfully dropped.
            Example: {"message": "Item dropped", "item": {...}}
        - 400 Bad Request: If required fields are missing.
            Example: {"error": "Item name is required"}
        - 404 Not Found: If the specified item does not exist.
            Example: {"error": "Item not found"}

    Notes:
        - The `item_owner` is fetched as a foreign key from the `OmnipresenceModel`.
        - The view currently reduces the item's quantity by 1. If the quantity
          reaches zero, additional handling may be required.
        - There are TODOs in the code suggesting potential refactoring or
          removal of this view.
    """

    # TODO: Potentially also a patch request?
    # Super TODO: Can we drop this view altogether?

class ListInventoryView(APIView):
    """
    API view to list all inventory items for a specific inventory holder.

    This view handles GET requests to retieve inventory items associated
    with a specific charaacter name. It queries the database for the inventory
    holder's ID, fetches the inventory items belonging to that ID, serilizies
    the data, and returns it as a JSON response.

    Methods:
        get(request, *args, **kwargs)
            Handles GET requests to retrieve and return the inventory items.

    Workflow: 
        1. Retrieve the character name ('charname') from the request's query parameters.
        2. Query the 'OmnipresenceModel' to get ID of the Inventory holder based 'charname'.
        3. use the retrieved ID to filter the 'inventory' model for items owned by the inventory
        4. Serialize the filtered inventory items using 'InventorySerializer'.
        5. Return the serialized data as a JSON response with an HTTP 200 status.

    Returns:
        HttpResponse: A JSON response containing the serialized inventory items
                      or an appropriate error message if the request fails.
    """
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
    """
    API view to search for a specific inventory item owned by a character.

    This view handles POST requests to retrieve details of a specific inventory
    item associated with a character. It queries the database for the inventory
    holder's ID based on the character name, fetches the requested item, and
    returns its details as a JSON response.

    Methods:
        post(request, *args, **kwargs):
            Handles POST requests to search for and return the details of a specific inventory item.

    Workflow:
        1. Retrieve the character name (`charname`) from the request's data.
        2. Query the `OmnipresenceModel` to get the ID of the inventory holder based on the `charname`.
        3. Use the retrieved ID to search the `Inventory` model for the specified item.
        4. If the item is found:
            - Convert the item to a dictionary using its `as_dict` method.
            - Remove the `item_owner` field from the response.
            - Convert the `item_bytestring` field to a hexadecimal string for transmission.
        5. Return the serialized item data as a JSON response with an HTTP 200 status.
        6. If the item is not found, return an HTTP 404 status.

    Returns:
        HttpResponse:
            - A JSON response containing the serialized item details if the item is found.
            - An HTTP 404 response if the item does not exist.
    """
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
    """
    API view to transfer an inventory item from one character to another.

    This view handles PATCH requests to facilitate the transfer of an inventory
    item from one character (giver) to another (receiver). It updates the inventory
    records for both characters to reflect the transfer.

    Methods:
        patch(request, to_charname, *args, **kwargs):
            Handles PATCH requests to transfer an inventory item.

    Workflow:
        1. Retrieve the item name from the request data.
        2. Retrieve the giver's and receiver's records from the `OmnipresenceModel` using their character names.
        3. Fetch the inventory item from the giver's inventory.
        4. If the item does not exist in the giver's inventory, return an HTTP 404 status.
        5. Convert the item to a dictionary and update its owner to the receiver.
        6. Check if the receiver already has the item:
            - If the item exists, update its quantity and bulk.
            - If the item does not exist, create a new record for the receiver.
        7. Update the giver's inventory to reflect the reduced quantity and bulk.
        8. Save the changes to both the giver's and receiver's inventory records.
        9. Return an HTTP 200 status to indicate a successful transfer.

    Returns:
        HttpResponse:
            - HTTP 200 status if the transfer is successful.
            - HTTP 400 status if either the giver or receiver does not exist.
            - HTTP 404 status if the item does not exist in the giver's inventory.
    """
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