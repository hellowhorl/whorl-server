"""
Persona Management Models

Defines core database models for:
    - PersonaModel: AI assistant configurations
    - PersonaThreadModel: Conversation threads tied to personas

Relationships:
    - Both link to OmnipresenceModel
    - Threads reference PersonaModel
    - Includes simple as_dict() serialization
"""

from django.db import models


class PersonaModel(models.Model):
    """
    Represents an AI Assistant Persona in the system.

    Attributes:
        * assistant_name (str): Name of the AI assistant persona.
        * assistant_id (str): Unique identifier from the AI provider (e.g., OpenAI).
        * assistant_owner (ForeignKey): Reference to the owner's OmnipresenceModel instance.

    Methods:
        * as_dict(): Serializes the model instance to a dictionary
    """

    assistant_name = models.CharField(max_length = 255)
    assistant_id = models.CharField(max_length = 255)
    assistant_owner = models.ForeignKey(
        'omnipresence.OmnipresenceModel',
        on_delete = models.DO_NOTHING,
        default = 1
    )

    def as_dict(self):
        """
        Serializes the PersonaModel instance to a dictionary.

        Returns:
            * Dictionary representation containing all model fields:
                * assistant_name
                * assistant_id
                * assistant_owner (ID of linked OmnipresenceModel)
        """
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result


class PersonaThreadModel(models.Model):
    """
    Represents a conversation thread associated with a specific AI assistant persona.

    Attributes:
        * thread_owner (ForeignKey): Reference to the owner's OmnipresenceModel instance
        * assistant_id (ForeignKey): Reference to the associated PersonaModel
        * thread_id (str): Unique thread identifier from the AI provider

    Methods:
        * as_dict(): Serializes the model instance to a dictionary
    """

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
        """
        Serializes the PersonaThreadModel instance to a dictionary.

        Returns:
            * dict: Dictionary representation containing all model fields:
                * thread_owner (ID of linked OmnipresenceModel)
                * assistant_id (ID of linked PersonaModel)
                * thread_id
        """
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result
