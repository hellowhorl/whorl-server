import sys
import base64

from rest_framework import serializers
from .models import Inventory

class InventorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Inventory
        fields = '__all__'

    def validate_item_structure(self, item):
        try:
            # TODO: Rewrite validation with binary interpretation
            pass
        except:
            # TODO: Raise individual exceptions for parts of the flow above?
            raise serializers.ValidationError(
                {"item_binary": "Item binary does not represent a valid item."}
            )
        return binary
