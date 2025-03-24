from django.db import models

class PersonaModel(models.Model):

    assistant_name = models.CharField(max_length = 255)
    assistant_id = models.CharField(max_length = 255)
    assistant_owner = models.ForeignKey(
        'omnipresence.OmnipresenceModel',
        on_delete = models.DO_NOTHING,
        default = 1
    )

    def as_dict(self):
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result

class PersonaThreadModel(models.Model):

    thread_owner = models.ForeignKey(
        'omnipresence.OmnipresenceModel',
        on_delete = models.DO_NOTHING,
        default = 1
    )
    assistant_id = models.ForeignKey(
        PersonaModel,
        on_delete = models.DO_NOTHING,
        default = 1
    )
    thread_id = models.CharField(max_length = 255)

    def as_dict(self):
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result
