import json
from app import exceptions


def json_load(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf8') as file:
            return json.load(file)
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            json.dump({}, file, indent=4)
        return {}


def json_dump(file_path: str, data: dict) -> None:
    with open(file_path, 'w', encoding='utf8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def add_group_to_json(file_path: str, group_name: str) -> None:
    data = json_load(file_path)
    if group_name not in data:
        if len(get_the_groups(file_path)) >= 5:
            raise exceptions.GroupLimitExceededError

        data[group_name] = []
        json_dump(file_path, data)

    else:
        raise exceptions.GroupAlreadyExistsError


def delete_group_from_json(file_path: str, group_name: str) -> None:
    data = json_load(file_path)
    if group_name in data:
        data.pop(group_name)
        json_dump(file_path, data)
    else:
        raise exceptions.GroupNotFoundError


def add_record_to_json(file_path: str, group_name: str, date: str, description: str) -> None:
    data = json_load(file_path)

    if group_name not in data:
        data[group_name] = []

    new_record = {
        'date': date,
        'description': description
    }
    data[group_name].append(new_record)

    json_dump(file_path, data)


def get_the_groups(file_path: str) -> list:
    data = json_load(file_path)
    return list(data.keys())


def get_the_record_number(file_path: str, group_name: str) -> int:
    data = json_load(file_path)
    if group_name not in data:
        return 0
    return len(data[group_name])


def get_the_shame_data(file_path: str, group_name: str, shame_id: int) -> str:
    data = json_load(file_path)
    id_data = data[group_name][shame_id]
    str_data = (f'Позор №{shame_id + 1} от {id_data["date"]}\n'
                f'{id_data["description"]}')
    return str_data


def delete_the_record(file_path: str, group_name: str, shame_id: int) -> None:
    data = json_load(file_path)
    data[group_name].pop(shame_id)
    json_dump(file_path, data)


def edit_json_record(file_path: str, group_name: str, shame_id: int, new_description: str) -> None:
    data = json_load(file_path)
    data[group_name][shame_id]['description'] = new_description
    json_dump(file_path, data)
