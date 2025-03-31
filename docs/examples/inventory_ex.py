import requests

BASE_URL = "/v1/inventory"


def add_inventory():
    url = f"{BASE_URL}/add"
    data = {
        "item_owner": "user_12345",
        "item_name": "Thermo Cube",
        "item_qty": 5,
        "item_consumable": True,
    }

    # Simulating file upload (e.g., item image)
    files = {"item": open("health_potion_image.png", "rb")}

    response = requests.post(url, data=data, files=files)
    print("Add Inventory Response:", response.status_code, response.text)


def get_inventory():
    url = f"{BASE_URL}/list"
    params = {"item_owner": "user_12345"}  # Example query parameter

    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("Inventory List:", response.json())
    else:
        print("Error fetching inventory:", response.status_code, response.text)


def update_inventory():
    url = f"{BASE_URL}/update"
    data = {"item_id": "inventory_6789", "new_qty": 10}

    response = requests.put(url, json=data)
    print("Update Inventory Response:", response.status_code, response.text)


def delete_inventory():
    url = f"{BASE_URL}/delete"
    data = {"item_id": "inventory_6789"}

    response = requests.delete(url, json=data)
    print("Delete Inventory Response:", response.status_code, response.text)
