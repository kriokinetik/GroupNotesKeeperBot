import json
import aiofiles

import exceptions


async def json_load(file_name: str) -> dict:
    try:
        async with aiofiles.open(file_name, 'r', encoding='utf8') as file:
            return json.loads(await file.read())
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        async with aiofiles.open(file_name, 'w', encoding='utf8') as file:
            await file.write(json.dumps({}, indent=4, ensure_ascii=False))
        return {}


async def json_dump(file_name: str, data: dict) -> None:
    async with aiofiles.open(file_name, 'w', encoding='utf8') as file:
        await file.write(json.dumps(data, indent=4, ensure_ascii=False))


async def check_records_existance(file_name: str, chat_id: int) -> bool:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]

    if not available_chat_records_data:
        return False

    return True


async def start_json_session(file_name: str, chat_id: int) -> None:
    data = await json_load(file_name)

    if chat_id in data:
        return

    data[str(chat_id)] = {"admins": [], "records": {}}
    await json_dump(file_name, data)


async def add_group_to_json(file_name: str, chat_id: int, group_name: str) -> None:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]

    if group_name in available_chat_records_data:
        raise exceptions.GroupAlreadyExistsError(group_name)

    if len(available_chat_records_data) >= 5:
        raise exceptions.GroupLimitExceededError

    available_chat_records_data[group_name] = []
    await json_dump(file_name, data)


async def delete_group_from_json(file_name: str, chat_id: int, group_name: str) -> None:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]

    if group_name not in available_chat_records_data:
        raise exceptions.GroupNotFoundError(group_name)

    available_chat_records_data.pop(group_name)
    await json_dump(file_name, data)


async def get_groups(file_name: str, chat_id: int) -> list:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    return list(available_chat_records_data.keys())


async def add_record_to_json(file_name: str, chat_id: int, group_name: str, datetime: str, content: str) -> None:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    record = {"datetime": datetime, "content": content}
    available_chat_records_data[group_name].append(record)
    await json_dump(file_name, data)


async def get_record_count(file_name: str, chat_id: int, group_name: str) -> int:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    return len(available_chat_records_data.get(group_name, []))


async def get_record_data(file_name: str, chat_id: int, group_name: str, record_id: int) -> dict:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    return available_chat_records_data[group_name][record_id]


async def edit_json_record(file_name: str, chat_id: int, group_name: str, record_id: int, new_description: str) -> None:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    records = available_chat_records_data.get(group_name, [])
    if 0 <= record_id < len(records):
        records[record_id]["content"] = new_description
        await json_dump(file_name, data)


async def delete_record(file_name: str, chat_id: int, group_name: str, record_id: int) -> None:
    data = await json_load(file_name)
    available_chat_records_data = data[str(chat_id)]["records"]
    records = available_chat_records_data.get(group_name, [])
    if 0 <= record_id < len(records):
        del records[record_id]
        await json_dump(file_name, data)


async def add_admin(file_name: str, chat_id: int, user_id: int) -> None:
    data = await json_load(file_name)
    admins_list = data[str(chat_id)]["admins"]

    if user_id not in admins_list:
        admins_list.append(user_id)
        await json_dump(file_name, data)


async def delete_admin(file_name: str, chat_id: int, user_id: int) -> None:
    data = await json_load(file_name)
    admins_list = data[str(chat_id)]["admins"]

    if user_id in admins_list:
        admins_list.remove(user_id)
        await json_dump(file_name, data)


async def get_admins_list(file_name: str, chat_id: int) -> list:
    data = await json_load(file_name)
    admins_list = data[str(chat_id)]["admins"]
    return admins_list
