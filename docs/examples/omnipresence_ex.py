import requests
import json


def get_character_example():
    """Retrieve character information based on 'charname'."""
    url = "/v1/omnipresence/"
    params = {
        "charname": "example_charname"
    }

    response = requests.get(url, params=params)
    print(response.json())
    return response.json()


def create_character_example():
    """Create a new OmnipresenceModel instance."""
    url = "v1/omnipresence/"

    data = {
        "username": "example_user",
        "charname": "example_charname",
        "working_dir": "/path/to/working/dir"
    }

    response = requests.post(url, json=data)
    print(response.status_code, response.json())
    return response.json()


def get_active_characters_example():
    """Retrieve all active characters."""
    url = "/v1/omnipresence/active/"

    response = requests.get(url)
    print(response.json())
    return response.json()


def get_local_active_characters_example():
    """Retrieve active characters based on the current working directory."""
    url = "v1/omnipresence/active/"
    data = {
        "cwd": "/path/to/working/dir"
    }

    response = requests.post(url, json=data)
    print(response.json())
    return response.json()


def update_character_example():
    """Partially update an OmnipresenceModel instance."""
    url = "/v1/omnipresence/update/1/"  # replace '1' with the actual ID of the character
    data = {
        "is_active": True
    }

    response = requests.patch(url, json=data)
    print(response.status_code, response.json())
    return response.json()
