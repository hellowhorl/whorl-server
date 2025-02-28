import os
import io
import json
import requests

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
            client.beta.threads.messages.create(
                thread_id = getattr(interaction, 'thread_id'),
                role = "assistant",
                content = f"Your name is {persona_name}. Refer to yourself as {persona_name}."
            )
            interaction.save()
        thread_id = getattr(interaction, 'thread_id')
        # send user message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.data.get('message')
        )
        # start the run
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant.assistant_id
        )
        while run.status not in ['completed', 'failed', 'cancelled']:
            # print(f"Run status: {run.status}")

            if run.status == "requires_action" and run.required_action:
                try:
                    # extract the tool calls from the required action
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls

                    # simulate tool execution
                    tool_outputs = []
                    for tool in tool_calls:
                        function_name = tool.function.name
                        function_args = json.loads(tool.function.arguments)

                        # add / instead of _ and then add a underscore in the front of the function name aswell
                        function_name = function_name.replace("_", "/")
                        function_name = f"/{function_name}"

                        try:

                            # i dont think this is right (im sorry)
                            # check if this is an inventory request
                            if "inventory" in function_name.lower():
                                requestor = request.data.get('charname')
                                # print(requestor, persona_name)
                                if requestor == persona_name.lower():
                                    raise ForbiddenInventoryError

                            # make a GET request to the tool function
                            response = requests.get(
                                f"http://localhost:8000{function_name}",
                                params=function_args,
                            )

                            # print(response.content)

                            # print(f"Executing tool function: {function_name} with args {function_args}")

                            # simulate function execution
                            output = {"result": f"Executed {function_name} with args {function_args}"}

                            tool_outputs.append({"tool_call_id": tool.id, "output": json.dumps(response.json())})

                        except ForbiddenInventoryError as inv_err:
                            output = {
                                "error": "Request failed",
                                "message": f"Can't access inventories that aren't yours. Address the player as {request.data.get('charname')}."
                            }
                            tool_outputs.append({"tool_call_id": tool.id, "output": json.dumps(output)})

                        except Exception as req_err:
                            # print(f"Request error: {req_err}")
                            output = {
                                "error": "Request failed",
                                "message": "Could not connect."
                            }
                            tool_outputs.append({"tool_call_id": tool.id, "output": json.dumps(output)})

                    # submit the tool outputs back to continue processing
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                except Exception as e:
                    # print(f"error handling tool execution: {e}")
                    return HttpResponse(json.dumps({"error": "tool execution failed", "details": str(e)}), status=500)

            # poll again to get the latest response
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        # fetch response
        response = client.beta.threads.messages.list(
            thread_id = thread_id,
            limit = 1,
            order = "desc"
        )
        
        latest = response.data[0].content[0].text.value
        # print(response)

        file_uri = None
        try:
            files = response.data[0].content[0].text.annotations
            for file in files:
                file_uri = file.file_citation.file_id
        except Exception as e:
            print(f"File processing error: {e}")

        data = {
            "response": latest,
            "attachments": json.dumps(file_uri),
        }

        return HttpResponse(json.dumps(data), status=200)

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

class PersonaThreadManagementView(APIView):

    def get(self, request, thread_id, *args, **kwargs):
        runs = client.beta.threads.runs.list(
            thread_id = thread_id
        )
        for run in runs:
            try:
                canceled = client.beta.threads.run.cancel(
                    thread_id = thread_id,
                    run_id = run.id
                )
            except:
                pass
        return HttpResponse(
            status = 200
        )

    def delete(self, request, thread_id, *args, **kwargs):
        thread = PersonaThreadModel.objects.get(
            thread_id = thread_id
        )
        thread.delete()
        return HttpResponse(
            status = 200
        )

class ForbiddenInventoryError(Exception):

    def __init__(self, *args):
        super().__init__(args)
