import json


def add_record_to_json(file_path: str, group_name: str, date: str, description: str) -> None:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if group_name not in data:
        data[group_name] = []
        count = 1
    else:
        count = len(data[group_name]) + 1

    new_record = {
        'id': count,
        'date': date,
        'description': description
    }

    data[group_name].append(new_record)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_the_record_number(file_path, group_name) -> int:
    with open(file_path, 'r') as file:
        data = json.load(file)

    return len(data[group_name])


def get_the_shame_data(file_path, group_name, shame_id) -> str:
    with open(file_path, 'r') as file:
        data = json.load(file)

    id_data = data[group_name][shame_id]
    str_data = (f'Позор №{id_data["id"]} от {id_data["date"]}\n'
                f'{id_data["description"]}')
    return str_data
