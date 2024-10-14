import pgtrigger
from datetime import datetime
from django.db import models

class OmnipresenceModel(models.Model):

    username = models.CharField(max_length = 255)
    charname = models.CharField(max_length = 255, unique = True)
    working_dir = models.CharField(max_length = 512)
    last_active = models.DateTimeField(auto_now = True)
    is_active = models.BooleanField(default = True)

    def as_dict(self):
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result
