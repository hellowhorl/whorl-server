import os
import io
import json

from openai import OpenAI, AssistantEventHandler
from django.core import serializers
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import UpdateModelMixin
from omnipresence.models import OmnipresenceModel
from persona.models import PersonaModel, PersonaThreadModel
from .serializers import PersonaModelSerializer, PersonaThreadSerializer

# TODO: Implement tool_calls and other estoterica

client = OpenAI(
    api_key = os.getenv('OPEN_AI_KEY')
)

class AssistantStream(AssistantEventHandler):
    pass

class StreamPersonaGenerateView(APIView):

    """
       This is not deprecated, but not nearly as useful as it seemed;
       we keep in in here because one day it may return to service.
    """

    def __stream_assistant_response(self, thread_id, assistant_id, charname):
        with client.beta.threads.runs.stream(
            thread_id = thread_id,
            assistant_id = assistant_id,
            event_handler = AssistantStream()
        ) as stream:
            for part in stream.text_deltas:
                yield part
            stream.until_done()

    def post(self, request, persona_name, *args, **kwargs):
        assistant_id = None
        interactor = OmnipresenceModel.objects.get(
            charname = request.data.get('charname')
        )
        try:
            assistant = PersonaModel.objects.get(
                assistant_name = persona_name
            )
        except PersonaModel.DoesNotExist:
            return HttpResponse(status = 400)
        interaction, created = PersonaThreadModel.objects.get_or_create(
            thread_owner = interactor,
            assistant_id = assistant
        )
        if created:
            thread = client.beta.threads.create()
            setattr(interaction, 'thread_id', thread.id)
            interaction.save()
        thread_id = getattr(interaction, 'thread_id')
        message = client.beta.threads.messages.create(
            thread_id = thread_id,
            role="user",
            content= request.data.get('message')
        )
        response = self.__stream_assistant_response(
            thread_id,
            getattr(assistant, 'assistant_id'),
            request.data.get('charname')
        )
        stream = StreamingHttpResponse(
            response,
            status = 200,
            content_type = 'text/event-stream'
        )
        stream['Cache-Control'] = 'no-cache'
        return stream

class SyncPersonaGenerateView(APIView):

    def post(self, request, persona_name, *args, **kwargs):
        assistant_id = None
        interactor = OmnipresenceModel.objects.get(
            charname = request.data.get('charname')
        )
        try:
            assistant = PersonaModel.objects.get(
                assistant_name = persona_name
            )
        except PersonaModel.DoesNotExist:
            return HttpResponse(status = 400)
        interaction, created = PersonaThreadModel.objects.get_or_create(
            thread_owner = interactor,
            assistant_id = assistant
        )
        if created:
            thread = client.beta.threads.create()
            setattr(interaction, 'thread_id', thread.id)
            interaction.save()
        thread_id = getattr(interaction, 'thread_id')
        message = client.beta.threads.messages.create(
            thread_id = thread_id,
            role="user",
            content= request.data.get('message')
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id = thread_id,
            assistant_id = getattr(assistant, 'assistant_id'),
            # TODO: Add trigger for tool_choice: {type: "file_search"}
            #       if flag is set in Ego, transmit
        )
        while run.status != 'completed':
            pass
        response = client.beta.threads.messages.list(
            thread_id = thread_id,
            limit = 1,
            order = "desc"
        )
        latest = response.data[0].content[0].text.value
        print(response)
        file_uri = None
        try:
            files = response.data[0].content[0].text.annotations
            for file in files:
                file_id = file.file_citation.file_id
                fh = client.beta.assistants.retrieve(
                    getattr(assistant, 'assistant_id')
                )
                file_uri = file.file_citation.file_id
                # print(file.file_citation.file_id)
        except Exception as e:
            print(e)
        data = {
            "response": latest,
            "attachments": json.dumps(file_uri),
        }
        return HttpResponse(
            json.dumps(data),
            status = 200
        )

class PersonaSearchView(APIView):

    def get(self, request, persona_name, *args, **kwargs):
        try:
            person = PersonaModel.objects.get(
                assistant_name = persona_name
            )
            return HttpResponse(status = 200)
        except PersonaModel.DoesNotExist:
            return HttpResponse(status = 404)

class PersonaCreateView(APIView):

    def post(self, request, persona_name, *args, **kwargs):

        vector_store = client.beta.vector_stores.create(name = "Inventory")

        persona_file_name = request.data.get('persona_file_name')
        persona_file = request.FILES['file_binary'].file

        if persona_file_name:
            persona_file.seek(0)
            persona_file.name = persona_file_name
            persona_binary = io.BufferedReader(persona_file)
            batch_upload = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id = vector_store.id, files = [persona_binary]
            )

        persona_creator = request.data.get('persona_creator')
        persona_prompt = request.data.get('persona_prompt')

        assistant = client.beta.assistants.create(
            name = persona_name,
            instructions = persona_prompt,
            model = "gpt-4o",
            tools = [{"type": "file_search"}],
            tool_resources = {
                "file_search": {
                    "vector_store_ids": [vector_store.id]
                }
            }
        )

        id = assistant.id
        name = assistant.name

        persona, created = PersonaModel.objects.get_or_create(
            assistant_name = name
        )

        if not created:
            return HttpResponse(
                json.dumps({"response": "Assistant with that name already exists!"}),
                status = 400
            )
        try:
            creator = OmnipresenceModel.objects.get(
                charname = persona_creator
            )
        except OmnipresenceModel.DoesNotExist:
            return HttpResponse(status = 400)

        setattr(persona, 'assistant_owner', creator)
        setattr(persona, 'assistant_id', id)
        persona.save()

        return HttpResponse(
            json.dumps({"response": "Assistant created!", "name": name, "id": id}),
            status = 200
        )

