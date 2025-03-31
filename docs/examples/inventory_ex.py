def add_inventory_example():
    url = "/v1/inventory/add"
    data = {
        "item_owner": "user_12345",
        "item_name": "Thermo Cube",
        "item_qty": 5,
        "item_consumable": True,
    }

    # file has to be read into a inventoruy
    files = {"item": open("health_potion_image.png", "rb")}

    response = requests.post(url, data=data, files=files)
    print(response.status_code, response.text)
