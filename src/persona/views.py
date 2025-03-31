"""
Persona Management Views

This module defines the views and endpoints for managing AI assistant personas and their interactions.

Features:
    - Real-time and synchronous AI persona interaction endpoints
    - Persona creation, search, and thread management
    - Integration with OpenAI's API for assistant responses and tools

Classes:
    - StreamPersonaGenerateView: Handles real-time streaming interactions with AI personas.
    - SyncPersonaGenerateView: Processes synchronous interactions with AI personas.
    - PersonaSearchView: Provides an endpoint to verify the existence of a persona.
    - PersonaCreateView: Handles the creation of new AI personas with OpenAI integration.
    - PersonaThreadManagementView: Manages conversation threads, including termination and cleanup.
"""

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
    Real-time streaming interface for AI persona interactions using Server-Sent Events (SSE)

    Endpoint: POST /generate/stream/<persona_name>/

    Flow:
        1. Validate requesting user through OmnipresenceModel
        2. Retrieve or create conversation thread
        3. Submit user message to OpenAI thread
        4. Stream assistant response deltas via SSE

    Parameters:
    - persona_name (str): Name of registered PersonaModel instance
    - Request Body:
        * charname (str): OmnipresenceModel identifier
        * message (str): User input content

    Returns:
        - StreamingHttpResponse: text/event-stream format with raw text deltas

    Exceptions:
        - HTTP 400: Invalid persona_name or missing required fields
        - HTTP 404: OmnipresenceModel not found
    """

    def __stream_assistant_response(self, thread_id, assistant_id, charname):
        """
        Internal generator for streaming OpenAI assistant responses

        Args:
            thread_id (str): OpenAI thread identifier
            assistant_id (str): OpenAI assistant ID
            charname (str): Owner identifier for logging

        Yields:
            str: Text deltas from assistant response stream

        Implementation Details:
            - Uses OpenAI's beta threads.runs.stream endpoint
            - Processes text_deltas in real-time
            - Maintains stream until completion with until_done()
        """
        with client.beta.threads.runs.stream(
            thread_id = thread_id,
            assistant_id = assistant_id,
            event_handler = AssistantStream()
        ) as stream:
            for part in stream.text_deltas:
                yield part
            stream.until_done()

    def post(self, request, persona_name, *args, **kwargs):
        """
        Handle POST request for streaming persona interaction

        Parameters:
            - request (Request): Django request object
            - persona_name (str): Target assistant name from URL

        Side Effects:
            - Creates new PersonaThreadModel if none exists
            - Updates thread_id in database
            - Creates new OpenAI thread when needed
        """
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
    """
    Synchronous AI persona interaction with full response handling

    Endpoint: POST /generate/sync/<persona_name>/

    Features:
        - Complete message processing before response
        - File citation extraction from responses
        - Automatic thread management
        - Polling mechanism for OpenAI run completion

    Parameters:
        - persona_name (str): Target PersonaModel name
        - Request Body:
            * charname (str): OmnipresenceModel identifier
            * message (str): User input content

    Returns:
        HttpResponse: JSON with structure:
            {
                "response": "full assistant text",
                "attachments": "file_id references"
            }
    """

    def post(self, request, persona_name, *args, **kwargs):
        """
        Process synchronous persona interaction request

        Flow:
            1. Validate user and persona existence
            2. Create/maintain conversation thread
            3. Submit message and poll for completion
            4. Extract response content and file references
            5. Return structured JSON response
        """
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
    """
    Persona existence verification endpoint

    Endpoint: GET /search/<persona_name>/

    Functionality:
        - Simple existence check for persona names
        - No payload required

    Responses:
        - HTTP 200: Persona exists
        - HTTP 404: Persona not found
    """

    def get(self, request, persona_name, *args, **kwargs):
        """
        Execute persona existence check

        Parameters:
            - persona_name (str): Name to check in PersonaModel registry
        """
        try:
            person = PersonaModel.objects.get(
                assistant_name = persona_name
            )
            return HttpResponse(status = 200)
        except PersonaModel.DoesNotExist:
            return HttpResponse(status = 404)


class PersonaCreateView(APIView):
    """
    Complete persona creation endpoint

    Endpoint: POST /create/<persona_name>/

    Creation Pipeline:
        1. Vector store initialization
        2. File upload to OpenAI storage
        3. Assistant creation with file_search capabilities
        4. Local PersonaModel registration
        5. Owner association through OmnipresenceModel

    Required Parameters:
        - persona_name (URL): Desired assistant name
        - persona_creator (str): OmnipresenceModel identifier
        - persona_prompt (str): System instructions for AI
        - file_binary (File): Knowledge base document
        - persona_file_name (str): Document display name

    Returns:
        - HttpResponse: JSON with creation status and IDs

    Error Conditions:
        - HTTP 400: Existing name || invalid creator || missing fields
        - HTTP 500: OpenAI API failures
    """

    def post(self, request, persona_name, *args, **kwargs):
        """
        Handle persona creation request

        File Handling:
            - Accepts multipart/form-data uploads
            - Processes files through OpenAI vector store API
            - Associates files with created assistant
        """

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
    """
    Conversation Thread Controller

    Manages active AI conversation sessions through two critical operations:
        - Termination of ongoing AI processes (GET)
        - Local session record cleanup (DELETE)

    Maintains synchronization between local tracking and OpenAI's thread system
    """

    def get(self, request, thread_id, *args, **kwargs):
        """
        Halts all ongoing AI processing for a thread

        Immediately stops all current AI operations on a thread:
            - Cancels text generation mid-process
            - Stops file search operations
            - Terminates any active tool executions

        Parameters:
            thread_id (str): OpenAI's unique thread identifier

        Behavior:
            - Attempts cancellation for all active runs
            - Silently ignores already completed/failed runs
            - Returns 200 even if partial failures occur

        Use Case: Stop runaway AI responses or stuck thread processing
        """
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
        """
        Delete local thread tracking/metadata

        Removes the database record tracking a conversation thread while:
            - Preserving the OpenAI thread history
            - Maintaining associated files stored
            - Keeping the audit trails on the servers

        Parameters:
            thread_id (str): Local thread_id reference

        Important Notes:
            - Thread can be revived via new messages
            - Permanently deletes local interaction history
        """
        thread = PersonaThreadModel.objects.get(
            thread_id = thread_id
        )
        thread.delete()
        return HttpResponse(
            status = 200
        )


class ForbiddenInventoryError(Exception):
    """
    Custom exception for forbidden inventory access.

    This exception is raised when a user attempts to access a restricted item or inventory.

    Args:
        *args: Variable length argument list to be passed to the parent Exception class.

    Returns:
        None

    Note:
        This exception does not add any additional functionality beyond the base Exception class.
        It serves as a specific identifier for inventory access violations.
    """
    def __init__(self, *args):
        super().__init__(args)
